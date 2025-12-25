from __future__ import annotations

import secrets
import time
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm

import asyncpg

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from mcp_server.db.pool import PgPool


@dataclass
class _PendingAuth:
    client_id: str
    params: AuthorizationParams


class Auth0BackedOAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """
    Minimal OAuth provider for MCP that delegates user authentication to Auth0.

    - MCP client dynamically registers against this server (/register).
    - MCP client redirects user to this server's /authorize.
    - We redirect user to Auth0 /authorize.
    - Auth0 redirects back to our /auth/callback.
    - We mint an OAuth authorization code for the MCP client and redirect to the
      client's redirect_uri.
    - MCP client exchanges that code at this server's /token, and receives an
      access token (opaque) + refresh token (opaque) that this server can verify.

    Notes:
    - This implementation stores clients/codes/tokens in memory (tutorial-simple).
      For production, persist in Postgres and encrypt tokens at rest.
    """

    def __init__(
        self,
        *,
        auth0_domain: str,
        auth0_client_id: str,
        auth0_client_secret: str,
        public_base_url: str,
        database_url: str | None = None,
    ) -> None:
        self.auth0_domain = auth0_domain.strip().rstrip("/")
        self.auth0_client_id = auth0_client_id
        self.auth0_client_secret = auth0_client_secret
        self.public_base_url = public_base_url.strip().rstrip("/")

        self._clients: Dict[str, OAuthClientInformationFull] = {}
        self._pending: Dict[str, _PendingAuth] = {}
        self._auth_codes: Dict[str, AuthorizationCode] = {}
        # Map auth code -> authenticated Auth0 subject (user id)
        self._auth_code_subject: Dict[str, str] = {}
        self._access_tokens: Dict[str, AccessToken] = {}
        self._refresh_tokens: Dict[str, RefreshToken] = {}

        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_fetched_at: float = 0.0

        self._db: PgPool | None = PgPool(database_url) if database_url else None
        self._db_ready: bool = False

    async def _ensure_db(self) -> None:
        if not self._db or self._db_ready:
            return
        await self._db.init()
        self._db_ready = True

    # ---- Client registration ----
    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        cached = self._clients.get(client_id)
        if cached:
            return cached

        if not self._db:
            return None

        try:
            await self._ensure_db()
            row = await self._db.fetchrow(
                "select client_info from public.oauth_clients where client_id = $1",
                client_id,
            )
            if not row:
                return None
            raw = row["client_info"]
            # asyncpg may return json/jsonb as a string unless codecs are configured.
            if isinstance(raw, str):
                raw = json.loads(raw)
            info = OAuthClientInformationFull.model_validate(raw)
            self._clients[client_id] = info
            return info
        except asyncpg.UndefinedTableError:
            # Migration not applied yet; fall back to in-memory only.
            return None

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self._clients[client_info.client_id] = client_info
        if not self._db:
            return
        try:
            await self._ensure_db()
            await self._db.execute(
                """
                insert into public.oauth_clients (client_id, client_secret, client_info)
                values ($1, $2, $3::jsonb)
                on conflict (client_id)
                do update set client_secret = excluded.client_secret, client_info = excluded.client_info, updated_at = now()
                """,
                client_info.client_id,
                client_info.client_secret or "",
                json.dumps(client_info.model_dump(mode="json")),
            )
        except asyncpg.UndefinedTableError:
            # Migration not applied yet; fall back to in-memory only.
            return

    # ---- Authorization flow ----
    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        # Stash the authorization params so we can complete the flow after Auth0 login.
        state_id = secrets.token_urlsafe(24)
        self._pending[state_id] = _PendingAuth(client_id=client.client_id, params=params)

        callback = f"{self.public_base_url}/auth/callback"
        auth0_authorize = f"https://{self.auth0_domain}/authorize"
        q = {
            "response_type": "code",
            "client_id": self.auth0_client_id,
            "redirect_uri": callback,
            "scope": "openid profile email",
            # We carry our internal state id; we’ll round-trip it through Auth0.
            "state": state_id,
        }
        return f"{auth0_authorize}?{urlencode(q)}"

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        ac = self._auth_codes.get(authorization_code)
        if not ac:
            return None
        if ac.client_id != client.client_id:
            return None
        if ac.expires_at < time.time():
            return None
        return ac

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        # Mint opaque access + refresh tokens for this MCP server.
        access = secrets.token_urlsafe(32)
        refresh = secrets.token_urlsafe(32)

        expires_at = int(time.time()) + 60 * 60  # 1 hour
        scopes = authorization_code.scopes

        # IMPORTANT: client_id on AccessToken is used by FastMCP as the "user id" downstream.
        # We store the authenticated Auth0 subject in a separate mapping keyed by the auth code.
        user_subject = self._auth_code_subject.get(authorization_code.code)
        if not user_subject:
            raise TokenError(error="invalid_grant", error_description="Unknown authorization code subject")

        self._access_tokens[access] = AccessToken(
            token=access,
            client_id=user_subject,
            scopes=scopes,
            expires_at=expires_at,
            resource=self.public_base_url + "/",
        )
        self._refresh_tokens[refresh] = RefreshToken(
            token=refresh,
            client_id=user_subject,
            scopes=scopes,
            expires_at=None,
        )

        # One-time use code
        self._auth_codes.pop(authorization_code.code, None)
        self._auth_code_subject.pop(authorization_code.code, None)

        return OAuthToken(access_token=access, token_type="bearer", expires_in=3600, refresh_token=refresh, scope=" ".join(scopes))

    # ---- Refresh token flow ----
    async def load_refresh_token(self, client: OAuthClientInformationFull, refresh_token: str) -> RefreshToken | None:
        rt = self._refresh_tokens.get(refresh_token)
        if not rt:
            return None
        # For refresh we accept any registered client; scope enforcement happens elsewhere if desired.
        return rt

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        # Rotate tokens
        access = secrets.token_urlsafe(32)
        refresh = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + 60 * 60

        requested_scopes = scopes or refresh_token.scopes
        user_subject = refresh_token.client_id

        self._access_tokens[access] = AccessToken(
            token=access,
            client_id=user_subject,
            scopes=requested_scopes,
            expires_at=expires_at,
            resource=self.public_base_url + "/",
        )
        self._refresh_tokens[refresh] = RefreshToken(
            token=refresh,
            client_id=user_subject,
            scopes=requested_scopes,
            expires_at=None,
        )

        # Invalidate old refresh token
        self._refresh_tokens.pop(refresh_token.token, None)

        return OAuthToken(access_token=access, token_type="bearer", expires_in=3600, refresh_token=refresh, scope=" ".join(requested_scopes))

    # ---- Access token verification (resource requests) ----
    async def load_access_token(self, token: str) -> AccessToken | None:
        at = self._access_tokens.get(token)
        if not at:
            return None
        if at.expires_at and at.expires_at < int(time.time()):
            return None
        return at

    async def revoke_token(self, token: str) -> None:
        self._access_tokens.pop(token, None)
        self._refresh_tokens.pop(token, None)

    # ---- Auth0 callback helper ----
    async def complete_auth0_callback(self, *, state: str, code: str) -> str:
        pending = self._pending.pop(state, None)
        if not pending:
            raise TokenError(error="invalid_grant", error_description="Unknown or expired state")

        callback = f"{self.public_base_url}/auth/callback"
        token_url = f"https://{self.auth0_domain}/oauth/token"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.auth0_client_id,
                    "client_secret": self.auth0_client_secret,
                    "code": code,
                    "redirect_uri": callback,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        id_token = data.get("id_token")
        if not isinstance(id_token, str):
            raise TokenError(error="invalid_grant", error_description="Auth0 did not return id_token")

        user_subject = await self._verify_auth0_id_token(id_token)

        # Mint an authorization code for the MCP client. IMPORTANT:
        # - AuthorizationCode.client_id must remain the MCP client's client_id (so /token can validate it).
        # - We store user_subject separately keyed by the authorization code.
        mcp_code = secrets.token_urlsafe(24)
        expires_at = time.time() + 60.0

        scopes = pending.params.scopes or []
        self._auth_codes[mcp_code] = AuthorizationCode(
            code=mcp_code,
            scopes=scopes,
            expires_at=expires_at,
            client_id=pending.client_id,
            code_challenge=pending.params.code_challenge,
            redirect_uri=pending.params.redirect_uri,
            redirect_uri_provided_explicitly=pending.params.redirect_uri_provided_explicitly,
            resource=pending.params.resource,
        )
        self._auth_code_subject[mcp_code] = user_subject

        # Redirect back to the MCP client
        q = {"code": mcp_code}
        if pending.params.state:
            q["state"] = pending.params.state
        return str(pending.params.redirect_uri) + ("&" if "?" in str(pending.params.redirect_uri) else "?") + urlencode(q)

    async def _get_auth0_jwks(self) -> Dict[str, Any]:
        now = time.time()
        if self._jwks_cache and (now - self._jwks_fetched_at) < 600:
            return self._jwks_cache
        url = f"https://{self.auth0_domain}/.well-known/jwks.json"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            jwks = resp.json()
        self._jwks_cache = jwks
        self._jwks_fetched_at = now
        return jwks

    async def _verify_auth0_id_token(self, id_token: str) -> str:
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        alg = header.get("alg")
        if alg != "RS256" or not kid:
            raise TokenError(error="invalid_grant", error_description="Invalid id_token header")

        jwks = await self._get_auth0_jwks()
        keys = jwks.get("keys") if isinstance(jwks, dict) else None
        if not isinstance(keys, list):
            raise TokenError(error="invalid_grant", error_description="Invalid JWKS")

        jwk = next((k for k in keys if isinstance(k, dict) and k.get("kid") == kid), None)
        if not jwk:
            raise TokenError(error="invalid_grant", error_description="Unknown signing key")

        public_key = RSAAlgorithm.from_jwk(json.dumps(jwk))
        claims = jwt.decode(
            id_token,
            key=public_key,
            algorithms=["RS256"],
            audience=self.auth0_client_id,
            issuer=f"https://{self.auth0_domain}/",
            options={"require": ["exp", "sub"]},
        )
        sub = claims.get("sub")
        if not isinstance(sub, str) or not sub.strip():
            raise TokenError(error="invalid_grant", error_description="Missing sub claim")
        return sub



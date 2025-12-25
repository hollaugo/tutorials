from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm

from mcp.server.auth.provider import AccessToken, TokenVerifier


@dataclass
class _JwksCache:
    jwks: Dict[str, Any]
    fetched_at: float


class Auth0TokenVerifier(TokenVerifier):
    """
    Verify Auth0-issued RS256 JWT access tokens using JWKS.

    We return an MCP AccessToken where:
    - client_id is set to the JWT subject (sub) so it can act as our stable user id
    - scopes are derived from 'scope' (string) and 'permissions' (array) when present
    """

    def __init__(
        self,
        *,
        auth0_domain: str,
        audience: str,
        issuer: Optional[str] = None,
        jwks_ttl_seconds: int = 600,
    ) -> None:
        self.auth0_domain = auth0_domain.strip().rstrip("/")
        self.audience = audience
        self.issuer = issuer or f"https://{self.auth0_domain}/"
        self.jwks_ttl_seconds = jwks_ttl_seconds
        self._cache: Optional[_JwksCache] = None

    async def _get_jwks(self) -> Dict[str, Any]:
        now = time.time()
        if self._cache and (now - self._cache.fetched_at) < self.jwks_ttl_seconds:
            return self._cache.jwks

        url = f"https://{self.auth0_domain}/.well-known/jwks.json"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            jwks = resp.json()

        self._cache = _JwksCache(jwks=jwks, fetched_at=now)
        return jwks

    @staticmethod
    def _scopes_from_claims(claims: Dict[str, Any]) -> List[str]:
        scopes: List[str] = []
        scope_str = claims.get("scope")
        if isinstance(scope_str, str) and scope_str.strip():
            scopes.extend([s for s in scope_str.split(" ") if s])
        perms = claims.get("permissions")
        if isinstance(perms, list):
            scopes.extend([p for p in perms if isinstance(p, str) and p])
        # de-dupe while preserving order
        out: List[str] = []
        seen = set()
        for s in scopes:
            if s in seen:
                continue
            seen.add(s)
            out.append(s)
        return out

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            alg = header.get("alg")
            if alg != "RS256" or not kid:
                return None

            jwks = await self._get_jwks()
            keys = jwks.get("keys") if isinstance(jwks, dict) else None
            if not isinstance(keys, list):
                return None

            jwk = next((k for k in keys if isinstance(k, dict) and k.get("kid") == kid), None)
            if not jwk:
                return None

            public_key = RSAAlgorithm.from_jwk(json.dumps(jwk))

            claims = jwt.decode(
                token,
                key=public_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "sub"]},
            )

            sub = claims.get("sub")
            if not isinstance(sub, str) or not sub.strip():
                return None

            exp = claims.get("exp")
            expires_at = int(exp) if isinstance(exp, (int, float)) else None
            scopes = self._scopes_from_claims(claims)

            # IMPORTANT: we set client_id=sub so our app can use it as the stable user key.
            return AccessToken(
                token=token,
                client_id=sub,
                scopes=scopes,
                expires_at=expires_at,
                resource=self.audience,
            )
        except Exception:
            return None



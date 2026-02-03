---
name: chatgpt-app:add-auth
description: Configure authentication for your ChatGPT App using Auth0 or Supabase Auth for multi-user support.
---

# Configure Authentication

You are helping the user add authentication to their ChatGPT App.

## When to Add Auth

- Multiple users will use the app
- Users need persistent, private data
- External APIs require user-specific credentials

## Supported Providers

### Auth0
- Full OAuth 2.1 implementation
- Enterprise features (SSO, MFA)
- Best for production apps

### Supabase Auth
- Simple email/password and social login
- Integrated with Supabase database
- Good for simpler apps

## Workflow

1. **Choose Provider**
   Ask: "Which authentication provider: Auth0 or Supabase Auth?"

2. **Guide Setup**

   **For Auth0:**
   - Create Auth0 application (Regular Web App)
   - Configure callback URLs: `{PUBLIC_URL}/auth/callback`
   - Get Domain, Client ID, Client Secret

   **For Supabase:**
   - Enable Authentication in project
   - Get Project URL and keys

3. **Generate Auth Code**
   Use `chatgpt-auth-configurator` agent to create:
   - OAuth provider implementation
   - Discovery endpoints
   - User subject extraction

4. **Update Server**
   Modify `server/index.ts` to use auth middleware.

5. **Update Environment**
   Add required variables to `.env.example`.

6. **Test Auth Flow**
   Guide through testing the OAuth flow.

## Environment Variables

**Auth0:**
```
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
PUBLIC_URL=http://localhost:8787
```

**Supabase:**
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

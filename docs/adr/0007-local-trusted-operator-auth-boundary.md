# ADR 0007: Local Trusted-Operator Assumption and Auth Evolution Path

## Status

Accepted

## Decision

Treat the control plane as a **local trusted-operator system** by default:

- a single technical operator runs the stack locally
- API surfaces are reachable for local tooling and UI integration
- there is no mandatory user/token/session authentication gate in front of the
  current FastAPI routes

At the same time, codify explicit threat-model boundaries and a staged migration
path so token/session authentication can be introduced later without breaking
local-first workflows.

## Current Design Evidence

The API process wires all v1 REST and WebSocket routes directly in the FastAPI
application startup path, and applies CORS middleware for browser-based local
UI access.

Primary evidence:

- `apps/api/app/main.py` creates the FastAPI app, configures CORS middleware,
  and includes both API and WebSocket routers under `/api/v1`
- `apps/api/app/api/v1/router.py` composes the primary feature routers without
  per-route auth guards today

This reflects a trusted local operator assumption rather than a
multi-tenant/Internet-exposed security posture.

## Threat Model Boundaries (Now)

### In scope assumptions

- the operator controls the machine running the stack
- localhost or equivalent local network exposure is deliberate and understood
- repository and worktree access is already trusted by the operator
- MCP/REST/UI clients are considered operator-adjacent tools, not separate
  untrusted users

### Out of scope protections

- strong identity guarantees between multiple human users
- Internet-facing hardening for hostile anonymous clients
- session revocation/audit semantics for external principals
- enterprise-grade access control layers (SSO/OIDC/RBAC) in the current state

### Operational implication

If deployed outside a trusted local context, the current defaults are
insufficient on their own and require external controls (network boundaries,
reverse-proxy auth, host hardening) until first-class auth is added.

## Future Auth Options

Introduce auth as an additive capability with local-first compatibility.
Pragmatic options include:

1. **Static local API token mode**
   - operator-generated token in local config
   - header-based API authentication for REST + WebSocket handshake
   - minimal operational overhead for single-user setups
2. **Session token mode**
   - explicit login endpoint (or bootstrap command) mints short-lived session
     tokens
   - enables rotation/expiration and clearer client lifecycle semantics
3. **External identity mode (optional)**
   - reverse-proxy or built-in OIDC integration
   - appropriate for non-local or shared deployments

## Migration Path (Non-Breaking, Local-First)

1. **Auth abstraction first**
   - add shared service interfaces for principal resolution and auth decisions
   - keep default implementation as `TrustedLocalOperator` (allow-all)
2. **Configuration-gated enforcement**
   - add an explicit auth mode setting (`trusted_local`, `token`, `session`,
     future `oidc`)
   - keep default at `trusted_local` so existing local workflows continue
3. **Introduce optional token checks**
   - enforce when mode is `token` or stronger
   - ensure REST and WebSocket surfaces share the same gate logic
4. **Client compatibility rollout**
   - update UI and MCP clients to send credentials when enabled
   - preserve no-auth behavior when mode remains `trusted_local`
5. **Observability and diagnostics**
   - emit structured auth-mode and auth-failure diagnostics for operator support
6. **Progressive hardening path**
   - document deployment profiles: local default vs shared/remote hardened
   - allow staged adoption without forcing schema-breaking changes

## Consequences

- we preserve today’s fast local setup and operator ergonomics
- we make the trusted boundary explicit, reducing ambiguity for contributors
- we establish a clear path to stronger auth without redefining the
  local-first product posture or breaking existing workflows

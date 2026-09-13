# Apache/WordPress wallet-challenge authentication: findings

- **Research ticket:** [#10 — Research Apache/WordPress authentication challenge integration requirements](https://github.com/jetpen/decent-ecosystem/issues/10)
- **Wayfinder context:** [#1](https://github.com/jetpen/decent-ecosystem/issues/1)
- **Branch:** `research/wordpress-authentication-challenge`
- **Scope:** requirements and conceptual interaction patterns only. This document does **not** select a wire protocol and does not implement an Apache module, WordPress plugin, wallet, or verifier.

## Claim classes

This document uses the following labels on every substantive finding:

- **Implemented/code-backed** — present in the local repositories or directly guaranteed by the cited upstream implementation/documentation.
- **Researched but unimplemented** — a capability or constraint established by a primary source, but not implemented for this integration in the local repositories.
- **Proposed design** — a possible decomposition or interaction pattern for later design work; not a committed protocol or implementation.
- **Long-term vision** — an ecosystem direction that is outside the MVP and must not be read as a current capability.

## Executive findings

1. **[Implemented/code-backed]** Apache separates authentication from authorization. Its core model selects an authentication type/provider and then evaluates `Require`; authorization can use registered providers and explicit boolean containers. The Apache documentation also says authentication-sensitive deployments should use TLS. [Apache authentication and authorization how-to](https://httpd.apache.org/docs/2.4/howto/auth.html), [mod_authz_core](https://httpd.apache.org/docs/2.4/mod/mod_authz_core.html).
2. **[Implemented/code-backed]** Apache has an official extension point suitable for an external verifier: `mod_authnz_fcgi` can invoke a separately managed FastCGI application for authentication, authorization, or both, and can return request variables to Apache. It supports arbitrary mechanisms in addition to user ID/password, but its documented invocation is a server-side request phase—not a browser-wallet ceremony. [mod_authnz_fcgi](https://httpd.apache.org/docs/2.4/mod/mod_authnz_fcgi.html).
3. **[Implemented/code-backed]** WordPress already has two useful seams: the `authenticate` filter can return a `WP_User`/`WP_Error`, and `rest_authentication_errors` can return `null` (not attempted), `true` (success), or `WP_Error` (failure). A plugin can register challenge/callback routes with a permission callback. [authenticate](https://developer.wordpress.org/reference/hooks/authenticate/), [REST authentication errors](https://developer.wordpress.org/reference/hooks/rest_authentication_errors/), [custom REST endpoints](https://developer.wordpress.org/rest-api/extending-the-rest-api/adding-custom-endpoints/).
4. **[Implemented/code-backed]** A successful WordPress browser login is a session transition. `wp_signon()` authenticates and sets cookies; `wp_set_auth_cookie()` sets authentication cookies for a known user ID; `wp_set_current_user()` alone does not log the user in. [wp_signon()](https://developer.wordpress.org/reference/functions/wp_signon/), [wp_set_auth_cookie()](https://developer.wordpress.org/reference/functions/wp_set_auth_cookie/), [wp_set_current_user()](https://developer.wordpress.org/reference/functions/wp_set_current_user/).
5. **[Researched but unimplemented]** The local `decent-identity` and `decent-registry` repositories provide public-key lookup and signed-record verification, not a wallet challenge lifecycle, browser transport, WordPress account mapping, Apache request-session bridge, or replay cache. Those boundaries must remain explicit.
6. **[Proposed design]** The least-coupled MVP shape is a browser-facing verifier flow that completes the wallet interaction first, then creates a normal site session. Apache may protect a resource or delegate a per-request decision to a verifier, but it should not be expected to block inside the Apache authentication phase waiting for a mobile-wallet interaction.
7. **[Researched but unimplemented]** WebAuthn and the W3C Digital Credentials API provide useful browser/wallet constraints, but neither is evidence that the decent-identity Ed25519 identity model is automatically interoperable with a mobile wallet. OpenID4VP supplies conceptual same-device and cross-device patterns, but explicitly requires profiling and therefore does not settle this project's protocol.

## Local repository baseline

### `decent-identity`

- **[Implemented/code-backed]** `decent-identity` performs exact-match lookup/publication of public-key bindings through `decent-registry`. Its documented identifier-to-key rule is SHA-256 over the raw UTF-8 identifier bytes with no normalization. It returns the latest verified public key and metadata. [Local `CONTEXT.md`](file:///home/ben/projects/decent-identity/CONTEXT.md), [local `README.md`](file:///home/ben/projects/decent-identity/README.md).
- **[Implemented/code-backed]** Its documented `get` path resolves a public key; its `put` path accepts an owner private-key PEM path to publish a signed binding. The private key is therefore an issuer/record-owner input to publication, not something a website login flow should receive. [Local `README.md`](file:///home/ben/projects/decent-identity/README.md).
- **[Researched but unimplemented]** There is no documented challenge object, challenge issuance endpoint, response envelope, wallet transport, freshness/replay store, audience binding, or authentication-session API in the local `decent-identity` documentation inspected for this ticket.

### `decent-registry`

- **[Implemented/code-backed]** The Registry stores/resolves signed Identity Records and Provider Records over libp2p Kad-DHT. Identity records bind owner-name bytes to an Ed25519 public key; records use canonical CBOR and Ed25519 signatures, with sequence monotonicity and owner binding on overwrite. [Local `CONTEXT.md`](file:///home/ben/projects/decent-registry/CONTEXT.md), [local `docs/protocol-concepts.md`](file:///home/ben/projects/decent-registry/docs/protocol-concepts.md).
- **[Implemented/code-backed]** The Registry's local multisignature workflow keeps private keys with the local signer and transports detached proofs/finalized envelopes; this is a record-update workflow, not a website login protocol. [Local `docs/protocol-concepts.md`](file:///home/ben/projects/decent-registry/docs/protocol-concepts.md).
- **[Researched but unimplemented]** The Registry does not, by the documented scope, define a short-lived authentication challenge, login nonce, relying-site audience, wallet handoff, response replay policy, or WordPress/Apache session. A Registry record is evidence from which a consuming verifier may obtain a public key; it is not itself a login session.

## Apache requirements and boundaries

### Core authentication model

- **[Implemented/code-backed]** Apache's official model distinguishes authentication (establishing who the requester is) from authorization (deciding whether they may access a resource). The standard configuration combines an authentication type such as `AuthType`, an authentication provider, and authorization through `Require`. `.htaccess` use requires suitable `AllowOverride` configuration. [Apache authentication and authorization how-to](https://httpd.apache.org/docs/2.4/howto/auth.html).
- **[Implemented/code-backed]** `mod_authz_core` authorization providers return **granted**, **denied**, or **neutral**; `<RequireAny>`, `<RequireAll>`, and `<RequireNone>` compose those results. A future verifier integration must define whether an unavailable/unattempted wallet flow is a neutral result, an authentication challenge/401, or a denial/403; Apache's result states do not define the wallet semantics. [mod_authz_core](https://httpd.apache.org/docs/2.4/mod/mod_authz_core.html).
- **[Researched but unimplemented]** Apache's standard Basic/Digest mechanisms are not a fit for sending a wallet signature as a new native credential without an additional module/provider. The official documentation describes Basic as sending the password to the server and recommends TLS; it does not define a mobile-wallet challenge exchange. [Apache authentication and authorization how-to](https://httpd.apache.org/docs/2.4/howto/auth.html), [mod_auth_basic](https://httpd.apache.org/docs/2.4/mod/mod_auth_basic.html).

### External verifier seam

- **[Implemented/code-backed]** `mod_authnz_fcgi` supports separately managed FastCGI applications in `authn`, `authz`, and combined `authnz` modes. Providers are defined in server configuration and selected with `AuthBasicProvider` and/or `Require`; the application returns a status and may return variables such as authenticated-user data. [mod_authnz_fcgi](https://httpd.apache.org/docs/2.4/mod/mod_authnz_fcgi.html).
- **[Proposed design]** A self-hosted verifier service could sit behind `mod_authnz_fcgi` for requests carrying an already-established site session or a request credential. It would resolve the identity public key, verify the response/session proof, and return an Apache principal or authorization result. This is a conceptual placement only; no FastCGI request/response schema is selected here.
- **[Proposed design]** For a first browser login, Apache should redirect or serve a login page that starts a wallet interaction, rather than invoke a synchronous auth provider that waits for a phone. After the callback completes, the site can establish a session and retry the original URL. The exact redirect status, callback binding, and session artifact are unresolved.
- **[Researched but unimplemented]** The Apache docs do not provide a standard mechanism for an authentication module to open a wallet, display a QR code, obtain user consent, or correlate an asynchronous mobile response with an in-flight HTTP request. A custom module, a helper service, or an application-level login route is required.

### Apache operational requirements

- **[Proposed design]** Require HTTPS for all challenge issuance, response delivery, callback, session-cookie, and verifier-to-site traffic. Do not put a private key, reusable bearer secret, or full signed response into URLs, logs, referrers, or cache keys.
- **[Proposed design]** Define failure behavior separately for: no credential, pending wallet interaction, invalid signature, expired/replayed response, unresolved public key, verifier outage, and insufficient site authorization. Do not collapse all failures into a misleading 401/403 until the user experience and logging policy are decided.
- **[Proposed design]** If Apache forwards an authenticated principal to WordPress, define the trust boundary and prevent client-controlled headers from impersonating it. Apache must overwrite, not merely pass through, any identity header consumed by PHP/WordPress; the deployment needs a documented trusted path.

## WordPress requirements and boundaries

### Authentication hooks

- **[Implemented/code-backed]** The `authenticate` filter is the general WordPress credential-validation seam. Its callback receives the prior result, username, and password and returns a `WP_User`, `WP_Error`, or null. `wp_authenticate()` is pluggable, but the normal extension path is the filter rather than replacing core. [WordPress `authenticate` hook](https://developer.wordpress.org/reference/hooks/authenticate/), [wp_authenticate()](https://developer.wordpress.org/reference/functions/wp_authenticate/).
- **[Implemented/code-backed]** The `wp_authenticate` action fires before authentication during `wp_signon()`, while `wp_login` fires after successful login and immediately follows the auth-cookie operation. `wp_login_failed` exposes failed-login notification/telemetry. These are lifecycle hooks, not a wallet protocol. [wp_authenticate](https://developer.wordpress.org/reference/hooks/wp_authenticate/), [wp_login](https://developer.wordpress.org/reference/hooks/wp_login/), [wp_login_failed](https://developer.wordpress.org/reference/hooks/wp_login_failed/).
- **[Proposed design]** A WordPress plugin could expose a dedicated login page/REST route that creates a pending challenge, accepts a wallet response, resolves or links the corresponding local `WP_User`, and then calls the normal session machinery. Using a fake username/password merely to reuse the `authenticate` filter is possible as an implementation tactic but should not be treated as the conceptual protocol.

### REST API and session boundaries

- **[Implemented/code-backed]** `rest_authentication_errors` is explicitly designed for multiple authentication methods. A method should return null when it was not attempted, true when it succeeded, or `WP_Error` with an appropriate status on failure. [REST authentication errors](https://developer.wordpress.org/reference/hooks/rest_authentication_errors/).
- **[Implemented/code-backed]** WordPress custom REST routes are registered during `rest_api_init`, should use a namespaced versioned route, and support argument validation/sanitization plus a `permission_callback`. [Adding custom REST endpoints](https://developer.wordpress.org/rest-api/extending-the-rest-api/adding-custom-endpoints/).
- **[Implemented/code-backed]** Cookie-authenticated REST requests require the WordPress REST nonce (`X-WP-Nonce` or `_wpnonce`) to establish the current user; absent a nonce, WordPress treats the request as unauthenticated. Application Passwords are a separate HTTPS Basic-auth method for API access. [REST authentication](https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/).
- **[Implemented/code-backed]** WordPress says its nonces help mitigate CSRF but are not true one-use nonces and must never be relied on for authentication, authorization, or access control. Capability checks remain required. [WordPress Nonces](https://developer.wordpress.org/apis/security/nonces/).
- **[Implemented/code-backed]** `wp_signon()` sets authentication cookies and must run before content is sent; `wp_set_auth_cookie()` sets cookies for a user ID with configurable persistence and secure-cookie behavior. `WP_Session_Tokens` manages per-user session tokens and supports verification, retrieval, update, and destruction. [wp_signon()](https://developer.wordpress.org/reference/functions/wp_signon/), [wp_set_auth_cookie()](https://developer.wordpress.org/reference/functions/wp_set_auth_cookie/), [WP_Session_Tokens](https://developer.wordpress.org/reference/classes/wp_session_tokens/).
- **[Proposed design]** Treat the wallet response as authentication input only. After verification, map the verified identity to a site-owned `WP_User`, set a normal WordPress session, and let existing capability checks authorize site actions. Do not use a WordPress nonce as the wallet challenge, and do not make a long-lived wallet signature serve as a bearer session token.
- **[Researched but unimplemented]** The local ecosystem has no policy for first login/account creation, identifier changes, unlinking, multiple wallet keys, WordPress multisite, role assignment, or session revocation after a key is rotated/revoked.

## Browser, wallet, and interoperability constraints

### WebAuthn: relevant boundary, not an automatic fit

- **[Implemented/code-backed]** WebAuthn defines a browser-mediated public-key credential API. The user agent mediates authenticator access; authenticators require user consent; credentials are scoped to a WebAuthn Relying Party/origin; and the credential private key is expected never to be exposed outside its managing authenticator. [W3C Web Authentication Level 3](https://www.w3.org/TR/webauthn-3/).
- **[Researched but unimplemented]** WebAuthn's RP-scoped credential model is not the same as the local decent-identity model of an Ed25519 public key bound to an exact-match owner name. Adopting WebAuthn would require an explicit identity/account-binding decision and may change the wallet and key semantics. This research therefore treats WebAuthn as a security and browser-boundary reference, not as the chosen integration.

### Digital Credentials API: useful future browser seam

- **[Researched but unimplemented]** The W3C Digital Credentials document is a Working Draft. It is designed to let user agents mediate presentation/issuance, remain agnostic to credential formats and protocols, keep requests inspectable, make responses opaque to the user agent, require user mediation and transient activation, and support platform credential-manager UX. [W3C Digital Credentials](https://www.w3.org/TR/digital-credentials/).
- **[Proposed design]** If a target browser and wallet eventually support a suitable Digital Credentials presentation protocol, the WordPress login page could invoke the browser-mediated API after explicit user activation. The verifier would still need to define how the response identifies/binds the decent identity, how the public key is resolved, and how a site session is created. The current Working Draft does not answer those application questions.
- **[Long-term vision]** A standards-based browser-to-wallet path could reduce custom QR/deep-link glue and give users consistent consent and privacy UX across participating sites. This is not an MVP dependency and must not be advertised as current interoperability.

### OpenID4VP: conceptual same-device and cross-device patterns

- **[Implemented/code-backed]** OpenID4VP 1.0 is a final OpenID Foundation specification for requesting and presenting credentials. It describes same-device redirect interaction and cross-device QR interaction; cross-device responses can use `direct_post` to send the response to a verifier-controlled HTTPS endpoint. It also states that interoperability requires profiling, including choices about mandatory/optional features. [OpenID for Verifiable Presentations 1.0](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html), especially [Introduction](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html#section-3) and [cross-device flow](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html#section-3.2).
- **[Proposed design]** Two viable conceptual UX patterns are therefore:
  - **Same device:** site creates a one-time pending transaction; browser invokes or redirects to a wallet; wallet obtains consent and returns a response to the site; site verifies it and creates the WordPress session.
  - **Cross device:** site displays a short-lived QR/deep-link request; phone wallet scans/opens it; wallet posts the response to a verifier endpoint; the browser polls or receives completion and then gets a site session.
- **[Researched but unimplemented]** These are interaction patterns only. The local repositories do not implement OpenID4VP, QR/deep-link transport, DCQL/credential presentation, `direct_post`, response encryption, or an OpenID client/verifier.
- **[Proposed design]** Do not infer from OpenID4VP that a raw decent-identity challenge response is a Verifiable Presentation. A later profile must decide whether the wallet returns a proof of control, a credential presentation, or both, and what claims (if any) the site may learn.

### Proof-of-possession and replay

- **[Implemented/code-backed]** DPoP is an OAuth sender-constraining mechanism: a client proves possession of a private key with a signed `DPoP` header, and a resource server can bind a token to the public key. It is explicitly defense in depth, requires HTTPS, and does not itself authenticate the client. [RFC 9449](https://www.rfc-editor.org/rfc/rfc9449.html).
- **[Proposed design]** DPoP is a possible future reference for sender-constrained site/API tokens, but it is not a reason to choose OAuth/DPoP for the MVP. A mobile wallet challenge can use the same general principle—fresh verifier context plus proof of private-key possession—without adopting DPoP's token and JWT requirements.
- **[Researched but unimplemented]** No local component currently specifies challenge freshness, unique-use storage, audience/origin binding, request binding, clock-skew tolerance, signature algorithm negotiation, key rotation, revocation, or recovery behavior for login proofs.

## Conceptual interaction patterns (not protocol selections)

### Pattern A — WordPress-owned browser login

**[Proposed design]**

1. Unauthenticated browser requests the WordPress login page or a protected route.
2. A plugin creates a pending transaction containing a high-entropy, short-lived, single-use challenge and the intended local return target. It renders a wallet button/QR/deep-link or invokes a supported browser-mediated API only after the required user activation.
3. The wallet signs/responds without exporting its private key. The browser or wallet sends the response to the site/verifier callback.
4. The verifier obtains the expected public key from `decent-identity`/`decent-registry`, validates the response against the pending transaction, and consumes the transaction exactly once.
5. The plugin maps the verified identity to a site-owned `WP_User`, establishes a normal secure WordPress session, and redirects to the allowlisted return target.
6. Subsequent REST requests use the established WordPress cookie plus the REST nonce where required; capabilities, not wallet authentication alone, authorize actions.

**Strengths:** aligns with WordPress's session lifecycle; supports normal browser UX; keeps Apache out of the asynchronous phone interaction.

**Open risks:** account linking and identity disclosure; verifier callback CSRF; session fixation; response replay; browser/wallet support; safe return URLs.

### Pattern B — Apache gateway with an external verifier

**[Proposed design]**

1. Apache protects a location using an external verifier via an official provider seam such as `mod_authnz_fcgi`.
2. If no established credential/session is present, Apache sends the browser to an application login route rather than waiting for a mobile wallet during the authn phase.
3. The application completes the wallet transaction and returns a short-lived session artifact or trusted server-side session reference.
4. Apache/verifier validates that artifact on protected requests, supplies a trusted principal/authorization result, and proxies to WordPress.
5. WordPress either consumes the trusted principal through a carefully defined server-side bridge or runs its own session establishment.

**Strengths:** can protect non-WordPress paths; centralizes verifier policy; uses documented Apache extension architecture.

**Open risks:** two session authorities (Apache and WordPress); trusted-header/proxy confusion; login redirects from arbitrary protected URLs; cache and subrequest behavior; difficult error/pending semantics; duplicated authorization policy.

### Pattern C — Shared verifier, separate site adapters

**[Proposed design]** A verifier service owns pending transactions, public-key resolution, proof validation, replay protection, and audit policy. A WordPress adapter creates WordPress sessions; an Apache adapter returns authn/authz results. This preserves a single cryptographic verifier while acknowledging that Apache and WordPress have different session boundaries.

**Strengths:** avoids duplicating cryptographic and replay logic; can support future sites.

**Open risks:** the verifier becomes security-critical infrastructure; APIs and trust between adapters must be designed; availability and privacy metadata need explicit policy; no local implementation exists.

### Pattern D — Standards-profiled wallet presentation

**[Long-term vision]** Profile OpenID4VP and/or a browser Digital Credentials API flow so the site is a verifier, a mobile wallet is a holder, and the response carries only the minimum proof/claims requested. A same-device redirect and cross-device QR/direct-post profile could share verifier transaction semantics.

**Constraint:** this is not a decision for ticket #10. Standards profiling, credential format, identity binding, browser support, and disclosure policy remain unresolved.

## Requirements placed on `decent-identity`

- **[Researched but unimplemented]** Provide a verifier-facing way to resolve the expected public key for a site-selected identifier without requiring the site to hold the user's private key. Current `get` is a lookup primitive, not a challenge verifier.
- **[Proposed design]** Keep identifier lookup separate from response verification: resolve a key, verify a response bound to a fresh site transaction, then return a structured verification result. Do not make lookup success alone authenticate a user.
- **[Proposed design]** Define how exact-match raw-UTF-8 identifiers are selected and disclosed. If a site starts with email/name input, it must not silently normalize, enumerate, or leak identifiers beyond the approved policy.
- **[Proposed design]** Bind verification to a site audience/origin and transaction context. A signature valid for one site, action, or login attempt must not be transferable to another.
- **[Proposed design]** Define freshness and replay handling independently from Registry `seq`. Registry sequence numbers order record updates; they are not login nonces and cannot substitute for a consumed challenge store.
- **[Proposed design]** Define key-rotation/revocation behavior and cache invalidation. A verifier needs an explicit answer for an old key, a newly published key, a temporarily unavailable Registry, and a compromised key.
- **[Long-term vision]** Add a wallet/verifier abstraction that can support multiple presentation mechanisms while preserving the invariant that private keys remain wallet-controlled and never cross the wallet boundary.

## MVP security and privacy invariants

These are requirements to carry into a later design/HITL ticket, not a wire protocol:

- **[Proposed design]** Private keys never leave the wallet. No Apache process, PHP process, browser JavaScript, `decent-identity`, `decent-registry`, log, analytics system, or WordPress database receives the private key.
- **[Proposed design]** Every pending challenge is unpredictable, short-lived, scoped to the site/origin and intended transaction, and single-use. Store only what the verifier needs; hash or otherwise protect lookup tokens where appropriate.
- **[Proposed design]** The response must prove control of the resolved public key and be bound to the exact pending transaction. A static signed message or public-key lookup is insufficient.
- **[Proposed design]** Use HTTPS for all network legs. Treat browser history, referrers, access logs, reverse-proxy logs, QR displays, and callback URLs as potential disclosure surfaces.
- **[Proposed design]** Validate the post-login return target against a same-site allowlist to prevent open redirects.
- **[Proposed design]** Separate authentication, account linking, authorization, and session issuance. A valid wallet proof establishes control of an identity for an interaction; it does not automatically grant a WordPress role or capability.
- **[Proposed design]** Make verifier failures fail closed for protected actions while providing a recoverable user experience for a pending or unavailable wallet. Avoid leaking whether an identifier exists through distinguishable errors.
- **[Researched but unimplemented]** WordPress nonces and Apache authentication outcomes cannot replace these wallet-specific properties. They protect different boundaries and lifecycles.

## Unresolved decisions requiring a later HITL grilling ticket

The following should become explicit human-in-the-loop decisions before any implementation or wire-protocol selection:

1. **Protocol family:** raw challenge/signature, a credential presentation, WebAuthn, OpenID4VP, Digital Credentials API, or a layered combination?
2. **Wallet transport:** same-device browser API, HTTPS redirect/deep link, cross-device QR, local bridge, or a defined fallback order?
3. **Identity input and privacy:** does the user enter an identifier, scan/select one in the wallet, or use an opaque wallet identifier? Which claims may the site learn, and may the site enumerate identities?
4. **Key model:** is the wallet key exactly the Ed25519 key resolved from `decent-identity`, or is there a separate wallet/RP key that must be linked to it?
5. **Challenge transcript:** which request fields are signed/bound (site origin, audience, path/action, timestamp, return transaction, browser/device binding), and what canonical encoding is used?
6. **Replay policy:** where are pending challenges stored, how are they atomically consumed, what is the expiry/clock-skew policy, and what happens after callback retries?
7. **Account mapping:** how does a verified identity select an existing `WP_User`; who may link/unlink; can first login create an account; what happens on identifier/key changes?
8. **Session policy:** normal WordPress auth cookie, a separate verifier session, an Apache principal, or both? What are lifetimes, logout/revocation semantics, and cross-site/multisite rules?
9. **Apache placement:** WordPress-owned login, Apache external provider, shared verifier, or a per-site choice? How are trusted principals forwarded without spoofable headers?
10. **Authorization policy:** does wallet authentication merely select a WordPress user, or can it carry role/capability/consent claims? Which claims are authoritative and which remain operator-controlled?
11. **Key rotation and recovery:** how are new keys, revoked keys, lost wallets, recovery identities, and Registry outages handled without silently authenticating stale bindings?
12. **Availability and caching:** may verified public keys be cached, for how long, and what is the fail-closed/fail-open policy during Registry/verifier outage?
13. **Wallet consent and anti-abuse:** how is user activation enforced; how are malicious sites, phishing domains, clickjacking, QR replacement, and repeated unsolicited prompts handled?
14. **Interoperability target:** which concrete wallet/browser versions and credential formats are in the MVP acceptance matrix, and what evidence is required before claiming support?
15. **Audit and data retention:** what authentication metadata may be logged, how long is it retained, and how are signatures/claims redacted from operational logs?
16. **Migration/fallback:** is password/Application Password login retained, disabled, or used only for bootstrap/recovery, and how is downgrade or account takeover prevented?

## Out of scope for this artifact

- Choosing a final wire protocol or canonical challenge schema.
- Implementing an Apache module, FastCGI authorizer, WordPress plugin, wallet, browser integration, or verifier service.
- Treating WebAuthn, Digital Credentials API, OpenID4VP, or DPoP as already implemented by the local repositories.
- Closing or editing GitHub issue #10.

## Source index

### Local primary sources

- [`decent-ecosystem/CONTEXT.md`](file:///home/ben/projects/decent-ecosystem/CONTEXT.md)
- [`decent-identity/CONTEXT.md`](file:///home/ben/projects/decent-identity/CONTEXT.md)
- [`decent-identity/README.md`](file:///home/ben/projects/decent-identity/README.md)
- [`decent-registry/CONTEXT.md`](file:///home/ben/projects/decent-registry/CONTEXT.md)
- [`decent-registry/docs/protocol-concepts.md`](file:///home/ben/projects/decent-registry/docs/protocol-concepts.md)

### Apache HTTP Server

- [Authentication and Authorization — Apache HTTP Server 2.4](https://httpd.apache.org/docs/2.4/howto/auth.html)
- [mod_auth_basic](https://httpd.apache.org/docs/2.4/mod/mod_auth_basic.html)
- [mod_authz_core](https://httpd.apache.org/docs/2.4/mod/mod_authz_core.html)
- [mod_authnz_fcgi](https://httpd.apache.org/docs/2.4/mod/mod_authnz_fcgi.html)

### WordPress Developer Resources

- [REST API authentication](https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/)
- [Adding custom REST endpoints](https://developer.wordpress.org/rest-api/extending-the-rest-api/adding-custom-endpoints/)
- [`authenticate` hook](https://developer.wordpress.org/reference/hooks/authenticate/)
- [`rest_authentication_errors` hook](https://developer.wordpress.org/reference/hooks/rest_authentication_errors/)
- [`wp_authenticate()`](https://developer.wordpress.org/reference/functions/wp_authenticate/)
- [`wp_signon()`](https://developer.wordpress.org/reference/functions/wp_signon/)
- [`wp_set_auth_cookie()`](https://developer.wordpress.org/reference/functions/wp_set_auth_cookie/)
- [`wp_set_current_user()`](https://developer.wordpress.org/reference/functions/wp_set_current_user/)
- [`wp_login` hook](https://developer.wordpress.org/reference/hooks/wp_login/)
- [`wp_login_failed` hook](https://developer.wordpress.org/reference/hooks/wp_login_failed/)
- [`WP_Session_Tokens`](https://developer.wordpress.org/reference/classes/wp_session_tokens/)
- [WordPress Nonces](https://developer.wordpress.org/apis/security/nonces/)
- [Roles and Capabilities](https://developer.wordpress.org/plugins/users/roles-and-capabilities/)

### Browser and interoperability specifications

- [W3C Web Authentication Level 3](https://www.w3.org/TR/webauthn-3/)
- [W3C Digital Credentials](https://www.w3.org/TR/digital-credentials/)
- [OpenID for Verifiable Presentations 1.0](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html)
- [RFC 9449 — OAuth 2.0 Demonstrating Proof of Possession](https://www.rfc-editor.org/rfc/rfc9449.html)

# Keycloak integration surfaces for wallet authentication

**Research date:** 2026-10-05
**Keycloak version examined:** 26.8.0 (documentation release version; the public 26.8.0 developer guide, release notes, configuration and API references were checked).
**Context:** Wayfinder research ticket [#30](https://github.com/jetpen/decent-ecosystem/issues/30), under the [shared ecosystem authentication, authorization, and Keycloak architecture map #29](https://github.com/jetpen/decent-ecosystem/issues/29). Scope is governed by [#36](https://github.com/jetpen/decent-ecosystem/issues/36). This is feasibility research, not a choice of the shared protocol or a recommendation to fork Keycloak.

## Executive result

Keycloak can issue the standard OIDC/OAuth session and access tokens after a wallet authentication step, but the current ecosystem’s raw Ed25519 challenge response and live `decent-identity` resolution are not a built-in Keycloak login mechanism. A Keycloak in-flow `Authenticator` can implement that bridge as an installable provider JAR. This is the smallest *in-Keycloak* integration seam identified; **however the 26.8.0 developer guide explicitly classifies the Authentication SPI as internal and subject to change without notice**, so an extension does not equal a stable, supported API contract. [Server Developer Guide § Authentication SPI](https://www.keycloak.org/docs/26.8.0/server_development/#_authentication_spi)

Keycloak’s supported RFC 7523 JWT Authorization Grant is a second possible route only after the wallet/identity protocol decides to issue a short-lived, signed JWT assertion and to trust/configure its issuer. Keycloak requires a pre-linked user, an external issuer, a JWT addressed to Keycloak, and a signed assertion; it exchanges that assertion without a direct user-approval step at Keycloak. It does **not** accept the existing non-JWT challenge response, resolve the Registry-backed key, or supply the preceding wallet consent ceremony. The feature is supported since 26.6, and the token endpoint mechanics are documented; the proposed identity relationship is not solved just by enabling it. [Keycloak JWT Authorization Grant](https://www.keycloak.org/securing-apps/jwt-authorization-grant), [26.6 release notes](https://www.keycloak.org/docs/26.8.0/release_notes/#keycloak-26-6-0)

**Feasibility finding:** an external provider is technically plausible for a first feasibility prototype, but its security-sensitive login seam is an explicitly internal SPI. Therefore research does not establish “provider is safely upgradeable” or “fork is needed.” An upstream feature request, a maintained provider, a separate standards-based wallet verifier/broker, or a fork remain architectural choices. The first experiment should establish whether a provider can implement a current-key lookup plus a fresh, single-use challenge *without* altering Keycloak internals, and then test that JAR against at least one supported Keycloak upgrade. The public repository URL searched for `decent-keycloak` returned 404 on the research date; its code, license, release policy, maintenance status, and delta from upstream could not be inspected.

## Existing ecosystem constraints (input, not redecided here)

- **[Accepted ecosystem concept]** The login proof is a fresh, short-lived, single-use Ed25519 signature over the exact transaction/site context. `decent-identity` resolves the selected exact-match identifier to its current Registry-validated public-key binding. Identity/Registry lookup alone is not authentication; invalid, stale, replayed, ambiguous, unresolved, or unavailable inputs fail closed. See [authentication challenge/verifier resolution #11](https://github.com/jetpen/decent-ecosystem/issues/11) and [`decent-identity` boundary](../../components/decent-identity.md).
- **[Accepted ecosystem concept]** Wallet private-key custody stays in the wallet. Authentication proof does not itself disclose Account Entity fields, authorize storage operations, establish a site session, or grant a bearer capability. WordPress owns its app session; `decent-simple-storage` independently enforces resource permissions and operator-approved onboarding/quota. See [`decent-wordpress-auth` boundary](../../components/decent-wordpress-auth.md), [`decent-simple-storage` boundary](../../components/decent-simple-storage.md), and [map scope resolution #36](https://github.com/jetpen/decent-ecosystem/issues/36).
- These existing semantics matter: a generic OIDC IdP configuration expects an upstream protocol response and trust model. It does not imply that a human-controlled identity record is automatically an OIDC issuer or that an IdP link is proof the wallet approved storage access.

## Findings by integration route

### 1. Configuration-only OIDC identity brokering

Keycloak can broker authentication to upstream OAuth/OIDC IdPs. A normal brokered login depends on an upstream provider implementing the expected authorization-code based protocol and returning a response Keycloak can validate. The broker then maps/links that external identity to a Keycloak user. [Keycloak Server Administration Guide—Identity Brokering](https://www.keycloak.org/docs/26.8.0/server_admin/#_identity_broker), [Developer Guide—Identity Brokering APIs](https://www.keycloak.org/docs/26.8.0/server_development/#_identity_brokering_apis)

The current `decent-identity` service is not such an OIDC authorization server: it resolves exact-match identifier-to-key bindings and does not issue OIDC authorization codes, ID Tokens, user sessions, or login challenges. [Identity component boundary](../../components/decent-identity.md)

A configuration-only solution is possible only if an independent wallet-verifier service is added that exposes a standard OIDC issuer interface, completes the wallet challenge and current Identity resolution, and emits an OIDC authentication response. That separate service could then be configured as a standard Keycloak OIDC identity provider. The standards-level division is clean, but creating that issuer/broker and deciding its subject/linking and trust semantics are still real work. It would also need to avoid turning `decent-identity` lookup into authentication.

**Finding:** ordinary broker configuration alone cannot consume the existing raw wallet response or query/verify the current Identity key. Configuration only becomes viable after a separate standards-speaking verifier/issuer exists.

### 2. Custom in-flow Keycloak Authenticator provider (SPI)

The Keycloak 26.8 developer guide documents a plugin surface for custom login mechanisms. It says an authenticator provider implements `Authenticator` and `AuthenticatorFactory`, is registered through the `META-INF/services/org.keycloak.authentication.AuthenticatorFactory` service file, is packaged in a JAR, copied to `providers/`, and picked up by running `kc.sh build` (or a non-optimized start). The Admin Console can apply, order, and configure authenticator steps in a login flow. [Keycloak Server Developer Guide—Providers](https://www.keycloak.org/docs/26.8.0/server_development/#_providers), [—Authentication SPI](https://www.keycloak.org/docs/26.8.0/server_development/#_authentication_spi), [AuthenticatorFactory Javadoc 26.8](https://www.keycloak.org/docs-api/26.8.0/javadocs/org/keycloak/authentication/AuthenticatorFactory.html)

An authenticator could, in principle:

1. create or bind the current Keycloak authentication session to a new high-entropy, expiring, single-use challenge;
2. display a QR/deep-link or hand off through the browser to the wallet;
3. receive or poll for the wallet response through a callback/helper;
4. resolve the exact identity binding through `decent-identity`, verify the Ed25519 proof and transaction audience/context, and atomically consume the pending transaction;
5. map the verified identity to a Keycloak principal and let Keycloak complete its normal OIDC login/session/token issuance.

This flow needs care: an HTTP login request cannot block awaiting mobile approval; callback state and browser session must be bound; challenge consumption needs shared/atomic storage under clustering; Keycloak user identity linking must avoid account takeover; Identity/Registry outage must fail closed. The Authenticator may call an external verifier rather than implement the whole transaction and Registry client within Keycloak. In either case the trust boundary and failure contract must be tested.

**Stability caveat:** the same official guide warns that the Authentication SPI is **internal** and a new Keycloak release can change it without prior notice. This caution applies even though the guide documents how to write the provider. Thus “officially documented extensibility” does not mean “stable public compatibility guarantee.” Tests, source review, and per-release rebuilds would be required; pinning to the exact Keycloak version is prudent. [Authentication SPI stability note](https://www.keycloak.org/docs/26.8.0/server_development/#_authentication_spi)

**Finding:** this is the narrowest candidate for a native login flow, and avoids patching Keycloak source at first. But it brings a recurring compatibility obligation and does not make a portable protocol: a separate verifier/protocol contract is still needed for WordPress and other consumers.

### 3. Custom Identity Provider SPI

Keycloak exposes `IdentityProviderFactory`/`IdentityProvider` plugin abstractions for providers that integrate external identity systems. The 26.8 API reference shows a factory creating a configured provider instance; the standard broker flows and model provide their surrounding account-linking and response handling. [IdentityProviderFactory Javadoc 26.8](https://www.keycloak.org/docs-api/26.8.0/javadocs/org/keycloak/broker/provider/IdentityProviderFactory.html), [IdentityProvider Javadoc 26.8](https://www.keycloak.org/docs-api/26.8.0/javadocs/org/keycloak/broker/provider/IdentityProvider.html)

A custom “decent wallet” IdP could model wallet interaction as an external identity-provider login and integrate with Keycloak’s broker callbacks/account linking. This is a plausible provider alternative to inserting a custom authenticator directly into a login flow. It still requires provider code and explicit design for the wallet handoff, exact-match Identity key resolution, replay/transaction storage, key lifecycle, and mapping into Keycloak’s external subject/user model. It cannot turn ordinary OIDC config into wallet verification by itself.

The current docs and Javadocs establish that the provider API exists, but this research did not find an explicit stability commitment for the `IdentityProvider` SPI comparable to an externally versioned protocol. Do not infer a long-term compatibility guarantee from it. Check the exact SPI/API status and extension tests against the specific supported Keycloak release before relying on it.

**Finding:** worth comparing with the Authenticator SPI in a prototype. The custom IdP has a more natural “external authentication provider” boundary, while an authenticator offers direct control of the login-flow step. Which is smaller and less fragile depends on the callback/consent UX and the precise APIs that must be called.

### 4. Supported RFC 7523 JWT Authorization Grant

As of Keycloak 26.6, JWT Authorization Grant (RFC 7523) is promoted from preview to supported. The 26.8 guide describes an OAuth token endpoint exchange where a confidential client supplies a signed JWT assertion under `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer`; the AS validates it under an explicitly configured external issuer relationship and issues a Keycloak access token. Keycloak requires `iss`, `sub`, a single-valued Keycloak audience, `exp`, and a valid signature, and maps `sub` through a user already linked to the Identity Provider. Its defaults disallow assertion reuse; it expects a `jti` for one-time assertion semantics. [JWT Authorization Grant guide](https://www.keycloak.org/securing-apps/jwt-authorization-grant), [26.6 release notes](https://www.keycloak.org/docs/26.8.0/release_notes/#keycloak-26-6-0)

The RFC 7523 assertion is **not** the HTTP Bearer credential sent to the storage Resource Server. It is a token-endpoint grant request; Keycloak responds with a separate Keycloak-issued access token (the guide's example has `token_type: Bearer`). The assertion is a signed JWT, so today’s raw Ed25519 challenge response cannot be submitted directly. One possible bridge would have a wallet or wallet-side auth component produce a short-lived JWT assertion with required `iss`/`sub`/`aud`/`exp` and a unique `jti`; another is a dedicated verifier that accepts the existing proof and then communicates authenticated state to Keycloak. Either bridge changes/extends the protocol and raises decisions about which party is a trusted assertion issuer and how the already-linked Keycloak subject is provisioned.

Crucially, Keycloak’s own guide characterizes the grant as relying on an existing trust relationship **without a direct user-approval step at the authorization server**. That is appropriate only if owner authentication and any required consent have already been correctly completed and represented. It is not an owner-consent substitute and does not by itself encode storage object/action/purpose permissions. Those must be handled separately (for example by a separate authorization grant/RPT/capability design). [JWT Authorization Grant guide](https://www.keycloak.org/securing-apps/jwt-authorization-grant)

**Finding:** configuration-only is viable *if* the ecosystem later chooses a trusted JWT assertion issuer and the existing challenge is bridged into it. It is not a zero-adapter path for current wallet proof, and no grant should be minted just because Identity resolves a key.

### 5. Token customization / claims after authentication

OIDC protocol mappers and client scopes can map already-established user/session attributes into OIDC tokens. They do not perform the wallet signature challenge or establish that a wallet authorized a specific object/action/purpose. A mapper is not a replacement for the authenticator/verifier boundary. [Keycloak Server Administration Guide—Protocol Mappers](https://www.keycloak.org/docs/26.8.0/server_admin/#_protocol-mappers), [OIDC guide](https://www.keycloak.org/securing-apps/oidc-layers)

If storage authorization ultimately uses Keycloak JWT access tokens, the token claim profile must still distinguish a Keycloak-authenticated principal from an owner-approved resource capability. A token carrying only subject/login claims should not grant broad Storage Object access. Resource server enforcement and operator quota remain independent. This ticket does not select the token claim profile; see standards comparison [#31](https://github.com/jetpen/decent-ecosystem/issues/31).

### 6. Custom OAuth token grant or core/fork modification

Keycloak release notes for 26.8 describe an “OAuth Grant Type SPI” as an **internal update** to add flexibility for custom grant types. The release notes do not present it as a stable supported extension contract. Therefore a custom RFC 6749 grant type should not be assumed to be reliably implementable as an out-of-tree extension on this evidence alone. It would need direct source/API investigation and a compatibility prototype. [Keycloak 26.8 release notes—OAuth Grant Type SPI](https://www.keycloak.org/docs/26.8.0/release_notes/)

A fork/patch series can modify the token endpoint, login flow, or supported core provider behavior more directly, but also creates a Keycloak source merge, security-fix, release, build, test, and compatibility responsibility. No source inspection of a `decent-keycloak` fork was possible: `https://github.com/jetpen/decent-keycloak` returned 404 to the public lookup on 2026-10-05. We therefore cannot report whether it exists privately, is merely proposed, or has any maintenance/tests. **The evidence does not establish that a fork is needed.** First verify the provider/Auth SPI and the protocol boundary; compare maintenance burden only after identifying a requirement that the upstream provider seam cannot meet.

### 7. Standard HTTP/OIDC interfaces and deployment constraints

Keycloak exposes OIDC discovery and public signing keys via its documented well-known configuration and certificate/JWKS endpoints; services can use standard discovery/JWKS rather than Keycloak-internal token-validation APIs. It also documents OAuth token revocation and introspection. These are good integration interfaces for the storage Resource Server if Keycloak remains the issuer. [OIDC endpoint guide](https://www.keycloak.org/securing-apps/oidc-layers)

Provider packaging is not “copy a JAR and forget”: Keycloak’s developer guide requires the provider to be built against a Keycloak version, register its factory under `META-INF/services/`, be placed in the `providers/` directory, then be included in a Keycloak build (`kc.sh build` or non-optimized start); additional libraries must also be supplied and JAR contents share classloader space with Keycloak. [Server Developer Guide—providers](https://www.keycloak.org/docs/26.8.0/server_development/#_providers)

The 26.8.0 developer guide states that the official container image uses OpenJDK 21; current supported-configurations page likewise names Java 21 for the image and lists Podman as a supported container deployment runtime. Extension compilation/runtime must match the actual Keycloak base image. [Preface to Developer Guide](https://www.keycloak.org/docs/26.8.0/server_development/#_preface), [Supported Configurations](https://www.keycloak.org/server/supported-configurations)

## Options comparison (facts and trade-offs, not a selection)

| Route | Can it accept the present wallet challenge? | Keycloak-specific code? | Main compatibility/support issue | Main boundary concern |
|---|---|---|---|---|
| Configure an ordinary OIDC broker | No, not without a separate OIDC wallet-verifier/issuer | No Keycloak code if that issuer already exists | Interop is standard OIDC; adapter/verifier itself must be designed, hosted, maintained | Keep verifier as authenticator and do not treat `decent-identity` lookup as login |
| Custom Authenticator provider | Yes, it is designed to add a Keycloak login-flow step, subject to implementation | Yes, provider JAR; no core fork initially | Authenticator SPI expressly internal/unstable; rebuild/test across versions | Binding challenge, callback, replay storage, Identity resolution and principal mapping correctly |
| Custom Identity Provider provider | Potentially, as a custom broker integration, subject to implementation | Yes, provider JAR | API exists, but stability must be validated; full broker/linking flow complexity | External subject/account linking must be tied to current Identity without silent alias normalization |
| RFC 7523 built-in JWT Authorization Grant | Not raw proof; requires signed JWT assertion and existing issuer/user trust setup | No Keycloak plugin for the grant itself | Supported in Keycloak 26.6+; requirements fix assertion semantics and Keycloak user linking | Grant has no direct AS consent step; use only after proof/consent, and keep resulting access separate from storage authorization |
| Custom grant SPI / custom token endpoint | Not proven | Probably: supported path not established from current docs | Grant SPI marked internal in 26.8 release notes; would need exact source verification | Expanding core token issuance for ecosystem-specific semantics can create a private dialect |
| Maintained Keycloak fork | Yes, arbitrary custom code can be integrated, but still must be designed | Yes, source fork | Must carry rebase, CVE/security fixes, release compatibility, build and deployment burden | Fork may become the de facto protocol; keep ecosystem contract portable and independent |
| Separate wallet verifier + standard AS | Yes; verifier consumes current flow and emits a standard integration artifact | Not necessarily | Adds a service and protocol bridge but leaves Keycloak core untouched | Clarify subject mapping and exact semantics of the signed assertion / OIDC response |

## Feasibility assessment and recommended experiment

This research is assigned to AFK research rather than an architecture decision; the points below are feasibility guidance for child decision [“Choose Keycloak extension, fork, or component architecture”](https://github.com/jetpen/decent-ecosystem/issues/32), not a final choice.

**Smallest useful prototype sequence:**

1. **Build a minimal provider-only Keycloak image at 26.8.0.** Implement an AuthenticatorFactory JAR against the 26.8 APIs, use `META-INF/services`, copy the JAR into `providers/`, run the optimized build, and confirm it appears/selects in an authentication flow. This verifies packaging, not wallet security.
2. **Add a development-only test verifier boundary.** Start an authentication transaction with a fresh nonce/audience; return a deterministic test signature; check valid, wrong key, wrong audience, expired, replayed, missing/ambiguous current Identity key, and Identity/Registry outage. Ensure no Keycloak session/token is issued on each invalid/failure case. Do not use real wallet keys or claim protocol compatibility from this harness.
3. **Replace mock key lookup with `decent-identity` current resolution** over the intended interface; exercise key rotation/cache/revocation behavior required by the Identity component contract. Test multiple Keycloak nodes or shared transaction state if clustering is in scope.
4. **Run the exact same extension and security tests against the next supported Keycloak release** (and at least the target Podman image), recording source/API fixes required. The Authenticator SPI’s internal status makes this compatibility result a decision input, not a one-off build success.
5. **Only then compare to a custom Identity Provider implementation or upstream feature request.** Prototype the broker callback/account-link path if the Authenticator approach has an unacceptable internal API dependency or UX fit. Do not fork merely to move the same SPI implementation in-tree.

Acceptance must establish: fresh per-transaction challenge; exact current Identity key; no user key copied outside wallet; atomic one-time use; site/audience/transcript binding; safe asynchronous phone callback; no Identity lookup => no authentication; explicit separation of login from user consent; no token/session before complete verification; and behavior on server restart, multi-node operation, and release upgrade.

## Concrete unknowns / facts not established

1. Whether a `decent-keycloak` repository is private, planned, or nonexistent. Public URL was 404; no fork code, ownership, license, tests, release stream, or rebase policy was available to examine.
2. Whether the Authenticator SPI is acceptable for a production security boundary despite explicit “internal” status. Keycloak’s docs do not promise compatibility; only prototype and upstream policy can inform the risk tolerance.
3. Whether `IdentityProvider` SPI has a stronger stability contract or provides a materially smaller, safer path for this exact challenge/consent UI. Docs/Javadocs show its API but this research found no clear public stability guarantee.
4. How a Registry-backed identity maps to a stable Keycloak external subject/user without turning the user DB or provider alias into the ecosystem’s root identity authority.
5. Whether token exchange based on RFC 7523 is acceptable after a wallet challenge, or whether the auth protocol should remain non-JWT and use a separate verifier-to-Keycloak bridge.
6. Whether the shared authorization artifact is Keycloak-issued OAuth/JWT, opaque token, or another resource-side capability; that’s in #31 and the later human decision tickets.
7. Whether the same wallet flow belongs in Keycloak for WordPress and storage, or only a Keycloak test/production AS profile. Keycloak-specific integration must not become a prerequisite for every `decent-auth` consumer.

## Sources checked (official/primary)

- [Keycloak Server Developer Guide 26.8.0](https://www.keycloak.org/docs/26.8.0/server_development/) — provider packaging, Authenticator SPI, Identity Brokering APIs, User Storage SPI, extension points, container Java version.
- [Keycloak Authentication SPI section 26.8.0](https://www.keycloak.org/docs/26.8.0/server_development/#_authentication_spi) — explicitly states internal status and potential change without prior notice.
- [Keycloak provider packaging section 26.8.0](https://www.keycloak.org/docs/26.8.0/server_development/#_providers) — JAR/service registration, version dependency and rebuild instructions.
- [Keycloak 26.8.0 `AuthenticatorFactory` API](https://www.keycloak.org/docs-api/26.8.0/javadocs/org/keycloak/authentication/AuthenticatorFactory.html).
- [Keycloak 26.8.0 `IdentityProviderFactory` API](https://www.keycloak.org/docs-api/26.8.0/javadocs/org/keycloak/broker/provider/IdentityProviderFactory.html).
- [Keycloak JWT Authorization Grant guide](https://www.keycloak.org/securing-apps/jwt-authorization-grant) — RFC 7523 mapping, assertion claims, user linking, trust setup, one-use/replay behavior and resulting access token.
- [Keycloak Release Notes 26.8.0](https://www.keycloak.org/docs/26.8.0/release_notes/) — JWT Authorization Grant supported since 26.6, custom OAuth grant SPI classified as internal in 26.8, OID4VP remains experimental in 26.8.
- [Keycloak OIDC endpoint guide](https://www.keycloak.org/securing-apps/oidc-layers) — standard discovery, JWKS/certificates, introspection and revocation.
- [Keycloak Supported Configurations](https://www.keycloak.org/server/supported-configurations) — container/runtime/JDK deployment constraints.
- Ecosystem primary decisions: [authentication challenge #11](https://github.com/jetpen/decent-ecosystem/issues/11), [scope/trust boundary #36](https://github.com/jetpen/decent-ecosystem/issues/36), [standards research #31](https://github.com/jetpen/decent-ecosystem/issues/31), and [parent map #29](https://github.com/jetpen/decent-ecosystem/issues/29).

---

*Research only. Does not resolve issue #30 or close it.*

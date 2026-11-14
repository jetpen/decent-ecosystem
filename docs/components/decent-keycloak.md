# `decent-keycloak` component decomposition

Status: provider integration direction selected; full wallet-login acceptance remains open

Source decisions: [shared ecosystem authentication and Keycloak architecture](https://github.com/jetpen/decent-ecosystem/issues/29) (open), [Keycloak integration strategy](https://github.com/jetpen/decent-ecosystem/issues/32) (installable provider plus provider-neutral protocol; no fork absent demonstrated need), and [wallet-login protocol and acceptance](https://github.com/jetpen/decent-ecosystem/issues/46) (approved protocol, consumer/runtime acceptance still open)

Component repository: [jetpen/decent-keycloak](https://github.com/jetpen/decent-keycloak)

## Claim classes

- **Implemented/code-backed** — present in the component repository or supported by its recorded tests/evidence.
- **Researched but unimplemented** — established by research but not implemented or qualified in the component.
- **Proposed ecosystem design** — agreed conceptual boundary or protocol direction; implementation or cross-component acceptance may remain incomplete.
- **Long-term vision** — beyond the current MVP or not yet selected.

## Purpose and authority

**[Proposed ecosystem design — key purpose and theme] Universal Single Sign-On (SSO):** `decent-keycloak` contributes to the ecosystem vision of Universal SSO across participating sites by adapting wallet-based identity proof to Keycloak's OIDC provider flow. This is an ecosystem purpose, not a claim that the current experimental provider already delivers universal or cross-deployment SSO. Each relying party must integrate OIDC, validate the response, map its local account, and establish its own application session under its own policy.

**[Implemented/code-backed]** `decent-keycloak` is an experimental Keycloak provider for wallet-based sign-in using the provider-neutral `decent-wallet-login-v1` profile. It adapts that login protocol to Keycloak's authentication flow and OIDC issuance. It is an adapter, not the wallet, a relying-party website, or the owner of the shared protocol. The protocol and shared vectors are maintained in `decent-ecosystem`; wallet proof signing is a separate wallet capability.

The repository describes its supported build target as Keycloak 26.8.0 on Linux/amd64 and explicitly states that it is experimental and not production-ready. Build and test success, image smoke tests, or bounded loopback evidence do not establish production readiness, broad Registry reliability, or real TLS/browser/native-wallet interoperability. See the [component support policy](https://github.com/jetpen/decent-keycloak/blob/main/docs/support-policy.md), [security review and limitations](https://github.com/jetpen/decent-keycloak/blob/main/docs/security-review.md), and [wallet-login acceptance tracking](https://github.com/jetpen/decent-keycloak/issues/1).

**[Proposed ecosystem design]** Keycloak is the wallet-proof verifier and OIDC Provider in the selected Keycloak-based login lane. It resolves the exact wallet-selected Identity against current Registry state, verifies the fresh proof, and maps the exact identity identifier to a local Keycloak principal. It issues the ordinary OIDC result only after successful authentication. It is not an ecosystem-wide identity or authorization authority; its local principal and OIDC subject belong to the configured Keycloak realm.

## Wallet-login responsibility

**[Proposed ecosystem design]** The shared `decent-wallet-login-v1` contract is provider-neutral. The Keycloak adapter is responsible for implementing the Keycloak-side transaction and authentication integration without changing the shared proof meaning:

1. Bind a fresh, expiring, single-use challenge to the initiating Keycloak authentication session and relying-party context.
2. Present the wallet interaction through the Keycloak-hosted login flow and its approved browser/native transport.
3. Resolve the exact selected Identity using the current Registry-validated owner key; do not normalize identifiers or treat lookup alone as authentication.
4. Verify the Ed25519 proof against the exact transaction challenge and reject invalid, stale, mismatched, replayed, unresolved, or unavailable cases without authenticating.
5. Map the exact Identity ID to the appropriate local Keycloak user and resume the ordinary Keycloak OIDC flow on success.

The protocol core specifies exact proof fields, canonicalization, signature and challenge constraints. Browser transaction routes, state binding, replay storage, account mapping, and runtime behavior remain component implementation and acceptance responsibilities. Keep the shared protocol and vectors in `decent-ecosystem`; a Keycloak-specific adapter must not make Keycloak wire details normative for other consumers.

## Relying-party and account boundary

**[Proposed ecosystem design]** Relying parties validate the OIDC response, including issuer, client/audience, state, nonce, and PKCE as applicable, then map their local account by validated `(iss, sub)`. A relying party does not query Registry or treat a raw human-readable Identity ID as its local account key. Keycloak's local user mapping is separate from each relying party's application account and session.

The relying party owns its login/signup interface and site-local session. The OIDC authorization request may carry the ecosystem's explicit `decent_account_action=login|signup` extension; this is not `prompt=login`. Signup may disclose selected, self-asserted wallet fields to the relying party only through the separate wallet-to-RP OID4VP profile after successful OIDC validation for the same transaction. The profile and its full acceptance remain tracked by [ecosystem issue #51](https://github.com/jetpen/decent-ecosystem/issues/51); do not represent it as complete or conflate it with login proof.

## Separation from storage authorization

**[Proposed ecosystem design]** Wallet authentication proves control for a specific login interaction. It does not itself disclose Account Entity fields, authorize Storage Object operations, enroll an owner with a Storage Provider, set quota, or create a Storage Account Entity. Those are separate owner and provider decisions.

The current Storage interoperability boundary uses ordinary Keycloak-issued access tokens and operator-assigned roles as specified by the Storage component. Storage remains responsible for validating tokens and enforcing its owner mapping, enrollment, quota, object, and operation policy. Keycloak login must not call Storage as a hidden prerequisite or turn a successful login into Storage consent.

**[Researched but unimplemented]** The Keycloak repository contains a separate proposed owner-signed site-grant architecture. Its broader grant envelope and WordPress behavior remain proposed and are not authorized for implementation by that document; grant-derived claims are unavailable under the documented design until an approved, safe token lifecycle exists. Do not present that proposal as part of `decent-wallet-login-v1` or as the current Storage role-only profile.

## Key and data custody

**[Proposed ecosystem design]** The wallet retains and uses the user's private key. Keycloak receives the proof required for the current transaction and the public key needed for verification through the Identity/Registry resolution boundary; it must not receive or persist the user's private key, wallet-container password, encryption key, or Master Account Entity.

Keycloak's realm user record and OIDC subject are local provider state, not Registry records and not user-owned Account Entities. The OIDC result does not make Keycloak the owner of the user's Identity or site data.

## Non-goals

**[Long-term vision or out of scope]** `decent-keycloak` does not:

- implement or own the wallet, shared login protocol, or relying-party website;
- replace `decent-identity` or `decent-registry`, or turn Identity lookup into authentication by itself;
- own the user's private keys, consent, Master Account Entity, or site-specific Account Entities;
- establish the relying party's application session or define its account policy;
- authorize Storage operations, approve provider enrollment, assign provider quota, or act as Storage;
- define a universal authorization server, identity federation policy, trust score, or application access policy;
- imply that an experimental provider build is production-ready or compatible with unqualified Keycloak releases;
- imply that Passkey authentication is part of the MVP; it is excluded by [ecosystem issue #40](https://github.com/jetpen/decent-ecosystem/issues/40).

## Handoff and acceptance boundaries

**[Researched but unimplemented]** The Keycloak repository's parent wallet-login issue remains the place to track component acceptance. Its documented follow-up gates include the current-Registry matrix, transaction/replay/callback behavior, signup recovery, TLS/browser/wallet/OIDC Code + PKCE acceptance, support policy, and aggregate security review. The present issue state and evidence must be read from [decent-keycloak issue #1](https://github.com/jetpen/decent-keycloak/issues/1); a passing proof-core or offline lifecycle is not completion of the full flow.

Cross-component follow-up includes:

- [Ecosystem issue #46](https://github.com/jetpen/decent-ecosystem/issues/46): provider-neutral login contract and first-consumer acceptance.
- [Ecosystem issue #51](https://github.com/jetpen/decent-ecosystem/issues/51): separate wallet-to-relying-party account disclosure profile.
- [decent-wordpress-auth issue #6](https://github.com/jetpen/decent-wordpress-auth/issues/6): OIDC relying-party integration; no Registry lookup by the relying party.
- [decent-keycloak issue #56](https://github.com/jetpen/decent-keycloak/issues/56): broader owner-signed grant proposal and its unresolved boundaries; not an implementation authorization.

## Provenance

- [Ecosystem map and shared authentication architecture](https://github.com/jetpen/decent-ecosystem/issues/29)
- [Keycloak integration strategy decision](https://github.com/jetpen/decent-ecosystem/issues/32)
- [Provider-neutral wallet-login contract and acceptance](https://github.com/jetpen/decent-ecosystem/issues/46)
- [Keycloak repository README](https://github.com/jetpen/decent-keycloak/blob/main/README.md)
- [Keycloak support policy](https://github.com/jetpen/decent-keycloak/blob/main/docs/support-policy.md)
- [Keycloak security review and limitations](https://github.com/jetpen/decent-keycloak/blob/main/docs/security-review.md)
- [Wallet-to-RP OID4VP profile issue](https://github.com/jetpen/decent-ecosystem/issues/51)

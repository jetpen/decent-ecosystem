# `decent-wordpress-auth` component decomposition

Status: canonical conceptual handoff

Source decision: [decent-wordpress-auth component decomposition](https://github.com/jetpen/decent-ecosystem/issues/8)

Component repository: [jetpen/decent-wordpress-auth](https://github.com/jetpen/decent-wordpress-auth)

## Claim classes

- **Implemented/code-backed** — present in Apache/WordPress or existing component repositories.
- **Researched but unimplemented** — established by research but not implemented in this repository.
- **Proposed MVP design** — accepted ecosystem boundary awaiting component specification.
- **Long-term vision** — beyond the current MVP.

## Purpose and authority

**[Proposed MVP design]** `decent-wordpress-auth` is the first site-specific authentication implementation for a self-hosted Apache/WordPress participating site. It coordinates wallet authentication and purpose-bound disclosure requests, verifies the designated wallet proof, and allows the application to establish its own login session.

It is not a universal identity, authentication, consent, or authorization authority. A separate opaque site-owned account registration is not required by the ecosystem MVP; the user-owned site-specific Account Entity is the conceptual registration record.

## Authentication lifecycle

**[Proposed MVP design]**

1. Create a fresh, high-entropy, short-lived, single-use challenge.
2. Bind it to the participating site, audience, origin, transaction, action, browser context, and safe return context.
3. Start asynchronous browser-mediated wallet transport.
4. Receive and verify the wallet response against the current public key resolved through `decent-identity`.
5. Consume the transaction exactly once.
6. Coordinate authorized storage onboarding, Master Account Entity disclosure, and site-specific Account Entity creation.
7. Establish the application’s own session after successful verification and authorization.

Cross-device QR/deep-link is the primary transport; same-device redirect/deep-link is a compatible variant. Exact protocol encoding remains a component-repository decision.

## Responsibility split

**[Proposed MVP design]**

- The wallet retains private keys, signs the challenge, and mediates disclosure/capability approval.
- `decent-wordpress-auth` manages the pending transaction, verifier flow, public-key lookup, replay consumption, and site integration.
- `decent-identity` resolves the selected exact-match public-key binding but does not authenticate or establish sessions.
- `decent-registry` validates and resolves signed records but is not a login nonce store or session authority.
- Apache may front or protect routes but does not synchronously wait for the mobile-wallet ceremony.
- WordPress/the participating application owns its session and resource policy.
- `decent-simple-storage` enforces owner onboarding, quota, and capabilities.

## Account, disclosure, and storage onboarding

**[Proposed MVP design]**

- The wallet selects or confirms the exact identity binding; the site does not enumerate or silently normalize identifiers.
- Authentication proof does not disclose Master Account Entity fields or storage access.
- The wallet separately authorizes master-field disclosure, storage onboarding, and Account Entity operations.
- The site may coordinate storage-provider enrollment but cannot approve quota or bypass capabilities.
- Successful onboarding creates or initializes a user-owned site-specific Account Entity.
- Object discovery uses the Storage Object’s SHA-256 digest and Provider Record.
- Master Account Entity edits do not automatically propagate to site-specific entities.
- WordPress session state remains application-owned; no opaque WordPress account-registration record is required at the ecosystem level.

## Failure and session boundary

**[Proposed MVP design]** Invalid, stale, replayed, malformed, audience-mismatched, denied, unresolved, or unavailable authentication operations fail closed. Pending or cancelled wallet interactions remain unauthenticated. Retries create fresh challenges. The wallet proof is not a bearer session token. The application establishes its own session after verification; session lifetime, logout, renewal, and revocation remain implementation decisions.

## Non-goals

**[Long-term vision or out of scope]** The MVP does not define:

- a universal authentication implementation;
- Apache-native wallet authentication as the required path;
- shared verifier infrastructure;
- account recovery, portability, multi-site orchestration, or site-independent identity management;
- wallet-secret or private-key access;
- capability issuance or broadening by the authentication component;
- implementation-ready protocol messages, APIs, deployment configuration, or production guarantees.

## Handoff questions

**[Researched but unimplemented]** The component repository must resolve:

- Apache request integration and WordPress hooks/session integration;
- challenge transcript encoding, browser-wallet transport, and pending-transaction storage;
- verifier implementation, freshness, replay, audience/origin binding, and outage behavior;
- current Identity Record resolution and key lifecycle handling;
- identity selection and disclosure minimization;
- Master/site-specific Account Entity mapping;
- storage onboarding and capability delivery;
- return-target validation, privacy, logging, audit metadata, and security tests;
- compatibility with future site-specific authentication implementations.

## Provenance

- [Ecosystem map](https://github.com/jetpen/decent-ecosystem/issues/1)
- [Vision glossary](../../CONTEXT.md)
- [Authentication research](../research/wordpress-authentication-challenge.md)
- [decent-wordpress-auth decomposition resolution](https://github.com/jetpen/decent-ecosystem/issues/8)
- [Authentication protocol resolution](https://github.com/jetpen/decent-ecosystem/issues/11)

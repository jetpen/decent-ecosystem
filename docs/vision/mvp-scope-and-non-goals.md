# MVP scope and non-goals

Status: canonical conceptual document

Parent map: [Ecosystem vision and component decomposition](https://github.com/jetpen/decent-ecosystem/issues/1)

## Claim classes

Every substantive claim uses one of these classes:

- **Implemented/code-backed** — present in an existing component repository.
- **Researched but unimplemented** — supported by research but not implemented for this ecosystem flow.
- **Proposed MVP design** — accepted ecosystem design that still requires component-repository specifications.
- **Long-term vision** — direction beyond the MVP.

This document remains conceptual. It does not define implementation-ready APIs, wire formats, cryptographic primitives, deployment procedures, or production guarantees.

## Purpose and scope

**[Proposed MVP design]** The MVP is one end-to-end user-sovereign ecosystem slice composed of:

- one user-controlled mobile wallet;
- one existing `decent-identity` deployment;
- one existing `decent-registry`-backed identity and discovery path;
- one self-hosted Apache/WordPress participating site;
- one `decent-simple-storage` service instance for user-owned Storage Objects.

The canonical vocabulary and ownership boundaries are defined in [`CONTEXT.md`](../../CONTEXT.md). The component handoffs are documented under [`docs/components/`](../components/).

## Components and boundaries

### Wallet

**[Proposed MVP design]** The wallet generates, retains, and protects private keys; signs Identity Record updates; responds to authentication challenges; mediates purpose-bound consent; and participates in independent multisignature approval. Wallet contents require strong encrypted storage initialized through a password-derived symmetric key. Secrets never leave the wallet.

### `decent-identity`

**[Implemented/code-backed]** `decent-identity` performs exact-match lookup, publication, and retrieval of public-key bindings through `decent-registry`.

**[Proposed MVP design]** It remains a capability-neutral adapter. It does not authenticate users, establish sessions, interpret consent, or authorize site actions.

### `decent-registry`

**[Implemented/code-backed]** `decent-registry` stores, validates, resolves, orders, and replicates authorized signed Registry Records, including Identity Records and Provider Records.

**[Proposed MVP design]** It remains neutral infrastructure and does not store account entities, arbitrary content, wallet secrets, or site sessions.

### `decent-wordpress-auth`

**[Proposed MVP design]** This is the first site-specific authentication implementation. It runs a WordPress-owned application flow, verifies wallet proof, coordinates storage onboarding and disclosure, and allows the application to establish its own session. The MVP does not require a separate opaque WordPress account-registration record; the user-owned site-specific Account Entity is the conceptual registration record.

### `decent-simple-storage`

**[Proposed MVP design]** This is a delegated external storage provider for user-owned Storage Objects. Its primary use is JSON Account Entities. It also supports owner-authorized binary or textual content when the content type is allowlisted and the owner has an operator-approved quota. It enforces capabilities and does not own content or issue consent.

## Conceptual MVP flows

### Owner and storage onboarding

**[Proposed MVP design]**

1. The owner authenticates at the participating site through the wallet.
2. The site checks or initiates enrollment with a selected storage-provider instance.
3. The Storage Provider Operator approves or rejects owner enrollment and assigns a bounded quota.
4. The owner authorizes creation of a Master Account Entity.
5. The entity initializes non-sensitive default preferences, including `language: en` and a defined default time-zone value.
6. The owner authorizes creation of a site-specific Account Entity.
7. Each uploaded Storage Object is content-addressed by its SHA-256 digest and has corresponding Provider Record discovery metadata in the Registry.
8. The application establishes its own login session after authentication and authorized onboarding succeed.

The site may coordinate enrollment but cannot self-approve storage access or quota.

### Authentication

**[Proposed MVP design]** The MVP uses application-level Ed25519 proof-of-control:

1. `decent-wordpress-auth` creates a fresh, high-entropy, short-lived, single-use challenge.
2. The challenge is bound to the participating site, audience, transaction, action, browser context, and safe return context.
3. The wallet selects or confirms the exact-match Identity Record and signs the challenge after user approval.
4. `decent-wordpress-auth` resolves the current public key through `decent-identity` and verifies the response.
5. The transaction is consumed exactly once.
6. The application establishes its own session using its selected mechanism.

Cross-device QR/deep-link transport is the primary UX path; same-device redirect/deep-link transport is a compatible variant. The exact protocol encoding remains delegated to the component repositories.

### Disclosure and account data

**[Proposed MVP design]** Authentication proves control of an identity but does not grant profile disclosure, storage access, WordPress roles, or site-resource authorization. The wallet separately authorizes:

- disclosure of identity metadata;
- disclosure of selected Master Account Entity fields;
- creation, retrieval, or update of Account Entities;
- storage-provider capabilities;
- sensitive threshold-approved operations.

Master Account Entity edits create new content-addressed state and do not automatically propagate to site-specific Account Entities. Sites request fresh disclosures when needed.

### Sensitive operation

**[Proposed MVP design]** A selected sensitive account operation, including site-relationship deactivation, requires threshold approval by independent signer wallets. Partial multisignature bundles remain outside the Registry; only finalized threshold-satisfying material is submitted for validation and publication.

## Failure and privacy invariants

**[Proposed MVP design]**

- Private keys and wallet encryption secrets never leave the wallet.
- Secrets are never displayed, logged, transmitted, placed in errors, or stored as Registry content.
- Missing, denied, invalid, stale, replayed, audience-mismatched, over-quota, unallowlisted, or unavailable operations fail closed.
- Registry sequence numbers order record updates; they are not authentication nonces.
- A wallet proof is not a bearer session token.
- A digest identifies content for discovery but does not authorize retrieval.
- Registry stores discovery metadata, not Storage Object content.
- Master Account Entity edits do not automatically propagate across sites.

## Explicit non-goals

**[Long-term vision or out of scope]** The MVP excludes:

- account recovery, key recovery, key rotation, and portability;
- multi-provider federation and general multi-site orchestration;
- integrations beyond the initial Apache/WordPress site;
- unrestricted or unallowlisted content storage;
- unlimited owner storage capacity;
- Registry or DHT storage of object content;
- universal authentication or authorization authority;
- implementation-ready protocol, API, cryptographic, deployment, retention, availability, or compliance guarantees.

## Handoff

Each component repository uses its decomposition document as input to its own wayfinder map and implementation-ready specification work. See:

- [`decent-registry` decomposition](../components/decent-registry.md)
- [`decent-identity` decomposition](../components/decent-identity.md)
- [`decent-wallet` decomposition](../components/decent-wallet.md)
- [`decent-wordpress-auth` decomposition](../components/decent-wordpress-auth.md)
- [`decent-simple-storage` decomposition](../components/decent-simple-storage.md)

Decision provenance is maintained in the resolved child issues of the [ecosystem map](https://github.com/jetpen/decent-ecosystem/issues/1).

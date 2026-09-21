# `decent-registry` component decomposition

Status: canonical conceptual handoff

Source decision: [decent-registry component decomposition](https://github.com/jetpen/decent-ecosystem/issues/5)

Component repository: [jetpen/decent-registry](https://github.com/jetpen/decent-registry)

## Claim classes

- **Implemented/code-backed** — present in the existing Registry repository.
- **Researched but unimplemented** — established by evidence but not implemented for the ecosystem integration.
- **Proposed MVP design** — accepted ecosystem boundary awaiting component specification.
- **Long-term vision** — beyond the current MVP.

## Purpose and scope

**[Implemented/code-backed]** `decent-registry` is the neutral, self-hostable signed-record substrate. It publishes, resolves, verifies, orders, and replicates authorized Registry Records without owning the user, identity, account, profile, consent, or site policy represented by those records.

The ecosystem relies on Registry infrastructure for public Identity Records and Provider Records. It does not use Registry as an account-entity database or arbitrary-content store.

## Existing capabilities

**[Implemented/code-backed]** The existing Registry repository provides the MVP-facing foundations described by the source decision:

- canonical CBOR record handling;
- Ed25519 signed envelopes;
- owner binding and monotonic sequence validation;
- local durable storage;
- libp2p Kad-DHT publication and resolution;
- `put` and `get` surfaces;
- Identity Records for owner-name/public-key bindings;
- Provider Records for external discovery metadata;
- finalized multisignature envelopes and detached signer proofs, with private keys remaining local to signers.

These capabilities are Registry infrastructure. They do not implement wallet authentication, website sessions, consent, or storage-provider policy.

## Ecosystem boundary

**[Proposed MVP design]**

- The wallet is the source of user authorization and private-key custody.
- `decent-identity` is the identity-specific lookup/publication adapter.
- `decent-registry` validates and resolves signed Registry Records.
- `decent-simple-storage` stores user-owned Storage Objects outside Registry.
- `decent-wordpress-auth` and future site-specific integrations consume validated bindings and Provider Record discovery metadata.

**[Proposed MVP design]** For each uploaded Storage Object, an owner-bound Provider Record may publish public discovery metadata keyed by the object’s SHA-256 content digest. The Registry stores metadata, not object content or reusable access credentials.

## Non-goals

**[Long-term vision or out of scope]** `decent-registry` does not:

- own identities, accounts, profiles, or Storage Objects;
- store arbitrary application content, account entities, or private fields;
- issue or interpret consent or capabilities;
- verify website login challenges or establish application sessions;
- approve site actions;
- guarantee external provider availability, confidentiality, retention, or permanent resolution;
- become a backing store for `decent-simple-storage`.

## Handoff questions

**[Researched but unimplemented]** The component repository must maintain its own wayfinding for:

- Registry support for Provider Records per content-addressed Storage Object;
- owner/object binding and record-key semantics for those records;
- interoperability between existing signed-record envelopes and wallet-facing finalized publication;
- CSRNG-only key generation and fatal failure behavior, tracked in [Enhancement: enforce CSRNG-only key generation](https://github.com/jetpen/decent-registry/issues/105);
- content digest, sequence, replacement, and revocation interactions;
- availability and conflict behavior for multiple Provider Records;
- private-key secrecy, partial-bundle rejection, and security-test coverage.

Implementation-ready protocol and API choices belong in the Registry repository, not this ecosystem document.

## Provenance

- [Ecosystem map](https://github.com/jetpen/decent-ecosystem/issues/1)
- [Cross-component trust and data ownership](https://github.com/jetpen/decent-ecosystem/issues/4)
- [decent-registry decomposition resolution](https://github.com/jetpen/decent-ecosystem/issues/5)
- [decent-simple-storage decomposition](https://github.com/jetpen/decent-ecosystem/issues/12)

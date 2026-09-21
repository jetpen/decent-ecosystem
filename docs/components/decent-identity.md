# `decent-identity` component decomposition

Status: canonical conceptual handoff

Source decision: [decent-identity component decomposition](https://github.com/jetpen/decent-ecosystem/issues/6)

Component repository: [jetpen/decent-identity](https://github.com/jetpen/decent-identity)

## Claim classes

- **Implemented/code-backed** — present in the existing Identity repository.
- **Researched but unimplemented** — established by evidence but not implemented for the ecosystem integration.
- **Proposed MVP design** — accepted ecosystem boundary awaiting component specification.
- **Long-term vision** — beyond the current MVP.

## Purpose and scope

**[Implemented/code-backed]** `decent-identity` is a capability-neutral, identity-specific adapter over `decent-registry`. It performs exact-match lookup, publication, and retrieval of user-authorized public-key bindings for human-readable identifiers.

Identifiers use raw UTF-8 bytes without normalization or alias expansion. Public-key resolution does not itself authenticate a user.

## Existing capabilities

**[Implemented/code-backed]** The existing repository provides:

- exact-match identifier lookup;
- Identity Record publication and retrieval through Registry;
- finalized-envelope publication;
- legacy private-key-path publication as compatibility behavior;
- Registry-delegated validation, storage, resolution, sequencing, and quorum behavior;
- CLI `put` and `get` surfaces;
- parsing and relay of verified authorization metadata.

The wallet-facing publication target reuses the established key-generation and signing toolchain. The legacy private-key-path mode is not the ecosystem wallet boundary.

## Ecosystem responsibility

**[Proposed MVP design]**

- The wallet generates and retains private keys and authorizes signed updates.
- `decent-identity` relays or publishes user-authorized signed material and resolves bindings.
- `decent-registry` validates owner binding, signatures, sequence, authorization metadata, storage, and resolution.
- `decent-wordpress-auth` uses current validated public-key resolution as an input to challenge verification.
- `decent-simple-storage` remains independent and uses Provider Records for external object discovery.

Resolution and publication fail closed. Invalid, absent, stale, ambiguous, unavailable, or insufficient-quorum Registry results do not create identity authority or publication success.

## Non-goals

**[Long-term vision or out of scope]** `decent-identity` does not:

- hold or generate wallet private keys for the ecosystem wallet flow;
- verify website login challenges;
- establish site sessions;
- issue or interpret consent or authorization;
- approve site actions;
- store accounts, profiles, Storage Objects, or arbitrary application data;
- implement DID methods, DID Documents, identity graphs, normalization, aliases, recovery, or portability in this MVP.

## Handoff questions

**[Researched but unimplemented]** The component repository must resolve:

- wallet-produced signed or finalized publication without moving private-key custody into Registry or Identity services;
- exact public-key resolution semantics for authentication verifiers;
- key rotation, revocation, cache invalidation, and Registry outage behavior;
- Provider Record discovery integration without storing external content;
- error and metadata contracts for consuming components;
- dependency packaging, transport, deployment, and implementation-ready APIs.

`decent-identity` must not turn lookup success into authentication, authorization, consent, or session state.

## Provenance

- [Ecosystem map](https://github.com/jetpen/decent-ecosystem/issues/1)
- [Vision glossary](../../CONTEXT.md)
- [decent-identity decomposition resolution](https://github.com/jetpen/decent-ecosystem/issues/6)
- [Authentication protocol resolution](https://github.com/jetpen/decent-ecosystem/issues/11)

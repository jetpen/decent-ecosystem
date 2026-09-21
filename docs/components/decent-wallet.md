# `decent-wallet` component decomposition

Status: canonical conceptual handoff

Source decision: [decent-wallet component decomposition](https://github.com/jetpen/decent-ecosystem/issues/7)

Component repository: [jetpen/decent-wallet](https://github.com/jetpen/decent-wallet)

## Claim classes

- **Implemented/code-backed** — present in the existing component repository or established supporting repositories.
- **Researched but unimplemented** — established by evidence but not implemented in the wallet repository.
- **Proposed MVP design** — accepted ecosystem boundary awaiting wallet specification.
- **Long-term vision** — beyond the current MVP.

## Purpose and scope

**[Proposed MVP design]** `decent-wallet` is the user-controlled private-key custodian, signing component, and consent agent. It is authentication-implementation-neutral and must never disclose private keys or wallet secrets.

## Custody and secure storage

**[Proposed MVP design]**

- The wallet generates, retains, and protects identity key material.
- Wallet contents are stored with strong encryption.
- Initialization includes an owner setup step that establishes a password-derived symmetric encryption key.
- The password and derived key remain local to wallet storage protection; they are not identity, authentication, consent, threshold, or recovery credentials.
- Private keys and wallet secrets are never displayed, logged, transmitted, placed in errors, written to temporary files, or stored as Registry/DHT content.
- Missing, invalid, or unusable unlock credentials fail closed.

The password-based key derivation, encryption, memory handling, backup, and recovery mechanisms are implementation decisions for the wallet repository.

## MVP capabilities

**[Proposed MVP design]** The wallet:

- displays authentication, signing, consent, and approval requests;
- responds to application-level authentication challenges without exposing private keys;
- signs user-authorized Identity Record updates through the established signing toolchain;
- mediates purpose-bound disclosure and storage-capability decisions;
- participates in selected threshold-approved operations;
- returns explicit approval, denial, cancellation, and failure outcomes;
- remains independent of Registry storage, account/profile storage, site sessions, and site policy.

## Multisignature boundary

**[Proposed MVP design]** Each authorized signer wallet independently reviews and signs the same operation. Signer secrets remain local. Wallets may create, exchange, merge, and finalize local authorization material outside the Registry. Only finalized threshold-satisfying material is submitted to Registry validation and publication. Partial bundles are never stored in the Registry or DHT.

## Authentication and component interactions

**[Proposed MVP design]** Site-specific authentication components send challenge, disclosure, and capability requests to the wallet. The wallet returns a proof, consent decision, or authorization material without exposing secrets. The same conceptual boundary supports future authentication implementations; the MVP begins with self-hosted Apache/WordPress.

Authentication proves control of identity but does not imply consent, storage access, site roles, or site-resource authorization.

## Non-goals

**[Long-term vision or out of scope]** The wallet MVP does not define:

- authoritative account/profile storage;
- Registry or DHT operation;
- site authentication-server or session authority;
- site policy or resource authorization;
- account recovery, key recovery, key rotation, portability, migration, or multi-device synchronization;
- universal authentication interoperability;
- production hardware-secure-enclave requirements.

## Handoff questions

**[Researched but unimplemented]** The wallet repository must resolve:

- threat model and security review;
- CSRNG-only key generation;
- password-derived encryption, unlock/lock behavior, and secret lifetime;
- secure memory, diagnostics, and failure handling;
- key lifecycle, backup, recovery, and migration;
- challenge transport and consent interaction;
- multisignature bundle creation, merging, signing, and finalization;
- finalized-envelope handoff;
- security, denial, replay, malformed-request, and secret-disclosure tests.

## Provenance

- [Ecosystem map](https://github.com/jetpen/decent-ecosystem/issues/1)
- [Vision glossary](../../CONTEXT.md)
- [decent-wallet decomposition resolution](https://github.com/jetpen/decent-ecosystem/issues/7)
- [Authentication protocol resolution](https://github.com/jetpen/decent-ecosystem/issues/11)

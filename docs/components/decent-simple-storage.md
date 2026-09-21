# `decent-simple-storage` component decomposition

Status: canonical conceptual handoff

Source decision: [decent-simple-storage component decomposition](https://github.com/jetpen/decent-ecosystem/issues/12)

Component repository: [jetpen/decent-simple-storage](https://github.com/jetpen/decent-simple-storage)

## Claim classes

- **Implemented/code-backed** — present in existing component repositories.
- **Researched but unimplemented** — established by evidence but not implemented in this repository.
- **Proposed MVP design** — accepted ecosystem boundary awaiting component specification.
- **Long-term vision** — beyond the current MVP.

## Purpose and custody

**[Proposed MVP design]** `decent-simple-storage` is a delegated external storage provider for user-owned Storage Objects. Users own the objects; the provider accepts, retains, retrieves, updates, replaces, and deletes them as a custodian.

The primary ecosystem use is schema-open JSON Account Entities. The generic storage capability also supports owner-authorized binary or textual content when the content type is allowlisted and the owner has an operator-approved capacity entitlement.

The provider does not own objects, issue or broaden consent, interpret site policy, become an identity authority, operate Registry, or receive wallet private keys or encryption secrets.

## Owner onboarding and quota

**[Proposed MVP design]**

- An owner requests access to a particular provider instance.
- The owner authenticates and authorizes the request through the wallet or a future repository-defined onboarding mechanism.
- The Storage Provider Operator approves or rejects onboarding and assigns a bounded quota.
- `decent-wordpress-auth` may initiate or relay the request but cannot self-approve access or assign quota.
- Provider enrollment and site-account registration are distinct events.
- Creates, uploads, replacements, and expansions cannot exceed the owner quota.
- Capabilities authorize operations but cannot expand the quota.

Exact quota units, accounting, provisioning, suspension, and revocation remain implementation decisions.

## Storage Objects

**[Proposed MVP design]**

- Account Entities are the primary JSON Storage Objects for account/profile information, site-specific settings, preferences, and selective disclosures.
- Master Account Entities are reusable cross-site JSON data.
- Site-specific Account Entities represent one participating-site relationship.
- Other Storage Objects may contain arbitrary owner-authorized binary or textual content whose content type passes the provider allowlist.
- Every protected create, upload, retrieve, download, update, replace, disclose, and delete operation requires an appropriate capability.
- Invalid, stale, revoked, over-scoped, missing, or insufficient capabilities fail closed.
- Storage Object updates produce new content-addressed state rather than silently mutating a prior digest.

## Content addressing and Registry discovery

**[Proposed MVP design]** Each uploaded Storage Object is identified for discovery by the SHA-256 digest of its content. A corresponding owner-bound Provider Record is published to `decent-registry` for each uploaded object.

Provider Records expose public discovery metadata and an external storage location. They do not contain object content, private fields, wallet secrets, or reusable access credentials. A website resolves the digest through Registry and retrieves the object from the provider using onboarding context and a valid capability.

The digest is a discovery identifier, not authorization. The future specification must account for digest exposure and recognition of low-entropy or predictable content. Registry never stores or proxies object content.

## Onboarding demonstration

**[Proposed MVP design]** The initial WordPress integration demonstrates:

1. Owner authentication at the participating site.
2. Provider enrollment and quota state being checked or initiated.
3. Owner-mediated Master Account Entity creation after provider access is approved.
4. Initialization of `language: en` and a defined default time-zone value.
5. Wallet-mediated selective disclosure of requested master fields.
6. Creation or initialization of a user-owned site-specific Account Entity.
7. Provider Record publication and content-addressed discovery.
8. Application-owned session establishment after successful verification and authorization.

Master Account Entity edits do not automatically propagate to site-specific entities. Sites request fresh disclosures and the wallet separately authorizes them.

## Non-goals

**[Long-term vision or out of scope]** The MVP excludes:

- unallowlisted content types;
- unlimited or unmetered owner capacity;
- unrestricted public downloads;
- provider ownership or unrestricted reuse of user objects;
- consent issuance, capability issuance, or capability broadening;
- Registry/DHT object-content storage;
- identity resolution, authentication, or site-session authority;
- automatic master-to-site synchronization;
- implementation-specific encryption, retention, replication, availability, deletion, backup, recovery, portability, or compliance guarantees.

## Handoff questions

**[Researched but unimplemented]** The component repository must resolve:

- owner onboarding, operator approval, quota accounting, suspension, and revocation;
- content-type allowlists and abuse controls;
- object lifecycle, content digest, replacement, deletion, and version semantics;
- Provider Record publication and discovery;
- capability validation, expiry, revocation, and scope;
- Master/site-specific Account Entity initialization and edits;
- website discovery/retrieval and selective disclosure;
- privacy, encryption, retention, replication, deletion, backup, and availability;
- invalid, unauthorized, over-quota, unallowlisted, and unavailable operation tests.

## Provenance

- [Ecosystem map](https://github.com/jetpen/decent-ecosystem/issues/1)
- [Vision glossary](../../CONTEXT.md)
- [decent-simple-storage decomposition resolution](https://github.com/jetpen/decent-ecosystem/issues/12)
- [decent-wordpress-auth decomposition resolution](https://github.com/jetpen/decent-ecosystem/issues/8)

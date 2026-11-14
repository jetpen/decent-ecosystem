# `decent-social` ecosystem component decomposition

Status: provisional conceptual decomposition; component boundary and repository destination unresolved

Ecosystem design sources: [Social Graph and Web-of-Trust vision](https://github.com/jetpen/decent-ecosystem/issues/13), [identity-linked Social Graph and Web-of-Trust protocol](../protocol/identity-linked-social-graph-and-web-of-trust.md), and [Social Graph protocol handoff](https://github.com/jetpen/decent-ecosystem/issues/27)

Repository: **unresolved**. The requested GitHub path `jetpen/decent-social` is not listed in the authenticated `jetpen` repository listing and returns 404; the local `/home/ben/projects/decent-social` directory has no commits and no configured remote. Do not treat that path as a verified component repository link.

## Claim classes

- **Implemented/code-backed** — present in an identified component repository or supported by its recorded tests/evidence.
- **Researched but unimplemented** — established by research but not implemented or qualified in a component.
- **Proposed ecosystem design** — defined as a protocol convention or conceptual boundary, but not demonstrated as a service implementation.
- **Long-term vision** — beyond the current protocol/MVP or not yet selected.

## Current status and scope

**[Proposed ecosystem design]** The ecosystem has a versioned Social Graph and Web-of-Trust protocol describing two digest-addressed JSON Storage Object families: owner-authored Social Graph snapshots and issuer-authored Trust Assertions collections. The protocol explicitly states that these are proposed object conventions, not implemented Registry record families or companion services. It provides schemas, conformance fixtures, and application-owned evaluation boundaries; it does not establish that a `decent-social` service or repository implements them.

**[Implemented/code-backed]** `decent-registry` supports signed Identity Records and Provider Records, including the recorded Provider Record withdrawal/tombstone behavior. Registry stores and resolves signed discovery metadata; it does not store or serve the Social Graph or Trust Assertions JSON object content. This is integration context only, not evidence that a Social service exists.

## Provisional component purpose

**[Proposed ecosystem design]** If `decent-social` is established as a distinct component, its provisional responsibility is to implement social-application behavior that consumes identity-linked Social Graph and Trust Assertions objects. The exact product surface and component boundary are not specified by the ecosystem protocol. A future component design may define user-facing relationship management, graph object creation/publication, trust assertion presentation, and application-specific discovery/evaluation, but none of those are implied as current repository capabilities.

The protocol-level objects and flows are not a mandate for a centralized service. A `decent-social` implementation could be one application or client of the portable conventions; it must not make itself the canonical owner of users' graph data or a universal trust authority by virtue of that role.

## Protocol objects and boundaries

**[Proposed ecosystem design]**

- A Social Graph Storage Object is an owner's JSON snapshot of directed relationship entries. Each entry identifies a subject by public key and carries an application-defined predicate and optional context.
- A Trust Assertions Storage Object is an issuer-authored collection whose entries identify a subject public key and an application-defined purpose. A relationship and a trust assertion are distinct object families and meanings.
- The objects are content-addressed by SHA-256 of their exact stored UTF-8 JSON bytes and retained by an External Storage Provider. They are not Registry Records.
- A Provider Record points to an external object by digest and location and authenticates Registry metadata under Registry's existing signing rules. It does not sign the referenced JSON bytes.
- Foundational Registry resolution begins with a known digest. The protocol requires no owner-key-to-graph lookup, global search index, or canonical discovery service. An application-specific account/storage object or other application-specific mechanism may supply the digest.
- Registry absence, Registry unavailability, external-object inaccessibility, malformed content, digest mismatch, unsupported schema, conflicting revisions, and unverified identity are distinct observations. Applications decide their acceptance and recovery behavior.

These rules are defined in the [protocol specification](../protocol/identity-linked-social-graph-and-web-of-trust.md), not as claims about a `decent-social` implementation.

## Responsibility split

**[Proposed ecosystem design]**

- **User / graph owner:** authors their own directed relationship statements and controls any publication decisions within the selected application.
- **Assertion issuer:** authors statements about a subject for a stated application-defined purpose. A subject's consent is not implied by another party's assertion.
- **`decent-social`, if implemented:** may provide application-specific user experience and local policy for managing or consuming these conventions. It must not imply a protocol-defined global relationship directory, evaluator, or accepted-trust result.
- **`decent-identity`:** resolves exact identifier-to-key bindings through Registry; lookup does not authenticate a user, discover a graph, or establish continuity between replacement keys.
- **`decent-registry`:** validates, stores, and resolves authorized signed Registry metadata, including Provider Records; it does not retain Social Graph/Trust Assertions content or decide its application meaning.
- **`decent-simple-storage` / another External Storage Provider:** retains and serves the external JSON bytes under its own service contract. It is a custodian, not the owner, trust evaluator, or Registry.
- **Consuming application:** chooses what digests to retrieve, which observations to enforce, whether to consider graph edges, how to interpret assertions, and what local decision follows.

## Interpretation, authenticity, and identity limits

**[Proposed ecosystem design]** A graph edge is an owner's statement; it does not imply that the subject recognizes, reciprocates, consents to, or was notified of the relationship. A Social Graph edge is not trust evidence by default. An application may choose to use it under disclosed local policy.

A Trust Assertion is an issuer's purpose-scoped statement, not standardized truth, reputation, competence, or a universal score. Protocol v1 does not require a cryptographic signature over the JSON object bytes. Owner/issuer public-key fields in the JSON are claims, not proof of authorship. Registry Provider Record signatures authenticate Registry metadata only.

A replacement public key is not presumed to control the same identity's graph or assertions. Continuity requires explicit evidence under the ecosystem identity/key-continuity boundary; a reused label or name alone is insufficient. A valid signature, where independent evidence exists, does not itself prove signing time, historical authorization, current status, real-world uniqueness, truth, or safety.

No protocol-defined path evaluator, trust score, threshold, ranking, search bound, access-control rule, or automatic transitivity exists. Each application owns those choices and must not present its local evaluation as a universal ecosystem judgment.

## Privacy and withdrawal limits

**[Proposed ecosystem design]** The v1 object profile assumes unencrypted JSON and does not define bearer-token access control at the External Storage Provider. Anyone who can access the external location can read the object. Publishing or withdrawing a Provider Record affects discovery through that Registry record, not confidentiality of known or copied bytes. Withdrawal cannot delete the external object, erase Registry history, remove caches, or retract prior copies, and propagation is not guaranteed to be immediate or global.

Consent to publish, access, and reuse are distinct concerns, but the protocol defines no permission fields or enforcement mechanism. Selective disclosure, encryption, and metadata minimization are not v1 requirements or guarantees. The protocol does not prohibit other parties from making independent statements about a subject.

## Non-goals

**[Long-term vision or out of scope]** This provisional decomposition does not establish:

- an implemented `decent-social` service, API, repository layout, product, or release;
- a canonical social network, global profile, mandatory graph host, or owner-key search/index;
- Registry storage or serving of graph/assertion content;
- required object-content signatures or proof of real-world identity;
- a universal Web-of-Trust algorithm, score, ranking, endorsement meaning, or access decision;
- automatic transitivity from relationships to trust;
- confidentiality, access control, encryption, deletion, erasure, or global withdrawal guarantees;
- application-specific feeds, moderation, discovery UX, or policy.

## Handoff questions

**[Researched but unimplemented]** Before treating `decent-social` as an implementation component, the owners must identify and verify its canonical repository URL, establish its purpose and distinct capability/data/trust boundaries, and decide which social-app functions (if any) it owns. The current public repository lookup did not establish a `jetpen/decent-social` repository.

The owners of a future implementation should also resolve:

- how an application obtains a known graph/assertion digest without adding a protocol-required global index;
- whether graph and assertion content is created/stored directly by the user or through an application, and how publication consent is represented;
- how object authorship will be presented given that v1 does not require content signatures;
- how local application policy distinguishes relationship statements, assertions, evidence, current Registry observations, and unresolved identities;
- which privacy/access model applies beyond the v1 public-readable object assumption;
- how a client treats schema versions, conflicting revisions, unavailable services, withdrawal, and replacement keys;
- what acceptance evidence is needed for any claimed graph or trust behavior, distinct from offline schema/fixture validation.

## Provenance

- **Repository verification:** `gh repo list jetpen` did not list `decent-social`; `gh repo view jetpen/decent-social` reported that the repository could not be resolved. The similarly named local directory is empty (`No commits yet on main`) and has no configured remote. A similarly named third-party project was not treated as the requested component.
- [Ecosystem Social Graph/Web-of-Trust vision and component handoff](https://github.com/jetpen/decent-ecosystem/issues/13)
- [Domain-model decision](https://github.com/jetpen/decent-ecosystem/issues/14)
- [Identity/key continuity decision](https://github.com/jetpen/decent-ecosystem/issues/20)
- [Social Graph and Web-of-Trust protocol](../protocol/identity-linked-social-graph-and-web-of-trust.md)
- [Protocol authoring and conformance handoff](https://github.com/jetpen/decent-ecosystem/issues/27)
- [Decentralized identity/relationship/trust prior-art research](../research/identity-relationships-trust-assertions.md)

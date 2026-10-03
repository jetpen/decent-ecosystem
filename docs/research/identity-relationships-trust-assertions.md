# Standards and prior art: identity-linked relationships and trust assertions

- **Research ticket:** [#19 — Research standards and prior art for decentralized identity-linked relationships and trust assertions](https://github.com/jetpen/decent-ecosystem/issues/19)
- **Wayfinder map:** [#13 — Identity-centered social graph and web of trust vision](https://github.com/jetpen/decent-ecosystem/issues/13)
- **Research branch:** `research/identity-relationships-trust-assertions`
- **Ecosystem base:** `jetpen/decent-ecosystem` `main` at `6c7b06142f855534711a1d36be03ea2389cc037c`
- **Registry context inspected:** `jetpen/decent-registry` `main` at `3e561bbdaf7c6da85528a717dd555445d5e7dff7`
- **Scope:** Comparative research from primary standards and project source documents. This artifact does not select schemas, wire formats, transports, identity methods, trust calculus, or implementation architecture.

## Summary

The source set has useful **complementary** parts, but no single standard covers the requested portable social graph + scoped trust assertions + publication/discovery + withdrawal + trust-path evaluation lifecycle.

- **DID Core** gives a common decentralized-identifier model and key-purpose relationships. It does not standardize a social graph, a generic trust assertion vocabulary, or trust evaluation.
- **Verifiable Credentials (VC) Data Model 2.0** gives issuer/subject/holder/verifier roles, a general claims container, integrity/status hooks, and an explicit limit: successful verification is not proof that claims are true. Credential status scheme and evaluation are deliberately left to extensions and verifier policy.
- **ActivityStreams 2.0** has a generic `Relationship` object and `Follow` activity vocabulary. **ActivityPub** adds federated delivery and `Follow`/`Accept`/`Undo` flows. These model social interactions and subscriptions, not trust endorsements; `Follow` is interest in an actor’s activities, not necessarily a mutual connection or endorsement.
- **OpenPGP RFC 9580** has an actual certification / introducer trust-signature mechanism with revocation and trust-depth/amount fields. It is tied to OpenPGP key/User ID certification and includes local trust state that is not ordinarily exported; it is not a general cross-domain, scoped assertion or universal trust algorithm.
- **RFC 9421 HTTP Message Signatures** signs selected HTTP message components. It is useful precedent for message authenticity/integrity and freshness/replay metadata, but is not a persistent relationship/assertion data model or a trust-path scheme.
- The current Registry offers signed, ordered identity/provider records and DHT discovery, while its companion-service document calls Identity Graph and Social conventions proposed and says no social graph protocol is implemented. Existing project notes do not describe a deployed trust-assertion facility.

Together these sources suggest a protocol-design space with separable concerns—stable subject/key references; relationship/claim meaning; proof; publication and discoverability; status/withdrawal; and application evaluation—but that decomposition is descriptive, not a project design decision.

## Project context and status

**Documented/code-backed project baseline.** Registry source documentation describes Identity Records binding owner-name bytes to an Ed25519 public key, canonical-CBOR signed updates/envelopes, sequence ordering and owner binding; Provider Records carry discovery metadata. These are Registry record mechanisms, not social edges or attestations about another subject. Sources: [Registry CONTEXT.md](https://github.com/jetpen/decent-registry/blob/3e561bbdaf7c6da85528a717dd555445d5e7dff7/CONTEXT.md), [protocol concepts](https://github.com/jetpen/decent-registry/blob/3e561bbdaf7c6da85528a717dd555445d5e7dff7/docs/protocol-concepts.md), [companion services](https://github.com/jetpen/decent-registry/blob/3e561bbdaf7c6da85528a717dd555445d5e7/docs/companion-services.md).

**Proposed, not implemented.** Registry companion-services docs describe Identity as a proposed convention over related records and Social as a proposed convention for owner-authored relationships referencing Identity Records; no social graph protocol is implemented. The ecosystem’s [decent-identity component handoff](https://github.com/jetpen/decent-ecosystem/blob/6c7b06142f855534711a1d36be03ea2389cc037c/docs/components/decent-identity.md) also says DID methods, identity graphs, aliasing, recovery, and portability are not current MVP operations. This status matters: standards examples below are prior art, not descriptions of shipped decent services.

**Wayfinder decisions already settled.** Map #13’s notes and resolved issues [#14](https://github.com/jetpen/decent-ecosystem/issues/14), [#15](https://github.com/jetpen/decent-ecosystem/issues/15), [#16](https://github.com/jetpen/decent-ecosystem/issues/16), and [#17](https://github.com/jetpen/decent-ecosystem/issues/17) distinguish directed owner-authored social relationships from issuer-authored, directed, scoped trust assertions; state that signatures authenticate authorship, not truth; keep trust interpretation and access/reputation decisions with applications; reject an automatic global score/transitivity; and require privacy/consent limits. Findings below do not reopen or alter those decisions.

## Comparative mechanisms

| Concern | Primary-source mechanism | What it establishes | Main limits for this use |
|---|---|---|---|
| Identity reference and keys | [DID Core 1.0](https://www.w3.org/TR/did-1.0/) | DID subject, DID Document, verification methods and purpose-specific verification relationships | DID methods define resolution/control details; Core does not define a relationship graph or trust calculus. A DID or key proof alone does not establish a unique human or claim truth. |
| Claim/assertion envelope | [VC Data Model 2.0](https://www.w3.org/TR/vc-data-model-2.0/) and [Data Integrity 1.0](https://www.w3.org/TR/vc-data-integrity/) | Issuer makes claims about subject; credential can be cryptographically integrity-protected and verified; holder can present to verifier | Meaning, issuer acceptability, truth assessment and many status details depend on verifier rules/extensions. Credential model is broader than lightweight social edges. |
| Relationship vocabulary | [ActivityStreams 2.0 Vocabulary](https://www.w3.org/TR/activitystreams-vocabulary/) | `Relationship` reifies subject–predicate–object; `Follow` names a directed activity | Vocabulary alone does not specify a signed portable assertion, privacy policy, resolution, or generalized trust. |
| Federated publication/lifecycle | [ActivityPub](https://www.w3.org/TR/activitypub/) | Client/server and federated-server API; Follow, Accept/Reject, Following/Followers collections, Undo | Social subscription semantics rather than endorsement; collection exposure may be filtered; servers and replication can retain earlier copies; Undo only reverses effects to the extent possible. |
| Trust-path precedent | [OpenPGP RFC 9580](https://www.rfc-editor.org/rfc/rfc9580.html) | User-ID certification signatures, trust-signature depth/amount, certification revocation | Specific to OpenPGP key and User ID structures; trust decisions/local trust packet semantics are implementation/user context, not general interoperable application policy. |
| Transport-message proof | [HTTP Message Signatures, RFC 9421](https://www.rfc-editor.org/rfc/rfc9421.html) | Signature over selected canonicalized HTTP components, with key identifier and optional time/expiry/nonce metadata | Signs HTTP messages, not a reusable semantic graph or assertion; key resolution, acceptable age and replay policy depend on application. |

### 1. Identity and verification-key references

**DID Core (W3C Recommendation, 19 July 2022).** [DID Core](https://www.w3.org/TR/did-1.0/) defines a DID syntax, DID Documents, verification methods and verification relationships. The `authentication` relationship indicates methods expected for authentication; `assertionMethod` indicates methods the DID subject uses to express claims, e.g. issuing a VC. Verifiers check that the verification method is authorized for the proof purpose, not merely present in the document ([verification relationships](https://www.w3.org/TR/did-1.0/#verification-relationships), [`assertionMethod`](https://www.w3.org/TR/did-1.0/#assertion)). DID Core’s abstract architecture leaves DID-method operations and the mechanism that resolves a DID to its document to the method/resolution ecosystem; different methods therefore have different control, update, recovery, and availability properties. It is an identity/key-reference layer, not a portable Social Graph schema or a claim-evaluation policy.

**Local contrast.** The Registry uses its own owner-name-to-public-key Identity Record and record-update conventions (including monotonic `seq` and current Owner-Key Rotation validation), not DID syntax or DID resolution. The project’s companion-service text treats aliases/Identity Graph as proposed. An adapter between DIDs and Registry records would require explicit choices about identifier equivalence, key history, and proof-purpose mapping; the cited standards do not supply that mapping.

### 2. Signed assertion data and claim semantics

**VC Data Model 2.0 (W3C Recommendation, 15 May 2025).** [VC Data Model](https://www.w3.org/TR/vc-data-model-2.0/) is a general model for issuer claims about one or more subjects and a three-party issuer/holder/verifier ecosystem. A credential may carry `issuer`, `credentialSubject`, proof and (optionally) `credentialStatus` material. Crucially, the specification says verification of a credential does **not** imply truth of its claims; verifiers apply their own business rules to decide which issuers/claims they rely on ([verification](https://www.w3.org/TR/vc-data-model-2.0/#verification), [status](https://www.w3.org/TR/vc-data-model-2.0/#status)). The `credentialStatus` property is a hook for status information; status formats/protocols are outside the Data Model’s scope and verifiers apply the status-type definition and their own criteria.

**Data Integrity 1.0 (W3C Recommendation, 15 May 2025).** [Data Integrity](https://www.w3.org/TR/vc-data-integrity/) describes proofs securing authenticity/integrity for credentials and similar constrained documents. Concrete cryptographic procedures are supplied by cryptosuites. It is a security mechanism for data, not a meaning vocabulary for relationship edges and not an oracle for factual correctness.

**Fit/limitation.** A VC is a natural comparison for “issuer X asserts scoped claim Y about subject Z,” including proof and status extension points. It does not mandate a social-relationship vocabulary, discoverability, distribution/withdrawal protocol, or an application trust calculus. A verifier’s decision to accept an otherwise valid credential is explicitly application-dependent. VC selective-disclosure capabilities depend on the securing format/cryptosuite, not merely on selecting the VC data model.

### 3. Relationships and social actions

**ActivityStreams 2.0 (W3C Recommendation, 23 May 2017).** The [Activity Vocabulary](https://www.w3.org/TR/activitystreams-vocabulary/) defines a `Relationship` object with `subject`, `relationship` predicate, and `object`, explicitly reifying a relation between entities ([Representing Relationships](https://www.w3.org/TR/activitystreams-vocabulary/#representing-relationships-between-entities)). This is the clearest standard vocabulary analogue for a directed edge/typed relationship statement. Its `Follow` activity instead means that the actor is interested in activities by the object ([Follow](https://www.w3.org/TR/activitystreams-vocabulary/#follow)); it must not be read as evidence of trust or reciprocity.

**ActivityPub (W3C Recommendation, 23 January 2018).** [ActivityPub](https://www.w3.org/TR/activitypub/) uses ActivityStreams and specifies client-to-server and federated server-to-server APIs. A Follow can be accepted or rejected; actor `following` and target `followers` collections track subscriptions ([Follow activity](https://www.w3.org/TR/activitypub/#follow-activity), [collections](https://www.w3.org/TR/activitypub/#actor-objects)). `Undo` can reverse a prior activity such as Follow when the same actor authored both; side effects are undone only “to the extent possible” ([Undo](https://www.w3.org/TR/activitypub/#undo-activity)). The spec permits collection filtering based on privileges/authentication, illustrating that publication need not mean public enumeration.

**Fit/limitation.** ActivityStreams supplies well-known social vocabulary, and ActivityPub a federation/delivery flow. Neither is a generic portable, cryptographically verifiable assertion format for arbitrary trust claims, nor does Follow mean mutual friendship. Undo is event/lifecycle behavior, not a guarantee that all recipients erase already delivered copies. Using ActivityPub mechanisms would imply its actor/server/inbox/outbox model and operations; it would not resolve cross-protocol identity continuity or application trust interpretation.

### 4. OpenPGP certifications, trust signatures, and path evaluation

**OpenPGP (RFC 9580, IETF Standards Track / Proposed Standard, July 2024).** [RFC 9580](https://www.rfc-editor.org/rfc/rfc9580.html) defines transferable key and signature packet formats. Its certification signature types (Sections 5.2.1.1–5.2.1.4) bind a User ID or User Attribute to a public key: a signer testifies to a belief about the association, not a general-purpose judgment over an arbitrary subject. Section [5.2.3.21 Trust Signature](https://www.rfc-editor.org/rfc/rfc9580.html#section-5.2.3.21) adds depth (“level”) and a trust amount (0–255); level 1 names a trusted introducer, higher levels delegate introducer authority, and RFC 9580 describes values below 120 as partial and 120+ as complete trust. Section [5.2.1.13 Certification Revocation](https://www.rfc-editor.org/rfc/rfc9580.html#section-5.2.1.13) defines a revocation signature for an earlier certification, normally from the same issuer key (or deprecated revocation-key mechanism).

The design is specifically a key-identity certification model. OpenPGP Trust packets record a user’s/local implementation’s trust specifications and are normally not exported; their format is implementation-defined (Section 5.10). Therefore a trust path is not an objective, universally agreed score: imported signatures are evidence processed under a user’s trust anchors, local trust settings, validity model, and implementation. The RFC defines signature structures and trust-signature fields but does not prescribe a universal policy for every application or a general typed relationship/assertion object.

### 5. Signing HTTP messages is not signing a graph protocol

**HTTP Message Signatures (RFC 9421, IETF Standards Track / Proposed Standard, February 2024).** [RFC 9421](https://www.rfc-editor.org/rfc/rfc9421.html) defines canonicalization and signatures over selected HTTP message components, carried in `Signature-Input` and `Signature` fields. It supports `keyid`, `created`, `expires`, and `nonce` parameters; the application defines key retrieval/interpretation and what freshness policy to enforce. This is useful transport integrity/authenticity prior art, including replay-risk controls, but it neither defines semantic relationship/assertion fields nor publication, durable record status, consent, or trust-path evaluation. A signed HTTP delivery should not be mistaken for a portable signed object after its HTTP context disappears.

## Lifecycle scenarios compared

These are comparative flows implied by the cited specifications, not a proposal for the project.

### A. Publish and discover a relationship

- **ActivityStreams/ActivityPub path:** an actor can express `Relationship` or issue `Follow`; ActivityPub delivers activities to actor inboxes and manages `following`/`followers` collection effects after the follow response. It has established social vocabulary and federation but server-centered collection/endpoints and subscription semantics. Relationship vocabulary by itself does not standardize global graph querying/discovery, cryptographic proof verification, or privacy policy.
- **DID/VC path:** DID resolution can locate DID Documents and services; a VC can carry a subject claim and proof/status metadata. DID Core does not define a relationships collection; VC does not specify general publication/discovery of all credentials or contacts. These are components, not a ready-made social graph protocol.
- **Registry path:** current signed Registry records resolve by project-defined keys over its DHT, but the source docs classify Social/Identity Graph conventions as proposed. This does not yet supply a documented social-edge schema, access-control model, graph query, or discovery semantics.

### B. Issue, verify, and withdraw a scoped assertion

- **VC path:** an issuer creates a credential with subject claims, secures it under a proof mechanism, and optionally provides `credentialStatus`. A verifier checks authenticity/currentness and then separately judges whether it trusts the issuer and claim. Status has extension-defined data/protocol and verifier-specific criteria; it is not a generic guaranteed erasure/retraction mechanism.
- **OpenPGP path:** a key holder certifies a User ID/key association; a certification revocation can revoke that certification, while a Trust Signature delegates bounded-depth introducer trust. The claim domain is narrower than arbitrary scoped assertions, and local trust state/policy remains significant.
- **ActivityPub path:** an actor can Undo their Follow; this is a social action reversal, not withdrawal of another party’s claim or a portable issuer assertion-status registry.
- **General consequence:** withdrawal can signal an issuer’s current position or alter future resolution/acceptance; it cannot ensure that previously disclosed signed material or its copies have vanished. What remains historically valid, whether stale copies can be accepted, how status changes are authenticated and cached, and what recipients retain are separate protocol/application decisions.

### C. Evaluate a trust path

OpenPGP is the direct precedent here: third-party certifications and trust signatures can form introducer chains, but each user/implementation evaluates that graph using its trusted keys and local trust state. The VC model similarly leaves trust in issuers and claim reliance to verifier business rules. DID verification relationships restrict which key can be used for a proof purpose but do not compute trust in that DID’s assertions. ActivityPub social edges/follows do not inherently contribute trust evidence. Thus path construction and acceptance semantics are deliberately not shared across these standards. A consuming application would have to choose trusted roots, scope propagation, path length/attenuation, handling of contradiction/expiry/revocation, and output meaning; none of the standards makes a universal score or transitivity automatic.

## Cross-cutting limitations and unresolved protocol topics

For later protocol work, the sources leave these design questions open without deciding their answers:

1. **Identity and continuity:** Which identifier types refer to issuer/subject, how are aliases/equivalence established, and what proof links old/new keys? DID methods differ; Registry has its own name/key-history rules; ActivityPub uses actors/URLs; OpenPGP uses key/User ID association.
2. **Edge vs. assertion semantics:** How are owner-authored social edges separated from issuer-authored claims, and how are predicate, scope, purpose, audience, evidence, time interval and context represented? ActivityStreams `Relationship` helps describe an edge; VCs help describe issuer claims; neither alone gives all social/trust semantics.
3. **Proof and verification profile:** What data is covered, which proof suite/key purpose is allowed, how is the issuer key resolved, and which profile versions must interoperate? A generic “signature present” rule is insufficient.
4. **Publication and privacy:** Is publication public, selectively disclosed, recipient-specific, or mediated by access control? DID services, DHT lookup, and ActivityPub inbox/collection delivery each expose different metadata and availability models; no cited standard imposes the project’s privacy/consent policy.
5. **Withdrawal, freshness, and history:** Does withdrawing an assertion change a live status endpoint, publish a tombstone/new sequence, or only stop future publication? How are old copies/caches treated? VC status, OpenPGP certification revocation and ActivityPub Undo have distinct semantics and are not interchangeable.
6. **Path policy:** What counts as a trust root, what scopes/depth can be delegated, and how are conflicting/expired/colluding issuers handled? OpenPGP’s trust signatures provide one key-validity-specific precedent but do not decide the application policy.
7. **Interoperability boundary:** Which common identifiers, data contexts/vocabularies, proof suites, content types, resolution methods, status types, and transport profiles would need agreement? Standards that define only syntax or proof primitives still require profiling.
8. **Operational guarantees:** How are replication, DHT/federation availability, stale reads, revocation propagation, endpoint privacy, rate limiting, and abuse reporting handled? A decentralized record or federated delivery mechanism alone does not guarantee confidentiality, availability, truth, or resistance to manipulation.

These are candidates for subsequent protocol-design work. They are not resolutions of those decisions.

## Sources (primary)

### W3C Recommendations

- [Decentralized Identifiers (DIDs) v1.0](https://www.w3.org/TR/did-1.0/) — W3C Recommendation, 19 July 2022. Especially [verification relationships](https://www.w3.org/TR/did-1.0/#verification-relationships) and [`assertionMethod`](https://www.w3.org/TR/did-1.0/#assertion).
- [Verifiable Credentials Data Model v2.0](https://www.w3.org/TR/vc-data-model-2.0/) — W3C Recommendation, 15 May 2025. Especially [verification](https://www.w3.org/TR/vc-data-model-2.0/#verification) and [status](https://www.w3.org/TR/vc-data-model-2.0/#status).
- [Verifiable Credential Data Integrity 1.0](https://www.w3.org/TR/vc-data-integrity/) — W3C Recommendation, 15 May 2025.
- [Activity Streams 2.0](https://www.w3.org/TR/activitystreams-core/) — W3C Recommendation, 23 May 2017.
- [Activity Vocabulary](https://www.w3.org/TR/activitystreams-vocabulary/) — W3C Recommendation, 23 May 2017. Especially [Relationship](https://www.w3.org/TR/activitystreams-vocabulary/#relationship), [Representing Relationships](https://www.w3.org/TR/activitystreams-vocabulary/#representing-relationships-between-entities), and [Follow](https://www.w3.org/TR/activitystreams-vocabulary/#follow).
- [ActivityPub](https://www.w3.org/TR/activitypub/) — W3C Recommendation, 23 January 2018. Especially [Follow](https://www.w3.org/TR/activitypub/#follow-activity) and [Undo](https://www.w3.org/TR/activitypub/#undo-activity).

### IETF RFCs

- [RFC 9580 — OpenPGP](https://www.rfc-editor.org/rfc/rfc9580.html) — Standards Track, Proposed Standard, July 2024. Especially Sections 5.2.1 certification signatures/revocation, 5.2.3.21 Trust Signature, and 5.10 Trust Packet.
- [RFC 9421 — HTTP Message Signatures](https://www.rfc-editor.org/rfc/rfc9421.html) — Standards Track, Proposed Standard, February 2024.

### Project source documents

- [decent-ecosystem `CONTEXT.md`](https://github.com/jetpen/decent-ecosystem/blob/6c7b06142f855534711a1d36be03ea2389cc037c/CONTEXT.md)
- [decent-ecosystem `docs/components/decent-identity.md`](https://github.com/jetpen/decent-ecosystem/blob/6c7b06142f855534711a1d36be03ea2389cc037c/docs/components/decent-identity.md)
- [decent-ecosystem `docs/components/decent-registry.md`](https://github.com/jetpen/decent-ecosystem/blob/6c7b06142f855534711a1d36be03ea2389cc037c/docs/components/decent-registry.md)
- [decent-registry `CONTEXT.md`](https://github.com/jetpen/decent-registry/blob/3e561bbdaf7c6da85528a717dd555445d5e7dff7/CONTEXT.md)
- [decent-registry `docs/protocol-concepts.md`](https://github.com/jetpen/decent-registry/blob/3e561bbdaf7c6da85528a717dd555445d5e7dff7/docs/protocol-concepts.md)
- [decent-registry `docs/companion-services.md`](https://github.com/jetpen/decent-registry/blob/3e561bbdaf7c6da85528a717dd555445d5e7dff7/docs/companion-services.md)

## Research boundary

This report compares mechanisms and limitations only. It does not amend the ecosystem vision, add a production design, close out any protocol question, or assert that any cited external standard is implemented by `decent-ecosystem` or `decent-registry`.

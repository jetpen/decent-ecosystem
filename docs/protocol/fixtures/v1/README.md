# V1 schema and conformance fixtures

This fixture set accompanies [Identity-linked Social Graph and Web of Trust](../../identity-linked-social-graph-and-web-of-trust.md). It is offline protocol-object evidence; it does not exercise the Registry or External Storage Provider.

## Normative schemas

- [`social-graph.schema.json`](../../schemas/social-graph.schema.json) — owner-authored snapshot, directed relationship entries.
- [`trust-assertion.schema.json`](../../schemas/trust-assertion.schema.json) — issuer-authored collection of purpose-scoped assertion entries.

Both are JSON Schema Draft 2020-12. The schema validates object shape and primitive constraints. Stateful checks—monotonic `version`, verifying `previous_digest` equals the fetched immediate predecessor's exact-byte digest, and conflicting revisions—require the companion verifier/stateful checks; standalone JSON Schema cannot dereference external predecessor bytes.

## Fixture organization

- `examples/`: valid v1 objects, v2 object revisions, and v1 objects with ignored unknown fields for both object families.
- `invalid/`: schema-invalid missing fields, malformed keys, invalid version/predecessor field shape, wrong JSON types, and empty required purpose.
- `unsupported/`: a syntactically well-formed object declaring a schema version not supported by this v1 profile. A consumer reports `unsupported-schema-version`; it does not silently reinterpret it as v1.
- `conflicts/`: same parsed Social Graph content and same ID/schema version/revision represented with different exact JSON bytes. The digests differ, so clients that encounter both report conflicting revisions; there is no normalization, merge, or protocol-defined winner.
- `outcome_vectors`: semantic outcomes that a consumer should distinguish; these are not a shared wire enum/status code and do not dictate application acceptance.
- [`verify.py`](verify.py): executable offline verifier for JSON Schema validity, expected digest vectors, exact-byte conflicts, predecessor-chain consistency, unknown-field probes, and outcome-vector completeness. Requires the `jsonschema` Python package.

## Byte and revision rules

Hash the exact stored UTF-8 byte sequence. Do not parse/re-serialize before digesting. A final newline is part of the bytes. Whitespace or key-order changes change the digest, even when JSON values compare equal.

Version 1 has no `previous_digest`. A later revision retains the same stable object ID, increments version by exactly one, and includes the lowercase SHA-256 digest of the immediate predecessor's exact stored bytes. A semantically distinct replacement begins a new ID at version 1. A revision chain does not prove global currentness.

## Conformance boundary

The verifier checks object schemas, both families' ignored-unknown-field probes, the semantic outcome-vector catalog's completeness, exact-byte digests, valid/invalid predecessor-chain checks, and conflicting-revision constraints. Outcome vectors document application/service observations; they do not implement or test a live service-status mapping. Object-profile conformance does not assert that an application trusts or accepts a claim.

Provider Record authorization, withdrawal/tombstone transitions, Registry lookup after withdrawal, and service API/CLI behavior are covered by the `decent-registry` component contract. In particular, these fixtures do not assert network-wide CAS, immediate/global propagation, external-object deletion, history/copy erasure, or mixed-version migration guarantees.

## Scenario traceability

| Destination scenario | Applicable artifacts | What remains application/component-owned |
|---|---|---|
| Publish/discover an identity-linked relationship | Social Graph schema, v1/v2 examples, exact-byte digest vectors | Application supplies the graph digest (for example through an application-specific account/storage object); Registry resolves by known digest; no foundational owner-key search/index. |
| Issue/verify/withdraw a scoped trust assertion | Trust Assertions schema, collection examples, Registry PR #119 | Application supplies the collection digest and interprets purposes; Registry withdrawal semantics and limits are verified by Registry component tests; copies and external content are not erased. |
| Evaluate a path and make an application decision | Both schemas, revision/conflict and outcome examples | Application chooses inputs, whether to include graph edges, policy, verification strictness, evaluation, and decision; no shared evaluator or score. |

The manifest lists 9 semantic outcome vectors. These are documented observation categories, not runnable consumer decisions or executable simulated service responses. A client/service conformance suite may map its own statuses and errors to these categories; these fixtures do not test live network/service outcomes.

## Expected fixture summary

`manifest.json` contains **7 valid/valid-revision cases** (including both families with ignored unknown fields), **7 schema-invalid cases**, **2 invalid stateful predecessor cases** (one with wrong digest, one missing the required predecessor field), **1 unsupported-version case**, **1 conflicting-revision pair**, **9 semantic outcome vectors**, and **4 exact-byte digest vectors**. Stateful checks are called out separately because JSON Schema alone cannot compare object revisions across documents.

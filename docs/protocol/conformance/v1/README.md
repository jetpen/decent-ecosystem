# V1 grant semantic and adapter conformance fixtures

**Semantic profile status: adopted by the user as normative decent Storage grant semantic v1.** This adoption applies to the provider-neutral semantic envelope and vectors only. Keycloak 26.8.0 JCS adapter qualification, WordPress/Storage consumer qualification and the ecosystem aggregate receipt are **not run/not qualified** and are separately gated by [Qualify adopted Storage grant v1 with Keycloak and both first consumers](https://github.com/jetpen/decent-ecosystem/issues/44). No RFC 9068, alternate-AS or forward-compatibility claim.

## Package

- [`grant-envelope.md`](grant-envelope.md): semantic scope, canonicalization and signed-profile distinction.
- [`grant-envelope.schema.json`](grant-envelope.schema.json): strict semantic envelope schema.
- [`adapter-keycloak-26.8.0.json`](adapter-keycloak-26.8.0.json): the prototype-derived RFC 7523 claim mapping and evidence boundary.
- [`manifest.json`](manifest.json): wire/profile identifiers, accepted/rejected semantic vectors, malformed/unsupported cases and current consumer qualification state. It contains 20 semantic vectors, including a mandatory `assertion-sub-mismatch` negative.
- [`fixtures/`](fixtures/): readable RFC 8259 positive/negative data plus the exact JCS canonical payload fixture.
- [`fixtures/assertion-payload.json`](fixtures/assertion-payload.json): unsigned representative RFC 7523 JWT claims payload whose `decent_grant` value is JCS; not a signed token or live adapter proof.
- [`verify.py`](verify.py): checks the illustrative assertion payload, Registry-key fixture bindings, JSON Schema, duplicate members, JCS canonical bytes/digest, semantic vectors and rejection-context consistency; makes no live signature-verification claim.
- [`requirements-test.lock`](requirements-test.lock): hash-locked dependencies for the static verifier.
- [`requirements-test.in`](requirements-test.in): direct verifier dependency inputs.

Run from the `decent-ecosystem` repository root with `uv` and CPython 3.13:

```sh
TEST_ENV="$TMPDIR/decent-grant-conformance-v1"
uv venv "$TEST_ENV" --python 3.13
uv pip install --python "$TEST_ENV/bin/python" --require-hashes --requirement docs/protocol/conformance/v1/requirements-test.lock
"$TEST_ENV/bin/python" docs/protocol/conformance/v1/verify.py
```

The offline verifier checks the illustrative payload, schema/vector consistency, exact subject and JTI bindings, key-field consistency, JCS bytes, duplicate members, and that the fixture explicitly marks live signature verification as not run. Passing is not proof of a real Registry lookup, signature verification, Keycloak behavior, or consumer conformance.

## Contract boundary

The v1 profile requires `iss`, `sub`, `aud`, `exp`, `iat`, and `jti`. RFC 7523 is Standards Track and requires `iss`, `sub`, `aud`, and `exp`; this project profile adds mandatory `iat` and `jti`. The `decent_grant` claim and semantic schema are project-defined, not RFC 7523 claims. JCS applies to the semantic object only, embedded within the normally serialized outer JWT claims set; the single EdDSA JWS signs the exact outer payload bytes.

`fixtures/assertion-payload.json` is an unsigned representative RFC 7523 JWT claims payload, not a JWS artifact; it shows the JCS byte boundary for `decent_grant` inside the normally serialized outer claims set. The offline verifier checks its subject, JTI, embedded envelope and current-key fixture bindings. This adds no live signature/adapter qualification. The mandatory `assertion-sub-mismatch` vector is rejected at the adapter boundary.

## Adapter and qualification status

The adapter JSON contains an **illustrative mapping only** and records #17's pinned source/runtime results as prior evidence: its adapter passed 41 mandatory cases on the prior regular-JWT fixture path. The JCS-profiled payload has not been exercised by the prior run; a real Keycloak positive/negative run is specifically required by [Qualify adopted Storage grant v1 with Keycloak and both first consumers](https://github.com/jetpen/decent-ecosystem/issues/44). Its placeholder/synthetic key and token fields are not signed artifacts, and this adapter profile is not qualified against v1.

Both first consumers must then pin this package revision, run positive/negative adapters, and publish machine-readable reports against immutable revisions. [Qualify adopted Storage grant v1 with Keycloak and both first consumers](https://github.com/jetpen/decent-ecosystem/issues/44) gates those adapter runs and the ecosystem-owned aggregate receipt covering both reports plus the exact Keycloak adapter/image. Future Keycloak releases require a separately requested candidate qualification; there is no forward-compatibility claim. RFC 9068, alternate ASes, numeric TTLs, refresh/revocation policy, and production mTLS/Storage lifecycle remain outside this baseline.

## Acceptance and qualification state

The provider-neutral semantic package is adopted by the user as decent Storage grant semantic v1. The offline verifier proves only internal consistency. Keycloak adapter proof, the WordPress and Storage consumer suites, and an ecosystem-owned aggregate receipt remain separate, unpassed obligations tracked in [Qualify adopted Storage grant v1 with Keycloak and both first consumers](https://github.com/jetpen/decent-ecosystem/issues/44). [Set shared protocol conformance and first-consumer acceptance](https://github.com/jetpen/decent-ecosystem/issues/35) was closed when the review-only package PR merged, before those qualification criteria passed. Preserve its closed historical state; do not treat it as evidence of adapter/consumer conformance.

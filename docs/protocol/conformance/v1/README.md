# V1 grant semantic and adapter conformance fixtures

Status: **Canonical provider-neutral semantic envelope, schema and offline vectors authored and statically verified.** They are an intermediate deliverable for [Wayfinder #35](https://github.com/jetpen/decent-ecosystem/issues/35). Keycloak 26.8.0 adapter requalification against this new JCS envelope, WordPress consumer suite, Storage consumer suite, and aggregate cross-repository receipt are **not run/not qualified**; do not claim #35 complete.

## Package

- [`grant-envelope.md`](grant-envelope.md): semantic scope, canonicalization and signed-profile distinction.
- [`grant-envelope.schema.json`](grant-envelope.schema.json): strict semantic envelope schema.
- [`adapter-keycloak-26.8.0.json`](adapter-keycloak-26.8.0.json): the prototype-derived RFC 7523 claim mapping and evidence boundary.
- [`manifest.json`](manifest.json): wire/profile identifiers, accepted/rejected semantic vectors, malformed/unsupported cases and current consumer qualification state.
- [`fixtures/`](fixtures/): readable RFC 8259 positive/negative data plus the exact JCS canonical payload fixture.
- [`verify.py`](verify.py): strict JSON duplicate-member checks, JSON Schema validation, RFC 8785 canonical-byte and SHA-256 checks, adapter binding invariants, and vector completeness checks.
- [`requirements-test.lock`](requirements-test.lock): hash-locked dependencies for the static verifier.
- [`requirements-test.in`](requirements-test.in): direct verifier dependency inputs.

Run from the `decent-ecosystem` repository root with `uv` and CPython 3.13:

```sh
TEST_ENV="$TMPDIR/decent-grant-conformance-v1"
uv venv "$TEST_ENV" --python 3.13
uv pip install --python "$TEST_ENV/bin/python" --require-hashes --requirement docs/protocol/conformance/v1/requirements-test.lock
"$TEST_ENV/bin/python" docs/protocol/conformance/v1/verify.py
```

Current verified result: **131 checks passed**: 2 valid fixture encodings, 7 schema-invalid cases, 1 semantic-invalid duplicate-member case, 1 duplicate-member rejection, and 19 semantic vectors. This proves local, offline package self-consistency only; it does not run Keycloak, WordPress, Storage, the private Registry verifier, or an end-to-end consumer suite.

## Contract boundary

RFC 8785 JCS is used to derive deterministic bytes for the semantic grant fixture. The RFC 7523 assertion is still a JWS. The selected wallet proof is a single EdDSA JWS Compact signature over the RFC 7515 signing input that wraps the semantic envelope in the Keycloak adapter assertion; there is no separate detached signature. RFC 8785 defines canonical JSON bytes for the vector/payload, not the JWS signing-input formula.

`assertion.aud` targets Keycloak; `decent_grant.storage_aud` targets Storage and is mapped to the output JWT's standard `aud`. `grant_jti` equals the assertion JWT `jti`. Assertion expiry and output access-token expiry must not exceed wallet consent expiry. Exact identifier/audience/purpose/action values are compared without normalization. Provider enrollment, quota, object existence and revocation stay component-owned current state; they are not owner-signed authority claims.

## Adapter and qualification status

The adapter JSON contains an **illustrative mapping only** and records #17's pinned source/runtime results as prior evidence: its adapter passed 41 mandatory cases on the prior regular-JWT fixture path. The new JCS-profiled payload has not been exercised by that run. Its placeholder/synthetic key and token fields are not signed artifacts. A component-owned real Keycloak positive control with this canonical JCS grant, plus negative signature/subject/audience/replay/expiry/outage controls, is required; this adapter profile is **not qualified against this package** yet.

Both first consumers must then pin this package revision, run positive/negative adapters, and publish machine-readable reports against immutable revisions. Only an ecosystem-owned aggregate receipt covering both reports and the exact Keycloak adapter/image can qualify the shared contract. Future Keycloak releases require a separately requested candidate qualification; there is no forward-compatibility claim. RFC 9068, alternate ASes, numeric TTLs, refresh/revocation policy, and production mTLS/Storage lifecycle remain outside this baseline.

## Review status

This directory was created as an approved intermediate package contribution while #35 is open. Treat it as a review draft, not as an adopted protocol or release. The offline verifier passing proves only the internal package/fixture consistency. Before #35 can close, the owner must review/adopt this v1 schema/profile; then the separate Keycloak 26.8.0 JCS-adapter positive/negative proof, WordPress suite, Storage suite, and aggregate qualification receipt are all required.

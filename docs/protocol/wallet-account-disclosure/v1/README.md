# Wallet Account Disclosure v1 — ecosystem package

**Status:** The base profile is normative and was merged in [PR #52](https://github.com/jetpen/decent-ecosystem/pull/52). The native continuation amendment has explicit protocol-owner approval; this change promotes it into the normative package. Issue #51 remains open for consumer conformance, runtime qualification, and independent human security/privacy review.

- [`PROFILE.md`](PROFILE.md): normative profile, including the native Android continuation, wire contract, lifecycle and account-state rules.
- [`schemas/profile.schema.json`](schemas/profile.schema.json): unchanged browser-compatible JSON Schema 2020-12 definitions for account request/context, Owner-Key binding, OID4VP Request Object/DCQL, direct-post response, self-issued credential and holder-bound VP.
- [`native-continuation.schema.json`](native-continuation.schema.json): additive, closed native request/context/binding and vector schemas; browser-only schemas remain unchanged.
- [`vectors/valid-signup.json`](vectors/valid-signup.json), [`vectors/valid-signup-optional-omitted.json`](vectors/valid-signup-optional-omitted.json), and [`vectors/valid-signup-recovery.json`](vectors/valid-signup-recovery.json): unchanged base positive end-to-end vectors for new signup, optional-claim omission, and fresh-proof account creation for an enabled existing Keycloak identity with no RP account.
- [`vectors/valid-request-iss-ignored.json`](vectors/valid-request-iss-ignored.json) and [`vectors/valid-extensions-ignored.json`](vectors/valid-extensions-ignored.json): unchanged base receiver-compatibility positives.
- [`vectors/negative.json`](vectors/negative.json): unchanged 29-case base negative vector set.
- [`vectors/continuation_vectors.native.json`](vectors/continuation_vectors.native.json): separately signed native positive cases and native continuation negatives; does not rewrite base browser-only fixtures.
- [`verify.py`](verify.py): offline verifier for the unchanged base vectors.
- [`verify_native_continuation.py`](verify_native_continuation.py): offline native verifier that reuses complete base validation over original signed bundles.
- [`generate_native_continuation.py`](generate_native_continuation.py) and [`test_native_continuation.py`](test_native_continuation.py): portable native vector generator and regression tests.
- [`requirements-test.in`](requirements-test.in) and [`requirements-test.lock`](requirements-test.lock): pinned/hash-locked verifier dependencies.
- [`ACCEPTANCE-MAP.md`](ACCEPTANCE-MAP.md): issue acceptance criteria mapped to normative artifacts and outstanding component/security gates.
- [`DESIGN-PROPOSAL.md`](DESIGN-PROPOSAL.md): superseded historical base proposal; `PROFILE.md` is normative.

## Run

```sh
uv venv .venv
uv pip install --python .venv/bin/python --require-hashes -r requirements-test.lock
.venv/bin/python verify.py
.venv/bin/python verify_native_continuation.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v test_native_continuation
```

All test keys and certificates in the vectors are public test material. The certificate vector uses an explicitly pinned self-signed test trust anchor; it is **not** a production trust chain. Vectors have no private signing keys and the verifier performs no network access.

Passing both offline verifiers means only that the fixed public vectors and their implemented checks pass. It does not qualify production wallet UI, encrypted pending-state storage, live OIDC, Keycloak/Registry integration, RP account-creation atomicity, cross-node replay protection, privacy telemetry, or component-level behavior. Wallet, Keycloak and first-RP consumers must run these unchanged vectors in their owning repositories. Independent human security/privacy review and component qualification remain required before issue #51 can close.

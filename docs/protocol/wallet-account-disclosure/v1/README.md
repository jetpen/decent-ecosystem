# Wallet Account Disclosure v1 — ecosystem package

**Status:** Adopted as the normative v1 profile by the protocol owner. The profile is committed on [PR #52](https://github.com/jetpen/decent-ecosystem/pull/52) but not yet merged. The live [ecosystem issue #51](https://github.com/jetpen/decent-ecosystem/issues/51) remains open for merge and component qualification.

- [`PROFILE.md`](PROFILE.md): adopted normative profile, wire contract, lifecycle and account-state rules.
- [`schemas/profile.schema.json`](schemas/profile.schema.json): JSON Schema 2020-12 definitions for account request/context, Owner-Key binding, OID4VP Request Object/DCQL, direct-post response, self-issued credential and holder-bound VP.
- [`vectors/valid-signup.json`](vectors/valid-signup.json), [`vectors/valid-signup-optional-omitted.json`](vectors/valid-signup-optional-omitted.json), and [`vectors/valid-signup-recovery.json`](vectors/valid-signup-recovery.json): positive end-to-end vectors for new signup, optional-claim omission, and fresh-proof account creation for an enabled existing Keycloak identity with no RP account; all include distinct Owner-Key credential/VP JWSs and a `direct_post` response/reply. The signed requests deliberately place optional `email` before required `given_name`, exercising original-order claim-set construction with both inclusion and omission of the optional claim.
- [`vectors/valid-request-iss-ignored.json`](vectors/valid-request-iss-ignored.json): fourth positive, a receiver-compatibility case with an RP-signed OID4VP request containing an unrelated `iss`. V1 senders MUST omit this member, but Wallets MUST ignore it if present; RP authentication still uses the certificate-bound `client_id`, not `iss`.
- [`vectors/valid-extensions-ignored.json`](vectors/valid-extensions-ignored.json): fifth positive, receiver compatibility for unknown parameters in the outer request, signed Request Object, client metadata, DCQL root/Credential Query/Claim Queries/format metadata, Authorization Response, and endpoint JSON reply. These do not widen consent or change any validated binding. Unsupported `transaction_data` is rejected by separate negatives.
- [`vectors/negative.json`](vectors/negative.json): 29 cryptographically signed or malformed negative vector cases.
- [`verify.py`](verify.py): offline verifier for nested credential/VP signatures, JCS, JSON Schema (including claim-ID uniqueness and at least one required claim), UTF-8 claim-value byte limit, exact transaction/claim binding, full compact-JWS size, certificate fixture, direct-post response shape, and negative rejection categories.
- [`requirements-test.in`](requirements-test.in) and [`requirements-test.lock`](requirements-test.lock): pinned/hash-locked verifier dependencies.
- [`ACCEPTANCE-MAP.md`](ACCEPTANCE-MAP.md): issue acceptance criteria mapped to ecosystem artifacts and outstanding gates.
- [`DESIGN-PROPOSAL.md`](DESIGN-PROPOSAL.md): superseded proposal; `PROFILE.md` is the adopted normative profile.

## Run

```sh
uv venv .venv
uv pip install --python .venv/bin/python --require-hashes -r requirements-test.lock
.venv/bin/python verify.py
```

All test keys and certificates in the vectors are public test material. The certificate vector uses an explicitly pinned self-signed test trust anchor; it is **not** a production trust chain. Vectors have no private signing keys and the verifier performs no network access.

A passing ecosystem verifier means only that the fixed public vectors and the implemented checks in `verify.py` pass. It does not qualify production wallet UI, encrypted pending-state storage, live OIDC, Keycloak/Registry integration, RP account-creation atomicity, cross-node replay protection, privacy telemetry, or component-level behavior. Wallet, Keycloak and first-RP consumers must run these unchanged vectors in their owning repositories. Independent human security/privacy review and component qualification remain required before issue #51 can close.

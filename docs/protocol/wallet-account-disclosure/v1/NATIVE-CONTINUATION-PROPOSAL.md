# Native wallet continuation amendment proposal for `decent-account-disclosure-v1`

**Status: unadopted proposal for protocol-owner review.** This document proposes a narrowly scoped additive amendment to the adopted v1 profile. It is not normative and does not authorize v1 consumer conformance claims for the native continuation. The existing adopted [`PROFILE.md`](PROFILE.md), schema, and vectors remain authoritative unless the protocol owner explicitly adopts this amendment and updates the profile. The canonical owner decision is open ecosystem [#51](https://github.com/jetpen/decent-ecosystem/issues/51); full native signup in wallet [#66](https://github.com/jetpen/decent-wallet/issues/66) is blocked on that decision. Wallet #62's already-implemented core stays within the existing profile contract.

This proposal does not change `decent-wallet-login-v1`, OID4VP credential or presentation bytes, browser-only v1 request/context bytes, existing signup/recovery rules, RP trust model, or Keycloak Owner-Key verification. It adds a native-only continuation capability so the Android wallet can retrieve the already-defined RP-signed OID4VP request after the RP has validated successful OIDC, without browser-to-app handoff or a bearer capability in a URL.

## 1. Roles and boundaries

- **Keycloak** remains the wallet-proof and current Registry Owner-Key verifier. It owns the wallet transaction, binds the RP request/action and OIDC AuthenticationSession, and issues a capability only for an explicitly enabled native-continuation transaction.
- **Wallet** reads the validated context, obtains one owner approval, submits the unchanged four-field proof, durably stores the returned capability inside the existing authenticated wallet-container v2 pending-approval record, then polls the RP. It never receives an OIDC code, token, or browser callback.
- **RP** is a registered confidential OIDC client for native opt-in. Its OIDC callback is server-side. It validates Code + PKCE and the ID token/binding, then retains only the continuation capability hash with transaction binding, expiry, and continuation state for polling. The capability-bearing ID token MUST NOT be persisted: retaining that token would also retain the raw capability. Raw capability bytes and that token exist only transiently during callback processing and are discarded after validation and hash verification. The RP then exposes only the already-defined signed OID4VP Request Object via the wallet-poll resource. It still delivers the direct wallet presentation at the fixed `response_uri` defined by the adopted profile.
- **Browser** stays with the initiating RP/Keycloak session. No app link, browser-to-wallet continuation URL, or bearer capability is added.

The binding statement still does not prove to the Wallet that the RP validated OIDC. The adopted trust assumption remains: the RP MUST issue its OID4VP continuation only after successful OIDC validation; RP-owned tests must prove this order. This proposal adds no Keycloak OIDC-completion receipt.

## 2. RP request opt-in and client policy

A browser-only RP transaction omits `decent_native_continuation` and remains byte-for-byte compatible with existing v1 requests and context responses. A native-capable RP MAY add this member to the otherwise closed `decent_account_request`:

```json
{
  "profile": "decent-account-disclosure-v1",
  "request_id": "<request-id>",
  "purpose": "Create a site account at Example Site",
  "claims": [
    {"id": "urn:decent:account:v1:given_name", "required": true}
  ],
  "decent_native_continuation": true
}
```

If present, it MUST be the JSON boolean `true`; false, null, string, number, or other values are invalid. The `nativeAccountRequest` schema validates opted-in requests only and requires this literal-true member. Browser-only requests omit it and use the unchanged adopted closed `accountRequest` schema; consumers select the variant from the explicit opt-in rather than validating browser-only requests against the opted-in schema. The RP MUST sign it within the existing ES256 JAR Request Object. Keycloak MUST accept it only when the registered client is confidential and explicitly configured to enable native continuation. The RP MUST opt in only when it can use a server-side registered callback, process code/token server-side without persisting the capability-bearing ID token, and retain only a hash of the continuation capability after callback validation. The context response carries `decent_native_continuation: true` only for a validated opted-in native request; browser-only contexts omit the member and remain byte-for-byte identical to adopted v1. The wallet compares the marker to the signed RP request if that request is available in the local transaction proof and MUST NOT infer `true` from absence.

For native Android signup/recovery, `decent_native_continuation` MUST be exactly `true`. If it is false or absent, Android MUST abort before consent and proof rather than downgrade to no-disclosure login or use an unapproved browser-only path. Browser-only consumers may continue using existing v1 behavior when the marker is absent.

## 3. Wallet-login disclosure-context HTTP result

The existing wallet-login GET response remains exactly `{profile,challenge,csrf_token}`. The disclosure context remains a separate same-origin read-only endpoint:

`GET /realms/{realm}/decent-wallet-login/v1/transactions/{handle}/disclosure-context`

For a valid pending `login` transaction, Keycloak returns **HTTP 204 No Content**, no body. For a valid pending `signup` or `signup_recovery` transaction whose signed RP request opted into native continuation, Keycloak returns **HTTP 200** with the exact adopted context schema plus `decent_native_continuation: true`. For a valid pending signup/recovery transaction whose request omitted the marker, it returns the exact adopted context response unchanged, with no marker. The marker is never returned as `false`; it is absent for browser-only flows. A present marker is valid only with value `true`, and any other value is a generic invalid-context error. No capability is returned from this GET. Responses include `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, `Content-Type: application/json` when a body exists, and no redirect.

Malformed, unknown, expired, consumed, cross-client, or mismatched handle/context requests return one generic **HTTP 404** with an empty body and no-store/no-referrer policy. A native wallet MUST treat every response other than the exact valid login 204 or valid signup/recovery 200 context containing literal `true` as an error. A missing or invalid context MUST NEVER downgrade a signup/recovery attempt to login. The endpoint returns no OIDC token, proof, Registry record, owner key, capability, or claim value.

## 4. Capability creation and native proof POST

A native-continuation capability is 32 independent bytes from the Keycloak CSPRNG, encoded base64url without padding. It is not the QR handle, login challenge, request ID, transaction ID, OIDC state/nonce, OID4VP state/nonce, JTI, or wallet proof. It is a bearer credential solely for the RP continuation GET.

For a valid native-opted `signup` or `signup_recovery`, only a **native** proof POST may win the existing wallet transaction and receive the capability. Here “native” is a transport classification, not cryptographic app attestation: the request has no `Origin` and no Fetch Metadata headers. Capability release is additionally bound to the winning request carrying the valid owner-signed proof. A browser-origin proof POST against such a transaction returns HTTP 403 with an empty no-store response, before consuming or mutating the transaction. It never receives a capability. Browser-only requests preserve their current behavior and receive no capability.

The winning native signup/recovery proof POST returns HTTP 200, `Content-Type: application/json`, `Cache-Control: no-store`, with exactly:

```json
{
  "profile": "decent-account-disclosure-v1",
  "decent_account_continuation_capability": "<32-byte-base64url-no-pad>",
  "expires_at": 1800000299
}
```

`expires_at` is integer Unix seconds and MUST be no later than the minimum of the Keycloak transaction/context expiry and 300 seconds after the proof is accepted. It MUST be later than the current Keycloak server time. The Wallet MUST further cap local use at the earlier persisted wallet-approval expiry. The RP's signed OID4VP Request Object `exp` MUST be an integer no later than both the capability expiry and Keycloak binding JWS `exp`; the RP MUST sign that bounded expiry into the immutable Request Object before making the continuation ready. The shared vector verifier checks the signed Request Object expiry against both values and includes boundary negatives for an expiry beyond either ceiling. No capability or expiry appears in a URL, redirect, browser-visible page/storage, logs, telemetry, or Keycloak's accepted-status body. An identical accepted-proof retry returns status only; it MUST NOT return or re-mint the capability. If the winning response is lost before durable wallet storage, the wallet MUST start a fresh end-to-end wallet-login transaction with new proof and owner approval. The fresh attempt MUST satisfy the existing `signup` or `signup_recovery` action/principal preconditions; if the prior attempt changed principal state so that they no longer hold, Keycloak MUST fail closed and require the caller to follow the existing recovery policy. There is no capability-recovery path, same-transaction retry, or browser fallback.

The proof-consume race remains the one-winner primitive of the existing wallet-login profile. For an opted-in transaction, Keycloak MUST issue neither an OIDC result nor capability unless it has won proof consumption and durably recorded/read back the accepted proof digest, capability hash, expiry, and private transient AuthenticationSession note required for one-time ID-token issuance. Any failed or uncertain write/readback fails closed; no browser-only fallback is permitted, and a fresh login is required. Durable transaction state stores the capability hash, never the raw value. The raw capability may exist only in a private, expiring Keycloak AuthenticationSession note until it is included in the one-time RP ID token; Keycloak then clears the note. Clear it on cancellation, failure, expiry, and terminal authentication cleanup.

## 5. Keycloak binding and RP server-side OIDC callback

For native opt-in only, the Keycloak-signed Owner-Key binding JWS adds exactly:

```text
continuation_capability_hash = BASE64URL_NOPAD(SHA-256(DECODE_BASE64URL_NOPAD(continuation_capability)))
```

The binding JWS `exp` MUST be no later than capability `expires_at` and retains the adopted profile's existing lifetime, audience, identity, action, transaction, request, nonce, and key-binding requirements. The outer OIDC ID token adds two top-level claims only for the opted-in native transaction:

- `decent_account_continuation_capability`: exact raw 32-byte capability, base64url-no-pad;
- `decent_account_continuation_expires_at`: same integer `expires_at` returned to the winning wallet POST and bound by the nested statement.

The normal OIDC ID-token signature algorithm remains governed by the configured client/provider OIDC policy. The RP MUST validate the ID token, the nested binding signature and all existing profile relationships, then compute SHA-256 over the decoded capability bytes and compare its base64url-no-pad encoding with `continuation_capability_hash`. The POST expiry and top-level capability-expiry claim MUST match; the signed binding expiry MUST be no later than that value, not necessarily equal to it. The Request Object expiry MUST be no later than both. The ordinary ID token retains the adopted time-validity rule, without inheriting the binding/capability's 300-second lifetime ceiling. The capability has at least 256 bits of entropy; comparisons use constant-time byte comparison.

The request MUST be a confidential Authorization Code request with `response_type=code`, `response_mode=form_post`, PKCE using `S256`, and the exact registered server-side callback URI. The RP callback binds `state` to the RP's initiating transaction, redeems the authorization code over TLS using the exact stored PKCE verifier and confidential-client authentication, and validates the ID token's signature/algorithm, issuer, audience/`azp` where applicable, time/expiry and nonce plus the Owner-Key binding. It verifies the capability claim against the binding hash and stores only `SHA-256(capability)`, transaction binding, expiry, and continuation state durably. Raw capability bytes may exist only transiently while processing the callback and MUST be discarded immediately after the hash is computed and verified; they MUST NOT be persisted, logged, or returned to browser script or the wallet. Poll authorization hashes the presented header capability and compares it to the stored hash in constant time. The callback then responds with a clean same-origin redirect after removing code/state from the visible URL. No code, token, or capability may be placed in a query/fragment, browser storage, logs, referrers, analytics or wallet transport. Callback hardening should include no-store/no-referrer and no third-party resources before URL cleanup. Browser-only requests without native opt-in remain unchanged.

## 6. Native wallet polling and RP continuation endpoint

After it durably stores the capability, expiry, and exact approved pending state in the existing authenticated encrypted wallet-container payload, the Wallet polls:

`GET {rp_origin}/oid4vp/continuations/{transaction_id}`

The wallet requires exact HTTPS `rp_origin`, the fixed path template, no user-info/query/fragment, valid platform certificate/hostname checking, and no redirects (especially cross-origin). It sends the capability only in the `Authorization` header, whose value is the literal `Bearer`, one ASCII space, then the exact capability. The capability MUST NOT appear in a path, query, body, Referer, intent/App Link, log or analytics. The Wallet uses integer `Retry-After` delta seconds as a **minimum** delay, with exponential backoff and jitter, never polling sooner than the header or beyond the remaining expiry.

The RP validates the capability hash in constant time, expiry and path transaction ID before returning any request metadata. The path `transaction_id` MUST match the stored native continuation and the authenticated Request Object's `decent_account.transaction_id`. The RP returns:

- **HTTP 202 Accepted**, empty body, `Retry-After: <integer delta-seconds>` while the callback/ID-token/binding validation is not complete. No request URI or account data is returned.
- **HTTP 200 OK**, `Content-Type: application/json`, body containing exactly `{ "client_id": "x509_san_dns:<lowercase-DNS-name>", "request_uri": "https://<same-rp-origin>/<opaque-locator>" }`, only after successful RP OIDC validation and local-account absence. The outer parameters are the unchanged OpenID4VP request parameters. The `request_uri` is same-origin HTTPS, has no query/fragment/user-info, cannot redirect, and returns the existing profile's ES256-signed Request Object with `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, and the existing Request Object media type. It is a short-lived random locator for signed request metadata only—not the continuation capability, a presentation submission capability, or a bearer authorization to create an account. The signed request has no profile values, ID token, capability, or wallet secrets. Any request URI fetch returns the exact same immutable signed Request Object bytes; it MUST NOT mint or re-sign a new request/JTI/state/nonce on retries. The RP persists and verifies the exact Request Object bytes before the first 200; storage/readback failure cancels the continuation and requires a fresh login/approval, never regeneration under that capability.
- **HTTP 410 Gone**, empty body, when that known capability/transaction is expired, consumed, cancelled or revoked. On RP knowledge of OIDC failure/cancel, mark terminal; never release a request. If no terminal signal arrives, 202 is allowed only until expiry, then 410.
- **Generic HTTP 404 Not Found**, empty body, for malformed/unknown capability or unknown continuation ID, to conceal existence.

All poll and request_uri responses use no-store/no-referrer and no redirects. The RP atomically couples capability validation, request readiness, presentation acceptance, and capability revocation: concurrent polls can return the same unchanged live request until an accepted presentation commits; that commit atomically consumes the one-use binding/credential/presentation replay keys with account creation per existing v1 §8, revokes continuation access, and subsequent polls return 410. Presentation delivery, direct_post fields, response code, and accepted account result remain exactly as in adopted v1; the new capability is only for request retrieval.

The RP MUST retain only a hash-only terminal tombstone for up to five minutes after capability expiry so a matching expired capability can receive 410, then purge it. Unknown or malformed credentials return generic 404. No raw capability persists in RP state or is logged.

## 7. Required conformance artifacts and ownership

The ecosystem-owned additive schemas MUST preserve existing `accountRequest` and positive/negative vectors for browser-only requests byte-for-byte. Add a separate opted-in native-request schema variant that requires literal-true `decent_native_continuation`; the overall protocol still permits omission through the unchanged browser-only schema. Define an opted-in context variant that adds literal `true` while preserving the adopted context schema unchanged for browser-only transactions, and extend the binding schema with the capability hash. Do not redefine the entire standard OIDC ID-token schema; vector-specific explicit ID-token claim assertions cover the two additional claims.

Add a separate native-continuation vector set referencing existing base `valid-signup.json` artifacts by stable fixture ID. Because the native marker changes the signed JAR, it is not valid to claim the browser-only fixture's JAR bytes are a native-opted JAR; add a complete native-opted positive bundle with public test-only signing keys and signatures, keeping all existing fixtures unchanged. The fixture generator uses a documented public EC scalar and Ed25519 seed plus a fresh disposable RSA key; it emits only public keys and signatures, never the RSA private key. Capability and OIDC nonce values come from distinct deterministic public test byte sequences. Regeneration produces a newly signed, self-consistent proposal set, not identical RSA/ES256 signature bytes. The capability in this fixture is deterministic public test material only; production MUST use 32 independent CSPRNG bytes. Include amendment-specific negatives without modifying the adopted 29-case `negative.json` set. The verifier validates cross-artifact request/context and ID-token/binding claims and compares two independently represented signed Request Object retrieval responses byte-for-byte, in addition to validating the adopted bundle semantics. These shared vectors establish wire/correlation semantics only; they do not establish HTTP runtime, Android UI, TLS/device, Keycloak storage, browser callback, or RP database behavior.

Consumer ownership remains separate:
- Wallet #66 implements and tests native app, context fail-closed behavior, pending-capability persistence, polling, exact request verification and same direct_post flow. Wallet #62 core remains the owner of encrypted approval and presentation operations.
- Keycloak #8/#1 implements and tests exact statuses, confidential-client opt-in enforcement, metadata-free native POST response, capability hash/replay/durability, transient raw note cleanup, and no-code/no-capability failure cases.
- The RP component (WordPress first) implements and tests the confidential `form_post` callback, server-side token and hash-only capability storage, OIDC-before-request ordering, immutable request_uri, capability-protected polling, atomic acceptance/revocation, browser clean redirect, and no secret leakage.
- Each consumer owns its own integration/E2E evidence. Ecosystem #51 records evidence links; it does not create a central consumer integration harness.

## 8. Adoption and acceptance gate

This proposal does not change the live normative profile, its version label, or issue status. Protocol owner review and explicit resolution of the new unchecked #51 acceptance criterion are required before this content can replace or amend `PROFILE.md`. Any disagreement requires editing this proposal and re-verifying it before owner adoption. Until then, wallet #66 MUST NOT infer fallback behavior or claim conformance with native signup; login-proof/core approval work remains independently possible.

The native-handoff contract criterion is satisfied only when the protocol owner adopts the amended profile and unchanged-existing plus new shared vectors, not merely when the proposal verifier passes. Wallet, Keycloak, relying-party runtime/integration evidence and independent security/privacy review remain separate open #51 gates.

## 9. Run the proposal-only checks

From this directory, use the adopted package's hash-locked dependencies in an isolated environment:

```sh
uv venv .venv
uv pip install --python .venv/bin/python --require-hashes -r requirements-test.lock
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python verify_native_continuation_proposal.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v test_native_continuation_proposal
```

The proposal verifier first runs every unchanged adopted positive and negative. For native bundles it loads a private adopted-verifier instance and adapts only the three closed schema variants (`accountRequest`, `context`, `binding`): validate the native variant first, then remove its one permitted addition from a deep-copied schema input. The complete adopted validator receives the original signed native bundle; no JWS is stripped, rewritten, or treated as authenticated after mutation. This reuses the adopted OID4VP, certificate, DCQL, credential, presentation, and direct-post checks.

`vectors/continuation_vectors.proposal.json` contains the complete primary positive plus explicit path/value patch arrays for additional positives and negatives. Signed-case patches include re-signed dependencies and synchronized response bytes/projections; the runner has no case-ID-specific mutation behavior. `proof_accepted_at` is fixture-only timing evidence for the capability's acceptance-time ceiling, not a new protocol claim. Constant status/storage assertions describe the proposed contract; they are not observations of a running server. A proposal-only sender-artifact policy rejects raw capability leakage in supplied signed metadata and URLs, including nested JSON strings and percent-escaped URL components. This does not change the adopted receiver's rule to ignore benign unknown extensions, and cannot establish secrecy of live pages, storage, logs, telemetry, or artifacts absent from the offline bundle. The fixture and verifier also enforce that the OIDC and OID4VP nonces differ while preserving each nonce's own signed correlations.

To deliberately replace the proposal fixtures with a newly signed set:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python generate_native_continuation_proposal.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python verify_native_continuation_proposal.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v test_native_continuation_proposal
```

Regeneration never reads previous proposal output and leaves adopted artifacts untouched. The regression harness also exercises regeneration twice in an isolated temporary package, so ordinary test execution does not rewrite the committed proposal fixtures. Never use these public test keys or capability bytes in a live transaction.

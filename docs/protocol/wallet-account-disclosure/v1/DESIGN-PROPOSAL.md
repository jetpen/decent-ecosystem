# Wallet Account Disclosure v1 — design proposal

**Status: superseded historical proposal.** The adopted normative profile is [`PROFILE.md`](PROFILE.md). This document is retained only to preserve the initial design exploration; its open questions and candidate behavior are not authoritative. The live issue for [ecosystem #51](https://github.com/jetpen/decent-ecosystem/issues/51) now reflects the adopted profile and remaining qualification work.

## 1. Purpose and boundaries

Define a provider-neutral OpenID for Verifiable Presentations (OpenID4VP) profile for a wallet to disclose only selected, owner-asserted fields from its locally held Master Account Entity directly to one relying party (RP), as part of explicit site signup or another explicitly selected account action.

This is not `decent-wallet-login-v1`, a Storage grant, a Registry record, a site session, a capability, or an attestation that a contact detail is true or reachable. Keycloak remains the sole verifier of the fresh wallet-login proof and current Registry Owner Key. The RP does not query Registry. The Master Account Entity remains in the authenticated wallet-container v2 payload and is not uploaded to Keycloak or Storage. Site-specific Account Entities and Storage consent are separate.

## 2. Inputs already fixed by issue #51

The proposal treats these as constraints, not open questions:

- The RP owns its signup/login UX and sends `decent_account_action=login|signup` as a registered OIDC authorization-request extension. Keycloak validates the client and binds the exact action to its AuthenticationSession and wallet transaction. Do not overload OIDC `prompt=login`.
- The `decent-wallet-login-v1` proof remains exactly `{profile,challenge,identity_id,signature}`. Do not add account fields to it.
- One initial wallet approval covers Keycloak identity proof/provider-local signup and the specific site-account fields, purpose, action, and RP.
- Keycloak rejects duplicate provider-local signup principals without profile disclosure. The RP receives the account fields only through a separate direct-wallet OID4VP continuation after successful OIDC completion.
- Keycloak returns a short-lived, RP/action/transaction-bound signed Owner-Key binding statement as an OIDC ID-token claim. The RP validates it using configured issuer keys and uses it to verify the Owner-Key-bound OID4VP presentation without Registry lookup.
- The wallet retains a one-use pending approval bound to the exact RP, action, fields, Keycloak transaction, and expiry. No fields are released before successful OIDC validation for that same transaction. Mismatch, failure, expiry, or replay discloses nothing and requires fresh approval.

## 3. Proposed end-to-end shape

This sequence is a design candidate; the continuation handoff in steps 5–7 requires owner confirmation before it can become normative.

1. **RP starts OIDC.** The RP chooses `login` or `signup`, creates its ordinary OIDC state/nonce/PKCE values, and sends `decent_account_action`. It also selects an RP-local signup purpose and candidate account fields. The RP must not request fields for a login action unless the user explicitly chose a separate disclosure action.
2. **Keycloak binds the request.** Keycloak validates the registered client and exact action, creates its AuthenticationSession transaction, and binds client, action, RP issuer/client identifier, and transaction to the wallet login. No field values are sent to Keycloak.
3. **Wallet reviews one consent.** The wallet receives a Keycloak-authenticated disclosure summary: the configured site name and origin, action, purpose, exact field paths and types, and the consequence that these are owner assertions, not externally verified facts. It lets the user select only a subset of the proposed fields. The existing login proof is submitted unchanged. The wallet stores a pending approval with the selected values (or a protected reference to them), exact RP/action/transaction, consented purpose, and expiry. No account values leave the wallet at this point.
4. **Keycloak completes OIDC.** Keycloak verifies current Registry identity/key and the wallet-login proof, applies the login/signup account policy, and issues the normal OIDC result only on success. It includes a short-lived signed Owner-Key binding statement in the ID token. This statement binds the current Owner Key to the exact identity and the RP/action/transaction; it contains no account fields.
5. **RP validates OIDC before requesting disclosure.** The RP validates the normal Authorization Code + PKCE result (including issuer, signature/algorithm, audience/authorized party, expiry, nonce, state, and code exchange) and the Keycloak binding statement. Only then does it begin an OID4VP continuation for the same RP/action/transaction. It must not create a site account or claim successful signup until the matching disclosure is validated and consumed.
6. **Authenticated OID4VP request.** Candidate: use a signed OpenID4VP Request Object fetched through an RP-registered `request_uri`, signed by a key configured for that RP. It names a registered `client_id`, a fixed registered RP response endpoint, a fresh random OID4VP `nonce`, exact requested fields, purpose, action, transaction reference, expiry, and the Keycloak-signed Owner-Key binding statement. The wallet verifies the request signature and registered RP identity before displaying or releasing anything. No arbitrary callback URL is accepted. The RP request must not be usable to ask for fields beyond the wallet's pending approval.
7. **Wallet releases one matching presentation.** The wallet matches the request against its unexpired pending approval, including exact RP, action, purpose, selected fields (request may narrow, never widen), Keycloak transaction, and the binding statement. It emits one presentation bound cryptographically to the request `client_id` and fresh `nonce`, plus the Owner-Key binding statement; it consumes the approval once. The presentation is delivered directly to the registered RP endpoint using an OpenID4VP response mode selected for the v1 profile. No presentation is sent to Keycloak or Storage.
8. **RP validates and consumes.** The RP verifies the OID4VP response/request correlation, the Owner-Key signature against the key thumbprint in the Keycloak-signed binding statement, exact transaction/action/client/nonce/purpose/field match, and one-use status. It rejects unrequested or extra claims. Only then may explicit signup proceed with the selected self-asserted fields. A valid signature proves who asserted the values and that they were not altered; it does not prove their real-world truth.

### Critical continuation question

The architecture requires the RP to release the OID4VP request only after validating OIDC, while the wallet must match that continuation to its pre-OIDC pending approval. The issue does not yet identify how the wallet receives an authenticated continuation across browser/device boundaries or how the request conveys trusted evidence of successful OIDC validation. The candidate above places the Keycloak-signed binding statement in an RP-signed Request Object. This makes the request authentic as an RP statement and supplies a Keycloak-authenticated identity/key binding, but it does **not by itself prove to the wallet** that the RP actually validated the OIDC transaction. Owner review must choose whether:

- the wallet trusts the authenticated RP's signed continuation assertion that it validated OIDC and binds it to the Keycloak statement; or
- Keycloak issues a separate signed, one-use completion receipt that the RP relays in the authenticated OID4VP request; or
- another trusted continuation channel proves the required condition.

The RP remains responsible for actually validating OIDC before it creates the continuation. The wallet's release condition must be stated in a way that can be verified, not merely assumed from timing.

## 4. Candidate request and presentation semantics

### Request

Use OpenID4VP 1.0 Authorization Request semantics: registered client identity, fresh transaction `nonce`, explicit response destination/mode, and a signed Request Object for authenticated request contents. The RP must use an immutable registered response endpoint; request-controlled redirects are forbidden. The request asks for only the approved allowlisted claim set and describes a human-readable purpose. Reject unknown critical profile parameters, duplicate JSON members, malformed encodings, stale requests, wrong client, wrong endpoint, bad signature, and any request whose claims exceed the wallet's stored approval.

The profile should define an exact closed `decent_account_action` enumeration (`login` or `signup`) in the signed request and bind it to the OIDC action. A response for one action cannot be replayed as the other.

### Account data and selective disclosure

Candidate v1 rule: treat the Master Account Entity as a private source JSON object, not as a public credential. Define a finite registry of claim identifiers, JSON types, and disclosure meaning. Each claim maps to a narrowly defined JSON Pointer or equivalent typed accessor in the wallet's local entity. The wallet shows the exact claims and values it is about to disclose; unknown or locally absent claims are omitted only if the RP request permits optionality, otherwise the request fails without partial disclosure.

The wallet constructs a presentation containing only selected requested claims. It never serializes the whole Master Account Entity. It rejects duplicate claim identifiers and unknown fields. The selected values are self-asserted; no `verified`, `attested`, or equivalent truth status is inferred. Email, phone, address, and other contact-like data must not be presented as verified absent a separate verification process.

### Candidate signed payload

The exact wire representation and signature inputs remain open. A small, auditable v1 candidate is an owner-key-signed canonical JSON object containing:

- a fixed profile/version identifier;
- exact canonical Identity identifier and a key identifier or thumbprint;
- relying-party client identifier;
- `decent_account_action` and purpose identifier/text;
- the OpenID4VP `nonce` and a transaction-binding identifier;
- issued-at and bounded expiry;
- an allowlisted map of only the selected claim identifiers and values.

The signature covers every member above using one canonical serialization. The RP verifies the identity/key link using the Keycloak-signed Owner-Key binding statement, not a Registry lookup. The profile must not put unselected fields in an outer credential, metadata, status list, debug object, or auxiliary disclosure envelope.

This custom signed presentation would require a precisely defined OpenID4VP format identifier and wallet/verifier interoperability profile. Alternative standards-based credential formats (including SD-JWT VC) need a separate comparison: they may bring issuer/credential semantics or issuance machinery that do not fit a directly self-asserted, per-transaction presentation. Do not silently choose one or label a custom payload as a standard VC format.

## 5. Proposed Owner-Key binding claim

Candidate claim name: `decent_owner_key_binding`. It should be a signed nested object in the Keycloak ID token, not an account/profile claim. Candidate closed fields:

| Field | Candidate meaning |
|---|---|
| `v` | Binding-profile version, fixed to `1` for this profile. |
| `identity_id` | Exact raw identifier used for the successful Keycloak wallet proof; no normalization. |
| `owner_key_thumbprint` | RFC 7638 JWK thumbprint of the exact current Registry-resolved Ed25519 public key used to verify the proof. |
| `rp_client_id` | Exact OIDC client ID for the relying party. |
| `action` | Exact `login` or `signup` value accepted by Keycloak. |
| `transaction_id` | Unpredictable, transaction-scoped identifier shared with the wallet approval and RP continuation; not an OIDC bearer credential. |
| `iat`, `exp` | Short validity window; exact maximum lifetime and skew remain to be chosen. |
| `jti` | Unique one-use statement identifier with explicit replay-consumption scope. |

The enclosing ID token already supplies the issuer signature, token audience, subject, and expiry. The binding profile must specify whether the nested object is independently signed or protected solely as a claim in the issuer-signed ID token, and how the RP binds it to the same authentication event and OIDC nonce. The RP verifies the complete ID token with a maintained OIDC implementation before using the claim. The claim must not be released to a different client or reused across transactions. Exact name, encoding, thumbprint profile, expiry, `jti` store/consumption, and token delivery location need owner review.

The claim says which key Keycloak used for this authentication; it is not a live Registry proof at the RP and does not prove contact values.

## 6. Account action and state behavior

| Situation | Candidate behavior |
|---|---|
| `login` action, Keycloak principal absent | Fail authentication; no OIDC success, no OID4VP request, no disclosure. |
| `login` action, exact principal exists | Complete OIDC under ordinary login policy. No profile fields unless the user separately authorized an explicit disclosure purpose. |
| `signup` action, exact principal already exists | Fail signup without account-field disclosure; offer a separate login path. |
| `signup` action, principal absent and wallet proof valid/current | Create or map the provider-local principal under the existing Keycloak policy, issue OIDC, then permit only the matching OID4VP continuation. |
| RP OIDC validation fails or callback is abandoned | No OID4VP release. Pending wallet approval expires or is cancelled; retry requires a new approval unless exact safe retry rules are adopted. |
| RP account already exists, concurrent signup, or partial provisioning | No duplicate account; idempotency and rollback/compensation semantics need to be specified by the RP. No Storage account is implicitly created. |
| OID4VP request, response, or binding statement mismatch/expiry/replay | Fail closed; disclose no fields, consume no mismatched approval, and require a fresh approval. |
| Registry/key state unavailable during Keycloak proof | Keycloak authentication fails closed; no binding statement or disclosure continuation. |

The use of the word “signup” identifies the site action, not guaranteed creation. The transaction must not create a site account until the RP has successfully validated both OIDC and the matching disclosure. If the RP provisions an account before disclosure verification, it must define a safe rollback/no-partial-account invariant.

## 7. State, replay, expiry, and cancellation

Candidate state machine for one wallet approval:

`PENDING_OIDC -> OIDC_BOUND -> DISCLOSURE_REQUESTED -> PRESENTED -> CONSUMED`

Terminal alternatives: `CANCELLED`, `EXPIRED`, `FAILED`. Only one successful transition may release the presentation. A duplicate request or response returns no second disclosure. A failed OIDC transaction, wrong transaction/client/action, mismatched binding statement, replayed `jti`/nonce, expired approval, or failed state read produces no disclosure. The design must say which component stores each state and what storage primitive makes one-use consumption atomic under concurrent nodes. It must not claim atomicity from a provider API that only guarantees single-key removal if a multi-key transaction is needed.

Use independent fresh random values for the OIDC transaction, OID4VP `nonce`, and any browser continuation handle; define their entropy, encoding, scope, lifetime, and storage form. Do not reuse OIDC `state`, OIDC `nonce`, a wallet-login challenge, or a visible RP URL as an OID4VP nonce. Store only digests for bearer-like opaque handles where lookup permits; never log credentials, proof, claim values, or unredacted request/response bodies.

Cancellation at the wallet or RP, browser closure, user denial, timeout, OIDC failure, and network retry must all terminate or resume only the same exact transaction. Retry behavior may return an already accepted status but cannot create another presentation or account.

## 8. Privacy and security requirements for the normative profile

- No Master Account Entity upload, replication, or automatic synchronization. No account fields in the wallet-login proof, Keycloak request, Keycloak user attributes, ID token, or Storage request.
- The RP sees only selected fields after successful OIDC validation. Keycloak sees no disclosed field values.
- The wallet displays a stable RP identity, exact action/purpose, and exact fields before approval; a request signature is checked against the RP identity configured by the profile.
- Unknown requested fields, extra response fields, unrecognized algorithms, ambiguous identity/key binding, and unsupported profile versions fail closed.
- The RP validates OIDC using a maintained library/protocol implementation, then validates the separate presentation; neither token validation nor a valid owner signature alone is sufficient.
- Do not normalize Identity IDs or use email/phone equality for account mapping. Do not treat owner-signed contact claims as externally verified.
- Define data minimization, value limits, retention/deletion, log redaction, response cache controls, endpoint-origin policy, CSRF/CORS protections where browser transport requires them, and anti-mix-up/session binding for the continuation.
- Define downgrade resistance: clients must reject an unknown profile version rather than fall back to an unsigned request or broader disclosure.

## 9. Decisions needed before this can become normative

1. **Presentation format:** custom owner-signed JSON envelope vs. a named existing credential format; exact OpenID4VP/DCQL format identifier and interoperability implications.
2. **Claim model:** finite standard claim registry vs. per-site namespaced claims; allowed JSON types, nested data, arrays, empty/null values, maximum sizes, and optionality rules.
3. **Canonicalization and signature:** exact serialization, duplicate-member policy, signature algorithm/encoding, domain separation, key/thumbprint representation, and complete signed-member set.
4. **OID4VP transport:** direct-post vs. another supported response mode; signed Request Object delivery, RP client authentication/registration, endpoint allowlisting, response correlation and wallet discovery/continuation UX.
5. **OIDC-success proof to wallet:** trust in an RP-signed continuation assertion vs. a separate Keycloak-signed one-use completion receipt vs. another verifiable mechanism.
6. **Transaction binding:** exact common transaction identifier derivation/claims, relation to OIDC `state`/`nonce` and ID-token `jti`, whether any transaction data is visible to the wallet, and mix-up protection.
7. **Owner-Key binding statement:** exact claim name/schema, current-key thumbprint algorithm, audience and action binding, issuance location, expiry/skew, replay storage, and whether it is independently signed or protected by the ID token only.
8. **Disclosure transaction lifetime:** approval persistence/at-rest protection, maximum expiry, cancellation, retry, process restart, device loss, and one-use atomic-consumption boundary.
9. **Signup/provisioning races:** duplicate local account behavior, idempotency key, concurrent creation, OIDC success followed by disclosure failure, and whether an incomplete account can exist.
10. **Conformance and security review:** canonical positive/negative vectors, exact expected failure states, vectors proving no premature disclosure, race tests, privacy review, and independent review of what the Owner Key proves.

Until these are decided and reviewed, the profile must not be labeled normative or ready for implementation. The six acceptance criteria in issue #51—including consumer tests for ecosystem, wallet, Keycloak, and the first RP—remain open.

## 10. Standards references and limits

- [OpenID for Verifiable Presentations 1.0](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html) is the current OpenID Foundation specification. It defines a protocol for requesting and delivering credential presentations, including request/response transaction binding. It does not define this project's self-asserted Master Account Entity semantics, signup action, Keycloak OIDC combination, or deferred wallet continuation.
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0-final.html) defines the ID token and OIDC authorization-code flow. The project-specific `decent_account_action` extension and Owner-Key binding claim require their own profile and validation rules.
- [RFC 7638](https://www.rfc-editor.org/rfc/rfc7638) defines JWK thumbprints, if selected for the Owner-Key identifier.
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) defines JSON Canonicalization Scheme, if selected for the custom owner-signed presentation. This proposal does not assume that the wallet-login proof's serialization automatically governs the separate presentation profile.

# Owner-authorized Storage grant semantic envelope v1

## Status and authority boundaries

This is a project profile, not a claim that an arbitrary authorization server supports it. RFC 7523 is the Standards Track JWT authorization-grant profile; its mandatory claims are `iss`, `sub`, `aud`, and `exp`. The project requires `iat` and `jti` in addition; do not describe them as RFC-required.

The corrected provider-neutral Storage grant semantic envelope is adopted as normative **decent Storage grant semantic v1** by explicit user direction. Adoption covers the semantic schema, exact identity/current-key binding, JCS/signature boundary, opaque exact action/purpose semantics, strict core-field rejection and non-authorizing extension handling. It does **not** qualify a Keycloak adapter, either consumer, or any issuer. Keep RFC 9068, alternate-AS support, future Keycloak compatibility and production readiness unclaimed unless separately qualified.

## Signed object and canonical bytes

**Required v1 profile claims:** `iss`, `sub`, `aud`, `exp`, `iat`, and `jti`. RFC 7523 requires `iss`, `sub`, `aud`, and `exp`; this project profile additionally requires `iat` and `jti`. The `decent_grant` semantic object MUST be RFC 8785 JCS-canonicalized before embedding as its member value in the normally serialized outer JWT claims set; the JWS signature covers the exact outer payload bytes per RFC 7515, not a detached signature over JCS bytes.

The wallet's single signature is the JWS signature over the RFC 7515 signing input `ASCII(BASE64URL(UTF8(protected-header)) || "." || BASE64URL(payload))`; there is no detached signature over the grant. The verifier MUST resolve the current Registry key for the exact assertion `sub`, require exact equality between that `sub` and `decent_grant.owner_identifier`, require `decent_grant.owner_public_key` to equal that current Registry key, and verify the JWS signature with it. `decent_grant.grant_jti` MUST equal assertion `jti` and is the one-use replay ID.

For deterministic semantics and cross-implementation comparison, JCS applies to the parsed `decent_grant` semantic object only. Its UTF-8 canonical bytes are the value embedded as that claim in the outer JWT claims object; the complete JWT claims object is serialized as JSON by the JWS producer and those exact payload bytes are base64url-encoded and covered by the JWS signature. V1 does not require JCS canonicalization of the outer JWT claims object. JCS does not normalize Unicode; comparisons preserve strings exactly. Reject duplicate JSON member names before ordinary object decoding, invalid Unicode, out-of-I-JSON/non-safe-integer values, invalid schema/unknown core members, and noncanonical fixture encodings where exact canonical bytes are the fixture. The canonical semantic grant bytes are not a replacement for the JWS signing input.

The v1 profile requires one exact owner-selected identifier, one existing object at its current digest, an operator-configured exact Storage resource, opaque exact action strings and opaque exact purpose. It also requires a unique one-use grant ID, consent-expiry ceiling, and current Storage policy at use. Assertion and output-token expiry cannot exceed consent. There is no retry/idempotency or refresh promise; an uncertain exchange requires fresh owner authorization.

## Semantic constraints

- The `owner_identifier` MUST equal RFC 7523 assertion `sub` exactly (byte-for-byte UTF-8 string value); no normalization, alias lookup or key-equality identity merge. The verifier MUST resolve the current Registry key for that identifier and verify the JWS with it; `owner_public_key` MUST exactly identify that same current Registry-resolved key. These are semantic profile requirements for every conforming adapter. A mismatch is rejected by the adapter before issuance; no other subject is inferred or merged. The adapter MUST map the exact subject to the intended local user.
- `assertion.aud` targets the AS; `storage_aud` identifies one operator-configured exact Storage resource and maps to the issued access JWT's standard `aud`; URI normalization is not allowed.
- The grant covers one existing object at its current `sha256:` + 64-lowercase-hex digest. Create/link, replacement, listing, disclosure, provider enrollment and quota are separate authorities.
- `actions` is a set of 1–8 unique, non-empty bounded strings; `purpose` is non-empty bounded opaque text. Values compare exactly. V1 defines no shared action/purpose vocabulary or universal method mapping; a consumer profile defines recognized operations and MUST deny unsupported/unimplemented actions.
- `grant_jti` is an exact non-empty identifier and MUST equal assertion JWT `jti`. Reuse is rejected. An uncertain exchange result requires new owner authorization.
- `iat`, `exp`, and `consent_exp` are positive Unix epoch integer seconds within the IEEE-754 safe-integer range. `consent_exp <= assertion exp`; output access-token `exp <= consent_exp`. Numeric maximum TTL and clock-skew allowance remain deployment policy.
- Current key fingerprint/Registry sequence and output grant fields derive from verified assertion/current Identity, never client-editable attributes. Storage checks current object, enrollment, quota, and revocation at protected use; required-state outage fails closed.

## Cryptographic review boundary

RFC 7515 signs the exact Base64URL(protected header) + "." + Base64URL(payload) JWS signing input; it does not require applying JCS to a JWT Claims Set before encoding. This project profile requires the `decent_grant` member value to use RFC 8785 JCS bytes; the outer JWT claims object is not JCS-required. The JCS profile choice is not an RFC 7523/JWS default. The Keycloak 26.8.0 adapter must be tested against this exact payload before it is qualified; the prior #17 run alone does not prove it.

## RFC 7523→Keycloak 26.8.0 adapter profile

The approved #34 adapter fixture uses the token endpoint's standard JWT Authorization Grant. The Keycloak provider verifies the assertion under configured external issuer/JWKS relationship, links `sub` to the local user, enforces single-value AS audience, expiry, EdDSA, and one-use JTI, and delegates actual wallet signature/current Registry lookup to the tested private verifier. It passes only verified semantic fields through trusted request/session context into the dedicated mapper. Mapper emits exact owner `sub`, standard Storage `aud`, consent-bounded token expiry and the fixture claims documented in `adapter-keycloak-26.8.0.json`.

This is private-SPI, pinned 26.8.0 evidence only. It is not RFC 9068 conformance. The prototype asserts no refresh token. Successor-release testing is excluded as unavailable; no future compatibility is claimed. Other AS profiles require a separately reviewed, tested adapter fixture.
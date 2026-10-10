# Owner-authorized Storage grant semantic envelope v1

**Status:** User-directed stage-1 draft for review under [Wayfinder #35](https://github.com/jetpen/decent-ecosystem/issues/35). It is not an adopted/released protocol. This file defines provider-neutral semantics plus a versioned fixture; it is not a general OAuth AS wire profile and does not claim every RFC 7523 provider supports it.

## Signed object and canonical bytes

The wallet signs an RFC 7523 assertion JWT (JWS Compact Serialization, EdDSA). Its payload contains the required RFC 7523 issuer, exact raw selected identity as `sub`, single AS/realm-or-token-endpoint `aud`, `iat`, `exp`, and assertion `jti`, plus the `decent_grant` member carrying the v1 semantic envelope in `grant-envelope.schema.json`.

The wallet's single signature is the JWS signature over the RFC 7515 signing input `ASCII(BASE64URL(UTF8(protected-header)) || "." || BASE64URL(payload))`; no second detached grant signature is defined. The verifier checks that signature with the current Registry-resolved exact owner key. `decent_grant.grant_jti` MUST equal the RFC 7523 assertion `jti` and is the one-use replay ID.

For deterministic semantic fixtures and comparison, serialize the parsed semantic envelope using RFC 8785 JSON Canonicalization Scheme (JCS), UTF-8 encoded. JCS does not normalize Unicode; comparisons preserve strings exactly. Reject duplicate JSON member names before ordinary object decoding, invalid Unicode, out-of-I-JSON/non-safe-integer values, invalid schema/unknown core members, and noncanonical fixture encodings where exact canonical bytes are the fixture. The JCS representation is a canonical test vector, not a replacement for the JWS signing input.

## Semantic constraints

- Exact raw owner identifier; no normalization, alias lookup or key-equality identity merge. It is explicitly mapped to a local user by the Keycloak adapter.
- One operator-configured Storage resource identifier; exact string comparison, no URI normalization. The input assertion `aud` targets the AS; `decent_grant.storage_aud` identifies Storage and is mapped into the issued access JWT's standard `aud`.
- One existing object at its current digest `sha256:` + 64 lowercase hex characters. Create/link, replacement digest, listing, disclosure, provider enrollment and quota are separate authorities.
- `actions` is 1–8 unique, non-empty bounded strings; `purpose` is non-empty bounded opaque text. V1 defines neither vocabulary nor universal method mapping.
- `grant_jti` is an exact non-empty identifier; it equals assertion JWT `jti`. Reuse is rejected. No exact retry/idempotency guarantee; an uncertain exchange result requires new owner authorization.
- `iat`, `exp`, and `consent_exp` are Unix epoch integer seconds within the IEEE-754 safe-integer range; values are positive. `consent_exp <= assertion exp`; issued access token `exp <= consent_exp`. Numeric maximum TTL and clock-skew allowance are deployment policy, not chosen here.
- Current key fingerprint/Registry sequence and grant fields in output access token derive from verified assertion/current Identity, not client/user-editable attributes. Provider enrollment, object existence, quota, and revocation are independent Storage state checked at protected use; unavailable required state fails closed.
- Optional namespaced `extensions` contain only primitive metadata, are non-authorizing and ignored by v1; unknown core fields are rejected.

## Cryptographic review boundary

RFC 7515 signs the exact Base64URL(protected header) + "." + Base64URL(payload) JWS signing input; it does not require applying JCS to a JWT Claims Set before encoding. This v1 adapter profile chooses JCS bytes for the semantic payload *inside the JWT* to make wallet grant serialization deterministic. That is a project profile choice, not an RFC 7523/JWS default. The Keycloak 26.8.0 adapter must be tested against this exact payload before it is qualified; the prior #17 run alone does not prove it.

## RFC 7523→Keycloak 26.8.0 adapter profile

The approved #34 adapter fixture uses the token endpoint's standard JWT Authorization Grant. The Keycloak provider verifies the assertion under configured external issuer/JWKS relationship, links `sub` to the local user, enforces single-value AS audience, expiry, EdDSA, and one-use JTI, and delegates actual wallet signature/current Registry lookup to the tested private verifier. It passes only verified semantic fields through trusted request/session context into the dedicated mapper. Mapper emits exact owner `sub`, standard Storage `aud`, consent-bounded token expiry and the fixture claims documented in `adapter-keycloak-26.8.0.json`.

This is private-SPI, pinned 26.8.0 evidence only. It is not RFC 9068 conformance. The prototype asserts no refresh token. Successor-release testing is excluded as unavailable; no future compatibility is claimed. Other AS profiles require a separately reviewed, tested adapter fixture.
#!/usr/bin/env python3
"""Offline verifier for the adopted Decent Wallet Account Disclosure v1 profile."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import re
import sys
import unicodedata
from itertools import combinations
from pathlib import Path
from urllib.parse import urlsplit

import jsonschema
import rfc8785
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.x509.oid import ExtensionOID

ROOT = Path(__file__).resolve().parent
PROFILE = "decent-account-disclosure-v1"
OID4VP_AUD = "https://self-issued.me/v2"
ACCOUNT_ACTIONS = {"signup", "signup_recovery"}
SCHEMA = json.loads((ROOT / "schemas/profile.schema.json").read_text(encoding="utf-8"))
CLAIM_SHORT = {
  "urn:decent:account:v1:given_name": "given_name",
  "urn:decent:account:v1:family_name": "family_name",
  "urn:decent:account:v1:email": "email",
  "urn:decent:account:v1:phone": "phone",
  "urn:decent:account:v1:locale": "locale",
}



class ProtocolError(Exception):
  def __init__(self, code: str):
    self.code = code
    super().__init__(code)


def b64d(value: str) -> bytes:
  if not isinstance(value, str) or "=" in value or not re.fullmatch(r"[A-Za-z0-9_-]*", value):
    raise ProtocolError("malformed-base64url")
  try:
    raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
  except Exception as exc:
    raise ProtocolError("malformed-base64url") from exc
  if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != value:
    raise ProtocolError("malformed-base64url")
  return raw


def b64(raw: bytes) -> str:
  return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def strict_json(raw: bytes) -> dict:
  def pairs(items):
    result = {}
    for key, value in items:
      if key in result:
        raise ProtocolError("duplicate-json-member")
      result[key] = value
    return result
  def finite_float(number):
    value = float(number)
    if not math.isfinite(value):
      raise ProtocolError("invalid-json-number")
    return value
  try:
    value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=pairs,
                       parse_float=finite_float,
                       parse_constant=lambda _value: (_ for _ in ()).throw(ProtocolError("invalid-json-number")))
  except ProtocolError:
    raise
  except Exception as exc:
    raise ProtocolError("invalid-json") from exc
  def reject_surrogates(value):
    if isinstance(value, str):
      if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ProtocolError("invalid-unicode-scalar")
    elif isinstance(value, list):
      for item in value:
        reject_surrogates(item)
    elif isinstance(value, dict):
      for key, item in value.items():
        reject_surrogates(key)
        reject_surrogates(item)
  reject_surrogates(value)
  if not isinstance(value, dict):
    raise ProtocolError("json-object-required")
  return value


def parse_jws(token: str):
  if not isinstance(token, str) or len(token) > 65536:
    raise ProtocolError("malformed-jws")
  parts = token.split(".")
  if len(parts) != 3 or not all(parts):
    raise ProtocolError("malformed-jws")
  header = strict_json(b64d(parts[0]))
  payload = strict_json(b64d(parts[1]))
  signature = b64d(parts[2])
  return parts, header, payload, signature


def ec_public(jwk) -> ec.EllipticCurvePublicKey:
  if set(jwk) - {"kty", "crv", "x", "y", "kid", "use", "alg"} or jwk.get("kty") != "EC" or jwk.get("crv") != "P-256":
    raise ProtocolError("unsupported-rp-key")
  try:
    return ec.EllipticCurvePublicNumbers(int.from_bytes(b64d(jwk["x"]), "big"),
                                         int.from_bytes(b64d(jwk["y"]), "big"),
                                         ec.SECP256R1()).public_key()
  except Exception as exc:
    raise ProtocolError("invalid-rp-key") from exc


def rsa_public(jwk):
  if jwk.get("kty") != "RSA":
    raise ProtocolError("unsupported-keycloak-key")
  try:
    return rsa.RSAPublicNumbers(int.from_bytes(b64d(jwk["e"]), "big"),
                                int.from_bytes(b64d(jwk["n"]), "big")).public_key()
  except Exception as exc:
    raise ProtocolError("invalid-keycloak-key") from exc


def ed_public(jwk):
  if set(jwk) - {"kty", "crv", "x", "kid"} or jwk.get("kty") != "OKP" or jwk.get("crv") != "Ed25519":
    raise ProtocolError("unsupported-owner-key")
  try:
    raw = b64d(jwk["x"])
    if len(raw) != 32:
      raise ValueError("Ed25519 public key must be 32 bytes")
    return ed25519.Ed25519PublicKey.from_public_bytes(raw)
  except Exception as exc:
    raise ProtocolError("invalid-owner-key") from exc


def jwk_thumbprint(jwk):
  if jwk.get("kty") == "OKP":
    obj = {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"]}
  elif jwk.get("kty") == "EC":
    obj = {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"], "y": jwk["y"]}
  elif jwk.get("kty") == "RSA":
    obj = {"e": jwk["e"], "kty": jwk["kty"], "n": jwk["n"]}
  else:
    raise ProtocolError("unsupported-key-type")
  return b64(hashlib.sha256(rfc8785.dumps(obj)).digest())


def verify_jws(token, alg, public_key, typ=None, kid=None, canonical_payload=False):
  parts, header, payload, signature = parse_jws(token)
  if header.get("alg") != alg or (typ is not None and header.get("typ") != typ):
    raise ProtocolError("jws-header-mismatch")
  if kid is not None and header.get("kid") != kid:
    raise ProtocolError("jws-kid-mismatch")
  if canonical_payload and b64(rfc8785.dumps(payload)) != parts[1]:
    raise ProtocolError("noncanonical-payload")
  signing_input = (parts[0] + "." + parts[1]).encode("ascii")
  try:
    if alg == "ES256":
      if len(signature) != 64:
        raise ValueError("ES256 signature length")
      der = encode_dss_signature(int.from_bytes(signature[:32], "big"), int.from_bytes(signature[32:], "big"))
      public_key.verify(der, signing_input, ec.ECDSA(hashes.SHA256()))
    elif alg == "RS256":
      public_key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
    elif alg == "EdDSA":
      public_key.verify(signature, signing_input)
    else:
      raise ProtocolError("unsupported-algorithm")
  except ProtocolError:
    raise
  except Exception as exc:
    raise ProtocolError("signature-invalid") from exc
  return header, payload


def check_lifetime(payload, now, error):
  if not isinstance(payload.get("iat"), int) or not isinstance(payload.get("exp"), int):
    raise ProtocolError(error)
  if payload["iat"] > now + 60 or payload["exp"] <= now or payload["exp"] <= payload["iat"] or payload["exp"] - payload["iat"] > 300:
    raise ProtocolError(error)


def claim_id_list(claims):
  ids = [item["id"] for item in claims]
  if len(ids) != len(set(ids)):
    raise ProtocolError("duplicate-claim-id")
  return ids


def validate_purpose(value):
  bidi_controls = {0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A)}
  if (not isinstance(value, str) or not 1 <= len(value) <= 160 or not value.strip() or
      any(unicodedata.category(char) in {"Cc", "Cs"} or ord(char) in bidi_controls for char in value)):
    raise ProtocolError("invalid-purpose")


def validate_schema(name, value):
  schema = copy.copy(SCHEMA)
  schema["$ref"] = f"#/$defs/{name}"
  jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(value)


def validate_bundle(bundle):
  now = bundle.get("validation_time")
  if not isinstance(now, int):
    raise ProtocolError("validation-time-missing")
  if bundle.get("oidc_callback_validated") is not True:
    raise ProtocolError("oidc-not-validated")
  if bundle.get("profile") != PROFILE or bundle.get("test_only") is not True:
    raise ProtocolError("wrong-vector-profile")

  # The RP's signed OIDC authorization request creates the claim-set ceiling.
  rp_jwk = bundle["rp_client_id_jwk"]
  rp_key = ec_public(rp_jwk)
  if jwk_thumbprint(rp_jwk) != rp_jwk.get("kid"):
    raise ProtocolError("rp-key-id-mismatch")
  _, jar = verify_jws(bundle["initial_oidc_request_jws"], "ES256", rp_key,
                      typ="oauth-authz-req+jwt", kid=rp_jwk["kid"])
  check_lifetime(jar, now, "oidc-request-expired")
  if (jar.get("iss") != jar.get("client_id") or
      jar.get("decent_account_action") not in ACCOUNT_ACTIONS or
      "decent_account_request" not in jar):
    raise ProtocolError("action-mismatch")
  validate_schema("accountRequest", jar["decent_account_request"])
  req = jar["decent_account_request"]
  validate_purpose(req["purpose"])
  initial_ids = claim_id_list(req["claims"])

  context = bundle["keycloak_context"]
  validate_schema("context", context)
  validate_purpose(context["purpose"])
  if b64(hashlib.sha256(bundle["transaction_handle"].encode("ascii")).digest()) != context["transaction_id"]:
    raise ProtocolError("transaction-mismatch")
  if (context["profile"] != PROFILE or context["action"] != jar["decent_account_action"] or
      context["request_id"] != req["request_id"] or context["purpose"] != req["purpose"] or
      context["claims"] != req["claims"] or context["rp_client_id"] != jar["client_id"] or
      context["oidc_nonce"] != jar["nonce"] or context["keycloak_issuer"] != jar["aud"]):
    raise ProtocolError("context-mismatch")

  # A real RP must complete OIDC Code + PKCE validation before this point.
  kc_jwk = bundle["keycloak_jwks"]["keys"][0]
  kc_key = rsa_public(kc_jwk)
  token_header, id_token = verify_jws(bundle["id_token_jws"], "RS256", kc_key,
                                      typ="JWT", kid=kc_jwk["kid"])
  if id_token.get("iss") != context["keycloak_issuer"] or id_token.get("aud") != context["rp_client_id"] or id_token.get("nonce") != context["oidc_nonce"]:
    raise ProtocolError("oidc-id-token-mismatch")
  if (not isinstance(id_token.get("iat"), int) or not isinstance(id_token.get("exp"), int) or
      id_token["iat"] > now + 60 or id_token["exp"] <= now or id_token["exp"] <= id_token["iat"]):
    raise ProtocolError("oidc-id-token-expired")
  binding_token = bundle["owner_key_binding_jws"]
  if id_token.get("decent_owner_key_binding") != binding_token:
    raise ProtocolError("binding-claim-mismatch")
  _, binding = verify_jws(binding_token, "RS256", kc_key,
                          typ="decent-owner-key-binding+jwt", kid=kc_jwk["kid"])
  validate_schema("binding", binding)
  if binding["iss"] != id_token["iss"] or binding["sub"] != id_token["sub"] or binding["oidc_nonce"] != id_token["nonce"]:
    raise ProtocolError("binding-oidc-mismatch")
  if binding["aud"] != context["rp_client_id"]:
    raise ProtocolError("binding-audience-mismatch")
  if (binding["action"] != context["action"] or binding["transaction_id"] != context["transaction_id"] or
      binding["request_id"] != context["request_id"] or binding["oidc_nonce"] != context["oidc_nonce"]):
    raise ProtocolError("binding-context-mismatch")
  check_lifetime(binding, now, "binding-expired")
  if binding["exp"] > min(id_token["exp"], context["expires_at"]):
    raise ProtocolError("binding-expiry-too-late")
  owner_jwk = bundle["owner_jwk"]
  if binding["owner_key"] != {k: owner_jwk[k] for k in ("kty", "crv", "x")} or jwk_thumbprint(owner_jwk) != binding["owner_key_thumbprint"]:
    raise ProtocolError("owner-binding-mismatch")

  # The signed OID4VP request is authenticated by the fixture's explicitly trusted test certificate.
  cert_info = bundle["rp_certificate"]
  cert_der = base64.b64decode(cert_info["leaf_der_base64"], validate=True)
  cert = x509.load_der_x509_certificate(cert_der)
  if cert.fingerprint(hashes.SHA256()).hex() != cert_info["trust_anchor_sha256"]:
    raise ProtocolError("untrusted-rp-certificate")
  cert_key = cert.public_key()
  if not isinstance(cert_key, ec.EllipticCurvePublicKey):
    raise ProtocolError("request-certificate-mismatch")
  cert_hash = cert.signature_hash_algorithm
  if cert_hash is None:
    raise ProtocolError("untrusted-rp-certificate")
  try:
    cert_key.verify(cert.signature, cert.tbs_certificate_bytes, ec.ECDSA(cert_hash))
  except Exception as exc:
    raise ProtocolError("untrusted-rp-certificate") from exc
  cert_numbers = cert_key.public_numbers()
  rp_numbers = rp_key.public_numbers()
  if (cert_numbers.x, cert_numbers.y) != (rp_numbers.x, rp_numbers.y):
    raise ProtocolError("request-certificate-mismatch")
  request_header, vp_request = verify_jws(bundle["oid4vp_request_jws"], "ES256", cert_key,
                                            typ="oauth-authz-req+jwt")
  if request_header.get("x5c") != [cert_info["leaf_der_base64"]] or request_header.get("kid") != rp_jwk["kid"]:
    raise ProtocolError("request-certificate-mismatch")
  oid4vp_client = bundle["oid4vp_client_id"]
  outer_params = bundle["oid4vp_authorization_parameters"]
  if "transaction_data" in outer_params or "transaction_data" in vp_request:
    raise ProtocolError("unsupported-transaction-data")
  # Unknown transport extensions are ignored, not alternate sources of known parameters.
  disallowed_outer = (set(SCHEMA["$defs"]["oid4vpRequest"]["properties"]) - {"client_id", "request_uri", "iss"}) | {
    "request", "redirect_uri", "scope", "request_uri_method"}
  if (outer_params.get("client_id") != oid4vp_client or
      outer_params.get("request_uri") != bundle["oid4vp_request_uri"] or
      set(outer_params) & disallowed_outer or
      vp_request.get("client_id") != oid4vp_client or vp_request.get("aud") != OID4VP_AUD):
    raise ProtocolError("request-client-mismatch")
  request_uri = urlsplit(bundle["oid4vp_request_uri"])
  if request_uri.scheme != "https" or request_uri.hostname != oid4vp_client.removeprefix("x509_san_dns:") or request_uri.query or request_uri.fragment:
    raise ProtocolError("request-uri-mismatch")
  check_lifetime(vp_request, now, "oid4vp-request-expired")
  if len(b64d(vp_request["nonce"])) < 32:
    raise ProtocolError("oid4vp-nonce-too-short")
  cert_sans = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME).value.get_values_for_type(x509.DNSName)
  uri = urlsplit(vp_request["response_uri"])
  client_host = oid4vp_client.removeprefix("x509_san_dns:")
  origin = urlsplit(context["rp_origin"])
  if (oid4vp_client != "x509_san_dns:" + client_host or client_host not in cert_sans or uri.scheme != "https" or
      uri.hostname != client_host or uri.path != "/oid4vp/response" or uri.query or uri.fragment or
      origin.scheme != "https" or origin.hostname != client_host or origin.path or origin.query or origin.fragment):
    raise ProtocolError("response-uri-host-mismatch")
  try:
    cert_time = __import__("datetime").datetime.fromtimestamp(vp_request["iat"], tz=__import__("datetime").timezone.utc)
    if not (cert.not_valid_before_utc <= cert_time <= cert.not_valid_after_utc):
      raise ValueError("certificate not valid at request iat")
  except Exception as exc:
    raise ProtocolError("untrusted-rp-certificate") from exc
  if vp_request.get("response_type") != "vp_token" or vp_request.get("response_mode") != "direct_post":
    raise ProtocolError("unsupported-response-mode")
  formats = vp_request.get("client_metadata", {}).get("vp_formats_supported", {})
  if formats.get("decent_account_jwt_v1", {}).get("alg_values") != ["EdDSA"]:
    raise ProtocolError("unsupported-presentation-format")
  ext = vp_request.get("decent_account")
  expected_ext = {"profile": PROFILE, "rp_oidc_client_id": context["rp_client_id"], "action": context["action"],
                  "request_id": context["request_id"], "transaction_id": context["transaction_id"],
                  "purpose": context["purpose"], "owner_key_binding": binding_token, "claims": context["claims"]}
  if ext != expected_ext:
    raise ProtocolError("request-context-mismatch")
  validate_purpose(ext["purpose"])
  try:
    validate_schema("oid4vpRequest", vp_request)
  except jsonschema.ValidationError as exc:
    raise ProtocolError("oid4vp-request-schema-invalid") from exc
  dcql_credential = vp_request.get("dcql_query", {}).get("credentials", [{}])[0]
  dcql_claims = dcql_credential.get("claims", [])
  if (dcql_credential.get("id") != "account" or dcql_credential.get("format") != "decent_account_jwt_v1" or
      dcql_credential.get("multiple") is not False or
      dcql_credential.get("require_cryptographic_holder_binding") is not True):
    raise ProtocolError("dcql-format-mismatch")
  expected_dcql_claims = [{"id": CLAIM_SHORT[item["id"]], "path": ["claims", item["id"]]} for item in context["claims"]]
  # Authenticate full bytes first; compare only recognized DCQL selection fields.
  recognized_dcql_claims = [{"id": item.get("id"), "path": item.get("path")} for item in dcql_claims]
  if recognized_dcql_claims != expected_dcql_claims:
    raise ProtocolError("dcql-claim-mismatch")
  required_ids = [item["id"] for item in context["claims"] if item["required"]]
  optional_ids = [item["id"] for item in context["claims"] if not item["required"]]
  if not required_ids or len(optional_ids) > 4:
    raise ProtocolError("unsupported-claim-selection-size")
  expected_sets = []
  for count in range(len(optional_ids) + 1):
    for selected in combinations(optional_ids, count):
      selected_ids = set(required_ids) | set(selected)
      expected_sets.append([CLAIM_SHORT[item["id"]] for item in context["claims"] if item["id"] in selected_ids])
  if dcql_credential.get("claim_sets") != expected_sets:
    raise ProtocolError("dcql-claim-sets-mismatch")

  # Bound the complete compact serialization before decoding, parsing or verifying it.
  presentation_token = bundle["presentation_jws"]
  if not isinstance(presentation_token, str) or len(presentation_token.encode("utf-8")) > 16384:
    raise ProtocolError("presentation-too-large")
  owner_key = ed_public(owner_jwk)
  owner_thumb = jwk_thumbprint(owner_jwk)
  _, presentation = verify_jws(presentation_token, "EdDSA", owner_key,
                                typ="decent-account-presentation+jwt", kid=owner_thumb,
                                canonical_payload=True)
  pheader = parse_jws(presentation_token)[1]
  if set(pheader) != {"alg", "kid", "typ"} or b64(rfc8785.dumps(pheader)) != presentation_token.split(".")[0]:
    raise ProtocolError("jws-header-mismatch")
  validate_schema("presentation", presentation)
  if presentation["nonce"] != vp_request["nonce"]:
    raise ProtocolError("presentation-nonce-mismatch")
  if presentation["aud"] != oid4vp_client:
    raise ProtocolError("presentation-audience-mismatch")
  if presentation["iss"] != binding["identity_id"] or presentation["sub"] != binding["identity_id"]:
    raise ProtocolError("presentation-identity-mismatch")
  check_lifetime(presentation, now, "presentation-expired")

  credential_token = presentation["vp"]["verifiableCredential"][0]
  _, credential = verify_jws(credential_token, "EdDSA", owner_key,
                             typ="decent-account-credential+jwt", kid=owner_thumb,
                             canonical_payload=True)
  cheader = parse_jws(credential_token)[1]
  if set(cheader) != {"alg", "kid", "typ"} or b64(rfc8785.dumps(cheader)) != credential_token.split(".")[0]:
    raise ProtocolError("jws-header-mismatch")
  validate_schema("accountCredential", credential)
  validate_purpose(credential["purpose"])
  if credential["iss"] != binding["identity_id"] or credential["sub"] != binding["identity_id"]:
    raise ProtocolError("presentation-identity-mismatch")
  if (credential["owner_key_thumbprint"] != binding["owner_key_thumbprint"] or
      credential["owner_binding_jti"] != binding["jti"]):
    raise ProtocolError("owner-binding-mismatch")
  if credential["transaction_id"] != context["transaction_id"]:
    raise ProtocolError("transaction-mismatch")
  if credential["request_id"] != context["request_id"]:
    raise ProtocolError("request-id-mismatch")
  if (credential["action"] != context["action"] or credential["rp_oidc_client_id"] != context["rp_client_id"] or
      credential["purpose"] != context["purpose"]):
    raise ProtocolError("presentation-context-mismatch")
  claim_ids = set(credential["claims"])
  approved = bundle["wallet_approved_claim_ids"]
  required = {item["id"] for item in context["claims"] if item["required"]}
  requested = {item["id"] for item in context["claims"]}
  if not claim_ids.issubset(requested):
    raise ProtocolError("unrequested-claim")
  if not required.issubset(claim_ids):
    raise ProtocolError("required-claim-missing")
  if not isinstance(approved, list) or len(approved) != len(set(approved)) or set(approved) != claim_ids:
    raise ProtocolError("claim-not-approved")
  selected_short_ids = [CLAIM_SHORT[item] for item in initial_ids if item in claim_ids]
  if selected_short_ids not in dcql_credential["claim_sets"]:
    raise ProtocolError("dcql-claim-set-mismatch")
  for value in credential["claims"].values():
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 1024:
      raise ProtocolError("invalid-claim-value")
  check_lifetime(credential, now, "presentation-expired")
  if credential["exp"] > min(context["expires_at"], binding["exp"]):
    raise ProtocolError("presentation-expiry-too-late")
  if presentation["exp"] > min(credential["exp"], context["expires_at"], vp_request["exp"]):
    raise ProtocolError("presentation-expiry-too-late")
  if credential["jti"] == presentation["jti"]:
    raise ProtocolError("duplicate-presentation-jti")
  if credential["iss"] != presentation["iss"] or credential["sub"] != presentation["sub"]:
    raise ProtocolError("presentation-identity-mismatch")

  if len(b64d(vp_request["state"])) < 16:
    raise ProtocolError("oid4vp-state-too-short")
  response = bundle["direct_post_response"]
  try:
    validate_schema("vpTokenResponse", response)
  except jsonschema.ValidationError as exc:
    raise ProtocolError("direct-post-response-schema-invalid") from exc
  if (response.get("state") != vp_request["state"] or
      response.get("vp_token") != {"account": [bundle["presentation_jws"]]}):
    raise ProtocolError("direct-post-response-mismatch")
  reply = bundle["direct_post_reply"]
  if (set(reply) != {"http_status", "content_type", "cache_control", "body"} or
      reply.get("http_status") != 200 or reply.get("content_type") != "application/json" or
      reply.get("cache_control") != "no-store" or not isinstance(reply.get("body"), dict) or
      "redirect_uri" not in reply["body"]):
    raise ProtocolError("direct-post-reply-mismatch")
  redirect = urlsplit(reply.get("body", {}).get("redirect_uri", ""))
  fragment = redirect.fragment.split("=", 1)
  if (redirect.scheme != "https" or redirect.hostname != client_host or redirect.path != "/oid4vp/return" or
      redirect.query or len(fragment) != 2 or fragment[0] != "response_code" or len(b64d(fragment[1])) != 32):
    raise ProtocolError("direct-post-redirect-mismatch")
  return True


def verify_claim_schema_invariants():
  # uniqueItems compares whole objects; conflicting flags must not hide a repeated ID.
  ids = SCHEMA["$defs"]["requestClaim"]["properties"]["id"]["enum"]
  for claim_id in ids:
    validate_schema("claims", [{"id": claim_id, "required": True}])
    for first in (False, True):
      for second in (False, True):
        claims = [{"id": claim_id, "required": first}, {"id": claim_id, "required": second}]
        try:
          validate_schema("claims", claims)
        except jsonschema.ValidationError:
          continue
        raise SystemExit("claim schema accepted a duplicate claim ID")
  validate_schema("claims", [{"id": item, "required": True} for item in ids])
  validate_schema("claims", [
    {"id": "urn:decent:account:v1:given_name", "required": True},
    {"id": "urn:decent:account:v1:email", "required": False},
  ])
  try:
    validate_schema("claims", [{"id": "urn:decent:account:v1:email", "required": False}])
  except jsonschema.ValidationError:
    pass
  else:
    raise SystemExit("claim schema accepted a request with no required claim")


def main():
  verify_claim_schema_invariants()
  valid_paths = sorted((ROOT / "vectors").glob("valid-*.json"))
  if not valid_paths:
    raise SystemExit("no positive vectors found")
  for valid_path in valid_paths:
    validate_bundle(json.loads(valid_path.read_text(encoding="utf-8")))
  negatives = json.loads((ROOT / "vectors/negative.json").read_text(encoding="utf-8"))["vectors"]
  seen = set()
  for vector in negatives:
    case_id = vector["id"]
    if case_id in seen:
      raise SystemExit(f"duplicate negative vector id: {case_id}")
    seen.add(case_id)
    try:
      validate_bundle(vector["bundle"])
    except ProtocolError as exc:
      if exc.code != vector["expected"]:
        raise SystemExit(f"{case_id}: expected {vector['expected']}, got {exc.code}") from exc
    except jsonschema.ValidationError as exc:
      raise SystemExit(f"{case_id}: unexpected schema failure at {list(exc.path)}") from exc
    else:
      raise SystemExit(f"{case_id}: invalid vector was accepted")
  print(f"PASS {len(valid_paths)} positive vectors; rejected {len(negatives)} negative vectors")
  for vector in negatives:
    print(f"PASS {vector['id']} -> {vector['expected']}")


if __name__ == "__main__":
  try:
    main()
  except ProtocolError as exc:
    print(f"FAIL protocol error: {exc.code}", file=sys.stderr)
    raise SystemExit(1)
  except jsonschema.ValidationError as exc:
    print(f"FAIL schema validation: {list(exc.path)}", file=sys.stderr)
    raise SystemExit(1)

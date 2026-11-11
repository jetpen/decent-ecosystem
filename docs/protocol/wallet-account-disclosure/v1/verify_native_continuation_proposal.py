#!/usr/bin/env python3
"""Offline verifier for the UNADOPTED native-continuation proposal only.

No HTTP, Android, Keycloak runtime, persistence, or deployment is qualified.
The adopted verifier and its vectors remain unchanged. Native signed bytes are
passed verbatim to its full validator through a schema-only variant adapter.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import hmac
import importlib.util
import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import jsonschema
from cryptography import x509
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent
BASE_SCHEMA = json.loads((ROOT / 'schemas/profile.schema.json').read_text())
PROPOSAL_SCHEMA = json.loads((ROOT / 'native-continuation.schema.proposal.json').read_text())
REGISTRY = Registry().with_resource(BASE_SCHEMA['$id'], Resource.from_contents(BASE_SCHEMA))


class ProposalError(Exception):
  pass


def load_adopted_verifier(module_name):
  """Private module instances isolate proposal adaptation from adopted checks."""
  spec = importlib.util.spec_from_file_location(module_name, ROOT / 'verify.py')
  if spec is None or spec.loader is None:
    raise RuntimeError('cannot load adopted verifier')
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


ADOPTED = load_adopted_verifier('native_proposal_adopted_validation')
_ADOPTED_VALIDATE_SCHEMA = ADOPTED.validate_schema
b64, b64d, parse_jws = ADOPTED.b64, ADOPTED.b64d, ADOPTED.parse_jws


def validate_schema(name, value):
  wrapper = copy.copy(PROPOSAL_SCHEMA)
  wrapper['$ref'] = '#/$defs/' + name
  jsonschema.Draft202012Validator(wrapper, format_checker=jsonschema.FormatChecker(),
    registry=REGISTRY).validate(value)


def validate_adopted_native_schema(name, value):
  """Validate native additions FIRST, then project only a schema input copy.

  Never strip/rewrite a signed payload, re-sign it, or pass a synthetic bundle
  to validate_bundle. All adopted non-schema semantics see the original fields.
  """
  variants = {'accountRequest': ('nativeAccountRequest', 'decent_native_continuation'),
              'context': ('nativeContextOptedIn', 'decent_native_continuation'),
              'binding': ('nativeBinding', 'continuation_capability_hash')}
  if name in variants:
    variant, addition = variants[name]
    validate_schema(variant, value)
    value = copy.deepcopy(value)
    value.pop(addition)
  _ADOPTED_VALIDATE_SCHEMA(name, value)


ADOPTED.validate_schema = validate_adopted_native_schema


def validate_time(payload, now, code, max_lifetime=None):
  """Ordinary ID tokens intentionally have NO 300-second lifetime cap."""
  iat, exp = payload.get('iat'), payload.get('exp')
  if (type(iat) is not int or type(exp) is not int or iat > now + 60 or
      exp <= now or exp <= iat or (max_lifetime is not None and exp - iat > max_lifetime)):
    raise ProposalError(code)


def validate_request_expiry(request_exp, capability_exp, binding_exp):
  if (any(type(value) is not int for value in (request_exp, capability_exp, binding_exp)) or
      request_exp > capability_exp or request_exp > binding_exp):
    raise ProposalError('request-object-expiry')


def reject_capability_leakage(value, capability, allowed_paths=frozenset(), path=()):
  """Proposal sender-artifact policy, NOT adopted receiver extension policy.

  Inspect supplied JSON values/member names, nested JSON strings and percent
  escaping (including URL paths/query/fragments). Signed contents must already
  be authenticated by the caller. Only exact intended raw-capability leaves
  are exempt. A hash is not the raw capability and needs no blanket exemption.
  This offline check cannot inspect live redirects, pages, storage, logs,
  telemetry or arbitrary encodings/other artifacts absent from the bundle.
  """
  if path in allowed_paths:
    return
  if isinstance(value, dict):
    for name, item in value.items():
      reject_capability_leakage(name, capability)
      reject_capability_leakage(item, capability, allowed_paths, path + (name,))
  elif isinstance(value, list):
    for index, item in enumerate(value):
      reject_capability_leakage(item, capability, allowed_paths, path + (index,))
  elif isinstance(value, str):
    if capability in value:
      raise ProposalError('capability-sender-artifact-leak')
    decoded = unquote(value)
    if decoded != value:
      reject_capability_leakage(decoded, capability)
    # Preserve every nested JSON member, including overwritten duplicates and
    # Unicode-escaped names/values, as lists traversed by the same leakage check.
    try:
      nested = json.loads(value, object_pairs_hook=lambda pairs: [[key, item] for key, item in pairs])
    except (ValueError, TypeError):
      return
    reject_capability_leakage(nested, capability)


def _validate_native(vector):
  validate_schema('nativeVector', vector)
  bundle = vector['bundle']
  now = bundle['validation_time']
  if now != vector['validation_time']:
    raise ProposalError('base-bundle')
  context = bundle['keycloak_context']
  rp_jwk = bundle['rp_client_id_jwk']
  jar_header, jar = ADOPTED.verify_jws(bundle['initial_oidc_request_jws'], 'ES256', ADOPTED.ec_public(rp_jwk),
    typ='oauth-authz-req+jwt', kid=rp_jwk['kid'], canonical_payload=True)
  if jar.get('aud') != context['keycloak_issuer']:
    raise ProposalError('native-oidc-request-audience')
  req = jar['decent_account_request']
  validate_schema('nativeAccountRequest', req)
  ADOPTED.validate_purpose(req['purpose'])
  ADOPTED.validate_purpose(context['purpose'])
  validate_time(jar, now, 'native-oidc-request-policy', 300)
  if (jar.get('iss') != jar.get('client_id') or jar.get('client_id') != context['rp_client_id'] or
      jar.get('nonce') != context['oidc_nonce'] or jar.get('decent_account_action') not in ADOPTED.ACCOUNT_ACTIONS or
      jar.get('response_mode') != 'form_post' or jar.get('response_type') != 'code' or
      jar.get('code_challenge_method') != 'S256' or len(b64d(jar.get('state', ''))) < 16 or
      len(b64d(jar.get('code_challenge', ''))) != 32 or
      jar.get('redirect_uri') != context['rp_origin'] + '/oidc/callback'):
    raise ProposalError('native-oidc-request-policy')
  if vector['account_request'] != req:
    raise ProposalError('request-opt-in-projection')
  if vector['context'] != context:
    raise ProposalError('context-bundle-projection')
  if (context['request_id'] != req['request_id'] or context['claims'] != req['claims'] or
      context['purpose'] != req['purpose'] or context['action'] != jar['decent_account_action']):
    raise ProposalError('context-request-binding')
  if vector['registered_client'] != {'client_id': context['rp_client_id'], 'confidential': True,
                                     'native_continuation_enabled': True}:
    raise ProposalError('registered-client-policy')

  kc_jwk = bundle['keycloak_jwks']['keys'][0]
  kc_key = ADOPTED.rsa_public(kc_jwk)
  binding_header, binding = ADOPTED.verify_jws(bundle['owner_key_binding_jws'], 'RS256', kc_key,
    typ='decent-owner-key-binding+jwt', kid=kc_jwk['kid'])
  id_token_header, id_token = ADOPTED.verify_jws(bundle['id_token_jws'], 'RS256', kc_key, typ='JWT', kid=kc_jwk['kid'])
  validate_schema('nativeBinding', binding)
  # Each temporal object is checked on its own signed values, before aliases or
  # dependent ceiling comparisons can mask an expired/future statement.
  validate_time(binding, now, 'binding-expiry', 300)
  validate_time(id_token, now, 'id-token-expiry')
  capability = id_token.get('decent_account_continuation_capability')
  cap_exp = id_token.get('decent_account_continuation_expires_at')
  validate_schema('nativeIdTokenClaims', {
    'decent_account_continuation_capability': capability, 'decent_account_continuation_expires_at': cap_exp})
  raw_capability = b64d(capability)
  if len(raw_capability) != 32 or capability != vector['capability_bytes_test_only']:
    raise ProposalError('capability-shape')
  if (type(cap_exp) is not int or cap_exp <= now or cap_exp > vector['proof_accepted_at'] + 300 or
      vector['proof_accepted_at'] > now):
    raise ProposalError('capability-response-expiry')
  cert_info = bundle['rp_certificate']
  cert = x509.load_der_x509_certificate(base64.b64decode(cert_info['leaf_der_base64'], validate=True))
  request_header, request = ADOPTED.verify_jws(bundle['oid4vp_request_jws'], 'ES256', cert.public_key(),
    typ='oauth-authz-req+jwt', kid=rp_jwk['kid'], canonical_payload=True)
  # Detect explicit reuse in authenticated bytes, not live RNG independence.
  if request.get('nonce') == jar.get('nonce'):
    raise ProposalError('oidc-oid4vp-nonce-reuse')
  validate_time(request, now, 'request-object-expiry', 300)
  # These use VERIFIED signed binding/capability claims, never display aliases.
  validate_request_expiry(request.get('exp'), cap_exp, binding['exp'])
  if request['exp'] != vector['request_object_expires_at']:
    raise ProposalError('request-object-expiry')
  if cap_exp > context['expires_at']:
    raise ProposalError('capability-response-expiry')
  if binding['exp'] > cap_exp:
    raise ProposalError('binding-expiry')
  if (vector['capability_response']['body']['expires_at'] != cap_exp or
      vector['capability_expires_at'] != cap_exp):
    raise ProposalError('capability-response-expiry')
  claims = {'decent_account_continuation_capability': capability,
            'decent_account_continuation_expires_at': cap_exp}
  if (vector['id_token_claims'] != claims or
      vector['capability_response']['body']['decent_account_continuation_capability'] != capability):
    raise ProposalError('id-token-capability-claim')
  digest = b64(hashlib.sha256(raw_capability).digest())
  if (not hmac.compare_digest(binding['continuation_capability_hash'], digest) or
      vector['capability_sha256_b64url'] != digest or
      vector['binding']['continuation_capability_hash'] != digest):
    raise ProposalError('binding-capability-hash')
  if vector['binding'] != binding:
    raise ProposalError('binding-context')
  # Independence is an issuer CSPRNG requirement; offline equality checks catch
  # explicit reuse, not entropy or statistical independence in a live issuer.
  forbidden = {context['oidc_nonce'], context['transaction_id'], context['request_id'],
    bundle['transaction_handle'], jar.get('state'), request.get('state'), request.get('nonce'),
    request.get('jti'), binding['jti']}
  if capability in forbidden:
    raise ProposalError('capability-not-independent')

  # Signatures above precede inspection of decoded signed objects. Unknown
  # extensions stay ignored by the adopted receiver; native senders must not
  # use them to leak the bearer capability. All supplied unsigned URL fields
  # and test projections are also checked, not just query/fragment components.
  for artifact in (jar_header, jar, request_header, request, binding_header,
                   binding, id_token_header):
    reject_capability_leakage(artifact, capability)
  reject_capability_leakage(id_token, capability,
    frozenset({('decent_account_continuation_capability',)}))
  reject_capability_leakage(vector, capability, frozenset({
    ('capability_bytes_test_only',), ('poll_authorization',),
    ('capability_response', 'body', 'decent_account_continuation_capability'),
    ('id_token_claims', 'decent_account_continuation_capability')}))

  expected_outer = {'client_id': bundle['oid4vp_client_id'], 'request_uri': bundle['oid4vp_request_uri']}
  if bundle['oid4vp_authorization_parameters'] != expected_outer or vector['outer_authorization_parameters'] != expected_outer:
    raise ProposalError('outer-authorization-parameters')
  origin = urlsplit(context['rp_origin'])
  uri = urlsplit(vector['poll_url'])
  if (uri.scheme != 'https' or uri.netloc != origin.netloc or uri.username or uri.password or
      uri.path != '/oid4vp/continuations/' + context['transaction_id'] or uri.query or uri.fragment):
    raise ProposalError('poll-url')
  if vector['poll_authorization'] != 'Bearer ' + capability:
    raise ProposalError('poll-authorization')
  if vector['retry_after'] != int(vector['poll_pending']['headers']['retry-after']):
    raise ProposalError('poll-pending')
  if vector['poll_ready']['body'] != expected_outer or vector['poll_http'] != vector['poll_ready']['http_status']:
    raise ProposalError('poll-ready')
  uri = urlsplit(bundle['oid4vp_request_uri'])
  if uri.scheme != 'https' or uri.netloc != origin.netloc or uri.username or uri.password or uri.query or uri.fragment:
    raise ProposalError('request-uri-origin')
  if (vector['request_uri_jws'] != bundle['oid4vp_request_jws'] or
      vector['request_uri_response']['body'] != bundle['oid4vp_request_jws']):
    raise ProposalError('request-uri-bytes')
  if vector['request_uri_retry_response'] != vector['request_uri_response']:
    raise ProposalError('request-immutability')
  direct = vector['direct_post_acceptance']
  if direct['state'] != bundle['direct_post_response']['state'] or direct['vp_token'] != bundle['presentation_jws']:
    raise ProposalError('direct-post-envelope')

  # FULL adopted OID4VP/DCQL/certificate/credential/VP/response validation sees
  # exactly the original signed native bundle. Only its schema-input copies are
  # projected by the private adapter, after native closed-schema validation.
  ADOPTED.validate_bundle(bundle)
  # Adopted validation has now authenticated the presentation and credential.
  # Inspect their decoded contents only after those signatures/schema checks.
  _, presentation_header, presentation, _ = parse_jws(bundle['presentation_jws'])
  _, credential_header, credential, _ = parse_jws(presentation['vp']['verifiableCredential'][0])
  for artifact in (presentation_header, presentation, credential_header, credential):
    reject_capability_leakage(artifact, capability)
  return True


def validate_native(vector, base=None):
  """`base` is retained for callers; no base payload substitutes native bytes."""
  try:
    return _validate_native(vector)
  except ADOPTED.ProtocolError as exc:
    raise ProposalError(exc.code) from exc


def apply_patches(vector, patches):
  result = copy.deepcopy(vector)
  for patch in patches:
    target = result
    for part in patch['path'][:-1]:
      target = target[part]
    target[patch['path'][-1]] = copy.deepcopy(patch['value'])
  return result


def disposition(vector):
  """Classification is independent of the fixture ID and expected result."""
  try:
    validate_native(vector)
  except jsonschema.ValidationError as exc:
    codes = {('account_request', 'decent_native_continuation'): 'request-opt-in-projection',
             ('context', 'decent_native_continuation'): 'context-request-binding'}
    return codes.get(tuple(exc.path), 'schema-reject')
  except ProposalError as exc:
    return str(exc)
  return 'accept'


def verify_document(document):
  validate_schema('nativeDocument', document)
  seen = {document['positive']['id']}
  validate_native(document['positive'])
  for case in document['positive_cases'] + document['negative']:
    if case['id'] in seen:
      raise ProposalError('duplicate-native-vector-id')
    seen.add(case['id'])
    actual = disposition(apply_patches(document['positive'], case['patches']))
    if actual != case['expected']:
      raise ProposalError(f"{case['id']}: expected {case['expected']}, got {actual}")
  return 1 + len(document['positive_cases']), len(document['negative'])


def main():
  # A second, UNADAPTED private instance verifies all adopted artifacts unchanged.
  adopted = load_adopted_verifier('unchanged_adopted_vector_validation')
  adopted.main()
  document = json.loads((ROOT / 'vectors/continuation_vectors.proposal.json').read_text())
  positives, negatives = verify_document(document)
  print(f'PASS {positives} native proposal positives; rejected {negatives} native amendment negatives')


if __name__ == '__main__':
  try:
    main()
  except (ProposalError, jsonschema.ValidationError, ValueError, KeyError, TypeError) as exc:
    print(f'FAIL native proposal verifier: {exc}', file=sys.stderr)
    raise SystemExit(1)

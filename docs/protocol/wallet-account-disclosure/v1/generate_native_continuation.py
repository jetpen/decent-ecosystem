#!/usr/bin/env python3
"""Generate normative native-continuation fixtures with PUBLIC TEST-ONLY keys.

The EC scalar 1 and Ed25519 seed bytes(range(32)) are intentionally public.
RSA keys are fresh throwaway test keys; only public keys/signatures are emitted.
Every signed case is regenerated together; prior output is never read.
No environment, credentials, network, or machine-specific paths are used.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import rfc8785
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parent
PROFILE = 'decent-account-disclosure-v1'
COMMIT = 'b861b8c7a088dd21c79e064c8dbb52a0e0e96eb8'
VECTOR_SET = PROFILE + '-native-continuation-1'
# Public deterministic test source, distinct from the adopted OID4VP nonce.
OIDC_NONCE_BYTES = bytes(range(64, 96))


def enc(raw):
  return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def payload(token):
  part = token.split('.')[1]
  return json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))


def sign(alg, header, value, key):
  h, p = enc(rfc8785.dumps(header)), enc(rfc8785.dumps(value))
  data = (h + '.' + p).encode('ascii')
  if alg == 'ES256':
    r, s = decode_dss_signature(key.sign(data, ec.ECDSA(hashes.SHA256())))
    signature = r.to_bytes(32, 'big') + s.to_bytes(32, 'big')
  elif alg == 'RS256':
    signature = key.sign(data, padding.PKCS1v15(), hashes.SHA256())
  elif alg == 'EdDSA':
    signature = key.sign(data)
  else:
    raise ValueError(alg)
  return h + '.' + p + '.' + enc(signature)


def apply(value, patches):
  """Apply explicit path/value replacements; array indexes are integers."""
  result = copy.deepcopy(value)
  for patch in patches:
    target = result
    for part in patch['path'][:-1]:
      target = target[part]
    target[patch['path'][-1]] = copy.deepcopy(patch['value'])
  return result


def differences(before, after, path=()):
  """Produce portable explicit replacements, not ID-dependent runner behavior."""
  if before == after:
    return []
  if isinstance(before, dict) and isinstance(after, dict) and before.keys() == after.keys():
    return [patch for key in before for patch in differences(before[key], after[key], path + (key,))]
  return [{'path': list(path), 'value': after}]


class FixtureFactory:
  def __init__(self):
    self.base = json.loads((ROOT / 'vectors/valid-signup.json').read_text())
    self.now = self.base['validation_time']
    self.rp_key = ec.derive_private_key(1, ec.SECP256R1())
    self.owner_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    self.kc_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = self.rp_key.public_key().public_numbers()
    self.rp_jwk = {'kty': 'EC', 'crv': 'P-256', 'x': enc(numbers.x.to_bytes(32, 'big')),
                   'y': enc(numbers.y.to_bytes(32, 'big'))}
    self.rp_jwk['kid'] = enc(hashlib.sha256(rfc8785.dumps(self.rp_jwk)).digest())
    self.rp_jwk.update(use='sig', alg='ES256')
    numbers = self.kc_key.public_key().public_numbers()
    encode_int = lambda n: enc(n.to_bytes((n.bit_length() + 7) // 8, 'big'))
    self.kc_jwk = {'kty': 'RSA', 'n': encode_int(numbers.n), 'e': encode_int(numbers.e),
                   'kid': 'kc-native-public-test-only', 'use': 'sig', 'alg': 'RS256'}
    self.owner_jwk = {'kty': 'OKP', 'crv': 'Ed25519', 'x': enc(self.owner_key.public_key().public_bytes(
      serialization.Encoding.Raw, serialization.PublicFormat.Raw))}
    self.owner_thumb = enc(hashlib.sha256(rfc8785.dumps(self.owner_jwk)).digest())
    self.owner_jwk['kid'] = self.owner_thumb
    self.cert = self.certificate()

  def certificate(self, host='site.example.test', start=2025, end=2040):
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
      .public_key(self.rp_key.public_key()).serial_number(0x5151)
      .not_valid_before(datetime(start, 1, 1, tzinfo=timezone.utc))
      .not_valid_after(datetime(end, 1, 1, tzinfo=timezone.utc))
      .add_extension(x509.SubjectAlternativeName([x509.DNSName(host)]), critical=False)
      .sign(self.rp_key, hashes.SHA256()))
    return {'leaf_der_base64': base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode('ascii'),
            'trust_anchor_sha256': cert.fingerprint(hashes.SHA256()).hex()}

  def build(self, changes=None):
    """Re-sign dependencies before applying caller's deliberate semantic faults."""
    changes = changes or {}
    change = lambda name, obj: apply(obj, changes.get(name, []))
    bundle = copy.deepcopy(self.base)
    cap = changes.get('capability', enc(bytes(range(32))))
    cap_exp = changes.get('cap_exp', 1800000240)
    context = bundle['keycloak_context']
    context.update(decent_native_continuation=True, oidc_nonce=enc(OIDC_NONCE_BYTES))
    context = change('context', context)
    bundle['keycloak_context'] = context
    jar = payload(bundle['initial_oidc_request_jws'])
    jar['decent_account_request']['decent_native_continuation'] = True
    jar.update(nonce=context['oidc_nonce'], aud=context['keycloak_issuer'], response_mode='form_post')
    jar = change('jar', jar)
    bundle['rp_client_id_jwk'] = copy.deepcopy(self.rp_jwk)
    bundle['keycloak_jwks'] = {'keys': [self.kc_jwk]}
    bundle['owner_jwk'] = copy.deepcopy(self.owner_jwk)
    cert = changes.get('certificate', self.cert)
    bundle['rp_certificate'] = copy.deepcopy(cert)
    bundle['initial_oidc_request_jws'] = sign('ES256', {
      'alg': 'ES256', 'typ': 'oauth-authz-req+jwt', 'kid': self.rp_jwk['kid']}, jar, self.rp_key)
    binding = payload(bundle['owner_key_binding_jws'])
    binding.update(oidc_nonce=context['oidc_nonce'], exp=cap_exp,
      continuation_capability_hash=enc(hashlib.sha256(base64.urlsafe_b64decode(cap + '=')).digest()),
      owner_key={k: self.owner_jwk[k] for k in ('kty', 'crv', 'x')}, owner_key_thumbprint=self.owner_thumb)
    binding = change('binding', binding)
    binding_token = sign('RS256', {'alg': 'RS256', 'typ': 'decent-owner-key-binding+jwt',
      'kid': self.kc_jwk['kid']}, binding, self.kc_key)
    bundle['owner_key_binding_jws'] = binding_token
    id_token = payload(bundle['id_token_jws'])
    id_token.update(nonce=context['oidc_nonce'], decent_owner_key_binding=binding_token,
      decent_account_continuation_capability=cap, decent_account_continuation_expires_at=cap_exp)
    id_token = change('id_token', id_token)
    bundle['id_token_jws'] = sign('RS256', {'alg': 'RS256', 'typ': 'JWT', 'kid': self.kc_jwk['kid']},
      id_token, self.kc_key)
    request = payload(bundle['oid4vp_request_jws'])
    request['decent_account']['owner_key_binding'] = binding_token
    request['exp'] = min(request['exp'], cap_exp, binding['exp'])
    request = change('request', request)
    request_token = sign('ES256', {'alg': 'ES256', 'typ': 'oauth-authz-req+jwt',
      'kid': self.rp_jwk['kid'], 'x5c': [cert['leaf_der_base64']]}, request, self.rp_key)
    bundle['oid4vp_request_jws'] = request_token
    bundle['oid4vp_request_uri'] = 'https://site.example.test/oid4vp/requests/' + enc(b'native-request-locator-00000001')
    bundle['oid4vp_authorization_parameters'] = {'client_id': bundle['oid4vp_client_id'],
      'request_uri': bundle['oid4vp_request_uri']}
    presentation = payload(bundle['presentation_jws'])
    credential = payload(presentation['vp']['verifiableCredential'][0])
    credential['owner_key_thumbprint'] = self.owner_thumb
    credential['exp'] = min(credential['exp'], binding['exp'], context['expires_at'])
    credential = change('credential', credential)
    credential_token = sign('EdDSA', {'alg': 'EdDSA', 'typ': 'decent-account-credential+jwt',
      'kid': self.owner_thumb}, credential, self.owner_key)
    presentation['vp']['verifiableCredential'] = [credential_token]
    presentation['exp'] = min(presentation['exp'], credential['exp'], request['exp'])
    presentation = change('presentation', presentation)
    presentation_token = sign('EdDSA', {'alg': 'EdDSA', 'typ': 'decent-account-presentation+jwt',
      'kid': self.owner_thumb}, presentation, self.owner_key)
    bundle['presentation_jws'] = presentation_token
    bundle['direct_post_response']['vp_token'] = {'account': [presentation_token]}
    empty_headers = {'cache-control': 'no-store', 'referrer-policy': 'no-referrer'}
    request_response = {'http_status': 200, 'content_type': 'application/oauth-authz-req+jwt',
      'cache_control': 'no-store', 'referrer_policy': 'no-referrer', 'body': request_token}
    vector = {
      'vector_set': VECTOR_SET, 'id': 'native-signup-ready', 'kind': 'positive',
      'base_vector': 'valid-signup.json', 'validation_time': self.now, 'proof_accepted_at': 1800000000,
      'source_profile_commit': COMMIT, 'test_only': True,
      'account_request': jar['decent_account_request'], 'context': context, 'binding': binding,
      'registered_client': {'client_id': 'site-client', 'confidential': True, 'native_continuation_enabled': True},
      'capability_response': {'http_status': 200, 'content_type': 'application/json', 'cache_control': 'no-store',
        'body': {'profile': PROFILE, 'decent_account_continuation_capability': cap, 'expires_at': cap_exp}},
      'capability_bytes_test_only': cap, 'capability_sha256_b64url': binding['continuation_capability_hash'],
      'capability_expires_at': cap_exp,
      'id_token_claims': {'decent_account_continuation_capability': cap, 'decent_account_continuation_expires_at': cap_exp},
      'poll_url': 'https://site.example.test/oid4vp/continuations/' + context['transaction_id'],
      'poll_authorization': 'Bearer ' + cap,
      'poll_pending': {'http_status': 202, 'headers': dict(empty_headers, **{'retry-after': '2'}), 'body': {}},
      'poll_ready': {'http_status': 200, 'headers': dict(empty_headers, **{'content-type': 'application/json'}),
        'body': bundle['oid4vp_authorization_parameters']},
      'poll_terminal': {'http_status': 410, 'headers': dict(empty_headers), 'body': {}},
      'poll_unknown': {'http_status': 404, 'headers': dict(empty_headers), 'body': {}},
      'outer_authorization_parameters': bundle['oid4vp_authorization_parameters'],
      'request_uri_jws': request_token, 'request_uri_response': request_response,
      'request_uri_retry_response': copy.deepcopy(request_response), 'request_object_expires_at': request['exp'],
      'poll_http': 200, 'retry_after': 2, 'request_bytes_retrieved': True,
      'request_bytes_repeat_identically': True, 'request_uri_jti_state_nonce_reused': True,
      'oidc_callback': {'response_mode': 'form_post', 'server_side_confidential_client': True,
        'validated_before_poll_ready': True, 'id_token_or_capability_exposed_to_browser': False,
        'clean_same_origin_redirect_after_processing': True},
      'failure': {'uncertain_keycloak_acceptance_write': 'no-code-no-capability-fresh-login',
        'no-browser-fallback': True, 'lost_wallet_post_response':
        'fresh-end-to-end-transaction-new-proof-approval-existing-action-preconditions-fail-closed-if-principal-changed'},
      'capability_storage': {'keycloak_durable_value': 'sha256-only',
        'raw_keycloak_value': 'private-authentication-session-note-until-id-token-issuance',
        'raw_rp_value': 'transient-until-hash-verified-then-discarded',
        'rp_durable_value': 'sha256-only-with-transaction-binding-expiry-and-continuation-state',
        'raw_wallet_value': 'authenticated-encrypted-pending-approval-only'},
      'keycloak_auth_post': {'kind': 'native', 'origin': None, 'sec_fetch_site': None,
        'sec_fetch_mode': None, 'sec_fetch_dest': None},
      'browser_post_rejection': {'http_status': 403, 'body': {}, 'cache_control': 'no-store', 'proof_consumed': False},
      'accepted_proof_retry': {'http_status': 202, 'body': {'status': 'accepted'}, 'capability_returned': False},
      'direct_post_acceptance': {'path': '/oid4vp/response', 'state': bundle['direct_post_response']['state'],
        'vp_token': presentation_token, 'atomic_acceptance_revokes_capability': True,
        'subsequent_poll_http': 410, 'identical_presentation_retry': 'existing-profile-byte-identical-retry-only'},
      'bundle': bundle, 'expected': 'accept',
    }
    # Return JSON-like independent trees, not accidental shared projection objects.
    return copy.deepcopy(json.loads(json.dumps(vector)))


def patch(path, value):
  return {'path': path.split('.') if isinstance(path, str) else path, 'value': value}


def generate():
  factory = FixtureFactory()
  positive = factory.build()
  negatives, positives = [], []

  def mutated(case_id, path, value, expected):
    negatives.append({'id': case_id, 'patches': [patch(path, value)], 'expected': expected})

  def signed(case_id, changes, expected, accept=False):
    candidate = factory.build(changes)
    (positives if accept else negatives).append({'id': case_id,
      'patches': differences(positive, candidate), 'expected': expected})

  # The original 22 invariant negatives, with all signed bytes regenerated.
  for case_id, path, value, expected in [
    ('accepted-presentation-does-not-revoke', 'direct_post_acceptance.subsequent_poll_http', 200, 'schema-reject'),
    ('binding-capability-hash-mismatch', 'binding.continuation_capability_hash', 'A' * 43, 'binding-capability-hash'),
    ('binding-subject-mismatch', 'binding.sub', 'wrong-subject', 'binding-context'),
    ('browser-post-accepted', 'browser_post_rejection.proof_consumed', True, 'schema-reject'),
    ('capability-expiry-mismatch', 'capability_response.body.expires_at', 1800000239, 'capability-response-expiry'),
    ('capability-wrong-length', 'capability_response.body.decent_account_continuation_capability', enc(bytes(range(16))), 'schema-reject'),
    ('context-bundle-mismatch', 'bundle.keycloak_context.transaction_id', 'A' * 43, 'context-bundle-projection'),
    ('context-opt-in-false', 'context.decent_native_continuation', False, 'context-request-binding'),
    ('id-token-capability-mismatch', 'id_token_claims.decent_account_continuation_capability', 'A' * 43, 'id-token-capability-claim'),
    ('id-token-context-projection-mismatch', 'id_token_claims.decent_account_continuation_expires_at', 1800000239, 'id-token-capability-claim'),
    ('oidc-gate-bypassed', 'oidc_callback.validated_before_poll_ready', False, 'schema-reject'),
    ('poll-capability-mismatch', 'poll_authorization', 'Bearer ' + 'A' * 43, 'poll-authorization'),
    ('poll-http-summary-mismatch', 'poll_http', 202, 'poll-ready'),
    ('poll-pending-leaks-request', 'poll_pending.body', {'request_uri': 'https://site.example.test/oid4vp/requests/leak'}, 'schema-reject'),
    ('poll-ready-client-mismatch', 'poll_ready.body.client_id', 'x509_san_dns:attacker.example', 'poll-ready'),
    ('request-jws-projection-mismatch', 'request_uri_jws', 'different-request-bytes', 'request-uri-bytes'),
    ('request-opt-in-projection-mismatch', 'account_request.decent_native_continuation', False, 'request-opt-in-projection'),
    ('request-response-byte-mismatch', 'request_uri_response.body', 'not-the-object-asserted-by-alias', 'request-uri-bytes'),
    ('request-retry-bytes-differ', 'request_uri_retry_response.body', 'changed-response-bytes', 'request-immutability'),
    ('request-uri-bytes-change', 'request_uri_response.body', 'not-the-signed-request', 'request-uri-bytes'),
    ('retry-returns-capability', 'accepted_proof_retry.capability_returned', True, 'schema-reject'),
  ]:
    mutated(case_id, path, value, expected)
  signed('request-object-signed-expiry-too-late', {'request': [patch('exp', 1800000241)]}, 'request-object-expiry')
  signed('native-oidc-audience-mismatch', {'jar': [patch('aud', 'https://wrong.example.test/realms/site')]}, 'native-oidc-request-audience')
  for label, purpose in [('whitespace', '   '), ('control', 'Create\naccount'), ('bidi', 'Create\u202eaccount')]:
    signed('native-purpose-' + label, {'jar': [patch('decent_account_request.purpose', purpose)]}, 'invalid-purpose')
  signed('native-context-purpose-control', {'context': [patch('purpose', 'Create\naccount')]}, 'invalid-purpose')
  signed('request-mode-not-direct-post', {'request': [patch('response_mode', 'fragment')]}, 'unsupported-response-mode')
  signed('request-response-uri-wrong-host', {'request': [patch('response_uri', 'https://wrong.example.test/oid4vp/response')]}, 'response-uri-host-mismatch')
  signed('request-audience-wrong', {'request': [patch('aud', 'https://wrong.example.test')]}, 'request-client-mismatch')
  signed('request-dcql-claim-path-wrong', {'request': [patch(['dcql_query', 'credentials', 0, 'claims', 0, 'path'], ['claims', 'urn:decent:account:v1:given_name'])]}, 'dcql-claim-mismatch')
  signed('request-dcql-claim-sets-wrong', {'request': [patch(['dcql_query', 'credentials', 0, 'claim_sets'], [['given_name']])]}, 'dcql-claim-sets-mismatch')
  signed('request-extension-context-wrong', {'request': [patch('decent_account.transaction_id', 'A' * 43)]}, 'request-context-mismatch')
  signed('request-certificate-san-wrong', {'certificate': factory.certificate(host='wrong.example.test')}, 'response-uri-host-mismatch')
  signed('request-certificate-expired', {'certificate': factory.certificate(end=2026)}, 'untrusted-rp-certificate')
  signed('presentation-nonce-wrong', {'presentation': [patch('nonce', 'A' * 43)]}, 'presentation-nonce-mismatch')
  signed('credential-purpose-wrong', {'credential': [patch('purpose', 'Different purpose')]}, 'presentation-context-mismatch')
  signed('credential-purpose-control', {'credential': [patch('purpose', 'Create\naccount')]}, 'invalid-purpose')
  signed('credential-unrequested-claim', {'credential': [patch(['claims'], {'urn:decent:account:v1:given_name': 'Ada', 'urn:decent:account:v1:phone': '123'})]}, 'unrequested-claim')
  negatives.append({'id': 'direct-post-state-wrong', 'patches': [
    patch('bundle.direct_post_response.state', 'A' * 22), patch('direct_post_acceptance.state', 'A' * 22)],
    'expected': 'direct-post-response-mismatch'})
  now = factory.now
  for part, expected in [('request', 'request-object-expiry'), ('binding', 'binding-expiry'), ('id_token', 'id-token-expiry')]:
    for label, claims in [('expired', [patch('exp', now)]), ('future', [patch('iat', now + 61)]),
                          ('exp-equals-iat', [patch('exp', now + 10), patch('iat', now + 10)])]:
      signed(part + '-' + label, {part: claims}, expected)
    if part != 'id_token':
      signed(part + '-lifetime-over-300', {part: [patch('iat', now - 100)]}, expected)
  signed('capability-expired', {'cap_exp': now, 'binding': [patch('exp', now + 100)],
    'request': [patch('exp', now + 50)]}, 'capability-response-expiry')
  signed('binding-after-capability', {'binding': [patch('exp', 1800000241)],
    'request': [patch('exp', 1800000239)]}, 'binding-expiry')
  signed('capability-after-context', {'context': [patch('expires_at', 1800000239)],
    'binding': [patch('exp', 1800000239)]}, 'capability-response-expiry')
  signed('request-exceeds-binding-only', {'cap_exp': 1800000250, 'binding': [patch('exp', 1800000240)],
    'request': [patch('exp', 1800000241)]}, 'request-object-expiry')
  signed('capability-lifetime-over-300', {'cap_exp': now + 301, 'binding': [patch('exp', now + 299)]}, 'capability-response-expiry')
  signed('capability-reuses-oidc-nonce', {'capability': enc(OIDC_NONCE_BYTES)}, 'capability-not-independent')
  signed('oidc-oid4vp-nonce-reused', {'context': [patch('oidc_nonce',
    payload(factory.base['oid4vp_request_jws'])['nonce'])]}, 'oidc-oid4vp-nonce-reuse')
  cap = positive['capability_bytes_test_only']
  escaped_cap = ''.join('\\u%04x' % ord(char) for char in cap)
  percent_cap = ''.join('%%%02X' % ord(char) for char in cap)
  # Unknown receiver extensions remain interoperable, but native senders may
  # not put their bearer capability in any part of those authenticated bytes.
  for artifact in ('jar', 'request'):
    for label, extra in [('top-level', cap), ('nested-value', {'array': ['prefix-' + cap + '-suffix']}),
                         ('nested-member-name', {'prefix-' + cap: 'value'}),
                         ('json-string', '{"nested":["' + escaped_cap + '"]}'),
                         ('json-string-duplicate-member', '{"nested":"' + escaped_cap + '","nested":"benign"}'),
                         ('url', 'https://site.example.test/redirect/' + percent_cap)]:
      signed('capability-leak-' + artifact + '-' + label,
        {artifact: [patch('future_extension', extra)]}, 'capability-sender-artifact-leak')
  signed('capability-leak-response-uri', {'request': [patch('response_uri',
    'https://site.example.test/oid4vp/response/' + cap)]}, 'capability-sender-artifact-leak')
  signed('capability-leak-id-token-other-url', {'id_token': [patch('future_url',
    'https://site.example.test/redirect/' + cap)]}, 'capability-sender-artifact-leak')
  signed('capability-leak-credential-value', {'credential': [patch(
    ['claims', 'urn:decent:account:v1:given_name'], cap)]}, 'capability-sender-artifact-leak')
  for label, uri in [
    ('path', 'https://site.example.test/oid4vp/requests/prefix-' + cap + '-suffix'),
    ('percent-path', 'https://site.example.test/oid4vp/requests/' + percent_cap),
    ('query', positive['bundle']['oid4vp_request_uri'] + '?cap=' + cap),
    ('fragment', positive['bundle']['oid4vp_request_uri'] + '#cap=' + cap),
  ]:
    negatives.append({'id': 'capability-leak-request-uri-' + label,
      'patches': [patch(path, uri) for path in (
        'bundle.oid4vp_request_uri', 'bundle.oid4vp_authorization_parameters.request_uri',
        'outer_authorization_parameters.request_uri', 'poll_ready.body.request_uri')],
      'expected': 'capability-sender-artifact-leak'})
  for label, path, uri in [
    ('poll-url', 'poll_url', positive['poll_url'] + '/' + cap),
    ('redirect-path', 'bundle.direct_post_reply.body.redirect_uri', 'https://site.example.test/oid4vp/return/' + cap),
    ('redirect-query', 'bundle.direct_post_reply.body.redirect_uri', 'https://site.example.test/oid4vp/return?cap=' + cap),
    ('redirect-fragment', 'bundle.direct_post_reply.body.redirect_uri', 'https://site.example.test/oid4vp/return#cap=' + cap),
    ('other-url', 'bundle.direct_post_reply.body.future_url', 'https://site.example.test/path/' + cap),
  ]:
    mutated('capability-leak-' + label, path, uri, 'capability-sender-artifact-leak')
  benign_extension = {'comment': 'benign', 'continuation_capability_hash': positive['binding']['continuation_capability_hash'],
                      'redirect_uri': 'https://site.example.test/harmless'}
  signed('benign-unknown-request-extensions-accepted', {
    'jar': [patch('future_extension', benign_extension)],
    'request': [patch('future_extension', benign_extension)]}, 'accept', True)
  signed('ordinary-id-token-lifetime-over-300-accepted', {'id_token': [patch('exp', now + 3600)]}, 'accept', True)
  signed('request-equals-capability-and-binding', {'request': [patch('exp', 1800000240)]}, 'accept', True)
  signed('binding-less-than-capability', {'binding': [patch('exp', 1800000239)]}, 'accept', True)
  signed('capability-equals-context-and-acceptance-300-boundary', {'cap_exp': 1800000300,
    'binding': [patch('exp', 1800000240)], 'request': [patch('exp', 1800000240)]}, 'accept', True)
  signed('id-token-future-skew-boundary', {'id_token': [patch('iat', now + 60)]}, 'accept', True)
  signed('request-future-skew-boundary', {'request': [patch('iat', now + 60)]}, 'accept', True)
  signed('binding-future-skew-boundary', {'binding': [patch('iat', now + 60)]}, 'accept', True)
  signed('request-lifetime-300-boundary', {'request': [patch('iat', 1800000240 - 300), patch('exp', 1800000240)]}, 'accept', True)
  signed('binding-lifetime-300-boundary', {'binding': [patch('iat', 1800000240 - 300)]}, 'accept', True)
  return {'vector_set': VECTOR_SET, 'source_profile_commit': COMMIT, 'status': 'adopted-normative-v1',
    'test_only': True, 'positive': positive, 'positive_cases': positives, 'negative': negatives}


def main():
  document = generate()
  target = ROOT / 'vectors/continuation_vectors.native.json'
  target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + '\n')
  print(f"Generated {1 + len(document['positive_cases'])} positives and {len(document['negative'])} negatives: {target}")


if __name__ == '__main__':
  main()

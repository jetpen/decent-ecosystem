#!/usr/bin/env python3
"""Offline normative native-continuation regression harness (stdlib unittest)."""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import rfc8785
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

import jsonschema
import generate_native_continuation as generator
import verify_native_continuation as verifier

ROOT = Path(__file__).resolve().parent


def signed_request(vector, member, updates):
  """Use the publicly documented test scalar, never a runtime/private key."""
  token = vector['bundle'][member]
  _, header, payload, _ = verifier.parse_jws(token)
  payload.update(updates)
  h, p = verifier.b64(rfc8785.dumps(header)), verifier.b64(rfc8785.dumps(payload))
  der = ec.derive_private_key(1, ec.SECP256R1()).sign(
    (h + '.' + p).encode('ascii'), ec.ECDSA(hashes.SHA256()))
  r, s = decode_dss_signature(der)
  return h + '.' + p + '.' + verifier.b64(r.to_bytes(32, 'big') + s.to_bytes(32, 'big'))


class NativeContinuationTests(unittest.TestCase):
  def setUp(self):
    self.doc = json.loads((ROOT / 'vectors/continuation_vectors.native.json').read_text())
    self.vector = copy.deepcopy(self.doc['positive'])
    self.base = json.loads((ROOT / 'vectors/valid-signup.json').read_text())

  def test_every_positive_preserves_distinct_correlated_nonces(self):
    cases = [{'id': 'positive', 'patches': []}] + self.doc['positive_cases']
    for case in cases:
      with self.subTest(case=case['id']):
        vector = verifier.apply_patches(self.vector, case['patches'])
        bundle = vector['bundle']
        jar = generator.payload(bundle['initial_oidc_request_jws'])
        request = generator.payload(bundle['oid4vp_request_jws'])
        binding = generator.payload(bundle['owner_key_binding_jws'])
        id_token = generator.payload(bundle['id_token_jws'])
        presentation = generator.payload(bundle['presentation_jws'])
        self.assertNotEqual(jar['nonce'], request['nonce'])
        self.assertEqual(jar['nonce'], bundle['keycloak_context']['oidc_nonce'])
        self.assertEqual(jar['nonce'], binding['oidc_nonce'])
        self.assertEqual(jar['nonce'], id_token['nonce'])
        self.assertEqual(request['nonce'], presentation['nonce'])
        self.assertTrue(verifier.validate_native(vector))

  def test_signed_correlated_oidc_oid4vp_nonce_reuse_is_rejected(self):
    factory = generator.FixtureFactory()
    nonce = generator.payload(factory.base['oid4vp_request_jws'])['nonce']
    vector = factory.build({'context': [generator.patch('oidc_nonce', nonce)]})
    # All original adopted schema/signature/correlation checks pass first.
    verifier.ADOPTED.validate_bundle(vector['bundle'])
    self.assertEqual('oidc-oid4vp-nonce-reuse', verifier.disposition(vector))

  def test_signed_request_sender_capability_leakage_is_rejected(self):
    factory = generator.FixtureFactory()
    cap = factory.build()['capability_bytes_test_only']
    escaped_json = json.dumps({'nested': [cap]}).replace(cap,
      ''.join('\\u%04x' % ord(char) for char in cap))
    for artifact in ('jar', 'request'):
      for label, extra in [('top-level', cap), ('nested-value', {'array': ['prefix-' + cap + '-suffix']}),
                           ('nested-member-name', {'prefix-' + cap: 'value'}), ('json-string', escaped_json)]:
        with self.subTest(artifact=artifact, leak=label):
          vector = factory.build({artifact: [generator.patch('future_extension', extra)]})
          verifier.validate_schema('nativeVector', vector)
          # Receiver interoperability intentionally accepts unknown extensions.
          verifier.ADOPTED.validate_bundle(vector['bundle'])
          self.assertEqual('capability-sender-artifact-leak', verifier.disposition(vector))

  def test_signed_nested_json_duplicate_members_cannot_hide_capability(self):
    factory = generator.FixtureFactory()
    cap = factory.build()['capability_bytes_test_only']
    escaped_cap = ''.join('\\u%04x' % ord(char) for char in cap)
    extra = '{"nested":"' + escaped_cap + '","nested":"benign"}'
    self.assertNotIn(cap, extra)
    for artifact, member in [('jar', 'initial_oidc_request_jws'),
                             ('request', 'oid4vp_request_jws')]:
      with self.subTest(artifact=artifact):
        vector = factory.build({artifact: [generator.patch('future_extension', extra)]})
        verifier.validate_schema('nativeVector', vector)
        # Authenticate both requests and all adopted semantic prerequisites.
        verifier.ADOPTED.validate_bundle(vector['bundle'])
        unauthenticated = copy.deepcopy(vector)
        h, p, s = unauthenticated['bundle'][member].split('.')
        raw = bytearray(verifier.b64d(s))
        raw[0] ^= 1
        token = h + '.' + p + '.' + verifier.b64(bytes(raw))
        unauthenticated['bundle'][member] = token
        if artifact == 'request':
          unauthenticated['request_uri_jws'] = token
          unauthenticated['request_uri_response']['body'] = token
          unauthenticated['request_uri_retry_response']['body'] = token
        self.assertEqual('signature-invalid', verifier.disposition(unauthenticated))
        with self.assertRaisesRegex(verifier.NativeContinuationError, '^capability-sender-artifact-leak$'):
          verifier.validate_native(vector)

  def test_sender_urls_cannot_embed_capability_with_synced_projections(self):
    factory = generator.FixtureFactory()
    vector = factory.build()
    cap = vector['capability_bytes_test_only']
    request_uri = 'https://site.example.test/oid4vp/requests/prefix-' + cap + '-suffix'
    cases = [
      ('request-uri-path', [generator.patch(path, request_uri) for path in (
        'bundle.oid4vp_request_uri', 'bundle.oid4vp_authorization_parameters.request_uri',
        'outer_authorization_parameters.request_uri', 'poll_ready.body.request_uri')]),
      ('poll-url', [generator.patch('poll_url', vector['poll_url'] + '/' + cap)]),
      ('redirect', [generator.patch('bundle.direct_post_reply.body.redirect_uri',
        'https://site.example.test/oid4vp/return/' + cap)]),
      ('unknown-reply-url', [generator.patch('bundle.direct_post_reply.body.future_url',
        'https://site.example.test/path/' + cap)]),
    ]
    for label, patches in cases:
      with self.subTest(leak=label):
        candidate = generator.apply(vector, patches)
        verifier.validate_schema('nativeVector', candidate)
        if label == 'request-uri-path':
          verifier.ADOPTED.validate_bundle(candidate['bundle'])
        self.assertEqual('capability-sender-artifact-leak', verifier.disposition(candidate))

  def test_generated_sender_negatives_reject_through_public_validator(self):
    cases = [case for case in self.doc['negative']
             if case['expected'] == 'capability-sender-artifact-leak']
    self.assertTrue(cases)
    for case in cases:
      with self.subTest(case=case['id']):
        vector = verifier.apply_patches(self.vector, case['patches'])
        verifier.validate_schema('nativeVector', vector)
        with self.assertRaisesRegex(verifier.NativeContinuationError, '^capability-sender-artifact-leak$'):
          verifier.validate_native(vector)

  def test_sender_leakage_is_not_trusted_before_signature_verification(self):
    factory = generator.FixtureFactory()
    cap = factory.build()['capability_bytes_test_only']
    for source, member in [('jar', 'initial_oidc_request_jws'),
                           ('request', 'oid4vp_request_jws'), ('id_token', 'id_token_jws')]:
      with self.subTest(artifact=source):
        vector = factory.build({source: [generator.patch('future_extension', cap)]})
        h, p, s = vector['bundle'][member].split('.')
        raw = bytearray(verifier.b64d(s))
        raw[0] ^= 1
        token = h + '.' + p + '.' + verifier.b64(bytes(raw))
        vector['bundle'][member] = token
        if source == 'request':
          vector['request_uri_jws'] = token
          vector['request_uri_response']['body'] = token
          vector['request_uri_retry_response']['body'] = token
        self.assertEqual('signature-invalid', verifier.disposition(vector))

  def test_benign_unknown_request_extensions_and_binding_hash_are_accepted(self):
    factory = generator.FixtureFactory()
    digest = factory.build()['binding']['continuation_capability_hash']
    extra = {'comment': 'benign', 'continuation_capability_hash': digest,
             'redirect_uri': 'https://site.example.test/harmless'}
    for extension in (extra, '{"nested":"first benign value","nested":"second benign value"}'):
      with self.subTest(extension=extension):
        vector = factory.build({'jar': [generator.patch('future_extension', extension)],
                                'request': [generator.patch('future_extension', extension)]})
        self.assertTrue(verifier.validate_native(vector))

  def test_signed_jar_audience_must_match_issuer(self):
    self.vector['bundle']['initial_oidc_request_jws'] = signed_request(
      self.vector, 'initial_oidc_request_jws', {'aud': 'https://wrong.example.test/realms/site'})
    with self.assertRaisesRegex(verifier.NativeContinuationError, '^native-oidc-request-audience$'):
      verifier.validate_native(self.vector, self.base)

  def test_signed_request_requires_direct_post(self):
    token = signed_request(self.vector, 'oid4vp_request_jws', {'response_mode': 'fragment'})
    self.vector['bundle']['oid4vp_request_jws'] = token
    self.vector['request_uri_jws'] = token
    self.vector['request_uri_response']['body'] = token
    self.vector['request_uri_retry_response']['body'] = token
    with self.assertRaisesRegex(verifier.NativeContinuationError, '^unsupported-response-mode$'):
      verifier.validate_native(self.vector, self.base)

  def test_signed_purpose_cannot_be_whitespace(self):
    _, _, jar, _ = verifier.parse_jws(self.vector['bundle']['initial_oidc_request_jws'])
    jar['decent_account_request']['purpose'] = '   '
    self.vector['bundle']['initial_oidc_request_jws'] = signed_request(
      self.vector, 'initial_oidc_request_jws', jar)
    self.vector['account_request'] = jar['decent_account_request']
    self.vector['context']['purpose'] = '   '
    self.vector['bundle']['keycloak_context']['purpose'] = '   '
    with self.assertRaisesRegex(verifier.NativeContinuationError, '^invalid-purpose$'):
      verifier.validate_native(self.vector, self.base)

  def test_all_fixture_signatures_and_semantic_prerequisites(self):
    cases = [{'id': 'positive', 'patches': [], 'expected': 'accept'}] + self.doc['positive_cases'] + self.doc['negative']
    adopted = verifier.ADOPTED
    for case in cases:
      with self.subTest(case=case['id']):
        vector = verifier.apply_patches(self.vector, case['patches'])
        bundle = vector['bundle']
        _, jar = adopted.verify_jws(bundle['initial_oidc_request_jws'], 'ES256',
          adopted.ec_public(bundle['rp_client_id_jwk']), typ='oauth-authz-req+jwt',
          kid=bundle['rp_client_id_jwk']['kid'], canonical_payload=True)
        kc_jwk = bundle['keycloak_jwks']['keys'][0]
        for member, typ in [('id_token_jws', 'JWT'), ('owner_key_binding_jws', 'decent-owner-key-binding+jwt')]:
          adopted.verify_jws(bundle[member], 'RS256', adopted.rsa_public(kc_jwk), typ=typ, kid=kc_jwk['kid'])
        adopted.verify_jws(bundle['oid4vp_request_jws'], 'ES256',
          adopted.ec_public(bundle['rp_client_id_jwk']), typ='oauth-authz-req+jwt', canonical_payload=True)
        _, presentation = adopted.verify_jws(bundle['presentation_jws'], 'EdDSA',
          adopted.ed_public(bundle['owner_jwk']), typ='decent-account-presentation+jwt', canonical_payload=True)
        adopted.verify_jws(presentation['vp']['verifiableCredential'][0], 'EdDSA',
          adopted.ed_public(bundle['owner_jwk']), typ='decent-account-credential+jwt', canonical_payload=True)
        if case['expected'] not in {'schema-reject', 'context-request-binding', 'request-opt-in-projection'}:
          verifier.validate_schema('nativeVector', vector)
        if case['id'].startswith('request-dcql-') or case['expected'] in {
            'capability-sender-artifact-leak', 'oidc-oid4vp-nonce-reuse'}:
          request = generator.payload(bundle['oid4vp_request_jws'])
          verifier._ADOPTED_VALIDATE_SCHEMA('oid4vpRequest', request)
        if case['expected'] in {'capability-sender-artifact-leak', 'oidc-oid4vp-nonce-reuse'}:
          verifier.validate_schema('nativeAccountRequest', jar['decent_account_request'])
          verifier.validate_schema('nativeBinding', generator.payload(bundle['owner_key_binding_jws']))
          verifier._ADOPTED_VALIDATE_SCHEMA('presentation', presentation)
          verifier._ADOPTED_VALIDATE_SCHEMA('accountCredential',
            generator.payload(presentation['vp']['verifiableCredential'][0]))
          if case['expected'] == 'capability-sender-artifact-leak':
            with self.assertRaisesRegex(verifier.NativeContinuationError, '^capability-sender-artifact-leak$'):
              verifier.validate_native(vector)
          else:
            self.assertEqual(case['expected'], verifier.disposition(vector))

  def test_original_signed_bundle_reaches_adopted_validation_unchanged(self):
    original = copy.deepcopy(self.vector)
    validate_bundle = verifier.ADOPTED.validate_bundle
    with patch.object(verifier.ADOPTED, 'validate_bundle', wraps=validate_bundle) as call:
      verifier.validate_native(self.vector)
    call.assert_called_once()
    self.assertIs(call.call_args.args[0], self.vector['bundle'])
    self.assertEqual(original, self.vector)

  def test_schema_adapter_does_not_mutate_input_or_ignore_unknown_native_fields(self):
    values = [('accountRequest', self.vector['account_request']), ('context', self.vector['context']),
              ('binding', self.vector['binding'])]
    for name, value in values:
      with self.subTest(schema=name):
        original = copy.deepcopy(value)
        verifier.validate_adopted_native_schema(name, value)
        self.assertEqual(original, value)
        value['unexpected_native_extension'] = True
        with self.assertRaises(jsonschema.ValidationError):
          verifier.validate_adopted_native_schema(name, value)

  def test_ordinary_id_token_has_no_native_300_second_cap(self):
    case = next(case for case in self.doc['positive_cases'] if case['id'] == 'ordinary-id-token-lifetime-over-300-accepted')
    vector = verifier.apply_patches(self.vector, case['patches'])
    claims = generator.payload(vector['bundle']['id_token_jws'])
    self.assertGreater(claims['exp'] - claims['iat'], 300)
    self.assertTrue(verifier.validate_native(vector))

  def test_binding_expiry_is_independently_bounded_by_capability(self):
    factory = generator.FixtureFactory()
    vector = factory.build({'cap_exp': 1800000240,
      'binding': [generator.patch('exp', 1800000241)],
      'request': [generator.patch('exp', 1800000239)]})
    self.assertEqual('binding-expiry', verifier.disposition(vector))

  def test_binding_before_capability_is_accepted(self):
    factory = generator.FixtureFactory()
    vector = factory.build({'binding': [generator.patch('exp', 1800000239)]})
    self.assertTrue(verifier.validate_native(vector))

  def test_capability_can_equal_context_and_acceptance_time_limit(self):
    factory = generator.FixtureFactory()
    vector = factory.build({'cap_exp': 1800000300,
      'binding': [generator.patch('exp', 1800000240)],
      'request': [generator.patch('exp', 1800000240)]})
    self.assertEqual(vector['context']['expires_at'], vector['capability_expires_at'])
    self.assertEqual(vector['proof_accepted_at'] + 300, vector['capability_expires_at'])
    self.assertTrue(verifier.validate_native(vector))

  def test_request_exceeding_only_binding_has_valid_expiry_direction(self):
    case = next(case for case in self.doc['negative'] if case['id'] == 'request-exceeds-binding-only')
    vector = verifier.apply_patches(self.vector, case['patches'])
    request = generator.payload(vector['bundle']['oid4vp_request_jws'])
    binding = generator.payload(vector['bundle']['owner_key_binding_jws'])
    claims = generator.payload(vector['bundle']['id_token_jws'])
    capability_expiry = claims['decent_account_continuation_expires_at']
    self.assertLess(binding['exp'], request['exp'])
    self.assertLessEqual(request['exp'], capability_expiry)
    self.assertLessEqual(capability_expiry, vector['context']['expires_at'])
    self.assertEqual('request-object-expiry', verifier.disposition(vector))

  def test_fresh_generation_is_portable_and_never_retains_stale_cases(self):
    with tempfile.TemporaryDirectory(prefix='native-continuation-') as temp:
      root = Path(temp) / 'portable'
      (root / 'vectors').mkdir(parents=True)
      (root / 'schemas').mkdir()
      for name in ['generate_native_continuation.py', 'verify_native_continuation.py',
                   'verify.py', 'native-continuation.schema.json', 'schemas/profile.schema.json',
                   'vectors/negative.json']:
        shutil.copyfile(ROOT / name, root / name)
      for source in (ROOT / 'vectors').glob('valid-*.json'):
        shutil.copyfile(source, root / 'vectors' / source.name)
      env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
      output = root / 'vectors/continuation_vectors.native.json'
      output.write_text('{"negative": [{"id": "stale-poison"}]}')
      for iteration in range(2):
        subprocess.run([sys.executable, str(root / 'generate_native_continuation.py')],
          cwd=temp, env=env, check=True, capture_output=True, text=True)
        document = json.loads(output.read_text())
        self.assertEqual({case['id'] for case in self.doc['negative']}, {case['id'] for case in document['negative']})
        self.assertEqual({case['id'] for case in self.doc['positive_cases']}, {case['id'] for case in document['positive_cases']})
        if iteration:
          self.assertNotEqual(previous_key, document['positive']['bundle']['keycloak_jwks'])
        previous_key = document['positive']['bundle']['keycloak_jwks']
        result = subprocess.run([sys.executable, str(root / 'verify_native_continuation.py')],
          cwd=temp, env=env, check=True, capture_output=True, text=True)
        self.assertIn(f"PASS {1 + len(document['positive_cases'])} native positives; rejected {len(document['negative'])}", result.stdout)

  def test_case_document_schema(self):
    verifier.validate_schema('nativeNegativeList', self.doc['negative'])
    for case in self.doc['positive_cases']:
      verifier.validate_schema('nativePositiveCase', case)

  def test_vector_requires_every_projection(self):
    for member in self.vector:
      with self.subTest(member=member):
        vector = copy.deepcopy(self.vector)
        del vector[member]
        with self.assertRaises(jsonschema.ValidationError):
          verifier.validate_schema('nativeVector', vector)

  def test_all_positive_cases(self):
    verifier.validate_native(self.vector, self.base)
    for case in self.doc['positive_cases']:
      with self.subTest(case=case['id']):
        verifier.validate_native(generator.apply(self.vector, case['patches']), self.base)

  def test_all_negative_dispositions(self):
    schema_codes = {('account_request', 'decent_native_continuation'): 'request-opt-in-projection',
                    ('context', 'decent_native_continuation'): 'context-request-binding'}
    for case in self.doc['negative']:
      with self.subTest(case=case['id']):
        vector = generator.apply(self.vector, case['patches'])
        try:
          verifier.validate_native(vector, self.base)
        except verifier.NativeContinuationError as exc:
          actual = str(exc)
        except jsonschema.ValidationError as exc:
          actual = schema_codes.get(tuple(exc.path), 'schema-reject')
        else:
          actual = 'accept'
        self.assertEqual(case['expected'], actual)


if __name__ == '__main__':
  unittest.main()

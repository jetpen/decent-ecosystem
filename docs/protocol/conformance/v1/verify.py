#!/usr/bin/env python3
"""Offline verifier for semantic envelope and Keycloak 26.8.0 adapter fixtures."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator
import rfc8785

ROOT=Path(__file__).resolve().parent
schema=json.loads((ROOT/'grant-envelope.schema.json').read_text(encoding='utf-8'))
Draft202012Validator.check_schema(schema)
validator=Draft202012Validator(schema)
adapter=json.loads((ROOT/'adapter-keycloak-26.8.0.json').read_text(encoding='utf-8'))
REQUIRED_VECTOR_IDS = [
  'positive-existing-object', 'exact-subject-case-change', 'different-storage-resource',
  'assertion-sub-mismatch',
  'different-existing-object-digest', 'reduced-action-subset', 'explicit-delete-scope',
  'create-is-not-entitled-by-existing-object-profile', 'purpose-whitespace-change',
  'different-jti-from-assertion', 'consent-outlives-assertion', 'consent-shorter-than-assertion',
  'namespaced-nonauthorizing-extension', 'extension-cannot-widen-scope',
  'rotated-owner-key-requires-current-registry-resolution', 'consent-expiry-rejected-at-adapter',
  'duplicate-action', 'audience-case-change', 'nonpositive-consent-exp', 'unqualified-extension-key',
]
REQUIRED_ADAPTER_REJECTION_IDS = [
  'exact-subject-case-change', 'different-storage-resource', 'assertion-sub-mismatch',
  'different-jti-from-assertion', 'consent-outlives-assertion',
  'consent-expiry-rejected-at-adapter', 'audience-case-change',
  'rotated-owner-key-requires-current-registry-resolution',
]
REQUIRED_RESOURCE_POLICY_IDS = [
  'different-existing-object-digest',
  'create-is-not-entitled-by-existing-object-profile',
  'purpose-whitespace-change',
]
checks=0

def check(cond,msg):
  global checks
  if not cond: raise AssertionError(msg)
  checks+=1

def pairs_no_duplicates(pairs):
  out={}
  for k,v in pairs:
    if k in out: raise ValueError(f'duplicate JSON member: {k}')
    out[k]=v
  return out

def load_strict(path):
  return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs_no_duplicates,
                    parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f'non-JSON numeric constant {x}')))

payload_path=ROOT/'fixtures/assertion-payload.json'
payload_text=payload_path.read_text(encoding='utf-8')
payload=load_strict(payload_path)
marker='"decent_grant": '
check(payload_text.count(marker)==1, 'assertion payload fixture must contain one decent_grant member')
value_start=payload_text.index(marker)+len(marker)
embedded_grant, value_end=json.JSONDecoder().raw_decode(payload_text, value_start)
envelope=payload['decent_grant']
check(envelope==adapter['claims']['assertion']['decent_grant'], 'assertion payload grant differs from adapter fixture')
check(payload_text[value_start:value_end].encode('utf-8')==rfc8785.dumps(embedded_grant), 'embedded decent_grant bytes are not JCS canonical')
check(payload['sub']==envelope['owner_identifier'], 'assertion sub must exactly equal owner_identifier')
check(payload['jti']==envelope['grant_jti'], 'assertion jti must exactly equal grant_jti')
verification=adapter['verification_context']
check(verification['resolved_owner_identifier']==payload['sub'], 'Registry key must be resolved for the exact assertion subject')
check(verification['current_registry_owner_public_key']==envelope['owner_public_key'], 'owner_public_key must equal current Registry key used for JWS verification')
check(verification['fixture_key_binding_matches'] is True, 'illustrative Registry key binding fixture must be consistent')
check(verification['live_signature_verification'] == 'not-run', 'fixture must not imply a live JWS signature verification')

errors=list(validator.iter_errors(envelope))
check(not errors, f'valid grant envelope rejected: {errors[0].message if errors else ""}')
canonical=rfc8785.dumps(envelope)
check(canonical==rfc8785.dumps(load_strict(ROOT/'fixtures/valid-grant.json')), 'JCS grant fixture differs from adapter payload')
parsed=load_strict(ROOT/'fixtures/valid-grant.json')
check(parsed==envelope, 'fixture JSON values differ from Keycloak adapter payload')

# Check standard RFC 7523 adapter role separation and exact time/JTI bindings.
assertion=adapter['claims']['assertion']; token=adapter['claims']['access_token_required']
check(assertion['aud']=='https://keycloak.example.test/realms/decent', 'assertion aud must target AS')
check(token['aud']==envelope['storage_aud'], 'output token aud must target Storage')
check(assertion['jti']==envelope['grant_jti'], 'grant jti must equal assertion jti')
check(envelope['consent_exp']<=assertion['exp'], 'consent must not exceed assertion exp')
check(token['exp']<=envelope['consent_exp'], 'access token must not outlive consent')
check('refresh_token' in adapter['claims']['access_token_forbidden'], 'no-refresh invariant missing')
check(adapter['test_scope']['passed']==adapter['test_scope']['mandatory_cases'], 'recorded adapter evidence not all passed')
check(adapter['test_scope']['failed']==adapter['test_scope']['errors']==adapter['test_scope']['skipped']==0, 'recorded adapter evidence contains failures/errors/skips')

manifest=load_strict(ROOT/'manifest.json')
subject_vector=next(v for v in manifest['semantic_vectors'] if v['id']=='assertion-sub-mismatch')
check(subject_vector['adapter_context']['assertion_sub'] != subject_vector['grant']['owner_identifier'], 'subject-mismatch vector must use different assertion and owner identifiers')
for case in manifest['valid']:
  obj=load_strict(ROOT/case['file'])
  errs=list(validator.iter_errors(obj))
  check(not errs, f"{case['file']} invalid: {errs[0].message if errs else ''}")
for case in manifest['invalid']:
  obj=load_strict(ROOT/case['file'])
  check(bool(list(validator.iter_errors(obj))), f"{case['file']} unexpectedly valid")
for case in manifest['invalid_semantic']:
  if case['expected']=='duplicate-json-member':
    try: load_strict(ROOT/case['file'])
    except ValueError: checks+=1
    else: raise AssertionError(f"{case['file']} duplicate member accepted")
  else:
    obj=load_strict(ROOT/case['file'])
    check(bool(list(validator.iter_errors(obj))), f"{case['file']} unexpectedly valid")
for case in manifest['unsupported']:
  obj=load_strict(ROOT/case['file'])
  check(obj['wire_version'] not in manifest['supported_wire_versions'], 'unsupported version fixture accepted')
for case in manifest['duplicate_member']:
  try: load_strict(ROOT/case['file'])
  except ValueError: checks+=1
  else: raise AssertionError(f"{case['file']} duplicate member accepted")
for case in manifest['canonicality']:
  raw=(ROOT/case['file']).read_bytes()
  obj=load_strict(ROOT/case['file'])
  expected=rfc8785.dumps(obj)
  if case['expected']=='canonical': check(raw.rstrip(b'\n')==expected, f"{case['file']} not canonical JCS")
  elif case['expected']=='noncanonical-but-same-json': check(raw.rstrip(b'\n')!=expected and obj==parsed, f"{case['file']} should be equivalent but noncanonical")
  else: raise AssertionError(f"unknown canonicality expectation {case['expected']}")
digest=manifest['canonical_sha256']
check(hashlib.sha256(rfc8785.dumps(load_strict(ROOT/digest['file']))).hexdigest()==digest['sha256'],'canonical JCS digest mismatch')

# All mandatory semantic vectors use schema-valid envelope values and unique IDs.
ids=set()
for vector in manifest['semantic_vectors']:
  check(vector['id'] not in ids, f"duplicate semantic vector id {vector['id']}")
  ids.add(vector['id'])
  errs=list(validator.iter_errors(vector['grant']))
  check(vector['expected'] in {'accept','reject-at-adapter','resource-policy-deny','schema-invalid'},f"unknown expected outcome {vector['expected']}")
  if vector['expected']=='schema-invalid':
    check(bool(errs),f"semantic malformed vector {vector['id']} unexpectedly validates")
  else:
    check(not errs,f"semantic vector {vector['id']} is invalid: {errs[0].message if errs else ''}")
  check(vector.get('reason'),f"semantic vector {vector['id']} missing reason")

# Adapter-context vectors must actually exercise their stated rejection condition.
by_id={vector['id']:vector for vector in manifest['semantic_vectors']}
jti_vector=by_id['different-jti-from-assertion']
check(jti_vector['adapter_context']['assertion_jti'] != jti_vector['grant']['grant_jti'], 'different-jti vector must use unequal assertion and grant JTIs')
key_vector=by_id['rotated-owner-key-requires-current-registry-resolution']
check(key_vector['adapter_context']['current_registry_key'] != key_vector['grant']['owner_public_key'], 'stale-key vector must use a key different from current Registry key')
expiry_vector=by_id['consent-expiry-rejected-at-adapter']
check(expiry_vector['adapter_context']['candidate_output_exp'] > expiry_vector['grant']['consent_exp'], 'output-expiry vector must exceed consent ceiling')
for expected_id in REQUIRED_ADAPTER_REJECTION_IDS:
  check(expected_id in ids and next(v for v in manifest['semantic_vectors'] if v['id']==expected_id)['expected']=='reject-at-adapter',f"adapter rejection vector {expected_id} missing or misclassified")
for expected_id in REQUIRED_RESOURCE_POLICY_IDS:
  check(expected_id in ids and next(v for v in manifest['semantic_vectors'] if v['id']==expected_id)['expected']=='resource-policy-deny',f"resource policy vector {expected_id} missing or misclassified")
for required in REQUIRED_VECTOR_IDS:
  check(required in ids,f"missing required semantic vector {required}")
print(f"grant conformance fixtures passed: {checks} checks; {len(manifest['valid'])} valid, {len(manifest['invalid'])} schema-invalid, {len(manifest['invalid_semantic'])} semantic-invalid, {len(manifest['duplicate_member'])} duplicate-member, {len(manifest['semantic_vectors'])} semantic-vector")

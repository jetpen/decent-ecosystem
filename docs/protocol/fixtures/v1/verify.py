#!/usr/bin/env python3
"""Validate v1 protocol fixture files against schemas and exact-byte/stateful rules."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SCHEMAS = {
    "social-graph": REPO / "docs/protocol/schemas/social-graph.schema.json",
    "trust-assertions": REPO / "docs/protocol/schemas/trust-assertion.schema.json",
}

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:
    raise SystemExit("Install jsonschema to run this verifier: python -m pip install jsonschema") from exc

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
validators = {}
for family, path in SCHEMAS.items():
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validators[family] = Draft202012Validator(schema)

checks = 0

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def schema_errors(family, rel):
    return list(validators[family].iter_errors(load(rel)))

def require_schema(rel, family, valid):
    global checks
    errors = schema_errors(family, rel)
    if valid and errors:
        raise AssertionError(f"{rel} unexpectedly invalid: {errors[0].message}")
    if not valid and not errors:
        raise AssertionError(f"{rel} unexpectedly valid")
    checks += 1

for case in manifest["valid"]:
    require_schema(case["file"], case["family"], True)
for case in manifest["invalid"]:
    require_schema(case["file"], case["family"], False)

for case in manifest["unsupported"]:
    document = load(case["file"])
    errors = schema_errors(case["family"], case["file"])
    if not errors or document.get("schema_version") == 1:
        raise AssertionError(f"{case['file']} should be rejected by the v1 schema")
    checks += 1

for vector in manifest["digest_vectors"]:
    actual = hashlib.sha256((ROOT / vector["file"]).read_bytes()).hexdigest()
    if actual != vector["sha256"]:
        raise AssertionError(f"digest mismatch for {vector['file']}: {actual}")
    checks += 1

for conflict in manifest["conflicts"]:
    first, second = [load(name) for name in conflict["files"]]
    raw_first, raw_second = [(ROOT / name).read_bytes() for name in conflict["files"]]
    if first != second or raw_first == raw_second:
        raise AssertionError("conflict fixture must have equal parsed objects and different exact bytes")
    identity = lambda obj: (obj["id"], obj["schema_version"], obj["version"])
    if identity(first) != identity(second):
        raise AssertionError("conflict fixture revision identity differs")
    checks += 1

# Stateful predecessor checks: validate both the valid link and deliberately wrong link.
for family, v1_name, v2_name in [
    ("social-graph", "examples/social-graph-v1.json", "examples/social-graph-v2-revision.json"),
    ("trust-assertions", "examples/trust-assertions-v1.json", "examples/trust-assertions-v2-revision.json"),
]:
    first, second = load(v1_name), load(v2_name)
    expected = hashlib.sha256((ROOT / v1_name).read_bytes()).hexdigest()
    if second.get("previous_digest") != expected or second["version"] != first["version"] + 1 or second["id"] != first["id"]:
        raise AssertionError(f"invalid {family} revision/predecessor chain")
    checks += 1

invalid_stateful = manifest.get("invalid_stateful", [])
for case in invalid_stateful:
    candidate = load(case["file"])
    predecessor = (ROOT / case["predecessor"]).read_bytes()
    actual_digest = hashlib.sha256(predecessor).hexdigest()
    if candidate.get("previous_digest") == actual_digest:
        raise AssertionError(f"{case['file']} unexpectedly links the actual predecessor")
    checks += 1

print(f"fixture verification passed: {checks} checks; {len(manifest['valid'])} valid, {len(manifest['invalid'])} schema-invalid, {len(invalid_stateful)} invalid-stateful, {len(manifest['unsupported'])} unsupported, {len(manifest['conflicts'])} conflict, {len(manifest['digest_vectors'])} digest, 2 valid stateful-chain")

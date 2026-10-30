"""Inspect declared evidence and snapshots without executing claimed commands."""

import hashlib
import json
import re

from .workspace import InputError, Workspace


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_FILES = 256
_MAX_TOTAL_BYTES = 64 * 1024 * 1024
_LIMITATIONS = (
    "This inspection checks manifest structure, file presence, and declared SHA-256 "
    "snapshots. It does not execute commands or authenticate claimed statuses, exit "
    "codes, test execution, human review, or semantic/business correctness. Matching "
    "hashes establish consistency with the supplied manifest, not independent proof "
    "of freshness or completeness. Files may change after inspection."
)


def _object(value, keys, location):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise InputError(f"Invalid manifest object at {location}")


def _list(value, maximum, location, minimum=0):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise InputError(f"Invalid manifest list at {location}")


def _text(value, maximum, location):
    if (not isinstance(value, str) or not value.strip() or len(value) > maximum
            or any(0xD800 <= ord(char) <= 0xDFFF for char in value)):
        raise InputError(f"Invalid manifest text at {location}")


def _hash(value, location):
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise InputError(f"Invalid SHA-256 at {location}")


def _path(workspace, value, location):
    _text(value, 1024, location)
    return workspace.relative(value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("Duplicate JSON object key in manifest")
        result[key] = value
    return result


def _validate(workspace, manifest):
    _object(manifest, ("version", "artifacts", "requirements"), "manifest")
    if type(manifest["version"]) is not int or manifest["version"] != 1:
        raise InputError("Manifest version must be integer 1")
    _list(manifest["artifacts"], 100, "artifacts")
    _list(manifest["requirements"], 100, "requirements", minimum=1)
    paths = set()
    for artifact in manifest["artifacts"]:
        paths.add(_path(workspace, artifact, "artifact path"))
    ids = set()
    for requirement in manifest["requirements"]:
        _object(requirement, ("id", "criterion", "status", "evidence"), "requirement")
        identifier = requirement["id"]
        _text(identifier, 80, "requirement id")
        if identifier != identifier.strip() or any(ord(char) < 32 for char in identifier):
            raise InputError("Requirement id must be trimmed text without control characters")
        if identifier in ids:
            raise InputError("Duplicate requirement id")
        ids.add(identifier)
        _text(requirement["criterion"], 4096, "criterion")
        if requirement["status"] not in ("verified", "unverified", "blocked"):
            raise InputError("Invalid requirement status")
        _list(requirement["evidence"], 10, "evidence")
        for evidence in requirement["evidence"]:
            _object(evidence, ("path", "sha256", "command", "exit_code", "inputs"), "evidence")
            paths.add(_path(workspace, evidence["path"], "evidence path"))
            _hash(evidence["sha256"], "evidence hash")
            _text(evidence["command"], 4096, "command")
            if type(evidence["exit_code"]) is not int:
                raise InputError("Evidence exit_code must be an integer")
            _list(evidence["inputs"], 100, "inputs")
            for snapshot in evidence["inputs"]:
                _object(snapshot, ("path", "sha256"), "input")
                paths.add(_path(workspace, snapshot["path"], "input path"))
                _hash(snapshot["sha256"], "input hash")
    return paths


def check_evidence(workspace: Workspace, manifest: str, limit: int = 5) -> dict:
    """Return bounded structural findings for workspace-relative manifest paths."""
    if type(limit) is not int or not 1 <= limit <= 30:
        raise InputError("limit must be an integer from 1 to 30")
    manifest_path = _path(workspace, manifest, "manifest path")
    manifest_bytes = workspace.read_bytes(manifest_path, max_bytes=262_144)
    try:
        document = json.loads(manifest_bytes.decode("utf-8-sig"), object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise InputError("Invalid JSON manifest") from exc
    paths = _validate(workspace, document)
    paths.add(manifest_path)
    if len(paths) > _MAX_FILES:
        raise InputError("Manifest exceeds the 256 distinct file limit")
    total_bytes = len(manifest_bytes)
    snapshots = {manifest_path: (total_bytes, hashlib.sha256(manifest_bytes).hexdigest())}

    findings = []
    total = 0

    def add(rule, path=None, identifier=None):
        nonlocal total
        total += 1
        if len(findings) < limit:
            finding = {"rule": rule}
            if path is not None:
                finding["path"] = workspace.relative(path)
            if identifier is not None:
                finding["id"] = identifier
            findings.append(finding)

    def inspect_file(path, kind, expected_hash=None, identifier=None):
        nonlocal total_bytes
        canonical = workspace.relative(path)
        if canonical not in snapshots:
            if len(snapshots) >= _MAX_FILES:
                raise InputError("Manifest exceeds the 256 distinct file limit")
            remaining = _MAX_TOTAL_BYTES - total_bytes
            if remaining <= 0:
                raise InputError("Manifest exceeds the 64 MiB total read limit")
            try:
                content = workspace.read_bytes(canonical, max_bytes=min(8_388_608, remaining))
            except FileNotFoundError:
                snapshots[canonical] = None
            else:
                total_bytes += len(content)
                snapshots[canonical] = (len(content), hashlib.sha256(content).hexdigest())
        snapshot = snapshots[canonical]
        if snapshot is None:
            add("missing_" + kind, path, identifier)
            return
        size, digest = snapshot
        if not size:
            add("empty_" + kind, path, identifier)
        elif expected_hash is not None and digest != expected_hash:
            add("stale_" + kind, path, identifier)

    for artifact in document["artifacts"]:
        inspect_file(artifact, "artifact")
    for requirement in document["requirements"]:
        identifier = requirement["id"]
        if requirement["status"] != "verified":
            add("requirement_" + requirement["status"], identifier=identifier)
        elif not requirement["evidence"]:
            add("missing_evidence_links", identifier=identifier)
        for evidence in requirement["evidence"]:
            path = evidence["path"]
            if evidence["exit_code"] != 0:
                add("unsuccessful_evidence", path, identifier)
            inspect_file(path, "evidence", evidence["sha256"], identifier)
            if not evidence["inputs"]:
                add("missing_input_snapshots", path, identifier)
            for snapshot in evidence["inputs"]:
                inspect_file(snapshot["path"], "input", snapshot["sha256"], identifier)

    return {
        "tool": "check_evidence",
        "status": "findings" if total else "no_findings",
        "total_findings": total,
        "findings": findings,
        "truncated": total > len(findings),
        "limitations": _LIMITATIONS,
    }

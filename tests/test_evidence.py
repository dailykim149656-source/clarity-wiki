import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/clarity-wiki/scripts'))

from clarity_wiki.evidence import check_evidence
from clarity_wiki.workspace import InputError, Workspace


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = Workspace(self.root)
        self.write("result.csv", b"answer\n42\n")
        self.write("verification.txt", b"1 test passed\n")
        self.write("src.py", b"answer = 42\n")
        self.manifest = {
            "version": 1,
            "artifacts": ["result.csv"],
            "requirements": [{
                "id": "R1", "criterion": "The answer is available", "status": "verified",
                "evidence": [{
                    "path": "verification.txt", "sha256": self.hash("verification.txt"),
                    "command": "python -m unittest", "exit_code": 0,
                    "inputs": [{"path": "src.py", "sha256": self.hash("src.py")}],
                }],
            }],
        }

    def write(self, name, contents):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)

    def hash(self, name):
        return hashlib.sha256((self.root / name).read_bytes()).hexdigest()

    def check(self, limit=5, name="manifest.json"):
        self.write(name, json.dumps(self.manifest).encode())
        return check_evidence(self.workspace, name, limit)

    def assert_findings(self, result, rule):
        self.assertEqual(result["status"], "findings")
        self.assertIn(rule, [finding["rule"] for finding in result["findings"]])

    def test_complete_manifest(self):
        result = self.check()
        self.assertEqual(result["tool"], "check_evidence")
        self.assertEqual(result["status"], "no_findings")
        self.assertEqual(result["total_findings"], 0)
        self.assertEqual(result["findings"], [])
        self.assertFalse(result["truncated"])
        self.assertIn("not execute", result["limitations"])

    def test_paths_are_relative_to_workspace_not_manifest_parent(self):
        self.assertEqual(self.check(name="nested/manifest.json")["total_findings"], 0)

    def test_missing_and_empty_artifacts(self):
        (self.root / "result.csv").unlink()
        self.assert_findings(self.check(), "missing_artifact")
        self.write("result.csv", b"")
        self.assert_findings(self.check(), "empty_artifact")

    def test_artifact_without_declared_snapshot_does_not_detect_content_change(self):
        self.write('result.csv', b'answer\n99\n')
        self.assertEqual(self.check()['status'], 'no_findings')

    def test_artifact_bound_as_inspected_input_detects_content_change(self):
        evidence = self.manifest['requirements'][0]['evidence'][0]
        evidence['inputs'].append({'path': 'result.csv', 'sha256': self.hash('result.csv')})
        self.assertEqual(self.check()['status'], 'no_findings')
        self.write('result.csv', b'answer\n99\n')
        self.assert_findings(self.check(), 'stale_input')

    def test_missing_empty_and_stale_evidence(self):
        (self.root / "verification.txt").unlink()
        self.assert_findings(self.check(), "missing_evidence")
        self.write("verification.txt", b"")
        self.assert_findings(self.check(), "empty_evidence")
        self.write("verification.txt", b"changed")
        self.assert_findings(self.check(), "stale_evidence")

    def test_missing_empty_and_stale_inputs(self):
        (self.root / "src.py").unlink()
        self.assert_findings(self.check(), "missing_input")
        self.write("src.py", b"")
        self.assert_findings(self.check(), "empty_input")
        self.write("src.py", b"changed")
        self.assert_findings(self.check(), "stale_input")

    def test_verified_without_evidence(self):
        self.manifest["requirements"][0]["evidence"] = []
        self.assert_findings(self.check(), "missing_evidence_links")

    def test_verified_without_input_snapshots(self):
        self.manifest["requirements"][0]["evidence"][0]["inputs"] = []
        self.assert_findings(self.check(), "missing_input_snapshots")

    def test_unverified_and_blocked_always_have_findings(self):
        for status in ("unverified", "blocked"):
            with self.subTest(status=status):
                self.manifest["requirements"][0]["status"] = status
                self.assert_findings(self.check(), "requirement_" + status)

    def test_nonzero_exit_is_finding(self):
        self.manifest["requirements"][0]["evidence"][0]["exit_code"] = 1
        self.assert_findings(self.check(), "unsuccessful_evidence")

    def test_duplicate_ids_are_invalid(self):
        self.manifest["requirements"].append(copy.deepcopy(self.manifest["requirements"][0]))
        with self.assertRaises(InputError):
            self.check()

    def test_invalid_schema_values(self):
        cases = [
            ((), "version", True), ((), "version", 2), ((), "extra", 1),
            ((), "artifacts", "result.csv"), ((), "requirements", None),
            ((), "requirements", []),
            (("requirements", 0), "id", " "),
            (("requirements", 0), "id", "R" * 81),
            (("requirements", 0), "id", " R1"),
            (("requirements", 0), "criterion", " "),
            (("requirements", 0), "criterion", "a" * 4097),
            (("requirements", 0), "status", "passed"),
            (("requirements", 0), "evidence", {}),
            (("requirements", 0, "evidence", 0), "sha256", "0" * 63),
            (("requirements", 0, "evidence", 0), "sha256", "A" * 64),
            (("requirements", 0, "evidence", 0), "exit_code", True),
            (("requirements", 0, "evidence", 0), "exit_code", "0"),
            (("requirements", 0, "evidence", 0), "exit_code", 0.0),
            (("requirements", 0, "evidence", 0), "command", " "),
            (("requirements", 0, "evidence", 0), "command", "a" * 4097),
            (("requirements", 0, "evidence", 0), "path", ""),
            (("requirements", 0, "evidence", 0), "path", "a" * 1025),
            (("requirements", 0, "evidence", 0), "inputs", None),
            (("requirements", 0, "evidence", 0, "inputs", 0), "sha256", "z" * 64),
        ]
        original = copy.deepcopy(self.manifest)
        for path, key, value in cases:
            with self.subTest(path=path, key=key, value=value):
                self.manifest = copy.deepcopy(original)
                target = self.manifest
                for item in path:
                    target = target[item]
                target[key] = value
                with self.assertRaises(InputError):
                    self.check()

    def test_missing_keys_and_nonobjects_are_invalid(self):
        original = copy.deepcopy(self.manifest)
        for key in original:
            self.manifest = copy.deepcopy(original)
            del self.manifest[key]
            with self.assertRaises(InputError):
                self.check()
        for invalid in ([], None, 1, "manifest"):
            self.manifest = invalid
            with self.assertRaises(InputError):
                self.check()

    def test_list_bounds(self):
        original = copy.deepcopy(self.manifest)
        for path, key, count in [((), "artifacts", 101), ((), "requirements", 101),
                                 (("requirements", 0), "evidence", 11),
                                 (("requirements", 0, "evidence", 0), "inputs", 101)]:
            with self.subTest(key=key):
                self.manifest = copy.deepcopy(original)
                target = self.manifest
                for item in path:
                    target = target[item]
                target[key] *= count
                with self.assertRaises(InputError):
                    self.check()

    def test_escaping_paths_at_every_location_are_invalid(self):
        original = copy.deepcopy(self.manifest)
        for field in ("artifact", "evidence", "input"):
            for unsafe in ("../outside.txt", str(self.root.parent / "outside.txt")):
                with self.subTest(field=field, unsafe=unsafe):
                    self.manifest = copy.deepcopy(original)
                    evidence = self.manifest["requirements"][0]["evidence"][0]
                    if field == "artifact":
                        self.manifest["artifacts"] = [unsafe]
                    elif field == "evidence":
                        evidence["path"] = unsafe
                    else:
                        evidence["inputs"][0]["path"] = unsafe
                    with self.assertRaises(InputError):
                        self.check()
        with self.assertRaises(InputError):
            check_evidence(self.workspace, "../manifest.json")

    def test_symlink_escape_is_invalid(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "file"
            target.write_bytes(b"external")
            (self.root / "linked").symlink_to(target)
            self.manifest["artifacts"] = ["linked"]
            with self.assertRaises(InputError):
                self.check()
            target.unlink()
            with self.assertRaises(InputError):
                self.check()

    def test_truncation_preserves_total_and_never_echoes_file_or_command(self):
        self.manifest["artifacts"] = [f"absent-{i}" for i in range(8)]
        self.manifest["requirements"][0]["evidence"][0]["command"] = "SECRET_COMMAND_CONTENT"
        result = self.check(limit=2)
        self.assertEqual(len(result["findings"]), 2)
        self.assertEqual(result["total_findings"], 8)
        self.assertTrue(result["truncated"])
        self.assertNotIn("SECRET_COMMAND_CONTENT", json.dumps(result))
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_invalid_limits(self):
        for limit in (0, 31, True, 1.2, "2"):
            with self.subTest(limit=limit), self.assertRaises(InputError):
                self.check(limit)

    def test_invalid_json_and_duplicate_json_keys(self):
        for contents in (b"{invalid", b'{"version":1,"version":1,"artifacts":[],"requirements":[]}'):
            self.write("manifest.json", contents)
            with self.assertRaises(InputError):
                check_evidence(self.workspace, "manifest.json")

    def test_nonregular_oversized_and_invalid_utf8_inputs_are_invalid(self):
        self.manifest["artifacts"] = ["directory"]
        (self.root / "directory").mkdir()
        with self.assertRaises(InputError):
            self.check()
        self.manifest["artifacts"] = ["large.bin"]
        with (self.root / "large.bin").open("wb") as stream:
            stream.truncate(8_388_609)
        with self.assertRaises(InputError):
            self.check()
        self.write("manifest.json", b"\xff\xfe")
        with self.assertRaises(InputError):
            check_evidence(self.workspace, "manifest.json")

    def test_invalid_schema_is_rejected_even_after_finding_limit(self):
        self.manifest["artifacts"] = ["missing"]
        self.manifest["requirements"][0]["evidence"][0]["inputs"][0]["path"] = "../outside"
        with self.assertRaises(InputError):
            self.check(limit=1)

    def test_commands_are_not_executed(self):
        self.manifest["requirements"][0]["evidence"][0]["command"] = f"touch '{self.root / 'sentinel'}'"
        self.assertEqual(self.check()["status"], "no_findings")
        self.assertFalse((self.root / "sentinel").exists())

    def test_lone_surrogates_are_rejected_in_all_manifest_text_fields(self):
        original = copy.deepcopy(self.manifest)
        for path, key in [(('requirements', 0), 'id'),
                          (('requirements', 0), 'criterion'),
                          (('requirements', 0, 'evidence', 0), 'command'),
                          (('requirements', 0, 'evidence', 0), 'path'),
                          (('requirements', 0, 'evidence', 0, 'inputs', 0), 'path')]:
            with self.subTest(key=key, path=path):
                self.manifest = copy.deepcopy(original)
                self.manifest['requirements'][0]['status'] = 'unverified'
                target = self.manifest
                for item in path:
                    target = target[item]
                target[key] = '\ud800'
                with self.assertRaises(InputError):
                    self.check()
        self.manifest = copy.deepcopy(original)
        self.manifest['artifacts'] = ['\udfff']
        with self.assertRaises(InputError):
            self.check()

    def test_repeated_canonical_file_is_read_once_and_uses_one_snapshot(self):
        calls = []

        class ChangingWorkspace(Workspace):
            def read_bytes(inner, path, max_bytes=8_388_608):
                canonical = inner.relative(path)
                calls.append(canonical)
                data = super().read_bytes(path, max_bytes)
                if canonical == 'verification.txt':
                    (self.root / canonical).write_bytes(b'changed after first read')
                return data

        self.workspace = ChangingWorkspace(self.root)
        (self.root / 'alias.txt').symlink_to(self.root / 'verification.txt')
        self.manifest['artifacts'] = ['verification.txt', './verification.txt', 'alias.txt']
        evidence = self.manifest['requirements'][0]['evidence'][0]
        evidence['inputs'] = [{'path': 'alias.txt', 'sha256': evidence['sha256']}]
        self.assertEqual(self.check()['status'], 'no_findings')
        self.assertEqual(calls.count('verification.txt'), 1)

    def test_distinct_path_budget(self):
        evidence = self.manifest['requirements'][0]['evidence'][0]
        links = []
        for index in range(3):
            link = copy.deepcopy(evidence)
            link['inputs'] = []
            for number in range(100):
                name = f'input-{index}-{number}'
                self.write(name, b'x')
                link['inputs'].append({'path': name, 'sha256': self.hash(name)})
            links.append(link)
        self.manifest['requirements'][0]['evidence'] = links
        with self.assertRaises(InputError):
            self.check()
        links[-1]['inputs'] = links[-1]['inputs'][:53]
        self.assertEqual(self.check()['status'], 'no_findings')

    def test_total_read_budget(self):
        bytes_read = []

        class CountingWorkspace(Workspace):
            def read_bytes(inner, path, max_bytes=8_388_608):
                data = super().read_bytes(path, max_bytes)
                bytes_read.append(len(data))
                return data

        self.workspace = CountingWorkspace(self.root)
        self.manifest['artifacts'] = []
        for index in range(9):
            name = f'large-{index}.bin'
            self.write(name, b'x' * 8_388_608)
            self.manifest['artifacts'].append(name)
        with self.assertRaises(InputError):
            self.check()
        self.assertLessEqual(sum(bytes_read), 64 * 1024 * 1024)
        self.manifest['artifacts'] = self.manifest['artifacts'][:7]
        self.assertEqual(self.check()['status'], 'no_findings')


if __name__ == "__main__":
    unittest.main()

"""Bounded, deterministic numeric and direct-quotation revision checks."""

from bisect import bisect_right
from dataclasses import dataclass
import re
from typing import TYPE_CHECKING

from .workspace import InputError

if TYPE_CHECKING:
    from .workspace import Workspace


_NUMBER = re.compile(
    r"[+−-]?(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?"
    r"(?P<unit>[ \t]*(?:[A-Za-zµμ°℃℉%‰]+|시간|개월|킬로그램|미터|"
    r"퍼센트|백만원|만원|천원|억원|건|회|명|개|원|년|월|일|분|초|주|배|대|톤))?"
)
_SUBJECT = re.compile(r"[^\W\d_]+$", re.UNICODE)
_LOOKAHEAD = 8
_LIMITATION = (
    "This heuristic compares numeric tokens, short preceding subject contexts, "
    "and paired direct quotations using bounded local alignment. Findings are "
    "review candidates; reordering, ambiguous alignment, unrecognized units, "
    "nested or unmatched quotes, and semantic changes require manual comparison. "
    "No findings does not establish semantic or factual correctness."
)


@dataclass(frozen=True)
class _Token:
    start: int
    value: str
    key: tuple[str, ...]
    context: str = ""


def _numbers(text: str) -> list[_Token]:
    tokens = []
    for match in _NUMBER.finditer(text):
        raw_unit = match.group("unit") or ""
        raw_number = match.group()[:len(match.group()) - len(raw_unit)]
        number = raw_number.replace(",", "").replace("−", "-")
        prefix = text[max(0, match.start() - 32):match.start()].rstrip(" \t")
        subject = _SUBJECT.search(prefix)
        tokens.append(_Token(match.start(), match.group(),
                             (number, raw_unit.strip()),
                             subject.group() if subject else ""))
    return tokens


def _quotes(text: str) -> list[_Token]:
    pairs = {'"': '"', "'": "'", '“': '”', '‘': '’'}
    tokens = []
    start = None
    closing = None
    for index, char in enumerate(text):
        # English contractions use apostrophes; Korean quoted words may be
        # immediately followed by a particle, so isalnum alone is too broad.
        if (char in "'’" and index > 0 and index + 1 < len(text)
                and text[index - 1].isascii() and text[index + 1].isascii()
                and text[index - 1].isalnum() and text[index + 1].isalnum()):
            continue
        if start is None:
            if char in pairs:
                start, closing = index, pairs[char]
        elif char == closing:
            value = text[start:index + 1]
            tokens.append(_Token(start, value, (text[start + 1:index],)))
            start, closing = None, None
    return tokens


def _align(original: list[_Token], revised: list[_Token]):
    """Greedy positional alignment with a constant-size exact-match window."""
    left = right = 0
    while left < len(original) and right < len(revised):
        if original[left].key == revised[right].key:
            yield original[left], revised[right]
            left += 1
            right += 1
            continue
        removed = next((step for step in range(1, _LOOKAHEAD + 1)
                        if left + step < len(original)
                        and original[left + step].key == revised[right].key), None)
        added = next((step for step in range(1, _LOOKAHEAD + 1)
                      if right + step < len(revised)
                      and original[left].key == revised[right + step].key), None)
        if removed is not None and (added is None or removed <= added):
            for token in original[left:left + removed]:
                yield token, None
            left += removed
        elif added is not None:
            for token in revised[right:right + added]:
                yield None, token
            right += added
        else:
            yield original[left], revised[right]
            left += 1
            right += 1
    for token in original[left:]:
        yield token, None
    for token in revised[right:]:
        yield None, token


def _brief(value: str) -> str:
    return value if len(value) <= 96 else value[:93] + "..."


def audit_revision(workspace: "Workspace", original: str, revised: str,
                   limit: int = 5) -> dict:
    """Inspect two workspace text files without asserting meaning preservation."""
    if type(limit) is not int or not 1 <= limit <= 30:
        raise InputError("limit must be an integer from 1 to 30")
    texts = [workspace.read_text(path, max_bytes=262144) for path in (original, revised)]
    paths = [str(workspace.relative(path)) for path in (original, revised)]
    line_starts = [[0] + [index + 1 for index, char in enumerate(text) if char == "\n"]
                   for text in texts]
    findings = []
    total = 0

    def side(token: _Token, which: int) -> dict:
        line = bisect_right(line_starts[which], token.start)
        result = {"value": _brief(token.value), "location": {
            "path": paths[which], "line": line,
            "column": token.start - line_starts[which][line - 1] + 1}}
        if token.context:
            result["context"] = token.context
        return result

    def record(rule: str, before: _Token | None, after: _Token | None):
        nonlocal total
        total += 1
        if len(findings) < limit:
            finding = {"rule": rule}
            if before is not None:
                finding["original"] = side(before, 0)
            if after is not None:
                finding["revised"] = side(after, 1)
            findings.append(finding)

    for kind, extractor in (("NUMBER", _numbers), ("QUOTE", _quotes)):
        for before, after in _align(extractor(texts[0]), extractor(texts[1])):
            if before is None:
                record(kind + "_ADDED", before, after)
            elif after is None:
                record(kind + "_REMOVED", before, after)
            elif kind == "QUOTE":
                if before.key != after.key:
                    record("QUOTE_CHANGED", before, after)
            else:
                if before.key[0] != after.key[0]:
                    record("NUMBER_CHANGED", before, after)
                if before.key[1] != after.key[1]:
                    record("UNIT_CHANGED", before, after)
                if before.key == after.key and before.context != after.context:
                    record("NUMBER_CONTEXT_CHANGED", before, after)
    return {"tool": "audit_revision", "status": "findings" if total else "no_findings",
            "total_findings": total, "findings": findings,
            "truncated": total > len(findings), "limitations": _LIMITATION}

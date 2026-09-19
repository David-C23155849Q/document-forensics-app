"""
DiffEngine: computes word-level diffs between two document states.

This underlies both event detection (what changed) and document
reconstruction (applying diffs on top of a checkpoint).
"""
import difflib
from dataclasses import dataclass, field


@dataclass
class DiffResult:
    op: str  # "equal" | "insert" | "delete" | "replace"
    old_words: list = field(default_factory=list)
    new_words: list = field(default_factory=list)
    old_start: int = 0
    new_start: int = 0


class DiffEngine:
    @staticmethod
    def tokenize(text: str):
        return (text or "").split()

    @classmethod
    def diff_words(cls, old_text: str, new_text: str):
        old_words = cls.tokenize(old_text)
        new_words = cls.tokenize(new_text)
        matcher = difflib.SequenceMatcher(a=old_words, b=new_words, autojunk=False)
        results = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            results.append(
                DiffResult(
                    op={"insert": "insert", "delete": "delete", "replace": "replace"}[tag],
                    old_words=old_words[i1:i2],
                    new_words=new_words[j1:j2],
                    old_start=i1,
                    new_start=j1,
                )
            )
        return results

    @classmethod
    def apply_diff(cls, base_text: str, diff_ops: list) -> str:
        """Reconstruct new text by applying a serialized diff to base_text."""
        words = cls.tokenize(base_text)
        offset = 0
        for op in diff_ops:
            start = op["old_start"] + offset
            old_len = len(op["old_words"])
            new_words = op["new_words"]
            words[start:start + old_len] = new_words
            offset += len(new_words) - old_len
        return " ".join(words)

    @classmethod
    def serialize(cls, diff_ops: list) -> list:
        return [
            {"op": d.op, "old_words": d.old_words, "new_words": d.new_words,
             "old_start": d.old_start, "new_start": d.new_start}
            for d in diff_ops
        ]

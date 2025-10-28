"""Automated quality checks for translated chapters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict, Any

REPLACEMENT_CHAR = "\ufffd"


@dataclass
class ParagraphIssue:
    """Represents an issue found in a paragraph."""

    chapter: str
    paragraph_index: int
    message: str
    severity: str = "warning"


@dataclass
class AutomatedCheckReport:
    """Summary of automated checks."""

    encoding_issues: List[ParagraphIssue]
    missing_paragraphs: List[ParagraphIssue]
    untranslated_text: List[ParagraphIssue]

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Serialize the report to a JSON-compatible dictionary."""

        return {
            "encoding_issues": [issue.__dict__ for issue in self.encoding_issues],
            "missing_paragraphs": [issue.__dict__ for issue in self.missing_paragraphs],
            "untranslated_text": [issue.__dict__ for issue in self.untranslated_text],
        }


def _iter_entries(entries: Iterable[Dict[str, Any]]):
    for entry in entries:
        if not isinstance(entry, dict):
            raise TypeError("Each entry must be a dictionary")
        try:
            chapter = str(entry["chapter"])
            paragraph_index = int(entry["paragraph_index"])
            source = str(entry.get("source", ""))
            translation = str(entry.get("translation", ""))
        except KeyError as exc:
            raise KeyError(f"Missing required key: {exc.args[0]}") from exc
        yield chapter, paragraph_index, source, translation


def detect_encoding_issues(entries: Iterable[Dict[str, Any]]) -> List[ParagraphIssue]:
    """Detect paragraphs that contain encoding problems such as replacement chars."""

    issues: List[ParagraphIssue] = []
    for chapter, paragraph_index, _, translation in _iter_entries(entries):
        if REPLACEMENT_CHAR in translation:
            issues.append(
                ParagraphIssue(
                    chapter=chapter,
                    paragraph_index=paragraph_index,
                    message="Translation contains the Unicode replacement character (�)",
                    severity="error",
                )
            )
    return issues


def detect_missing_paragraphs(entries: Iterable[Dict[str, Any]]) -> List[ParagraphIssue]:
    """Find paragraphs where the translation is empty or nearly empty."""

    issues: List[ParagraphIssue] = []
    for chapter, paragraph_index, source, translation in _iter_entries(entries):
        if source.strip() and not translation.strip():
            issues.append(
                ParagraphIssue(
                    chapter=chapter,
                    paragraph_index=paragraph_index,
                    message="Missing translation for non-empty source paragraph",
                    severity="error",
                )
            )
    return issues


def detect_untranslated_text(entries: Iterable[Dict[str, Any]]) -> List[ParagraphIssue]:
    """Identify paragraphs that are likely left untranslated."""

    issues: List[ParagraphIssue] = []
    for chapter, paragraph_index, source, translation in _iter_entries(entries):
        normalized_source = source.strip()
        normalized_translation = translation.strip()
        if not normalized_source or not normalized_translation:
            continue
        if normalized_source == normalized_translation:
            issues.append(
                ParagraphIssue(
                    chapter=chapter,
                    paragraph_index=paragraph_index,
                    message="Translation matches source text exactly",
                )
            )
            continue
        source_chinese_ratio = _chinese_character_ratio(normalized_source)
        translation_chinese_ratio = _chinese_character_ratio(normalized_translation)
        if translation_chinese_ratio > 0.4 and translation_chinese_ratio >= source_chinese_ratio:
            issues.append(
                ParagraphIssue(
                    chapter=chapter,
                    paragraph_index=paragraph_index,
                    message="Translation still contains a high proportion of Chinese characters",
                )
            )
    return issues


def _chinese_character_ratio(text: str) -> float:
    if not text:
        return 0.0
    chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    return chinese_chars / len(text)


def run_automated_checks(entries: Iterable[Dict[str, Any]]) -> AutomatedCheckReport:
    """Run all automated checks and return an aggregated report."""

    entries_list = list(entries)
    return AutomatedCheckReport(
        encoding_issues=detect_encoding_issues(entries_list),
        missing_paragraphs=detect_missing_paragraphs(entries_list),
        untranslated_text=detect_untranslated_text(entries_list),
    )


__all__ = [
    "ParagraphIssue",
    "AutomatedCheckReport",
    "detect_encoding_issues",
    "detect_missing_paragraphs",
    "detect_untranslated_text",
    "run_automated_checks",
]

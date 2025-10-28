"""Glossary utilities for enforcing consistent terminology."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass
class GlossaryIssue:
    """Represents an inconsistency between the glossary and a translation."""

    chapter: str
    paragraph_index: int
    term: str
    expected_translation: str
    actual_text: str


class Glossary:
    """Load a bilingual glossary and detect term inconsistencies."""

    def __init__(self, glossary_map: Dict[str, str]):
        self.glossary_map = {term.strip(): translation.strip() for term, translation in glossary_map.items() if term.strip()}

    @classmethod
    def from_csv(cls, path: str) -> "Glossary":
        """Load a glossary from a CSV file with two columns: term,translation."""

        glossary_map: Dict[str, str] = {}
        with open(path, "r", encoding="utf-8") as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                if not row or row[0].startswith("#"):
                    continue
                if len(row) < 2:
                    raise ValueError(f"Expected at least two columns in glossary row: {row}")
                glossary_map[row[0].strip()] = row[1].strip()
        return cls(glossary_map)

    def check_translation(self, entries: Iterable[Dict[str, str]]) -> List[GlossaryIssue]:
        """Verify that each term is translated according to the glossary."""

        issues: List[GlossaryIssue] = []
        for entry in entries:
            chapter = str(entry.get("chapter", ""))
            paragraph_index = int(entry.get("paragraph_index", -1))
            translation = str(entry.get("translation", ""))
            for term, expected in self.glossary_map.items():
                if term in translation and expected not in translation:
                    issues.append(
                        GlossaryIssue(
                            chapter=chapter,
                            paragraph_index=paragraph_index,
                            term=term,
                            expected_translation=expected,
                            actual_text=translation,
                        )
                    )
        return issues

    def replace_terms(self, text: str) -> str:
        """Return text with glossary terms replaced by their expected translation."""

        for term, expected in self.glossary_map.items():
            text = text.replace(term, expected)
        return text

    def suggestions(self, translation: str) -> List[Tuple[str, str]]:
        """Return glossary suggestions for a translation snippet."""

        matches: List[Tuple[str, str]] = []
        for term, expected in self.glossary_map.items():
            if term in translation and expected not in translation:
                matches.append((term, expected))
        return matches


__all__ = ["Glossary", "GlossaryIssue"]

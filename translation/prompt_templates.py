"""Prompt templates for translation emphasizing fidelity and cultural context."""
from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass
from typing import Dict


class _SafeDict(UserDict):
    def __missing__(self, key: str) -> str:  # type: ignore[override]
        return ""


@dataclass(frozen=True)
class PromptTemplate:
    """Container for prompt templates used for translation requests."""

    system: str
    user: str

    def render(self, *, source_text: str, metadata: Dict[str, str] | None = None) -> Dict[str, str]:
        """Render the prompt templates with the provided content.

        Parameters
        ----------
        source_text:
            The Chinese source text to translate.
        metadata:
            Optional metadata such as chapter titles that can be interpolated
            into the prompt.
        """

        metadata = _SafeDict(metadata or {})
        user_args = _SafeDict(metadata)
        user_args["source_text"] = source_text
        formatted_user = self.user.format_map(user_args)
        formatted_system = self.system.format_map(metadata)
        return {"system": formatted_system, "user": formatted_user}


DEFAULT_PROMPT_TEMPLATE = PromptTemplate(
    system=(
        "You are a meticulous literary translator specializing in xianxia and "
        "wuxia cultivation novels. Preserve terminology, relationships, and "
        "cultivation ranks. Maintain respectful address forms and accurately "
        "render dialogue punctuation."
    ),
    user=(
        "Translate the following Chinese passage into natural, fluent English. "
        "Preserve paragraph breaks, speaker formatting, and cultivation terms. "
        "Do not summarize or omit details.\n\n"
        "<Source>{source_text}</Source>"
    ),
)

"""Translation entry point that honors the configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List

import pandas as pd
from dotenv import load_dotenv

from config_loader import APIConfig, ConfigError, LocalModelConfig, TranslationConfig, load_config

try:
    import openai
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "openai is required for API-based translation. Install via `pip install openai`."
    ) from exc

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "transformers is required for local translation. Install via `pip install transformers`."
    ) from exc


class Translator:
    """Translate Chinese text to English using API or local models."""

    def __init__(self, config: TranslationConfig) -> None:
        self.config = config
        load_dotenv()

        if config.approach == "api":
            self._initialize_api_client(config.api)
        else:
            self._initialize_local_model(config.local)

    def _initialize_api_client(self, config: APIConfig) -> None:
        if config.provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ConfigError("OPENAI_API_KEY must be set for OpenAI translation")
            openai.api_key = api_key
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            azure_key = os.environ.get("AZURE_OPENAI_API_KEY")
            if endpoint and azure_key:
                openai.base_url = endpoint
                openai.api_key = azure_key
        elif config.provider == "deepl":
            api_key = os.environ.get("DEEPL_API_KEY")
            if not api_key:
                raise ConfigError("DEEPL_API_KEY must be set for DeepL translation")
        else:
            raise ConfigError(f"Unsupported API provider '{config.provider}'")

    def _initialize_local_model(self, config: LocalModelConfig) -> None:
        self._tokenizer = AutoTokenizer.from_pretrained(config.model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(config.model_name)
        self._local_config = config

    def translate(self, texts: Iterable[str]) -> List[str]:
        """Translate a batch of texts based on the configured approach."""

        if self.config.approach == "api":
            return self._translate_via_api(list(texts))
        return self._translate_locally(list(texts))

    def _translate_via_api(self, texts: List[str]) -> List[str]:
        client = openai.OpenAI()
        responses = []
        for text in texts:
            response = client.responses.create(
                model=self.config.api.model,
                input=[
                    {
                        "role": "system",
                        "content": "You are a professional translator that converts Chinese into English while preserving tone and nuance.",
                    },
                    {
                        "role": "user",
                        "content": f"Translate the following Chinese text to English:\n\n{text}",
                    },
                ],
                temperature=self.config.api.temperature,
                max_output_tokens=self.config.api.max_tokens_per_request,
                timeout=self.config.api.request_timeout_seconds,
            )
            responses.append(response.output[0].content[0].text)
        return responses

    def _translate_locally(self, texts: List[str]) -> List[str]:
        tokenizer = self._tokenizer
        model = self._model
        local_config = self._local_config

        inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=local_config.max_length)
        outputs = model.generate(
            **inputs,
            max_length=local_config.max_length,
        )
        return tokenizer.batch_decode(outputs, skip_special_tokens=True)

    @classmethod
    def from_config_path(cls, path: Path) -> "Translator":
        return cls(load_config(path))


def translate_dataframe(input_path: Path, output_path: Path, config_path: Path) -> None:
    """Translate the ``text`` column of a CSV file."""

    translator = Translator.from_config_path(config_path)
    df = pd.read_csv(input_path)
    if "text" not in df.columns:
        raise ValueError("Input CSV must contain a 'text' column")

    df["translation"] = translator.translate(df["text"].tolist())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


__all__ = ["Translator", "translate_dataframe"]

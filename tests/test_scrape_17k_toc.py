import sqlite3
from pathlib import Path

import pytest

from src.scrape_17k_toc import (
    Chapter,
    dump_to_json,
    extract_chapter_id,
    parse_toc,
    persist_chapters,
)


@pytest.fixture
def sample_html() -> str:
    return Path("sample_data/17k_list_sample.html").read_text(encoding="utf-8")


def test_parse_toc_extracts_chapters(sample_html):
    chapters = parse_toc(sample_html, "https://www.17k.com/list/493239.html")
    assert len(chapters) == 3
    ids = {chapter.identifier for chapter in chapters}
    assert ids == {"3660486", "3660487", "3660488"}
    titles = [chapter.title for chapter in chapters]
    assert "第一章 天地初开" in titles
    assert any(ch.publication_date == "2012-02-16 10:00:00" for ch in chapters)


def test_extract_chapter_id_fallback():
    assert extract_chapter_id("https://www.17k.com/chapter/1/2.html") == "2"
    assert (
        extract_chapter_id("https://www.17k.com/chapter/novel/extra")
        == "extra"
    )


def test_persist_chapters_skips_existing(tmp_path, sample_html):
    db_path = tmp_path / "chapters.db"
    with sqlite3.connect(db_path) as connection:
        chapters = parse_toc(sample_html, "https://www.17k.com/list/493239.html")
        inserted_first = persist_chapters(connection, chapters)
        assert inserted_first == 3

        # Re-run: nothing should be inserted.
        inserted_second = persist_chapters(connection, chapters)
        assert inserted_second == 0

        rows = connection.execute(
            "SELECT id, title, url, publication_date FROM chapters ORDER BY id"
        ).fetchall()
        assert len(rows) == 3
        assert rows[0][0] == "3660486"


def test_dump_to_json(tmp_path):
    chapters = [
        Chapter(identifier="1", title="Test", url="http://example.com", publication_date=None)
    ]
    json_path = tmp_path / "chapters.json"
    dump_to_json(chapters, json_path)
    assert json_path.exists()
    content = json_path.read_text(encoding="utf-8")
    assert "Test" in content

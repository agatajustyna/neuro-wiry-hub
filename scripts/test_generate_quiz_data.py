#!/usr/bin/env python3
import datetime
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_quiz_data import slugify, parse_tags, cites_letter, cell_text, build_section_meta, is_excluded


def _cell(value, number_format="General"):
    return SimpleNamespace(value=value, number_format=number_format)


def test_slugify():
    assert slugify("Ogólne") == "ogolne"
    assert slugify("Kresomózgowie") == "kresomozgowie"
    assert slugify("Kora mózgu - płat czołowy") == "kora-mozgu-plat-czolowy"
    assert slugify("Czucie powierzchniowe") == "czucie-powierzchniowe"
    assert slugify("  Wyspa  ") == "wyspa"


def test_parse_tags():
    assert parse_tags("#nerw_VII #neuroanatomia #Krasucki") == ["nerw_vii", "neuroanatomia", "krasucki"]
    assert parse_tags("neuron, akson") == ["neuron", "akson"]
    assert parse_tags("#OUN #anatomia #oun") == ["oun", "anatomia"]
    assert parse_tags("") == []


def test_cites_letter():
    assert cites_letter("Odpowiedź C jest poprawna, bo...") is True
    assert cites_letter("B jest nieprawidłowa, ponieważ...") is True
    assert cites_letter("Nerwy czaszkowe to układ obwodowy.") is False
    assert cites_letter("Pole A należy do kory ruchowej.") is False


def test_cell_text():
    assert cell_text(_cell(31.0)) == "31"            # integer-valued float, no decimals
    assert cell_text(_cell(1.007)) == "1.007"        # non-integer float verbatim
    assert cell_text(_cell(datetime.datetime(2026, 1, 2), "m-d")) == "1-2"  # date w/o year -> m-d
    assert cell_text(_cell(datetime.datetime(2026, 1, 2), "yyyy-mm-dd")) == "2026-01-02"
    assert cell_text(_cell(None)) == ""
    assert cell_text(_cell("  x  ")) == "x"


def test_is_excluded():
    assert is_excluded("TAK") is True
    assert is_excluded(" tak ") is True
    assert is_excluded("x") is True
    assert is_excluded("") is False
    assert is_excluded("nie") is False


def test_build_section_meta():
    section = {
        "id": 6,
        "title": "Śródmózgowie",
        "topics": [
            {"slug": "istota-czarna", "title": "Istota czarna"},
            {"slug": "wzgorki", "title": "Wzgórki"},
        ],
        "questions": [
            {"topic": "Istota czarna"},
            {"topic": "Istota czarna"},
            {"topic": "Wzgórki"},
        ],
    }
    meta = build_section_meta(section)
    assert meta["questionCount"] == 3
    assert meta["file"] == "sections/6.json"
    assert meta["slug"] == "srodmozgowie"
    topics_by_title = {t["title"]: t for t in meta["topics"]}
    assert topics_by_title["Istota czarna"]["questionCount"] == 2
    assert topics_by_title["Wzgórki"]["questionCount"] == 1


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"OK {fn.__name__}")
    print(f"Wszystkie testy przeszły ({len(tests)})")

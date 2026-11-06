"""The image holds what the API reads at run time, and nothing that must stay out of it."""

import re
from pathlib import Path

import pytest

import api.main as main
from api.foundry import setting

ROOT = Path(__file__).parent.parent


def copied() -> list[str]:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    return [source for source in re.findall(r"^COPY (\S+) ", text, re.M)]


def ignored() -> list[str]:
    lines = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def test_the_image_has_the_code_the_sample_and_the_statistics_canada_copy():
    sources = copied()
    assert {"requirements.txt", "api/"} <= set(sources)
    assert main.SAMPLE.as_posix() in sources
    assert main.REFERENCE.as_posix() in sources


def test_settings_and_local_environments_never_reach_the_image():
    rules = ignored()
    assert {".env", ".env.*", ".venv/", ".git/", "scripts/out/"} <= set(rules)


def test_a_missing_setting_says_which_one(monkeypatch):
    monkeypatch.delenv("AGENT_NAME", raising=False)
    with pytest.raises(RuntimeError, match="AGENT_NAME is missing"):
        setting("AGENT_NAME")

"""config.py 单元测试：.env 解析（用临时文件，绝不读真实 .env）。"""

import os

import pytest

from agent.config import Config, load_dotenv


def test_load_dotenv_parses_key_value(monkeypatch, tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nexport BAZ='qux'\n# comment\n\n", encoding="utf-8")
    monkeypatch.delenv("FOO", raising=False)
    monkeypatch.delenv("BAZ", raising=False)
    load_dotenv(p)
    assert os.environ["FOO"] == "bar"
    assert os.environ["BAZ"] == "qux"


def test_load_dotenv_does_not_override_env(monkeypatch, tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=file\n", encoding="utf-8")
    monkeypatch.setenv("FOO", "env")
    load_dotenv(p)
    assert os.environ["FOO"] == "env"


def test_config_defaults(monkeypatch):
    monkeypatch.setattr("agent.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    c = Config.from_env()
    assert c.api_key == "k"
    assert c.base_url == "https://api.deepseek.com"
    assert c.model == "deepseek-chat"


def test_config_requires_api_key(monkeypatch):
    monkeypatch.setattr("agent.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        Config.from_env()


def test_config_think_switch(monkeypatch):
    monkeypatch.setattr("agent.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    monkeypatch.setenv("DEEPSEEK_THINK", "1")
    c = Config.from_env()
    assert c.think is True
    assert c.model == "deepseek-reasoner"


def test_config_explicit_model_wins_over_think(monkeypatch):
    monkeypatch.setattr("agent.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_THINK", "true")
    c = Config.from_env()
    assert c.think is True
    assert c.model == "deepseek-chat"  # 显式模型优先


def test_config_goal_switch(monkeypatch):
    monkeypatch.setattr("agent.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k")
    monkeypatch.setenv("DEEPSEEK_GOAL", "1")
    c = Config.from_env()
    assert c.goal is True

"""Tests for LLM client factory."""

from unittest.mock import patch

import pytest

from backend.app.agent.llm import get_llm_uncached

pytestmark = pytest.mark.unit


class TestGetLlm:
    """Test get_llm factory function."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        """Ensure lru_cache doesn't interfere between tests."""
        from backend.app.agent.llm import get_llm

        get_llm.cache_clear()
        yield
        get_llm.cache_clear()

    @patch("backend.app.agent.llm.get_settings")
    def test_openai_provider(self, mock_settings):
        mock_settings.return_value.llm_provider = "openai"
        mock_settings.return_value.openai_model = "gpt-4o"
        mock_settings.return_value.openai_api_key = "sk-test-key"

        llm = get_llm_uncached(temperature=0.0, max_tokens=2048)

        assert llm.model_name == "gpt-4o"
        assert llm.temperature == 0.0
        assert llm.max_tokens == 2048

    @patch("backend.app.agent.llm.get_settings")
    def test_claude_provider(self, mock_settings):
        mock_settings.return_value.llm_provider = "claude"
        mock_settings.return_value.anthropic_model = "claude-sonnet-4-5-20250929"
        mock_settings.return_value.anthropic_api_key = "sk-ant-test"

        llm = get_llm_uncached(temperature=0.1, max_tokens=4096)

        assert llm.model == "claude-sonnet-4-5-20250929"
        assert llm.temperature == 0.1
        assert llm.max_tokens == 4096

    @patch("backend.app.agent.llm.get_settings")
    def test_ollama_provider(self, mock_settings):
        mock_settings.return_value.llm_provider = "ollama"
        mock_settings.return_value.ollama_model = "qwen3:14b"
        mock_settings.return_value.ollama_base_url = "http://localhost:11434"

        llm = get_llm_uncached(temperature=0.0, max_tokens=2048)

        assert llm.model == "qwen3:14b"
        assert llm.base_url == "http://localhost:11434"
        assert llm.temperature == 0.0
        assert llm.num_predict == 2048

    @patch("backend.app.agent.llm.get_settings")
    def test_default_parameters(self, mock_settings):
        mock_settings.return_value.llm_provider = "openai"
        mock_settings.return_value.openai_model = "gpt-4o"
        mock_settings.return_value.openai_api_key = "sk-test"

        llm = get_llm_uncached()

        assert llm.temperature == 0.0
        assert llm.max_tokens == 4096

    @patch("backend.app.agent.llm.get_settings")
    def test_cached_get_llm_returns_same_instance(self, mock_settings):
        from backend.app.agent.llm import get_llm

        mock_settings.return_value.llm_provider = "openai"
        mock_settings.return_value.openai_model = "gpt-4o"
        mock_settings.return_value.openai_api_key = "sk-test"

        llm1 = get_llm()
        llm2 = get_llm()

        assert llm1 is llm2

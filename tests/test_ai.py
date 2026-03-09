"""Tests for strot_ai.ai."""
import pytest
import responses
from strot_ai.ai import LLM, MODELS


@pytest.fixture
def llm_instance(clean_env):
    inst = LLM(model="default", temperature=0.1)
    # Inject a test client
    from strot_ai.client import StrotClient
    inst._client = StrotClient(
        url="https://test.strot.ai", api_key="sk_test", max_retries=0,
    )
    return inst


class TestLLMModels:
    def test_default_model_resolved(self):
        inst = LLM(model="default")
        assert inst.model == MODELS["default"]

    def test_custom_model_passthrough(self):
        inst = LLM(model="my-custom-model")
        assert inst.model == "my-custom-model"


class TestLLMComplete:
    @responses.activate
    def test_complete(self, llm_instance):
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/arena/llm/complete",
            json={"content": "The answer is 42"},
        )
        result = llm_instance.complete("What is the meaning of life?")
        assert result == "The answer is 42"

    @responses.activate
    def test_call_syntax(self, llm_instance):
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/arena/llm/complete",
            json={"content": "Hello!"},
        )
        result = llm_instance("Say hello")
        assert result == "Hello!"


class TestLLMChat:
    @responses.activate
    def test_chat(self, llm_instance):
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/arena/llm/chat",
            json={"content": "Hi there!"},
        )
        result = llm_instance.chat([{"role": "user", "content": "Hello"}])
        assert result == "Hi there!"


class TestLLMClassify:
    @responses.activate
    def test_classify(self, llm_instance):
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/arena/llm/classify",
            json={"category": "positive"},
        )
        result = llm_instance.classify("Great product!", ["positive", "negative"])
        assert result == "positive"


class TestLLMExtract:
    @responses.activate
    def test_extract(self, llm_instance):
        responses.add(
            responses.POST,
            "https://test.strot.ai/api/arena/llm/extract",
            json={"result": {"name": "John", "age": 30}},
        )
        result = llm_instance.extract("John is 30", {"name": "string", "age": "number"})
        assert result == {"name": "John", "age": 30}

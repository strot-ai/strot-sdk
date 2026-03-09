"""Tests for strot_ai.decorators."""
from strot_ai.decorators import (
    function, agent, cortex, page,
    get_registry, get_functions, get_agents, get_cortex_nodes, get_pages,
    FunctionConfig, AgentConfig, CortexConfig, PageConfig,
)


class TestFunctionDecorator:
    def test_registers_class(self):
        @function(name="calc", description="Calculator", category="math")
        class Calc:
            def run(self, x: int) -> int:
                return x * 2

        registry = get_functions()
        assert "calc" in registry
        assert registry["calc"]["class"] is Calc

    def test_config_values(self):
        @function(
            name="my_func",
            description="Does stuff",
            category="tools",
            parameters=[{"name": "x", "type": "number"}],
            returns={"type": "string"},
        )
        class MyFunc:
            pass

        cfg = MyFunc._strot_config
        assert isinstance(cfg, FunctionConfig)
        assert cfg.name == "my_func"
        assert cfg.description == "Does stuff"
        assert cfg.category == "tools"
        assert len(cfg.parameters) == 1
        assert cfg.returns == {"type": "string"}

    def test_default_values(self):
        @function(name="minimal")
        class Minimal:
            pass

        cfg = Minimal._strot_config
        assert cfg.category == "custom"
        assert cfg.parameters == []
        assert cfg.returns == {}


class TestAgentDecorator:
    def test_registers_agent(self):
        @agent(name="analyst", tools=["calc"], model="gpt-4o")
        class Analyst:
            system_prompt = "You are a financial analyst."

        registry = get_agents()
        assert "analyst" in registry
        cfg = Analyst._strot_config
        assert isinstance(cfg, AgentConfig)
        assert cfg.tools == ["calc"]
        assert cfg.model == "gpt-4o"
        assert cfg.system_prompt == "You are a financial analyst."

    def test_system_prompt_from_docstring(self):
        @agent(name="helper")
        class Helper:
            """You are a helpful assistant."""
            pass

        cfg = Helper._strot_config
        assert cfg.system_prompt == "You are a helpful assistant."

    def test_default_values(self):
        @agent(name="basic")
        class Basic:
            pass

        cfg = Basic._strot_config
        assert cfg.model == "gpt-4o-mini"
        assert cfg.temperature == 0.1
        assert cfg.max_iterations == 10
        assert cfg.approval_required is False


class TestCortexDecorator:
    def test_registers_cortex(self):
        @cortex(name="etl", description="Daily ETL")
        class ETL:
            def build(self, flow):
                pass

        registry = get_cortex_nodes()
        assert "etl" in registry
        cfg = ETL._strot_config
        assert isinstance(cfg, CortexConfig)
        assert cfg.name == "etl"
        assert cfg.description == "Daily ETL"


class TestPageDecorator:
    def test_registers_page(self):
        @page(name="dashboard", type="dashboard", public=True)
        class Dashboard:
            def layout(self):
                pass

        registry = get_pages()
        assert "dashboard" in registry
        cfg = Dashboard._strot_config
        assert isinstance(cfg, PageConfig)
        assert cfg.type == "dashboard"
        assert cfg.public is True


class TestRegistry:
    def test_get_registry_returns_all_types(self):
        reg = get_registry()
        assert "function" in reg
        assert "agent" in reg
        assert "cortex" in reg
        assert "page" in reg

    def test_isolation_between_types(self):
        @function(name="tool_a")
        class ToolA:
            pass

        @agent(name="agent_a")
        class AgentA:
            pass

        assert "tool_a" in get_functions()
        assert "tool_a" not in get_agents()
        assert "agent_a" in get_agents()
        assert "agent_a" not in get_functions()

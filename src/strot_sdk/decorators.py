"""
STROT SDK — Decorators

Decorators for registering code as different STROT entities:
- @function: Register as a reusable tool
- @agent: Register as an AI agent
- @cortex: Register as a Cortex pipeline node
- @page: Register as a Pages dashboard/app

Usage:
    from strot_sdk import function, agent

    @function(name='calculate_roi', category='finance')
    class CalculateROI:
        async def run(self, cost: float, revenue: float) -> float:
            return ((revenue - cost) / cost) * 100

    @agent(
        name='sales_analyst',
        description='Analyzes sales data',
        tools=['top_n', 'trend_analysis']
    )
    class SalesAnalyst:
        system_prompt = '''You are a Sales Analyst.'''
"""
import logging
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Global registry for decorated classes
_REGISTRY = {
    'cortex': {},
    'page': {},
    'function': {},
    'agent': {},
}


@dataclass
class CortexConfig:
    """Configuration for @cortex decorated classes."""
    name: str
    description: str = ''
    category: str = 'custom'
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    node_type: str = 'arena_function'


@dataclass
class PageConfig:
    """Configuration for @page decorated classes."""
    name: str
    description: str = ''
    type: str = 'dashboard'
    layout: str = 'default'
    public: bool = False
    embed_allowed: bool = True


@dataclass
class FunctionConfig:
    """Configuration for @function decorated classes."""
    name: str
    description: str = ''
    category: str = 'custom'
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    returns: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)


@dataclass
class AgentConfig:
    """Configuration for @agent decorated classes."""
    name: str
    description: str = ''
    category: str = 'custom'
    tools: List[str] = field(default_factory=list)
    model: str = 'gpt-4o-mini'
    temperature: float = 0.1
    max_iterations: int = 10
    can_handoff_to: List[str] = field(default_factory=list)
    approval_required: bool = False
    system_prompt: str = ''


def cortex(
    name: str,
    description: str = '',
    category: str = 'custom',
    inputs: Optional[List[Dict[str, Any]]] = None,
    outputs: Optional[List[Dict[str, Any]]] = None,
):
    """Register a class as a Cortex workflow node."""
    def decorator(cls: Type) -> Type:
        config = CortexConfig(
            name=name, description=description, category=category,
            inputs=inputs or [], outputs=outputs or [],
        )
        cls._strot_config = config
        cls._strot_type = 'cortex'
        _REGISTRY['cortex'][name] = {'class': cls, 'config': config}
        logger.info(f"Registered Cortex node: {name}")
        return cls
    return decorator


def page(
    name: str,
    description: str = '',
    type: str = 'dashboard',
    layout: str = 'default',
    public: bool = False,
    embed_allowed: bool = True,
):
    """Register a class as a Page (dashboard or app)."""
    def decorator(cls: Type) -> Type:
        config = PageConfig(
            name=name, description=description, type=type,
            layout=layout, public=public, embed_allowed=embed_allowed,
        )
        cls._strot_config = config
        cls._strot_type = 'page'
        _REGISTRY['page'][name] = {'class': cls, 'config': config}
        logger.info(f"Registered Page: {name} (type={type})")
        return cls
    return decorator


def function(
    name: str,
    description: str = '',
    category: str = 'custom',
    parameters: Optional[List[Dict[str, Any]]] = None,
    returns: Optional[Dict[str, Any]] = None,
    examples: Optional[List[str]] = None,
):
    """Register a class or function as a reusable Arena tool."""
    def decorator(cls_or_func) -> Any:
        config = FunctionConfig(
            name=name, description=description, category=category,
            parameters=parameters or [], returns=returns or {},
            examples=examples or [],
        )
        cls_or_func._strot_config = config
        cls_or_func._strot_type = 'function'
        _REGISTRY['function'][name] = {'class': cls_or_func, 'config': config}
        logger.info(f"Registered Function: {name} (category={category})")
        return cls_or_func
    return decorator


def agent(
    name: str,
    description: str = '',
    category: str = 'custom',
    tools: Optional[List[str]] = None,
    model: str = 'gpt-4o-mini',
    temperature: float = 0.1,
    max_iterations: int = 10,
    can_handoff_to: Optional[List[str]] = None,
    approval_required: bool = False,
):
    """Register a class as an AI Agent."""
    def decorator(cls: Type) -> Type:
        system_prompt = getattr(cls, 'system_prompt', '') or cls.__doc__ or ''
        config = AgentConfig(
            name=name, description=description, category=category,
            tools=tools or [], model=model, temperature=temperature,
            max_iterations=max_iterations,
            can_handoff_to=can_handoff_to or [],
            approval_required=approval_required,
            system_prompt=system_prompt.strip(),
        )
        cls._strot_config = config
        cls._strot_type = 'agent'
        _REGISTRY['agent'][name] = {'class': cls, 'config': config}
        logger.info(f"Registered Agent: {name} (category={category}, tools={len(tools or [])})")
        return cls
    return decorator


# Registry access
def get_registry() -> Dict[str, Dict[str, Any]]:
    """Get the full decorator registry."""
    return _REGISTRY

def get_functions() -> Dict[str, Any]:
    return _REGISTRY['function']

def get_agents() -> Dict[str, Any]:
    return _REGISTRY['agent']

def get_cortex_nodes() -> Dict[str, Any]:
    return _REGISTRY['cortex']

def get_pages() -> Dict[str, Any]:
    return _REGISTRY['page']

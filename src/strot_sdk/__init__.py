"""
STROT SDK — Build tools, agents, pipelines, and dashboards in Python.

Usage:
    from strot_sdk import function, agent, cortex, page, strot, llm

    # Tool
    @function(name='calculate_roi', category='finance')
    class CalculateROI:
        def run(self, cost: float, revenue: float) -> float:
            return ((revenue - cost) / cost) * 100

    # Agent
    @agent(name='analyst', tools=['calculate_roi'])
    class Analyst:
        system_prompt = "You are a financial analyst."

    # Cortex Pipeline
    from strot_sdk.cortex import Flow
    @cortex(name='daily_etl', description='Daily ETL')
    class DailyETL:
        def build(self, flow: Flow):
            data = flow.data_connector('load', query_id=42)
            cleaned = flow.transform(data, prompt='Clean the data')
            flow.publish(cleaned, name='report', destination='slack')

    # Page / Dashboard
    from strot_sdk.pages import Dashboard, Row, KPI, Chart, Table
    @page(name='sales_dashboard', type='dashboard')
    class SalesDashboard:
        def layout(self):
            return Dashboard(
                Row(KPI(query_id=1, label='Revenue')),
                Row(Chart(query_id=2, type='line', title='Trend', span=8)),
                Row(Table(query_id=3, title='Top Customers')),
            )

    # LLM
    result = llm.complete("Summarize this text: " + text)

    # Data access
    rows = strot.queries['monthly_sales'].execute()

    # Notifications
    email.send(to="team@example.com", subject="Report", body="...")
"""

__version__ = "0.1.0"

# Decorators
from .decorators import function, agent, cortex, page

# Registry
from .registry import strot, StrotRegistry

# AI
from .ai import llm, LLM

# Data
from .data import query, query_one, query_df, execute_saved_query

# Destinations
from .destinations import email, slack, webhook

# Client
from .client import StrotClient, StrotAPIError

# Config
from .config import StrotConfig

# Types
from .types import ExecutionResult, QueryResult, DeployResult, Resource

__all__ = [
    # Decorators
    "function", "agent", "cortex", "page",
    # Registry
    "strot", "StrotRegistry",
    # AI
    "llm", "LLM",
    # Data
    "query", "query_one", "query_df", "execute_saved_query",
    # Destinations
    "email", "slack", "webhook",
    # Client
    "StrotClient", "StrotAPIError",
    # Config
    "StrotConfig",
    # Types
    "ExecutionResult", "QueryResult", "DeployResult", "Resource",
]

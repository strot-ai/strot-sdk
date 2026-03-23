# STROT

[![PyPI](https://img.shields.io/pypi/v/strot-ai)](https://pypi.org/project/strot-ai/)
[![Python](https://img.shields.io/pypi/pyversions/strot-ai)](https://pypi.org/project/strot-ai/)
[![License](https://img.shields.io/pypi/l/strot-ai)](LICENSE)

Build tools, agents, skills, pipelines, and dashboards for your [STROT](https://strot.ai) instance — in Python.

## Installation

```bash
pip install strot-ai
```

## Quick Start

```bash
strot login                         # Authenticate
strot init tool my-calculator       # Scaffold a project
cd my-calculator                    # Edit main.py with any editor
strot test                          # Validate locally
strot deploy                        # Ship to your STROT instance
```

## What You Can Build

| Type | Decorator | Description |
|------|-----------|-------------|
| **Tool** | `@function` | Reusable AI-callable functions (e.g., calculate ROI, parse CSV) |
| **Agent** | `@agent` | AI agents with system prompts and tool access |
| **Skill** | `@skill` | Multi-step AI workflows defined as markdown prompts |
| **Pipeline** | `@cortex` | Data pipelines with LLM transforms, routing, and publishing |
| **Dashboard** | `@page` | Interactive dashboards with KPIs, charts, and tables |

## Examples

### Tool

```python
from strot_ai import function, llm

@function(
    name='calculate_roi',
    description='Calculate return on investment',
    category='finance',
    parameters=[
        {'name': 'cost', 'type': 'number', 'description': 'Total cost'},
        {'name': 'revenue', 'type': 'number', 'description': 'Total revenue'},
    ],
    returns={'type': 'number', 'description': 'ROI percentage'}
)
class CalculateROI:
    def run(self, cost: float, revenue: float) -> float:
        return ((revenue - cost) / cost) * 100
```

### Agent

```python
from strot_ai import agent

@agent(
    name='sales_analyst',
    description='Analyzes sales data and provides insights',
    tools=['calculate_roi', 'top_n'],
    temperature=0.1,
)
class SalesAnalyst:
    system_prompt = """You are a sales analyst.
    Analyze data and provide actionable recommendations."""
```

### Skill

```python
from strot_ai import skill

@skill(
    name='dashboard_builder',
    description='Build interactive dashboards from queries',
    tools=['query_info', 'create_app', 'update_app', 'deploy_app'],
    trigger='build.*dashboard|create.*dashboard',
    emoji='📊',
    examples=['Build a dashboard from query 4'],
)
class DashboardBuilder:
    """## Workflow

    ### Step 1: Analyze Data
    Call `query_info` with the query_id to fetch schema and sample data.
    Ask: "Does this data look right?"

    ### Step 2: Map Data
    Plan how columns map to dashboard sections.
    Ask: "Does this mapping look good?"

    ### Step 3: Build
    Call `create_app` with the app_spec.
    """
```

### Pipeline

```python
from strot_ai import cortex
from strot_ai.cortex import Flow

@cortex(name='daily_etl', description='Daily ETL pipeline')
class DailyETL:
    def build(self, flow: Flow):
        data = flow.data_connector('load_sales', query_id=42)
        cleaned = flow.transform(data, prompt='Clean and normalize the data')
        flow.publish(cleaned, name='daily_report', destination='slack', channel='#data')
```

### Dashboard

```python
from strot_ai import page
from strot_ai.pages import Dashboard, Row, KPI, Chart, Table

@page(name='sales_dashboard', description='Sales overview', type='dashboard')
class SalesDashboard:
    def layout(self):
        return Dashboard(
            Row(
                KPI(query_id=1, label='Revenue', format='currency'),
                KPI(query_id=2, label='Orders'),
                KPI(query_id=3, label='Customers'),
            ),
            Row(
                Chart(query_id=5, type='line', title='Revenue Trend', span=8),
                Chart(query_id=6, type='donut', title='By Region', span=4),
            ),
            Row(
                Table(query_id=7, title='Recent Orders', sortable=True),
            ),
        )
```

## CLI Reference

```bash
strot login                              # Authenticate
strot login --token sk_live_abc123       # Direct API key
strot whoami                             # Show current user/org
strot logout                             # Clear credentials

strot init tool my-calculator            # Scaffold tool
strot init agent my-analyst              # Scaffold agent
strot init skill my-workflow             # Scaffold skill
strot init cortex my-pipeline            # Scaffold pipeline
strot init page my-dashboard             # Scaffold dashboard

strot test                               # Validate locally
strot deploy                             # Deploy to STROT
strot deploy --dry-run                   # Validate without deploying

strot resources                          # List all resources
strot resources queries                  # List saved queries
strot resources datasources              # List data sources
```

## Documentation

See [docs/guide.md](docs/guide.md) for the full SDK guide covering all decorators, built-in modules, configuration, and advanced patterns.

## Configuration

Credentials stored in `~/.strot/credentials`:

```yaml
version: 1
current_profile: default
profiles:
  default:
    url: https://app.strot.ai
    api_key: sk_live_abc123
    org: 98bf9a0a-c9cd-42a8-9ea4-4f7fee9a4535
```

**Priority:** Constructor args > Environment variables (`STROT_URL`, `STROT_API_KEY`) > Credentials file

## License

MIT

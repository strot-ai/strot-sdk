# STROT

[![PyPI](https://img.shields.io/pypi/v/strot-ai)](https://pypi.org/project/strot-ai/)
[![Python](https://img.shields.io/pypi/pyversions/strot-ai)](https://pypi.org/project/strot-ai/)
[![License](https://img.shields.io/pypi/l/strot-ai)](LICENSE)

Build tools, agents, pipelines, and dashboards for your [STROT](https://strot.ai) instance — in Python.

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

## SDK Reference

### Tools (`@function`)

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

### Agents (`@agent`)

```python
from strot_ai import agent

@agent(
    name='sales_analyst',
    description='Analyzes sales data and provides insights',
    tools=['calculate_roi', 'top_n'],
    model='gpt-4o',
    temperature=0.1,
)
class SalesAnalyst:
    system_prompt = """You are a sales analyst.
    Analyze data and provide actionable recommendations."""
```

### Cortex Pipelines (`@cortex`)

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

### Pages / Dashboards (`@page`)

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

### LLM

All LLM calls go through your STROT instance — no API keys needed in your code.

```python
from strot_ai import llm

result = llm.complete("Summarize this: " + text)
result = llm.chat([{"role": "user", "content": "What is 2+2?"}])
category = llm.classify("Great product!", ["positive", "negative", "neutral"])
data = llm.extract("John is 30 years old", {"name": "string", "age": "number"})
```

### Data Access

```python
from strot_ai import strot, query, query_one

rows = strot.queries['monthly_sales'].execute()
rows = query("SELECT * FROM users", data_source_id=1)
row = query_one("SELECT * FROM users WHERE id = 1", data_source_id=1)
```

### Destinations

```python
from strot_ai import email, slack, webhook

email.send(to="team@example.com", subject="Report Ready", body="Done.")
slack.send(channel="#alerts", message="New alert!")
webhook.post(url="https://api.example.com/hook", data={"event": "deploy"})
```

## CLI Reference

```bash
strot login                              # Authenticate
strot login --token sk_live_abc123       # Direct API key
strot whoami                             # Show current user/org
strot logout                             # Clear credentials

strot init tool my-calculator            # Scaffold tool
strot init agent my-analyst              # Scaffold agent
strot init cortex my-pipeline            # Scaffold pipeline
strot init page my-dashboard             # Scaffold dashboard

strot test                               # Validate locally
strot deploy                             # Deploy to STROT
strot deploy --dry-run                   # Validate without deploying

strot resources                          # List all resources
strot resources queries                  # List saved queries
strot resources datasources              # List data sources
```

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

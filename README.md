# STROT SDK

Build tools, agents, pipelines, and dashboards for your [STROT](https://strot.ai) instance — in Python.

## Installation

```bash
pip install strot-sdk

# With CLI (login, init, deploy commands)
pip install strot-sdk[cli]

# With pandas support (query_df)
pip install strot-sdk[pandas]

# Everything
pip install strot-sdk[cli,pandas]
```

## Quick Start

```bash
# 1. Authenticate
strot login

# 2. Scaffold a project
strot init tool my-calculator

# 3. Edit main.py (use Claude Code, Cursor, or any editor)
cd my-calculator

# 4. Test locally
strot test

# 5. Deploy to your STROT instance
strot deploy
```

## SDK Reference

### Tools (`@function`)

```python
from strot_sdk import function, llm

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
from strot_sdk import agent

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

Build data pipelines that compile to JSON DSL and deploy to your STROT instance.

```python
from strot_sdk import cortex
from strot_sdk.cortex import Flow

@cortex(name='daily_etl', description='Daily ETL pipeline')
class DailyETL:
    def build(self, flow: Flow):
        # Load data from a saved query
        data = flow.data_connector('load_sales', query_id=42)

        # Transform with LLM
        cleaned = flow.transform(data, prompt='Clean and normalize the data')

        # Route based on content
        router = flow.router(cleaned, routes=[
            {'name': 'high_value', 'description': 'Orders over $1000'},
            {'name': 'standard', 'description': 'Regular orders'},
        ], prompt='Classify by order value')

        # Publish results
        flow.publish(router, name='daily_report', destination='slack', channel='#data')
```

**Available Flow methods:**

| Method | Description |
|--------|-------------|
| `flow.data_connector(id, query_id=...)` | Load data from a saved query |
| `flow.transform(step, prompt=...)` | LLM-powered data transformation |
| `flow.arena(step, tool=..., parameters=...)` | Run an Arena tool |
| `flow.router(step, routes=[], prompt=...)` | Conditional routing |
| `flow.gate(step, condition=..., approval_required=...)` | Quality gate or approval |
| `flow.publish(step, name=..., destination=...)` | Output/publish results |
| `flow.action(step, action_type=..., target=...)` | Notifications/triggers |
| `flow.ai_feeds(step, prompt=..., insight_count=...)` | Generate AI insights |
| `flow.connect(source, target)` | Manual edge connection |

### Pages / Dashboards (`@page`)

Build dashboards that compile to JSON layout and deploy to your STROT instance.

```python
from strot_sdk import page
from strot_sdk.pages import Dashboard, Row, KPI, Chart, Table

@page(name='sales_dashboard', description='Sales overview', type='dashboard')
class SalesDashboard:
    def layout(self):
        return Dashboard(
            Row(
                KPI(query_id=1, label='Revenue', format='currency'),
                KPI(query_id=2, label='Orders'),
                KPI(query_id=3, label='Customers'),
                KPI(query_id=4, label='Avg Order', format='currency'),
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

**Block types:** `KPI`, `Chart`, `Table`, `Text`, `StatGrid`, `ProgressList`

**Chart types:** `line`, `bar`, `area`, `donut`, `scatter`, `stacked_bar`, `funnel`

**Grid:** 12-column layout. Set `span` on any block (default varies by type).

### LLM

All LLM calls go through your STROT instance — no API keys needed in your code.

```python
from strot_sdk import llm

# Simple completion
result = llm.complete("Summarize this: " + text)
result = llm("Shorthand syntax works too")

# Chat
result = llm.chat([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is 2+2?"},
])

# Classify
category = llm.classify("Great product!", ["positive", "negative", "neutral"])

# Extract structured data
data = llm.extract("John is 30 years old", {"name": "string", "age": "number"})

# Transform data
result = llm.transform(data, "Convert to French", output_format="json")
```

### Data Access

```python
from strot_sdk import strot, query, query_one, query_df

# Via registry (saved queries by name)
rows = strot.queries['monthly_sales'].execute()

# Via data source
rows = strot.dataSources['production'].query("SELECT * FROM users LIMIT 10")

# Direct SQL
rows = query("SELECT * FROM users", data_source_id=1)
row = query_one("SELECT * FROM users WHERE id = 1", data_source_id=1)

# Pandas DataFrame (requires strot-sdk[pandas])
df = query_df("SELECT * FROM orders", data_source_id=1)
```

### Destinations

```python
from strot_sdk import email, slack, webhook

email.send(to="team@example.com", subject="Report Ready", body="The daily report is ready.")
slack.send(channel="#alerts", message="New alert!")
webhook.post(url="https://api.example.com/hook", data={"event": "deploy"})
```

## CLI Reference

### Authentication

```bash
strot login                              # Interactive (opens browser)
strot login --token sk_live_abc123       # Direct API key
strot login -i https://app.strot.ai -o <org-uuid>
strot whoami                             # Show current user/org
strot logout                             # Clear credentials
strot logout --all                       # Clear all profiles
```

### Project Scaffolding

```bash
strot init tool my-calculator            # Python tool
strot init agent my-analyst              # Python agent
strot init cortex my-pipeline            # Cortex pipeline
strot init page my-dashboard             # Page/dashboard
strot init tool my-tool -d "Description" -c finance
```

### Resources

```bash
strot resources                          # List all resources
strot resources queries                  # List saved queries
strot resources datasources              # List data sources
strot resources tools                    # List deployed tools
```

### Testing & Deployment

```bash
strot test                               # Run/compile locally
strot test -p input_text="Hello"         # Run with parameters
strot deploy                             # Deploy to STROT instance
strot deploy --dry-run                   # Validate without deploying
```

## Configuration

Credentials are stored in `~/.strot/credentials` (YAML, 0600 permissions):

```yaml
version: 1
current_profile: default
profiles:
  default:
    url: https://app.strot.ai
    api_key: sk_live_abc123
    org: 98bf9a0a-c9cd-42a8-9ea4-4f7fee9a4535
    user_email: dev@example.com
```

**Priority chain** (highest to lowest):
1. Constructor arguments (`StrotClient(url=..., api_key=...)`)
2. Environment variables (`STROT_URL`, `STROT_API_KEY`)
3. Credentials file (`~/.strot/credentials`)

**Multiple profiles:**

```bash
strot login --profile staging -i https://staging.strot.ai
strot login --profile production -i https://app.strot.ai
```

## Development

```bash
git clone https://github.com/strot-ai/strot-sdk.git
cd strot-sdk
poetry install --with dev,cli

# Run tests
poetry run pytest -v

# Run with coverage
poetry run pytest --cov=strot_sdk
```

## License

MIT

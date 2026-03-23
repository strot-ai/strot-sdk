# STROT SDK — Developer Guide

Complete reference for building and deploying tools, agents, skills, pipelines, and dashboards on the STROT platform.

## Table of Contents

- [Installation & Setup](#installation--setup)
- [Authentication](#authentication)
- [Project Workflow](#project-workflow)
- [Tools (`@function`)](#tools-function)
- [Agents (`@agent`)](#agents-agent)
- [Skills (`@skill`)](#skills-skill)
- [Cortex Pipelines (`@cortex`)](#cortex-pipelines-cortex)
- [Pages & Dashboards (`@page`)](#pages--dashboards-page)
- [LLM Module](#llm-module)
- [Data Access](#data-access)
- [Destinations](#destinations)
- [Resource Registry](#resource-registry)
- [Configuration](#configuration)
- [CLI Reference](#cli-reference)
- [Project File (`strot.yaml`)](#project-file-strotyaml)

---

## Installation & Setup

```bash
pip install strot-ai
```

Optional dependencies:

```bash
pip install strot-ai[pandas]    # For DataFrame support
```

Verify installation:

```bash
strot --version
```

---

## Authentication

### Interactive Login

```bash
strot login
```

You'll be prompted for your STROT instance URL and API key. Credentials are saved to `~/.strot/credentials` with restricted file permissions.

### Direct Token Login

```bash
strot login --token sk_live_abc123 --url https://app.strot.ai
```

### Environment Variables

```bash
export STROT_URL=https://app.strot.ai
export STROT_API_KEY=sk_live_abc123
```

### Multiple Profiles

```bash
strot login --profile staging --url https://staging.strot.ai
strot login --profile production --url https://app.strot.ai
```

Switch profiles:

```bash
export STROT_PROFILE=staging
```

### Check Current Session

```bash
strot whoami
```

### Priority Order

Credentials are resolved in this order:
1. Constructor arguments (programmatic use)
2. Environment variables (`STROT_URL`, `STROT_API_KEY`)
3. Credentials file (`~/.strot/credentials`)

---

## Project Workflow

Every STROT project follows the same lifecycle:

### 1. Scaffold

```bash
strot init <type> <name>
```

This creates a directory with:
- `main.py` — Your code with the appropriate decorator
- `strot.yaml` — Project configuration
- `CLAUDE.md` — SDK reference for AI-assisted development

### 2. Develop

Edit `main.py` using any editor or AI coding tool. The `CLAUDE.md` file provides context for AI assistants like Claude Code or Cursor.

### 3. Test

```bash
strot test              # Validate the project
strot test --mock       # Validate with mocked resources
```

### 4. Deploy

```bash
strot deploy            # Deploy to your STROT instance
strot deploy --dry-run  # Validate without deploying
```

### 5. Iterate

Edit, test, and redeploy. The CLI handles create-vs-update automatically — if a resource with the same name exists, it gets updated.

---

## Tools (`@function`)

Tools are reusable functions that AI agents can call. They accept typed parameters and return results.

### Basic Tool

```python
from strot_ai import function

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

### Tool with LLM

```python
from strot_ai import function, llm

@function(
    name='summarize_feedback',
    description='Summarize customer feedback',
    category='analytics',
    parameters=[
        {'name': 'feedback_text', 'type': 'string', 'description': 'Raw feedback text'},
    ],
    returns={'type': 'string', 'description': 'Summary'}
)
class SummarizeFeedback:
    def run(self, feedback_text: str) -> str:
        return llm.complete(
            f"Summarize this customer feedback in 2 sentences:\n\n{feedback_text}",
            system_prompt="You are a customer success analyst."
        )
```

### Tool with Data Access

```python
from strot_ai import function, strot

@function(
    name='top_customers',
    description='Get top N customers by revenue',
    category='analytics',
    parameters=[
        {'name': 'n', 'type': 'number', 'description': 'Number of customers'},
    ],
    returns={'type': 'array', 'description': 'Top customers'}
)
class TopCustomers:
    def run(self, n: int = 10) -> list:
        rows = strot.dataSources['production'].query(
            f"SELECT name, revenue FROM customers ORDER BY revenue DESC LIMIT {int(n)}"
        )
        return rows
```

### Decorator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Unique function name |
| `description` | str | `''` | What the function does |
| `category` | str | `'custom'` | Category for organization |
| `parameters` | list | `[]` | Input parameter definitions |
| `returns` | dict | `{}` | Return type definition |
| `examples` | list | `[]` | Example usage strings |

### Parameter Types

Parameters use a simple type system:

```python
{'name': 'count', 'type': 'number', 'description': 'How many items'}
{'name': 'query', 'type': 'string', 'description': 'Search query'}
{'name': 'active', 'type': 'boolean', 'description': 'Active only'}
{'name': 'filters', 'type': 'object', 'description': 'Filter criteria'}
{'name': 'ids', 'type': 'array', 'description': 'List of IDs'}
```

### Rules

- Use `def run(self, ...)` — not `async def`
- Do not use `await`
- Do not import `openai`, `anthropic`, or `litellm` directly — use `llm` from `strot_ai`
- Parameters must be a list of dicts with `name`, `type`, `description`

---

## Agents (`@agent`)

Agents are AI entities with their own system prompt and access to tools. They can be routed to by the chatbot for specialized tasks.

### Basic Agent

```python
from strot_ai import agent

@agent(
    name='sales_analyst',
    description='Analyzes sales data and provides insights',
    tools=['calculate_roi', 'top_n', 'trend_analysis'],
    temperature=0.1,
)
class SalesAnalyst:
    system_prompt = """You are a sales analyst.

Your responsibilities:
1. Analyze sales data using available tools
2. Provide specific numbers and percentages
3. Give actionable recommendations
4. Ask clarifying questions when the request is ambiguous
"""
```

### Agent with Handoff

```python
from strot_ai import agent

@agent(
    name='triage_agent',
    description='Routes requests to the right specialist',
    tools=[],
    can_handoff_to=['sales_analyst', 'support_agent'],
)
class TriageAgent:
    system_prompt = """You are a triage agent. Route user requests:
    - Sales/revenue questions → sales_analyst
    - Support/bug reports → support_agent
    """
```

### Decorator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Unique agent name |
| `description` | str | `''` | What the agent does |
| `category` | str | `'custom'` | Category for organization |
| `tools` | list | `[]` | Arena tool names the agent can call |
| `temperature` | float | `0.1` | LLM temperature (0.0–1.0) |
| `max_iterations` | int | `10` | Max tool-call loops |
| `can_handoff_to` | list | `[]` | Agent names this agent can delegate to |
| `approval_required` | bool | `False` | Require human approval before actions |

### System Prompt

The system prompt can be defined as:
- A `system_prompt` class attribute (preferred)
- The class docstring (fallback)

```python
# Option 1: Class attribute
class MyAgent:
    system_prompt = "You are a helpful agent."

# Option 2: Docstring
class MyAgent:
    """You are a helpful agent."""
```

### Rules

- The platform decides the LLM model — do not pass a `model` parameter
- Tools must be registered Arena tools (check with `strot resources tools`)
- Keep `temperature` low (0.1) for analytical tasks, higher (0.7+) for creative tasks

---

## Skills (`@skill`)

Skills are multi-step AI workflows defined as markdown prompts with tool access. Unlike tools (which are code that runs) or agents (which are AI with a system prompt), skills are **structured workflows** — step-by-step instructions the AI follows, calling tools along the way.

### Basic Skill

```python
from strot_ai import skill

@skill(
    name='data_analyzer',
    description='Analyze query data and provide insights',
    tools=['query_info'],
    trigger='analyze.*data|analyze.*query',
    emoji='🔍',
    examples=[
        'Analyze the data from query 5',
        'What insights can you find in the sales data?',
    ],
)
class DataAnalyzer:
    """# Data Analyzer

## Workflow

Follow these steps IN ORDER. Do ONE step per turn, then STOP and wait.

### Step 1: Fetch Data
Call `query_info` with the query_id to get schema, columns, and sample data.
Present: column names, types, row count, and 2-3 sample rows.
Ask: "Does this data look right?"

### Step 2: Analyze
Identify patterns, outliers, and key statistics.
Present 3-5 insights with specific numbers.
Ask: "Would you like me to dig deeper into any of these?"

### Step 3: Summarize
Provide a concise summary with actionable recommendations.

## Rules
1. ALWAYS call query_info first — never guess column names.
2. Use ONLY column names from the query_info result.
3. Do ONE step per turn, then STOP and wait.
4. Be specific — use actual numbers, not vague statements.
"""
```

### Dashboard Builder Skill

```python
from strot_ai import skill

@skill(
    name='dashboard_builder',
    description='Build interactive dashboards from queries',
    tools=['query_info', 'create_app', 'update_app', 'deploy_app', 'get_app'],
    trigger='build.*dashboard|create.*dashboard|make.*dashboard',
    emoji='📊',
    examples=[
        'Build a dashboard from query 4',
        'Create a dashboard using the customer data',
    ],
)
class DashboardBuilder:
    """# Dashboard Builder

## Workflow

### Step 1: Analyze Data
Call `query_info` with the query_id to fetch schema and sample data.
Present column names, types, row count, and 2-3 sample rows.
Ask: "Does this data look right?"

### Step 2: Map Data
Plan how columns map to dashboard components (KPIs, charts, tables).
Keep the mapping description to 2-3 sentences.
Ask: "Does this mapping look good? Say 'build it' to proceed."

### Step 3: Build
Call `create_app` with a complete app_spec including template_id, query_id, and layout.
Say "Building your dashboard now..." before calling create_app.

### Step 4: Refine
Handle feedback — add/remove KPIs, change columns, swap chart types.
Call `update_app` with the FULL updated spec.

### Step 5: Deploy
When the user says "deploy" or "publish", call `deploy_app`.

## Rules
1. ALWAYS call query_info first.
2. Use ONLY column names from the query_info result.
3. Do ONE step per turn, then STOP and wait.
"""
```

### Using `prompt` Attribute

For longer prompts, you can use a `prompt` class attribute instead of the docstring:

```python
@skill(name='my_skill', description='...', tools=['query_info'])
class MySkill:
    prompt = """# My Skill

## Workflow
### Step 1: ...
### Step 2: ...
"""
```

The `prompt` attribute takes precedence over the docstring.

### Decorator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Unique skill name |
| `description` | str | `''` | What the skill does |
| `category` | str | `'custom'` | Category for organization |
| `tools` | list | `[]` | Arena tool names the skill can use |
| `trigger` | str | `''` | Regex pattern to auto-route user messages |
| `emoji` | str | `''` | Displayed in chat UI |
| `examples` | list | `[]` | Example prompts shown as suggestions |
| `icon` | str | `''` | Tabler icon name (e.g., `'layout-dashboard'`) |

### How Skills Work

1. User sends a message in chat (e.g., "Build a dashboard from query 4")
2. The `trigger` regex matches → skill is activated
3. The AI receives the skill's markdown prompt as instructions
4. The AI follows the workflow steps, calling `tools` as needed
5. Each step pauses for user input before proceeding

### Writing Good Skill Prompts

1. **Structure as steps** — Use `### Step N:` headers for each phase
2. **One step per turn** — Always tell the AI to STOP and wait after each step
3. **Use real tool names** — Reference tools by their exact registered name
4. **Include rules** — Add constraints at the end (e.g., "never guess columns")
5. **Show expected formats** — Include sample tool call parameters or output shapes
6. **Keep mappings short** — 2-3 sentences, not markdown tables

### Available System Tools

These tools are available to all skills by default:

| Tool | Description |
|------|-------------|
| `query_info` | Get query metadata, schema, column types, and sample data |
| `create_app` | Create a new app/dashboard |
| `update_app` | Update an existing app |
| `deploy_app` | Deploy an app to production |
| `get_app` | Get app details and current state |

Run `strot resources tools` to see all available tools in your instance.

---

## Cortex Pipelines (`@cortex`)

Cortex pipelines are data processing workflows that compile to JSON DSL. They chain together data connectors, LLM transforms, Arena tools, routers, gates, and publish steps.

### Basic Pipeline

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

### Pipeline with Routing

```python
@cortex(name='order_processor', description='Process and classify orders')
class OrderProcessor:
    def build(self, flow: Flow):
        orders = flow.data_connector('load_orders', query_id=10)

        classified = flow.transform(orders, prompt='Classify each order as high/low value')

        router = flow.router(classified, routes=[
            {'name': 'high_value', 'description': 'Orders over $1000'},
            {'name': 'low_value', 'description': 'Orders under $1000'},
        ], prompt='Route by order value')

        # High-value path
        high = flow.transform(classified, step_id='enrich_high',
                              prompt='Add risk scoring for high-value orders')
        gate = flow.gate(high, approval_required=True, approvers=['manager'])
        flow.publish(gate, name='high_value_orders', destination='email',
                     format='csv')

        # Low-value path
        low = flow.transform(classified, step_id='process_low',
                             prompt='Summarize low-value orders')
        flow.publish(low, name='low_value_summary', destination='slack',
                     channel='#orders')

        # Connect router to paths
        flow.route(router, high, condition='high_value')
        flow.route(router, low, condition='low_value')
```

### Pipeline with Arena Tools

```python
@cortex(name='analytics_pipeline', description='Run analytics on sales data')
class AnalyticsPipeline:
    def build(self, flow: Flow):
        data = flow.data_connector('load_data', query_id=5)

        # Use Arena tools
        top = flow.arena(data, tool='top_n', parameters={'n': 10, 'field': 'revenue'})
        trends = flow.arena(data, tool='trend_analysis',
                            parameters={'date_field': 'date', 'value_field': 'revenue'})

        # Generate insights
        insights = flow.ai_feeds(data, prompt='Generate key business insights',
                                 insight_count=5)

        flow.publish(top, name='top_performers')
        flow.publish(insights, name='weekly_insights', destination='slack',
                     channel='#analytics')
```

### Flow Methods

#### Data Input

```python
data = flow.data_connector('step_name', query_id=42)
data = flow.data_connector('step_name', query_name='monthly_sales')
```

#### LLM Transform

```python
result = flow.transform(prev_step, prompt='Your instruction')
result = flow.transform(prev_step, prompt='Merge datasets', operation='merge')
result = flow.llm_transform(prev_step, prompt='Same as transform')
```

Operations: `transform`, `merge`, `lookup`, `append`, `exclude`

#### Arena Tool

```python
result = flow.arena(prev_step, tool='top_n', parameters={'n': 10, 'field': 'revenue'})
```

#### Router (Conditional Branching)

```python
router = flow.router(prev_step, routes=[
    {'name': 'high', 'description': 'High value'},
    {'name': 'low', 'description': 'Low value'},
], prompt='Classify by value')

flow.route(router, high_handler, condition='high')
flow.route(router, low_handler, condition='low')
```

#### Gate (Approval / Quality Check)

```python
gate = flow.gate(prev_step, condition='quality_score > 0.95')
gate = flow.gate(prev_step, approval_required=True, approvers=['admin'])
```

#### Publish

```python
flow.publish(prev_step, name='report', destination='slack', channel='#data')
flow.publish(prev_step, name='export', destination='email', format='csv')
```

#### Action (Notifications)

```python
flow.action(prev_step, action_type='send_slack', target='#alerts')
flow.action(prev_step, action_type='send_email', target='team@example.com')
```

#### AI Feeds (Insights)

```python
flow.ai_feeds(prev_step, prompt='Generate key insights', insight_count=5)
```

#### Manual Connect

```python
flow.connect(step_a, step_b)
flow.connect(step_a, step_b, condition='approved')
```

### Decorator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Pipeline name |
| `description` | str | `''` | What the pipeline does |
| `category` | str | `'custom'` | Category for organization |
| `inputs` | list | `[]` | Input definitions |
| `outputs` | list | `[]` | Output definitions |

### Rules

- Every step after `data_connector` must receive a previous step as the first argument
- Use `def build(self, flow: Flow)` — not async
- Step IDs must be unique within a pipeline
- Run `strot resources queries` to find query IDs for `data_connector`

---

## Pages & Dashboards (`@page`)

Pages compile to layout JSON that STROT renders as interactive dashboards.

### Basic Dashboard

```python
from strot_ai import page
from strot_ai.pages import Dashboard, Row, KPI, Chart, Table

@page(name='sales_dashboard', description='Sales overview', type='dashboard')
class SalesDashboard:
    def layout(self):
        return Dashboard(
            Row(
                KPI(query_id=1, label='Revenue', value_field='total', format='currency'),
                KPI(query_id=2, label='Orders', value_field='count'),
                KPI(query_id=3, label='Customers', value_field='total'),
                KPI(query_id=4, label='Avg Order', value_field='average', format='currency'),
            ),
            Row(
                Chart(query_id=5, type='line', title='Revenue Trend',
                      x_field='date', y_field='revenue', span=8),
                Chart(query_id=6, type='donut', title='By Region', span=4),
            ),
            Row(
                Table(query_id=7, title='Recent Orders', sortable=True, paginated=True),
            ),
        )
```

### Components

#### KPI Card (default span: 3)

```python
# Simple KPI
KPI(query_id=1, label='Revenue', value_field='total', format='currency')

# KPI with change indicator
KPI(query_id=2, label='Growth', value_field='value', change_field='change')

# KPI with sparkline
KPI(query_id=3, label='Trend', value_field='value', trend_field='sparkline')

# KPI with progress bar
KPI(query_id=4, label='Goal', value_field='current', target_field='target')
```

Formats: `'number'`, `'currency'`, `'percent'`

#### Chart (default span: 6)

```python
Chart(query_id=1, type='line', title='Trend', x_field='date', y_field='value')
Chart(query_id=2, type='bar', title='By Category')
Chart(query_id=3, type='area', title='Volume Over Time')
Chart(query_id=4, type='donut', title='Distribution')
Chart(query_id=5, type='scatter', title='Correlation')
Chart(query_id=6, type='stacked_bar', title='Breakdown')
Chart(query_id=7, type='stacked_area', title='Composition')
```

Chart types: `line`, `bar`, `area`, `donut`, `pie`, `scatter`, `stacked_bar`, `stacked_area`, `funnel`

#### Table (default span: 12)

```python
# Basic table
Table(query_id=1, title='Orders')

# Table with specific columns
Table(query_id=2, title='Users', columns=['name', 'email', 'role'])

# Table with status badges
Table(query_id=3, title='Tickets', status_field='status')

# Table with pagination
Table(query_id=4, title='Logs', paginated=True, page_size=50,
      sortable=True, filterable=True)
```

#### Text (default span: 12)

```python
# Static text
Text(content='This dashboard shows Q4 sales performance.')

# AI-generated summary from query data
Text(query_id=1, title='AI Summary')
```

#### Other Components

```python
# Stat grid
StatGrid(stats=[
    {'label': 'Active Users', 'value': '1,234'},
    {'label': 'Response Time', 'value': '45ms'},
])

# Progress list
ProgressList(query_id=1, name_field='rep', value_field='actual',
             target_field='quota', title='Sales Quotas')
```

### Grid System

All components use a 12-column grid. Set `span` on any component:

```python
Row(
    Chart(query_id=1, type='line', span=8),   # 2/3 width
    Chart(query_id=2, type='donut', span=4),  # 1/3 width
)
# Spans should sum to 12 per row
```

### Decorator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Page name |
| `description` | str | `''` | What the page shows |
| `type` | str | `'dashboard'` | Page type |
| `layout` | str | `'default'` | Layout preset |
| `public` | bool | `False` | Publicly accessible |
| `embed_allowed` | bool | `True` | Allow embedding |

### Rules

- `layout()` must return a `Dashboard` instance
- Use `query_id` to bind components to saved queries
- Run `strot resources queries` to find available query IDs
- Spans in a Row should sum to 12

---

## LLM Module

All LLM calls go through your STROT instance — no API keys needed in your code.

### Completions

```python
from strot_ai import llm

# Basic completion
result = llm.complete("Summarize this text: " + text)

# With system prompt
result = llm.complete(
    "What are the key trends?",
    system_prompt="You are a financial analyst."
)

# Shorthand
result = llm("What is 2+2?")
```

### Chat

```python
result = llm.chat([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What are the top 3 programming languages?"},
])
```

### Classification

```python
category = llm.classify(
    "This product is amazing! Best purchase ever.",
    ["positive", "negative", "neutral"]
)
# Returns: "positive"
```

### Extraction

```python
data = llm.extract(
    "John Smith is 30 years old and works at Acme Corp.",
    {"name": "string", "age": "number", "company": "string"}
)
# Returns: {"name": "John Smith", "age": 30, "company": "Acme Corp"}
```

### Data Transform

```python
result = llm.transform(
    [{"name": "John", "city": "NYC"}, {"name": "Jane", "city": "LA"}],
    "Convert city names to full state names",
    output_format="json"
)
```

### Aliases

These are all equivalent to `llm.complete()`:

```python
llm.generate("prompt")
llm.summarize("prompt")
llm.translate("prompt")
llm.ask("prompt")
```

---

## Data Access

### Using the Registry

```python
from strot_ai import strot

# Execute a saved query by name
rows = strot.queries['monthly_sales'].execute()

# Execute a saved query by ID
rows = strot.queries[42].execute()

# Execute with parameters
rows = strot.queries['filtered_sales'].execute(params={'region': 'US'})

# Query a data source directly
rows = strot.dataSources['production'].query("SELECT * FROM users LIMIT 10")

# Get a DataFrame
df = strot.dataSources['production'].query_df("SELECT * FROM orders")
```

### Direct Query Functions

```python
from strot_ai import query, query_one, query_df

# Execute SQL, get list of dicts
rows = query("SELECT * FROM users", data_source_id=1)

# Get single row
user = query_one("SELECT * FROM users WHERE id = 1", data_source_id=1)

# Get DataFrame (requires pandas)
df = query_df("SELECT * FROM orders WHERE date > '2024-01-01'", data_source_id=1)
```

### Execute Saved Queries

```python
from strot_ai import execute_saved_query

rows = execute_saved_query(query_id=42)
rows = execute_saved_query(query_id=42, params={'date': '2024-01-01'})
```

### Browse Resources

```python
# List all queries
for q in strot.queries:
    print(f"{q.id}: {q.name} (ds={q.data_source_id})")

# List all data sources
for ds in strot.dataSources:
    print(f"{ds.id}: {ds.name} ({ds.type})")

# List all tools
for tool in strot.tools:
    print(f"{tool.id}: {tool.name} ({tool.function_type})")

# Check if a resource exists
if 'monthly_sales' in strot.queries:
    rows = strot.queries['monthly_sales'].execute()

# Reload from API
strot.reload()
```

---

## Destinations

Send notifications and data to external services.

### Email

```python
from strot_ai import email

email.send(
    to="team@example.com",
    subject="Weekly Report",
    body="The weekly report is ready.",
    html="<h1>Report</h1><p>See attached.</p>",
    cc="manager@example.com",
    bcc="archive@example.com",
)
```

### Slack

```python
from strot_ai import slack

slack.send(
    channel="#analytics",
    message="Daily sales report is ready!",
)

# With rich blocks
slack.send(
    channel="#alerts",
    message="New alert",
    blocks=[
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Alert:* Revenue dropped 15%"}},
    ],
)
```

### Webhook

```python
from strot_ai import webhook

# POST
webhook.post(
    url="https://api.example.com/hook",
    data={"event": "report_ready", "report_id": 42},
    headers={"X-API-Key": "abc123"},
)

# GET
webhook.get(url="https://api.example.com/status")

# PUT
webhook.put(url="https://api.example.com/resource/1", data={"status": "complete"})
```

---

## Resource Registry

The `strot` registry provides lazy-loaded, typed access to platform resources.

```python
from strot_ai import strot
```

### Collections

| Collection | Access | Returns |
|------------|--------|---------|
| `strot.queries` | `strot.queries['name']` or `strot.queries[id]` | `QueryProxy` |
| `strot.tools` | `strot.tools['name']` or `strot.tools[id]` | `ToolProxy` |
| `strot.dataSources` | `strot.dataSources['name']` or `strot.dataSources[id]` | `DataSourceProxy` |

### QueryProxy

```python
q = strot.queries['monthly_sales']
q.id                # int
q.name              # str
q.description       # str
q.data_source_id    # int
q.execute()         # List[Dict]
q.execute(params={})
```

### ToolProxy

```python
tool = strot.tools['calculate_roi']
tool.id              # int
tool.name            # str
tool.description     # str
tool.function_type   # str
tool.run(cost=1000, revenue=1500)  # Any
```

### DataSourceProxy

```python
ds = strot.dataSources['production']
ds.id        # int
ds.name      # str
ds.type      # str (e.g., 'pg', 'mysql', 'bigquery')
ds.query("SELECT 1")     # List[Dict]
ds.query_df("SELECT 1")  # pandas DataFrame
```

---

## Configuration

### Credentials File

Located at `~/.strot/credentials`:

```yaml
version: 1
current_profile: default
profiles:
  default:
    url: https://app.strot.ai
    api_key: sk_live_abc123
    org: 98bf9a0a-c9cd-42a8-9ea4-4f7fee9a4535
    user_email: user@example.com
  staging:
    url: https://staging.strot.ai
    api_key: sk_test_xyz789
    org: staging-org-slug
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `STROT_URL` | STROT instance URL |
| `STROT_API_KEY` | API key |
| `STROT_PROFILE` | Active profile name |

### Programmatic Configuration

```python
from strot_ai import StrotClient, StrotConfig

# Direct client
client = StrotClient(
    url="https://app.strot.ai",
    api_key="sk_live_abc123",
    org="my-org-slug",
)

# Check config
config = StrotConfig()
print(config.is_configured)  # True/False
config.validate()             # Raises if not configured
```

---

## CLI Reference

### Authentication

```bash
strot login                          # Interactive login
strot login --token sk_live_abc123   # Direct API key
strot login --profile staging        # Named profile
strot whoami                         # Show current user/org
strot logout                         # Clear credentials
```

### Project Scaffolding

```bash
strot init tool my-calculator           # Create a tool project
strot init agent my-analyst             # Create an agent project
strot init skill my-workflow            # Create a skill project
strot init cortex my-pipeline           # Create a pipeline project
strot init page my-dashboard            # Create a dashboard project

# With options
strot init tool my-tool -d "Calculate metrics" -c finance
```

### Testing & Deployment

```bash
strot test                  # Validate project
strot test --mock           # Validate with mocked resources
strot deploy                # Deploy to STROT instance
strot deploy --dry-run      # Validate without deploying
```

### Resource Discovery

```bash
strot resources             # List all resources
strot resources queries     # List saved queries
strot resources datasources # List data sources
strot resources tools       # List Arena tools
```

---

## Project File (`strot.yaml`)

Every STROT project has a `strot.yaml` configuration file:

```yaml
name: my-tool
type: tool            # tool, agent, skill, cortex, or page
language: python
version: "1.0.0"
description: "What this project does"
category: custom
entry: main.py        # Entry point file
files:                # Additional files to include (optional)
  - utils.py
  - config.json
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Project name (must match decorator name) |
| `type` | yes | `tool`, `agent`, `skill`, `cortex`, or `page` |
| `language` | yes | `python` |
| `version` | no | Semantic version |
| `description` | no | Project description |
| `category` | no | Category for organization |
| `entry` | yes | Entry point file |
| `files` | no | Additional files to bundle |

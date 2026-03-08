"""strot init — Scaffold a new STROT project."""
import click
from pathlib import Path
from rich.console import Console

console = Console()

# Project templates
TEMPLATES = {
    "tool": {
        "language": "python",
        "files": {
            "main.py": '''\
from strot_sdk import function, llm, strot

@function(
    name='{name}',
    description='{description}',
    category='{category}',
    parameters=[
        {{'name': 'input_text', 'type': 'string', 'description': 'Input text to process'}}
    ],
    returns={{'type': 'string', 'description': 'Processed result'}}
)
class {class_name}:
    def run(self, input_text: str) -> str:
        """Process input and return result."""
        result = llm.complete(f"Process this: {{input_text}}")
        return result
''',
            "strot.yaml": '''\
name: {name}
type: tool
language: python
version: "1.0.0"
description: "{description}"
category: {category}
entry: main.py
''',
            "CLAUDE.md": '''\
# {name} — STROT Tool

## What this is
A STROT tool that can be deployed to your STROT instance and used by AI agents.

## SDK Reference

### Imports (ONLY use these)
```python
from strot_sdk import function, agent, llm, strot, query, email, slack, webhook
```

### @function decorator
```python
@function(
    name='my_tool',
    description='What it does',
    category='custom',
    parameters=[
        {{'name': 'param1', 'type': 'string', 'description': 'Description'}},
        {{'name': 'param2', 'type': 'number', 'description': 'Description'}}
    ],
    returns={{'type': 'string', 'description': 'What it returns'}}
)
class MyTool:
    def run(self, param1: str, param2: float) -> str:
        return "result"
```

### LLM (via STROT proxy — no API keys needed)
```python
result = llm.complete("Your prompt here")
result = llm.complete("Prompt", system_prompt="You are a helpful assistant")
result = llm.classify("text", ["positive", "negative", "neutral"])
result = llm.extract("John is 30", {{"name": "string", "age": "number"}})
result = llm.transform(data, "Convert to French", output_format="json")
```

### Data Access
```python
rows = strot.queries['monthly_sales'].execute()
rows = strot.dataSources['production'].query("SELECT * FROM users LIMIT 10")
rows = query("SELECT * FROM users", data_source_id=1)
```

### Destinations
```python
email.send(to="user@example.com", subject="Alert", body="Message")
slack.send(channel="#alerts", message="New alert!")
webhook.post(url="https://api.example.com/hook", data={{"key": "value"}})
```

## Rules
- Use `def run(self, ...)` — NOT `async def`
- Do NOT use `await`
- Do NOT import litellm, openai, or anthropic directly — use `llm` from strot_sdk
- Parameters must be a list of dicts with name, type, description
- Only use data from `strot.queries` and `strot.dataSources`

## Testing
```bash
strot test          # Run against real STROT instance
strot test --mock   # Run with mocked data
```

## Deploying
```bash
strot deploy        # Deploy to your STROT instance
```
''',
        },
    },
    "agent": {
        "language": "python",
        "files": {
            "main.py": '''\
from strot_sdk import agent, llm, strot

@agent(
    name='{name}',
    description='{description}',
    category='{category}',
    tools=[],
    model='gpt-4o-mini',
    temperature=0.1,
    max_iterations=10,
)
class {class_name}:
    system_prompt = """You are {name}, an AI agent.

Your role: {description}

When analyzing data:
1. Be specific with numbers and percentages
2. Provide actionable recommendations
3. Ask clarifying questions if needed
"""
''',
            "strot.yaml": '''\
name: {name}
type: agent
language: python
version: "1.0.0"
description: "{description}"
category: {category}
entry: main.py
''',
            "CLAUDE.md": '''\
# {name} — STROT Agent

## What this is
A STROT AI agent with its own system prompt and tools. Agents can be routed to
by the chatbot for specialized tasks.

## SDK Reference

### @agent decorator
```python
@agent(
    name='my_agent',
    description='What the agent does',
    category='analytics',
    tools=['tool_name1', 'tool_name2'],
    model='gpt-4o-mini',
    temperature=0.1,
    max_iterations=10,
    can_handoff_to=['other_agent'],
    approval_required=False,
)
class MyAgent:
    system_prompt = """You are a specialized agent..."""
```

### Available tools
Run `strot resources tools` to see available tools for the `tools` list.

## Rules
- The `system_prompt` class attribute defines the agent's behavior
- Tools must be registered Arena tools (check with `strot resources tools`)
- Use `can_handoff_to` to enable multi-agent collaboration

## Deploying
```bash
strot deploy
```
''',
        },
    },
    "cortex": {
        "language": "python",
        "files": {
            "main.py": '''\
from strot_sdk import cortex
from strot_sdk.cortex import Flow

@cortex(
    name='{name}',
    description='{description}',
)
class {class_name}:
    def build(self, flow: Flow):
        # 1. Load data from a saved query
        data = flow.data_connector('load_data', query_id=1)

        # 2. Transform with LLM
        cleaned = flow.transform(data, prompt='Clean and normalize the data')

        # 3. Publish results
        flow.publish(cleaned, name='output', destination='slack', channel='#data')
''',
            "strot.yaml": '''\
name: {name}
type: cortex
language: python
version: "1.0.0"
description: "{description}"
category: {category}
entry: main.py
''',
            "CLAUDE.md": '''\
# {name} — STROT Cortex Pipeline

## What this is
A STROT Cortex pipeline that processes data through a series of steps.
The pipeline compiles to JSON DSL and gets deployed to your STROT instance.

## SDK Reference

### @cortex decorator
```python
from strot_sdk import cortex
from strot_sdk.cortex import Flow

@cortex(name='my_pipeline', description='What it does')
class MyPipeline:
    def build(self, flow: Flow):
        data = flow.data_connector('load', query_id=42)
        cleaned = flow.transform(data, prompt='Clean the data')
        flow.publish(cleaned, name='report')
```

### Flow Methods

#### Data Input
```python
data = flow.data_connector('step_name', query_id=42)
data = flow.data_connector('step_name', query_name='monthly_sales')
```

#### Transform (LLM)
```python
result = flow.transform(prev_step, prompt='Instruction', model='gpt-4o')
result = flow.llm_transform(prev_step, prompt='Same as transform')
```

#### Arena Tool
```python
result = flow.arena(prev_step, tool='top_n', parameters={{'n': 10, 'field': 'revenue'}})
```

#### Router (Conditional Branching)
```python
router = flow.router(prev_step, routes=[
    {{'name': 'high', 'description': 'High value orders'}},
    {{'name': 'low', 'description': 'Low value orders'}},
], prompt='Classify by order value')
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

## Rules
- Every step after data_connector must receive a previous step as first argument
- Use `def build(self, flow: Flow)` — NOT async
- Step IDs must be unique within a pipeline
- Run `strot resources queries` to find query IDs for data_connector

## Testing
```bash
strot test          # Compile and validate the pipeline DSL
strot test --mock   # Same but with mocked resources
```

## Deploying
```bash
strot deploy        # Deploy to your STROT instance
strot deploy --dry-run  # Validate without deploying
```
''',
        },
    },
    "page": {
        "language": "python",
        "files": {
            "main.py": '''\
from strot_sdk import page
from strot_sdk.pages import Dashboard, Row, KPI, Chart, Table

@page(
    name='{name}',
    description='{description}',
    type='dashboard',
)
class {class_name}:
    def layout(self):
        return Dashboard(
            Row(
                KPI(query_id=1, label='Total Revenue', value_field='total', format='currency'),
                KPI(query_id=2, label='Orders', value_field='count'),
                KPI(query_id=3, label='Customers', value_field='total'),
                KPI(query_id=4, label='Avg Order', value_field='average', format='currency'),
            ),
            Row(
                Chart(query_id=5, type='line', title='Revenue Trend', x_field='date', y_field='revenue', span=8),
                Chart(query_id=6, type='donut', title='By Region', span=4),
            ),
            Row(
                Table(query_id=7, title='Recent Orders', sortable=True, paginated=True),
            ),
        )
''',
            "strot.yaml": '''\
name: {name}
type: page
language: python
version: "1.0.0"
description: "{description}"
category: {category}
entry: main.py
''',
            "CLAUDE.md": '''\
# {name} — STROT Page / Dashboard

## What this is
A STROT dashboard page that displays data using KPIs, charts, and tables.
The layout compiles to JSON and gets deployed to your STROT instance.

## SDK Reference

### @page decorator
```python
from strot_sdk import page
from strot_sdk.pages import Dashboard, Row, KPI, Chart, Table, Text

@page(name='my_dashboard', description='Sales overview', type='dashboard')
class MyDashboard:
    def layout(self):
        return Dashboard(
            Row(KPI(query_id=1, label='Revenue', format='currency')),
            Row(Chart(query_id=2, type='line', title='Trend')),
            Row(Table(query_id=3, title='Orders')),
        )
```

### Layout Components

#### Dashboard & Row
```python
Dashboard(*rows, title='Optional title')
Row(*blocks, height='auto')  # height can be 'auto' or CSS like '350px'
```

#### KPI Card (span default: 3)
```python
KPI(query_id=1, label='Revenue', value_field='total', format='currency')
KPI(query_id=2, label='Growth', value_field='value', change_field='change')
KPI(query_id=3, label='Trend', value_field='value', trend_field='sparkline')
KPI(query_id=4, label='Goal', value_field='current', target_field='target')
```
Formats: 'number', 'currency', 'percent'

#### Chart (span default: 6)
```python
Chart(query_id=1, type='line', title='Title', x_field='date', y_field='value')
Chart(query_id=2, type='bar', title='Title')
Chart(query_id=3, type='donut', title='Title')
Chart(query_id=4, type='area', title='Title')
Chart(query_id=5, type='scatter', title='Title')
Chart(query_id=6, type='stacked_bar', title='Title')
Chart(query_id=7, type='funnel', title='Title')
```

#### Table (span default: 12)
```python
Table(query_id=1, title='Orders', columns=['id', 'name', 'total'])
Table(query_id=2, title='Status', status_field='status', sortable=True, filterable=True)
Table(query_id=3, title='Large', paginated=True, page_size=50)
```

#### Text (span default: 12)
```python
Text(content='Static text or markdown')
Text(query_id=1, title='AI Summary')  # LLM-generated from query data
```

### Grid System
All blocks use a 12-column grid. Set `span` on any block:
```python
Chart(query_id=1, type='line', span=8)  # 2/3 width
Chart(query_id=2, type='donut', span=4)  # 1/3 width
```

## Rules
- `layout()` must return a `Dashboard` instance
- Use `query_id` to bind blocks to saved queries
- Run `strot resources queries` to find available query IDs
- Blocks in a Row should have spans that sum to 12

## Testing
```bash
strot test          # Compile and validate the layout
strot test --mock   # Same but with mocked resources
```

## Deploying
```bash
strot deploy        # Deploy to your STROT instance
strot deploy --dry-run  # Validate without deploying
```
''',
        },
    },
}


def _to_class_name(name: str) -> str:
    """Convert kebab-case or snake_case to PascalCase."""
    parts = name.replace("-", "_").split("_")
    return "".join(p.capitalize() for p in parts)


@click.command()
@click.argument("project_type", type=click.Choice(["tool", "agent", "cortex", "page"]))
@click.argument("name")
@click.option("--description", "-d", default="", help="Project description")
@click.option("--category", "-c", default="custom", help="Category")
def init(project_type, name, description, category):
    """Scaffold a new STROT project.

    PROJECT_TYPE: tool, agent, cortex, or page
    NAME: Project name (e.g., my-calculator)
    """
    template = TEMPLATES.get(project_type)
    if not template:
        console.print(f"[red]Unknown project type: {project_type}[/red]")
        raise SystemExit(1)

    project_dir = Path.cwd() / name
    if project_dir.exists():
        console.print(f"[red]Directory '{name}' already exists.[/red]")
        raise SystemExit(1)

    project_dir.mkdir(parents=True)

    class_name = _to_class_name(name)
    description = description or f"A STROT {project_type}"

    for filename, content in template["files"].items():
        filepath = project_dir / filename
        rendered = content.format(
            name=name,
            class_name=class_name,
            description=description,
            category=category,
        )
        filepath.write_text(rendered)

    console.print(f"[green]Created {project_type} project:[/green] {name}/")
    console.print()
    for filename in template["files"]:
        console.print(f"  {name}/{filename}")
    console.print()
    console.print(f"[dim]Next steps:[/dim]")
    console.print(f"  cd {name}")
    console.print(f"  # Edit main.py with your IDE (Claude Code, Cursor, etc.)")
    console.print(f"  strot test")
    console.print(f"  strot deploy")

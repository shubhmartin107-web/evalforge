# Integrations & Extensibility

## Provider Integrations

EvalForge supports multiple LLM providers through a common interface. Adding a new provider requires implementing just 3 methods.

### Adding a Custom Provider

```python
from evalforge.providers.base import ProviderBase

class MyCustomProvider(ProviderBase):
    name = "my-provider"
    default_model = "my-model"

    def chat(self, messages, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        # Call your LLM API
        response = my_api.chat(messages)
        return {
            "content": response.text,
            "tool_calls": response.tool_calls,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "cost_usd": response.cost,
        }

    def count_tokens(self, text, model=None):
        return my_tokenizer.count(text)
```

Then use it:

```python
ef = EvalForge(provider=MyCustomProvider())
```

## Agent Framework Integrations

### LangGraph

Wrap your LangGraph agent in an eval function:

```python
from langgraph.graph import StateGraph

def evaluate_langgraph_agent(instructions, criteria, record_step):
    record_step("thought", "Starting LangGraph agent...")
    
    graph = build_my_graph()
    result = graph.invoke({"input": instructions})
    
    record_step("output", content=result.get("output", ""))
    return result

ef = EvalForge()
runs = ef.run(evaluation, agent_function=evaluate_langgraph_agent)
```

### CrewAI

Evaluate CrewAI crews:

```python
from crewai import Crew, Agent, Task

def evaluate_crew(instructions, criteria, record_step):
    agent = Agent(...)
    task = Task(description=instructions, agent=agent)
    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()
    record_step("output", content=str(result))
    return str(result)
```

### Claude API / Anthropic SDK

```python
import anthropic

client = anthropic.Anthropic()

def evaluate_claude(instructions, criteria, record_step):
    record_step("thought", f"Processing: {instructions[:50]}...")
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[{"role": "user", "content": instructions}],
    )
    content = response.content[0].text
    record_step("output", content=content)
    return content
```

## Memory System Integration (Memora)

EvalForge can evaluate agents that use persistent memory:

```python
def agent_with_memory(instructions, criteria, record_step):
    memory = memora.MemoryClient()
    context = memory.retrieve(instructions)
    
    record_step("thought", f"Retrieved {len(context)} memory items")
    response = llm_call(instructions, context)
    memory.store(instructions, response)
    
    return response
```

This allows evaluating:
- Memory retrieval accuracy
- Context relevance over multiple turns
- Long-term consistency

## Observability Integration (FlowLens)

Export traces to FlowLens or OpenTelemetry:

```python
from evalforge import EvalForge

ef = EvalForge()
runs = ef.run(evaluation)

# Export as OpenTelemetry-compatible JSON
for run in runs:
    trace = ef.get_trace(run.id)
    # Forward to your observability pipeline
    export_to_flowlens(trace)
```

## Benchmark Extensibility

Add custom benchmarks by creating `TaskDefinition` objects:

```python
from evalforge.models import Evaluation, TaskDefinition, SuccessCriteria

custom_benchmark = Evaluation(
    name="my-custom-benchmark",
    description="Domain-specific tasks",
    tasks=[
        TaskDefinition(
            name="task-1",
            instructions="Your task instructions here...",
            success_criteria=[
                SuccessCriteria(type="contains", description="Requirement", expected="keyword"),
                SuccessCriteria(type="regex", description="Format check", expected=r"pattern"),
            ],
        ),
    ],
)

ef = EvalForge()
ef.register_evaluation(custom_benchmark)
```

## Custom Grading

Support for three grading modes:

1. **Deterministic** — Exact match, contains, regex checks (fast, cheap)
2. **LLM-as-Judge** — Another LLM grades the output (slower, more nuanced)
3. **Hybrid** — Combine both approaches

For LLM-as-Judge grading:

```python
from evalforge.models import Evaluation, GradingType

evaluation = Evaluation(
    name="judge-eval",
    grading_type=GradingType.llm_as_judge,
    judge_config={"model": "deepseek-chat", "prompt": "Grade this output..."},
)
```

import gradio as gr

from ...core.engine import EvaluationEngine
from ...models.evaluation import Evaluation, SuccessCriteria, TaskDefinition
from ...models.provider import AgentConfig, ProviderConfig, ProviderType
from ...providers.factory import create_provider
from ...storage.db import init_db
from ...storage.repository import EvaluationRepository, RunRepository


def create_benchmarks_tab(tab: gr.Tab):
    init_db()
    EvaluationRepository()
    RunRepository()

    with gr.Tabs():
        with gr.Tab("Available Benchmarks"):
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
            eval_list_md = gr.Markdown("Loading...")
            with gr.Row():
                gr.Textbox(label="Benchmark Name", placeholder="e.g., Simple Coding Test")
                gr.Textbox(label="Description", placeholder="Description of the benchmark")
            refresh_btn.click(refresh_benchmarks, None, eval_list_md)

        with gr.Tab("Create Benchmark"):
            name = gr.Textbox(label="Name", placeholder="My Benchmark")
            desc = gr.Textbox(label="Description", placeholder="Description", lines=2)
            task_instructions = gr.Textbox(
                label="Task Instructions", placeholder="Instructions for the agent...", lines=4
            )
            criteria_text = gr.Textbox(
                label="Success Criteria (one per line, format: type|description|expected)",
                placeholder="contains|Must include answer|the result is\nregex|Must have valid format|\\d+\\.\\d+",
                lines=3,
            )
            create_btn = gr.Button("Create Benchmark", variant="primary")
            create_status = gr.Markdown("")
            create_btn.click(create_benchmark, [name, desc, task_instructions, criteria_text], [create_status])

        with gr.Tab("Run Benchmark"):
            gr.Markdown("### Run an Evaluation")
            with gr.Row():
                sel_eval = gr.Dropdown(label="Select Benchmark", interactive=True)
                provider_choice = gr.Dropdown(
                    choices=["deepseek", "gemini", "groq", "ollama", "anthropic"], value="deepseek", label="Provider"
                )
                model_name = gr.Textbox(value="deepseek-chat", label="Model")
            run_btn = gr.Button("▶ Run Evaluation", variant="primary", size="lg")
            run_status = gr.Markdown("")
            run_results = gr.Markdown("")
            run_btn.click(run_benchmark, [sel_eval, provider_choice, model_name], [run_status, run_results])

    tab.select(lambda: refresh_benchmarks(), None, eval_list_md)


def refresh_benchmarks():
    init_db()
    eval_repo = EvaluationRepository()
    eval_list = eval_repo.find_all()
    md = "### Registered Benchmarks\n\n"
    if eval_list:
        md += "| Name | Tasks | Grading | Created |\n|---|---|---|---|\n"
        for e in eval_list:
            md += f"| **{e.name}** | {len(e.tasks)} | {e.grading_type.value} | {e.created_at[:10]} |\n"
    else:
        md += "_No benchmarks registered. Create one below._\n"
    return md


def create_benchmark(name, desc, instructions, criteria):
    init_db()
    eval_repo = EvaluationRepository()
    if not name or not instructions:
        return "_Name and instructions required_"
    criteria_list = []
    for line in criteria.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            criteria_list.append(
                SuccessCriteria(type=parts[0].strip(), description=parts[1].strip(), expected=parts[2].strip())
            )
        elif len(parts) == 2:
            criteria_list.append(SuccessCriteria(type=parts[0].strip(), description=parts[1].strip()))
        else:
            criteria_list.append(
                SuccessCriteria(type="contains", description=parts[0].strip(), expected=parts[0].strip())
            )
    task = TaskDefinition(name=name, description=desc, instructions=instructions, success_criteria=criteria_list)
    eval_obj = Evaluation(name=name, description=desc, tasks=[task])
    eval_repo.save(eval_obj)
    return f"✅ Benchmark **{name}** created with ID `{eval_obj.id}`"


_eval_choices: dict[str, str] = {}


def run_benchmark(eval_name, provider_type, model):
    global _eval_choices
    init_db()
    eval_repo = EvaluationRepository()
    if not eval_name or eval_name == "_No benchmarks_":
        return "_Select a benchmark_", ""
    if not _eval_choices:
        evals = eval_repo.find_all()
        _eval_choices = {e.name: e.id for e in evals}
    eval_id = _eval_choices.get(eval_name)
    if not eval_id:
        return "_Benchmark not found_", ""
    eval_obj = eval_repo.find_by_id(eval_id)
    if not eval_obj:
        return "_Benchmark not found_", ""

    try:
        provider = create_provider(provider_type)
    except Exception:
        return f"_Could not create provider: {provider_type}_", ""

    agent_config = AgentConfig(provider=ProviderConfig(provider=ProviderType(provider_type), model=model))
    engine = EvaluationEngine(provider=provider)
    return _run_with_status(engine, eval_obj, agent_config)


def _run_with_status(engine, eval_obj, agent_config):
    try:
        runs = engine.run(eval_obj, agent_config=agent_config)
        results_md = "### Results\n\n"
        results_md += "| Task | Status | Score | Cost | Steps |\n|---|---|---|---|---|\n"
        for run in runs:
            icon = "✅" if run.metrics.success else "❌"
            results_md += f"| {run.task_id[:8]} | {icon} | {run.metrics.success_score:.2f} | ${run.metrics.total_cost_usd:.6f} | {run.metrics.step_count} |\n"
        results_md += f"\n**Total cost**: ${sum(r.metrics.total_cost_usd for r in runs):.6f}\n"
        results_md += f"**Success rate**: {sum(1 for r in runs if r.metrics.success)}/{len(runs)}"
        return "✅ Evaluation complete!", results_md
    except Exception as e:
        return f"❌ Error: {e}", ""

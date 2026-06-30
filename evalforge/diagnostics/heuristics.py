from ..models.diagnostics import Diagnostic, DiagnosticCategory, Severity
from ..models.trace import Step, StepType


def detect_looping(steps: list[Step], threshold: int = 5) -> list[Diagnostic]:
    diagnostics = []
    tool_names = [s.tool_name for s in steps if s.step_type == StepType.tool_call and s.tool_name]
    if len(tool_names) >= threshold:
        recent = tool_names[-threshold:]
        if len(set(recent)) == 1:
            diagnostics.append(
                Diagnostic(
                    run_id=steps[0].run_id if steps else "",
                    severity=Severity.warning,
                    category=DiagnosticCategory.looping,
                    title="Potential tool call loop detected",
                    description=f"Agent called '{recent[0]}' {threshold} consecutive times without progress",
                    step_index=len(steps) - 1,
                    recommendation="Consider adding a termination condition or varying tool selection strategy",
                )
            )
    return diagnostics


def detect_context_window_exhaustion(steps: list[Step], max_context: int = 32000) -> list[Diagnostic]:
    diagnostics = []
    cumulative = 0
    for i, step in enumerate(steps):
        cumulative += step.token_count
        if cumulative > max_context * 0.85:
            diagnostics.append(
                Diagnostic(
                    run_id=step.run_id,
                    severity=Severity.warning if cumulative < max_context else Severity.critical,
                    category=DiagnosticCategory.context_window,
                    title="Context window near exhaustion",
                    description=f"Cumulative tokens ({cumulative}) approaching limit ({max_context})",
                    step_index=i,
                    recommendation="Use shorter messages, implement sliding window, or increase context limit",
                )
            )
            break
    return diagnostics


def detect_cost_overrun(steps: list[Step], max_cost: float = 0.10) -> list[Diagnostic]:
    diagnostics = []
    total_cost = sum(s.cost_usd for s in steps)
    if total_cost > max_cost:
        diagnostics.append(
            Diagnostic(
                run_id=steps[0].run_id if steps else "",
                severity=Severity.warning,
                category=DiagnosticCategory.cost_overrun,
                title="Cost overrun detected",
                description=f"Total cost ${total_cost:.4f} exceeds threshold ${max_cost:.4f}",
                step_index=len(steps) - 1,
                recommendation="Use a cheaper model, reduce token usage, or set cost budgets",
            )
        )
    return diagnostics


def detect_tool_selection_issues(steps: list[Step]) -> list[Diagnostic]:
    diagnostics = []
    tool_results: dict[str, dict[str, int]] = {}
    for s in steps:
        if s.step_type == StepType.tool_call and s.tool_name:
            tool_results.setdefault(s.tool_name, {"calls": 0, "errors": 0})
            tool_results[s.tool_name]["calls"] += 1
        if s.step_type == StepType.error and s.tool_name:
            tool_results.setdefault(s.tool_name, {"calls": 0, "errors": 0})
            tool_results[s.tool_name]["errors"] += 1

    for tool, stats in tool_results.items():
        if stats["calls"] > 0 and stats["errors"] / stats["calls"] > 0.3:
            diagnostics.append(
                Diagnostic(
                    run_id=steps[0].run_id if steps else "",
                    severity=Severity.warning,
                    category=DiagnosticCategory.tool_selection,
                    title=f"High error rate for tool '{tool}'",
                    description=f"Tool '{tool}' has {stats['errors']} errors in {stats['calls']} calls ({stats['errors'] / stats['calls'] * 100:.0f}%)",
                    step_index=len(steps) - 1,
                    recommendation="Verify tool availability and input format; consider fallback options",
                )
            )
    return diagnostics


def detect_reasoning_failures(steps: list[Step]) -> list[Diagnostic]:
    diagnostics = []
    error_steps = [s for s in steps if s.step_type == StepType.error]
    if error_steps:
        diagnostics.append(
            Diagnostic(
                run_id=steps[0].run_id if steps else "",
                severity=Severity.error,
                category=DiagnosticCategory.reasoning,
                title=f"{len(error_steps)} error(s) during execution",
                description=error_steps[-1].error_message or "Multiple errors encountered",
                step_index=steps.index(error_steps[-1]),
                recommendation="Review error handling, input validation, and tool response parsing",
            )
        )

    for i, step in enumerate(steps):
        if step.step_type == StepType.thought and len(step.content) > 2000:
            diagnostics.append(
                Diagnostic(
                    run_id=step.run_id,
                    severity=Severity.info,
                    category=DiagnosticCategory.reasoning,
                    title="Unusually long reasoning step",
                    description=f"Step {step.step_number} has {len(step.content)} characters of reasoning",
                    step_index=i,
                    recommendation="Consider prompting for more concise reasoning",
                )
            )

    return diagnostics


def detect_timeout(steps: list[Step], timeout_ms: float = 300000) -> list[Diagnostic]:
    diagnostics = []
    total = sum(s.latency_ms for s in steps)
    if total > timeout_ms:
        diagnostics.append(
            Diagnostic(
                run_id=steps[0].run_id if steps else "",
                severity=Severity.error,
                category=DiagnosticCategory.timeout,
                title="Run exceeded time threshold",
                description=f"Total latency {total / 1000:.1f}s exceeds {timeout_ms / 1000:.1f}s threshold",
                step_index=len(steps) - 1,
                recommendation="Optimize tool calls, reduce step count, or increase timeout",
            )
        )
    return diagnostics


def detect_efficiency_issues(steps: list[Step]) -> list[Diagnostic]:
    diagnostics = []
    thought_steps = [s for s in steps if s.step_type == StepType.thought]
    tool_steps = [s for s in steps if s.step_type == StepType.tool_call]

    if thought_steps and tool_steps:
        if len(tool_steps) < len(thought_steps) * 0.2:
            diagnostics.append(
                Diagnostic(
                    run_id=steps[0].run_id if steps else "",
                    severity=Severity.info,
                    category=DiagnosticCategory.efficiency,
                    title="Low tool utilization",
                    description=f"Only {len(tool_steps)} tool calls across {len(steps)} steps",
                    step_index=len(steps) - 1,
                    recommendation="Agent may benefit from more aggressive tool use",
                )
            )

    return diagnostics


def detect_hallucination_patterns(steps: list[Step]) -> list[Diagnostic]:
    diagnostics = []
    for i, step in enumerate(steps):
        if step.step_type == StepType.output:
            indicators = [
                "i don't have access to",
                "i cannot",
                "i'm not able to",
                "i do not have",
                "it is important to note",
                "i think",
                "i believe",
                "as an ai",
                "as a language model",
            ]
            matches = [ind for ind in indicators if ind in step.content.lower()]
            if len(matches) >= 3:
                diagnostics.append(
                    Diagnostic(
                        run_id=step.run_id,
                        severity=Severity.info,
                        category=DiagnosticCategory.hallucination,
                        title="Potential hedging or hallucination markers",
                        description=f"Multiple hedging phrases detected in output: {', '.join(matches)}",
                        step_index=i,
                        recommendation="Verify factual accuracy; consider retrieval-augmented generation",
                    )
                )
                break
    return diagnostics


def run_all_heuristics(
    steps: list[Step],
    max_context: int = 32000,
    max_cost: float = 0.10,
    timeout_ms: float = 300000,
) -> list[Diagnostic]:
    all_diags = []
    all_diags.extend(detect_looping(steps))
    all_diags.extend(detect_context_window_exhaustion(steps, max_context))
    all_diags.extend(detect_cost_overrun(steps, max_cost))
    all_diags.extend(detect_tool_selection_issues(steps))
    all_diags.extend(detect_reasoning_failures(steps))
    all_diags.extend(detect_timeout(steps, timeout_ms))
    all_diags.extend(detect_efficiency_issues(steps))
    all_diags.extend(detect_hallucination_patterns(steps))
    return all_diags

from ..models.diagnostics import Diagnostic
from ..models.evaluation import Evaluation, TaskDefinition
from ..models.metrics import RunMetrics
from ..models.run import Run
from ..models.trace import Step, Trace
from .db import deserialize, get_connection, get_connection_dict, serialize


class EvaluationRepository:
    table = "evaluations"

    def save(self, evaluation: Evaluation) -> None:
        conn = get_connection()
        conn.execute(
            f"""INSERT OR REPLACE INTO {self.table}
            (id, name, description, tasks, grading_type, judge_config, tags, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                evaluation.id,
                evaluation.name,
                evaluation.description,
                serialize([t.model_dump() for t in evaluation.tasks]),
                evaluation.grading_type.value,
                serialize(evaluation.judge_config),
                serialize(evaluation.tags),
                serialize(evaluation.metadata),
                evaluation.created_at,
                evaluation.updated_at,
            ),
        )
        conn.commit()

    def find_by_id(self, eval_id: str) -> Evaluation | None:
        conn = get_connection_dict()
        row = conn.execute(f"SELECT * FROM {self.table} WHERE id = ?", (eval_id,)).fetchone()
        return self._row_to_model(row) if row else None

    def find_all(self) -> list[Evaluation]:
        conn = get_connection_dict()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY created_at DESC").fetchall()
        return [self._row_to_model(r) for r in rows]

    def delete(self, eval_id: str) -> None:
        conn = get_connection()
        conn.execute(f"DELETE FROM {self.table} WHERE id = ?", (eval_id,))
        conn.commit()

    def _row_to_model(self, row: dict) -> Evaluation:
        row["tasks"] = [TaskDefinition(**t) for t in deserialize(row.get("tasks", "[]"))]
        row["tags"] = deserialize(row.get("tags", "[]"))
        row["metadata"] = deserialize(row.get("metadata", "{}"))
        row["judge_config"] = deserialize(row.get("judge_config"))
        return Evaluation(**row)


class TaskDefinitionRepository:
    table = "task_definitions"

    def save(self, task: TaskDefinition) -> None:
        conn = get_connection()
        conn.execute(
            f"""INSERT OR REPLACE INTO {self.table}
            (id, evaluation_id, name, description, instructions, success_criteria,
             expected_output, max_steps, max_tokens, timeout_seconds,
             required_tools, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task.id,
                task.evaluation_id if hasattr(task, "evaluation_id") else "",
                task.name,
                task.description,
                task.instructions,
                serialize([c.model_dump() for c in task.success_criteria]),
                task.expected_output,
                task.max_steps,
                task.max_tokens,
                task.timeout_seconds,
                serialize(task.required_tools),
                serialize(task.tags),
                serialize(task.metadata),
                task.created_at,
            ),
        )
        conn.commit()


class RunRepository:
    table = "runs"

    def save(self, run: Run) -> None:
        conn = get_connection()
        conn.execute(
            f"""INSERT OR REPLACE INTO {self.table}
            (id, evaluation_id, task_id, status, agent_config, started_at, completed_at,
             seed, env_snapshot, metrics, trace_id, diagnostics, error_message, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run.id,
                run.evaluation_id,
                run.task_id,
                run.status,
                serialize(run.agent_config),
                run.started_at,
                run.completed_at,
                run.seed,
                serialize(run.env_snapshot),
                serialize(run.metrics.model_dump()),
                run.trace_id,
                serialize([d.model_dump() for d in run.diagnostics]),
                run.error_message,
                serialize(run.metadata),
                run.created_at,
            ),
        )
        conn.commit()

    def find_by_id(self, run_id: str) -> Run | None:
        conn = get_connection_dict()
        row = conn.execute(f"SELECT * FROM {self.table} WHERE id = ?", (run_id,)).fetchone()
        return self._row_to_model(row) if row else None

    def find_by_evaluation(self, evaluation_id: str) -> list[Run]:
        conn = get_connection_dict()
        rows = conn.execute(
            f"SELECT * FROM {self.table} WHERE evaluation_id = ? ORDER BY created_at DESC",
            (evaluation_id,),
        ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def find_all(self, limit: int = 100, offset: int = 0) -> list[Run]:
        conn = get_connection_dict()
        rows = conn.execute(
            f"SELECT * FROM {self.table} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def count(self) -> int:
        conn = get_connection_dict()
        row = conn.execute(f"SELECT COUNT(*) as cnt FROM {self.table}").fetchone()
        return row["cnt"]  # type: ignore[no-any-return]

    def update_status(self, run_id: str, status: str) -> None:
        conn = get_connection()
        conn.execute(f"UPDATE {self.table} SET status = ? WHERE id = ?", (status, run_id))
        conn.commit()

    def _row_to_model(self, row: dict) -> Run:
        row["agent_config"] = deserialize(row.get("agent_config", "{}"))
        row["env_snapshot"] = deserialize(row.get("env_snapshot", "{}"))
        row["metrics"] = RunMetrics(**deserialize(row.get("metrics", "{}")))
        row["diagnostics"] = [Diagnostic(**d) for d in deserialize(row.get("diagnostics", "[]"))]
        row["metadata"] = deserialize(row.get("metadata", "{}"))
        return Run(**row)


class TraceRepository:
    table = "traces"

    def __init__(self):
        self._step_repo = StepRepository()

    def save(self, trace: Trace) -> None:
        conn = get_connection()
        conn.execute(
            f"""INSERT OR REPLACE INTO {self.table}
            (id, run_id, metadata, created_at)
            VALUES (?, ?, ?, ?)""",
            (
                trace.id,
                trace.run_id,
                serialize(trace.metadata),
                trace.created_at,
            ),
        )
        conn.commit()

    def find_by_run_id(self, run_id: str) -> Trace | None:
        conn = get_connection_dict()
        row = conn.execute(f"SELECT * FROM {self.table} WHERE run_id = ?", (run_id,)).fetchone()
        return self._row_to_model(row) if row else None

    def find_by_id(self, trace_id: str) -> Trace | None:
        conn = get_connection_dict()
        row = conn.execute(f"SELECT * FROM {self.table} WHERE id = ?", (trace_id,)).fetchone()
        return self._row_to_model(row) if row else None

    def _row_to_model(self, row: dict) -> Trace:
        row["steps"] = self._step_repo.find_by_run_id(row["run_id"])
        row["metadata"] = deserialize(row.get("metadata", "{}"))
        return Trace(**row)


class StepRepository:
    table = "steps"

    def save(self, step: Step) -> None:
        conn = get_connection()
        conn.execute(
            f"""INSERT INTO {self.table}
            (id, run_id, step_number, timestamp, step_type, content,
             tool_name, tool_input, tool_output, token_count, input_tokens, output_tokens,
             cost_usd, latency_ms, state_snapshot, error_message, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                step.id,
                step.run_id,
                step.step_number,
                step.timestamp,
                step.step_type.value,
                step.content,
                step.tool_name,
                serialize(step.tool_input),
                step.tool_output,
                step.token_count,
                step.input_tokens,
                step.output_tokens,
                step.cost_usd,
                step.latency_ms,
                serialize(step.state_snapshot),
                step.error_message,
                serialize(step.metadata),
            ),
        )
        conn.commit()

    def find_by_run_id(self, run_id: str) -> list[Step]:
        conn = get_connection_dict()
        rows = conn.execute(
            f"SELECT * FROM {self.table} WHERE run_id = ? ORDER BY step_number",
            (run_id,),
        ).fetchall()
        return [self._row_to_model(r) for r in rows]

    def _row_to_model(self, row: dict) -> Step:
        row["tool_input"] = deserialize(row.get("tool_input"))
        row["state_snapshot"] = deserialize(row.get("state_snapshot"))
        row["metadata"] = deserialize(row.get("metadata", "{}"))
        return Step(**row)


class DiagnosticRepository:
    table = "diagnostics"

    def save(self, diagnostic: Diagnostic) -> None:
        conn = get_connection()
        conn.execute(
            f"""INSERT OR REPLACE INTO {self.table}
            (id, run_id, severity, category, title, description,
             step_index, recommendation, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                diagnostic.id,
                diagnostic.run_id,
                diagnostic.severity.value,
                diagnostic.category.value,
                diagnostic.title,
                diagnostic.description,
                diagnostic.step_index,
                diagnostic.recommendation,
                serialize(diagnostic.metadata),
                diagnostic.created_at,
            ),
        )
        conn.commit()

    def find_by_run_id(self, run_id: str) -> list[Diagnostic]:
        conn = get_connection_dict()
        rows = conn.execute(
            f"SELECT * FROM {self.table} WHERE run_id = ? ORDER BY created_at",
            (run_id,),
        ).fetchall()
        result = []
        for r in rows:
            r["metadata"] = deserialize(r.get("metadata", "{}"))
            result.append(Diagnostic(**r))
        return result

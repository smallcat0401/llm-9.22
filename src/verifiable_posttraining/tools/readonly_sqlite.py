"""Tier A: constrained read-only SQLite execution.

SQL text produced by a model is untrusted.  This tool combines SQLite's
``query_only`` mode with an engine-level authorizer, table/function allowlists,
an execution-step budget, and a result-row limit.  String-prefix checks such as
``query.startswith('SELECT')`` are deliberately not treated as a safety
boundary.
"""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from typing import Any, Mapping

from ..schemas import Observation, ToolCall

MAX_QUERY_LENGTH = 2_000
DEFAULT_MAX_ROWS = 100
DEFAULT_MAX_VM_STEPS = 100_000
_PROGRESS_INTERVAL = 100

_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
}

_DEFAULT_ALLOWED_FUNCTIONS = frozenset(
    {
        "abs",
        "avg",
        "coalesce",
        "count",
        "ifnull",
        "length",
        "lower",
        "max",
        "min",
        "nullif",
        "round",
        "sum",
        "total",
        "typeof",
        "upper",
    }
)


@dataclass(frozen=True, slots=True)
class SQLToolLimits:
    max_rows: int = DEFAULT_MAX_ROWS
    max_vm_steps: int = DEFAULT_MAX_VM_STEPS

    def __post_init__(self) -> None:
        if self.max_rows <= 0:
            raise ValueError("max_rows must be positive")
        if self.max_vm_steps <= 0:
            raise ValueError("max_vm_steps must be positive")


class ReadOnlySQLiteTool:
    """Callable tool executor bound to one pre-created SQLite connection."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        allowed_tables: frozenset[str] | set[str],
        allowed_functions: frozenset[str] | set[str] = _DEFAULT_ALLOWED_FUNCTIONS,
        limits: SQLToolLimits | None = None,
    ) -> None:
        if not allowed_tables:
            raise ValueError("allowed_tables must not be empty")
        self._connection = connection
        self._allowed_tables = frozenset(name.casefold() for name in allowed_tables)
        self._allowed_functions = frozenset(name.casefold() for name in allowed_functions)
        self._limits = limits or SQLToolLimits()
        self._connection.execute("PRAGMA query_only = ON")
        self._connection.set_authorizer(self._authorize)

    def __call__(self, call: ToolCall) -> Observation:
        if call.name != "sql":
            return self._failure(call, "wrong_tool", "tool call name must be 'sql'")
        arguments: Mapping[str, Any] = call.arguments
        if set(arguments) != {"query"} or not isinstance(arguments.get("query"), str):
            return self._failure(
                call,
                "invalid_arguments",
                "sql requires exactly one string 'query' argument",
            )
        query = arguments["query"].strip()
        if not query:
            return self._failure(call, "invalid_arguments", "query must not be empty")
        if len(query) > MAX_QUERY_LENGTH:
            return self._failure(call, "query_too_long", "query exceeds the length limit")
        return self._execute(call, query)

    def _authorize(
        self,
        action_code: int,
        argument_one: str | None,
        argument_two: str | None,
        database_name: str | None,
        trigger_name: str | None,
    ) -> int:
        del database_name, trigger_name
        if action_code not in _ALLOWED_ACTIONS:
            return sqlite3.SQLITE_DENY
        if action_code == sqlite3.SQLITE_READ:
            table_name = (argument_one or "").casefold()
            if table_name not in self._allowed_tables:
                return sqlite3.SQLITE_DENY
        if action_code == sqlite3.SQLITE_FUNCTION:
            function_name = (argument_two or "").casefold()
            if function_name not in self._allowed_functions:
                return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def _execute(self, call: ToolCall, query: str) -> Observation:
        progress_calls = 0
        max_progress_calls = max(1, self._limits.max_vm_steps // _PROGRESS_INTERVAL)

        def progress_handler() -> int:
            nonlocal progress_calls
            progress_calls += 1
            return int(progress_calls > max_progress_calls)

        self._connection.set_progress_handler(progress_handler, _PROGRESS_INTERVAL)
        try:
            cursor = self._connection.execute(query)
            if cursor.description is None:
                return self._failure(call, "unsafe_query", "query did not produce rows")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchmany(self._limits.max_rows + 1)
        except sqlite3.DatabaseError as exc:
            message = str(exc)
            lowered = message.casefold()
            if "interrupted" in lowered:
                return self._failure(call, "query_limit_exceeded", "query exceeded step limit")
            if any(
                marker in lowered
                for marker in (
                    "not authorized",
                    "prohibited",
                    "readonly",
                    "one statement at a time",
                )
            ):
                return self._failure(call, "unsafe_query", "query violates read-only policy")
            return self._failure(call, "query_error", message)
        finally:
            self._connection.set_progress_handler(None, 0)

        if len(rows) > self._limits.max_rows:
            return self._failure(
                call,
                "row_limit_exceeded",
                f"query returned more than {self._limits.max_rows} rows",
            )
        try:
            normalized_rows = [
                [self._normalize_value(value) for value in row]
                for row in rows
            ]
        except ValueError as exc:
            return self._failure(call, "unsupported_result", str(exc))
        return Observation(
            call_id=call.call_id,
            ok=True,
            content={
                "columns": columns,
                "rows": normalized_rows,
                "row_count": len(normalized_rows),
            },
        )

    @staticmethod
    def _normalize_value(value: Any) -> str | int | float | None:
        if value is None or isinstance(value, (str, int)):
            return value
        if isinstance(value, float) and math.isfinite(value):
            return value
        raise ValueError(f"unsupported SQLite result type: {type(value).__name__}")

    @staticmethod
    def _failure(call: ToolCall, code: str, message: str) -> Observation:
        return Observation(
            call_id=call.call_id,
            ok=False,
            content={"message": message},
            error_code=code,
        )

"""Lab compliance helpers tests."""
from __future__ import annotations

from pathlib import Path

from labs.run_lab import evaluate_trace


def write_trace(trace: Path, lines: list[str]) -> None:
    trace.write_text("\n".join(lines), encoding="utf-8")


def test_evaluate_trace_missing_status_before(tmp_path: Path) -> None:
    trace = tmp_path / "trace.log"
    write_trace(trace, [
        "2025-01-01T00:00:00Z\tupdate\tstatus=completed",
        "2025-01-01T00:00:01Z\tstatus-after\treason=idle",
    ])
    score, reasons = evaluate_trace(trace)
    assert score < 60
    assert "missing status-after" in reasons


def test_evaluate_trace_missing_update(tmp_path: Path) -> None:
    trace = tmp_path / "trace.log"
    write_trace(trace, [
        "2025-01-01T00:00:00Z\tstatus-before\treason=idle",
        "2025-01-01T00:00:01Z\tstatus-after\treason=idle",
    ])
    score, reasons = evaluate_trace(trace)
    assert score < 60
    assert "missing update" in reasons


def test_evaluate_trace_missing_status_after(tmp_path: Path) -> None:
    trace = tmp_path / "trace.log"
    write_trace(trace, [
        "2025-01-01T00:00:00Z\tstatus-before\treason=idle",
        "2025-01-01T00:00:01Z\tupdate\tstatus=ok",
    ])
    score, reasons = evaluate_trace(trace)
    assert score < 60
    assert "missing status-after" in reasons


def test_evaluate_trace_all_steps_present(tmp_path: Path) -> None:
    trace = tmp_path / "trace.log"
    write_trace(trace, [
        "2025-01-01T00:00:00Z\tstatus-before\treason=idle",
        "2025-01-01T00:00:01Z\tupdate\tstatus=ok",
        "2025-01-01T00:00:02Z\tstatus-after\treason=task",
    ])
    score, reasons = evaluate_trace(trace)
    assert score >= 60
    assert reasons == []


def test_evaluate_trace_signal_not_closed(tmp_path: Path) -> None:
    trace = tmp_path / "trace.log"
    write_trace(trace, [
        "2025-01-01T00:00:00Z\tstatus-before\treason=idle",
        "2025-01-01T00:00:01Z\tsignal-open\tid=ci-blocker",
        "2025-01-01T00:00:02Z\tupdate\tstatus=ok",
        "2025-01-01T00:00:03Z\tstatus-after\treason=task",
    ])
    score, reasons = evaluate_trace(trace)
    assert score < 60
    assert "signal left open" in reasons

from __future__ import annotations
import json, statistics, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def measurement(identifier: str, stage: str, target: str, protocol: str, result: str, duration_ms: float | None, error_category: str = "none", *, attempts: int = 1, successful_attempts: int = 0, failed_attempts: int = 0, details: dict[str, Any] | None = None, error_detail: str | None = None) -> dict[str, Any]:
    item = {"id": identifier, "timestamp_utc": utc_now(), "stage": stage, "target": target, "protocol": protocol, "result": result, "duration_ms": duration_ms, "error_category": error_category, "attempts": attempts, "successful_attempts": successful_attempts, "failed_attempts": failed_attempts, "details": details or {}}
    if error_detail: item["error_detail"] = error_detail[:1000]
    return item

def latency_statistics(durations: list[float], attempts: int) -> dict[str, float | None]:
    if not durations:
        return {"minimum_ms": None, "median_ms": None, "maximum_ms": None, "mean_ms": None, "packet_loss_percent": 100.0 if attempts else None}
    return {"minimum_ms": min(durations), "median_ms": statistics.median(durations), "maximum_ms": max(durations), "mean_ms": statistics.mean(durations), "packet_loss_percent": round(100 * (attempts - len(durations)) / attempts, 2) if attempts else None}

def new_report(network_configuration: dict[str, Any], operating_system: str) -> dict[str, Any]:
    return {"schema_version": "1.0", "session_id": str(uuid.uuid4()), "collected_at_utc": utc_now(), "probe": {"os": operating_system, "version": "1.0.0"}, "network_configuration": network_configuration, "results": [], "statistics": {}, "traceroute": []}

def write_report(report: dict[str, Any], output: str) -> Path:
    path = Path(output).expanduser().resolve()
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return path

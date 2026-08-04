"""Pipeline metrics for Path A and Path B observability."""

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class PathMetrics:
    shortlist_sizes: list[int] = field(default_factory=list)
    llm_candidate_sizes: list[int] = field(default_factory=list)
    processing_latencies_ms: list[int] = field(default_factory=list)
    match_counts: list[int] = field(default_factory=list)
    output_counts: list[int] = field(default_factory=list)


_path_a_metrics = PathMetrics()
_path_b_metrics = PathMetrics()
_lock = Lock()


def record_path_a_run(
    *,
    shortlist_size: int,
    llm_candidate_size: int,
    latency_ms: int,
    match_count: int,
) -> None:
    with _lock:
        _path_a_metrics.shortlist_sizes.append(shortlist_size)
        _path_a_metrics.llm_candidate_sizes.append(llm_candidate_size)
        _path_a_metrics.processing_latencies_ms.append(latency_ms)
        _path_a_metrics.match_counts.append(match_count)


def record_path_b_run(
    *,
    shortlist_size: int,
    llm_candidate_size: int,
    output_count: int,
    latency_ms: int,
) -> None:
    with _lock:
        _path_b_metrics.shortlist_sizes.append(shortlist_size)
        _path_b_metrics.llm_candidate_sizes.append(llm_candidate_size)
        _path_b_metrics.output_counts.append(output_count)
        _path_b_metrics.processing_latencies_ms.append(latency_ms)


def get_path_a_metrics() -> dict:
    with _lock:
        return {
            "runs": len(_path_a_metrics.shortlist_sizes),
            "avg_shortlist_size": _avg(_path_a_metrics.shortlist_sizes),
            "avg_llm_candidate_size": _avg(_path_a_metrics.llm_candidate_sizes),
            "max_llm_candidate_size": max(_path_a_metrics.llm_candidate_sizes) if _path_a_metrics.llm_candidate_sizes else 0,
            "avg_processing_latency_ms": _avg(_path_a_metrics.processing_latencies_ms),
            "avg_match_count": _avg(_path_a_metrics.match_counts),
        }


def get_path_b_metrics() -> dict:
    with _lock:
        return {
            "runs": len(_path_b_metrics.shortlist_sizes),
            "avg_shortlist_size": _avg(_path_b_metrics.shortlist_sizes),
            "avg_llm_candidate_size": _avg(_path_b_metrics.llm_candidate_sizes),
            "max_llm_candidate_size": max(_path_b_metrics.llm_candidate_sizes) if _path_b_metrics.llm_candidate_sizes else 0,
            "avg_output_count": _avg(_path_b_metrics.output_counts),
            "avg_processing_latency_ms": _avg(_path_b_metrics.processing_latencies_ms),
        }


def _avg(values: list[int | float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)

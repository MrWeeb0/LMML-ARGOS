from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

MOISTURE_MIN = 10.5
MOISTURE_MAX = 12.5
DRY_STEP = 0.8
GRADE_TOLERANCE = 0.5


class BatchState(TypedDict):
    batch_id: str
    moisture: float
    passes: int
    inspections: int
    received: bool
    approved: bool
    grade: str


def receive_batch(state: BatchState) -> dict:
    return {"received": True}


def inspect_batch(state: BatchState) -> dict:
    return {
        "inspections": state["inspections"] + 1,
        "approved": MOISTURE_MIN <= state["moisture"] <= MOISTURE_MAX,
    }


def dry_batch(state: BatchState) -> dict:
    return {
        "moisture": round(max(state["moisture"] - DRY_STEP, 0.0), 4),
        "passes": state["passes"] + 1,
    }


def grade_batch(state: BatchState) -> dict:
    midpoint = (MOISTURE_MIN + MOISTURE_MAX) / 2
    grade = "A" if abs(state["moisture"] - midpoint) <= GRADE_TOLERANCE else "B"
    return {"grade": grade}


def route_after_inspection(state: BatchState) -> Literal["dry_batch", "grade_batch"]:
    if state["approved"]:
        return "grade_batch"
    return "dry_batch"


def build_graph():
    graph = StateGraph(BatchState)
    graph.add_node("receive_batch", receive_batch)
    graph.add_node("inspect_batch", inspect_batch)
    graph.add_node("dry_batch", dry_batch)
    graph.add_node("grade_batch", grade_batch)
    graph.add_edge(START, "receive_batch")
    graph.add_edge("receive_batch", "inspect_batch")
    graph.add_conditional_edges(
        "inspect_batch",
        route_after_inspection,
        {"dry_batch": "dry_batch", "grade_batch": "grade_batch"},
    )
    graph.add_edge("dry_batch", "inspect_batch")
    graph.add_edge("grade_batch", END)
    return graph.compile()


def initial_state(batch_id: str, moisture: float) -> BatchState:
    return {
        "batch_id": batch_id,
        "moisture": moisture,
        "passes": 0,
        "inspections": 0,
        "received": False,
        "approved": False,
        "grade": "",
    }

"""LangGraph workflow definition for AI Automation Agent."""

from langgraph.graph import END, START, StateGraph

from src.llm_factory import get_llm
from src.nodes.evaluator import evaluator_node
from src.nodes.executor import executor_node
from src.nodes.finalizer import finalizer_node
from src.nodes.planner import planner_node
from src.nodes.replanner import replanner_node
from src.state import AutomationState


def create_evaluation_router():
    """Route from evaluator to either next executor step, retry, replanner, or finalizer."""

    def route_evaluation(state: AutomationState) -> str:
        status = state.get("evaluation_status", "continue")
        if status == "finish":
            return "finalizer"
        elif status == "replan":
            return "replanner"
        elif status == "retry":
            return "executor"
        else:
            return "executor"

    return route_evaluation


def build_automation_graph(llm=None):
    """Construct and compile the LangGraph AI Automation workflow.

    Workflow Topology:
      START -> planner -> executor -> evaluator
                           ^             |
                           |-(retry/next)-+
                           |             | (replan)
                           +- replanner <-+
                                         | (finish)
                                         v
                                     finalizer -> END
    """
    if llm is None:
        llm = get_llm()

    # Node wrappers passing LLM instance
    def _planner(state: AutomationState):
        return planner_node(state, llm)

    def _executor(state: AutomationState):
        return executor_node(state, llm)

    def _evaluator(state: AutomationState):
        return evaluator_node(state, llm)

    def _replanner(state: AutomationState):
        return replanner_node(state, llm)

    def _finalizer(state: AutomationState):
        return finalizer_node(state, llm)

    # Initialize StateGraph
    workflow = StateGraph(AutomationState)

    # Register Nodes
    workflow.add_node("planner", _planner)
    workflow.add_node("executor", _executor)
    workflow.add_node("evaluator", _evaluator)
    workflow.add_node("replanner", _replanner)
    workflow.add_node("finalizer", _finalizer)

    # Define Transitions
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "evaluator")

    # Conditional branching from evaluator
    workflow.add_conditional_edges(
        "evaluator",
        create_evaluation_router(),
        {
            "executor": "executor",
            "replanner": "replanner",
            "finalizer": "finalizer",
        },
    )

    # From replanner, proceed back to executor
    workflow.add_edge("replanner", "executor")

    # From finalizer, complete the graph
    workflow.add_edge("finalizer", END)

    return workflow.compile()

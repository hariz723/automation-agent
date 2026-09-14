"""Unit and integration tests for LangGraph AI Automation Agent."""

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from src.graph import build_automation_graph, create_evaluation_router
from src.nodes.evaluator import EvaluationSchema, evaluator_node
from src.nodes.finalizer import finalizer_node
from src.nodes.planner import PlanSchema, StepSchema, planner_node
from src.state import AutomationState
from src.tools.file_tools import read_file, write_file
from src.tools.lint_tools import lint_code
from src.tools.python_repl import execute_python
from src.tools.shell_tools import execute_shell


def test_lint_code_valid():
    """Test that lint_code reports pass on valid python code."""
    valid_code = "x = 42\ny = x + 1\nprint(y)\n"
    res = lint_code.invoke({"filepath_or_code": valid_code})
    assert "✅ Lint passed" in res or "✅ Syntax check passed" in res


def test_lint_code_invalid():
    """Test that lint_code detects syntax errors."""
    invalid_code = "def bad_syntax(:\n    pass\n"
    res = lint_code.invoke({"filepath_or_code": invalid_code})
    assert "Lint findings" in res or "Syntax Error" in res or "error" in res.lower()


def test_file_tools(tmp_path):
    """Test file creation, reading, and listing."""
    test_file = tmp_path / "sample.txt"
    write_res = write_file.invoke({"filepath": str(test_file), "content": "Hello LangGraph!"})
    assert "Successfully wrote" in write_res

    read_res = read_file.invoke({"filepath": str(test_file)})
    assert read_res == "Hello LangGraph!"


def test_python_repl():
    """Test dynamic python execution sandbox."""
    code = """
total = sum([1, 2, 3, 4, 5])
print(f"SUM={total}")
"""
    res = execute_python.invoke({"code": code})
    assert "STDOUT:" in res
    assert "SUM=15" in res


def test_python_repl_error_handling():
    """Test python execution captures exceptions without crashing."""
    code = "1 / 0"
    res = execute_python.invoke({"code": code})
    assert "ZeroDivisionError" in res


def test_shell_safety():
    """Test that destructive shell commands are blocked."""
    res = execute_shell.invoke({"command": "rm -rf /"})
    assert "blocked for safety" in res


def test_graph_compilation():
    """Test that the LangGraph StateGraph builds and compiles without errors."""
    dummy_llm = MagicMock()
    app = build_automation_graph(llm=dummy_llm)
    assert app is not None
    graph = app.get_graph()
    node_names = set(graph.nodes.keys())
    assert "planner" in node_names
    assert "executor" in node_names
    assert "evaluator" in node_names
    assert "replanner" in node_names
    assert "finalizer" in node_names


def test_evaluation_router():
    """Test router decision based on evaluation_status."""
    router = create_evaluation_router()

    assert router({"evaluation_status": "continue"}) == "executor"
    assert router({"evaluation_status": "retry"}) == "executor"
    assert router({"evaluation_status": "replan"}) == "replanner"
    assert router({"evaluation_status": "finish"}) == "finalizer"


def test_planner_node_structured():
    """Test planner node with structured output from LLM."""
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = PlanSchema(
        steps=[
            StepSchema(
                id=1,
                title="Fetch Data",
                description="Fetch source data",
                expected_output="Data fetched",
            ),
            StepSchema(
                id=2,
                title="Process Data",
                description="Run analysis",
                expected_output="Analysis complete",
            ),
        ]
    )
    mock_llm.with_structured_output.return_value = mock_structured

    state: AutomationState = {"task": "Analyze quarterly sales data"}
    result = planner_node(state, mock_llm)

    assert len(result["plan"]) == 2
    assert result["plan"][0]["title"] == "Fetch Data"
    assert result["plan"][1]["title"] == "Process Data"
    assert result["current_step_index"] == 0


def test_evaluator_node_success():
    """Test evaluator marking a step successful and advancing."""
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = EvaluationSchema(
        is_successful=True,
        critique="Step succeeded completely.",
        recommendation="continue",
    )
    mock_llm.with_structured_output.return_value = mock_structured

    state: AutomationState = {
        "task": "Test goal",
        "plan": [
            {"id": 1, "title": "Step 1", "description": "", "expected_output": ""},
            {"id": 2, "title": "Step 2", "description": "", "expected_output": ""},
        ],
        "current_step_index": 0,
        "last_step_result": "Step 1 done",
        "retry_count": 0,
    }

    res = evaluator_node(state, mock_llm)
    assert res["evaluation_status"] == "continue"
    assert res["current_step_index"] == 1


def test_evaluator_node_final_step():
    """Test evaluator signaling finish on the final step."""
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = EvaluationSchema(
        is_successful=True,
        critique="Final step fulfilled.",
        recommendation="continue",
    )
    mock_llm.with_structured_output.return_value = mock_structured

    state: AutomationState = {
        "task": "Test goal",
        "plan": [
            {"id": 1, "title": "Step 1", "description": "", "expected_output": ""},
        ],
        "current_step_index": 0,
        "last_step_result": "Step 1 done",
        "retry_count": 0,
    }

    res = evaluator_node(state, mock_llm)
    assert res["evaluation_status"] == "finish"


def test_finalizer_node():
    """Test finalizer synthesizing completed steps."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Final Report: Automation Success.")

    state: AutomationState = {
        "task": "Automate report generation",
        "plan": [{"id": 1, "title": "Create Report"}],
        "step_history": [{"step_id": 1, "title": "Create Report", "result": "Report generated"}],
    }

    res = finalizer_node(state, mock_llm)
    assert "Final Report: Automation Success." in res["final_output"]

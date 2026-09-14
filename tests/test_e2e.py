"""End-to-end simulation test verifying complete flow execution."""

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from src.nodes.evaluator import EvaluationSchema
from src.nodes.planner import PlanSchema, StepSchema
from src.runner import run_automation


def test_full_graph_e2e(tmp_path, monkeypatch):
    """Verify that a prompt goes through planner -> executor -> evaluator -> finalizer end-to-end."""

    output_file = tmp_path / "test_result.txt"

    # Mock LLM that generates a 1-step plan, calls a tool or completes the step, evaluates to success, and finalizes
    mock_llm = MagicMock()

    # Planner call: returns a 1-step plan
    mock_planner = MagicMock()
    mock_planner.invoke.return_value = PlanSchema(
        steps=[
            StepSchema(
                id=1,
                title="Write Output File",
                description=f"Write test content to {output_file}",
                expected_output="File written",
            )
        ]
    )

    # Evaluator call: returns successful evaluation
    mock_eval = MagicMock()
    mock_eval.invoke.return_value = EvaluationSchema(
        is_successful=True,
        critique="Output file was created and verified.",
        recommendation="continue",
    )

    def side_effect_structured(schema):
        if schema == PlanSchema:
            return mock_planner
        elif schema == EvaluationSchema:
            return mock_eval
        return mock_eval

    mock_llm.with_structured_output.side_effect = side_effect_structured

    # Executor call: simulate LLM with tool call or direct message
    ai_exec_msg = AIMessage(
        content=f"Successfully created {output_file} with results.",
        tool_calls=[
            {
                "name": "write_file",
                "args": {
                    "filepath": str(output_file),
                    "content": "Automation Result: Fibonacci [0, 1, 1, 2, 3, 5, 8]",
                },
                "id": "call_write_1",
            }
        ],
    )
    ai_final_step_msg = AIMessage(content="Step finished. File written successfully.")
    ai_finalizer_msg = AIMessage(content="Final Report: Fibonacci analysis generated and saved.")

    # Model invocations during execution and finalizer
    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools.invoke.side_effect = [ai_exec_msg, ai_final_step_msg]
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_llm.invoke.return_value = ai_finalizer_msg

    # Execute workflow
    result = run_automation(
        prompt="Compute Fibonacci series and write to file",
        llm=mock_llm,
        verbose=True,
    )

    assert result is not None
    assert "final_output" in result
    assert "Fibonacci" in result["final_output"]

    # Verify that the tool actually ran and created the file on disk!
    assert output_file.exists()
    content = output_file.read_text()
    assert "Fibonacci [0, 1, 1, 2, 3, 5, 8]" in content

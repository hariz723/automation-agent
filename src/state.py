"""State definition for LangGraph AI Automation Agent."""

from typing import Any

from typing_extensions import TypedDict


class SubTask(TypedDict, total=False):
    """Represents a single step in the execution plan."""
    id: int
    title: str
    description: str
    expected_output: str
    status: str  # "pending", "in_progress", "completed", "failed"
    result: str | None


class AutomationState(TypedDict, total=False):
    """State passed through the LangGraph automation workflow."""
    task: str                               
    plan: list[SubTask]                     
    current_step_index: int                 
    step_history: list[dict[str, Any]]      
    context: dict[str, Any]                 
    last_step_result: str | None         
    evaluation_status: str       # "continue", "retry", "replan", "finish"
    evaluation_feedback: str | None      
    retry_count: int                        
    final_output: str | None             
    error: str | None                    

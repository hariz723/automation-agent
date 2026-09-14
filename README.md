# 🤖 Autonomous AI Automation Agent

An autonomous AI agent built with **LangGraph**, designed to turn any user prompt into a structured, self-healing execution flow that accomplishes complex tasks end-to-end.

Supports both **Google Gemini** (recommended for speed and tool use) and **Hugging Face** open-source models.

---

## 🌟 Features

- **Goal-Driven Prompt-to-Execution**: Give the agent any prompt or use case, and it plans, executes, evaluates, and delivers the result.
- **Dynamic LangGraph Architecture**:
  - **Planner**: Decomposes prompts into structured subtasks with success criteria.
  - **Executor**: Executes steps using a suite of integrated tools (Python REPL, File I/O, Web Search, Shell).
  - **Evaluator**: Inspects step output against expected criteria.
  - **Replanner**: Dynamically adapts and rewrites remaining steps if blockers or errors occur.
  - **Finalizer**: Synthesizes results into a polished deliverable.
- **Tool Suite**:
  - 🐍 **Python REPL**: Dynamic code execution for computations, data analysis, and script running.
  - 📁 **File I/O**: Read, write, and list workspace files.
  - 🌐 **Web Search & Fetch**: DuckDuckGo search and webpage content scraping.
  - 💻 **Shell Execution**: Run workspace commands safely with security guards.
- **Dual LLM Support**:
  - **Google Gemini** (`gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-1.5-flash`) via `langchain-google-genai`.
  - **Hugging Face** (`Qwen/Qwen2.5-72B-Instruct`, `meta-llama/Llama-3.3-70B-Instruct`, etc.) via `langchain-huggingface`.
- **Rich Terminal UI**: Live streaming execution with tables, panels, and markdown formatting.

---

## 📐 Architecture & Workflow

```mermaid
graph TD
    __start__([Start: User Prompt]) --> planner
    planner[Planner: Decompose into Subtasks] --> executor
    executor[Executor: Tool-Calling Agent Loop] --> evaluator
    evaluator{Evaluator: Check Success}
    
    evaluator -- "Step Succeeded & More Steps" --> executor
    evaluator -- "Step Failed (Retry < Max)" --> executor
    evaluator -- "Step Failed (Retries Exhausted)" --> replanner[Replanner: Dynamic Plan Revision]
    replanner --> executor
    evaluator -- "All Steps Complete" --> finalizer[Finalizer: Synthesize Deliverable]
    finalizer --> __end__([End: Final Deliverable])
```

---

## 🚀 Quickstart

### 1. Requirements

All required libraries are specified in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your API key:
```ini
# For Google Gemini (Recommended)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# For Hugging Face (Optional)
# LLM_PROVIDER=huggingface
# HUGGINGFACEHUB_API_TOKEN=your_hf_token_here
# HF_MODEL=Qwen/Qwen2.5-72B-Instruct
```
> 💡 Get a free Gemini API key at [Google AI Studio](https://aistudio.google.com/).  
> 💡 Get a Hugging Face token at [Hugging Face Settings](https://huggingface.co/settings/tokens).

Alternatively, export directly in your shell:
```bash
export GEMINI_API_KEY="your_api_key"
```

---

## 💻 Usage

### 1. Single Prompt Execution
Provide any task directly as an argument:
```bash
python main.py 

# sample prompt
"Fetch the latest Python 3.13 release highlights and write a markdown summary to python313_summary.md"
```

Another example:
```bash
python main.py 

#sample prompt - 2
"Create a Python script that generates 100 dummy customer records, calculate average purchase value, and save results to summary.json"
```

### 2. Interactive Mode
Run an interactive session where you can enter prompts continuously:
```bash
python main.py --interactive
# or
python main.py -i
```

### 3. Model & Provider Selection
Switch between Gemini and Hugging Face or choose specific models via CLI:
```bash
# Using Gemini 2.5 Pro for complex reasoning
python main.py "Design and test a caching algorithm in Python" --model gemini-2.5-pro

# Using Hugging Face open-source model
python main.py "Analyze trends in artificial intelligence" --provider huggingface
```

### 4. Visualize the Workflow
Export the LangGraph topology as a diagram:
```bash
python main.py --visualize
```

---

## 🧪 Testing

Run the comprehensive test suite (unit tests, tools, router, and end-to-end graph simulation):
```bash
pytest -v tests/
```

---

## 📂 Project Structure

```
automation-agent/
├── main.py                # Main CLI entrypoint
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
├── graph.png              # Rendered LangGraph architecture diagram
├── src/
│   ├── config.py          # Configuration and environment loaders
│   ├── state.py           # TypedDict state definition
│   ├── llm_factory.py     # Gemini and Hugging Face model factory
│   ├── graph.py           # LangGraph StateGraph compiler
│   ├── runner.py          # Rich console streaming runner
│   ├── tools/
│   │   ├── file_tools.py  # File reading, writing, and listing
│   │   ├── python_repl.py # Dynamic Python execution sandbox
│   │   ├── web_tools.py   # DuckDuckGo search & webpage scraper
│   │   ├── shell_tools.py # Shell command runner
│   │   └── registry.py    # Unified tool registry
│   └── nodes/
│       ├── planner.py     # Task decomposition node
│       ├── executor.py    # Tool-calling execution node
│       ├── evaluator.py   # Step evaluation & router node
│       ├── replanner.py   # Dynamic plan adjustment node
│       └── finalizer.py   # Final synthesis node
└── tests/
    ├── conftest.py        # Pytest path configuration
    ├── test_graph.py      # Unit tests for tools, nodes, and router
    └── test_e2e.py        # End-to-end integration test
```

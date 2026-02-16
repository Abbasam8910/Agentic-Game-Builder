# 🎮 Agentic Game-Builder AI

An intelligent multi-agent system that transforms natural language game ideas into fully playable HTML/CSS/JavaScript games — powered by Google Gemini.

## ✨ Features

- **Natural Language Input** — Describe your game idea in plain English
- **Intelligent Clarification** — Asks only necessary questions (max 4 total), never cosmetic details
- **Automatic Framework Selection** — Chooses Phaser 3 or Vanilla JS based on game complexity
- **Complete Code Generation** — Produces three files (HTML, CSS, JS) with no placeholders
- **Two-Layer Validation** — Deterministic regex checks + LLM semantic review
- **Self-Healing Retry Logic** — Auto-retries failed code generation up to 3 times with error feedback
- **Rich CLI** — Beautiful terminal interface with progress bars, tables, and color-coded output
- **Fully Dockerized** — Containerized with volume mounts for local file output

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [Google AI API key](https://aistudio.google.com/apikey)
- Docker (optional, for containerized deployment)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/agentic-game-builder.git
cd agentic-game-builder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run the agent
python main.py
```

## 🐳 Docker Build & Run Instructions

This application is fully containerized. Because it is an interactive CLI agent that generates local files, the Docker container must be run in interactive mode (`-it`) and use a volume mount (`-v`) to save the generated games to your host machine.

### 1. Build the Docker Image

```bash
docker build -t agentic-game-builder .
```

### 2. Run the Agent

**Mac / Linux:**

```bash
docker run -it --env-file .env -v "$(pwd)/output:/app/output" agentic-game-builder
```

**Windows (Command Prompt):**

```bash
docker run -it --env-file .env -v "%cd%\output:/app/output" agentic-game-builder
```

**Windows (PowerShell):**

```bash
docker run -it --env-file .env -v "${PWD}/output:/app/output" agentic-game-builder
```

## 🏗️ Agent Architecture

```
                        ┌──────────────────────────┐
  "Make a space          │    Master Orchestrator    │
   shooter game"  ──────▶│  (While-loop + Pydantic)  │
                        └──────┬───────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ Clarifier │──────▶│  Planner  │──────▶│ Executor  │
    │(Flash Lite)│       │  (Flash)  │       │  (Flash)  │
    └───────────┘       └───────────┘       └─────┬─────┘
     asks 2-4 Qs         JSON design doc          │
     + user Q&A                               generates code
                                                  │
                                                  ▼
                                           ┌───────────┐     ❌ fail
                                           │ Validator  │────────┐
                                           │  (Flash)   │        │ retry
                                           └─────┬─────┘        │ (max 3)
                                                 │               │
                                            ✅ pass        ┌────┘
                                                 │         ▼
                                                 ▼     back to Executor
                                           ┌───────────┐
                                           │  OUTPUT    │
                                           │ index.html │
                                           │ style.css  │
                                           │ game.js    │
                                           └───────────┘
```

### Agent Model Routing

| Agent | Model | Role |
|-------|-------|------|
| **Clarifier** | Gemini 2.5 Flash Lite | Extracts requirements with minimal questions. Highly cost-efficient for conversation. |
| **Planner** | Gemini 2.5 Flash | Creates structured JSON game design document with robust fallback parsing. |
| **Executor** | Gemini 2.5 Flash | Generates complete, playable code (100% dynamic) using an 8K output token window. |
| **Validator** | Gemini 2.5 Flash | Two-layer validation: deterministic structure checks + LLM semantic review. |

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | Custom sequential orchestrator (while-loop) |
| State Management | Pydantic V2 BaseModel |
| LLM Provider | Google Gemini (via google-genai SDK) |
| CLI Interface | Rich (panels, tables, progress bars) |
| Game Frameworks | Phaser 3 / Vanilla JavaScript |
| Containerization | Docker |
| Testing | pytest |

## ⚖️ Trade-Offs Made

### 1. The FinOps Pivot (Cost vs. Raw Capabilities)

I initially architected the system using Anthropic's Claude 3.5 Sonnet and Opus for the Executor agent. While Opus provided excellent zero-shot code generation, telemetry revealed an unsustainable cost-to-performance ratio (averaging $1.50+ per run for simple games), largely due to expensive retry loops. I made the architectural trade-off to pivot the entire stack to the Google Gemini 2.5 API. This dropped the operational cost by over 95% while maintaining generation quality.

### 2. State Machine vs. Autonomous Frameworks

Instead of using heavy, black-box agent frameworks like AutoGen or CrewAI, I implemented a custom Sequential Orchestrator using a while loop and a Pydantic V2 state object. The trade-off is a loss of "autonomous creativity" (agents cannot arbitrarily call each other), but the gain is absolute deterministic control, ensuring the system never loops infinitely or skips the clarification phase.

### 3. Data Privacy vs. Free Tier

To maximize cost-efficiency during development, this system defaults to the Google Gemini API Free Tier. The architectural trade-off is data privacy, as free-tier API data may be used for model training. For a production deployment, the system would require a Paid Tier billing account to ensure Amgo Games' IP remains private.

## 🏆 Technical Win: Solving YAML Hallucination

During development, the Planner agent initially output YAML, but Gemini models frequently hallucinated invalid indentation — causing silent parse failures. Rather than adding fragile post-processing, I made the architectural decision to **migrate the entire Planner pipeline to strict JSON output** with a robust `{`…`}` extraction fallback in `planner.py`. This eliminated the class of errors entirely while keeping the design document fully structured.

## 🔮 Improvements With More Time

- **Native Structured Outputs** — With more time, I would strictly enforce Gemini's `response_schema` API parameter to mathematically guarantee Pydantic validation on the LLM's output, removing the need for regex fallback parsing entirely.

- **Parallel Validation** — The Validator currently runs sequentially after file generation. I would refactor this to run asynchronous syntax linters (like ESLint) in parallel with the LLM semantic review to reduce latency.

- **Streaming UI Responses** — Implementing token streaming in the CLI would significantly improve UX during the Execution phase, giving the user immediate visual feedback while the 10KB+ game code generates.

## 🔄 Error Handling (Self-Healing in Action)

Because LLMs are non-deterministic, generating raw code zero-shot is prone to hallucination. This architecture uses a multi-agent system to achieve "self-healing."

- **`@safe_llm_call` decorator** — wraps all API calls with:
  - Rate-limit / 503 overload → exponential backoff (2ˣ seconds, max 3 retries)
  - Timeout → retry after 5 seconds
  - API errors → logged and re-raised
  - Empty responses → `ValueError`
- **Validation retry loop** — If the Executor mistakenly imports the wrong framework (e.g., Phaser instead of Vanilla JS) or leaves placeholder comments (`// TODO`), the Validator Agent catches the mismatch, rejects the code, and passes the error logs back to the Executor for regeneration.
- **Failed attempts** — saved to `output/failed/` with timestamps for debugging.

## 📁 Project Structure

```
agentic-game-builder/
├── agents/
│   ├── __init__.py          # Package exports
│   ├── clarifier.py         # Requirements extraction (Flash Lite)
│   ├── planner.py           # Game design document (Flash)
│   ├── executor.py          # Code generation (Flash)
│   └── validator.py         # Code validation (Flash)
├── prompts/
│   └── agent_prompts.py     # All prompt templates
├── utils/
│   ├── __init__.py
│   ├── api_helpers.py       # @safe_llm_call, GenAI client
│   ├── file_manager.py      # File I/O, save/failed helpers
│   └── validation.py        # Regex-based code validation
├── tests/
│   ├── test_imports.py      # Module import smoke tests
│   ├── test_orchestrator.py # State, retry, stopping criteria
│   └── test_validation.py   # Validation utility tests
├── output/                  # Generated games (runtime)
├── main.py                  # Rich CLI entry point
├── orchestrator.py          # Custom sequential orchestrator
├── config.py                # Model routing & constants
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── pytest.ini
├── LICENSE
└── README.md
```

## 🧪 Running Tests

```bash
pytest -v
```

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
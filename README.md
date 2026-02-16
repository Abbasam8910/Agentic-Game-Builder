# 🎮 Agentic Game-Builder AI

An intelligent multi-agent system that transforms natural language game ideas into fully playable HTML/CSS/JavaScript games.

## ✨ Features

- **Natural Language Input** — Describe your game idea in plain English
- **Intelligent Clarification** — Asks only necessary questions (max 5-7), never cosmetic details
- **Automatic Framework Selection** — Chooses Phaser 3 or Vanilla JS based on game complexity
- **Complete Code Generation** — Produces three files (HTML, CSS, JS) with no placeholders
- **Two-Layer Validation** — Deterministic regex checks + LLM semantic review
- **Retry Logic** — Auto-retries failed code generation up to 3 times
- **Rich CLI** — Beautiful terminal interface with progress bars, tables, and color-coded output
- **Dockerized** — Ready for containerized deployment

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

### Docker Setup

```bash
# Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Build and run
docker-compose up
```

## 💡 Example Usage

```
🎮 Agentic Game-Builder AI

Enter your game idea:
→ Create a space shooter game

━━━ Phase 1: Requirements Clarification ━━━
❓ A few quick questions …
✅ Requirements gathered successfully!

━━━ Phase 2: Game Planning ━━━
┌───── 📋 Game Design Document ─────┐
│ Title: Space Blaster               │
│ Framework: vanilla-js              │
│ Win Condition: Reach 1000 points   │
└────────────────────────────────────┘

━━━ Phase 3: Code Generation & Validation ━━━
✅ Validation passed!

📁 Generated Files — index.html (1.2 KB), style.css (0.8 KB), game.js (8.5 KB)
✅ Game files saved to: output/space-blaster/
🎉 Game generated successfully!
```

## 🏗️ Agent Architecture

```
┌─────────────────────────────────────────────┐
│     Master Orchestrator                      │
│  (While-loop, Pydantic V2 state)            │
└──────┬──────────┬──────────┬───────────┬────┘
       ▼          ▼          ▼           ▼
  Clarifier   Planner   Executor    Validator
 (Flash Lite) (Flash)    (Pro)      (Flash)
```

### Agent Model Routing

| Agent | Model | Role |
|-------|-------|------|
| **Clarifier** | Gemini 2.5 Flash Lite | Extracts requirements with minimal questions |
| **Planner** | Gemini 2.5 Flash | Creates structured YAML game design document |
| **Executor** | Gemini 2.5 Pro | Generates complete, playable code — 100% dynamic |
| **Validator** | Gemini 2.5 Flash | Two-layer validation: deterministic + LLM review |

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

## 🔄 Error Handling

- **`@safe_llm_call` decorator** — wraps all API calls with:
  - Rate-limit (429) → exponential backoff (2ˣ seconds, max 3 retries)
  - Timeout → retry after 5 seconds
  - API errors → logged and re-raised
  - Empty responses → `ValueError`
- **Retry logic** — validation failures trigger re-execution (max 3 attempts)
- **Failed attempts** — saved to `output/failed/` for debugging

## 📁 Project Structure

```
agentic-game-builder/
├── agents/
│   ├── __init__.py          # Package exports
│   ├── clarifier.py         # Requirements extraction
│   ├── planner.py           # Game design document
│   ├── executor.py          # Code generation
│   └── validator.py         # Code validation
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
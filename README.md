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

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)
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
# Edit .env and add your ANTHROPIC_API_KEY

# Run the agent
python main.py
```

### Docker Setup

```bash
# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Build Docker image
docker build -t agentic-game-builder .

# Run the agent (interactive mode)
docker run -it -v ./output:/app/output --env-file .env agentic-game-builder

# Or use docker-compose
docker-compose up
```

## 💡 Example Usage

```
🎮 Agentic Game-Builder AI

Enter your game idea:
→ Create a space shooter game

━━━ Phase 1: Requirements Clarification ━━━

❓ A few quick questions to refine your game:

1. What type of space game — shooter (destroy enemies), dodge (avoid obstacles), or collection (gather items)?
   → Shooter, destroy alien waves

2. How should the player control the ship — arrow keys, WASD, or mouse?
   → Arrow keys

3. How does the player win — survive for X seconds, reach a score, or defeat all enemies?
   → Reach score of 1000

✅ Requirements gathered successfully!

━━━ Phase 2: Game Planning ━━━

┌──────────────── 📋 Game Design Document ────────────────┐
│ Title            │ Space Blaster                         │
│ Type             │ shooter                               │
│ Framework        │ vanilla-js                            │
│ Win Condition    │ Reach 1000 points                     │
│ Controls         │ ArrowLeft → Move left, ...            │
└──────────────────────────────────────────────────────────┘

━━━ Phase 3: Code Generation & Validation ━━━

✅ Validation passed!

┌───────── 📁 Generated Files ─────────┐
│ File       │ Size                     │
│ index.html │ 1.2 KB                  │
│ style.css  │ 0.8 KB                  │
│ game.js    │ 8.5 KB                  │
└──────────────────────────────────────┘

✅ Game files saved to: output/space-blaster/
Open index.html in your browser to play!

🎉 Game generated successfully!
```

## 🏗️ Agent Architecture

```
┌─────────────────────────────────────────────────┐
│          Master Orchestrator                     │
│  (While-loop pipeline, Pydantic V2 state)       │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────┴────────┬──────────────┬──────────┐
       ▼                ▼              ▼          ▼
┌─────────────┐  ┌─────────────┐  ┌────────┐  ┌────────┐
│ Clarifier   │  │  Planner    │  │Executor│  │Validator│
│ (Haiku)     │  │ (Sonnet)    │  │ (Opus) │  │(Sonnet) │
└─────────────┘  └─────────────┘  └────────┘  └────────┘
```

### Pipeline Flow

```
User Input → Clarifier → [Interactive Q&A] → Planner → Executor → Validator
                                                          ↑           │
                                                          └── retry ──┘
                                                         (max 3 times)
```

### Agent Responsibilities

| Agent | Model | Role |
|-------|-------|------|
| **Clarifier** | Claude Haiku | Extracts requirements with minimal questions (max 5-7). Stopping criteria: ≥3/4 critical fields resolved. |
| **Planner** | Claude Sonnet | Creates structured YAML game design document. Selects framework (Phaser vs Vanilla JS). |
| **Executor** | Claude Opus | Generates complete, playable code — 100% dynamic, no templates. |
| **Validator** | Claude Sonnet | Two-layer validation: deterministic regex + LLM semantic review. |

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | Custom sequential orchestrator (while-loop) |
| State Management | Pydantic V2 BaseModel |
| LLM Provider | Anthropic (direct SDK) |
| CLI Interface | Rich (panels, tables, progress bars) |
| Game Frameworks | Phaser 3 / Vanilla JavaScript |
| Containerization | Docker |
| Testing | pytest |

## 🔄 Error Handling

- **`@safe_llm_call` decorator** — wraps all API calls with:
  - Rate-limit → exponential backoff (2ˣ seconds, max 3 retries)
  - Timeout → retry after 5 seconds
  - API errors → logged and re-raised
  - Empty responses → `ValueError`
- **Retry logic** — validation failures trigger re-execution (max 3 attempts)
- **Failed attempts** — saved to `output/failed/` for debugging

## ⚖️ Trade-Offs

| Decision | Why | Alternative |
|----------|-----|-------------|
| Phaser + Vanilla JS only | Covers 90% of simple game types | Could add Pixi.js, Three.js for 3D |
| Colored shapes for visuals | Simplifies output, avoids asset licensing | Integrate AI image generators |
| Single `game.js` file | No bundler needed, opens directly in browser | Modular code with webpack |
| Simple arcade games | Keeps clarification short, ensures playability | Complex RPG/strategy support |
| Anthropic only | Consistent quality, single API key | Multi-provider fallback |

## 🔮 Future Improvements

1. **Enhanced Validation** — Automated browser testing with Playwright, performance profiling
2. **Asset Integration** — AI-generated sprites and sound effects via APIs
3. **Advanced Planning** — Historical game data to improve framework selection
4. **Deployment** — One-click deploy to GitHub Pages, Netlify, or Vercel
5. **Multiplayer** — WebSocket networking for real-time multiplayer games
6. **Mobile Export** — Cordova/Capacitor wrappers for mobile deployment

## 📁 Project Structure

```
agentic-game-builder/
├── agents/
│   ├── __init__.py          # Package exports
│   ├── clarifier.py         # Requirements extraction (Haiku)
│   ├── planner.py           # Game design document (Sonnet)
│   ├── executor.py          # Code generation (Opus)
│   └── validator.py         # Code validation (Sonnet)
├── prompts/
│   └── agent_prompts.py     # All prompt templates
├── utils/
│   ├── __init__.py          # Package exports
│   ├── api_helpers.py       # @safe_llm_call, Anthropic client
│   ├── file_manager.py      # File I/O, save/failed helpers
│   └── validation.py        # Regex-based code validation
├── tests/
│   ├── test_imports.py      # Module import smoke tests
│   ├── test_orchestrator.py # State, retry, stopping criteria
│   └── test_validation.py   # Validation utility tests
├── output/                  # Generated games (created at runtime)
├── main.py                  # Rich CLI entry point
├── orchestrator.py          # Custom sequential orchestrator
├── config.py                # Model routing, temperatures, constants
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Container orchestration
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── .gitignore               # Git exclusions
├── pytest.ini               # Test configuration
├── LICENSE                  # MIT License
└── README.md                # This file
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_validation.py -v
```

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
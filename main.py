"""
Agentic Game-Builder AI — Main CLI Entry Point

Rich-powered interactive interface that drives the orchestrator pipeline:
  1. Accept game idea from user
  2. Clarification loop (questions + answers)
  3. Planning phase
  4. Execution + validation (with retry)
  5. Output files
"""

import logging
import os
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.theme import Theme

from config import LOG_LEVEL
from orchestrator import GameBuilderOrchestrator

# ---------------------------------------------------------------------------
# Logging setup — RichHandler (console) + FileHandler (agent.log)
# ---------------------------------------------------------------------------

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
})

console = Console(theme=custom_theme)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(
            console=console,
            rich_tracebacks=True,
            show_path=False,
        ),
        logging.FileHandler("agent.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger("game_builder")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def show_banner():
    """Print a fancy startup banner."""
    banner = (
        "[bold cyan]🎮 Agentic Game-Builder AI[/bold cyan]\n"
        "[dim]Transform your game ideas into playable HTML/CSS/JS games[/dim]"
    )
    console.print(Panel(banner, border_style="bright_blue", padding=(1, 2)))
    console.print()


def show_plan_table(plan: dict):
    """Display the game design document in a Rich Table."""
    metadata = plan.get("metadata", {})
    rules = plan.get("game_rules", {})
    tech = plan.get("technical_architecture", {})
    controls = plan.get("controls", {})

    table = Table(
        title="📋 Game Design Document",
        border_style="bright_blue",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Property", style="bold", min_width=20)
    table.add_column("Value", min_width=40)

    table.add_row("Title", str(metadata.get("game_title", "—")))
    table.add_row("Type", str(metadata.get("game_type", "—")))
    table.add_row("Framework", str(metadata.get("framework", "—")))
    table.add_row("Complexity", str(metadata.get("estimated_complexity", "—")))
    table.add_row("Win Condition", str(rules.get("win_condition", "—")))
    table.add_row("Lose Condition", str(rules.get("lose_condition", "—")))
    table.add_row("Scoring", str(rules.get("scoring", "—")))

    # Controls
    kb = controls.get("keyboard", [])
    if kb:
        ctrl_str = ", ".join(
            f"{c.get('key','?')} → {c.get('action','?')}" for c in kb[:5]
        )
        table.add_row("Controls", ctrl_str)

    # Framework choice reasoning
    choice = tech.get("framework_choice", {})
    if choice.get("reasoning"):
        table.add_row("Framework Reasoning", str(choice["reasoning"]))

    console.print(table)
    console.print()


def show_files_summary(files: dict[str, str], output_dir: str):
    """Show a summary of generated files."""
    table = Table(
        title="📁 Generated Files",
        border_style="green",
        show_header=True,
        header_style="bold green",
    )
    table.add_column("File", style="bold")
    table.add_column("Size", justify="right")

    for fname, content in files.items():
        size_kb = len(content.encode("utf-8")) / 1024
        table.add_row(fname, f"{size_kb:.1f} KB")

    console.print(table)
    console.print(
        f"\n[success]✅ Game files saved to:[/success] [bold]{output_dir}[/bold]"
    )
    console.print("[dim]Open index.html in your browser to play![/dim]\n")


# ---------------------------------------------------------------------------
# Interactive clarification loop
# ---------------------------------------------------------------------------

def run_clarification_loop(orchestrator: GameBuilderOrchestrator):
    """
    Present clarification questions to the user and feed answers back
    into the orchestrator until requirements are complete.
    """
    round_num = 0
    max_rounds = 3  # Safety: at most 3 question rounds

    while orchestrator.state.current_phase == "clarifying" and round_num < max_rounds:
        round_num += 1

        # Run clarifier
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Analysing your game idea …", total=None)
            orchestrator._run_clarifier()

        # Check if requirements are already complete
        if orchestrator.state.current_phase != "clarifying":
            break

        questions = orchestrator.state.clarification_questions
        if not questions:
            break

        # Present questions
        console.print(
            "\n[bold yellow]❓ A few quick questions to refine your game:[/bold yellow]\n"
        )
        responses = []
        for i, question in enumerate(questions, 1):
            console.print(f"[cyan]{i}.[/cyan] {question}")
            answer = input("   → ").strip()
            if not answer:
                answer = "No preference, use your best judgement."
            responses.append(answer)

        console.print()

        # Feed answers back
        orchestrator.resume_after_clarification(responses)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    show_banner()

    # Get game idea
    console.print("[bold]Enter your game idea:[/bold]")
    user_input = input("→ ").strip()

    if not user_input:
        console.print("[error]No input provided. Exiting.[/error]")
        sys.exit(1)

    logger.info("User input: %s", user_input)
    console.print()

    # Create orchestrator
    orchestrator = GameBuilderOrchestrator()
    orchestrator.state = __import__("orchestrator").GameBuilderState(user_input=user_input)

    # Phase 1: Clarification
    console.print(Panel("[bold cyan]Phase 1: Requirements Clarification[/bold cyan]", border_style="cyan"))
    run_clarification_loop(orchestrator)

    if orchestrator.state.requirements:
        console.print("[success]✅ Requirements gathered successfully![/success]\n")
    else:
        console.print("[warning]⚠️  Proceeding with limited requirements.[/warning]\n")

    # Phase 2: Planning
    console.print(Panel("[bold cyan]Phase 2: Game Planning[/bold cyan]", border_style="cyan"))
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Designing your game architecture …", total=None)
        orchestrator._run_planner()

    if orchestrator.state.game_plan:
        show_plan_table(orchestrator.state.game_plan)

    # Phase 3 & 4: Execution + Validation (with retry loop)
    console.print(Panel("[bold cyan]Phase 3: Code Generation & Validation[/bold cyan]", border_style="cyan"))

    while not orchestrator.state.is_complete:
        phase = orchestrator.state.current_phase

        if phase == "executing":
            attempt = orchestrator.state.retry_count + 1
            label = f"Generating game code (attempt {attempt}) …"
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(label, total=None)
                orchestrator._run_executor()

        elif phase == "validating":
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task("Validating generated code …", total=None)
                orchestrator._run_validator()

            if not orchestrator.state.is_complete:
                vr = orchestrator.state.validation_result or {}
                issues = vr.get("issues", [])
                if issues:
                    console.print("[warning]⚠️  Validation issues found:[/warning]")
                    for issue in issues:
                        console.print(f"   [yellow]• {issue}[/yellow]")
                    console.print()
        else:
            break

    # Final output
    console.print()
    if orchestrator.state.generated_files:
        from utils.file_manager import save_game_files
        title = "generated-game"
        if orchestrator.state.game_plan:
            title = orchestrator.state.game_plan.get("metadata", {}).get("game_title", title)
        output_dir = os.path.join(
            os.path.dirname(__file__), "output",
            title.lower().strip().replace(" ", "-"),
        )
        show_files_summary(orchestrator.state.generated_files, output_dir)
    else:
        console.print("[error]❌ No game files were generated.[/error]")

    vr = orchestrator.state.validation_result or {}
    if vr.get("is_valid"):
        console.print("[success]🎉 Game generated successfully![/success]")
    else:
        console.print(
            "[warning]⚠️  Game saved with validation warnings. "
            "It may still be playable — try opening it![/warning]"
        )


if __name__ == "__main__":
    main()

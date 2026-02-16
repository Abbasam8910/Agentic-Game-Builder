"""
Test: Code validation utilities.
"""

import pytest
from utils.validation import (
    extract_code_blocks,
    check_completeness,
    validate_html_structure,
    validate_js_structure,
    check_framework_consistency,
    run_all_checks,
)


# ---------------------------------------------------------------------------
# extract_code_blocks
# ---------------------------------------------------------------------------

class TestExtractCodeBlocks:
    def test_single_block(self):
        text = "Some text\n```javascript\nconsole.log('hi');\n```\nMore text"
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert "console.log" in blocks[0]

    def test_multiple_blocks(self):
        text = (
            "```html\n<h1>Test</h1>\n```\n"
            "text\n"
            "```css\nbody { margin: 0; }\n```\n"
            "```js\nalert(1);\n```"
        )
        blocks = extract_code_blocks(text)
        assert len(blocks) == 3

    def test_no_blocks(self):
        blocks = extract_code_blocks("no code here")
        assert len(blocks) == 0

    def test_case_insensitive(self):
        text = "```HTML\n<div></div>\n```"
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1


# ---------------------------------------------------------------------------
# check_completeness
# ---------------------------------------------------------------------------

class TestCheckCompleteness:
    def test_clean_code(self):
        ok, issues = check_completeness("function update() { doStuff(); }")
        assert ok is True
        assert issues == []

    def test_todo_detected(self):
        ok, issues = check_completeness("function update() { // TODO implement }")
        assert ok is False
        assert any("TODO" in i for i in issues)

    def test_placeholder_detected(self):
        ok, issues = check_completeness("var x = PLACEHOLDER;")
        assert ok is False

    def test_empty_function(self):
        ok, issues = check_completeness("function update() {}")
        assert ok is False


# ---------------------------------------------------------------------------
# validate_html_structure
# ---------------------------------------------------------------------------

class TestValidateHtml:
    def test_valid_html(self):
        html = '<!DOCTYPE html><html><body><canvas id="c"></canvas><script src="game.js"></script></body></html>'
        ok, issues = validate_html_structure(html)
        assert ok is True

    def test_missing_doctype(self):
        html = '<html><body><canvas></canvas><script></script></body></html>'
        ok, issues = validate_html_structure(html)
        assert ok is False
        assert any("DOCTYPE" in i for i in issues)

    def test_missing_canvas(self):
        html = '<!DOCTYPE html><html><body><script></script></body></html>'
        ok, issues = validate_html_structure(html)
        assert ok is False


# ---------------------------------------------------------------------------
# validate_js_structure
# ---------------------------------------------------------------------------

class TestValidateJs:
    def test_valid_vanilla_js(self):
        js = 'document.addEventListener("keydown", handler); requestAnimationFrame(loop);'
        ok, issues = validate_js_structure(js)
        assert ok is True

    def test_valid_phaser_js(self):
        js = 'const game = new Phaser.Game(config); this.input.keyboard.on("keydown", cb);'
        ok, issues = validate_js_structure(js)
        assert ok is True

    def test_missing_game_loop(self):
        js = 'var x = 5;'
        ok, issues = validate_js_structure(js)
        assert ok is False

    def test_missing_events(self):
        js = 'requestAnimationFrame(loop);'
        ok, issues = validate_js_structure(js)
        assert ok is False


# ---------------------------------------------------------------------------
# check_framework_consistency
# ---------------------------------------------------------------------------

class TestFrameworkConsistency:
    def test_phaser_consistent(self):
        plan = {"technical_architecture": {"framework_choice": {"selected": "phaser"}}}
        html = '<script src="phaser.min.js"></script>'
        js = 'const game = new Phaser.Game(config);'
        ok, issues = check_framework_consistency(plan, html, js)
        assert ok is True

    def test_phaser_mismatch(self):
        plan = {"technical_architecture": {"framework_choice": {"selected": "phaser"}}}
        html = "<html></html>"
        js = "requestAnimationFrame(loop);"
        ok, issues = check_framework_consistency(plan, html, js)
        assert ok is False

    def test_vanilla_consistent(self):
        plan = {"technical_architecture": {"framework_choice": {"selected": "vanilla-js"}}}
        js = "requestAnimationFrame(loop);"
        ok, issues = check_framework_consistency(plan, "<html></html>", js)
        assert ok is True


# ---------------------------------------------------------------------------
# run_all_checks
# ---------------------------------------------------------------------------

class TestRunAllChecks:
    def test_missing_file(self):
        files = {"index.html": "<html>", "style.css": "body {}"}
        ok, issues = run_all_checks(files)
        assert ok is False
        assert any("game.js" in i for i in issues)

    def test_empty_file(self):
        files = {"index.html": "", "style.css": "body {}", "game.js": "code here"}
        ok, issues = run_all_checks(files)
        assert ok is False

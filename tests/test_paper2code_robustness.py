from pathlib import Path
from types import SimpleNamespace

from bookworm.paper2code import pipeline
from bookworm.paper2code.validation import ValidationResult


def test_failure_signature_ignores_timing_but_tracks_nodes():
    base = "FAILED tests/test_x.py::test_a\n"
    a = ValidationResult(ok=False, log=base + "=== 1 failed in 0.70s ===", failed_files=["tests/test_x.py"])
    b = ValidationResult(ok=False, log=base + "=== 1 failed in 9.91s ===", failed_files=["tests/test_x.py"])
    assert _sig(a) == _sig(b)          # timing ignored
    c = ValidationResult(ok=False, log="FAILED tests/test_x.py::test_b\n", failed_files=["tests/test_x.py"])
    assert _sig(a) != _sig(c)          # node change tracked


def _sig(result):
    return pipeline._failure_signature(result)


def test_coding_prompt_demands_invariants_for_tests_only():
    from bookworm.paper2code import prompts
    args = dict(
        paper_text="p", overall_plan="o", success_criteria="s",
        logic_design="l", file_analysis="a", prior_files={},
    )
    test_prompt = prompts.coding_prompt(filename="tests/test_solver.py", **args)
    prod_prompt = prompts.coding_prompt(filename="solver.py", **args)
    assert "INVARIANTS" in test_prompt          # test files steered to invariants
    assert "hallucinated" in test_prompt
    assert "INVARIANTS" not in prod_prompt       # production files untouched


def test_success_criteria_prompt_carries_invariant_field():
    from bookworm.paper2code import prompts
    prompt = prompts.success_criteria_prompt(paper_text="p", overall_plan="o")
    assert '"invariant"' in prompt                # criteria shape requests an invariant
    assert "invariant-based criteria" in prompt   # and the rule prefers them


def test_loop_keeps_best_and_stops_on_revisit(monkeypatch, tmp_path):
    """Validation goes fail-A -> regress-B -> fail-A. The loop must NOT carry the
    regression forward, must stop on the revisited signature, and must ship/report
    the better state (A's two tests), never B's third failure."""
    # Seed the artifact cache so every planning/coding stage is skipped (no LLM).
    canned = {
        "overall_plan.txt": "plan",
        "success_criteria.json": "{}",
        "architecture.txt": '{"files": [{"name": "solver.py", "description": "d"}]}',
        "logic_design.txt": '{"task_list": ["solver.py"], "logic": {"solver.py": "l"}, "packages": []}',
        "analysis/solver.py.txt": "analysis",
        "code/solver.py.txt": "print('v1')",
    }
    monkeypatch.setattr(pipeline.artifacts, "load", lambda _dir, name: canned.get(name))
    monkeypatch.setattr(pipeline.artifacts, "save", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "extract_text", lambda _p: "paper")

    a = ValidationResult(
        ok=False,
        log="FAILED solver.py::test_1\nFAILED solver.py::test_2\n=== 2 failed in 0.1s ===",
        failed_files=["solver.py"],
    )
    b = ValidationResult(  # regression: more failures, bigger signature
        ok=False,
        log="FAILED solver.py::test_1\nFAILED solver.py::test_2\nFAILED solver.py::test_3\n=== 3 failed in 9.9s ===",
        failed_files=["solver.py", "helper.py"],
    )
    scripted = iter([a, b, a])
    monkeypatch.setattr(pipeline, "_run_validation", lambda _dir: next(scripted))
    monkeypatch.setattr(
        pipeline, "_triage_failure",
        lambda **k: {"failures": [{"classification": "implementation_bug", "affected_files": ["solver.py"]}]},
    )
    monkeypatch.setattr(pipeline, "_llm", lambda *a, **k: "```python\nprint('patched')\n```")

    config = SimpleNamespace(working_dir=tmp_path, llm_model="test")
    report = pipeline.run_pipeline(
        client=None, config=config, paper_path=Path("Demo.pdf"), output_dir=tmp_path / "out"
    )

    assert "Validation: stalled" in report                 # revisit stopped the loop
    assert "FAILED solver.py::test_1" in report            # best state's failures reported
    assert "FAILED solver.py::test_2" in report
    assert "test_3" not in report                          # regression (B) was not adopted

"""The GitHub Actions files point at this repository and pin every action to a commit."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
UPSTREAM = "Rizzo-AI-Academy/rizzo-flow"
USES = re.compile(r"^\s*-?\s*uses:\s*(?P<action>\S+)", re.MULTILINE)
PINNED = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")


def test_there_are_workflows_to_check():
    assert {path.name for path in WORKFLOWS} >= {"ci.yml", "scorecard.yml"}


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda path: path.name)
def test_every_action_is_pinned_to_a_full_commit(path):
    actions = USES.findall(path.read_text(encoding="utf-8"))
    assert actions, "the workflow uses no action"
    assert [action for action in actions if not PINNED.match(action)] == []


@pytest.mark.parametrize(
    "path", [*WORKFLOWS, ROOT / ".github" / "dependabot.yml"], ids=lambda path: path.name
)
def test_the_automation_does_not_name_the_upstream_repository(path):
    # A copy of upstream's file that still names upstream would run, or publish, for the wrong one.
    assert UPSTREAM not in path.read_text(encoding="utf-8")


def test_the_scorecard_job_runs_only_in_this_repository():
    text = (ROOT / ".github" / "workflows" / "scorecard.yml").read_text(encoding="utf-8")
    assert "if: github.repository == 'Axiumine/quillpick'" in text


def test_the_scorecard_badge_in_the_readme_is_this_repositorys():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "api.scorecard.dev/projects/github.com/Axiumine/quillpick/badge" in readme
    assert "scorecard.dev/viewer/?uri=github.com/Axiumine/quillpick" in readme

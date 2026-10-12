"""The starter: the setup check runs, and every design-pack template is there with its parts."""

from pathlib import Path

import pytest

from scripts.check_setup import checks

TEMPLATES = Path(__file__).resolve().parent.parent / "docs" / "templates"
REQUIRED = {
    "project-brief.md": ["## User and decision", "## Non-goals", "## Track"],
    "acceptance-criteria.md": ["## Required behaviour", "## Quality thresholds", "## Access control", "## Budget"],
    "evidence-plan.md": ["## Claims and evidence", "## Held-out questions"],
    "data-card.md": ["## Source and permission", "## Deliberate difficulties"],
    "architecture.md": ["## Components", "## Contracts", "## Data model", "## Ingestion states"],
    "threat-and-cost.md": ["## Trust boundaries", "## Tenant isolation rules", "## Budget"],
    "evaluation-report.md": ["## Held-out results", "## Error categories", "## Baseline and candidate"],
    "demo-script.md": ["## The user problem", "## A failure case", "## One trade-off"],
    "portfolio-checklist.md": ["## Claims and their evidence"],
}


def test_the_setup_check_runs():
    names = [name for name, _, _ in checks()]
    assert names[0] == "Python 3.12 or newer" and "Design-pack templates" in names


@pytest.mark.parametrize("name", sorted(REQUIRED))
def test_every_template_has_its_parts(name):
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    for heading in REQUIRED[name]:
        assert heading in text, f"{name}: {heading}"

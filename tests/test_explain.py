"""New detectors and adapters must ship an explanation, not rely on the display fallback."""

import ast
from pathlib import Path

import pytest

from tests.test_backends_contract import CASES, FIX, recorded
from unpick import backends, checks, judges, scan
from unpick.explain import BACKEND_EXPLANATIONS, EXPLANATIONS, get_explanation


def test_every_emitted_rule_has_an_entry():
    expected = {mod.RULE_ID for mod in checks.all_checks()} | {scan.UNREAD_RULE}
    expected |= set(judges.CATEGORIES) - {"OTHER"}
    # Also discover literal IDs emitted outside the registered checks (e.g. review failures).
    for module in (scan, judges):
        tree = ast.parse(Path(module.__file__).read_text())
        expected |= {n.value for n in ast.walk(tree)
                     if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("RT-")}
    assert expected <= EXPLANATIONS.keys(), expected - EXPLANATIONS.keys()
    assert backends.adapters().keys() == BACKEND_EXPLANATIONS.keys()
    for name in backends.adapters():
        assert get_explanation(f"{name}:future-rule") == BACKEND_EXPLANATIONS[name]


@pytest.mark.parametrize("name", CASES)
def test_recorded_external_findings_have_explanations(name):
    folder, target = CASES[name]
    for finding in backends.adapters()[name].parse(recorded(folder), FIX / folder / target):
        assert get_explanation(finding.rule_id).what_to_do


def test_explanations_are_short_and_actionable():
    for entry in [*EXPLANATIONS.values(), *BACKEND_EXPLANATIONS.values()]:
        assert 1 <= len(entry.title.split()) <= 8
        assert entry.what_it_means.endswith(".")
        assert entry.what_to_do.endswith(".")


def test_unknown_rules_are_not_silently_registered():
    with pytest.raises(KeyError):
        get_explanation("RT-NEW-RULE")

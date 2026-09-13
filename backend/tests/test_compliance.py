from types import SimpleNamespace

from apps.compliance.services.rules import run_compliance_rules


def test_cease_and_desist_and_legal():
    segments = [
        SimpleNamespace(line_number=1, text="Hello from collections"),
        SimpleNamespace(line_number=2, text="Please stop calling. I have an attorney."),
        SimpleNamespace(line_number=3, string="ok"),
    ]
    segments[2].text = "Any settlement needs supervisor approval."
    hits = run_compliance_rules(segments)
    cats = {h.category for h in hits}
    assert "CEASE_AND_DESIST" in cats
    assert "LEGAL_MENTION" in cats
    assert "SETTLEMENT_APPROVAL" in cats

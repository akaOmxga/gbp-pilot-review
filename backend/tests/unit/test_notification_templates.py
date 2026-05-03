from app.services.notification_templates import render


def test_render_known_event() -> None:
    subject, html, text = render("publish_failed", {"failure_reason": "boom"})
    assert "boom" in text
    assert "boom" in html
    assert "Échec" in subject


def test_render_unknown_event_falls_back() -> None:
    subject, _html, _text = render("xxx_does_not_exist", {})
    assert "génération" in subject.lower() or "ia" in subject.lower()


def test_render_missing_var_does_not_crash() -> None:
    subject, _html, _text = render("publish_failed", {})
    assert subject  # no KeyError, missing var rendered as ""

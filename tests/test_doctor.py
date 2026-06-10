def test_doctor_importa():
    """Verifica se o módulo doctor importa sem erros."""
    from jarvis.doctor import build_report

    report = build_report()
    assert isinstance(report, dict)
    assert "whisper" in report
    assert "llm" in report
    assert "cloud_keys" in report

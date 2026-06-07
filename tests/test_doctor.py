from __future__ import annotations

import doctor


def test_doctor_reports_missing_ocr(monkeypatch) -> None:
    monkeypatch.setattr(
        doctor,
        "check_ocr",
        lambda languages: {
            "executable": None,
            "requested_languages": ["chi_sim", "eng"],
            "installed_languages": [],
            "missing_languages": ["chi_sim", "eng"],
            "ready": False,
        },
    )
    report = doctor.run_doctor()
    assert report["ready"] is False
    assert "Tesseract: 缺失" in doctor.format_report(report)

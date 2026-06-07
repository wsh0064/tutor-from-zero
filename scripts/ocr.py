"""Local OCR helpers for scanned course materials."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance, ImageOps


DEFAULT_LANGUAGES = "chi_sim+eng"


def tesseract_executable() -> str | None:
    """Return the Tesseract executable path when available."""
    return shutil.which("tesseract")


def available_languages() -> set[str]:
    """Return installed Tesseract language identifiers."""
    if not tesseract_executable():
        return set()
    import pytesseract

    try:
        return set(pytesseract.get_languages(config=""))
    except Exception:
        return set()


def check_ocr(languages: str = DEFAULT_LANGUAGES) -> dict[str, Any]:
    """Describe whether the OCR runtime can satisfy a language request."""
    requested = {item for item in languages.split("+") if item}
    installed = available_languages()
    missing = sorted(requested - installed)
    return {
        "executable": tesseract_executable(),
        "requested_languages": sorted(requested),
        "installed_languages": sorted(installed),
        "missing_languages": missing,
        "ready": bool(tesseract_executable()) and not missing,
    }


def preprocess_image(image: Image.Image) -> Image.Image:
    """Improve common slide, screenshot, and scanned-page OCR inputs."""
    image = ImageOps.exif_transpose(image).convert("L")
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Contrast(image).enhance(1.5)
    if max(image.size) < 1800:
        image = image.resize((image.width * 2, image.height * 2))
    return image


def ocr_image(
    image_or_path: Image.Image | str | Path,
    languages: str = DEFAULT_LANGUAGES,
    timeout: int = 90,
) -> dict[str, Any]:
    """OCR one image and return text plus mean confidence."""
    status = check_ocr(languages)
    if not status["ready"]:
        missing = ", ".join(status["missing_languages"]) or "Tesseract executable"
        raise RuntimeError(f"OCR runtime is not ready; missing: {missing}")

    import pytesseract
    from pytesseract import Output

    image = (
        image_or_path.copy()
        if isinstance(image_or_path, Image.Image)
        else Image.open(image_or_path)
    )
    image = preprocess_image(image)
    data = pytesseract.image_to_data(
        image,
        lang=languages,
        config="--oem 3 --psm 6",
        output_type=Output.DICT,
        timeout=timeout,
    )
    words: list[str] = []
    confidences: list[float] = []
    for text, confidence in zip(data["text"], data["conf"]):
        text = text.strip()
        try:
            score = float(confidence)
        except (TypeError, ValueError):
            score = -1
        if text:
            words.append(text)
        if score >= 0:
            confidences.append(score)
    return {
        "text": " ".join(words),
        "confidence": round(sum(confidences) / len(confidences), 2)
        if confidences
        else None,
        "word_count": len(words),
        "languages": languages,
    }

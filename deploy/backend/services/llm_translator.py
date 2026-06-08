from ..config import get_settings
from .label_display import display_label


settings = get_settings()


def fallback_translation(labels: list[str]) -> str:
    return " ".join(display_label(label).replace("_", " ") for label in labels).strip()


def translate_labels(labels: list[str]) -> dict:
    clean_labels = [label.strip() for label in labels if label.strip()]
    display_labels = [display_label(label) for label in clean_labels]
    if not clean_labels:
        return {"sentence": "", "provider": "fallback", "enabled": settings.openai_enabled}
    if not settings.openai_enabled or not settings.openai_api_key:
        return {"sentence": fallback_translation(clean_labels), "provider": "fallback", "enabled": False}

    from openai import OpenAI, OpenAIError

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        prompt = (
            "Bạn là hệ thống hỗ trợ dịch nhãn Ngôn ngữ Ký hiệu Việt Nam thành một câu "
            "tiếng Việt tự nhiên, ngắn gọn. Không thêm thông tin ngoài các nhãn đầu vào. "
            f"Nhãn đầu vào theo thứ tự nhận diện: {display_labels}"
        )
        response = client.responses.create(model=settings.openai_model, input=prompt)
        return {"sentence": response.output_text.strip(), "provider": "openai", "enabled": True}
    except OpenAIError as exc:
        return {
            "sentence": fallback_translation(clean_labels),
            "provider": "fallback",
            "enabled": True,
            "warning": f"OpenAI unavailable: {type(exc).__name__}",
        }

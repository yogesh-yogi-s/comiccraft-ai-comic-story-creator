import os
import io
from unittest.mock import Mock, patch
from PIL import Image
from app.image_generator import _build_comic_prompt, generate_image, sanitize_filename


def test_sanitize_filename():
    raw_prompt = "A Brave Fox, in an ENCHANTED Forest! @#$%"
    filename = sanitize_filename(raw_prompt, panel_num=2)
    assert filename.startswith("panel_2_")
    assert filename.endswith(".png")
    assert "@" not in filename
    assert "#" not in filename


def test_build_comic_prompt_normalizes_non_text_input():
    result = _build_comic_prompt({"scene": "heroic entrance"}, "comic book")
    assert isinstance(result, str)
    assert "heroic entrance" in result


def test_generate_image_creates_file():
    prompt = "Rusty leaping over glowing crystal stream, comic style"
    image_url = generate_image(prompt=prompt, art_style="comic book", panel_num=1)

    assert image_url.startswith("/static/panels/")
    assert image_url.endswith(".png")

    local_path = image_url.lstrip("/")
    assert os.path.exists(local_path)
    assert os.path.getsize(local_path) > 1000  # valid image file generated


def test_generate_image_uses_huggingface_token(monkeypatch):
    monkeypatch.setenv("HF_API_KEY", "hf_test_token")
    image_bytes = io.BytesIO()
    Image.new("RGB", (64, 64), "red").save(image_bytes, format="PNG")
    response = Mock(status_code=200, content=image_bytes.getvalue(), headers={"content-type": "image/png"})

    with patch("app.image_generator.requests.post", return_value=response) as post:
        with patch("app.image_generator._generate_via_pollinations") as fallback:
            image_url = generate_image("test comic hero", panel_num=1)

    assert image_url.startswith("/static/panels/")
    post.assert_called_once()
    fallback.assert_not_called()

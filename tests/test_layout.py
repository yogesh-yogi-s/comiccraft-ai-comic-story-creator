import os
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf


def test_build_comic_layout_and_pdf_export():
    outline = [
        {"panel": 1, "title": "The Start", "description": "Standing tall", "prompt": "p1 prompt"},
        {"panel": 2, "title": "The Climb", "description": "Climbing hill", "prompt": "p2 prompt"}
    ]
    story = {
        "panels": [
            {"panel": 1, "caption": "WHOOSH", "narration": "Wind blows", "dialogue": "Let's go!"},
            {"panel": 2, "caption": "CRUMBLE", "narration": "Rocks fall", "dialogue": "Hold on!"}
        ]
    }
    image_paths = [
        "/static/panels/test_p1.png",
        "/static/panels/test_p2.png"
    ]

    layout = build_comic_layout(outline, story, image_paths)
    assert len(layout) == 2
    assert layout[0]["panel"] == 1
    assert layout[0]["title"] == "The Start"
    assert layout[0]["dialogue"] == "Let's go!"
    assert layout[0]["image_path"] == "/static/panels/test_p1.png"

    # Test PDF generation
    pdf_url = save_pdf(layout, story_title="Test Chronicle", character_name="Rusty")
    assert pdf_url.startswith("/static/exports/")
    assert pdf_url.endswith(".pdf")

    local_pdf = pdf_url.lstrip("/")
    assert os.path.exists(local_pdf)
    assert os.path.getsize(local_pdf) > 500

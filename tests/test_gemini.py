from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story


def test_generate_outline_structure():
    prompt = "A brave fox exploring an enchanted forest"
    character_name = "Rusty"
    setting = "Enchanted Forest"
    tone = "Epic Adventure"
    art_style = "Comic Book Classic"

    outline = generate_outline(prompt, character_name, setting, tone, art_style)
    
    assert isinstance(outline, list)
    assert len(outline) == 5

    for i, panel in enumerate(outline, start=1):
        assert "panel" in panel
        assert panel["panel"] == i
        assert "title" in panel
        assert len(panel["title"]) > 0
        assert "description" in panel
        assert "prompt" in panel


def test_generate_story_structure():
    outline = [
        {"panel": 1, "title": "The Awakening", "description": "Rusty enters the forest", "prompt": "fox in forest"},
        {"panel": 2, "title": "Deep Woods", "description": "Ancient ruins ahead", "prompt": "ancient ruins"},
        {"panel": 3, "title": "The Encounter", "description": "A spirit appears", "prompt": "glowing spirit"},
        {"panel": 4, "title": "The Challenge", "description": "Solving the puzzle", "prompt": "puzzle challenge"},
        {"panel": 5, "title": "The Dawn", "description": "Triumph and dawn", "prompt": "sunrise over woods"}
    ]
    character_name = "Rusty"
    tone = "Dramatic"
    art_style = "Anime"

    story = generate_story(outline, character_name, tone, art_style)

    assert isinstance(story, dict)
    assert "panels" in story
    assert "full_text" in story
    assert len(story["panels"]) == 5

    for p in story["panels"]:
        assert "panel" in p
        assert "title" in p
        assert "narration" in p
        assert "caption" in p
        assert "dialogue" in p

import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "Comic Craft" in response.text or "ComicCraft" in response.text
    assert "Story Prompt" in response.text


def test_health_route():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "storage" in data


def test_test_image_route():
    response = client.get("/test-image?prompt=test%20warrior")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["image_url"].startswith("/static/panels/")


def test_generate_comic_form_submission():
    form_data = {
        "story_prompt": "A brave fox exploring an enchanted forest",
        "character_name": "Rusty",
        "setting": "Enchanted Ancient Forest",
        "story_tone": "Epic Adventure",
        "art_style": "Comic Book Classic"
    }
    response = client.post("/generate", data=form_data)
    assert response.status_code == 200
    assert "Finished Comic" in response.text
    assert "Rusty" in response.text
    assert "Download Your Comic as PDF" in response.text


def test_generate_comic_json_api():
    payload = {
        "story_prompt": "A cyber samurai in neo tokyo",
        "character_name": "Kenji",
        "setting": "Neo Tokyo",
        "story_tone": "Dramatic",
        "art_style": "Cyberpunk Neon"
    }
    response = client.post("/generate-comic/json", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["character_name"] == "Kenji"
    assert len(data["layout"]) == 5
    assert data["pdf_path"].endswith(".pdf")


def test_export_success_route():
    response = client.get("/export-success?pdf_url=/static/exports/comic_test.pdf&title=Test")
    assert response.status_code == 200
    assert "Your Comic PDF Is Ready" in response.text

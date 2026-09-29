import logging
import os
from typing import Optional
from fastapi import APIRouter, Form, HTTPException, Request, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.gemini_flash import generate_outline, generate_full_comic
from app.gemini_pro import generate_story
from app.image_generator import generate_image, generate_comic_panels, _get_hf_api_key
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


class PromptRequest(BaseModel):
    story_prompt: str = Field(..., description="Main story premise or idea")
    character_name: str = Field(..., description="Hero or protagonist name")
    setting: str = Field(..., description="Location or environment")
    story_tone: str = Field("Dramatic", description="Mood or narrative tone")
    art_style: str = Field("Comic Book Classic", description="Visual comic art style")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Loads the homepage with the comic generation studio form."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "ComicCraft | AI Comic Story Creator"
        }
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic_form(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    story_tone: str = Form(...),
    art_style: str = Form(...)
):
    """
    Handles form submission from index.html:
    1. Generates 5-panel outline via Gemini Flash
    2. Writes narrative story & dialogues via Gemini Pro
    3. Generates comic illustrations for each panel
    4. Assembles layout
    5. Exports to PDF
    6. Renders comic_preview.html
    """
    try:
        logger.info("Generating comic for prompt: '%s', character: '%s'", story_prompt[:40], character_name)

        # 1 & 2. Single Consolidated Gemini Generation (Strictly 1 API Credit)
        outline, story = generate_full_comic(
            prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=story_tone,
            art_style=art_style
        )

        # 3. High-Clarity Batch Panel Illustrations (AI Horde with cel-shaded styling)
        image_paths = generate_comic_panels(
            panels_data=outline,
            art_style=art_style
        )

        # 4. Comic Layout
        layout = build_comic_layout(outline, story, image_paths)

        # 5. Export to PDF
        pdf_path = save_pdf(
            layout=layout,
            story_title=story_prompt[:36],
            character_name=character_name,
            tone=story_tone,
            art_style=art_style
        )

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "pdf_path": pdf_path,
                "story_prompt": story_prompt,
                "character_name": character_name,
                "setting": setting,
                "story_tone": story_tone,
                "art_style": art_style,
                "story_title": story_prompt
            }
        )

    except Exception as e:
        logger.error("Failed to generate comic: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate comic: {str(e)}")


@router.post("/generate-comic/json")
async def generate_comic_json(payload: PromptRequest):
    """
    API endpoint for headless or external consumers:
    Accepts JSON payload, executes full generation pipeline,
    and returns structured layout and PDF URL.
    """
    try:
        # 1 & 2. Single Consolidated Gemini Generation (Strictly 1 API Credit)
        outline, story = generate_full_comic(
            prompt=payload.story_prompt,
            character_name=payload.character_name,
            setting=payload.setting,
            tone=payload.story_tone,
            art_style=payload.art_style
        )

        # 3. High-Clarity Batch Panel Illustrations (AI Horde with cel-shaded styling)
        image_paths = generate_comic_panels(
            panels_data=outline,
            art_style=payload.art_style
        )

        layout = build_comic_layout(outline, story, image_paths)

        pdf_path = save_pdf(
            layout=layout,
            story_title=payload.story_prompt[:36],
            character_name=payload.character_name,
            tone=payload.story_tone,
            art_style=payload.art_style
        )

        return {
            "status": "success",
            "character_name": payload.character_name,
            "setting": payload.setting,
            "story_tone": payload.story_tone,
            "art_style": payload.art_style,
            "pdf_path": pdf_path,
            "layout": layout
        }
    except Exception as e:
        logger.error("JSON comic generation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(
    request: Request,
    pdf_url: str = Query("/static/exports/", description="Path to generated PDF file"),
    title: str = Query("AI Comic Chronicle", description="Title of the comic")
):
    """Displays export confirmation and direct download link."""
    filename = os.path.basename(pdf_url)
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_url": pdf_url,
            "filename": filename,
            "title": title
        }
    )


@router.get("/download/{filename}")
async def download_pdf(filename: str):
    """Direct PDF download endpoint."""
    file_path = os.path.join("static", "exports", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested comic PDF was not found.")
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename
    )


@router.get("/test-image")
async def test_image(prompt: str = Query("heroic cybernetic warrior gazing at neon city", description="Test prompt")):
    """Developer utility route to verify image generation."""
    try:
        img_path = generate_image(prompt=prompt, art_style="comic book", panel_num=1)
        return {
            "status": "success",
            "prompt": prompt,
            "image_url": img_path
        }
    except Exception as e:
        logger.error("Image generation test failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint displaying system readiness and API key status."""
    gemini_key = bool(os.getenv("GEMINI_API_KEY", "").strip())
    hf_key = bool(_get_hf_api_key())
    return {
        "status": "online",
        "service": "ComicCraft AI Story Creator",
        "gemini_api_configured": gemini_key,
        "huggingface_api_configured": hf_key,
        "image_provider": "huggingface" if hf_key else "fallback",
        "storage": {
            "panels_directory": os.path.exists(os.path.join("static", "panels")),
            "exports_directory": os.path.exists(os.path.join("static", "exports"))
        }
    }

import json
import logging
import os
import re
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip(' "\'')
PRO_MODEL_NAME = os.getenv("GEMINI_PRO_MODEL", "gemini-3.8-flash").strip()

try:
    from google import genai
    from google.genai import types as genai_types
    _client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception as e:
    logger.warning("Could not initialize google-genai: %s", e)
    genai = None
    genai_types = None
    _client = None


def _get_fallback_story(outline: List[Dict[str, Any]], character_name: str, tone: str, art_style: str) -> Dict[str, Any]:
    """Provides customized narrative script reflecting the outline panels."""
    hero = character_name.strip() or "The Wanderer"
    panels_story = []
    formatted_texts = []

    for i, panel in enumerate(outline, start=1):
        p_num = panel.get("panel", i)
        p_title = panel.get("title", f"Panel {p_num}")
        p_desc = panel.get("description", "")

        # Dynamic captions and dialogues matching the panel title/description
        if i == 1:
            cap = "THE STAGE IS SET..."
            narr = f"At the center of it all, {hero} steps forward into the bustling atmosphere. {p_desc}"
            diag = f'{hero}: "Here we go! Let\'s see what happens next."'
        elif i == 2:
            cap = "ENERGY CRACKLES ACROSS THE SCENE!"
            narr = f"Things quickly gain momentum. {p_desc} Every moment brings unexpected discoveries."
            diag = f'{hero}: "I didn\'t expect this to happen, but I\'m not turning back!"'
        elif i == 3:
            cap = "A SUDDEN SHOCK ECHOES OUT!"
            narr = f"Without warning, the situation changes in an instant. {p_desc}"
            diag = f'{hero}: "Wait, look out! What was that?!"'
        elif i == 4:
            cap = "CLASH OF FORCES!"
            narr = f"Surging into action, {hero} meets the challenge head-on with full determination and strength. {p_desc}"
            diag = f'{hero}: "Believe it! We can overcome this together!"'
        else:
            cap = "THE DUST SETTLES UNDER THE SUNSET..."
            narr = f"With the trial behind them, smiles and camaraderie fill the air. {p_desc}"
            diag = f'{hero}: "That was legendary! Ready for the next adventure?"'

        panel_entry = {
            "panel": p_num,
            "title": p_title,
            "caption": cap,
            "narration": narr,
            "dialogue": diag
        }
        panels_story.append(panel_entry)
        formatted_texts.append(
            f"--- Panel {p_num}: {p_title} ---\n"
            f"[Caption]: {cap}\n"
            f"[Narration]: {narr}\n"
            f"[Dialogue]: {diag}\n"
        )

    return {
        "panels": panels_story,
        "full_text": "\n".join(formatted_texts)
    }


def generate_story(outline: List[Dict[str, Any]], character_name: str, tone: str, art_style: str) -> Dict[str, Any]:
    """
    Uses Gemini to expand comic panel outlines into detailed narrative,
    captions, and character dialogues.
    Returns a dictionary with 'panels' (list of panel story dicts) and 'full_text' (formatted string).
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip(' "\'') or GEMINI_API_KEY

    if not api_key or _client is None:
        logger.info("Using local fallback generator for comic story (no GEMINI_API_KEY detected).")
        return _get_fallback_story(outline, character_name, tone, art_style)

    outline_summary = "\n".join([
        f"Panel {p.get('panel')}: {p.get('title')} - {p.get('description')}"
        for p in outline
    ])

    system_instruction = (
        "You are an acclaimed graphic novel and comic book author. "
        "Expand the given panel outline into vivid narration, atmospheric captions, and authentic character dialogue. "
        "Return strictly a valid JSON array of objects, one for each panel (exactly 5 items). "
        "Each object must have: 'panel' (int), 'title' (string), 'caption' (short atmospheric setting or sound effect), "
        "'narration' (engaging descriptive narrative paragraph for the panel), and 'dialogue' (character speech lines with speaker names). "
        "Do not use markdown backticks."
    )

    user_query = f"""
Character Name: {character_name}
Tone: {tone}
Art Style: {art_style}

Panel Outline:
{outline_summary}

Write the full script for these 5 panels. Keep dialogue punchy and narration atmospheric.
Output strictly JSON without markdown fences.
"""

    models_to_try = ["gemini-flash-lite-latest", "gemini-3.8-flash", PRO_MODEL_NAME, "gemini-flash-latest"]
    # De-duplicate while preserving order
    seen = set()
    candidate_models = []
    for m in models_to_try:
        if m and m not in seen:
            seen.add(m)
            candidate_models.append(m)

    for model_name in candidate_models:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=user_query,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.75,
                    max_output_tokens=2000,
                )
            )

            response_text = response.text.strip()
            logger.debug("Gemini story response received from %s", model_name)

            cleaned_json = re.sub(r"^```(?:json)?\s*", "", response_text, flags=re.MULTILINE)
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json, flags=re.MULTILINE).strip()

            match = re.search(r"\[\s*\{.*\}\s*\]", cleaned_json, re.DOTALL)
            if match:
                cleaned_json = match.group(0)

            data = json.loads(cleaned_json)

            if isinstance(data, list) and len(data) >= 1:
                panels_story = []
                formatted_texts = []
                for i, p in enumerate(data[:len(outline)], start=1):
                    p_num = p.get("panel", i)
                    p_title = p.get("title", outline[i-1].get("title") if i-1 < len(outline) else f"Panel {p_num}")
                    cap = p.get("caption", "...")
                    narr = p.get("narration", "")
                    diag = p.get("dialogue", "")

                    panel_entry = {
                        "panel": p_num,
                        "title": p_title,
                        "caption": cap,
                        "narration": narr,
                        "dialogue": diag
                    }
                    panels_story.append(panel_entry)
                    formatted_texts.append(
                        f"--- Panel {p_num}: {p_title} ---\n"
                        f"[Caption]: {cap}\n"
                        f"[Narration]: {narr}\n"
                        f"[Dialogue]: {diag}\n"
                    )

                return {
                    "panels": panels_story,
                    "full_text": "\n".join(formatted_texts)
                }

        except Exception as e:
            logger.warning("Gemini model %s failed: %s. Trying next...", model_name, e)

    logger.warning("Could not generate story with Gemini (rate limit or network). Using custom prompt story fallback.")
    return _get_fallback_story(outline, character_name, tone, art_style)

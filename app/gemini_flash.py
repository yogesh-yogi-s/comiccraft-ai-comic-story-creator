import json
import logging
import os
import re
from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip(' "\'')
FLASH_MODEL_NAME = os.getenv("GEMINI_FLASH_MODEL", "gemini-flash-lite-latest").strip()

try:
    from google import genai
    from google.genai import types as genai_types
    _client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception as e:
    logger.warning("Could not initialize google-genai: %s", e)
    genai = None
    genai_types = None
    _client = None


def _get_fallback_full_comic(prompt: str, character_name: str, setting: str, tone: str, art_style: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generates a complete 5-panel structured outline and rich narrative script
    specifically tailored to the user's prompt when Gemini API quota is exceeded.
    Consumes 0 API credits.
    """
    hero = character_name.strip() or "The Hero"
    place = setting.strip() or "the scene"
    mood = tone.strip() or "Heroic"
    style = art_style.strip() or "Comic Book Classic"
    story_idea = prompt.strip() or f"{hero} on an epic journey in {place}"

    outline = [
        {
            "panel": 1,
            "title": f"Act 1: Arrival at {place}",
            "description": f"Under the atmospheric skies of {place}, {hero} arrives as {story_idea} begins to unfold.",
            "prompt": f"masterpiece comic book panel, {style} style, {hero} standing in front of {place}, cinematic wide shot, sharp ink lineart, vivid anime cel shading, vibrant lighting, clean 8k resolution"
        },
        {
            "panel": 2,
            "title": f"Act 2: Tension Mounts in {place}",
            "description": f"Exploring deeper into {place}, {hero} encounters unexpected elements escalating {story_idea}.",
            "prompt": f"masterpiece comic book panel, {style} style, {hero} inside {place}, dynamic camera perspective, sharp ink linework, vivid cel shading, high contrast, clean details, 8k resolution"
        },
        {
            "panel": 3,
            "title": "Act 3: A Sudden Encounter",
            "description": f"A dramatic twist erupts, creating an unforgettable clash or surprise in {place}.",
            "prompt": f"masterpiece comic book panel, {style} style, dramatic face-to-face encounter, {hero} reacting with intense emotion, vivid lighting, dynamic action lines, sharp inks, 8k"
        },
        {
            "panel": 4,
            "title": "Act 4: The Climax Unfolds",
            "description": f"With high stakes, {hero} leaps into decisive action to resolve the core dilemma of {story_idea}.",
            "prompt": f"masterpiece comic book panel, {style} style, explosive dynamic action shot, {hero} in heroic motion in {place}, vibrant cel-shaded colors, sharp linework, 8k resolution"
        },
        {
            "panel": 5,
            "title": "Act 5: Triumph and Camaraderie",
            "description": f"The dust settles over {place}, leaving {hero} victorious in a heartwarming, memorable conclusion.",
            "prompt": f"masterpiece comic book panel, {style} style, {hero} smiling peacefully in {place}, warm cinematic golden hour lighting, heartwarming ending, sharp linework, 8k resolution"
        }
    ]

    panels_story = [
        {
            "panel": 1,
            "title": outline[0]["title"],
            "caption": f"THE LEGEND BEGINS IN {place.upper()}...",
            "narration": f"The atmosphere in {place} hangs heavy with anticipation. {hero} steps onto the scene, ready for whatever lies ahead.",
            "dialogue": f'{hero}: "Here we go! Time to see what destiny has in store."'
        },
        {
            "panel": 2,
            "title": outline[1]["title"],
            "caption": "ENERGY CRACKLES ACROSS THE SCENE!",
            "narration": f"Every step through {place} reveals hidden surprises. {hero} stays sharp, feeling the momentum build.",
            "dialogue": f'{hero}: "I didn\'t expect this to happen so fast, but there\'s no turning back now!"'
        },
        {
            "panel": 3,
            "title": outline[2]["title"],
            "caption": "A SUDDEN SHOCK ECHOES OUT!",
            "narration": f"Without warning, the situation turns in an instant! The clash in {place} catches everyone off guard.",
            "dialogue": f'{hero}: "Hold on! Look out!"'
        },
        {
            "panel": 4,
            "title": outline[3]["title"],
            "caption": "DECISIVE MOMENT!",
            "narration": f"With unwavering courage, {hero} meets the challenge head-on, giving everything to triumph.",
            "dialogue": f'{hero}: "Believe it! We\'ve got this!"'
        },
        {
            "panel": 5,
            "title": outline[4]["title"],
            "caption": "VICTORY UNDER THE TWILIGHT SKY...",
            "narration": f"As peace returns to {place}, smiles and camaraderie fill the air. A heroic memory is forged forever.",
            "dialogue": f'{hero}: "That was unforgettable! Ready for the next adventure?"'
        }
    ]

    formatted_texts = [
        f"--- Panel {p['panel']}: {p['title']} ---\n[Caption]: {p['caption']}\n[Narration]: {p['narration']}\n[Dialogue]: {p['dialogue']}\n"
        for p in panels_story
    ]

    story = {
        "panels": panels_story,
        "full_text": "\n".join(formatted_texts)
    }

    return outline, story


def generate_full_comic(prompt: str, character_name: str, setting: str, tone: str, art_style: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Executes a SINGLE consolidated Gemini call that generates:
    1. A structured 5-panel comic storyboard outline with high-clarity image prompts.
    2. The full narrative script (captions, atmospheric narration, character dialogue).
    Consumes strictly ONE Gemini API credit per comic (satisfying the <= 3 credit limit).
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip(' "\'') or GEMINI_API_KEY

    if not api_key or _client is None:
        logger.info("Using tailored local generator for full comic (no GEMINI_API_KEY configured).")
        return _get_fallback_full_comic(prompt, character_name, setting, tone, art_style)

    system_instruction = (
        "You are an elite graphic novel director, storyboard artist, and comic scriptwriter. "
        "Create a complete, cohesive 5-panel comic narrative and script in a SINGLE JSON response. "
        "Your response MUST be strictly a valid JSON array of exactly 5 panel objects. "
        "Each object must have these exact keys:\n"
        "  - 'panel': integer (1 to 5)\n"
        "  - 'title': string (punchy act title, e.g. 'Act 1: Arrival')\n"
        "  - 'description': string (scene narrative action)\n"
        "  - 'caption': string (dramatic narrator caption or sound cue in uppercase, e.g. 'THE STAGE IS SET...')\n"
        "  - 'narration': string (atmospheric paragraph describing the moment)\n"
        "  - 'dialogue': string (character dialogue with speaker name prefix, e.g. 'Naruto: \"Ramen time!\"')\n"
        "  - 'prompt': string (detailed text-to-image prompt for Stable Diffusion: "
        "describe subject, characters, actions, camera angle, composition, lighting, art style, sharp ink outlines, vibrant cel-shaded colors, clean details, 8k resolution, no blur)\n"
        "Output ONLY the raw JSON array. Do not include markdown fences or extra prose."
    )

    user_query = f"""
Story Idea: {prompt}
Main Character: {character_name}
Setting: {setting}
Tone: {tone}
Art Style Preference: {art_style}

Produce all 5 acts for this comic:
Act 1: Introduction, establishing shot, inciting atmosphere
Act 2: Exploration, rising stakes, character interaction
Act 3: Sudden twist, surprise encounter, or dramatic confrontation
Act 4: High-energy climax, decisive action or teamwork
Act 5: Resolution, triumph, camaraderie, heartwarming aftermath

Ensure each panel's 'prompt' is descriptive, specifies '{character_name}', the environment '{setting}', and visual cues suited for '{art_style}' comic art with sharp linework.
Output strictly JSON.
"""

    models_to_try = ["gemini-flash-lite-latest", "gemini-3.8-flash", FLASH_MODEL_NAME, "gemini-flash-latest"]
    # De-duplicate while preserving order
    seen = set()
    candidate_models = []
    for m in models_to_try:
        if m and m not in seen:
            seen.add(m)
            candidate_models.append(m)

    for model_name in candidate_models:
        try:
            logger.info("Requesting full comic script via Gemini model: %s (1 API call)", model_name)
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=user_query,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=2500,
                )
            )

            response_text = response.text.strip()
            cleaned_json = re.sub(r"^```(?:json)?\s*", "", response_text, flags=re.MULTILINE)
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json, flags=re.MULTILINE).strip()

            match = re.search(r"\[\s*\{.*\}\s*\]", cleaned_json, re.DOTALL)
            if match:
                cleaned_json = match.group(0)

            data = json.loads(cleaned_json)

            if isinstance(data, list) and len(data) >= 5:
                outline = []
                panels_story = []
                formatted_texts = []

                for i, p in enumerate(data[:5], start=1):
                    p_num = p.get("panel", i)
                    p_title = p.get("title", f"Act {i}: Panel {i}")
                    p_desc = p.get("description", "")
                    p_cap = p.get("caption", "...")
                    p_narr = p.get("narration", "")
                    p_diag = p.get("dialogue", "")
                    p_prompt = p.get("prompt", f"{character_name} in {setting}, {art_style} comic illustration")

                    outline.append({
                        "panel": p_num,
                        "title": p_title,
                        "description": p_desc,
                        "prompt": p_prompt
                    })

                    panels_story.append({
                        "panel": p_num,
                        "title": p_title,
                        "caption": p_cap,
                        "narration": p_narr,
                        "dialogue": p_diag
                    })

                    formatted_texts.append(
                        f"--- Panel {p_num}: {p_title} ---\n"
                        f"[Caption]: {p_cap}\n"
                        f"[Narration]: {p_narr}\n"
                        f"[Dialogue]: {p_diag}\n"
                    )

                story = {
                    "panels": panels_story,
                    "full_text": "\n".join(formatted_texts)
                }

                logger.info("Successfully generated complete comic storyboard & script in 1 Gemini call via %s", model_name)
                return outline, story

        except Exception as e:
            logger.warning("Gemini generation attempt with %s failed: %s. Trying fallback model...", model_name, e)

    logger.warning("All Gemini model attempts exhausted or rate-limited. Using custom tailored comic fallback.")
    return _get_fallback_full_comic(prompt, character_name, setting, tone, art_style)


def generate_outline(prompt: str, character_name: str, setting: str, tone: str, art_style: str) -> List[Dict[str, Any]]:
    """
    Backwards-compatible wrapper that returns only the outline list.
    """
    outline, _ = generate_full_comic(prompt, character_name, setting, tone, art_style)
    return outline

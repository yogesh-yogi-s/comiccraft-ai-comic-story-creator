import hashlib
import io
import logging
import math
import os
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import requests

load_dotenv()
logger = logging.getLogger(__name__)

STATIC_PANELS_DIR = os.path.join("static", "panels")
HF_INFERENCE_URL = os.getenv(
    "HF_INFERENCE_URL",
    "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-3-medium-diffusers",
).strip()
HF_REQUEST_TIMEOUT_SECS = 90

# Pollinations model pool — each panel gets its own model name.
# Despite sharing an IP quota, different model backends have slightly
# different worker pools, reducing collision probability when fired in parallel.
POLLINATIONS_MODELS = [
    "flux",
    "turbo",
    "flux-realism",
    "flux-anime",
    "flux-3d",
]

# Stagger delay (seconds) between launching each parallel panel request.
# Spreading the burst over 6 seconds drastically reduces 402 collisions.
PANEL_LAUNCH_STAGGER_SECS = 6


def ensure_panels_directory():
    """Ensures the static/panels directory exists."""
    os.makedirs(STATIC_PANELS_DIR, exist_ok=True)


def sanitize_filename(prompt: str, panel_num: int = 1) -> str:
    """Generates a clean, filesystem-safe filename with timestamp and hash."""
    clean_text = re.sub(r"[^\w\s-]", "", prompt.lower()).strip()
    slug = re.sub(r"[-\s]+", "_", clean_text)[:28]
    prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:6]
    timestamp = int(time.time())
    return f"panel_{panel_num}_{timestamp}_{slug}_{prompt_hash}.png"


def _build_comic_prompt(prompt: str, art_style: str) -> str:
    """Builds a rich comic-style prompt string."""
    # Gemini is asked for a string, but external model responses cannot be
    # trusted blindly. Normalizing here prevents an invalid prompt from
    # crashing URL encoding in the fallback path.
    if not isinstance(prompt, str):
        prompt = str(prompt or "dynamic comic scene")
    if not isinstance(art_style, str):
        art_style = "comic book"
    clean = (
        prompt
        .replace("masterpiece comic panel, ", "")
        .replace("masterpiece action comic panel, ", "")
        .strip()[:220]
    )
    return (
        f"masterpiece comic book panel, {art_style} style, {clean}, "
        f"sharp clean ink outlines, vivid dynamic anime cel shading, "
        f"cinematic comic lighting, high contrast, graphic novel illustration, "
        f"no text, no watermarks"
    )


def _get_hf_api_key() -> str:
    """Return a usable Hugging Face token without ever logging its value."""
    for name in ("HF_API_KEY", "HUGGINGFACEHUB_API_TOKEN"):
        value = os.getenv(name, "").strip().strip('"').strip("'")
        if value and not value.lower().startswith(("your_", "hf_your_")):
            return value
    return ""


def _generate_via_huggingface(prompt: str, art_style: str, panel_num: int) -> Optional[Image.Image]:
    """Generate a panel through Hugging Face's authenticated inference router.

    Hugging Face serverless inference can queue or throttle parallel image jobs.
    The caller deliberately sends the five comic panels one at a time whenever a
    token is configured, which makes a full comic considerably more reliable.
    """
    token = _get_hf_api_key()
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}", "Accept": "image/png"}
    payload = {
        "inputs": _build_comic_prompt(prompt, art_style),
        "parameters": {"num_inference_steps": 25, "guidance_scale": 7.5},
        "options": {"wait_for_model": True},
    }

    for attempt in range(1, 3):
        try:
            logger.info("Panel %s: requesting Hugging Face image (%s/2).", panel_num, attempt)
            response = requests.post(
                HF_INFERENCE_URL,
                headers=headers,
                json=payload,
                timeout=HF_REQUEST_TIMEOUT_SECS,
            )
            content_type = response.headers.get("content-type", "").lower()
            if response.status_code == 200 and (content_type.startswith("image/") or len(response.content) > 1000):
                image = Image.open(io.BytesIO(response.content)).convert("RGB")
                logger.info("Panel %s generated via Hugging Face (%sx%s).", panel_num, image.width, image.height)
                return image.resize((768, 512), Image.Resampling.LANCZOS)

            # A 503 normally means the selected model is loading.  The router
            # includes an estimated wait time in its JSON response when available.
            if response.status_code in (429, 503) and attempt == 1:
                wait_seconds = 8
                try:
                    wait_seconds = max(1, min(30, int(response.json().get("estimated_time", wait_seconds))))
                except (ValueError, requests.JSONDecodeError):
                    pass
                logger.warning(
                    "Panel %s: Hugging Face returned HTTP %s; retrying in %ss.",
                    panel_num, response.status_code, wait_seconds,
                )
                time.sleep(wait_seconds)
                continue

            detail = response.text[:240].replace("\n", " ")
            if response.status_code in (401, 403):
                logger.error(
                    "Panel %s: Hugging Face rejected the token (HTTP %s). "
                    "Create a token with Inference Providers permission.",
                    panel_num, response.status_code,
                )
            else:
                logger.warning("Panel %s: Hugging Face HTTP %s: %s", panel_num, response.status_code, detail)
            return None
        except requests.RequestException as exc:
            logger.warning("Panel %s: Hugging Face request failed: %s", panel_num, exc)
            if attempt == 1:
                time.sleep(3)

    return None


# ---------------------------------------------------------------------------
# Primary: Pollinations (free, no key — the only confirmed-working generator)
# ---------------------------------------------------------------------------

def _generate_via_pollinations(
    prompt: str,
    art_style: str,
    panel_num: int,
    model_name: str = "flux",
    initial_delay: float = 0.0,
) -> Optional[Image.Image]:
    """
    Generates one comic panel image via Pollinations.
    - `model_name`: which Pollinations backend to use (flux / turbo / flux-realism / etc.)
    - `initial_delay`: seconds to sleep before the first request (used for staggering).
    - On HTTP 402 (rate limit), waits 20 s then retries up to 3 times on the same model,
      then escalates to the next model in the pool before giving up.
    """
    if initial_delay > 0:
        logger.info("Panel %s [%s]: stagger delay %.0fs before first request...",
                    panel_num, model_name, initial_delay)
        time.sleep(initial_delay)

    full_prompt = _build_comic_prompt(prompt, art_style)
    encoded_prompt = urllib.parse.quote(full_prompt)
    seed = abs(hash(prompt + str(panel_num))) % 100000

    # Model rotation: start with assigned model, then cycle through the rest
    all_models = [model_name] + [m for m in POLLINATIONS_MODELS if m != model_name]

    for current_model in all_models[:3]:   # try at most 3 different models
        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width=768&height=512&nologo=true&seed={seed}"
            f"&model={current_model}&enhance=true"
        )
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info("Panel %s [%s] attempt %s/%s...",
                            panel_num, current_model, attempt, max_attempts)
                response = requests.get(url, timeout=50)

                if response.status_code == 200 and len(response.content) > 1000:
                    img = Image.open(io.BytesIO(response.content)).convert("RGB")
                    img = img.resize((768, 512), Image.Resampling.LANCZOS)
                    logger.info("Panel %s generated via Pollinations [%s] attempt %s (%sx%s)",
                                panel_num, current_model, attempt, img.width, img.height)
                    return img

                elif response.status_code == 402:
                    logger.warning(
                        "Panel %s [%s] got 402 (rate limit) on attempt %s. Waiting 20s...",
                        panel_num, current_model, attempt
                    )
                    time.sleep(20)

                else:
                    logger.warning(
                        "Panel %s [%s] HTTP %s / %s bytes on attempt %s",
                        panel_num, current_model, response.status_code,
                        len(response.content), attempt
                    )
                    time.sleep(6)

            except Exception as e:
                logger.warning("Panel %s [%s] exception on attempt %s: %s",
                               panel_num, current_model, attempt, e)
                time.sleep(6)

        logger.info("Panel %s: [%s] exhausted. Rotating to next model...",
                    panel_num, current_model)

    logger.warning("Panel %s: all Pollinations models exhausted.", panel_num)
    return None


# ---------------------------------------------------------------------------
# Fallback: Local stylized canvas (offline, always works)
# ---------------------------------------------------------------------------

def _render_stylized_comic_art(
    prompt: str,
    art_style: str = "comic book",
    panel_num: int = 1,
) -> Image.Image:
    """
    Offline canvas renderer — guaranteed last-resort fallback.
    Renders action rays, comic border, and styled typography.
    """
    width, height = 768, 512
    img = Image.new("RGB", (width, height), color=(20, 24, 28))
    draw = ImageDraw.Draw(img)

    cx, cy = width // 2, height // 2
    for i in range(20):
        if i % 2 == 0:
            a1 = (i / 20) * 2 * math.pi
            a2 = ((i + 1) / 20) * 2 * math.pi
            r = max(width, height)
            draw.polygon(
                [(cx, cy),
                 (int(cx + r * math.cos(a1)), int(cy + r * math.sin(a1))),
                 (int(cx + r * math.cos(a2)), int(cy + r * math.sin(a2)))],
                fill=(32, 40, 48)
            )

    inset = 12
    draw.rectangle([(inset, inset), (width - inset, height - inset)],
                   outline=(245, 245, 240), width=5)
    draw.rectangle([(inset + 6, inset + 6), (width - inset - 6, height - inset - 6)],
                   outline=(234, 88, 12), width=2)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    draw.text((inset + 20, inset + 18),
              f"ACT // PANEL {panel_num} [{art_style.upper()[:16]}]",
              fill=(255, 255, 255), font=font)
    short = prompt[:76] + ("..." if len(prompt) > 76 else "")
    draw.text((inset + 18, height - inset - 26),
              f">> SCENE: {short}", fill=(203, 213, 225), font=font)

    return img


# ---------------------------------------------------------------------------
# Panel worker — called per thread
# ---------------------------------------------------------------------------

def _generate_single_panel(
    panel: Dict[str, Any],
    index: int,
    art_style: str,
) -> tuple:
    """
    Worker that generates one panel image.
    - Each panel is assigned a different Pollinations model.
    - Each panel is given a staggered start delay to avoid simultaneous 402s.
    Returns (index, image_url_path).
    """
    p_num = panel.get("panel", index + 1)
    p_prompt = panel.get("prompt") or f"Heroic comic scene, panel {p_num}"
    if not isinstance(p_prompt, str):
        logger.warning("Panel %s supplied a non-text image prompt; converting it to text.", p_num)
        p_prompt = str(p_prompt)
    filename = sanitize_filename(p_prompt, panel_num=p_num)
    out_path = os.path.join(STATIC_PANELS_DIR, filename)

    # Prefer the configured, authenticated provider. Pollinations remains a
    # best-effort fallback for installations without a usable HF token.
    img = _generate_via_huggingface(p_prompt, art_style, p_num)

    # Assign a dedicated model and a staggered start time per panel
    model = POLLINATIONS_MODELS[index % len(POLLINATIONS_MODELS)]
    stagger = index * PANEL_LAUNCH_STAGGER_SECS  # 0, 6, 12, 18, 24 seconds

    if img is None:
        img = _generate_via_pollinations(p_prompt, art_style, p_num,
                                         model_name=model, initial_delay=stagger)

    if img is None:
        logger.warning("Panel %s: all cloud generators failed — using canvas fallback.", p_num)
        img = _render_stylized_comic_art(p_prompt, art_style, p_num)

    img.save(out_path, format="PNG")
    logger.info("Panel %s saved → %s", p_num, out_path)
    return index, f"/static/panels/{filename}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_comic_panels(
    panels_data: List[Dict[str, Any]],
    art_style: str = "Comic Book Classic",
) -> List[str]:
    """
    Generates all comic panel images using ThreadPoolExecutor.

    With a configured Hugging Face token, panels are generated serially. This
    avoids a five-request burst, which commonly produces 429/503 quota errors
    from serverless inference. Without a token, Pollinations runs with its
    existing staggered parallel fallback strategy.

    Expected total time: ~35-50 seconds for 5 panels.
    """
    ensure_panels_directory()
    image_paths: List[str] = [""] * len(panels_data)

    using_huggingface = bool(_get_hf_api_key())
    max_workers = 1 if using_huggingface else max(1, len(panels_data))
    logger.info(
        "Launching %s panel generation (%s panels).",
        "serial Hugging Face" if using_huggingface else "staggered fallback",
        len(panels_data),
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_generate_single_panel, panel, i, art_style): i
            for i, panel in enumerate(panels_data)
        }
        for future in as_completed(futures):
            try:
                idx, url = future.result()
                image_paths[idx] = url
                logger.info("Panel index %s complete → %s", idx, url)
            except Exception as e:
                i = futures[future]
                logger.error("Panel index %s worker crashed: %s", i, e)
                panel = panels_data[i]
                p_num = panel.get("panel", i + 1)
                p_prompt = panel.get("prompt", f"Comic panel {p_num}")
                filename = sanitize_filename(p_prompt, panel_num=p_num)
                out_path = os.path.join(STATIC_PANELS_DIR, filename)
                fallback = _render_stylized_comic_art(p_prompt, art_style, p_num)
                fallback.save(out_path, format="PNG")
                image_paths[i] = f"/static/panels/{filename}"

    logger.info("All %s panels complete.", len(panels_data))
    return image_paths


def generate_image(
    prompt: str,
    art_style: str = "comic book",
    panel_num: int = 1,
) -> str:
    """Single-panel generator for the /test-image route."""
    ensure_panels_directory()
    filename = sanitize_filename(prompt, panel_num=panel_num)
    file_path = os.path.join(STATIC_PANELS_DIR, filename)

    img = _generate_via_huggingface(prompt, art_style, panel_num)
    if img is None:
        model = POLLINATIONS_MODELS[panel_num % len(POLLINATIONS_MODELS)]
        img = _generate_via_pollinations(prompt, art_style, panel_num, model_name=model)

    if img is None:
        img = _render_stylized_comic_art(prompt, art_style, panel_num)

    img.save(file_path, format="PNG")
    logger.info("Single panel %s saved → %s", panel_num, file_path)
    return f"/static/panels/{filename}"

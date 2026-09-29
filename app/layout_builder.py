import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def build_comic_layout(
    outline: List[Dict[str, Any]],
    story: Dict[str, Any],
    image_paths: List[str]
) -> List[Dict[str, Any]]:
    """
    Organizes the generated images, panel outlines, and story narration into
    a cohesive, structured comic layout ready for rendering in templates and exporting to PDF.
    """
    layout = []
    story_panels = story.get("panels", []) if isinstance(story, dict) else []

    num_panels = max(len(outline), len(image_paths), len(story_panels))

    for idx in range(num_panels):
        panel_num = idx + 1

        # Outline details
        outline_entry = outline[idx] if idx < len(outline) else {}
        title = outline_entry.get("title", f"Panel {panel_num}: Scene {panel_num}")
        description = outline_entry.get("description", "")
        prompt = outline_entry.get("prompt", "")

        # Story script details
        story_entry = story_panels[idx] if idx < len(story_panels) else {}
        caption = story_entry.get("caption", "...")
        narration = story_entry.get("narration", description)
        dialogue = story_entry.get("dialogue", "")

        # Image path
        img_path = image_paths[idx] if idx < len(image_paths) else "/static/panels/placeholder.png"

        layout_item = {
            "panel": panel_num,
            "title": title,
            "image_path": img_path,
            "description": description,
            "caption": caption,
            "narration": narration,
            "dialogue": dialogue,
            "prompt": prompt
        }
        layout.append(layout_item)

    logger.info("Successfully constructed comic layout with %s panels.", len(layout))
    return layout

"""Summarize Kaggle notebook strategies with OpenAI."""

import json
import base64
from openai import OpenAI
from pathlib import Path
from typing import Dict

client = OpenAI()

PROMPT_TMPL = (
    "You are a journalist for the New York Times tech section. "
    "Write a concise article explaining the main modelling and feature-engineering "
    "Make the headline interesting and attention-grabbing."
    "strategy used in the following Kaggle notebook. Be detailed. Say what is unusual or interesting about this strategy. Mention interesting techniques and results.\n\n"
    "NOTEBOOK CONTEXT:\n{context}\n"
)


def extract_text_from_notebook(ipynb_path: Path, max_chars: int = 4000) -> str:
    cells = json.loads(ipynb_path.read_text())['cells']
    texts = []
    for c in cells:
        if c['cell_type'] in {'markdown', 'code'}:
            texts.append(''.join(c['source']))
        if sum(len(t) for t in texts) > max_chars:
            break
    return '\n\n'.join(texts)[:max_chars]


def summarise_notebook(ipynb_path: Path, image_dir: Path = None) -> Dict[str, str]:
    context = extract_text_from_notebook(ipynb_path)
    prompt = PROMPT_TMPL.format(context=context)
    resp = client.chat.completions.create(
        model="o4-mini-2025-04-16",
        messages=[{"role": "user", "content": prompt}],
    )
    summary = resp.choices[0].message.content.strip()
    # Cheap title: first line until dot
    title = summary.split('\n')[0][:120]

    # Tagline: first sentence or first 140 characters
    plain_summary = summary.replace('\n', ' ').strip()
    first_sentence_end = plain_summary.find('.')
    if first_sentence_end == -1 or first_sentence_end > 160:
        tagline = (plain_summary[:140] + '…') if len(plain_summary) > 140 else plain_summary
    else:
        tagline = plain_summary[: first_sentence_end + 1]

    # --- Generate DALL-E image ---
    image_url = None
    if image_dir is not None:
        # ensure we work with absolute paths to avoid relative_to errors later
        image_dir = image_dir.resolve()

        dalle_prompt = f"Magazine cover illustration for: {title}"
        try:
            dalle_result = client.images.generate(
                model="dall-e-3",
                prompt=dalle_prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json",
            )
            image_base64 = dalle_result.data[0].b64_json
            if image_base64 is None:
                raise ValueError("Empty b64_json from DALL·E API")
            image_bytes = base64.b64decode(image_base64)
            image_dir.mkdir(parents=True, exist_ok=True)
            image_path = image_dir / "cover.png"
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            # Build root-relative URL (remove leading "docs/") so site served from docs/ works.
            rel_path = image_path.relative_to(Path.cwd())
            if rel_path.parts[0] == "docs":
                rel_path = Path(*rel_path.parts[1:])
            image_url = "/" + rel_path.as_posix()
        except Exception as e:
            # Fallback: try URL-based generation if base64 failed or was rejected
            try:
                dalle_result = client.images.generate(
                    model="dall-e-3",
                    prompt=dalle_prompt,
                    size="1024x1024",
                )
                url = dalle_result.data[0].url  # type: ignore
                # Save remote image locally
                import requests

                img_resp = requests.get(url)
                if img_resp.ok:
                    image_dir.mkdir(parents=True, exist_ok=True)
                    image_path = image_dir / "cover.png"
                    image_path.write_bytes(img_resp.content)
                    rel_path = image_path.relative_to(Path.cwd())
                    if rel_path.parts[0] == "docs":
                        rel_path = Path(*rel_path.parts[1:])
                    image_url = "/" + rel_path.as_posix()
                else:
                    print("[WARN] Failed to download image URL from DALL·E response")
            except Exception as e2:
                print(f"[WARN] DALL-E image generation failed: {e2}")
            print("DALL-E image TITLE:", title)

    return {"summary_html": summary.replace('\n', '<br>'), "title": title, "image_url": image_url, "tagline": tagline}

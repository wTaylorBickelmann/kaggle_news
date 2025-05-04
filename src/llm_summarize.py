"""Summarize Kaggle notebook strategies with OpenAI."""

import json
from openai import OpenAI
from pathlib import Path
from typing import Dict

client = OpenAI()

PROMPT_TMPL = (
    "You are a journalist for the New York Times tech section. "
    "Write a concise (<=300 words) article explaining the main modelling and feature-engineering "
    "strategy used in the following Kaggle notebook. Mention interesting techniques and results.\n\n"
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


def summarise_notebook(ipynb_path: Path) -> Dict[str, str]:
    context = extract_text_from_notebook(ipynb_path)
    prompt = PROMPT_TMPL.format(context=context)
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role": "user", "content": prompt}],
    )
    summary = resp.choices[0].message.content.strip()
    # Cheap title: first line until dot
    title = summary.split('\n')[0][:120]
    return {"summary_html": summary.replace('\n', '<br>'), "title": title}

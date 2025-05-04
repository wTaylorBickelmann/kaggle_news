"""Main pipeline to fetch Kaggle hot notebooks, summarise and render static site."""
from datetime import datetime
from pathlib import Path
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape
from slugify import slugify

from kaggle_fetch import fetch_hot_kernels, pull_kernel_notebook
from llm_summarize import summarise_notebook

SITE_ROOT = Path("docs")  # GitHub Pages serves /docs on the main branch
TEMPLATES_DIR = Path(__file__).parent / "templates"


def render(env, template_name: str, context: dict, out_path: Path):
    tpl = env.get_template(template_name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tpl.render(**context), encoding="utf-8")


def main():
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html"]))

    today = datetime.utcnow().date()
    date_str = today.strftime("%B %d, %Y")

    print("Fetching Kaggle notebooks …")
    notebooks = fetch_hot_kernels(limit=10)

    api_cache = Path(".cache/kernels")
    articles = []
    for nb in notebooks:
        ref = nb["ref"]
        slug = nb["slug"]
        dest_dir = api_cache / slug
        ipynb_path = pull_kernel_notebook(KaggleApi(), ref, dest_dir)
        if ipynb_path is None:
            print("Could not download", ref)
            continue
        summary = summarise_notebook(ipynb_path)
        article_dir = SITE_ROOT / str(today.year) / today.strftime("%m") / today.strftime("%d") / slug
        article_html_path = article_dir / "index.html"

        article_context = {
            "date": date_str,
            "article": {
                **nb,
                **summary,
                "original_url": nb["url"],
            },
        }
        render(env, "article.html", article_context, article_html_path)

        articles.append({
            **nb,
            **summary,
            "original_url": nb["url"],
        })

    # render front page
    front_dir = SITE_ROOT / str(today.year) / today.strftime("%m") / today.strftime("%d")
    render(env, "index.html", {"date": date_str, "articles": articles}, front_dir / "index.html")

    # also copy to root as latest index
    render(env, "index.html", {"date": date_str, "articles": articles}, SITE_ROOT / "index.html")

    # optional: clean cache
    shutil.rmtree(api_cache, ignore_errors=True)


if __name__ == "__main__":
    main()

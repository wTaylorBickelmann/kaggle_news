"""Fetch hot Kaggle notebooks via Kaggle API."""
from pathlib import Path
from datetime import datetime
from slugify import slugify

from kaggle.api.kaggle_api_extended import KaggleApi


def fetch_hot_kernels(limit: int = 30):
    api = KaggleApi()
    api.authenticate()

    kernels = api.kernels_list(sort_by="hotness", page_size=limit, kernel_type="notebook")
    results = []
    for k in kernels:
        ref = k.ref  # username/kernel-slug
        title = k.title
        url = f"https://www.kaggle.com/{ref}"
        source_domain = "kaggle.com"
        image_url = k.coverImageUrl or "https://www.kaggle.com/static/images/site-logo.png"
        slug = slugify(title)[:60]

        results.append(
            {
                "ref": ref,
                "title": title,
                "url": url,
                "image_url": image_url,
                "source_domain": source_domain,
                "slug": slug,
                "raw_kernel": k,
            }
        )
    return results


def pull_kernel_notebook(api: KaggleApi, ref: str, dest_dir: Path):
    """Download a notebook to dest_dir and return path to .ipynb file."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    api.kernels_pull(kernel=ref, path=dest_dir, metadata=False, quiet=True)
    # Search for ipynb in dest_dir
    for p in dest_dir.glob("*.ipynb"):
        return p
    return None

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

NAMESPACE = "JoaoRG"
DATASET_ID = f"{NAMESPACE}/pfild-ppf-evidence-corpus"
SPACE_ID = f"{NAMESPACE}/pfild-review-agents"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def require_token() -> str:
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Set HF_TOKEN with write permission before running this script.")
    return token


def main() -> None:
    api = HfApi(token=require_token())
    identity = api.whoami()
    print(f"Authenticated as {identity.get('name', 'unknown')}")

    api.create_repo(DATASET_ID, repo_type="dataset", private=True, exist_ok=True)
    api.create_repo(SPACE_ID, repo_type="space", private=True, space_sdk="gradio", exist_ok=True)

    with tempfile.TemporaryDirectory() as temporary:
        dataset = Path(temporary) / "dataset"
        dataset.mkdir()

        state = PROJECT_ROOT / "data" / "project_state.json"
        seeds = sorted((PROJECT_ROOT / "data" / "seeds").glob("seeds-*.json"))
        if not state.exists() or not seeds:
            raise FileNotFoundError("Project state or seed files are missing from the GitHub checkout.")

        (dataset / "project_state.json").write_bytes(state.read_bytes())
        for source in seeds:
            (dataset / source.name).write_bytes(source.read_bytes())

        (dataset / "README.md").write_text(
            "# Private PF-ILD / PPF evidence corpus\n\n"
            "Snapshot date: 2026-08-02. Contains the complete set of 1,004 PubMed PMIDs, "
            "the reproducible query and 66 discovery seeds. AI recommendations are not final decisions.\n",
            encoding="utf-8",
        )

        api.upload_folder(
            repo_id=DATASET_ID,
            repo_type="dataset",
            folder_path=str(dataset),
            commit_message="Initialize private PF-ILD/PPF evidence corpus",
        )

    api.upload_folder(
        repo_id=SPACE_ID,
        repo_type="space",
        folder_path=str(Path(__file__).resolve().parent),
        ignore_patterns=["bootstrap_hub.py", "__pycache__/*"],
        commit_message="Initialize private PF-ILD review agents",
    )

    print(
        json.dumps(
            {
                "dataset": f"https://huggingface.co/datasets/{DATASET_ID}",
                "space": f"https://huggingface.co/spaces/{SPACE_ID}",
                "private": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

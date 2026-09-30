"""Tạo prompt day13-chat v1 (baseline + production) và v2 (candidate) trong Langfuse."""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from app.cli import configure_utf8_stdio  # noqa: E402
from langfuse import get_client  # noqa: E402

NAME = "day13-chat"
V1 = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
V2 = (
    "You are a concise assistant. Answer in at most three sentences.\n"
    "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
)


def main() -> None:
    configure_utf8_stdio()
    client = get_client()
    try:
        existing = client.get_prompt(NAME, label="production", type="text", max_retries=0)
        print(f"Prompt {NAME} đã tồn tại (production = v{existing.version}); không tạo lại.")
        return
    except Exception:
        pass
    v1 = client.create_prompt(name=NAME, type="text", prompt=V1, labels=["baseline", "production"])
    v2 = client.create_prompt(name=NAME, type="text", prompt=V2, labels=["candidate"])
    client.flush()
    print(f"Đã tạo v{v1.version} (baseline, production) và v{v2.version} (candidate)")


if __name__ == "__main__":
    sys.exit(main())

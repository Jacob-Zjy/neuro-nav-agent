from __future__ import annotations

import argparse
import json

from medevalops.audit import audit_items, write_audit_outputs
from medevalops.config import PROCESSED_DIR, SOURCE_FILENAME, SOURCE_SHA256, SOURCE_URL
from medevalops.data import (
    build_items,
    download_source,
    load_source,
    write_private_items,
    write_public_index,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and validate PromptCBLUE data.")
    parser.add_argument("--force", action="store_true", help="Replace a cached source file.")
    args = parser.parse_args()

    source = download_source(force=args.force)
    items = build_items(load_source(source))
    private_path = write_private_items(items)
    public_path = write_public_index(items)
    quality, report = audit_items(items)
    audit_paths = write_audit_outputs(quality, report)

    manifest = {
        "source_url": SOURCE_URL,
        "source_filename": SOURCE_FILENAME,
        "source_sha256": SOURCE_SHA256,
        "selected_rows": len(items),
        "raw_text_committed": False,
        "transformations": {
            "KUAKE-QIC": [
                "Canonicalize 疾病表述 to the PromptCBLUE evaluator label 疾病描述",
                "Append the documented implicit 非上述类型 reject option",
            ]
        },
        "private_items_path": str(private_path.relative_to(private_path.parents[2])),
        "public_index_path": str(public_path.relative_to(public_path.parents[2])),
    }
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = PROCESSED_DIR / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Validated source: {source}")
    print(f"Selected evaluation items: {len(items)}")
    print(f"Public index: {public_path}")
    print(f"Audit outputs: {', '.join(str(path) for path in audit_paths)}")


if __name__ == "__main__":
    main()

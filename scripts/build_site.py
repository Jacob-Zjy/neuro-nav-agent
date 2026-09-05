from __future__ import annotations

import shutil
from pathlib import Path


def main() -> None:
    assets = Path("docs/assets")
    assets.mkdir(parents=True, exist_ok=True)
    stems = ("figure1_navigation_performance", "figure2_trial_landscape")
    for stem in stems:
        for suffix in (".svg", ".png"):
            source = Path("figures") / f"{stem}{suffix}"
            if not source.exists():
                raise FileNotFoundError(f"Generate figures first: missing {source}")
            shutil.copy2(source, assets / source.name)
    print(f"Prepared static project guide in {Path('docs/index.html').resolve()}")


if __name__ == "__main__":
    main()


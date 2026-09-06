from __future__ import annotations

import argparse
import subprocess
import sys


def run(*arguments: str) -> None:
    command = [sys.executable, "-m", *arguments]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the complete MedEval-DataOps pipeline.")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--bootstrap-draws", type=int, default=2000)
    args = parser.parse_args()
    run("scripts.download_data")
    run("scripts.run_inference", "--device", args.device, "--batch-size", str(args.batch_size))
    run("scripts.run_evaluation", "--bootstrap-draws", str(args.bootstrap_draws))
    run("scripts.make_figures")
    run("scripts.build_results")
    run("scripts.build_site")
    run("scripts.verify_release")


if __name__ == "__main__":
    main()


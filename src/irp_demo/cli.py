from __future__ import annotations

import argparse
from irp_demo.api.service import CompareRequest, OptimizationAPI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adaptive IRP optimization portfolio demo")
    sub = parser.add_subparsers(dest="command", required=True)

    compare = sub.add_parser("compare", help="Run configured experiment variants")
    compare.add_argument("--config", default="configs/demo.yaml")
    compare.add_argument("--runs", nargs="*", default=None,
                         help="Optional run names, e.g. baseline_lp proposed_mcf")
    compare.add_argument("--time-limit", type=float, default=None,
                         help="Override per-run time limit in seconds")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "compare":
        OptimizationAPI().compare(CompareRequest(
            config_path=args.config,
            selected_runs=args.runs,
            time_limit_override=args.time_limit,
        ))


if __name__ == "__main__":
    main()

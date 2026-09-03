"""Command-line entry point.

    python -m goddard.cli check                 list unfilled register parameters
    python -m goddard.cli run    --config ...   single forward run
    python -m goddard.cli band   --config ...   sweep the three unmeasured constants

A config module must define ``build_vehicle()`` returning a ``sim.Vehicle``.
There is no such module yet -- 54 register parameters are still OPEN, and the
model refuses to invent them. ``check`` works today and tells you what is
missing.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


def _load_vehicle(config_name: str):
    """Import a config module and call its ``build_vehicle()``."""
    try:
        module = importlib.import_module(config_name)
    except ImportError as exc:
        raise SystemExit(
            f"cannot import config module {config_name!r}: {exc}\n"
            "A config module must be importable and define build_vehicle()."
        ) from exc

    builder = getattr(module, "build_vehicle", None)
    if builder is None:
        raise SystemExit(
            f"{config_name} does not define build_vehicle(). It must return a "
            "goddard.sim.Vehicle."
        )
    return builder()


def cmd_check(args: argparse.Namespace) -> int:
    """Report which register parameters are still unfilled."""
    from goddard.config import RocketConfig

    config = RocketConfig()
    print(config.report_missing())
    missing = config.missing()
    if missing:
        print()
        print(
            f"{len(missing)} parameter(s) block a run. See "
            "docs/assumptions_register.md -- that document is the meeting "
            "artifact for filling them in."
        )
        return 1
    print("All schema parameters filled.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from goddard import sim as sim_mod

    vehicle = _load_vehicle(args.config)
    result = sim_mod.run(vehicle, dt=args.dt, max_time_s=args.max_time)
    print(result.summary())

    # Constraints are printed on every run, pass or fail. A requirement that is
    # computed but not shown is a requirement nobody checks -- rail departure
    # velocity was failing for exactly that reason while thrust-to-weight, a
    # proxy for it, was being reported and passing.
    print()
    print("CONSTRAINTS")
    failures = 0
    for name, actual, limit, ok in result.constraints(vehicle):
        if not ok:
            failures += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {name:28s} {actual:9.2f}  vs {limit:.2f}")
    if failures:
        print(f"\n  {failures} CONSTRAINT(S) FAILING -- see docs/WHAT_WE_NEED.md")

    if args.out:
        out = Path(args.out)
        from goddard.report import excel, plots

        excel.write(result, out / "goddard_results.xlsx")
        print(f"\nwrote {out / 'goddard_results.xlsx'}")
        if plots.available():
            written = plots.write(result, out / "plots")
            print(f"wrote {len(written)} plots to {out / 'plots'}")
        else:
            print("matplotlib not installed -- skipped plots")
    return 0


def cmd_band(args: argparse.Namespace) -> int:
    from goddard import band as band_mod

    vehicle = _load_vehicle(args.config)
    out = band_mod.run_band(
        vehicle, levels=args.levels, dt=args.dt, max_time_s=args.max_time
    )
    print(out.summary())

    if args.out:
        directory = Path(args.out)
        from goddard.report import excel

        best = next((c.result for c in out.corners if c.ok), None)
        if best is not None:
            excel.write(best, directory / "goddard_results.xlsx", band=out)
            print(f"\nwrote {directory / 'goddard_results.xlsx'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="goddard",
        description="Goddard 26-27 flight performance model",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser(
        "check", help="list register parameters that are still OPEN"
    )
    p_check.set_defaults(func=cmd_check)

    for name, func, help_text in (
        ("run", cmd_run, "single forward simulation"),
        ("band", cmd_band, "sweep the three unmeasured constants"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument(
            "--config", required=True,
            help="importable module defining build_vehicle()",
        )
        p.add_argument("--dt", type=float, default=0.01, help="time step, s")
        p.add_argument(
            "--max-time", type=float, default=600.0, dest="max_time",
            help="simulation cutoff, s",
        )
        p.add_argument("--out", help="output directory for report and plots")
        if name == "band":
            p.add_argument(
                "--levels", type=int, default=3,
                help="grid levels per constant (3 gives 27 corners)",
            )
        p.set_defaults(func=func)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

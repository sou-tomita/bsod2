#! /usr/bin/env python3

import argparse
from pathlib import Path

from .sondeset import Sondeset


def qc(args) -> None:

    ss = Sondeset(args.input, interp=args.interp)

    args.output.mkdir(parents=True, exist_ok=True)
    for s in ss:
        s.save_df(args.output / Path(f"{s.sonde_no}.csv"))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bsod2", description="Quality control command for radiosonde data."
    )

    parser.set_defaults(func=qc)

    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input radiosonde data file or directory.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path to save the quality-controlled data directory.",
    )
    parser.add_argument(
        "--interp",
        type=str,
        choices=["p", "z"],
        help="If specified, interpolate along pressure ('p') or height ('z').",
        default=None,
    )

    args = parser.parse_args()
    args.func(args)

#! /usr/bin/env python3

import numpy as np
from pathlib import Path
from pint import Quantity
import matplotlib.pyplot as plt
import metpy.calc as mpcalc
from metpy.units import units
from typing import cast


def plot_tmp_emagram(
    p: Quantity,
    t: Quantity,
    td: Quantity,
    u: Quantity,
    v: Quantity,
    save_fpath: Path,
    title: str = "",
    **kwargs,
) -> None:

    if not save_fpath.exists():
        save_fpath.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(9, 12))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_aspect(200)
    ax.set_title(title, fontsize=15)

    # x axis(degC)
    ax.set_xlabel(r"Temperature [$^\circ$C]")
    ax.set_xlim(-90, 40)
    ax.set_xticks(np.arange(-90, 41, 10))
    ax.set_xticks(np.arange(-90, 41, 5), minor=True)

    # y axis (pressure)
    ax.set_ylabel("Pressure [hPa]")
    ax.set_ylim(100, 1050)
    ax.set_yscale("log")
    ax.invert_yaxis()
    ax.set_yticks(np.arange(100, 1100, 100))
    ax.set_yticklabels([f"{int(p):d}" for p in np.arange(100, 1100, 100)])

    ax.grid(True, which="both", linewidth=0.5, color="gray")

    # plot the temperature profile
    ax.plot(t, p, color="r")

    # plot the dew point temperature profile
    ax.plot(td, p, color="b")

    # plot wind barbs
    SKIP = 15
    ax.barbs(
        np.full((p.shape[0]), 37)[::SKIP],
        p[::SKIP],
        u.to("kt")[::SKIP],
        v.to("kt")[::SKIP],
        p[::SKIP],
        length=6,
        barb_increments={"half": 5, "full": 10, "flag": 50},
        color="k",
    )

    # plot the dry adiabats
    t0s = np.arange(240, 381, 10) * units("K")
    plev = np.arange(50, 1101) * units.hPa
    for i in range(t0s.shape[0]):
        t0 = t0s[i]
        dry_l = mpcalc.dry_lapse(plev, t0, 1000 * units.hPa).to("degC")
        ax.plot(dry_l, plev, c="brown", linewidth="0.7")
        label_i = np.abs(dry_l - -88 * units("degC")).argmin()
        if plev[label_i] > 100.0 * units.hPa:
            ax.text(
                dry_l[label_i],
                plev[label_i],
                f"{int(t0.m)}",
                fontsize=7,
                color="brown",
            )
        else:
            label_i = np.abs(plev - 102 * units.hPa).argmin()
            ax.text(
                dry_l[label_i],
                plev[label_i],
                f"{int(t0.m)}",
                fontsize=7,
                color="brown",
            )

    # plot the moist adiabats
    t0s = np.arange(240, 361, 10) * units("K")
    plev = np.arange(50, 1101) * units.hPa
    for i in range(t0s.shape[0]):
        t0 = t0s[i]
        moist_l = cast(Quantity, mpcalc.moist_lapse(plev, t0, 1000 * units.hPa)).to(
            "degC"
        )
        ax.plot(moist_l, plev, c="purple", linewidth="0.7")

    # plot the saturation mixing ratio lines
    for sat_mixr in [
        0.2,
        0.4,
        0.6,
        1,
        2,
        3,
        4,
        5,
        10,
        15,
        20,
    ]:
        tmp = np.arange(-90, 41, 0.01)
        prs = (
            6.11
            * (sat_mixr + 622)
            / sat_mixr
            * np.exp(19.84 * tmp / (tmp + 273.15) + 1e-5)
        )
        ax.plot(tmp, prs, c="g", lw=0.5)
        i = np.abs(prs - 120).argmin()
        ax.text(tmp[i].item(), prs[i], f"{sat_mixr}", fontsize=6)

    plt.savefig(save_fpath)
    plt.close()

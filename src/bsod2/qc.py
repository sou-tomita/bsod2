#! /usr/bin/env python3

from datetime import datetime, timedelta
import math
import numpy as np
import pandas as pd
import warnings

remove_columns = [
    "ST",
    "SondeN",
    "FCnt",
    "AGC",
    "rcvFREQ",
    "GF",
    "FE",
    "V",
    "RE",
    "N1",
    "N2",
    "N3",
    "N4",
    "N5",
    "N6",
    "N7",
    "N8",
    "Press0",
    "Temp0",
    "Humi0",
]
cast_fields = [
    "WD",
    "WS",
    "Height",
    "Xdistanc",
    "Ydistanc",
    "GeodetLat",
    "GeodetLon",
    "Prs",
    "Tmp",
    "Hum",
]


def numeric_condition_idx(df: pd.DataFrame, field: str, conditons: list):
    """evaluate AND conditions

    Parameters
    ----------
    df : pd.DataFrame

    field : str
        target field name
    conditons : list
        numerical condition

    Returns
    -------
    _type_
        AND conditions
    """

    idx_all = False
    for i in range(len(conditons)):
        idx = pd.to_numeric(df[field], errors="coerce") == conditons[i]
        idx_all = idx_all | idx if i != 0 else idx

    return idx_all


def get_qc_df(
    raw_df: pd.DataFrame,
    sonde_no: str,
    launch_time: datetime,
    **kwargs,
) -> pd.DataFrame:
    """get post QC DataFrame

    Parameters
    ----------
    raw_df : pd.DataFrame
        raw DataFrame
    sonde_no : str
        sonde No.
    launch_time : datetime
        launch time

    Returns
    -------
    pd.DataFrame
        post QC DataFrame
    """

    df = raw_df.copy()

    # --- rename column name.
    df.columns = [c.replace(" ", "") for c in df.columns]

    # --- remove error records.
    # observation status(ST)
    st = numeric_condition_idx(df, "ST", [7])
    # reciever error status(RE)
    re = numeric_condition_idx(df, "RE", [0, 4])
    # sonde No.(sondeN)
    sonden = df["SondeN"].astype(str) == sonde_no
    # GPS Flag(GF)
    gf = numeric_condition_idx(df, "GF", [4, 3, 2, 1])
    # number of the GPS satellite(N)
    n = pd.to_numeric(df["N"], errors="coerce") >= 4

    condition = st & re & sonden & gf & n
    df = df[condition].copy()
    df = df.reset_index(drop=True)

    # ---- time control
    time_cname = df.columns[0]

    df = df.rename(columns={time_cname: "Time"})

    if len(df) > 0:

        time0 = datetime.strptime(df["Time"].iloc[0], "%H:%M:%S")
        time0 = datetime(
            launch_time.year,
            launch_time.month,
            launch_time.day,
            time0.hour,
            time0.minute,
            time0.second,
        )
        df.loc[0, "Time"] = time0.strftime("%Y-%m-%d %H:%M:%S")
        for i in range(1, len(df)):
            time = datetime.strptime(df["Time"].iloc[i], "%H:%M:%S")
            time = datetime(
                time0.year,
                time0.month,
                time0.day,
                time.hour,
                time.minute,
                time.second,
            )
            time = time + timedelta(days=1) if time < time0 else time
            df.loc[i, "Time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            time0 = time

        df["Time"] = pd.to_datetime(df["Time"])
        df["Time"] = df["Time"].values.astype("datetime64[ns]")

        # --- error control
        prs = pd.to_numeric(df["Press0"], errors="coerce").values.copy()
        tmp = pd.to_numeric(df["Temp0"], errors="coerce").values.copy()
        hum = pd.to_numeric(df["Humi0"], errors="coerce").values.copy()

        # VE
        ve = pd.to_numeric(df["V"], errors="coerce").values
        for i in range(ve.shape[0]):
            b = format(ve[i], "03b")
            hum[i] = np.nan if b[0] == 1 else hum[i]
            tmp[i] = np.nan if b[1] == 1 else tmp[i]
            prs[i] = np.nan if b[2] == 1 else prs[i]

        # FE
        fe = pd.to_numeric(df["FE"], errors="coerce").values
        fcnts = pd.to_numeric(df["FCnt"], errors="coerce").values
        for i in range(fe.shape[0]):
            fcnt = fcnts[i]
            if math.isnan(fcnt):
                hum[i] = np.nan
                tmp[i] = np.nan
                prs[i] = np.nan
                continue
            fcnt = int(fcnt)
            hx = fe[i]
            if math.isnan(hx):
                hum[i] = np.nan
                tmp[i] = np.nan
                prs[i] = np.nan
            else:
                hx = f"{int(hx):04d}"
                if int(hx[0]) != 0:
                    hum[i] = np.nan
                    tmp[i] = np.nan
                    prs[i] = np.nan
                    continue
                hx1 = format(int(hx[1]), "03b")
                if int(hx1[0]) == 1 and fcnt % 2 == 0:
                    tmp[i] = np.nan
                if int(hx1[1]) == 1 and fcnt % 2 == 0:
                    hum[i] = np.nan
                if int(hx1[2]) == 1 and fcnt % 2 == 0:
                    prs[i] = np.nan
                hx2 = format(int(hx[2]), "03b")
                if int(hx2[0]) == 1 and fcnt % 2 == 1:
                    tmp[i] = np.nan
                if int(hx2[1]) == 1 and fcnt % 2 == 1:
                    hum[i] = np.nan
                if int(hx2[2]) == 1 and fcnt % 2 == 1:
                    prs[i] = np.nan

        df["Prs"] = prs
        df["Tmp"] = tmp
        df["Hum"] = hum

        for col in remove_columns:
            del df[col]
        df = df.reset_index(drop=True)

        # --- cast some fields
        for field in cast_fields:
            df[field] = pd.to_numeric(df[field], errors="coerce")

        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

        return df
    else:
        warnings.warn("No records found in the DataFrame.")
        df["Prs"] = np.nan
        df["Tmp"] = np.nan
        df["Hum"] = np.nan
        for col in remove_columns:
            if col in df.columns:
                del df[col]
        df = df.reset_index(drop=True)

        return df


def interp_df(
    df: pd.DataFrame, field: str, min: float, max: float, step: float, **kwargs
) -> pd.DataFrame:
    """interpolate with vertical coordinate(z or p).

    Parameters
    ----------
    df : pd.DataFrame
        target DataFrame
    field : str
        intepolate axis name.(""p" or "z")
    min : float
        minimum value of interpolated axis.
    max : float
        maximum value of interpolated axis.
    step : float
        step value of interpolated axis.

    Returns
    -------
    pd.DataFrame
        interpolated DataFrame

    Raises
    ------
    ValueError
        raise if field is not "z" or "p"
    """

    if field not in ["z", "p"]:
        raise ValueError("field must be either 'z' or 'p'.")

    col_name = "Height" if field == "z" else "Prs"
    df = df.sort_values(col_name).reset_index(drop=True)
    new_col = np.arange(min, max + step, step)
    df_interp = pd.DataFrame({col_name: new_col})
    for field in ["Time", *cast_fields]:

        if field == col_name:
            continue
        elif field == "Time":
            mask = df[col_name].notna() & df["Time"].notna()
            if np.sum(mask) < 3:
                df_interp["Time"] = np.full(
                    new_col.shape[0], np.datetime64("NaT", "ns")
                )
            else:
                x = df.loc[mask, col_name].to_numpy()
                t = df.loc[mask, "Time"].astype("int64").to_numpy()

                df_interp["Time"] = pd.to_datetime(
                    np.interp(new_col, x, t).astype("int64")
                )
        else:
            x = df[col_name].to_numpy(dtype=float)
            y = df[field].to_numpy(dtype=float)
            mask = ~np.isnan(x) & ~np.isnan(y)

            if np.sum(mask) < 3:
                df_interp[field] = np.full((new_col.shape[0],), np.nan)
            else:
                df_interp[field] = np.interp(
                    new_col,
                    x[mask],
                    y[mask],
                    left=np.nan,
                    right=np.nan,
                )

    return df_interp

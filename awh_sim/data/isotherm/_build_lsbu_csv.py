"""Parse the LSBU Yeboah & Darkwa 2021 FPB Primary Data (Run 1) xlsx into a tidy
breakthrough CSV: time + inlet/outlet RH + inlet/outlet T + C/C0 ratio.

Source: Mendeley Data 10.17632/xzss43z4fw.3, file 'FPB Primary Data  Run 1.xlsx'.
The breakthrough = outlet absolute humidity / inlet absolute humidity. We compute
absolute humidity (humidity ratio) from RH and T so the ratio is on a real water-
content basis, not raw RH%.
"""
import numpy as np
import pandas as pd
from pathlib import Path

D = Path("/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/data/isotherm")
src = D / "FPB_Primary_Data_Run1.xlsx"

raw = pd.read_excel(src, sheet_name=0, header=None)
# header row is index 6; data starts at row 7
hdr = raw.iloc[6]
data = raw.iloc[7:].reset_index(drop=True)

# identify columns by the row-6 labels
# col 0 sample index; 7 inlet T; 8 outlet T; 15 inlet RH; 16 outlet RH
def colidx(label_substr, start=0):
    for i, v in enumerate(hdr):
        if isinstance(v, str) and label_substr.lower() in v.lower() and i >= start:
            return i
    return None

# from inspection: 7=FPB Inlet (T), 8=FPB Outlet (T), 15=FPB Inlet (RH), 16=FPB Outlet (RH)
c_idx = 0
T_in_i, T_out_i = 7, 8
RH_in_i, RH_out_i = 15, 16

idx = pd.to_numeric(data[c_idx], errors="coerce")
T_in = pd.to_numeric(data[T_in_i], errors="coerce")
T_out = pd.to_numeric(data[T_out_i], errors="coerce")
RH_in = pd.to_numeric(data[RH_in_i], errors="coerce")
RH_out = pd.to_numeric(data[RH_out_i], errors="coerce")

df = pd.DataFrame({
    "sample": idx, "T_in_C": T_in, "T_out_C": T_out,
    "RH_in_pct": RH_in, "RH_out_pct": RH_out,
}).dropna(subset=["sample", "RH_in_pct", "RH_out_pct"])
df["time_s"] = (df["sample"] - df["sample"].iloc[0]) * 10.0  # 10 s sampling

def psat(T_C):
    return 611.21 * np.exp((18.678 - T_C / 234.5) * (T_C / (257.14 + T_C)))

# absolute humidity ratio omega = 0.622 * Pv/(P-Pv), Pv = RH*Psat(T)
P_atm = 101325.0
Pv_in = (df["RH_in_pct"] / 100.0) * psat(df["T_in_C"])
Pv_out = (df["RH_out_pct"] / 100.0) * psat(df["T_out_C"])
df["w_in"] = 0.622 * Pv_in / (P_atm - Pv_in)
df["w_out"] = 0.622 * Pv_out / (P_atm - Pv_out)

# breakthrough ratio = outlet/inlet absolute humidity (steady inlet -> use median inlet)
w_in_ref = df["w_in"].median()
df["ratio"] = df["w_out"] / w_in_ref
# clip tiny negatives
df["ratio"] = df["ratio"].clip(lower=0)

out = D / "lsbu_yeboah2021.csv"
df_out = df[["time_s", "RH_in_pct", "RH_out_pct", "T_in_C", "T_out_C", "ratio"]].copy()
df_out.to_csv(out, index=False)
print("wrote", out, "rows", len(df_out))
print("inlet RH median:", round(df["RH_in_pct"].median(), 1), "% ; T_in median:",
      round(df["T_in_C"].median(), 1), "C")
print("duration:", df["time_s"].iloc[-1] / 60.0, "min")
print("ratio start/end:", round(df["ratio"].iloc[0], 3), round(df["ratio"].iloc[-1], 3))
# t50 of the dataset
r = df["ratio"].to_numpy(); t = df["time_s"].to_numpy()
i = np.where(r >= 0.5)[0]
print("LSBU t50 (min):", round(t[i[0]] / 60.0, 1) if len(i) else "not reached")
print(df_out.head(8).to_string())
print("...")
print(df_out.tail(5).to_string())

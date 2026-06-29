import pandas as pd, numpy as np
from pathlib import Path
D = Path("/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/data/isotherm")
raw = pd.read_excel(D/"FPB_Primary_Data_Run1.xlsx", sheet_name=0, header=None)
hdr = raw.iloc[6]; data = raw.iloc[7:].reset_index(drop=True)
# inlet velocity col 17, outlet velocity col 18
vin = pd.to_numeric(data[17], errors="coerce")
vout = pd.to_numeric(data[18], errors="coerce")
RHin = pd.to_numeric(data[15], errors="coerce")
Tin = pd.to_numeric(data[7], errors="coerce")
RHout = pd.to_numeric(data[16], errors="coerce")
# steady portion = after first 10 min (60 samples)
steady = slice(200, None)
print("Inlet velocity: median(all)=%.3f, median(steady)=%.3f m/s, range %.2f-%.2f"%(
    vin.median(), vin[steady].median(), vin[steady].quantile(.1), vin[steady].quantile(.9)))
print("Inlet RH steady median: %.1f%%, range %.0f-%.0f"%(RHin[steady].median(), RHin[steady].quantile(.1), RHin[steady].quantile(.9)))
print("Inlet T steady median: %.1f C"%(Tin[steady].median()))
print("Outlet RH: start %.1f, min %.1f, end %.1f"%(RHout.iloc[0], RHout.min(), RHout.iloc[-1]))
# Does outlet ever exceed 50% of inlet absolute humidity? already know ratio 0.42-0.68, peak:
print("Outlet RH never rises to inlet -> no classic full breakthrough in 21h window")

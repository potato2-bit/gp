import pandas as pd
from pathlib import Path
f = Path("/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/data/isotherm/FPB_Primary_Data_Run1.xlsx")
xl = pd.ExcelFile(f)
print("SHEETS:", xl.sheet_names)
for s in xl.sheet_names:
    df = xl.parse(s, header=None, nrows=12)
    print(f"\n===== SHEET: {s}  shape(first12)={df.shape} =====")
    with pd.option_context("display.max_columns", 30, "display.width", 200):
        print(df.to_string(max_cols=20))

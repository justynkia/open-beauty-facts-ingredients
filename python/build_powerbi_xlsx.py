# Project contains data from Open Beauty Facts, available under the Open Database License

# Builds Excel files for Power BI using tables exported by openbeauty.py.
# Required files (relative to the project folder):
#   sql/01_schema.sql, sql/02_queries.sql
#   classification/ingredients_classification.csv
#   tables/products_table.csv, tables/product_categories.csv, tables/product_ingredients.csv
# Output: open_beauty_power_bi.xlsx (12 worksheets) and class_counts_ranking10.xlsx (worksheet Arkusz1)
# The script can be run from any folder. The project folder is the folder containing this script
# or its parent folder (if the script is located in a subfolder such as python/).
# 

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
if not (ROOT / "sql").exists():
    ROOT = ROOT.parent
OUT = ROOT  # output directory; can be changed, e.g. to ROOT / "powerbi"

REQUIRED = [
    "sql/01_schema.sql", "sql/02_queries.sql",
    "classification/ingredients_classification.csv",
    "tables/products_table.csv", "tables/product_categories.csv", "tables/product_ingredients.csv",
]
missing = [f for f in REQUIRED if not (ROOT / f).exists()]
if missing:
    sys.exit(f"Project folder: {ROOT}\nMissing files:\n  " + "\n  ".join(missing))
OUT.mkdir(parents=True, exist_ok=True)

con = sqlite3.connect(":memory:")
con.executescript((ROOT / "sql/01_schema.sql").read_text(encoding="utf-8"))

for table, file in [("products", "products_table"),
                    ("product_categories", "product_categories"),
                    ("product_ingredients", "product_ingredients")]:
    pd.read_csv(ROOT / f"tables/{file}.csv", dtype={"code": str}).to_sql(
        table, con, if_exists="append", index=False)

# Ingredient classification: detect the delimiter and encoding from the header.
# The allergen column supports both names: alergen_UE and allergen_EU.
class_path = ROOT / "classification/ingredients_classification.csv"
try:
    text = class_path.read_text(encoding="utf-8-sig")
    encoding = "utf-8-sig"
except UnicodeDecodeError:
    text = class_path.read_text(encoding="cp1250")
    encoding = "cp1250"
sep = ";" if ";" in text.splitlines()[0] else ","
ic = pd.read_csv(class_path, sep=sep, encoding=encoding)

db_cols = [r[1] for r in con.execute("PRAGMA table_info(ingredient_classes)")]
allergen_csv = next((c for c in ic.columns if c.strip().lower() in ("allergen_eu", "alergen_ue")), None)
if allergen_csv is None:
    sys.exit(f"The classification file does not contain an allergen column. Available columns: {list(ic.columns)}")
ic = ic.rename(columns={allergen_csv: db_cols[3]})
absent = [c for c in db_cols if c not in ic.columns]
if absent:
    sys.exit(f"Missing columns in the classification file: {absent}. Available columns: {list(ic.columns)}")
ic[db_cols].to_sql("ingredient_classes", con, if_exists="append", index=False)

con.executescript((ROOT / "sql/02_queries.sql").read_text(encoding="utf-8"))


def export(name):
    df = pd.read_sql(f"SELECT * FROM {name}", con)
    if "code" in df.columns:
        df["code"] = pd.to_numeric(df["code"])
    return df


sheets = ["ingredient_classes", "product_categories", "product_ingredients", "products",
          "vw_allergen_share", "vw_avg_category", "vw_cat_ingredient_share", "vw_avg_class",
          "vw_cat_ranking10", "vw_category", "vw_class_counts", "vw_class_ingredient_count"]
with pd.ExcelWriter(OUT / "open_beauty_power_bi.xlsx") as w:
    for s in sheets:
        export(s).to_excel(w, sheet_name=s, index=False)
export("vw_class_ranking10").to_excel(OUT / "class_counts_ranking10.xlsx", sheet_name="Arkusz1", index=False)
print(f"Success: Excel files saved to {OUT}")

#Project contains data from Open Beauty Facts, available under the Open Database License
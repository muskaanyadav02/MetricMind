import pandas as pd
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
CSV_PATH = os.path.join(ROOT_DIR, "global_superstore_raw.csv")

def inspect_dataset():
    if not os.path.exists(CSV_PATH):
        print(f"Error: Could not find file at path: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH, nrows=5)

    print("=" * 50)
    print("REAL COLUMN NAMES IN YOUR CSV:")
    print("=" * 50)
    for idx, col in enumerate(df.columns, 1):
        print(f"{idx}. '{col}'")

if __name__ == "__main__":
    inspect_dataset()
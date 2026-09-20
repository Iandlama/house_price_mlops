from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "housing.csv"
OUT_DIR = ROOT / "data" / "processed"

NUM_FEATURES = ["OverallQual", "GrLivArea", "GarageArea", "YearBuilt",
                "FullBath", "LotArea", "LotFrontage", "Fireplaces"]
CAT_FEATURES = []
TARGET = "SalePrice"
OUTLIER_COLS = ["GrLivArea", "LotArea", "LotFrontage"]


def main():
    df = pd.read_csv(RAW_PATH)
    df.columns = df.columns.str.replace(" ", "", regex=False)
    df = df[NUM_FEATURES + CAT_FEATURES + [TARGET]].copy()
    print(f"Loaded: {df.shape}")

    df = df.dropna(subset=[TARGET])

    train, test = train_test_split(df, test_size=0.2, random_state=42)
    train = train.copy()
    test = test.copy()

    for col in NUM_FEATURES:
        train_median = train[col].median()
        train[col] = train[col].fillna(train_median)
        test[col] = test[col].fillna(train_median)  

    for col in CAT_FEATURES:
        train_mode = train[col].mode()[0]
        train[col] = train[col].fillna(train_mode)
        test[col] = test[col].fillna(train_mode)

    before_outliers = len(train)
    for col in OUTLIER_COLS:
        q1, q3 = train[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        train = train[train[col].between(q1 - 3 * iqr, q3 + 3 * iqr)]
    print(f"Outliers removed from train: {before_outliers - len(train)}")


    OUT_DIR.mkdir(parents=True, exist_ok=True)
    train.to_csv(OUT_DIR / "train.csv", index=False)
    test.to_csv(OUT_DIR / "test.csv", index=False)
    print(f"Saved train={train.shape}, test={test.shape}")


if __name__ == "__main__":
    main()

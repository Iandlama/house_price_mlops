from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
MODEL_PATH = ROOT / "models" / "model.joblib"

NUM_FEATURES = ["OverallQual", "GrLivArea", "GarageArea", "YearBuilt",
                "FullBath", "LotArea", "LotFrontage", "Fireplaces"]
TARGET = "SalePrice"

PARAMS = {"n_estimators": 200, "max_depth": 12, "random_state": 42}


def main():
    
    train = pd.read_csv(DATA_DIR / "train.csv")
    test = pd.read_csv(DATA_DIR / "test.csv")
    X_train, y_train = train[NUM_FEATURES], train[TARGET]
    X_test, y_test = test[NUM_FEATURES], test[TARGET]

    
    model = Pipeline([
        ("poly", PolynomialFeatures(degree=2, interaction_only=True,
                                    include_bias=False)),
        ("scaler", StandardScaler()),
        ("rf", RandomForestRegressor(**PARAMS)),
    ])

    mlflow.set_tracking_uri("sqlite:///" + (ROOT / "mlflow.db").as_posix())
    mlflow.set_experiment("house-price")

    with mlflow.start_run():
        
        model.fit(X_train, y_train)

        
        pred = model.predict(X_test)
        metrics = {
            "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
            "mae": float(mean_absolute_error(y_test, pred)),
            "r2": float(r2_score(y_test, pred)),
        }

        
        mlflow.log_params(PARAMS)
        mlflow.log_param("features", ",".join(NUM_FEATURES))
        mlflow.log_param("feature_engineering", "poly_interactions+scaler")
        mlflow.log_param("sklearn_version", sklearn.__version__)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            "model",
            skops_trusted_types=["sklearn.tree._tree.Tree"],
        )
        print("Test metrics:", metrics)
        print("sklearn version:", sklearn.__version__)

    
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
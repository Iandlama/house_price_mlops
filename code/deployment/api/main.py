import os

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

MODEL_PATH = os.getenv("MODEL_PATH", "/models/model.joblib")
FEATURES = ["OverallQual", "GrLivArea", "GarageArea", "YearBuilt",
            "FullBath", "LotArea", "LotFrontage", "Fireplaces"]

model = joblib.load(MODEL_PATH)
app = FastAPI(title="House Price API")


class HouseFeatures(BaseModel):
    OverallQual: int = Field(ge=1, le=10)
    GrLivArea: float = Field(gt=0)
    GarageArea: float = Field(ge=0)
    YearBuilt: int = Field(ge=1800, le=2030)
    FullBath: int = Field(ge=0, le=10)
    LotArea: float = Field(gt=0)
    LotFrontage: float = Field(ge=0)
    Fireplaces: int = Field(ge=0, le=10)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(item: HouseFeatures):
    X = pd.DataFrame([item.model_dump()])[FEATURES]
    return {"prediction": float(model.predict(X)[0])}
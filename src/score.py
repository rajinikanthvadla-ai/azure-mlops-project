import json
import os
from typing import Any

import mlflow.pyfunc
import pandas as pd


FEATURE_COLUMNS = [
    "tenure",
    "monthly_charges",
    "total_charges",
    "contract_months",
    "support_calls",
    "paperless_billing",
]

model = None


def init() -> None:
    global model
    model_dir = os.environ["AZUREML_MODEL_DIR"]
    model = mlflow.pyfunc.load_model(model_dir)


def run(raw_data: str) -> str:
    if model is None:
        raise RuntimeError("Model is not initialized.")

    payload: dict[str, Any] = json.loads(raw_data)
    records = payload.get("data", payload)
    data = pd.DataFrame(records)
    data = data[FEATURE_COLUMNS]

    predictions = model.predict(data)
    labels = ["churn" if int(prediction) == 1 else "no_churn" for prediction in predictions]

    return json.dumps(
        {
            "predictions": [int(prediction) for prediction in predictions],
            "labels": labels,
        }
    )

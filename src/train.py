import argparse
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "tenure",
    "monthly_charges",
    "total_charges",
    "contract_months",
    "support_calls",
    "paperless_billing",
]
TARGET_COLUMN = "churn"
MODEL_NAME = "churn-model"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/churn.csv")
    parser.add_argument("--model-output", type=str, default="outputs/model")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.data)

    x = data[FEATURE_COLUMNS]
    y = data[TARGET_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    numeric_transformer = ColumnTransformer(
        transformers=[("numeric", StandardScaler(), FEATURE_COLUMNS)]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", numeric_transformer),
            ("classifier", RandomForestClassifier(n_estimators=100, random_state=42)),
        ]
    )

    with mlflow.start_run():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)

        accuracy = accuracy_score(y_test, predictions)
        f1 = f1_score(y_test, predictions)

        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)

        model_output = Path(args.model_output)
        model_output.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_output / "model.joblib")

        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name=MODEL_NAME,
        )

        print(f"Registered model: {MODEL_NAME}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"F1 score: {f1:.4f}")


if __name__ == "__main__":
    main()

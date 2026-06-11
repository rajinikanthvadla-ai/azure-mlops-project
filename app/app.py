import json
import os
from typing import Any

import requests
from flask import Flask, render_template, request


app = Flask(__name__)


FEATURE_DEFAULTS = {
    "tenure": 6,
    "monthly_charges": 89.0,
    "total_charges": 534.0,
    "contract_months": 1,
    "support_calls": 4,
    "paperless_billing": 1,
}


def call_azure_ml_endpoint(features: dict[str, Any]) -> dict[str, Any]:
    endpoint_url = os.environ.get("AML_ENDPOINT_URL")
    endpoint_key = os.environ.get("AML_ENDPOINT_KEY")

    if not endpoint_url or not endpoint_key:
        raise RuntimeError(
            "AML_ENDPOINT_URL and AML_ENDPOINT_KEY must be configured in App Service settings."
        )

    response = requests.post(
        endpoint_url,
        headers={
            "Authorization": f"Bearer {endpoint_key}",
            "Content-Type": "application/json",
        },
        json={"data": [features]},
        timeout=30,
    )
    response.raise_for_status()

    result = response.json()
    if isinstance(result, str):
        return json.loads(result)
    return result


@app.get("/health")
def health() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    prediction = None
    error = None
    values = FEATURE_DEFAULTS.copy()

    if request.method == "POST":
        try:
            values = {
                "tenure": int(request.form["tenure"]),
                "monthly_charges": float(request.form["monthly_charges"]),
                "total_charges": float(request.form["total_charges"]),
                "contract_months": int(request.form["contract_months"]),
                "support_calls": int(request.form["support_calls"]),
                "paperless_billing": int(request.form["paperless_billing"]),
            }
            prediction = call_azure_ml_endpoint(values)
        except Exception as exc:
            error = str(exc)

    return render_template(
        "index.html",
        values=values,
        prediction=prediction,
        error=error,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

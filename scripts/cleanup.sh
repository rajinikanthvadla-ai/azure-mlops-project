#!/usr/bin/env bash
set -euo pipefail

LOCATION="${LOCATION:-eastus}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-churn-mlops-lab}"
WORKSPACE="${WORKSPACE:-mlw-churn-lab}"
COMPUTE="${COMPUTE:-cpu-cluster}"
APP_PLAN="${APP_PLAN:-asp-churn-lab}"
WEBAPP="${WEBAPP:-app-churn-ui-lab}"
AML_ENDPOINT_NAME="${AML_ENDPOINT_NAME:-churn-endpoint}"
DELETE_RESOURCE_GROUP="${DELETE_RESOURCE_GROUP:-false}"

echo "Cleanup configuration:"
echo "  LOCATION=$LOCATION"
echo "  RESOURCE_GROUP=$RESOURCE_GROUP"
echo "  WORKSPACE=$WORKSPACE"
echo "  COMPUTE=$COMPUTE"
echo "  APP_PLAN=$APP_PLAN"
echo "  WEBAPP=$WEBAPP"
echo "  AML_ENDPOINT_NAME=$AML_ENDPOINT_NAME"
echo "  DELETE_RESOURCE_GROUP=$DELETE_RESOURCE_GROUP"
echo

if [[ "$DELETE_RESOURCE_GROUP" == "true" ]]; then
  echo "Deleting entire resource group: $RESOURCE_GROUP"
  az group delete --name "$RESOURCE_GROUP" --yes --no-wait
  echo "Delete submitted. Azure will remove the resource group asynchronously."
  exit 0
fi

echo "Deleting lab resources from resource group: $RESOURCE_GROUP"

if az ml online-endpoint show --name "$AML_ENDPOINT_NAME" --resource-group "$RESOURCE_GROUP" --workspace-name "$WORKSPACE" > /dev/null 2>&1; then
  echo "Deleting Azure ML online endpoint: $AML_ENDPOINT_NAME"
  az ml online-endpoint delete --name "$AML_ENDPOINT_NAME" --resource-group "$RESOURCE_GROUP" --workspace-name "$WORKSPACE" --yes
else
  echo "Azure ML endpoint not found: $AML_ENDPOINT_NAME"
fi

if az webapp show --name "$WEBAPP" --resource-group "$RESOURCE_GROUP" > /dev/null 2>&1; then
  echo "Deleting Web App: $WEBAPP"
  az webapp delete --name "$WEBAPP" --resource-group "$RESOURCE_GROUP"
else
  echo "Web App not found: $WEBAPP"
fi

if az appservice plan show --name "$APP_PLAN" --resource-group "$RESOURCE_GROUP" > /dev/null 2>&1; then
  echo "Deleting App Service Plan: $APP_PLAN"
  az appservice plan delete --name "$APP_PLAN" --resource-group "$RESOURCE_GROUP" --yes
else
  echo "App Service Plan not found: $APP_PLAN"
fi

if az ml compute show --name "$COMPUTE" --resource-group "$RESOURCE_GROUP" --workspace-name "$WORKSPACE" > /dev/null 2>&1; then
  echo "Deleting Azure ML compute: $COMPUTE"
  az ml compute delete --name "$COMPUTE" --resource-group "$RESOURCE_GROUP" --workspace-name "$WORKSPACE" --yes
else
  echo "Azure ML compute not found: $COMPUTE"
fi

if az ml workspace show --name "$WORKSPACE" --resource-group "$RESOURCE_GROUP" > /dev/null 2>&1; then
  echo "Deleting Azure ML workspace: $WORKSPACE"
  az ml workspace delete --name "$WORKSPACE" --resource-group "$RESOURCE_GROUP" --yes
else
  echo "Azure ML workspace not found: $WORKSPACE"
fi

echo
echo "Cleanup completed."
echo "The resource group was kept. To delete the full resource group, run:"
echo "  DELETE_RESOURCE_GROUP=true bash scripts/cleanup.sh"

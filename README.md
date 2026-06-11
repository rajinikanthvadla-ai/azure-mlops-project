# Azure ML Churn MLOps Lab

This lab trains a sample churn model in Azure ML, registers the model, deploys it to an Azure ML managed online endpoint, and deploys a Flask UI to Azure App Service.

The browser does **not** call Azure ML directly. The Flask backend calls the Azure ML endpoint with the endpoint key stored in App Service application settings.

## Architecture

```text
GitHub Actions
  -> Azure ML training job
  -> Register churn-model
  -> Deploy Azure ML online endpoint
  -> Deploy Flask UI to App Service
  -> Flask backend calls Azure ML endpoint for inference
```

## What Runs Where

Use Azure CLI locally for one-time infrastructure creation:

- Resource group
- Azure ML workspace
- Azure ML compute cluster
- App Service plan
- Web App
- GitHub service principal

Use GitHub Actions for the pipeline:

- Train model
- Register model
- Create/update Azure ML endpoint
- Create/update Azure ML deployment
- Configure App Service with Azure ML endpoint URL/key
- Deploy Flask UI

Use Azure ML Studio only to verify:

- Jobs
- Metrics
- Registered model
- Endpoint
- Deployment logs

## Repository Structure

```text
.
+-- .github/workflows/
|   +-- 01-train-register-model.yml
|   +-- 02-deploy-endpoint.yml
|   +-- 03-deploy-appservice.yml
+-- app/
|   +-- app.py
|   +-- requirements.txt
|   +-- templates/index.html
+-- data/churn.csv
+-- ml/
|   +-- conda.yml
|   +-- deployment.yml
|   +-- endpoint.yml
|   +-- environment.yml
|   +-- job.yml
+-- src/
    +-- score.py
    +-- train.py
```

## 1. Create Infrastructure With Azure CLI

Login and select subscription:

```powershell
az login
az account set --subscription "<SUBSCRIPTION_ID>"
az extension add --name ml --upgrade --yes
```

Set lab values:

```powershell
$LOCATION = "eastus"
$RESOURCE_GROUP = "rg-churn-mlops-lab"
$WORKSPACE = "mlw-churn-lab"
$COMPUTE = "cpu-cluster"
$APP_PLAN = "asp-churn-lab"
$WEBAPP = "app-churn-ui-lab"
```

Create the resource group:

```powershell
az group create `
  --name $RESOURCE_GROUP `
  --location $LOCATION
```

Create the Azure ML workspace:

```powershell
az ml workspace create `
  --name $WORKSPACE `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION
```

Create Azure ML compute:

```powershell
az ml compute create `
  --name $COMPUTE `
  --resource-group $RESOURCE_GROUP `
  --workspace-name $WORKSPACE `
  --type amlcompute `
  --min-instances 0 `
  --max-instances 2 `
  --size Standard_DS3_v2
```

Create App Service:

```powershell
az appservice plan create `
  --name $APP_PLAN `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --sku B1 `
  --is-linux

az webapp create `
  --name $WEBAPP `
  --resource-group $RESOURCE_GROUP `
  --plan $APP_PLAN `
  --runtime "PYTHON:3.11"
```

### Azure Portal UI Navigation For Infrastructure

If you want to create or verify the same infrastructure from the Azure Portal UI, use this navigation:

```text
Azure Portal -> Resource groups -> Create
```

Use:

```text
Resource group: rg-churn-mlops-lab
Region: eastus
```

Create or verify the Azure ML workspace:

```text
Azure Portal -> Search "Azure Machine Learning" -> Create
```

Use:

```text
Workspace name: mlw-churn-lab
Resource group: rg-churn-mlops-lab
Region: eastus
```

Create or verify Azure ML compute:

```text
Azure ML Studio -> Manage -> Compute -> Compute clusters -> New
```

Use:

```text
Compute name: cpu-cluster
Virtual machine size: Standard_DS3_v2
Minimum instances: 0
Maximum instances: 2
```

Create or verify App Service:

```text
Azure Portal -> Search "App Services" -> Create -> Web App
```

Use:

```text
Web App name: app-churn-ui-lab
Publish: Code
Runtime stack: Python 3.11
Operating System: Linux
App Service Plan: asp-churn-lab
Pricing plan: B1
```

## 2. Create GitHub Azure Login Secret

Create a service principal for GitHub Actions:

```powershell
$SUBSCRIPTION_ID = az account show --query id -o tsv

az ad sp create-for-rbac `
  --name "sp-github-churn-mlops-lab" `
  --role contributor `
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" `
  --json-auth
```

Copy the full JSON output into this GitHub repository secret:

```text
AZURE_CREDENTIALS
```

GitHub UI navigation:

```text
GitHub repository -> Settings -> Secrets and variables -> Actions -> Secrets -> New repository secret
```

Use:

```text
Name: AZURE_CREDENTIALS
Secret: full JSON output from az ad sp create-for-rbac
```

## 3. Create GitHub Repository Variables

In GitHub, go to:

```text
Settings -> Secrets and variables -> Actions -> Variables
```

Add:

```text
AZURE_RESOURCE_GROUP = rg-churn-mlops-lab
AZURE_ML_WORKSPACE  = mlw-churn-lab
AZURE_WEBAPP_NAME   = app-churn-ui-lab
AML_ENDPOINT_NAME   = churn-endpoint
AML_DEPLOYMENT_NAME = blue
```

## 4. Run GitHub Actions Pipelines

Run these workflows in order:

1. `01 Train and Register Churn Model`
2. `02 Deploy Azure ML Endpoint`
3. `03 Deploy App Service UI`

After the first successful manual run, pushes to `main` can trigger the relevant workflows automatically.

GitHub Actions UI navigation:

```text
GitHub repository -> Actions -> 01 Train and Register Churn Model -> Run workflow
GitHub repository -> Actions -> 02 Deploy Azure ML Endpoint -> Run workflow
GitHub repository -> Actions -> 03 Deploy App Service UI -> Run workflow
```

Azure ML Studio verification navigation:

```text
Azure ML Studio -> Jobs
Azure ML Studio -> Models
Azure ML Studio -> Endpoints -> Real-time endpoints
```

## 5. Test The Azure ML Endpoint

Get endpoint details:

```powershell
az ml online-endpoint show `
  --name churn-endpoint `
  --resource-group rg-churn-mlops-lab `
  --workspace-name mlw-churn-lab

az ml online-endpoint get-credentials `
  --name churn-endpoint `
  --resource-group rg-churn-mlops-lab `
  --workspace-name mlw-churn-lab
```

Sample request payload:

```json
{
  "data": [
    {
      "tenure": 6,
      "monthly_charges": 89.0,
      "total_charges": 534.0,
      "contract_months": 1,
      "support_calls": 4,
      "paperless_billing": 1
    }
  ]
}
```

Azure ML Studio endpoint UI navigation:

```text
Azure ML Studio -> Endpoints -> Real-time endpoints -> churn-endpoint
```

Use the endpoint page to check:

```text
Scoring URI
Deployment status
Traffic allocation
Logs
Test tab
```

## 6. Test The App Service UI

Open:

```text
https://app-churn-ui-lab.azurewebsites.net
```

The UI submits the form to Flask. Flask reads these App Service settings and calls Azure ML from the backend:

```text
AML_ENDPOINT_URL
AML_ENDPOINT_KEY
```

These settings are created by the `03 Deploy App Service UI` workflow.

Azure Portal App Service UI navigation:

```text
Azure Portal -> App Services -> app-churn-ui-lab -> Overview
```

Use:

```text
Browse: open the deployed UI
Configuration -> Application settings: verify AML_ENDPOINT_URL and AML_ENDPOINT_KEY
Log stream: check Flask app logs
Deployment Center: check deployment status
```

## Cleanup

To delete all lab resources:

```powershell
az group delete --name rg-churn-mlops-lab --yes --no-wait
```
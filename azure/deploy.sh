# ============================================================
# OmniDev AI — Azure Container Apps Deployment
# ============================================================
# Deploy using Azure CLI:
#   az login
#   chmod +x azure/deploy.sh
#   ./azure/deploy.sh
# ============================================================

# ── Variables ─────────────────────────────────────────────────
RESOURCE_GROUP="omnidev-ai-rg"
LOCATION="eastus"
ACR_NAME="omnidevacr"
ENVIRONMENT="omnidev-env"
LOG_ANALYTICS_WORKSPACE="omnidev-logs"

echo "=== OmniDev AI — Azure Deployment ==="

# ── 1. Resource Group ─────────────────────────────────────────
echo "[1/8] Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# ── 2. Azure Container Registry ──────────────────────────────
echo "[2/8] Creating container registry..."
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# ── 3. Build & Push Images ───────────────────────────────────
echo "[3/8] Building and pushing Docker images..."
az acr build \
  --registry $ACR_NAME \
  --image omnidev-backend:latest \
  --file backend/Dockerfile.prod \
  backend/

az acr build \
  --registry $ACR_NAME \
  --image omnidev-frontend:latest \
  --file frontend/Dockerfile.prod \
  --build-arg NEXT_PUBLIC_API_URL=https://omnidev-backend.${LOCATION}.azurecontainerapps.io \
  --build-arg NEXT_PUBLIC_WS_URL=wss://omnidev-backend.${LOCATION}.azurecontainerapps.io/ws \
  frontend/

# ── 4. Log Analytics Workspace ───────────────────────────────
echo "[4/8] Creating Log Analytics workspace..."
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE

LOG_ANALYTICS_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --query customerId -o tsv)

LOG_ANALYTICS_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_ANALYTICS_WORKSPACE \
  --query primarySharedKey -o tsv)

# ── 5. Container Apps Environment ─────────────────────────────
echo "[5/8] Creating Container Apps environment..."
az containerapp env create \
  --name $ENVIRONMENT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --logs-workspace-id "$LOG_ANALYTICS_ID" \
  --logs-workspace-key "$LOG_ANALYTICS_KEY"

# ── 6. Azure Database for PostgreSQL ─────────────────────────
echo "[6/8] Creating PostgreSQL Flexible Server..."
PG_PASSWORD=$(openssl rand -base64 24)
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name omnidev-pg \
  --location $LOCATION \
  --admin-user omnidev \
  --admin-password "$PG_PASSWORD" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --yes

az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name omnidev-pg \
  --database-name omnidev

az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name omnidev-pg \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

PG_HOST="omnidev-pg.postgres.database.azure.com"
DATABASE_URL="postgresql+asyncpg://omnidev:${PG_PASSWORD}@${PG_HOST}:5432/omnidev?ssl=require"

# ── 7. Azure Cache for Redis ─────────────────────────────────
echo "[7/8] Creating Azure Cache for Redis..."
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name omnidev-redis \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0 \
  --enable-non-ssl-port

REDIS_KEY=$(az redis list-keys \
  --resource-group $RESOURCE_GROUP \
  --name omnidev-redis \
  --query primaryKey -o tsv)
REDIS_URL="redis://:${REDIS_KEY}@omnidev-redis.redis.cache.windows.net:6379/0"

# ── 8. Deploy Container Apps ─────────────────────────────────
echo "[8/8] Deploying container apps..."
SECRET_KEY=$(openssl rand -hex 32)

# Backend
az containerapp create \
  --name omnidev-backend \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image "${ACR_LOGIN_SERVER}/omnidev-backend:latest" \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_NAME \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 5 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars \
    "DATABASE_URL=${DATABASE_URL}" \
    "REDIS_URL=${REDIS_URL}" \
    "CELERY_BROKER_URL=${REDIS_URL}" \
    "SECRET_KEY=${SECRET_KEY}" \
    "ENVIRONMENT=production" \
    "CORS_ORIGINS=https://omnidev-frontend.${LOCATION}.azurecontainerapps.io"

# Frontend
BACKEND_FQDN=$(az containerapp show \
  --name omnidev-backend \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)

az containerapp create \
  --name omnidev-frontend \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image "${ACR_LOGIN_SERVER}/omnidev-frontend:latest" \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_NAME \
  --registry-password "$ACR_PASSWORD" \
  --target-port 3000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    "NODE_ENV=production"

# Celery Worker
az containerapp create \
  --name omnidev-worker \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image "${ACR_LOGIN_SERVER}/omnidev-backend:latest" \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_NAME \
  --registry-password "$ACR_PASSWORD" \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --command "celery" "-A" "app.utils.celery_app:celery_app" "worker" "--loglevel=info" "-Q" "agent-queue,notification-queue" "--concurrency=4" \
  --env-vars \
    "DATABASE_URL=${DATABASE_URL}" \
    "REDIS_URL=${REDIS_URL}" \
    "CELERY_BROKER_URL=${REDIS_URL}" \
    "SECRET_KEY=${SECRET_KEY}" \
    "ENVIRONMENT=production"

# ── Output ────────────────────────────────────────────────────
FRONTEND_URL=$(az containerapp show \
  --name omnidev-frontend \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)

echo ""
echo "============================================"
echo "  OmniDev AI — Deployed to Azure!"
echo "============================================"
echo "  Frontend:  https://${FRONTEND_URL}"
echo "  Backend:   https://${BACKEND_FQDN}"
echo "  PostgreSQL: ${PG_HOST}"
echo "  Redis:     omnidev-redis.redis.cache.windows.com"
echo ""
echo "  PG Password: ${PG_PASSWORD}"
echo "  Secret Key:  ${SECRET_KEY}"
echo "  (Save these securely!)"
echo "============================================"

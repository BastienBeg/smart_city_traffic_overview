
Write-Host "Building api-gateway (Root Context)..."
docker build -t api-gateway:latest -f services/api-gateway/Dockerfile .
if ($LASTEXITCODE -ne 0) { exit 1 }

# Write-Host "Building web-dashboard (Root Context)..."
# docker build -t web-dashboard:latest -f services/web-dashboard/Dockerfile .
# if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Building camera-service..."
docker build -t camera-service:latest -f services/camera-service/Dockerfile services/camera-service
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Building inference-service..."
docker build -t inference-service:latest -f services/inference-service/Dockerfile services/inference-service
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Building training-controller..."
docker build -t training-controller:latest -f services/training-controller/Dockerfile services/training-controller
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Building training-job..."
docker build -t training-job:latest -f services/training-job/Dockerfile services/training-job
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "All images built successfully."

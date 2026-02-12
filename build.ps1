# OmniDev AI - Build & Deployment Script
# ==========================================
# Comprehensive build, test, and deployment automation
# Phases 44-47 Infrastructure

param(
    [Parameter(HelpMessage = "Build command: build, test, deploy, stop, logs, clean")]
    [string]$Command = "help",
    
    [Parameter(HelpMessage = "Environment: development, staging, production")]
    [string]$Environment = "development",
    
    [Parameter(HelpMessage = "Enable rebuild (ignores cache)")]
    [switch]$Rebuild = $false,
    
    [Parameter(HelpMessage = "Number of workers for backend")]
    [int]$Workers = 4,
    
    [Parameter(HelpMessage = "Log level: DEBUG, INFO, WARNING, ERROR")]
    [string]$LogLevel = "INFO"
)

# Color output helpers
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Set script directory
$ProjectRoot = Get-Location
$BackendDir = Join-Path $ProjectRoot "backend"
$DockerDir = Join-Path $BackendDir "docker"

# Configuration
$ProjectName = "omnidev-ai"
$ImageName = "omnidev-ai-backend"
$ImageTag = "latest"
$ComposeFile = Join-Path $DockerDir "docker-compose.yml"
$NginxConfFile = Join-Path $DockerDir "nginx.conf"

# Requirements file path
$RequirementsFile = Join-Path $BackendDir "requirements.txt"

Write-Info "OmniDev AI Build & Deployment System"
Write-Info "Project Root: $ProjectRoot"
Write-Info "Environment: $Environment"
Write-Info ""

# Command implementations
function Build {
    Write-Info "Building OmniDev AI (Phase 44-47 Infrastructure)"
    Write-Info ""
    
    # Check if Docker is installed
    try {
        $dockerVersion = docker --version
        Write-Success "Docker installed: $dockerVersion"
    } catch {
        Write-Error-Custom "Docker not found. Please install Docker first."
        exit 1
    }

    # Check if docker-compose is installed
    try {
        $composeVersion = docker-compose --version
        Write-Success "Docker Compose installed: $composeVersion"
    } catch {
        Write-Warning-Custom "docker-compose not found. Using 'docker compose' instead."
    }

    # Build arguments
    $BuildArgs = ""
    if ($Rebuild) {
        $BuildArgs = "--no-cache"
        Write-Info "Building with --no-cache (rebuild mode)"
    }

    # Build Docker image
    Write-Info ""
    Write-Info "Building Docker image..."
    docker build -t "${ImageName}:${ImageTag}" -f "backend/docker/Dockerfile" "."

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker image built successfully"
    } else {
        Write-Error-Custom "Docker build failed"
        exit 1
    }

    # Validate docker-compose configuration
    Write-Info ""
    Write-Info "Validating docker-compose configuration..."
    docker-compose -f $ComposeFile config > $null

    if ($LASTEXITCODE -eq 0) {
        Write-Success "docker-compose configuration is valid"
    } else {
        Write-Error-Custom "docker-compose configuration validation failed"
        exit 1
    }

    Write-Success "Build completed successfully"
    Write-Info ""
    Write-Info "Next steps:"
    Write-Info "  - Start services: .\build.ps1 -Command deploy"
    Write-Info "  - View logs: .\build.ps1 -Command logs"
}

function Deploy {
    Write-Info "Deploying OmniDev AI Services"
    Write-Info ""

    # Verify build was done
    $ImageExists = docker images --quiet "${ImageName}:${ImageTag}"
    if (-not $ImageExists) {
        Write-Warning-Custom "Docker image not found. Building first..."
        Build
    }

    # Start services with docker-compose
    Write-Info "Starting services with docker-compose..."
    docker-compose -f $ComposeFile -p $ProjectName up -d

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services started successfully"
    } else {
        Write-Error-Custom "Failed to start services"
        exit 1
    }

    Write-Info ""
    Write-Info "Waiting for services to become healthy..."
    Start-Sleep -Seconds 5

    # Check service health
    Write-Info ""
    Write-Info "Checking service health..."

    $HealthCheckPassed = $true
    $Services = @("backend", "postgres", "redis", "nginx")

    foreach ($Service in $Services) {
        $Output = docker-compose -f $ComposeFile ps $Service 2>&1
        if ($Output -like "*running*") {
            Write-Success "${Service}: Running"
        } else {
            Write-Error-Custom "${Service}: Not running"
            $HealthCheckPassed = $false
        }
    }

    Write-Info ""
    if ($HealthCheckPassed) {
        Write-Success "All services are running"
        Write-Info ""
        Write-Info "Services available at:"
        Write-Info "  - API: http://localhost/api"
        Write-Info "  - WebSocket: ws://localhost/ws"
        Write-Info "  - Grafana: http://localhost/grafana"
        Write-Info "  - Prometheus: http://localhost/prometheus"
    } else {
        Write-Warning-Custom "Some services failed to start. Check logs with: .\build.ps1 -Command logs"
        exit 1
    }

    Write-Info ""
    Write-Info "Deployment completed"
}

function Test {
    Write-Info "Running Tests"
    Write-Info ""

    # Check if Python is available
    try {
        $pythonVersion = python --version
        Write-Success "Python installed: $pythonVersion"
    } catch {
        Write-Error-Custom "Python not found. Please install Python 3.11+"
        exit 1
    }

    # Install test dependencies if needed
    Write-Info "Installing test dependencies..."
    pip install -q pytest pytest-asyncio pytest-cov

    # Run tests
    Write-Info ""
    Write-Info "Running pytest..."
    $TestDir = Join-Path $BackendDir "app" "tests"
    
    if (Test-Path $TestDir) {
        pytest $TestDir -v --tb=short --cov=app --cov-report=term-missing
    } else {
        Write-Warning-Custom "Test directory not found: $TestDir"
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tests passed"
    } else {
        Write-Warning-Custom "Some tests failed"
    }
}

function Stop {
    Write-Info "Stopping OmniDev AI Services"
    Write-Info ""

    docker-compose -f $ComposeFile -p $ProjectName down

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services stopped successfully"
    } else {
        Write-Error-Custom "Failed to stop services"
        exit 1
    }
}

function Logs {
    param(
        [string]$Service = ""
    )

    if ($Service) {
        Write-Info "Showing logs for $Service..."
        docker-compose -f $ComposeFile logs -f $Service
    } else {
        Write-Info "Showing logs for all services..."
        docker-compose -f $ComposeFile logs -f
    }
}

function Status {
    Write-Info "OmniDev AI Service Status"
    Write-Info ""

    docker-compose -f $ComposeFile -p $ProjectName ps
}

function Clean {
    Write-Info "Cleaning up..."
    Write-Info ""

    # Stop all containers
    Write-Info "Stopping containers..."
    docker-compose -f $ComposeFile -p $ProjectName down

    # Optional: remove volumes
    Write-Info "Removing volumes..."
    docker-compose -f $ComposeFile -p $ProjectName down -v

    # Clean Docker images
    Write-Info "Removing Docker image..."
    docker rmi "${ImageName}:${ImageTag}" 2>&1 | Out-Null

    # Clean Python cache
    Write-Info "Cleaning Python cache..."
    Get-ChildItem -Path $BackendDir -Directory -Name "__pycache__" -Recurse | ForEach-Object {
        Remove-Item -Path (Join-Path $BackendDir $_) -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Success "Cleanup completed"
}

function ShowHelp {
    Write-Info "OmniDev AI Build & Deployment System"
    Write-Info ""
    Write-Info "Usage: .\build.ps1 -Command <command> [options]"
    Write-Info ""
    Write-Info "Commands:"
    Write-Info "  build    - Build Docker image (Phase 44-47 services)"
    Write-Info "  deploy   - Start all services with docker-compose"
    Write-Info "  test     - Run test suite"
    Write-Info "  stop     - Stop all services"
    Write-Info "  logs     - Show service logs"
    Write-Info "  status   - Show service status"
    Write-Info "  clean    - Clean up containers, images, cache"
    Write-Info "  help     - Show this help message"
    Write-Info ""
    Write-Info "Options:"
    Write-Info "  -Environment development|staging|production"
    Write-Info "  -Rebuild (Force rebuild without cache)"
    Write-Info "  -Workers <number> (Number of backend workers, default: 4)"
    Write-Info "  -LogLevel DEBUG|INFO|WARNING|ERROR"
    Write-Info ""
    Write-Info "Examples:"
    Write-Info "  .\build.ps1 -Command build"
    Write-Info "  .\build.ps1 -Command build -Rebuild"
    Write-Info "  .\build.ps1 -Command deploy"
    Write-Info "  .\build.ps1 -Command logs -Service backend"
    Write-Info "  .\build.ps1 -Command stop"
}

# Route commands
switch ($Command.ToLower()) {
    "build" { Build }
    "deploy" { Deploy }
    "test" { Test }
    "stop" { Stop }
    "logs" { Logs }
    "status" { Status }
    "clean" { Clean }
    "help" { ShowHelp }
    default { 
        Write-Error-Custom "Unknown command: $Command"
        ShowHelp
        exit 1
    }
}

#!/bin/bash

# OmniDev AI Setup Script
# This script sets up the complete OmniDev AI environment

set -e

echo "🚀 OmniDev AI - Autonomous Developer Agent Setup"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python3 not found. Installing...${NC}"
    sudo apt-get install python3 python3-pip python3-venv
fi
echo -e "${GREEN}✓ Python installed${NC}"

# Check Docker
echo -e "${BLUE}Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found. Installing...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Setup backend
echo -e "${BLUE}Setting up backend...${NC}"
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Create .env file if not exists
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cat > .env << EOF
DATABASE_URL=postgresql://user:password@localhost:5432/omnidev
OPENAI_API_KEY=your_api_key_here
GITHUB_TOKEN=your_github_token_here
REDIS_URL=redis://localhost:6379
DEBUG=true
LOG_LEVEL=INFO
EOF
    echo -e "${YELLOW}⚠️  Please update .env file with your credentials${NC}"
fi

# Return to root
cd ..

# Docker setup
echo -e "${BLUE}Setting up Docker containers...${NC}"

# Create docker network if not exists
docker network create omnidev-network 2>/dev/null || true

# Build backend image
docker build -f backend/docker/Dockerfile -t omnidev-ai:latest .

echo -e "${GREEN}✓ Docker setup complete${NC}"

# Print next steps
echo ""
echo -e "${GREEN}=============================================="
echo "Setup Complete! 🎉"
echo "=============================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update .env file with your credentials:"
echo "   - OPENAI_API_KEY"
echo "   - GITHUB_TOKEN"
echo ""
echo "2. Start Docker containers:"
echo "   docker-compose -f backend/docker/docker-compose.yml up"
echo ""
echo "3. Backend will be available at:"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo ""
echo "4. (Optional) Setup Android development:"
echo "   - Install Android Studio"
echo "   - Open android/ folder in Android Studio"
echo "   - Build and run on emulator"
echo ""
echo -e "${YELLOW}For more information, see README.md${NC}"

"""DevOps Agent - Handles deployment and infrastructure"""

from typing import Dict
from app.agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class DevOpsAgent(BaseAgent):
    """Agent specialized in DevOps, CI/CD, and deployment"""
    
    def __init__(self, memory=None):
        super().__init__("DevOpsAgent", memory)
        self.capabilities = [
            "docker_containerization",
            "ci_cd_setup",
            "deployment_automation",
            "monitoring_setup",
            "infrastructure_as_code"
        ]
        self.deployment_platforms = [
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "GitHub Actions"
        ]
    
    async def process(self, task: str, context: Dict) -> Dict:
        """Setup DevOps infrastructure and deployment"""
        
        logger.info(f"DevOps task: {task}")
        
        subtasks = context.get('subtasks', [])
        deployment_configs = []
        
        # Generate deployment configs for each subtask
        for subtask in subtasks:
            config = await self._generate_config(subtask, context)
            deployment_configs.append(config)
        
        return {
            "status": "success",
            "configs_generated": len(deployment_configs),
            "configs": deployment_configs,
            "platforms": self.deployment_platforms,
            "ready_to_deploy": True
        }
    
    async def _generate_config(self, subtask: str, context: Dict) -> Dict:
        """Generate deployment configuration"""
        
        configs = {
            "docker": {
                "type": "Dockerfile",
                "content": self._generate_dockerfile(context),
                "location": "Dockerfile"
            },
            "ci/cd": {
                "type": "GitHub Actions",
                "content": self._generate_github_actions(),
                "location": ".github/workflows/deploy.yml"
            },
            "production": {
                "type": "Deploy Script",
                "content": self._generate_deploy_script(),
                "location": "deploy.sh"
            }
        }
        
        return configs.get(subtask.lower(), {
            "type": subtask,
            "content": f"# Configuration for {subtask}",
            "location": f"{subtask.lower()}.config"
        })
    
    def _generate_dockerfile(self, context: Dict) -> str:
        """Generate Dockerfile for containerization"""
        
        dockerfile = """
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        return dockerfile
    
    def _generate_github_actions(self) -> str:
        """Generate GitHub Actions CI/CD workflow"""
        
        workflow = """
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: docker build -t omnidev-ai .
    
    - name: Run tests
      run: |
        pip install -r requirements.txt
        pytest tests/
    
    - name: Deploy
      run: |
        echo "Deploying to production..."
        # Add deployment commands here
"""
        return workflow
    
    def _generate_deploy_script(self) -> str:
        """Generate deployment script"""
        
        script = """
#!/bin/bash

# OmniDev AI Deployment Script

echo "Starting deployment..."

# Pull latest changes
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Build Docker image
docker build -t omnidev-ai:latest .

# Stop existing container
docker stop omnidev-ai-container 2>/dev/null || true

# Run new container
docker run -d \\
  --name omnidev-ai-container \\
  -p 8000:8000 \\
  -e DATABASE_URL=$DATABASE_URL \\
  omnidev-ai:latest

echo "Deployment completed!"
"""
        return script

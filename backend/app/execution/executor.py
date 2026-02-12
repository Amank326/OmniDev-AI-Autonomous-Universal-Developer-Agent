"""Execution Engine - Runs actual commands and tasks"""

import subprocess
import os
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ExecutionEngine:
    """Executes code, creates files, and manages project structure"""
    
    def __init__(self, project_root: str = "./projects"):
        self.project_root = Path(project_root)
        self.project_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Execution Engine initialized at {project_root}")
    
    async def create_file(self, project_id: str, filename: str, content: str) -> bool:
        """Create a file in project directory"""
        try:
            project_path = self.project_root / project_id
            project_path.mkdir(parents=True, exist_ok=True)
            
            file_path = project_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_path.write_text(content)
            logger.info(f"Created file: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating file: {str(e)}")
            return False
    
    async def create_folder(self, project_id: str, folder_name: str) -> bool:
        """Create a folder in project directory"""
        try:
            project_path = self.project_root / project_id / folder_name
            project_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created folder: {project_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating folder: {str(e)}")
            return False
    
    async def run_command(self, project_id: str, command: str) -> Dict:
        """Execute shell command in project directory"""
        try:
            project_path = self.project_root / project_id
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            logger.info(f"Command executed: {command}")
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {command}")
            return {
                "status": "timeout",
                "error": "Command execution timed out"
            }
        
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def initialize_git(self, project_id: str, repo_name: str) -> bool:
        """Initialize git repository for project"""
        try:
            project_path = self.project_root / project_id
            
            commands = [
                "git init",
                f"git config user.name 'OmniDev AI'",
                f"git config user.email 'ai@omnidev.com'",
                "git add .",
                "git commit -m 'Initial commit by OmniDev AI'"
            ]
            
            for cmd in commands:
                await self.run_command(project_id, cmd)
            
            logger.info(f"Git repository initialized: {project_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing git: {str(e)}")
            return False
    
    async def push_to_github(
        self,
        project_id: str,
        github_url: str,
        branch: str = "main"
    ) -> bool:
        """Push project to GitHub"""
        try:
            commands = [
                f"git remote add origin {github_url}",
                f"git branch -M {branch}",
                f"git push -u origin {branch}"
            ]
            
            for cmd in commands:
                result = await self.run_command(project_id, cmd)
                if result['status'] != 'success':
                    return False
            
            logger.info(f"Project pushed to GitHub: {github_url}")
            return True
        
        except Exception as e:
            logger.error(f"Error pushing to GitHub: {str(e)}")
            return False
    
    async def build_docker(self, project_id: str) -> bool:
        """Build Docker image for project"""
        try:
            result = await self.run_command(
                project_id,
                "docker build -t omnidev-ai:latest ."
            )
            
            if result['status'] == 'success':
                logger.info(f"Docker image built: {project_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error building Docker: {str(e)}")
            return False
    
    async def deploy(self, project_id: str, platform: str = "local") -> Dict:
        """Deploy project to specified platform"""
        
        deployment_results = {
            "project_id": project_id,
            "platform": platform,
            "status": "success",
            "steps": []
        }
        
        if platform == "docker":
            build_success = await self.build_docker(project_id)
            deployment_results["steps"].append({
                "step": "build_docker",
                "status": "success" if build_success else "failed"
            })
        
        elif platform == "github":
            git_success = await self.initialize_git(project_id, project_id)
            deployment_results["steps"].append({
                "step": "init_git",
                "status": "success" if git_success else "failed"
            })
        
        logger.info(f"Deployment completed: {project_id} on {platform}")
        return deployment_results

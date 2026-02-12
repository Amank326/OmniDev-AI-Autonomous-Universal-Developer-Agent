"""
Build and Deploy CLI Tool
Command-line interface for building, testing, and deploying applications
Phase 41: CI/CD Pipeline & Automated Deployment
"""

import logging
import subprocess
import sys
import json
import time
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime
import click
from click import (
    Command, Group, option, argument, pass_context, 
    echo, style, progressbar
)

logger = logging.getLogger(__name__)


class BuildContext:
    """Context for build operations"""
    
    def __init__(self):
        self.workspace_root = Path.cwd()
        self.backend_root = self.workspace_root / "backend"
        self.frontend_root = self.workspace_root / "frontend"
        self.docker_enabled = self._check_docker()
        self.kubectl_enabled = self._check_kubectl()
        self.build_start_time = None
        self.build_duration = 0.0

    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            subprocess.run(["docker", "--version"], capture_output=True, timeout=5)
            return True
        except Exception:
            return False

    def _check_kubectl(self) -> bool:
        """Check if kubectl is available"""
        try:
            subprocess.run(["kubectl", "version", "--client"], capture_output=True, timeout=5)
            return True
        except Exception:
            return False


@click.group()
@click.version_option("1.0.0")
@pass_context
def cli(ctx):
    """
    OmniDev Build and Deploy CLI
    
    Comprehensive tool for building, testing, and deploying applications
    """
    ctx.ensure_object(dict)
    ctx.obj['build_context'] = BuildContext()


@cli.command()
@option('--component', type=click.Choice(['all', 'backend', 'frontend']), 
        default='all', help='Component to build')
@option('--config', type=click.Choice(['debug', 'release']), 
        default='release', help='Build configuration')
@option('--docker', is_flag=True, help='Build Docker images')
@option('--push', is_flag=True, help='Push Docker images to registry')
@option('--registry', default='registry.example.com', help='Docker registry URL')
@option('--verbose', is_flag=True, help='Verbose output')
@pass_context
def build(ctx, component, config, docker, push, registry, verbose):
    """Build the application"""
    context = ctx.obj['build_context']
    context.build_start_time = time.time()
    
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    echo(style("🔨 Starting build process...", fg='blue', bold=True))
    
    try:
        # Backend build
        if component in ['all', 'backend']:
            echo(style("\n📦 Building backend...", fg='cyan'))
            if not _build_backend(context, config, verbose):
                echo(style("❌ Backend build failed", fg='red', bold=True))
                sys.exit(1)
            echo(style("✅ Backend build successful", fg='green'))
        
        # Frontend build
        if component in ['all', 'frontend']:
            echo(style("\n📦 Building frontend...", fg='cyan'))
            if not _build_frontend(context, config, verbose):
                echo(style("❌ Frontend build failed", fg='red', bold=True))
                sys.exit(1)
            echo(style("✅ Frontend build successful", fg='green'))
        
        # Docker build
        if docker:
            echo(style("\n🐳 Building Docker images...", fg='cyan'))
            if not _build_docker_images(context, component, registry, verbose):
                echo(style("❌ Docker build failed", fg='red', bold=True))
                sys.exit(1)
            
            if push:
                echo(style("\n📤 Pushing Docker images...", fg='cyan'))
                if not _push_docker_images(context, component, registry, verbose):
                    echo(style("❌ Docker push failed", fg='red', bold=True))
                    sys.exit(1)
        
        context.build_duration = time.time() - context.build_start_time
        echo(style(f"\n✅ Build completed in {context.build_duration:.1f}s", fg='green', bold=True))
    
    except Exception as e:
        echo(style(f"\n❌ Build error: {e}", fg='red', bold=True))
        sys.exit(1)


@cli.command()
@option('--test-type', type=click.Choice(['unit', 'integration', 'e2e', 'all']),
        default='all', help='Type of tests to run')
@option('--component', type=click.Choice(['all', 'backend', 'frontend']),
        default='all', help='Component to test')
@option('--coverage', is_flag=True, help='Generate coverage report')
@option('--failfast', is_flag=True, help='Stop on first failure')
@option('--verbose', is_flag=True, help='Verbose output')
@pass_context
def test(ctx, test_type, component, coverage, failfast, verbose):
    """Run tests"""
    context = ctx.obj['build_context']
    
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    echo(style("🧪 Starting test suite...", fg='blue', bold=True))
    
    try:
        test_options = []
        if coverage:
            test_options.append('--cov')
        if failfast:
            test_options.append('-x')
        if verbose:
            test_options.append('-vv')
        
        # Backend tests
        if component in ['all', 'backend']:
            echo(style("\n📋 Running backend tests...", fg='cyan'))
            if not _run_backend_tests(context, test_type, test_options, verbose):
                echo(style("❌ Backend tests failed", fg='red', bold=True))
                sys.exit(1)
            echo(style("✅ Backend tests passed", fg='green'))
        
        # Frontend tests
        if component in ['all', 'frontend']:
            echo(style("\n📋 Running frontend tests...", fg='cyan'))
            if not _run_frontend_tests(context, test_type, verbose):
                echo(style("❌ Frontend tests failed", fg='red', bold=True))
                sys.exit(1)
            echo(style("✅ Frontend tests passed", fg='green'))
        
        echo(style("\n✅ All tests passed", fg='green', bold=True))
    
    except Exception as e:
        echo(style(f"\n❌ Test error: {e}", fg='red', bold=True))
        sys.exit(1)


@cli.command()
@option('--environment', type=click.Choice(['staging', 'production']),
        default='staging', help='Deployment environment')
@option('--strategy', type=click.Choice(['blue-green', 'canary', 'rolling']),
        default='blue-green', help='Deployment strategy')
@option('--replicas', type=int, default=3, help='Number of replicas')
@option('--version', required=True, help='Version to deploy')
@option('--wait', is_flag=True, help='Wait for deployment to complete')
@option('--rollback-on-failure', is_flag=True, default=True, help='Rollback on failure')
@pass_context
def deploy(ctx, environment, strategy, replicas, version, wait, rollback_on_failure):
    """Deploy application"""
    context = ctx.obj['build_context']
    
    if not context.kubectl_enabled:
        echo(style("❌ kubectl not found in PATH", fg='red', bold=True))
        sys.exit(1)
    
    echo(style(f"🚀 Deploying to {environment}...", fg='blue', bold=True))
    
    try:
        # Validate version
        echo(style("\n📋 Validating version...", fg='cyan'))
        if not _validate_version(context, version):
            echo(style(f"❌ Version {version} not found", fg='red', bold=True))
            sys.exit(1)
        
        # Create deployment config
        echo(style("\n⚙️ Creating deployment config...", fg='cyan'))
        deployment_config = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': 'omnidev',
                'namespace': environment
            },
            'spec': {
                'replicas': replicas,
                'strategy': {
                    'type': strategy.upper().replace('-', '')
                },
                'selector': {
                    'matchLabels': {'app': 'omnidev'}
                },
                'template': {
                    'metadata': {
                        'labels': {'app': 'omnidev', 'version': version}
                    },
                    'spec': {
                        'containers': [
                            {
                                'name': 'backend',
                                'image': f'registry.example.com/omnidev-backend:{version}',
                                'ports': [{'containerPort': 5000}],
                                'livenessProbe': {
                                    'httpGet': {'path': '/api/v1/health', 'port': 5000},
                                    'initialDelaySeconds': 30,
                                    'periodSeconds': 10
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        # Apply deployment
        echo(style("\n📤 Applying deployment...", fg='cyan'))
        config_file = Path(f"/tmp/deployment-{datetime.now().isoformat()}.json")
        config_file.write_text(json.dumps(deployment_config, indent=2))
        
        cmd = ['kubectl', 'apply', '-f', str(config_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            echo(style(f"❌ Deployment failed: {result.stderr}", fg='red', bold=True))
            sys.exit(1)
        
        # Wait for deployment
        if wait:
            echo(style("\n⏳ Waiting for deployment to complete...", fg='cyan'))
            cmd = ['kubectl', 'rollout', 'status', 'deployment/omnidev', 
                   '-n', environment, '--timeout=600s']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                echo(style(f"❌ Deployment timeout or failed", fg='red', bold=True))
                if rollback_on_failure:
                    echo(style("\n🔄 Rolling back...", fg='yellow'))
                    _rollback_deployment(context, environment)
                sys.exit(1)
        
        # Smoke tests
        echo(style("\n🧪 Running smoke tests...", fg='cyan'))
        if not _run_smoke_tests(context, environment):
            echo(style(f"❌ Smoke tests failed", fg='red', bold=True))
            if rollback_on_failure:
                echo(style("\n🔄 Rolling back...", fg='yellow'))
                _rollback_deployment(context, environment)
            sys.exit(1)
        
        echo(style(f"\n✅ Deployment to {environment} successful", fg='green', bold=True))
        _print_deployment_info(environment, version)
    
    except Exception as e:
        echo(style(f"\n❌ Deployment error: {e}", fg='red', bold=True))
        sys.exit(1)


@cli.command()
@option('--environment', type=click.Choice(['staging', 'production']),
        default='staging', help='Environment to rollback')
@option('--revision', type=int, help='Specific revision to rollback to')
@pass_context
def rollback(ctx, environment, revision):
    """Rollback deployment"""
    context = ctx.obj['build_context']
    
    if not context.kubectl_enabled:
        echo(style("❌ kubectl not found in PATH", fg='red', bold=True))
        sys.exit(1)
    
    echo(style(f"🔄 Rolling back {environment}...", fg='blue', bold=True))
    
    try:
        _rollback_deployment(context, environment, revision)
        echo(style(f"\n✅ Rollback completed", fg='green', bold=True))
    
    except Exception as e:
        echo(style(f"\n❌ Rollback error: {e}", fg='red', bold=True))
        sys.exit(1)


@cli.command()
@option('--environment', type=click.Choice(['staging', 'production']),
        default='staging', help='Environment to check')
@pass_context
def status(ctx, environment):
    """Check deployment status"""
    context = ctx.obj['build_context']
    
    if not context.kubectl_enabled:
        echo(style("❌ kubectl not found in PATH", fg='red', bold=True))
        sys.exit(1)
    
    echo(style(f"📊 Status for {environment}", fg='blue', bold=True))
    
    try:
        # Get deployment status
        cmd = ['kubectl', 'get', 'deployment', 'omnidev', '-n', environment, '-o', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            deployment = json.loads(result.stdout)
            spec = deployment['spec']
            status = deployment['status']
            
            echo(f"\n  Desired Replicas: {spec['replicas']}")
            echo(f"  Ready Replicas: {status.get('readyReplicas', 0)}")
            echo(f"  Updated Replicas: {status.get('updatedReplicas', 0)}")
            echo(f"  Image: {spec['template']['spec']['containers'][0]['image']}")
            
            # Get pods
            cmd = ['kubectl', 'get', 'pods', '-n', environment, '-l', 'app=omnidev', '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                pods = json.loads(result.stdout)
                echo(f"\n  Pods ({len(pods['items'])} total):")
                for pod in pods['items']:
                    pod_status = pod['status']['phase']
                    color = 'green' if pod_status == 'Running' else 'yellow'
                    echo(f"    - {pod['metadata']['name']}: {style(pod_status, fg=color)}")
    
    except Exception as e:
        echo(style(f"❌ Status check error: {e}", fg='red', bold=True))
        sys.exit(1)


@cli.command()
@option('--output', type=click.Path(), default='build-report.json',
        help='Output file for report')
@pass_context
def report(ctx, output):
    """Generate build report"""
    context = ctx.obj['build_context']
    
    echo(style("📄 Generating build report...", fg='blue', bold=True))
    
    try:
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'build_duration_seconds': context.build_duration,
            'docker_available': context.docker_enabled,
            'kubectl_available': context.kubectl_enabled,
            'workspace_root': str(context.workspace_root),
            'backend_available': context.backend_root.exists(),
            'frontend_available': context.frontend_root.exists()
        }
        
        Path(output).write_text(json.dumps(report_data, indent=2))
        echo(style(f"✅ Report saved to {output}", fg='green'))
    
    except Exception as e:
        echo(style(f"❌ Report generation error: {e}", fg='red', bold=True))
        sys.exit(1)


# Helper functions

def _build_backend(context: BuildContext, config: str, verbose: bool) -> bool:
    """Build backend"""
    try:
        cmd = ['python', '-m', 'pip', 'install', '-e', '.']
        if not verbose:
            cmd.append('-q')
        
        result = subprocess.run(cmd, cwd=context.backend_root, capture_output=not verbose)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Backend build error: {e}")
        return False


def _build_frontend(context: BuildContext, config: str, verbose: bool) -> bool:
    """Build frontend"""
    try:
        # Install dependencies
        cmd = ['npm', 'install']
        result = subprocess.run(cmd, cwd=context.frontend_root, capture_output=not verbose)
        if result.returncode != 0:
            return False
        
        # Build
        cmd = ['npm', 'run', 'build']
        result = subprocess.run(cmd, cwd=context.frontend_root, capture_output=not verbose)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Frontend build error: {e}")
        return False


def _build_docker_images(context: BuildContext, component: str, registry: str, verbose: bool) -> bool:
    """Build Docker images"""
    try:
        if component in ['all', 'backend']:
            cmd = ['docker', 'build', '-t', f'{registry}/omnidev-backend:latest', '-f', 'docker/Dockerfile', '.']
            result = subprocess.run(cmd, cwd=context.backend_root, capture_output=not verbose)
            if result.returncode != 0:
                return False
        
        return True
    except Exception as e:
        logger.error(f"Docker build error: {e}")
        return False


def _push_docker_images(context: BuildContext, component: str, registry: str, verbose: bool) -> bool:
    """Push Docker images"""
    try:
        if component in ['all', 'backend']:
            cmd = ['docker', 'push', f'{registry}/omnidev-backend:latest']
            result = subprocess.run(cmd, capture_output=not verbose)
            if result.returncode != 0:
                return False
        
        return True
    except Exception as e:
        logger.error(f"Docker push error: {e}")
        return False


def _run_backend_tests(context: BuildContext, test_type: str, options: List[str], verbose: bool) -> bool:
    """Run backend tests"""
    try:
        cmd = ['pytest'] + options
        if test_type != 'all':
            cmd.append(f'-m {test_type}')
        
        result = subprocess.run(cmd, cwd=context.backend_root, capture_output=not verbose)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Backend test error: {e}")
        return False


def _run_frontend_tests(context: BuildContext, test_type: str, verbose: bool) -> bool:
    """Run frontend tests"""
    try:
        cmd = ['npm', 'test', '--', '--watchAll=false']
        result = subprocess.run(cmd, cwd=context.frontend_root, capture_output=not verbose)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Frontend test error: {e}")
        return False


def _run_smoke_tests(context: BuildContext, environment: str) -> bool:
    """Run smoke tests"""
    try:
        import requests
        
        # Wait for service to be available
        max_retries = 30
        for attempt in range(max_retries):
            try:
                response = requests.get(f'http://localhost:5000/api/v1/health', timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return False
    except Exception as e:
        logger.error(f"Smoke test error: {e}")
        return False


def _validate_version(context: BuildContext, version: str) -> bool:
    """Validate version exists"""
    try:
        cmd = ['docker', 'inspect', f'registry.example.com/omnidev-backend:{version}']
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False


def _rollback_deployment(context: BuildContext, environment: str, revision: Optional[int] = None) -> bool:
    """Rollback deployment"""
    try:
        cmd = ['kubectl', 'rollout', 'undo', 'deployment/omnidev', '-n', environment]
        if revision:
            cmd.append(f'--to-revision={revision}')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Rollback error: {e}")
        return False


def _print_deployment_info(environment: str, version: str) -> None:
    """Print deployment information"""
    echo(style(f"\n  Environment: {environment}", fg='cyan'))
    echo(style(f"  Version: {version}", fg='cyan'))
    echo(style(f"  Dashboard: https://dashboard.example.com/{environment}", fg='cyan'))


if __name__ == '__main__':
    cli(obj={})

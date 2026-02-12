#!/usr/bin/env python3
"""
GitHub CLI Automation Setup & Integration Guide
Comprehensive instructions for enabling GitHub automation for the omnidev-ai project.
"""

SETUP_GUIDE = """
╔════════════════════════════════════════════════════════════════════════════╗
║               GitHub CLI Automation Setup Guide                            ║
║                      omnidev-ai Project                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

1. SETUP GITHUB PERSONAL ACCESS TOKEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Create Personal Access Token
  1. Go to: https://github.com/settings/tokens
  2. Click "Generate new token" → "Generate new token (classic)"
  3. Name: "omnidev-ai-automation"
  4. Expiration: "90 days"
  5. Select scopes:
     ✓ repo (Full control of private repositories)
     ✓ admin:org_hook (Full control of organization hooks)
     ✓ workflow (Update GitHub Action workflows)
     ✓ gist (Create gists)
  6. Click "Generate token"
  7. Copy the token immediately (you won't see it again)

Step 2: Set Environment Variable (Windows PowerShell)
  [Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "ghp_xxxxx...", "User")
  # Or temporarily:
  $env:GITHUB_TOKEN = "ghp_xxxxx..."

Step 3: Verify Token
  python github_automation_toolkit.py auth
  # Should output: ✓ Authenticated as: <your-username>


2. GITHUB AUTOMATION TOOLKIT USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

List Your Repositories:
  python github_automation_toolkit.py repos

List Repository Issues:
  python github_automation_toolkit.py issues <owner> <repo> [open|closed|all]
  Example: python github_automation_toolkit.py issues microsoft vscode open

List Pull Requests:
  python github_automation_toolkit.py prs <owner> <repo> [open|closed|merged|all]
  Example: python github_automation_toolkit.py prs python cpython merged

Monitor Workflows:
  python github_automation_toolkit.py workflows <owner> <repo>
  Example: python github_automation_toolkit.py workflows torvalds linux

View Statistics:
  python github_automation_toolkit.py stats


3. GITHUB ACTIONS WORKFLOWS FOR OMNIDEV-AI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Create .github/workflows/ directory structure:

.github/
├── workflows/
│   ├── test.yml           # Run tests on push/PR
│   ├── lint.yml           # Code quality checks
│   ├── build.yml          # Build Docker images
│   ├── security.yml       # Security scanning
│   └── release.yml        # Automated releases


4. EXAMPLE WORKFLOW: Automated Testing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: .github/workflows/test.yml
─────────────────────────────────────────

name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest backend/ -v --cov=backend
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true


5. EXAMPLE WORKFLOW: Linting & Code Quality
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: .github/workflows/lint.yml
────────────────────────────────

name: Lint

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install flake8 black isort pylint mypy
    
    - name: Run Flake8
      run: flake8 backend/ --count --select=E9,F63,F7,F82 --show-source
    
    - name: Check formatting with Black
      run: black backend/ --check
    
    - name: Check import sorting with isort
      run: isort backend/ --check-only
    
    - name: Run Pylint
      run: pylint backend/ --fail-under=8.0 || true
    
    - name: Type check with mypy
      run: mypy backend/ || true


6. EXAMPLE WORKFLOW: Docker Build & Push
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: .github/workflows/build.yml
─────────────────────────────────

name: Build

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./docker/Dockerfile
        push: true
        tags: |
          ${{ secrets.DOCKER_USERNAME }}/omnidev-ai:latest
          ${{ secrets.DOCKER_USERNAME }}/omnidev-ai:${{ github.sha }}


7. SETTING REPOSITORY SECRETS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For workflows that need credentials:

1. Go to: Repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add secrets:
   
   DOCKER_USERNAME     → Your Docker Hub username
   DOCKER_PASSWORD     → Docker Hub access token
   REGISTRY_URL        → Container registry URL
   AWS_ACCESS_KEY_ID   → AWS credentials (if using AWS)
   AWS_SECRET_ACCESS_KEY → AWS credentials
   CODECOV_TOKEN       → Codecov integration token
   SONAR_TOKEN         → SonarQube token (if using)


8. AUTOMATED PYTHON TESTING WITH GITHUB ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Python test runner script for omnidev-ai:

File: scripts/run_phase_tests.py
─────────────────────────────────

#!/usr/bin/env python3
import subprocess
import sys
import json
from pathlib import Path

def run_phase_tests():
    '''Run all phase test files and report results.'''
    
    test_files = [
        'backend/security_tests_phase56.py',
        # Add other phase test files here
    ]
    
    results = {'passed': 0, 'failed': 0, 'errors': []}
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\\n{'='*60}")
            print(f"Running: {test_file}")
            print(f"{'='*60}")
            
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                results['passed'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(test_file)
    
    # Report summary
    print(f"\\n{'='*60}")
    print(f"Test Summary: {results['passed']} passed, {results['failed']} failed")
    print(f"{'='*60}")
    
    if results['failed'] > 0:
        print("\\nFailed tests:")
        for error in results['errors']:
            print(f"  - {error}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(run_phase_tests())


9. CONTINUOUS INTEGRATION BENEFITS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Automated testing on every push/PR
✓ Code quality checks (lint, format, type checking)
✓ Docker image builds and pushes
✓ Security scanning (SAST, dependency checks)
✓ Automated releases and changelogs
✓ Coverage reports and tracking
✓ Performance benchmarking
✓ Deployment automation


10. AUTOMATION TOOLKIT FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The github_automation_toolkit.py provides:

✓ User Authentication
✓ Repository Management
  - List repositories
  - Get repository details
  - Create repositories
  
✓ Issue Management
  - List issues
  - Create issues
  - Update issues
  
✓ Pull Request Management
  - List PRs
  - Create PRs
  - Review PRs
  
✓ Workflow Management
  - List workflow runs
  - Trigger workflows
  - Monitor CI/CD
  
✓ Release Management
  - List releases
  - Create releases
  - Generate changelogs
  
✓ Statistics & Monitoring
  - Cache statistics
  - API usage tracking
  - Performance metrics


11. TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problem: "Authentication failed" or "token not found"
Solution:
  1. Verify token is set: echo $env:GITHUB_TOKEN (PowerShell)
  2. Token may have expired (check GitHub settings)
  3. Create new token and update environment variable

Problem: "API rate limit exceeded"
Solution:
  1. GitHub limits unauthenticated requests to 60/hour
  2. Use GITHUB_TOKEN to get 5,000/hour limit
  3. For higher limits, use GitHub App or OAuth

Problem: "No workflows found" or "Workflows not triggering"
Solution:
  1. Ensure .github/workflows/*.yml files are in default branch
  2. YAML syntax must be valid (use online YAML validator)
  3. Permissions may be restricted (check workflow permissions)

Problem: "Docker push fails"
Solution:
  1. Verify Docker credentials in repository secrets
  2. Ensure registry is accessible
  3. Check Docker username/password are correct


12. INTEGRATION WITH OMNIDEV-AI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommended automation for omnidev-ai:

1. On every push to main/develop:
   ✓ Run Phase test suites (Phase 56, etc.)
   ✓ Run security checks
   ✓ Generate coverage reports
   ✓ Lint and format check

2. On pull request:
   ✓ Run tests to verify changes
   ✓ Code review automation
   ✓ Dependency checking

3. On release tags (v*):
   ✓ Build Docker images
   ✓ Push to registry
   ✓ Create GitHub releases
   ✓ Generate changelogs

4. Scheduled workflows:
   ✓ Daily dependency updates
   ✓ Weekly security scans
   ✓ Performance benchmarks


13. NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ✓ Create .github/workflows/ directory
2. ✓ Add workflow YAML files (test.yml, lint.yml, build.yml)
3. ✓ Set repository secrets (Docker credentials, API tokens)
4. ✓ Push workflows to repository
5. ✓ Monitor workflow runs in GitHub UI
6. ✓ Use GitHub Automation Toolkit for automation scripts
7. ✓ Integrate with monitoring/logging systems

═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(SETUP_GUIDE)

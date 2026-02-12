"""
Security Scanner Service
Automated security scanning, vulnerability detection, and compliance checking
Phase 41: CI/CD Pipeline & Automated Deployment
"""

import logging
import subprocess
import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Callable, Set
from datetime import datetime
from threading import RLock
from pathlib import Path

logger = logging.getLogger(__name__)


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScanType(Enum):
    """Types of security scans"""
    SAST = "sast"  # Static Application Security Testing
    DAST = "dast"  # Dynamic Application Security Testing
    DEPENDENCY = "dependency"
    CONTAINER = "container"
    CONFIG = "config"
    SECRET = "secret"
    CODE_QUALITY = "code_quality"


class ComplianceFramework(Enum):
    """Compliance frameworks"""
    OWASP_TOP_10 = "owasp_top_10"
    CIS_BENCHMARKS = "cis_benchmarks"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    GDPR = "gdpr"


class ScanStatus(Enum):
    """Scan execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Vulnerability:
    """Represents a detected vulnerability"""
    id: str
    title: str
    description: str
    severity: VulnerabilitySeverity
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    cve_id: Optional[str] = None
    remediation: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.utcnow)
    scanner: str = "unknown"
    tags: List[str] = field(default_factory=list)


@dataclass
class ScanResult:
    """Results of a security scan"""
    scan_id: str
    scan_type: ScanType
    status: ScanStatus
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    scanned_files: int = 0
    scanned_dependencies: int = 0
    error_message: Optional[str] = None
    
    def get_statistics(self) -> Dict[str, int]:
        """Get vulnerability statistics"""
        stats = {
            'total': len(self.vulnerabilities),
            'critical': sum(1 for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL),
            'high': sum(1 for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.HIGH),
            'medium': sum(1 for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.MEDIUM),
            'low': sum(1 for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.LOW),
            'info': sum(1 for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.INFO),
            'scanned_files': self.scanned_files,
            'scanned_dependencies': self.scanned_dependencies
        }
        return stats


@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    name: str
    max_critical: int = 0
    max_high: int = 5
    max_medium: int = 20
    max_low: int = 100
    frameworks: List[ComplianceFramework] = field(default_factory=list)
    auto_remediate: bool = False
    fail_on_violation: bool = True


class SecurityScanner:
    """Orchestrates security scanning operations"""

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.scans: List[ScanResult] = []
        self.vulnerabilities: Dict[str, Vulnerability] = {}
        self.policies: Dict[str, SecurityPolicy] = {}
        self.callbacks: List[Callable] = []
        self.lock = RLock()

    def register_policy(self, policy: SecurityPolicy) -> None:
        """Register a security policy"""
        with self.lock:
            self.policies[policy.name] = policy
        logger.info(f"Policy registered: {policy.name}")

    def scan_code(self) -> ScanResult:
        """Perform SAST code scanning"""
        import uuid
        scan_id = f"scan_{uuid.uuid4().hex[:12]}"
        
        result = ScanResult(
            scan_id=scan_id,
            scan_type=ScanType.SAST,
            status=ScanStatus.IN_PROGRESS
        )
        
        try:
            logger.info(f"Starting SAST scan {scan_id}")
            
            # Run bandit for Python security issues
            vulnerabilities = self._run_bandit()
            result.vulnerabilities.extend(vulnerabilities)
            
            # Run pylint for code quality issues
            vulnerabilities = self._run_pylint()
            result.vulnerabilities.extend(vulnerabilities)
            
            # Count files
            result.scanned_files = len(list(self.workspace_root.rglob("*.py")))
            
            result.status = ScanStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            
            with self.lock:
                self.scans.append(result)
                for vuln in result.vulnerabilities:
                    self.vulnerabilities[vuln.id] = vuln
            
            logger.info(f"SAST scan completed: {result.get_statistics()}")
            self._trigger_callbacks(result)
            
            return result
        
        except Exception as e:
            logger.error(f"SAST scan error: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)
            return result

    def scan_dependencies(self) -> ScanResult:
        """Scan dependencies for vulnerabilities"""
        import uuid
        scan_id = f"scan_{uuid.uuid4().hex[:12]}"
        
        result = ScanResult(
            scan_id=scan_id,
            scan_type=ScanType.DEPENDENCY,
            status=ScanStatus.IN_PROGRESS
        )
        
        try:
            logger.info(f"Starting dependency scan {scan_id}")
            
            # Run pip-audit for Python dependencies
            vulnerabilities = self._run_pip_audit()
            result.vulnerabilities.extend(vulnerabilities)
            result.scanned_dependencies = len(self._get_installed_packages())
            
            # Run npm audit for Node dependencies
            vulnerabilities = self._run_npm_audit()
            result.vulnerabilities.extend(vulnerabilities)
            
            result.status = ScanStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            
            with self.lock:
                self.scans.append(result)
                for vuln in result.vulnerabilities:
                    self.vulnerabilities[vuln.id] = vuln
            
            logger.info(f"Dependency scan completed: {result.get_statistics()}")
            self._trigger_callbacks(result)
            
            return result
        
        except Exception as e:
            logger.error(f"Dependency scan error: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)
            return result

    def scan_container(self, image: str) -> ScanResult:
        """Scan Docker container image"""
        import uuid
        scan_id = f"scan_{uuid.uuid4().hex[:12]}"
        
        result = ScanResult(
            scan_id=scan_id,
            scan_type=ScanType.CONTAINER,
            status=ScanStatus.IN_PROGRESS
        )
        
        try:
            logger.info(f"Starting container scan {scan_id} for {image}")
            
            # Run Trivy for container scanning
            vulnerabilities = self._run_trivy(image)
            result.vulnerabilities.extend(vulnerabilities)
            
            result.status = ScanStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            
            with self.lock:
                self.scans.append(result)
                for vuln in result.vulnerabilities:
                    self.vulnerabilities[vuln.id] = vuln
            
            logger.info(f"Container scan completed: {result.get_statistics()}")
            self._trigger_callbacks(result)
            
            return result
        
        except Exception as e:
            logger.error(f"Container scan error: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)
            return result

    def scan_secrets(self) -> ScanResult:
        """Scan for exposed secrets"""
        import uuid
        scan_id = f"scan_{uuid.uuid4().hex[:12]}"
        
        result = ScanResult(
            scan_id=scan_id,
            scan_type=ScanType.SECRET,
            status=ScanStatus.IN_PROGRESS
        )
        
        try:
            logger.info(f"Starting secret scan {scan_id}")
            
            # Run git-secrets or similar tool
            vulnerabilities = self._scan_for_secrets()
            result.vulnerabilities.extend(vulnerabilities)
            
            result.status = ScanStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            
            with self.lock:
                self.scans.append(result)
                for vuln in result.vulnerabilities:
                    self.vulnerabilities[vuln.id] = vuln
            
            logger.info(f"Secret scan completed: {result.get_statistics()}")
            self._trigger_callbacks(result)
            
            return result
        
        except Exception as e:
            logger.error(f"Secret scan error: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)
            return result

    def run_full_scan(self) -> List[ScanResult]:
        """Run all security scans"""
        logger.info("Starting full security scan suite")
        
        results = [
            self.scan_code(),
            self.scan_dependencies(),
            self.scan_secrets()
        ]
        
        return results

    def check_policy_compliance(self, policy_name: str) -> Dict[str, any]:
        """Check compliance against a policy"""
        with self.lock:
            policy = self.policies.get(policy_name)
            if not policy:
                logger.error(f"Policy {policy_name} not found")
                return {'compliant': False, 'violations': []}
        
        # Get latest scans
        stats = {}
        for scan in self.scans:
            scan_stats = scan.get_statistics()
            stats.update(scan_stats)
        
        violations = []
        
        if stats.get('critical', 0) > policy.max_critical:
            violations.append(f"Critical vulnerabilities: {stats['critical']} > {policy.max_critical}")
        
        if stats.get('high', 0) > policy.max_high:
            violations.append(f"High vulnerabilities: {stats['high']} > {policy.max_high}")
        
        if stats.get('medium', 0) > policy.max_medium:
            violations.append(f"Medium vulnerabilities: {stats['medium']} > {policy.max_medium}")
        
        if stats.get('low', 0) > policy.max_low:
            violations.append(f"Low vulnerabilities: {stats['low']} > {policy.max_low}")
        
        return {
            'policy': policy_name,
            'compliant': len(violations) == 0,
            'violations': violations,
            'statistics': stats
        }

    def generate_report(self, format: str = 'json') -> str:
        """Generate security report"""
        report_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'scans': []
        }
        
        for scan in self.scans[-10:]:  # Last 10 scans
            scan_summary = {
                'scan_id': scan.scan_id,
                'type': scan.scan_type.value,
                'status': scan.status.value,
                'statistics': scan.get_statistics(),
                'vulnerabilities': [
                    {
                        'id': v.id,
                        'title': v.title,
                        'severity': v.severity.value,
                        'cve_id': v.cve_id,
                        'remediation': v.remediation
                    }
                    for v in scan.vulnerabilities[:5]  # Top 5 vulnerabilities
                ]
            }
            report_data['scans'].append(scan_summary)
        
        if format == 'json':
            return json.dumps(report_data, indent=2)
        else:
            return str(report_data)

    # Private helper methods

    def _run_bandit(self) -> List[Vulnerability]:
        """Run bandit security scanner"""
        vulnerabilities = []
        
        try:
            cmd = ["bandit", "-r", str(self.workspace_root), "-f", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 or result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for issue in data.get('results', []):
                        vuln = Vulnerability(
                            id=f"bandit_{issue['test_id']}",
                            title=issue['test'],
                            description=issue['issue_text'],
                            severity=self._map_severity(issue.get('severity', 'MEDIUM')),
                            file_path=issue.get('filename'),
                            line_number=issue.get('line_number'),
                            scanner='bandit',
                            tags=['sast']
                        )
                        vulnerabilities.append(vuln)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse bandit output")
        
        except Exception as e:
            logger.error(f"Bandit scan error: {e}")
        
        return vulnerabilities

    def _run_pylint(self) -> List[Vulnerability]:
        """Run pylint for code quality issues"""
        vulnerabilities = []
        
        try:
            python_files = self.workspace_root.rglob("*.py")
            for py_file in list(python_files)[:100]:  # Limit to 100 files
                cmd = ["pylint", str(py_file), "--output-format=json"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.stdout:
                    try:
                        issues = json.loads(result.stdout)
                        for issue in issues:
                            if issue['symbol'] in ['security-issue', 'dangerous-default']:
                                vuln = Vulnerability(
                                    id=f"pylint_{issue['symbol']}",
                                    title=issue['symbol'],
                                    description=issue['message'],
                                    severity=VulnerabilitySeverity.MEDIUM,
                                    file_path=issue.get('path'),
                                    line_number=issue.get('line'),
                                    scanner='pylint',
                                    tags=['code_quality']
                                )
                                vulnerabilities.append(vuln)
                    except json.JSONDecodeError:
                        pass
        
        except Exception as e:
            logger.error(f"Pylint error: {e}")
        
        return vulnerabilities

    def _run_pip_audit(self) -> List[Vulnerability]:
        """Run pip-audit for dependency vulnerabilities"""
        vulnerabilities = []
        
        try:
            cmd = ["pip-audit", "--desc", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for vuln_data in data.get('vulnerabilities', []):
                        vuln = Vulnerability(
                            id=f"pip_{vuln_data['id']}",
                            title=vuln_data.get('description', 'Security Issue'),
                            description=vuln_data.get('advisory', ''),
                            severity=self._severity_from_string(vuln_data.get('vulnerability', 'MEDIUM')),
                            cve_id=vuln_data.get('cve'),
                            scanner='pip-audit',
                            tags=['dependency']
                        )
                        vulnerabilities.append(vuln)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse pip-audit output")
        
        except Exception as e:
            logger.error(f"pip-audit error: {e}")
        
        return vulnerabilities

    def _run_npm_audit(self) -> List[Vulnerability]:
        """Run npm audit for Node dependencies"""
        vulnerabilities = []
        
        try:
            frontend_path = self.workspace_root / "frontend"
            if frontend_path.exists():
                cmd = ["npm", "audit", "--json"]
                result = subprocess.run(cmd, cwd=str(frontend_path), capture_output=True, text=True, timeout=60)
                
                if result.stdout:
                    try:
                        data = json.loads(result.stdout)
                        for package, info in data.get('vulnerabilities', {}).items():
                            for vuln_data in info.get('via', []):
                                if isinstance(vuln_data, dict):
                                    vuln = Vulnerability(
                                        id=f"npm_{package}_{vuln_data.get('cves', [None])[0]}",
                                        title=vuln_data.get('title', package),
                                        description=vuln_data.get('description', ''),
                                        severity=self._severity_from_string(vuln_data.get('severity', 'MEDIUM')),
                                        cve_id=vuln_data.get('cves', [None])[0],
                                        scanner='npm-audit',
                                        tags=['dependency']
                                    )
                                    vulnerabilities.append(vuln)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse npm audit output")
        
        except Exception as e:
            logger.error(f"npm audit error: {e}")
        
        return vulnerabilities

    def _run_trivy(self, image: str) -> List[Vulnerability]:
        """Run Trivy container scanner"""
        vulnerabilities = []
        
        try:
            cmd = ["trivy", "image", "--format", "json", image]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for result_item in data.get('Results', []):
                        for vuln in result_item.get('Vulnerabilities', []):
                            severity = self._severity_from_string(vuln.get('Severity', 'UNKNOWN'))
                            vulnerability = Vulnerability(
                                id=f"trivy_{vuln.get('VulnerabilityID', 'unknown')}",
                                title=vuln.get('Title', 'Container Vulnerability'),
                                description=vuln.get('Description', ''),
                                severity=severity,
                                cve_id=vuln.get('VulnerabilityID'),
                                remediation=vuln.get('FixedVersion'),
                                scanner='trivy',
                                tags=['container']
                            )
                            vulnerabilities.append(vulnerability)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Trivy output")
        
        except Exception as e:
            logger.error(f"Trivy error: {e}")
        
        return vulnerabilities

    def _scan_for_secrets(self) -> List[Vulnerability]:
        """Scan for exposed secrets in code"""
        vulnerabilities = []
        secret_patterns = {
            'AWS_KEY': r'AKIA[0-9A-Z]{16}',
            'PRIVATE_KEY': r'-----BEGIN RSA PRIVATE KEY-----',
            'API_KEY': r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\']+)',
            'PASSWORD': r'password["\']?\s*[:=]\s*["\']?([^"\']+)'
        }
        
        try:
            for pattern_name, pattern in secret_patterns.items():
                for py_file in self.workspace_root.rglob("*.py"):
                    try:
                        content = py_file.read_text()
                        if re.search(pattern, content):
                            vuln = Vulnerability(
                                id=f"secret_{pattern_name}_{py_file.name}",
                                title=f"Potential {pattern_name} detected",
                                description=f"File may contain {pattern_name}",
                                severity=VulnerabilitySeverity.CRITICAL,
                                file_path=str(py_file),
                                scanner='secret-scanner',
                                tags=['secret']
                            )
                            vulnerabilities.append(vuln)
                    except Exception:
                        pass
        
        except Exception as e:
            logger.error(f"Secret scan error: {e}")
        
        return vulnerabilities

    def _get_installed_packages(self) -> List[str]:
        """Get list of installed packages"""
        try:
            cmd = ["pip", "list", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.stdout:
                packages = json.loads(result.stdout)
                return [p['name'] for p in packages]
        
        except Exception as e:
            logger.error(f"Error getting installed packages: {e}")
        
        return []

    @staticmethod
    def _map_severity(severity_str: str) -> VulnerabilitySeverity:
        """Map string severity to enum"""
        severity_map = {
            'CRITICAL': VulnerabilitySeverity.CRITICAL,
            'HIGH': VulnerabilitySeverity.HIGH,
            'MEDIUM': VulnerabilitySeverity.MEDIUM,
            'LOW': VulnerabilitySeverity.LOW,
            'INFO': VulnerabilitySeverity.INFO
        }
        return severity_map.get(severity_str.upper(), VulnerabilitySeverity.MEDIUM)

    @staticmethod
    def _severity_from_string(severity_str: str) -> VulnerabilitySeverity:
        """Convert string to severity enum"""
        severity_lower = severity_str.lower()
        if 'critical' in severity_lower:
            return VulnerabilitySeverity.CRITICAL
        elif 'high' in severity_lower:
            return VulnerabilitySeverity.HIGH
        elif 'medium' in severity_lower:
            return VulnerabilitySeverity.MEDIUM
        elif 'low' in severity_lower:
            return VulnerabilitySeverity.LOW
        else:
            return VulnerabilitySeverity.INFO

    def register_callback(self, callback: Callable[[ScanResult], None]) -> None:
        """Register callback for scan completion"""
        with self.lock:
            self.callbacks.append(callback)

    def _trigger_callbacks(self, result: ScanResult) -> None:
        """Trigger callbacks"""
        for callback in self.callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Callback error: {e}")


# Global scanner instance
_scanner: Optional[SecurityScanner] = None


def get_security_scanner(workspace_root: str = ".") -> SecurityScanner:
    """Get or create security scanner instance"""
    global _scanner
    if _scanner is None:
        _scanner = SecurityScanner(workspace_root)
    return _scanner

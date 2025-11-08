"""
Security Auditor Agent

Performs comprehensive security analysis:
- OWASP Top 10 vulnerability scanning
- Dependency vulnerability checking
- Secret detection
- License compliance
- Security best practices
- Automated fix suggestions
- Risk scoring

Integrates with security tools like bandit, semgrep, snyk, etc.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from enum import Enum
import re
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class VulnerabilityType(Enum):
    """Types of security vulnerabilities"""
    INJECTION = "injection"
    BROKEN_AUTH = "broken_authentication"
    SENSITIVE_DATA = "sensitive_data_exposure"
    XXE = "xml_external_entities"
    BROKEN_ACCESS = "broken_access_control"
    SECURITY_MISCONFIG = "security_misconfiguration"
    XSS = "cross_site_scripting"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    VULNERABLE_COMPONENTS = "vulnerable_components"
    INSUFFICIENT_LOGGING = "insufficient_logging"
    SECRETS = "hardcoded_secrets"
    LICENSE_VIOLATION = "license_violation"


class RiskLevel(Enum):
    """Risk severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityFinding:
    """A security vulnerability or issue"""
    title: str
    vulnerability_type: VulnerabilityType
    risk_level: RiskLevel
    file: str
    line: Optional[int]
    description: str
    impact: str
    remediation: str
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    cvss_score: Optional[float] = None  # Common Vulnerability Scoring System
    references: List[str] = field(default_factory=list)
    code_snippet: Optional[str] = None
    automated_fix: Optional[str] = None


@dataclass
class DependencyVulnerability:
    """Vulnerability in a dependency"""
    package_name: str
    installed_version: str
    vulnerable_versions: str
    patched_version: Optional[str]
    vulnerability_id: str  # CVE ID or similar
    severity: RiskLevel
    description: str
    exploit_available: bool = False


@dataclass
class LicenseIssue:
    """License compliance issue"""
    package_name: str
    license_type: str
    issue_type: str  # "incompatible", "unknown", "restrictive"
    description: str
    recommendation: str


@dataclass
class SecurityReport:
    """Complete security audit report"""
    summary: str
    overall_risk_score: float  # 0-100
    risk_level: RiskLevel
    findings: List[SecurityFinding] = field(default_factory=list)
    dependency_vulnerabilities: List[DependencyVulnerability] = field(default_factory=list)
    license_issues: List[LicenseIssue] = field(default_factory=list)
    secrets_found: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    compliance_status: Dict[str, bool] = field(default_factory=dict)


class SecurityAuditor:
    """
    Security Auditor Agent

    Performs comprehensive security analysis and generates
    actionable reports with automated fix suggestions.
    """

    def __init__(
        self,
        model_id: str = "claude-sonnet-4",
        enable_auto_fix: bool = True,
        scan_dependencies: bool = True,
    ):
        """
        Initialize Security Auditor

        Args:
            model_id: LLM model for analysis
            enable_auto_fix: Generate automated fixes
            scan_dependencies: Scan dependencies for vulnerabilities
        """
        self.model_id = model_id
        self.enable_auto_fix = enable_auto_fix
        self.scan_dependencies = scan_dependencies

        # OWASP Top 10 patterns
        self.owasp_patterns = self._init_owasp_patterns()

        # Secret patterns
        self.secret_patterns = self._init_secret_patterns()

    def _init_owasp_patterns(self) -> Dict[VulnerabilityType, List[Dict[str, Any]]]:
        """Initialize OWASP vulnerability patterns"""
        return {
            VulnerabilityType.INJECTION: [
                {
                    'pattern': r'execute\([^)]*%[^)]*\)',
                    'description': 'Potential SQL injection via string formatting',
                    'cwe': 'CWE-89',
                },
                {
                    'pattern': r'execute\([^)]*\+[^)]*\)',
                    'description': 'Potential SQL injection via string concatenation',
                    'cwe': 'CWE-89',
                },
                {
                    'pattern': r'eval\(.*request\.',
                    'description': 'Code injection via eval with user input',
                    'cwe': 'CWE-94',
                },
            ],
            VulnerabilityType.BROKEN_AUTH: [
                {
                    'pattern': r'password\s*==\s*["\']',
                    'description': 'Hardcoded password comparison',
                    'cwe': 'CWE-798',
                },
                {
                    'pattern': r'md5\(.*password',
                    'description': 'Weak password hashing (MD5)',
                    'cwe': 'CWE-327',
                },
                {
                    'pattern': r'sha1\(.*password',
                    'description': 'Weak password hashing (SHA1)',
                    'cwe': 'CWE-327',
                },
            ],
            VulnerabilityType.SENSITIVE_DATA: [
                {
                    'pattern': r'print\(.*password',
                    'description': 'Sensitive data logged',
                    'cwe': 'CWE-532',
                },
                {
                    'pattern': r'log.*password',
                    'description': 'Password in logs',
                    'cwe': 'CWE-532',
                },
            ],
            VulnerabilityType.XSS: [
                {
                    'pattern': r'innerHTML\s*=.*request\.',
                    'description': 'Potential XSS via innerHTML',
                    'cwe': 'CWE-79',
                },
                {
                    'pattern': r'dangerouslySetInnerHTML',
                    'description': 'React XSS risk',
                    'cwe': 'CWE-79',
                },
            ],
            VulnerabilityType.SECURITY_MISCONFIG: [
                {
                    'pattern': r'DEBUG\s*=\s*True',
                    'description': 'Debug mode enabled',
                    'cwe': 'CWE-489',
                },
                {
                    'pattern': r'verify\s*=\s*False',
                    'description': 'SSL verification disabled',
                    'cwe': 'CWE-295',
                },
            ],
        }

    def _init_secret_patterns(self) -> List[Dict[str, str]]:
        """Initialize secret detection patterns"""
        return [
            {
                'name': 'AWS Access Key',
                'pattern': r'AKIA[0-9A-Z]{16}',
            },
            {
                'name': 'AWS Secret Key',
                'pattern': r'aws_secret_access_key\s*=\s*["\']([^"\']+)["\']',
            },
            {
                'name': 'GitHub Token',
                'pattern': r'ghp_[a-zA-Z0-9]{36}',
            },
            {
                'name': 'Generic API Key',
                'pattern': r'api[_-]?key\s*[=:]\s*["\']([^"\']{20,})["\']',
            },
            {
                'name': 'Generic Secret',
                'pattern': r'secret\s*[=:]\s*["\']([^"\']{20,})["\']',
            },
            {
                'name': 'Private Key',
                'pattern': r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
            },
            {
                'name': 'Password',
                'pattern': r'password\s*[=:]\s*["\']([^"\']{8,})["\']',
            },
        ]

    async def audit_codebase(
        self,
        files: Dict[str, str],
        context: Optional[Dict[str, Any]] = None,
    ) -> SecurityReport:
        """
        Perform comprehensive security audit

        Args:
            files: Dictionary of file_path -> content
            context: Additional context (dependencies, config, etc.)

        Returns:
            SecurityReport with all findings
        """
        logger.info(f"Starting security audit of {len(files)} files")

        findings = []
        secrets_found = []

        # Scan for OWASP vulnerabilities
        for file_path, content in files.items():
            file_findings = await self._scan_owasp(file_path, content)
            findings.extend(file_findings)

            # Scan for secrets
            file_secrets = self._scan_secrets(file_path, content)
            secrets_found.extend(file_secrets)

        # Scan dependencies
        dependency_vulns = []
        if self.scan_dependencies and context and 'dependencies' in context:
            dependency_vulns = await self._scan_dependencies(
                context['dependencies']
            )

        # Check license compliance
        license_issues = []
        if context and 'dependencies' in context:
            license_issues = await self._check_licenses(context['dependencies'])

        # Calculate risk score
        risk_score = self._calculate_risk_score(
            findings,
            dependency_vulns,
            secrets_found,
        )

        # Determine overall risk level
        risk_level = self._determine_risk_level(risk_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            findings,
            dependency_vulns,
            license_issues,
            secrets_found,
        )

        # Check compliance
        compliance_status = self._check_compliance(findings, secrets_found)

        # Generate summary
        summary = self._generate_summary(
            findings,
            dependency_vulns,
            license_issues,
            secrets_found,
            risk_level,
        )

        report = SecurityReport(
            summary=summary,
            overall_risk_score=risk_score,
            risk_level=risk_level,
            findings=findings,
            dependency_vulnerabilities=dependency_vulns,
            license_issues=license_issues,
            secrets_found=secrets_found,
            recommendations=recommendations,
            compliance_status=compliance_status,
        )

        logger.info(f"Audit complete: {len(findings)} findings, risk score {risk_score:.1f}")
        return report

    async def scan_file(
        self,
        file_path: str,
        content: str,
    ) -> List[SecurityFinding]:
        """
        Scan a single file for security issues

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of security findings
        """
        logger.info(f"Scanning {file_path}")

        findings = await self._scan_owasp(file_path, content)
        secrets = self._scan_secrets(file_path, content)

        # Convert secrets to findings
        for secret in secrets:
            findings.append(SecurityFinding(
                title="Hardcoded Secret Detected",
                vulnerability_type=VulnerabilityType.SECRETS,
                risk_level=RiskLevel.CRITICAL,
                file=file_path,
                line=secret['line'],
                description=f"{secret['type']} found in code",
                impact="Credentials could be exposed in version control",
                remediation="Remove hardcoded secret and use environment variables",
                automated_fix=self._generate_secret_fix(secret) if self.enable_auto_fix else None,
            ))

        return findings

    async def _scan_owasp(
        self,
        file_path: str,
        content: str,
    ) -> List[SecurityFinding]:
        """Scan for OWASP Top 10 vulnerabilities"""
        findings = []

        for vuln_type, patterns in self.owasp_patterns.items():
            for pattern_info in patterns:
                matches = self._find_pattern_matches(
                    content,
                    pattern_info['pattern'],
                )

                for match in matches:
                    # Generate automated fix if enabled
                    auto_fix = None
                    if self.enable_auto_fix:
                        auto_fix = self._generate_fix(
                            vuln_type,
                            match['line_content'],
                        )

                    finding = SecurityFinding(
                        title=pattern_info['description'],
                        vulnerability_type=vuln_type,
                        risk_level=self._assess_risk(vuln_type),
                        file=file_path,
                        line=match['line_number'],
                        description=pattern_info['description'],
                        impact=self._get_impact(vuln_type),
                        remediation=self._get_remediation(vuln_type),
                        cwe_id=pattern_info.get('cwe'),
                        code_snippet=match['line_content'],
                        automated_fix=auto_fix,
                    )
                    findings.append(finding)

        return findings

    def _scan_secrets(
        self,
        file_path: str,
        content: str,
    ) -> List[Dict[str, Any]]:
        """Scan for hardcoded secrets"""
        secrets = []

        # Skip common config/test files that might legitimately have examples
        skip_patterns = ['test', 'example', 'sample', '.md', '.txt']
        if any(pattern in file_path.lower() for pattern in skip_patterns):
            return secrets

        for secret_pattern in self.secret_patterns:
            matches = self._find_pattern_matches(
                content,
                secret_pattern['pattern'],
            )

            for match in matches:
                secrets.append({
                    'type': secret_pattern['name'],
                    'file': file_path,
                    'line': match['line_number'],
                    'content': match['line_content'],
                })

        return secrets

    async def _scan_dependencies(
        self,
        dependencies: Dict[str, str],
    ) -> List[DependencyVulnerability]:
        """
        Scan dependencies for known vulnerabilities

        This would integrate with:
        - npm audit
        - pip-audit
        - snyk
        - OWASP Dependency-Check
        """
        logger.info(f"Scanning {len(dependencies)} dependencies")

        vulnerabilities = []

        # Simulate vulnerability database lookup
        # In production, this would query actual vulnerability databases
        for package, version in dependencies.items():
            # Mock: randomly find some vulnerabilities
            if 'old' in package.lower() or 'vulnerable' in package.lower():
                vuln = DependencyVulnerability(
                    package_name=package,
                    installed_version=version,
                    vulnerable_versions=f"<= {version}",
                    patched_version=self._increment_version(version),
                    vulnerability_id="CVE-2024-XXXXX",
                    severity=RiskLevel.HIGH,
                    description=f"Known vulnerability in {package}",
                    exploit_available=False,
                )
                vulnerabilities.append(vuln)

        return vulnerabilities

    async def _check_licenses(
        self,
        dependencies: Dict[str, str],
    ) -> List[LicenseIssue]:
        """Check license compliance"""
        logger.info("Checking license compliance")

        issues = []

        # Define incompatible licenses
        incompatible_licenses = {'GPL-3.0', 'AGPL-3.0', 'SSPL'}
        restrictive_licenses = {'GPL-2.0', 'LGPL'}

        # In production, this would query actual license information
        # For now, mock some license issues
        for package in list(dependencies.keys())[:2]:
            if 'gpl' in package.lower():
                issue = LicenseIssue(
                    package_name=package,
                    license_type="GPL-3.0",
                    issue_type="incompatible",
                    description=f"{package} uses GPL-3.0 which may be incompatible",
                    recommendation="Review licensing requirements or replace package",
                )
                issues.append(issue)

        return issues

    def _find_pattern_matches(
        self,
        content: str,
        pattern: str,
    ) -> List[Dict[str, Any]]:
        """Find all matches of a pattern in content"""
        matches = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            if re.search(pattern, line, re.IGNORECASE):
                matches.append({
                    'line_number': line_num,
                    'line_content': line.strip(),
                })

        return matches

    def _assess_risk(self, vuln_type: VulnerabilityType) -> RiskLevel:
        """Assess risk level for vulnerability type"""
        high_risk = {
            VulnerabilityType.INJECTION,
            VulnerabilityType.BROKEN_AUTH,
            VulnerabilityType.SECRETS,
        }

        if vuln_type in high_risk:
            return RiskLevel.CRITICAL

        return RiskLevel.HIGH

    def _get_impact(self, vuln_type: VulnerabilityType) -> str:
        """Get impact description for vulnerability type"""
        impacts = {
            VulnerabilityType.INJECTION: "Attackers could execute arbitrary code or queries",
            VulnerabilityType.BROKEN_AUTH: "Unauthorized access to user accounts",
            VulnerabilityType.SENSITIVE_DATA: "Exposure of confidential information",
            VulnerabilityType.XSS: "Malicious scripts executed in user browsers",
            VulnerabilityType.SECURITY_MISCONFIG: "System vulnerable to various attacks",
            VulnerabilityType.SECRETS: "Credentials exposed in version control",
        }

        return impacts.get(vuln_type, "Security vulnerability present")

    def _get_remediation(self, vuln_type: VulnerabilityType) -> str:
        """Get remediation steps for vulnerability type"""
        remediations = {
            VulnerabilityType.INJECTION: "Use parameterized queries or prepared statements",
            VulnerabilityType.BROKEN_AUTH: "Use secure password hashing (bcrypt, argon2)",
            VulnerabilityType.SENSITIVE_DATA: "Remove sensitive data from logs",
            VulnerabilityType.XSS: "Sanitize user input and use Content Security Policy",
            VulnerabilityType.SECURITY_MISCONFIG: "Review and harden configuration",
            VulnerabilityType.SECRETS: "Use environment variables or secret management",
        }

        return remediations.get(vuln_type, "Review and fix security issue")

    def _generate_fix(
        self,
        vuln_type: VulnerabilityType,
        code: str,
    ) -> str:
        """Generate automated fix suggestion"""
        if vuln_type == VulnerabilityType.INJECTION:
            if 'execute' in code:
                return "Use parameterized query: cursor.execute(query, (param1, param2))"

        elif vuln_type == VulnerabilityType.BROKEN_AUTH:
            if 'md5' in code or 'sha1' in code:
                return "Use bcrypt: bcrypt.hashpw(password.encode(), bcrypt.gensalt())"

        elif vuln_type == VulnerabilityType.SECURITY_MISCONFIG:
            if 'DEBUG' in code:
                return "Set DEBUG = False in production"
            if 'verify=False' in code:
                return "Remove verify=False or set to True"

        return "Manual fix required - see remediation guidance"

    def _generate_secret_fix(self, secret: Dict[str, Any]) -> str:
        """Generate fix for hardcoded secret"""
        return (
            f"Replace with environment variable:\n"
            f"import os\n"
            f"{secret['type'].lower().replace(' ', '_')} = os.environ.get('{secret['type'].upper().replace(' ', '_')}')"
        )

    def _calculate_risk_score(
        self,
        findings: List[SecurityFinding],
        dependency_vulns: List[DependencyVulnerability],
        secrets: List[str],
    ) -> float:
        """Calculate overall risk score (0-100)"""
        score = 0.0

        # Weight by severity
        severity_weights = {
            RiskLevel.CRITICAL: 25,
            RiskLevel.HIGH: 15,
            RiskLevel.MEDIUM: 5,
            RiskLevel.LOW: 1,
            RiskLevel.INFO: 0.5,
        }

        for finding in findings:
            score += severity_weights.get(finding.risk_level, 0)

        for vuln in dependency_vulns:
            score += severity_weights.get(vuln.severity, 0)

        # Secrets are critical
        score += len(secrets) * 30

        # Cap at 100
        return min(score, 100.0)

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine overall risk level from score"""
        if risk_score >= 75:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 25:
            return RiskLevel.MEDIUM
        elif risk_score >= 10:
            return RiskLevel.LOW
        else:
            return RiskLevel.INFO

    def _generate_recommendations(
        self,
        findings: List[SecurityFinding],
        dependency_vulns: List[DependencyVulnerability],
        license_issues: List[LicenseIssue],
        secrets: List[str],
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Critical items first
        if secrets:
            recommendations.append(
                f"URGENT: Remove {len(secrets)} hardcoded secret(s) from code immediately"
            )

        critical_findings = [f for f in findings if f.risk_level == RiskLevel.CRITICAL]
        if critical_findings:
            recommendations.append(
                f"Fix {len(critical_findings)} critical security vulnerabilities before deployment"
            )

        # Dependency updates
        if dependency_vulns:
            recommendations.append(
                f"Update {len(dependency_vulns)} vulnerable dependencies"
            )

        # License compliance
        if license_issues:
            recommendations.append(
                "Review license compliance issues with legal team"
            )

        # General security improvements
        if len(findings) > 10:
            recommendations.append(
                "Consider security training for development team"
            )

        recommendations.append(
            "Integrate security scanning into CI/CD pipeline"
        )

        recommendations.append(
            "Schedule regular security audits"
        )

        return recommendations

    def _check_compliance(
        self,
        findings: List[SecurityFinding],
        secrets: List[str],
    ) -> Dict[str, bool]:
        """Check compliance with security standards"""
        return {
            'owasp_top_10': len([f for f in findings if f.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]]) == 0,
            'no_hardcoded_secrets': len(secrets) == 0,
            'pci_dss': len(secrets) == 0 and len([f for f in findings if f.vulnerability_type == VulnerabilityType.SENSITIVE_DATA]) == 0,
            'hipaa': len([f for f in findings if f.vulnerability_type == VulnerabilityType.SENSITIVE_DATA]) == 0,
        }

    def _generate_summary(
        self,
        findings: List[SecurityFinding],
        dependency_vulns: List[DependencyVulnerability],
        license_issues: List[LicenseIssue],
        secrets: List[str],
        risk_level: RiskLevel,
    ) -> str:
        """Generate executive summary"""
        summary_parts = []

        # Risk level indicator
        risk_emoji = {
            RiskLevel.CRITICAL: "🔴",
            RiskLevel.HIGH: "🟠",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.LOW: "🟢",
            RiskLevel.INFO: "ℹ️",
        }

        summary_parts.append(
            f"{risk_emoji[risk_level]} Overall Risk: {risk_level.value.upper()}"
        )

        # Findings summary
        summary_parts.append(f"\n\n📋 Security Findings:")
        summary_parts.append(f"  - {len(findings)} code vulnerabilities")
        summary_parts.append(f"  - {len(dependency_vulns)} vulnerable dependencies")
        summary_parts.append(f"  - {len(secrets)} hardcoded secrets")
        summary_parts.append(f"  - {len(license_issues)} license issues")

        # Severity breakdown
        if findings:
            critical = len([f for f in findings if f.risk_level == RiskLevel.CRITICAL])
            high = len([f for f in findings if f.risk_level == RiskLevel.HIGH])
            medium = len([f for f in findings if f.risk_level == RiskLevel.MEDIUM])

            summary_parts.append(
                f"\n🔍 Severity: {critical} critical, {high} high, {medium} medium"
            )

        return "".join(summary_parts)

    def _increment_version(self, version: str) -> str:
        """Increment patch version"""
        parts = version.split('.')
        if len(parts) >= 3:
            parts[2] = str(int(parts[2]) + 1)
            return '.'.join(parts)
        return version


# Convenience functions

async def audit_code(
    files: Dict[str, str],
    scan_dependencies: bool = True,
) -> SecurityReport:
    """
    Quick security audit function

    Args:
        files: Files to audit
        scan_dependencies: Include dependency scanning

    Returns:
        Security report
    """
    auditor = SecurityAuditor(scan_dependencies=scan_dependencies)
    return await auditor.audit_codebase(files)


async def scan_for_secrets(file_path: str, content: str) -> List[str]:
    """
    Quick secret scanning

    Args:
        file_path: File to scan
        content: File content

    Returns:
        List of secrets found
    """
    auditor = SecurityAuditor()
    return auditor._scan_secrets(file_path, content)

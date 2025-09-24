# Security Policy

## 🔒 Security Overview

The Filesystem MCP Server handles file system operations, Git repositories, Docker containers, and various system-level operations. We take security seriously and appreciate your help in keeping our users safe.

## 🚨 Reporting Security Vulnerabilities

If you discover a security vulnerability, please report it to us as follows:

### 📧 Contact Information
- **Email**: security@filesystem-mcp.com (placeholder - update with actual contact)
- **GitHub Security Advisories**: [Create a private security advisory](https://github.com/sandr/filesystem-mcp/security/advisories/new)

### 📝 What to Include
Please include the following information in your report:
- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact and severity
- Any suggested fixes or mitigations
- Your contact information for follow-up

## 🔍 Security Considerations

### File System Operations
- All file operations are validated for path traversal attacks
- File access is restricted to the current working directory and subdirectories
- No access to system-critical files or directories

### Docker Operations
- Container operations require proper Docker daemon access
- No privileged container execution by default
- Image operations are logged and auditable

### Network Operations
- No outbound network requests without explicit user consent
- All API calls are properly authenticated and validated

## 🛡️ Security Features

### Built-in Security Measures
- ✅ Path traversal protection
- ✅ Input validation and sanitization
- ✅ Comprehensive logging and audit trails
- ✅ No arbitrary code execution
- ✅ Secure credential handling
- ✅ File permission validation

### Automated Security Scanning
- 🔍 **CodeQL Security Analysis**: Weekly automated security scans
- 🔍 **Dependency Vulnerability Scanning**: Automated with Trivy and Safety
- 🔍 **Container Security**: Docker image vulnerability scanning
- 🔍 **Secret Detection**: Automated secret scanning in CI/CD

## 📋 Vulnerability Classification

We use the following severity levels:

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **Critical** | Remote code execution, data loss, system compromise | < 24 hours |
| **High** | Privilege escalation, significant data exposure | < 72 hours |
| **Medium** | Limited information disclosure, DoS conditions | < 1 week |
| **Low** | Minor issues with limited impact | < 2 weeks |

## 🕐 Response Process

1. **Acknowledgment**: We'll acknowledge receipt within 24 hours
2. **Investigation**: We'll investigate and provide regular updates
3. **Fix Development**: We'll develop and test a fix
4. **Release**: We'll release the fix and security advisory
5. **Disclosure**: We'll coordinate public disclosure timing

## 🎉 Recognition

We appreciate security researchers who help keep our users safe. With your permission, we'll acknowledge your contribution in our security advisories and hall of fame.

## 📜 Security Updates

Subscribe to our releases to stay informed about security updates:
- [GitHub Releases](https://github.com/sandr/filesystem-mcp/releases)
- [Security Advisories](https://github.com/sandr/filesystem-mcp/security/advisories)

## 📞 Support

For general support or questions about security best practices:
- [GitHub Discussions](https://github.com/sandr/filesystem-mcp/discussions)
- [Documentation](https://github.com/sandr/filesystem-mcp/blob/main/README.md)

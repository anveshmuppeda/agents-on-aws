# Security Policy

## Supported Versions

This repository contains educational guides and example code. We maintain the latest version of each guide.

| Version | Supported |
|---------|-----------|
| `main` branch | ✅ |
| Older commits | ❌ |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

If you discover a security issue in any guide — for example, insecure CDK configurations, overly permissive IAM policies, hardcoded credentials in example code, or a pattern that could lead to data exposure in production — please report it privately.

### How to report

Email: [muppedaanvesh@gmail.com](mailto:muppedaanvesh@gmail.com)

Subject line: `[SECURITY] agents-on-aws — <brief description>`

Include:
- Which guide(s) are affected (e.g. `021-gateway-lambda-tool`)
- A description of the vulnerability
- Steps to reproduce or demonstrate the issue
- The potential impact

### What happens next

1. You will receive an acknowledgment within **48 hours**
2. We will investigate and work on a fix within **7 days** for critical issues
3. We will credit you in the fix commit unless you prefer to remain anonymous
4. We will open a public issue and PR once the fix is ready

## Security Best Practices for Guide Users

When using these guides in production, please review:

- **IAM permissions** — guides use broad permissions for simplicity; scope down to least-privilege in production
- **Secrets** — never commit `.env` files or credentials; all secrets should be in AWS Secrets Manager or AgentCore Identity
- **CDK destroy** — always run `bash destroy.sh` after testing to avoid leaving resources exposed
- **Network mode** — guides use `PUBLIC` network mode; consider `VPC` mode for sensitive workloads
- **JWT auth** — enable inbound JWT auth (guide 029) for any public-facing Runtime endpoints

## Credential Safety

This repo's guides intentionally do NOT include any real credentials, API keys, or secrets. If you see any committed credentials (even example ones that look real), please report them immediately.

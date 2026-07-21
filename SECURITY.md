# Security Policy

## Supported Versions

KToolBox provides security fixes for the current major release. Older release
lines may receive a fix only at the maintainers' discretion.

| KToolBox version | Supported          |
|------------------|--------------------|
| 1.x              | :white_check_mark: |
| 0.24.x and older | :x:                |

KToolBox 1.x supports CPython 3.10 through 3.14. Reports that reproduce only
on an unsupported Python version or an unmodified third-party package should
first be directed to the relevant upstream project.

## Reporting a Vulnerability

Please do not open a public issue for a suspected vulnerability. Use one of
these private channels instead:

1. Submit a [private GitHub security advisory](https://github.com/Ljzd-PRO/KToolBox/security/advisories/new) (preferred).
2. Email the maintainer at [me@ljzd.link](mailto:me@ljzd.link) if GitHub's private reporting form is unavailable.

Include enough information for the maintainers to reproduce and assess the
issue:

- the affected KToolBox version or commit;
- operating system and Python version;
- impact, prerequisites, and a minimal reproduction or proof of concept;
- relevant configuration and logs with credentials, cookies, personal data,
  downloaded content, and local paths removed; and
- any known mitigations or suggested fixes.

Do not include a Pawchive session cookie, account credential, private post
content, or other secret in a report. If a secret is exposed accidentally,
revoke or rotate it before continuing the report.

The maintainers aim to acknowledge a report within 7 days, provide an initial
assessment within 14 days, and coordinate disclosure after a fix is available.
Timelines may vary with severity and complexity. Please allow a reasonable
remediation period before publishing details.

## Scope

This policy covers vulnerabilities in KToolBox's source code, packaged CLI,
configuration handling, Pawchive API client, and download workflow. Examples
include arbitrary code execution, path traversal, unsafe file writes, credential
disclosure, and security boundary bypasses.

The following are outside this repository's security scope:

- vulnerabilities in the Pawchive service, website, file host, or its accounts;
- availability, content, or policy issues controlled by Pawchive;
- unsupported account-authenticated Pawchive operations; and
- general bugs, feature requests, and documentation errors without a security
  impact.

Report Pawchive service vulnerabilities privately to the Pawchive maintainers.
For non-security KToolBox bugs and feature requests, use the public
[issue tracker](https://github.com/Ljzd-PRO/KToolBox/issues).

## Safe Research

When investigating a potential vulnerability:

- use only systems, files, and accounts you own or are authorized to test;
- avoid accessing or retaining other users' data;
- avoid destructive actions, service disruption, and high-volume requests or
  downloads; and
- stop testing and report privately if you encounter sensitive data.

Good-faith research that follows these guidelines is appreciated. This policy
does not authorize testing against Pawchive or any other third-party service.

## Operational Guidance

Treat `.env` and `prod.env` as secret-bearing files when
`downloader.session_key` is configured. Do not commit or share them. KToolBox
sends that cookie only to configured file-download requests; API requests do
not support an account session. Review custom API and file-host URLs before use,
and install KToolBox and its dependencies from trusted sources.

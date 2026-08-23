# Project Information

## Release status

KToolBox v1 is the new Pawchive-based release line. It is a breaking upgrade from v0 and has not yet received enough real-world validation, so test a bounded download before relying on a large synchronization. Start with [Migrating to v1](migration-v1.md) when upgrading an existing installation.

Kemono is no longer available, and Pawchive is the only supported backend. The original Pawchive OpenAPI file remains untouched so generated-client changes can be audited against the normalized contract.

## Support and resources

Use the documentation search and [FAQ](faq.md) before leaving the documentation site. If the answer is missing, use these intentional project links:

- [Issue tracker](https://github.com/Ljzd-PRO/KToolBox/issues) for reproducible defects;
- [Discussions](https://github.com/Ljzd-PRO/KToolBox/discussions) for questions and proposals;
- [Releases](https://github.com/Ljzd-PRO/KToolBox/releases) for published notes and artifacts; and
- [Source repository](https://github.com/Ljzd-PRO/KToolBox) for code and contribution history.

## Quality and license

The default test suite is fully offline and blocks accidental network access. CI validates the OpenAPI contracts, deterministic generation, tests, Ruff, Mypy, Python bytecode compilation, package artifacts, WebUI builds, and strict MkDocs builds.

KToolBox uses the [BSD 3-Clause License](https://opensource.org/license/bsd-3-clause). Copyright © 2023 by Ljzd-PRO.

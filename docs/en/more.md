# Project Information

## Development branch

The Pawchive v1 work is maintained on the [`pawchive`](https://github.com/Ljzd-PRO/KToolBox/tree/pawchive) branch until it is ready to become the default release line.

Changes are split into focused commits covering the contract, client, project migration, tests, documentation, and release metadata. The original Pawchive OpenAPI file remains untouched so generated-code changes can be audited against the normalized contract.

## Quality policy

The default test suite is fully offline and blocks accidental network access. The handwritten API layer must retain 100% line and branch coverage, generated models are excluded from statistics, and the full project must remain at or above 85% coverage.

CI also validates the OpenAPI document, deterministic model generation, Ruff, strict API-layer Mypy, Python bytecode compilation, package builds, and strict MkDocs builds on supported Python versions.

## License

KToolBox is licensed under the [BSD 3-Clause License](https://github.com/Ljzd-PRO/KToolBox/blob/master/LICENSE).

Copyright © 2023 by Ljzd-PRO.

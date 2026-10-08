# Public release preparation

The initial release is an alpha toolkit: importing, reviewed-case execution and
[three-KPI artifact scoring](agentic-kpis.md) work, but no approved agentic cases
or measured live model score ship with the dataset. The configured target is
GPT-6.1 Sol, with equal weights for state recreation, human-move agreement and
rule correctness. State this when describing results; source observations,
candidate counts and structural operation coverage are not agent performance scores.

## Publication scope

The code and documentation are MIT licensed. Replay source data has separate
attribution in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). The selected
fixture includes actual displayed usernames and match chat. No separate
third-party redistribution license was supplied. Review this data-publication
scope before making the repository public; the code license does not resolve
rights to third-party replay content.

Changing visibility exposes existing Git history too. The removed archive
fixture remains in historical commits with its original MIT source notice.
The release-preparation scan examined all 14 main-history commits and 1,602
unique tracked file versions at commit `c86a55b299926f5e24e85ede9b73767c2ef30c86`.
No matches were found for the checked credential patterns: GitHub/provider keys,
AWS access keys, private-key blocks, JWTs, URL passwords and long assigned
credentials. This is a bounded pattern scan, not proof that every sensitive
value can be detected. No history rewrite was performed.

Raw imports, runs, environment files, keys and harness saves must stay local.
The repository requires no secrets for offline CI or public harness tests.
Only a caller-supplied model transport needs provider credentials; keep those
outside source control and outside player packets.

## Verify a release candidate

From a clean checkout, using Python 3.11 or newer:

```sh
python -m pip install .
python -m unittest discover -s tests -v
yugioh-benchmark inspect replays/db-text-aco77-sdesowitz02-2026-10-07
python -m pip install build
python -m build
```

Offline CI runs conversion/scoring tests on Linux and Windows with Python
3.11–3.13, integration tests against the pinned public harness, and installation
tests for the built wheel. The wheel contains the Python toolkit and license
notices. The source distribution also includes docs, schemas, tests and selected
source fixtures; use it or a repository checkout when working with the dataset.

## Make public and release

1. Merge the release-preparation PR after CI passes.
2. Change repository visibility to public in GitHub Settings, after reviewing
   the source data and history scope above.
3. For a versioned release, keep `pyproject.toml` and the package
   `__version__` consistent, update `CHANGELOG.md`, and create a matching tag.
4. Run **Build release artifacts** in Actions, or push a `v*` tag. Download the
   `yugioh-benchmark-dist` artifact containing the wheel and source distribution.
5. If desired, create a GitHub Release for that tag and attach those files.

The artifact workflow has read-only repository permissions and does not publish
to PyPI, create a release, push a tag or change repository visibility.

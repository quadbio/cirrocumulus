# quadbio fork of cirrocumulus

Why this fork exists, and how to keep it working.

Upstream is [lilab-bcb/cirrocumulus](https://github.com/lilab-bcb/cirrocumulus) and is
actively maintained. We run from source only because a few server-side bugs made most of
the UI unusable; each one is open as an upstream PR, and once they land this fork can go
away and `uv tool install cirrocumulus` is enough again.

| PR | What it fixes |
| --- | --- |
| [#230](https://github.com/lilab-bcb/cirrocumulus/pull/230) | `X_stats` returned 2-D columns for sparse `X`, 500ing the composition view |
| [#231](https://github.com/lilab-bcb/cirrocumulus/pull/231) | `DotPlotAggregator` was written for a DataFrame but is passed an AnnData, 500ing the dot plot view; multi-dimension grouping was broken too |
| [#232](https://github.com/lilab-bcb/cirrocumulus/pull/232) | pre-commit.ci could not build its hook environment on Python 3.12+ |
| [#233](https://github.com/lilab-bcb/cirrocumulus/pull/233) | zarr stores written by modern anndata could not be opened at all |

Each PR lives on its own branch off `upstream/main`. `main` here is upstream plus the
branches we actually need merged, and is what we install. #233 is deliberately *not*
merged into `main`: we feed the viewer an h5ad, so it buys us nothing and only adds
divergence to carry.

## Install

```bash
python scripts/fetch_client.py     # populate build/ (see below)
uv tool install . --force --python 3.12
```

**Deliberately not `--editable`.** This clone is also where the PR branches are developed,
and an editable install serves whatever branch happens to be checked out — so a plain
`git checkout` silently changes the running app. (That bit us once.) A regular install
snapshots `main`, at the cost of one reinstall per update.

## The `build/` directory

`cirrocumulus/client` is a symlink to gitignored `build/`, which upstream produces with
`yarn build`. We do not build it: it needs a node toolchain and ~50 npm packages via the
unmaintained `react-scripts`, and there is no node module on Euler. Published wheels
already ship the built client, so `scripts/fetch_client.py` unpacks it from one and
records the version in `build/CLIENT_VERSION`. Hatchling follows the symlink, so the
client ends up in our own wheel too.

This is sound **only because every change here is server-side Python**. If anyone ever
patches `src/`, the client has to be built for real and this shortcut has to go.

## Update from upstream

```bash
git checkout main && git fetch upstream && git merge upstream/main
.venv/bin/python -m pytest tests/ -q               # see below
python scripts/fetch_client.py --version <newer>   # only if you want a newer client
uv tool install . --force --python 3.12
```

Test baseline: `tests/test_de.py` has 64 pre-existing failures (`KeyError: 0`) unrelated
to anything here. Everything else should pass. Set the dev venv up with:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e . -r requirements-test.txt pyarrow
```

## Who uses this

`gli3_merscope_analysis` — `gli3-merscope-analysis viewer launch`. See that repo's
`AGENTS.md`.

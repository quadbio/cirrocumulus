# quadbio fork of cirrocumulus

Upstream is [lilab-bcb/cirrocumulus](https://github.com/lilab-bcb/cirrocumulus). We run from
source because a few server-side bugs make most of the UI unusable, and because we browse zarr
stores written by current anndata, which upstream cannot read.

## Branch model

| branch | what it is |
| --- | --- |
| `main` | a **mirror of `upstream/main`**. Never commit here. It is the base every topic branch is cut from, and the answer to "what does upstream actually say?" |
| `fix/*`, `fork/*` | one branch per change. Each `fix/*` is an open upstream pull request; `fork/tooling` is ours forever and is not upstreamable |
| `integration` | **what we install and run.** Rebuilt by merging every topic onto `main`; never committed to directly |

`integration` is *recreated*, not appended to, so it is force-pushed. Two rules follow: never
branch off it, and never `git pull` it — use `git fetch && git reset --hard origin/integration`.

Topic branches are not rebased while their PR is open unless upstream moves under them, since
rebasing force-pushes the PR.

**Why not merge everything into `main`?** Because upstream is alive. When they merge one of our
PRs, a divergent `main` carries that change twice from two different commits, and the next
`git merge upstream/main` conflicts. Against a mirror it is always a fast-forward, and retiring a
merged fix is one line out of the recipe below.

## Rebuilding `integration`

```bash
git fetch upstream && git checkout main && git merge --ff-only upstream/main && git push
git checkout -B integration main
for b in fork/tooling fix/x-stats-sparse-dense fix/dotplot-aggregator-anndata \
         fix/anndata-013-none-layer fix/zarr-categorical-obs fix/zarr3; do
    git merge --no-edit "$b" || break   # resolve, `git commit`, then rerun from the failed branch
done
git push --force-with-lease origin integration
```

One at a time, not an octopus merge — an octopus refuses the moment any pair conflicts,
and these branches touch the same files.

That list is the recipe. Drop a branch from it once upstream merges its PR, then delete the branch.

## Topics

| branch | upstream PR | what it fixes |
| --- | --- | --- |
| `fork/tooling` | — | this file and `scripts/fetch_client.py`. Never upstreamable |
| `fix/x-stats-sparse-dense` | [#230](https://github.com/lilab-bcb/cirrocumulus/pull/230) | `X_stats` returned 2-D columns for sparse `X`, 500ing the composition view, and did not handle dense `X` at all |
| `fix/dotplot-aggregator-anndata` | [#231](https://github.com/lilab-bcb/cirrocumulus/pull/231) | `DotPlotAggregator` was written for a DataFrame but is passed an AnnData, 500ing the dot plot view; multi-dimension grouping was broken too |
| `fix/anndata-013-none-layer` | new | anndata >= 0.13 exposes `None` in `layers` as an alias for `X`, so six call sites treated it as a layer. Broke the parquet and zarr writers |
| `fix/zarr-categorical-obs` | [#233](https://github.com/lilab-bcb/cirrocumulus/pull/233) | elements anndata writes as *groups* rather than arrays — categoricals, nullable strings — could not be read at all |
| `fix/zarr3` | new | zarr 3 support: unpins `zarr<3`, and replaces the vendored 2021-era anndata zarr writer with `anndata.io.write_elem`. Upstream [#235](https://github.com/lilab-bcb/cirrocumulus/pull/235) removes the pin without any of this |

Retired: #232 (docformatter) — upstream switched to ruff in #234, so the hook is gone.

## Install

```bash
git checkout integration
python scripts/fetch_client.py     # populate build/ (see below)
uv tool install . --force --python 3.12
```

**Deliberately not `--editable`.** This clone is also where topic branches are developed, and an
editable install serves whatever branch happens to be checked out — so a plain `git checkout`
would silently change the running app. (That bit us once.) A regular install snapshots
`integration`, at the cost of one reinstall per update.

## The `build/` directory

`cirrocumulus/client` is a symlink to gitignored `build/`, which upstream produces with
`yarn build`. We do not build it: it needs a node toolchain and ~50 npm packages, and there is no
node module on Euler. Published wheels already ship the built client, so
`scripts/fetch_client.py` unpacks it from one and records the version in `build/CLIENT_VERSION`.
Hatchling follows the symlink, so the client ends up in our own wheel too.

This is sound **only because every change here is server-side Python**. If anyone ever patches
`src/`, the client has to be built for real and this shortcut has to go.

## Tests

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e . -r requirements-test.txt pyarrow mongomock
.venv/bin/python -m pytest tests/ -q
```

Baseline: `tests/test_de.py` has 64 pre-existing failures (`KeyError: 0`) unrelated to anything
here. Everything else should pass.

## Who uses this

`gli3_merscope_analysis` — `gli3-merscope-analysis viewer launch`. See that repo's `AGENTS.md`.

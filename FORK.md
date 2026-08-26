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
         fix/anndata-013-none-layer fix/zarr-categorical-obs fix/zarr3 fix/pandas3; do
    git merge --no-edit "$b" || break   # resolve, `git commit`, then rerun from the failed branch
done
git push --force-with-lease origin integration
```

One at a time, not an octopus merge — an octopus refuses the moment any pair conflicts,
and these branches touch the same files.

That list is the recipe. Drop a branch from it once upstream merges its PR, then delete the branch.

## Cutting a release

Consumers install a wheel from a GitHub Release; a `git+https://` install has no UI (see
"The `build/` directory").

After rebuilding `integration`:

```bash
git tag -a quadbio-1.1.61.postN -m "<one line>" integration
git push origin quadbio-1.1.61.postN
```

`.github/workflows/release.yml` builds the client, checks the wheel really ships it, serves it
once, and attaches `cirrocumulus-1.1.61.postN-py3-none-any.whl`. Pushing `integration` runs
everything except the publish — push the branch first, tag once it is green.

`postN` is sequential; restart at `.post1` when upstream releases a new version. The `quadbio-`
prefix keeps our tags out of upstream's namespace and is stripped by setuptools_scm, so the
version is `1.1.61.postN` — after upstream's 1.1.61, before their 1.1.62.

**Never delete a release tag.** `integration` is force-pushed, so the tag is the only thing
keeping that tree reachable.

Without CI — build the client (below), then:

```bash
uv build --wheel
python scripts/check_wheel.py dist/*.whl
gh release create quadbio-1.1.61.postN dist/*.whl --repo quadbio/cirrocumulus
```

`--repo` is not optional: in this clone `gh` can resolve to `upstream`.

## Topics

| branch | upstream PR | what it fixes |
| --- | --- | --- |
| `fork/tooling` | — | this file, `scripts/check_wheel.py` and `.github/workflows/release.yml`. Never upstreamable |
| `fix/x-stats-sparse-dense` | [#230](https://github.com/lilab-bcb/cirrocumulus/pull/230) | `X_stats` returned 2-D columns for sparse `X`, 500ing the composition view, and did not handle dense `X` at all |
| `fix/dotplot-aggregator-anndata` | [#231](https://github.com/lilab-bcb/cirrocumulus/pull/231) | `DotPlotAggregator` was written for a DataFrame but is passed an AnnData, 500ing the dot plot view; multi-dimension grouping was broken too |
| `fix/anndata-013-none-layer` | [#236](https://github.com/lilab-bcb/cirrocumulus/pull/236) | anndata >= 0.13 exposes `None` in `layers` as an alias for `X`, so six call sites treated it as a layer. Broke the parquet and zarr writers |
| `fix/zarr-categorical-obs` | [#233](https://github.com/lilab-bcb/cirrocumulus/pull/233) | elements anndata writes as *groups* rather than arrays — categoricals, nullable strings — could not be read at all |
| `fix/zarr3` | [#237](https://github.com/lilab-bcb/cirrocumulus/pull/237) | zarr 3 support: unpins `zarr<3`, and replaces the vendored 2021-era anndata zarr writer with `anndata.io.write_elem`. Upstream [#235](https://github.com/lilab-bcb/cirrocumulus/pull/235) removes the pin without any of this |
| `fix/pandas3` | [#238](https://github.com/lilab-bcb/cirrocumulus/pull/238) | pandas 3 backs strings with `ArrowStringArray`, which the JSON encoder recurses into until it overflows. Broke `prepare_data --format jsonl` entirely, and 500'd `/api/data` for every categorical `obs` — the UI loaded but could not colour by anything textual. Plus one DE test that built its fixture with `Series.replace` on a categorical |

Retired: #232 (docformatter) — upstream switched to ruff in #234, so the hook is gone.

## Install

To use it — no clone, no node toolchain, works on Euler and on a Mac:

```bash
uv tool install <wheel URL from the latest release> --python 3.12
```

`gli3_merscope_analysis` declares that same URL in its `pixi.toml`.

To develop it:

```bash
git checkout integration
# build the client -- see below
uv tool install . --force --python 3.12
```

**Deliberately not `--editable`.** This clone is also where topic branches are developed, and an
editable install serves whatever branch happens to be checked out — so a plain `git checkout`
would silently change the running app. (That bit us once.) A regular install snapshots
`integration`, at the cost of one reinstall per update.

## The `build/` directory

`cirrocumulus/client` is a symlink to gitignored `build/`, which `yarn build` produces. CI builds
it for every release, so the wheel carries the client. Locally, on Euler:

```bash
module load stack/2025-06 gcc/12.2.0 node-js/22.4.0 eth_proxy
export COREPACK_HOME="$SCRATCH/corepack"      # the module ships corepack, not npm
corepack prepare yarn@1.22.22 --activate      # yarn.lock is v1 / Classic
corepack yarn install --frozen-lockfile --ignore-engines
corepack yarn build                           # "Compiled with warnings", exit 0
```

`--ignore-engines` is needed because `puppeteer` wants node >= 22.12 and Euler caps at 22.4; it is
a devDependency for the e2e tests only. Do not carry it into CI, where node 26 satisfies the
constraint and an engine failure should be loud.

**An empty `build/` produces a wheel with no client, silently** — no error, just a 404 on `/` at
runtime. That is what `scripts/check_wheel.py` exists to catch, in CI and by hand.

To run the tests you do not need the client, only a symlink that resolves — `mkdir -p build` is
enough. A *dangling* symlink breaks every build; an *empty* target does not.

## Tests

```bash
mkdir -p build     # only needed if you have not built the client
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e . -r requirements-test.txt pyarrow mongomock
.venv/bin/python -m pytest tests/ -q
```

Measured 2026-08-24, anndata 0.13.2 / zarr 3.3.0 / pandas 3.0.5:

| | failed | passed |
| --- | --- | --- |
| plain `upstream/main` | 88 (+16 errors) | 1144 |
| `integration` | **0** | **1384** |

**`integration` is green.** Any failure is a regression — there is no baseline to subtract.

## Who uses this

`gli3_merscope_analysis` — `gli3-merscope-analysis viewer launch`. It declares the release wheel
in the `viewer` feature of its `pixi.toml`; updating cirro there means bumping that URL. See that
repo's `AGENTS.md`.

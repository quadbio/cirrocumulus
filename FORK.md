# quadbio fork of cirrocumulus

Upstream is [lilab-bcb/cirrocumulus](https://github.com/lilab-bcb/cirrocumulus). We run from
source because a few server-side bugs make most of the UI unusable, and because we browse zarr
stores written by current anndata, which upstream cannot read.

## Branch model

| branch | what it is |
| --- | --- |
| `main` | **what we install, run and release.** Append-only, never force-pushed. Everything lands here by pull request |
| `fix/*`, `feat/*`, `chore/*` | one branch per change, cut from `main` and merged back into `main` |
| `upstream/main` | the remote-tracking ref *is* our mirror. There is no local or pushed copy |

**Upstream does not take our patches.** Of the 100 most recently merged PRs upstream, back to
Jan 2023, every one came from lilab-bcb itself; the only outside contributor PR has been open
since Oct 2024. The six PRs under [Topics](#topics) stay open, but they are the last ones we send.

To offer something upstream anyway, cut *that one* branch from `upstream/main`. This degrades —
once `main` has taken upstream merges, extracting an upstream-applicable patch gets harder.

## Landing a change

Cut from `main`, PR into `main`, squash or merge as suits. A ruleset on `main` blocks force-pushes
and deletion and requires the PR, so a direct push is refused.

## Merging upstream

```bash
git fetch upstream
git switch -c chore/merge-upstream-$(date +%F) main
git merge upstream/main          # a real merge; `--ff-only` stopped applying when main diverged
git push -u origin HEAD
```

Then PR into `main` and **merge it with a merge commit. Never squash it, never rebase it.**
Squashing discards the second parent, `upstream/main` stops being an ancestor of `main`, and every
later merge re-conflicts on everything. (Squash is fine for ordinary topic PRs; only fatal here.)

Expect conflicts. Merges are clean when upstream merges *our* commits — they use merge commits, so
our SHAs become ancestors. What conflicts is upstream reimplementing a fix independently, as in
[#235](https://github.com/lilab-bcb/cirrocumulus/pull/235), which drops the `zarr<3` pin over the
same lines `fix/zarr3` rewrote. Turn on `git config rerere.enabled true` to resolve each such
conflict once.

`git diff upstream/main...main` is the answer to "what does the fork actually carry?"

## Cutting a release

Consumers install a wheel from a GitHub Release; a `git+https://` install has no UI (see
[The `build/` directory](#the-build-directory)).

```bash
git tag -a quadbio-1.1.61+quadbio.N -m "<one line>" main
git push origin quadbio-1.1.61+quadbio.N
```

`.github/workflows/release.yml` builds the client, runs `scripts/check_wheel.py`, serves the wheel
once, and attaches `cirrocumulus-1.1.61+quadbio.N-py3-none-any.whl`. Every push to `main` runs all
of that except the publish, so tag once `main` is green. `workflow_dispatch` reruns it by hand.

`1.1.61` is the upstream version we sit on; `+quadbio.N` is a **PEP 440 local version identifier**,
sequential, restarting at `.1` when upstream releases a new version. Local versions are the
mechanism for "upstream's release plus our patches", and PyPI *must not* accept them — which is
exactly why ours cannot collide with upstream's. That matters here: upstream has 86 `.postN` tags
on PyPI and has already released `1.1.61`, so the old `1.1.61.postN` scheme was claiming version
strings upstream can publish at will.

The `quadbio-` tag prefix keeps our tags out of upstream's namespace. `tag_regex` in
`pyproject.toml` strips it while keeping the local segment, which setuptools_scm's default would
otherwise drop; `check_wheel.py` fails the build if `+quadbio.` ever goes missing. Off-tag builds
keep the marker too — one commit past a tag gives `1.1.62.dev1+quadbio.N.g<sha>`.

**Never delete a release tag.** For `quadbio-1.1.61.post1` and `.post2` this is literal: they were
cut from the old force-pushed `integration` and are reachable from no branch at all, so the tag is
the only thing keeping those trees alive. From the next tag onward it is a stable reference into an
append-only `main` — still not something to delete, but no longer load-bearing.

## Install

To use it — no clone, no node toolchain, works on Euler and on a Mac:

```bash
uv tool install <wheel URL from the latest release> --python 3.12
```

To develop it, build the client (below) and then:

```bash
uv tool install . --force --python 3.12
```

**Deliberately not `--editable`.** This clone is also where topic branches are developed, and an
editable install serves whatever branch happens to be checked out — so a plain `git checkout`
would silently change the running app. (That bit us once.) A regular install snapshots `main`, at
the cost of one reinstall per update.

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
runtime. That is what `scripts/check_wheel.py` catches, in CI and by hand.

## Tests

The client is not needed, only a symlink that resolves: a *dangling* symlink breaks every build,
an *empty* target does not.

```bash
mkdir -p build
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e . -r requirements-test.txt pyarrow mongomock
.venv/bin/python -m pytest tests/ -q
```

Measured 2026-08-24, anndata 0.13.2 / zarr 3.3.0 / pandas 3.0.5: plain `upstream/main` gives 88
failed (+16 errors) / 1144 passed; `main` gives **0 failed / 1384 passed**. **`main` is green** —
any failure is a regression, with no baseline to subtract.

CI also runs `yarn test` and `yarn e2e`. **e2e is flaky**: the same tree failed and then passed on
consecutive runs, and it is red on upstream's `main` too. Triage an e2e failure against
`upstream/main` before assuming it is ours.

## Topics

All seven are merged into `main`; nothing is rebuilt from this table. The six `fix/*` branches are
kept alive only because deleting one closes its upstream PR. `fork/tooling` had no PR and is gone.

| branch | upstream PR | what it fixes |
| --- | --- | --- |
| `fork/tooling` | — | this file, `scripts/check_wheel.py`, `.github/workflows/release.yml`. Never upstreamable |
| `fix/x-stats-sparse-dense` | [#230](https://github.com/lilab-bcb/cirrocumulus/pull/230) | `X_stats` returned 2-D columns for sparse `X`, 500ing the composition view, and did not handle dense `X` at all |
| `fix/dotplot-aggregator-anndata` | [#231](https://github.com/lilab-bcb/cirrocumulus/pull/231) | `DotPlotAggregator` was written for a DataFrame but is passed an AnnData, 500ing the dot plot view; multi-dimension grouping was broken too |
| `fix/anndata-013-none-layer` | [#236](https://github.com/lilab-bcb/cirrocumulus/pull/236) | anndata >= 0.13 exposes `None` in `layers` as an alias for `X`, so six call sites treated it as a layer. Broke the parquet and zarr writers |
| `fix/zarr-categorical-obs` | [#233](https://github.com/lilab-bcb/cirrocumulus/pull/233) | elements anndata writes as *groups* rather than arrays — categoricals, nullable strings — could not be read at all |
| `fix/zarr3` | [#237](https://github.com/lilab-bcb/cirrocumulus/pull/237) | zarr 3 support: unpins `zarr<3`, replaces the vendored 2021-era anndata zarr writer with `anndata.io.write_elem` |
| `fix/pandas3` | [#238](https://github.com/lilab-bcb/cirrocumulus/pull/238) | pandas 3 backs strings with `ArrowStringArray`, which the JSON encoder recurses into until it overflows. Broke `prepare_data --format jsonl` entirely, and 500'd `/api/data` for every categorical `obs` — the UI loaded but could not colour by anything textual |

## Who uses this

`gli3_merscope_analysis` — `gli3-merscope-analysis viewer launch`. It pins the release wheel URL
in the `viewer` feature of its `pixi.toml`; updating cirro there means bumping that URL. See that
repo's `AGENTS.md`.

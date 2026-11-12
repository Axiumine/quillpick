# About Quillpick, an unofficial fork of Rizzo Flow

> **Quillpick is an unofficial community fork of [Rizzo Flow](https://github.com/Rizzo-AI-Academy/rizzo-flow) by Simone Rizzo / Rizzo AI Academy (Apache-2.0). Not affiliated with, endorsed or maintained by the upstream authors.**

This page says why the fork exists, what it adds to upstream and what it does not, who is credited,
and how to keep following upstream. Everything here can be checked against the git history of this
repository and the public pages of the upstream repository; the dates and counts were checked between
10 and 12 November 2026.

## Why the fork exists

These are the facts, with dates:

- The last commit on upstream `main` is `b9ba007`, dated 25 September 2026. There has been none since.
- Twelve pull requests are open upstream: #2, #8, #16, #17, #19, #21, #24, #26, #27, #28, #30 and
  #32. No review has been submitted on any of them, so none has an upstream maintainer's review, and
  the only comments on them are from their own authors. This fork reviewed the ones it considered
  merging; what it decided for each is listed below.
- Upstream issue [#29](https://github.com/Rizzo-AI-Academy/rizzo-flow/issues/29), opened on 30 September 2026
  to offer the fixes, the CI and lint setup and the test suite that are in this fork, is open and has no reply
  from the maintainers; its author added two follow-ups, on 7 October and on 10 November 2026.

Six of those pull requests are merged in this fork, and the others are listed below with the reason
each is not. They stay open upstream; this fork does not close them or comment on them.

So the changes below are published under another name, where people can install them and report
problems against them. They are Apache-2.0 like the rest, and upstream can take them, in whole or in
part, at any time. If upstream resumes, this fork would rather converge with it than diverge.

## Base

This fork starts from upstream `main` at commit `b9ba007` (25 September 2026) and adds 57 commits
on top of it. The first Quillpick release adds a few more, listed under "What the first release
changes" below, and the merges of upstream pull requests are listed under "Merged from upstream pull
requests".

## What this fork adds

The 57 commits, counted from `git log b9ba007..52afa67`:

- **29 commits that fix defects.** 24 of them change code in `src/rizzo_flow`; the other 5 raise the
  Python floor to 3.11.4 and the FastAPI floor to 0.132, fix the skill client and the report
  scripts, and declare `huggingface-hub` in the MLX extras. They cover input validation and HTTP
  status codes, the command line and the files it writes (reports and JSONL are UTF-8 with LF, a
  `--output` that already exists is refused before the weights load), downloads and runtime
  installation (a `.part` file that is already complete, the choice of runtime build, `PATH`
  entries, `HF_TOKEN` and `.env` parsing), and the llama.cpp backend (checks done before the
  weights are hashed, `--kv-type` validation, one library per runtime folder, waiting for the
  decode in flight before the model is freed). Each commit message says what it fixes.
- **6 commits for lint, types and CI.** ruff, mypy and deptry are enforced; the findings they
  reported are fixed, dead code is removed and one check is shared by both backends; a GitHub Actions workflow runs the lint job and the tests on Linux, macOS
  and Windows with Python 3.11 and 3.14.
- **22 commits for the test suite.** 19 of them add tests, one configures mutation testing
  (`mutmut`), one sets the 100% coverage gate in CI and one documents how to run all this. On
  `b9ba007` the tests were 8 `test_*.py` files; this fork has 48.

Test results, with the locked dependencies and the CPU MLX extra, on Linux with Python 3.12:

- Upstream `b9ba007`, its own tests run with this fork's locked dependencies: 82 passed and 6 skipped.
- This fork: **1813 passed and 6 skipped** in between 15 and 40 seconds, depending on the machine and
  on whether coverage is measured, with 100% line and branch coverage of
  `src/rizzo_flow` (1792 statements, 534 branches). The count includes the merged pull requests below.
  The 6 skipped are the integration tests that load real weights; they run only with `RIZZO_REAL=1`.

The tests use fakes: no network, no GPU, no weights and no real llama.cpp runtime. They do not
show that the real model gives the same answers on a given machine, and **this fork has not
re-run any measurement** of upstream's README. The one addition is the Linux + NVIDIA and CPU-only
report merged from pull request #26 (see below), which a contributor of this fork measured on
upstream's code before the fork. Every number inherited from upstream keeps the
caveats written next to it, probabilities are not calibrated, and nothing here claims to beat
Jev or SemIf.

## What the first release changes

- The product is called **Quillpick**: README (English and Italian), the other documents, the help
  text of the command line, the title of the OpenAPI document, the playground and Snake pages
  (Italian and English), the agent skill text and the landing page in `docs/`.
- A **new logo**, a plain placeholder that was drawn for this fork (a letter Q with a quill for a
  tail, no third-party art). The mascot of upstream is not used as the identity of the fork; the
  screenshots that still show it are captioned as upstream's, taken before the fork.
- The distribution is called `quillpick`; the lock file changes only because of that name, with no
  change of any dependency.
- This page, `SECURITY.md`, and a paragraph in `NOTICE` that says this is a modified version, as
  Apache-2.0 section 4 asks. `LICENSE` is unchanged and every upstream line of `NOTICE` is kept.

## Merged from upstream pull requests

These pull requests, open upstream, are merged here with `git merge --no-ff`, so the contributors'
own commits and authorship are in this repository's history
(`git log --format='%h %an | %s' b9ba007..HEAD`). Each merge is followed by commits that adapt what
it needed: tests, `request.schema.json` where a model changed, and the English and Italian
documents. The tests use fake backends and a fake llama.cpp session, so **none of these changes has
been run with the real model or a real runtime by this fork**.

- [#24](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/24), "Accept a choice with a single
  option (all backends)", by @msaelices. A `choice` with one option is accepted on both endpoints
  (it was a 422): with abstention it is a decision between that option and `__insufficient__`,
  without it the answer is certain by construction. Follow-up here: the tests that checked the old
  minimum and error message, a one-candidate job through the llama.cpp backend, the schema file, the
  Italian README and the skill reference.
- [#16](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/16), "Protect native decisions
  endpoint with configured API key", by @andypara73-ai. With `RIZZO_API_KEY` set,
  `POST /v1/decisions` needs the Bearer token like the other model endpoints; `/health` and the
  pages stay open. **Behaviour change** for clients of the native endpoint. The playground already
  sent its API key field on every endpoint; Snake had none and would have stopped working, so this
  fork added the field (Italian and English). The documents and the skill say which endpoints check
  the key.
- [#17](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/17), "Raise the per-request question
  limit from 64 to 256", by @andrea-tomassi. Both endpoints take up to 256 questions. The time grows
  with the number of questions; no request near the limit has been timed. Follow-up here: boundary
  tests at 256 and 257, a 256-question request through the engine and the llama.cpp backend, the
  schema file and the documents.
- [#30](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/30), "CI: OpenSSF Scorecard workflow,
  Dependabot for the actions, README badge", by @giovannimanzoni (a contributor of this fork). The
  workflow and the Dependabot file are pointed at `Axiumine/quillpick`, and a test checks that every
  action is pinned to a commit. The Scorecard workflow is **manual-only** here (`workflow_dispatch`,
  not push, schedule or branch-protection changes): this repository is registered on GitHub as a
  fork, and the README of the Scorecard action says that running it on a fork is not supported. It
  has **not run yet**, so it may need changes after a first run. The README badge is **not** merged:
  there is no badge until a score exists.
- [#32](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/32), "Document the RX 9070 XT Vulkan
  community report", by @monsterlag. Documentation only: the hardware table and the Italian README
  mention the report in [upstream issue #23](https://github.com/Rizzo-AI-Academy/rizzo-flow/issues/23)
  (Radeon RX 9070 XT, RADV, Vulkan). Not reproduced by upstream's maintainers or by this fork.
- [#26](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/26), "docs: community report for
  Linux + NVIDIA (CUDA, Vulkan) and desktop CPU-only", by @giovannimanzoni. Documentation only, in
  the hardware table, the README limits, the Italian README and the landing page. **The report was
  measured by a contributor of this fork**, with the base weights on upstream's code at `c30cc63`
  (before the fork), on their own machine (Debian 13, RTX PRO 4000 Blackwell, Ryzen 9 9950X3D); the
  raw data is in the
  [`hardware-report-issue-25` branch](https://github.com/Axiumine/quillpick/tree/hardware-report-issue-25)
  of this repository, and the report itself is
  [upstream issue #25](https://github.com/Rizzo-AI-Academy/rizzo-flow/issues/25). Nobody else has
  reproduced it. Upstream's own text keeps its attribution to upstream.

## Credits

- **Simone Rizzo and Rizzo AI Academy**: Rizzo Flow, the code, the documents, the benchmarks and
  the fine-tuned weights this fork builds on (`rizzoaiacademy/rizzo-flow` on Hugging Face).
  Everything that is not listed above is theirs.
- **XHToken**: the Spark-X2.5 models, their GGUF conversions and the Spark MLX runtime.
  **llama.cpp** and **ggml**, **MLX** and **MLX-LM**, as in `NOTICE`.
- **TypeSafe** for the idea and the API shape ("Jev" and "TypeSafe" belong to them), and **SemIf**
  by TheoLeeCJ for the fixtures and evaluator used in upstream's comparison.
- Contributors of the upstream pull requests that upstream merged, whose commits this fork inherits:
  [@danilocarta](https://github.com/danilocarta) (#4), [@BiG86](https://github.com/BiG86) (#6),
  [@radqnico](https://github.com/radqnico) (#10) and [@dajiaohuang](https://github.com/dajiaohuang) (#13).
  Upstream's README credits them in more detail.
- Authors of the upstream pull requests merged here, whose commits are in this history:
  [@msaelices](https://github.com/msaelices) (#24),
  [@andypara73-ai](https://github.com/andypara73-ai) (#16),
  [@andrea-tomassi](https://github.com/andrea-tomassi) (#17),
  [@giovannimanzoni](https://github.com/giovannimanzoni) (#30 and #26) and
  [@monsterlag](https://github.com/monsterlag) (#32). The Linux + NVIDIA report of #26 is
  @giovannimanzoni's own measurement; the RX 9070 XT report of #32 is in upstream issue #23.
- [@pieronoviello](https://github.com/pieronoviello): their upstream pull requests
  [#27](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/27) and
  [#28](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/28) fix the same two bugs as
  commits `04dd8bf` (a complete `.part` file on HTTP 416) and `0d64b5b` (check `--output` before the
  weights load) of this series. Their pull requests were opened on 2026-09-29, before those commits
  were dated; the author's account of the timeline is in
  [upstream issue #29](https://github.com/Rizzo-AI-Academy/rizzo-flow/issues/29). Either set of
  changes can replace the other.

## Upstream pull requests not merged

These are open upstream and are **not** in this fork. Each reason is a fact that can be checked
against the pull request:

- [#27](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/27) and
  [#28](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/28), by @pieronoviello: they fix two
  bugs that this series also fixes (see Credits), so merging them as well would duplicate the change.
- [#19](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/19), "Fix access violation error on
  rizzo serve", by @dav04, which refers to
  [upstream issue #18](https://github.com/Rizzo-AI-Academy/rizzo-flow/issues/18) (an "access
  violation reading 0x0000000000000000" on `rizzo serve` on Windows 11, reported also with
  `--device cpu`): reviewed by this fork, not merged. It changes two source files
  (`backend_llama.py` and `llama_cpp.py`) and adds no test. On Windows it scans the `PAGE_READWRITE`
  memory of libllama and of the ggml DLLs for a byte pattern (three consecutive 8-byte values
  2, 0, 0) and calls the MSVC mutex initialiser `_Mtx_init_in_situ` at each match, which writes a
  mutex structure there; the stated cause is that MSVC mutexes are left uninitialised, which this
  fork has not reproduced (it has no Windows machine). It also adds a `ggml_log_set` binding, on
  every platform. A CPU fallback runs only if loading the GPU runtime raises `OSError` or
  `ValueError`, the device is `auto` and a different CPU runtime is installed; otherwise the original
  error is raised again. The fallback logs nothing and has no platform guard.
- [#8](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/8), "Typed records end to end", by
  @mgattilabs: 38 files changed, 6,108 lines added and 5,038 removed, as GitHub counts the pull
  request; it conflicts with this fork's `main`.
- [#21](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/21), "MAX (Modular) backend", by
  @msaelices: 29 files changed, 31,759 lines added and 772 removed; it conflicts with this
  fork's `main`, and it needs the MAX runtime, which this fork has not run.
- [#2](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/2), "rizzo-flow-rs: an independent Rust
  port", by @alforiva1970: 44 files and 10,173 lines added, none removed: a separate code base, not
  a change to this one.

## Names kept for compatibility

Only the product name changed. These keep their upstream names so that scripts, clients, cached
downloads and the published weights keep working, and so that changes can still be exchanged with
upstream:

- the Python package `rizzo_flow` and the command `rizzo`;
- the `RIZZO_*` environment variables;
- the served model ids (`rizzo-latest`, `rizzo-flow-*`, `rizzo-spark-*`);
- the Hugging Face repositories `rizzoaiacademy/*`, with their revisions and sha256 pins;
- the agent skill folder and name `skills/rizzo-flow` and the downloader's HTTP User-Agent
  `rizzo-flow`;
- the `results/` and `benchmarks/` folders, which are historical, create-only data covered by
  `results/SHA256SUMS`, so they still say "Rizzo Flow".

A later release is planned to rename the package, the command and the variables. Until then nothing
in your scripts needs to change, and there is no date for it.

## Following upstream

```bash
git remote add upstream https://github.com/Rizzo-AI-Academy/rizzo-flow.git
git fetch upstream
git log --oneline main..upstream/main     # what upstream has that this fork does not
```

The first release is a rename on top of a series of independent commits, so merging upstream later
will conflict in the files that carry the product name (the README, the two pages, the CLI help);
the code under `src/rizzo_flow` is where the two histories are closest.

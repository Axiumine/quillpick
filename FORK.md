# About Quillpick, an unofficial fork of Rizzo Flow

> **Quillpick is an unofficial community fork of [Rizzo Flow](https://github.com/Rizzo-AI-Academy/rizzo-flow) by Simone Rizzo / Rizzo AI Academy (Apache-2.0). Not affiliated with, endorsed or maintained by the upstream authors.**

This page says why the fork exists, what it adds to upstream and what it does not, who is credited,
and how to keep following upstream. Everything here can be checked against the git history of this
repository and the public pages of the upstream repository; the dates and counts were checked on
10 November 2026.

## Why the fork exists

These are the facts, with dates:

- The last commit on upstream `main` is `b9ba007`, dated 25 September 2026. There has been none since.
- Twelve pull requests are open upstream: #2, #8, #16, #17, #19, #21, #24, #26, #27, #28, #30 and
  #32. None has a review, and the only comments on them are from their own authors.
- Upstream issue [#29](https://github.com/Rizzo-AI-Academy/rizzo-flow/issues/29), opened on 30 September 2026
  to offer the fixes, the CI and lint setup and the test suite that are in this fork, is open and has no reply
  from the maintainers; its author added one follow-up on 7 October 2026.

So the changes below are published under another name, where people can install them and report
problems against them. They are Apache-2.0 like the rest, and upstream can take them, in whole or in
part, at any time. If upstream resumes, this fork would rather converge with it than diverge.

## Base

This fork starts from upstream `main` at commit `b9ba007` (25 September 2026) and adds 57 commits
on top of it. The first Quillpick release adds a few more, listed under "What the first release
changes" below.

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
  `b9ba007` the tests were 8 `test_*.py` files; this fork has 47.

Test results, with the locked dependencies and the CPU MLX extra, on Linux with Python 3.12:

- Upstream `b9ba007`, its own tests run with this fork's locked dependencies: 82 passed and 6 skipped.
- This fork: **1790 passed and 6 skipped** in about 25 seconds, with 100% line and branch coverage of
  `src/rizzo_flow` (1788 statements, 532 branches). The 6 skipped are the integration tests that
  load real weights; they run only with `RIZZO_REAL=1`.

The tests use fakes: no network, no GPU, no weights and no real llama.cpp runtime. They do not
show that the real model gives the same answers on a given machine, and **this fork has not
re-run any measurement** of upstream's README. Every number inherited from upstream keeps the
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
- [@pieronoviello](https://github.com/pieronoviello): their upstream pull requests
  [#27](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/27) and
  [#28](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/28) fix the same two bugs as
  commits `04dd8bf` (a complete `.part` file on HTTP 416) and `0d64b5b` (check `--output` before the
  weights load) of this series. Their pull requests were opened on 2026-09-29, before those commits
  were dated; the author's account of the timeline is in
  [upstream issue #29](https://github.com/Rizzo-AI-Academy/rizzo-flow/issues/29). Either set of
  changes can replace the other.

## Upstream pull requests not merged here yet

These are open upstream and are **not** in this fork. They may be merged later, with credit to their
authors, after being checked against this code and its tests:

- [#2](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/2): a Rust port (`rizzo-flow-rs`), by @alforiva1970
- [#8](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/8): typed records end to end, by @mgattilabs
- [#16](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/16): protect the native decisions endpoint with the configured API key, by @andypara73-ai
- [#17](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/17): raise the per-request question limit from 64 to 256, by @andrea-tomassi
- [#19](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/19): fix an access violation on `rizzo serve`, by @dav04
- [#21](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/21): a MAX (Modular) backend, by @msaelices
- [#24](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/24): accept a choice with a single option, by @msaelices
- [#26](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/26): a community report for Linux and NVIDIA (documentation), by a contributor of this fork
- [#30](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/30): OpenSSF Scorecard workflow, Dependabot for the actions and a badge, by a contributor of this fork
- [#32](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/32): document the RX 9070 XT Vulkan community report, by @monsterlag

[#27](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/27) and
[#28](https://github.com/Rizzo-AI-Academy/rizzo-flow/pull/28) cover bugs that this fork has already fixed
(see Credits).

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

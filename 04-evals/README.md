# Chapter 4: Agent evals

Demos lie because sampling is random and agents close tasks confidently without finishing them. Measure whether it works every time (pass^k), and verify the end state (the file, the citations), not the transcript.

## Files

| file | what it shows |
|---|---|
| `tasks.jsonl` | Twenty topics in three buckets: typical, hard, regression. Some carry `must_mention` facts any correct brief has to contain. Replace these with your own; the set grows every time something breaks and never shrinks. |
| `smoke.jsonl` | The first five tasks, for the pull-request gate. |
| `graders.py` | Deterministic graders, each a function of the task and the run: `file_exists`, `min_sources`, `urls_resolve`, `quotes_grounded`, `facts_present`, `trajectory_ok`. `quotes_grounded` is the eight lines that catch hallucinated citations. `grounding_problems` is reused by the chapter 6 hook and the chapter 7 verifier. |
| `run.py` | The runner: every task, k attempts, per model, through `run_brief_traced`. A task passes at k only if all k attempts pass. Writes a dated report with pass^k, mean tool calls, p50 and p95 latency, and dollars per passing task. |
| `judge.py` | A judge for what code cannot decide. Binary questions, evidence not transcript, a different model family from the agent under test, and a calibration mode against hand labels. |
| `labels.example.jsonl` | The shape of the hand-label file: a run directory, your yes or no, and a one-line reason. |
| `tool_errors.py` | Tool-call unit checks: which tool fails argument validation, on which model, across every trace. |

## Run

From the repository root:

```bash
uv run --env-file .env python 04-evals/run.py --tasks 04-evals/smoke.jsonl --k 1
```

```bash
uv run --env-file .env python 04-evals/run.py --k 3 --models zai-org/GLM-5.3,deepseek-ai/DeepSeek-V4.1-Flash,qwen/Qwen3.8-27B
```

Reports land in `04-evals/results/<date>.md` with a `.json` sidecar. Runs land in `runs/evals/<task>/<model>/<attempt>/`.

The pull-request gate, as the workflow in `.github/workflows/eval.yml` runs it:

```bash
uv run --env-file .env python 04-evals/run.py --tasks 04-evals/smoke.jsonl --k 3 --max-usd 1.00 --baseline 04-evals/results/main.json
```

It exits non-zero when the per-run pass rate drops more than five points against the baseline. Commit the nightly run's JSON as `04-evals/results/main.json` to create the baseline.

The judge on one run, and calibration against your labels:

```bash
uv run --env-file .env python 04-evals/judge.py runs/evals/t01/zai-org_GLM-5.3/0
```

```bash
uv run --env-file .env python 04-evals/judge.py --calibrate 04-evals/labels.jsonl
```

Tool-call unit checks over every trace:

```bash
uv run python 04-evals/tool_errors.py "runs/**/trace.jsonl"
```

## Environment variables

| variable | required | purpose |
|---|---|---|
| `CRUSOE_API_KEY` | yes | runs and judging |
| `MODEL` | no | the model `run.py` evaluates when `--models` is not given |
| `JUDGE_MODEL` | no | defaults to `zai-org/GLM-5.3-Flash`; never the same family as the agent under test |
| `JUDGE_MIN_AGREEMENT` | no | threshold for `--calibrate`; defaults to 0.8 |
| `BRAVE_API_KEY` or `TAVILY_API_KEY` | one of them | the search API behind the MCP server |

## Notes

- Dollars per passing task reads prices from `03-agent/prices.toml`. Until that file is filled in the column is zero.
- `urls_resolve` falls back from HEAD to a ranged GET and caches each URL for the process, because a flaky grader is worse than none.
- The replay cache that lets the smoke eval run with no key is not part of this repository.

## Verified

- All six graders were exercised offline against a synthetic run: they pass on a grounded brief, and `grounding_problems` reports a source whose URL was never fetched. `urls_resolve` was skipped offline because it makes HTTP requests.
- `run.py`, `judge.py` and `tool_errors.py` import cleanly but were not run against the endpoint, because no API key was available in the build environment.

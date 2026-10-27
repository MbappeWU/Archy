# Issue 549

`archy_score` accepted any float for `strict_tolerance`. `archy score --strict-tolerance` already rejects a value outside [0, 1]. The MCP gate is `passed = delta >= -strict_tolerance`. Scores sit in [0, 1], so a delta sits in [-1, 1]. Tolerance 5.0 makes every drop pass, because -1 >= -5. A negative tolerance can fail a run whose score did not drop.

## Reproduction

The tree is a two-module package. One history row sets the previous overall to 0.99. The current overall on that tree is 0.6293916741966014, so the delta is -0.36060832580339863.

The CLI rejects the out-of-range values. Exit code 1 in both cases.

```
Error: --strict-tolerance must be in [0, 1]; got 5.0
Error: --strict-tolerance must be in [0, 1]; got -0.1
```

Tolerance 0.0 on the same drop exits 1. Tolerance 1.0 exits 0, and the gate reports `passed` true. Those two ends of the interval stay legal.

The MCP input schema for `strict_tolerance` is an unconstrained number. The default is 0.02. There is no minimum and no maximum.

`archy_score` with `strict` true, before the fix, returned these gates.

```
{"previous": 0.99, "previous_commit": "deadbee", "previous_timestamp": "2026-05-09T13:45:07Z", "current": 0.6293916741966014, "delta": -0.36060832580339863, "tolerance": 5.0, "passed": true}
{"previous": 0.99, "previous_commit": "deadbee", "previous_timestamp": "2026-05-09T13:45:07Z", "current": 0.6293916741966014, "delta": -0.36060832580339863, "tolerance": -0.1, "passed": false}
```

Tolerance 5.0 marked a real drop as passed. Tolerance -0.1 marked that same drop as failed. A separate call with previous 0.0 and tolerance -5.0 still returned `passed` false after the score rose by 0.6293916741966014, because no delta can reach 5.

## Fix

`archy score` calls `_require` with `0.0 <= strict_tolerance <= 1.0` before it scores. `archy_score` forwarded the float into `_run_score`, and `_run_score` used it in the gate with no check.

`_run_score` now raises `ValueError` when the value is outside [0, 1]. The message is `strict_tolerance must be in [0, 1]; got {strict_tolerance}`. The check runs even when `strict` is false, which is what the CLI does with the flag. FastMCP reports that `ValueError` as a tool error.

`view=history` does not call `_run_score`. That view still ignores `strict_tolerance`, including a value outside [0, 1]. The tool text already says the argument does not apply on that view. The gate this bug breaks runs only for `view=current`.

## Tests

`tests/test_mcp.py::test_archy_score_rejects_strict_tolerance_outside_unit_interval` calls `_run_score` and the `archy_score` tool. It expects the exact `ValueError` for 5.0 and -0.1, including when `strict` is false. It also calls the tool with 0.0 and 1.0 on the seeded drop. The delta has to satisfy `-1 < delta < 0` before the test accepts `passed` false at 0.0 and `passed` true at 1.0.

Before the check existed, the new test failed.

```
E   Failed: DID NOT RAISE <class 'ValueError'>
FAILED tests/test_mcp.py::test_archy_score_rejects_strict_tolerance_outside_unit_interval
1 failed in 0.75s
```

After the check, that test and the neighboring score tests passed.

```
.....                                                                    [100%]
5 passed in 0.70s
```

The command was `uv run pytest` on `test_archy_score_rejects_strict_tolerance_outside_unit_interval`, `test_run_score_payload_shape`, `test_run_score_strict_includes_gate_block`, `test_score_view_history_routes_to_trend`, and `test_error_model_tier2_raises_tier3_returns_in_band`.

Widening the check from `<= 1.0` to `<= 10.0` made the same test fail again, then the bound was put back.

```
E   Failed: DID NOT RAISE <class 'ValueError'>
FAILED tests/test_mcp.py::test_archy_score_rejects_strict_tolerance_outside_unit_interval
1 failed in 0.59s
```

`uv run ruff check` with no path argument passed. `uv run ruff format --check` passed for `src/archy/mcp.py` and `tests/test_mcp.py`.

After the fix, the same seeded project rejects the bad values and still gates the legal ones.

```
MCP view=current strict=True tol=5.0 RAISED ToolError: Error executing tool archy_score: strict_tolerance must be in [0, 1]; got 5.0
MCP view=current strict=True tol=-0.1 RAISED ToolError: Error executing tool archy_score: strict_tolerance must be in [0, 1]; got -0.1
MCP view=current strict=False tol=5.0 RAISED ToolError: Error executing tool archy_score: strict_tolerance must be in [0, 1]; got 5.0
MCP view=current strict=True tol=0.0 OK gate={"previous": 0.99, "previous_commit": "deadbee", "previous_timestamp": "2026-05-09T13:45:07Z", "current": 0.6293916741966014, "delta": -0.36060832580339863, "tolerance": 0.0, "passed": false}
MCP view=current strict=True tol=1.0 OK gate={"previous": 0.99, "previous_commit": "deadbee", "previous_timestamp": "2026-05-09T13:45:07Z", "current": 0.6293916741966014, "delta": -0.36060832580339863, "tolerance": 1.0, "passed": true}
DIRECT -5.0 strict_tolerance must be in [0, 1]; got -5.0
```

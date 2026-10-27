# Issue 552 evidence

MCP tools rejected a missing project path the way the CLI already does. A typo no longer becomes a directory, and it no longer scores 1.0.

## Repro

Command: in-process `create_server().call_tool("archy_score", {"path": "/tmp/archy-552-repro/no-such-project"})` before the fix. The directory did not exist before the call.

Result: the tool returned a score and created the cache.

```
TEXTS ['{\n  "overall": 1.0,\n  "components": {\n    "modularity": 1.0,\n    "acyclicity": 1.0,\n    "depth": 1.0,\n    "equality": 1.0,\n    "complexity": 1.0\n  }, ...
EXISTS True
DB_EXISTS True
CREATED /tmp/archy-552-repro/no-such-project/.archy
CREATED /tmp/archy-552-repro/no-such-project/.archy/index.db
```

`inputs.module_count` in that payload was 0.

The same missing path on the CLI:

```
uv run archy score /tmp/archy-552-repro/cli-missing-dir
Error: Invalid value for '[PATH]': Directory '/tmp/archy-552-repro/cli-missing-dir' does not exist.
cli_exit:2
```

A file path also scored 1.0 and left the file in place. `archy_score` on `/tmp/archy-552-repro/a-file` returned `overall: 1.0`. `still_file True`. `.archy` was not created under the file.

After the fix, the same kind of call:

```
ToolError
Error executing tool archy_score: Directory '/tmp/archy-552-repro/after-fix' does not exist.
EXISTS False
DB False
```

## Root cause

Each MCP tool takes `path: str` and passes `Path(path)` straight into the scan. Nothing checks that the path exists.

`IndexManager.__init__` calls `open_index`. `open_index` runs `db_path.parent.mkdir(parents=True, exist_ok=True)` where `db_path` is `<root>/.archy/index.db` (`src/archy/index.py`). `parents=True` creates the missing project directory and `.archy`. The scan then sees an empty tree. An empty graph scores 1.0.

The CLI never reaches that code. Its project argument is `click.Path(exists=True, file_okay=False)`.

A file is a second way to the same score. `mkdir` fails because the path is a file. `_warm_or_cold` treats that `OSError` as a cache failure and falls through to a cold `build_graph`, which also scores the empty graph as 1.0. Stopping the `mkdir` alone would not fix the score. The tool has to raise before either scan.

## Fix

`_project_dir` in `src/archy/mcp.py` is the shared guard. Every MCP tool entrypoint calls it on its project path before any scan.

An existing directory is returned. A file raises `ValueError` with `Directory '<path>' is a file.` Anything else raises `ValueError` with `Directory '<path>' does not exist.` FastMCP turns that into `ToolError`, which is the tier-2 `isError` channel already used for a bad argument value.

`open_index` is unchanged. An existing project that has no `.archy` directory yet still needs that `mkdir` to create the cache directory.

## Test commands and results

Failing tests, written before the guard existed:

```
uv run pytest tests/test_mcp.py -k "nonexistent_project_path or project_path_guard or file_as_the_project or existing_project_directory" -q --tb=line
```

```
15 failed, 2 passed, 129 deselected in 1.80s
```

Fourteen of the failures were `Failed: DID NOT RAISE <class 'mcp.server.fastmcp.exceptions.ToolError'>`. `archy_module_view` raised `ToolError` for a missing module named `pkg.a`, and the message did not contain `does not exist`. The two passes were the tool-map check and the existing-directory control (`module_count == 3`).

After the guard:

```
uv run ruff check
uv run ruff format --check
uv run pytest tests/test_mcp.py tests/test_mcp_protocol.py -q --tb=line
uv run archy conventions . --emit-headers --check
```

```
All checks passed!
155 files already formatted
153 passed, 1 skipped, 2 warnings in 7.66s
# 81 header(s) match the tree.
```

The warnings are the existing import-linter fallback in contract tests. They are not from this change.

## Mutate-to-fail check

Replaced the body of `_project_dir` with `return Path(path)`, deleted `src/archy/**/__pycache__`, and reran the new tests.

```
uv run pytest tests/test_mcp.py -k "nonexistent_project_path or file_as_the_project or existing_project_directory" -q --tb=line
```

```
15 failed, 1 passed, 130 deselected in 1.40s
```

The failures were again `DID NOT RAISE ToolError`, plus the `archy_module_view` message mismatch. The existing-directory control still passed, so the mutation was not inert. The guard was restored. A pycache clear and a full rerun of `tests/test_mcp.py` and `tests/test_mcp_protocol.py` then reported `153 passed, 1 skipped`.

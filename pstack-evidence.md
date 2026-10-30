# pstack-evidence — Archy #524

- **fix-root-causes**: malformed archy.yaml raised LayerConfigError past CLI; convert at `_graph_kwargs_or_exit` / `_load_graph`, leave `graph_kwargs` raising for MCP.
- **laziness**: one helper + catch in `_load_graph` (covers `resolve_max_modules`); no MCP/score/gate change.
- **test-behavior**: parametrized CLI test over 14 commands; check/contracts keep clean Error; mutation (passthrough helper) goes red.
- **prove-it-works**: focused 15 passed; mutation 14 failed; broader test_cli 194 passed; ruff clean.

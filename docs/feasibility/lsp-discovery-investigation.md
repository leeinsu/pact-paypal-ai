# LSP discovery investigation

Review date: 2026-10-22.
Target task: `pact-jpy-v2-20261022`.
Scope: cause analysis, minimal repair, and restart verification.
LSP means Language Server Protocol.
MCP means Model Context Protocol.
Code Mode executes tool calls through JavaScript.

## Conclusion

The evidence supports omitted tool discovery as the immediate failure mechanism.
The implementation agents reported unavailable LSP tools without attempting an MCP call.
The configured tools work through the actual adapter when Code Mode calls their registered names.
Historical runtime state remains unavailable, so this reproduction cannot prove every historical session condition.

## Evidence

The [evidence summary](evidence/lsp-discovery-20261022.json) records source hashes and successful calls.
The historical task logs remain unchanged.

| Observation | Evidence | Meaning |
| --- | --- | --- |
| Both implementation attempts contain zero MCP call events | `logs/implementation.1.jsonl` and `logs/implementation.2.jsonl` | Neither attempt tested LSP access |
| Attempt two executes `command -v lsp` | `logs/implementation.2.jsonl` | It checks a shell executable, not the configured MCP server |
| Initial tool definitions omit the LSP namespace | Captured request to the local endpoint | Direct visibility differs from runtime registration |
| `ALL_TOOLS` lists six permitted LSP tools | Captured Code Mode output | Deferred tools remain discoverable |
| Actual adapter calls succeed | `status`, `symbols`, and `diagnostics` | The tested transport and approval configuration work |
| Source diagnostics return zero findings | `No diagnostics found` | The tested source has no reported LSP diagnostics |

## Reproduction boundaries

The reproduction used `CodexAdapter.run` without changing framework source.
It used the configured coder model identifier `gpt-5.6-terra` and the `workspace-write` sandbox.
It reused the historical implementation output schema and isolated worktree.
It retained adapter hooks, environment filtering, and the six-tool approval configuration.
It substituted a local endpoint and temporary Codex configuration directory.
The endpoint supplied a deterministic tool call instead of a model-generated decision.
No paid model request occurred.
The endpoint returned HTTP 400 after capturing successful tool results.
The resulting exit code does not indicate an LSP failure.
The test proves tool execution, not autonomous model discovery or pipeline approval.

## Failure chain

1. `codex_adapter.py` registers six read-only MCP tools under server `lsp`.
2. Code Mode omits their direct definitions but retains their runtime registrations.
3. `language_policy.py` requires `lsp.status` without explaining Code Mode discovery or registered callable names.
4. The agents report tool unavailability without checking `ALL_TOOLS` or calling the MCP server.
5. `_context` includes the previous blocked report when the next attempt starts.
6. `_route_failure` retries the same stage after an environment failure.
7. `_attempt_allowed` stops execution after the configured failure limit.

The previous report supplies a repeated claim, not independent confirmation.
The logs cannot establish whether that report caused the second agent's decision.

## Contributing framework gaps

- The policy gives a conceptual tool name instead of an explicit discovery and call procedure.
- The environment failure report needs no recorded failed LSP call.
- `diagnose` checks initialization and tool listing rather than agent discovery and file operations.
- An environment retry repeats the stage without requiring new diagnostic evidence.

The tool description already explains `ALL_TOOLS` discovery.
The missing framework guidance therefore contributes to agent noncompliance rather than proving that discovery instructions were entirely absent.

## Minimum correction points

1. Explain `ALL_TOOLS` discovery and `tools.mcp__lsp__status({})` in the shared policy.
2. Require a discovery result or actual tool error before reporting unavailable LSP tools.
3. Add a regression check for the generated discovery instructions.
4. Add an offline adapter check that exercises deferred discovery and a file diagnostic.

The shared policy now includes discovery, status invocation, and evidence requirements.
Generated-role regression checks enforce these instructions.
The framework verification passed all 171 tests with zero failures or skips.
The coordinator repeated the offline actual-adapter check after the repair.
Status, symbols, and file diagnostics succeeded through deferred tools.
The endpoint remained local and deterministic.
No paid model or payment request occurred during that check.

An independent reviewer approved a fresh restart after these checks.
Task `pact-jpy-v3-20261022` obtains fresh approvals under the changed policy.
It preserves the historical V2 records and approved contract.
It requires independent reproduction and freezing of the approved JPY test before product changes.
V3 design, test coding, and implementation subsequently completed actual LSP calls.
The implementation agent discovered tools and completed status, symbols, references, and diagnostics successfully.
The implementation stage passed with 85 local tests.
This evidence demonstrates compliance in the new implementation session.
Both security review attempts later stopped because workspace credits were exhausted.
That interruption is separate from LSP access.
An independent reviewer recommended fresh task `pact-jpy-v4-20261022` after the user reported restored credits.
The fresh task preserves the source, approved contract, independent test digest, and normal approval stages.
V4 subsequently passed implementation, security review, and 85 shell tests.
The runtime rejected its logic result because two acceptance measures exceeded 25 words.
An independent reviewer confirmed this separate format failure through in-memory validation.
No historical result was changed.
The reviewer recommended fresh task `pact-jpy-v5-20261022` with mandatory complete candidate prevalidation.
V5 then exposed a coordinator instruction conflict with read-only role permissions.
The coordinator had required temporary candidate files.
The designer returned blocked because it could not write those files.
An independent reviewer recommended equivalent in-memory validation.
Task `pact-jpy-v6-20261022` applies that operational correction.
V6 completed all configured stages with unchanged framework validators and approval boundaries.
Its implementation completed actual status, symbols, diagnostics, and references calls.
Security review and logic verification passed.
UI review recorded the eight approved exclusions.
The coordinator delivered the three approved files and reran the project verification.
All 85 tests passed with zero failures, errors, or skips.
This local completion does not establish external payment permission or a gate pass.
Do not bypass required diagnostics or increase retry limits to conceal this failure.

## Language review

The review covered new prose, technical terms, quantities, and uncertainty.
Code identifiers retain their exact spelling.
No prose exception remains.
This review does not establish formal ASD-STE100 compliance.

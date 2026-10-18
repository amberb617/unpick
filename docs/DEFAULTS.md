# Defaults to change before you trust a tool

Verified 2026-10-18. Re-check against each project's README when you upgrade.

## NVIDIA SkillSpector (tested 2.12.0, git cf5cac7)

LLM analysis is on by default and sends skill content to the default provider (build.nvidia.com).
Turn it off on every run:

```
skillspector scan <skill-dir> --no-llm
```

Even with `--no-llm` it sends dependency names to OSV.dev when the skill has a manifest, and no flag
turns that off. Block it at the OS level (runthrough's `--boxed`, or any no-network sandbox); it then
falls back to its bundled advisory list.
Source: https://github.com/nvidia/skillspector @ cf5cac7 (static_patterns_supply_chain.py, osv_client.py).

## agentjail (tested 1.8.x)

Anonymous usage telemetry and a 6-hourly auto-update are on by default.

```
agentjail telemetry disable
export AGENTJAIL_AUTO_UPDATE=false
export AGENTJAIL_NO_UPDATE_CHECK=1
```

PowerShell:

```
agentjail telemetry disable
$env:AGENTJAIL_AUTO_UPDATE = 'false'
$env:AGENTJAIL_NO_UPDATE_CHECK = '1'
```

Telemetry can also be turned off with `AGENTJAIL_SEND_ANONYMOUS_USAGE_STATS=false`.
Source: https://github.com/LuD1161/agentjail (README, v1.8.x).

## Cisco mcp-scanner (tested 4.8.6)

The default analyzers are `api,yara,llm`; pass `--analyzers yara` to stay local. Set
`LITELLM_LOCAL_MODEL_COST_MAP=True` so its litellm dependency does not fetch a cost map from GitHub on import.
Source: https://github.com/cisco-ai-defense/mcp-scanner (4.8.6).

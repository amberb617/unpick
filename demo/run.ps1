# Reproduces slides 18, 19 and B2 of "The Devil Wears Markdown". Makes no network calls.
# Works in PowerShell 7 and Windows PowerShell 5.1.
# Set $env:RT_BACKENDS = 'installed' to add every installed offline scanner.
$ErrorActionPreference = 'Continue'
Set-Location -Path $PSScriptRoot
$B = @()
if ($env:RT_BACKENDS) { $B = @('--backends', $env:RT_BACKENDS) }
function Pause-Demo { [void](Read-Host "`n[enter]") }

Write-Host "== Slide 18: sample A. Rendered, it looks clean. Raw, it does not. =="
unpick raw sample-a/SKILL.md
Pause-Demo
unpick scan sample-a --no-decisions @B
Pause-Demo

Write-Host "== Slide 19: sample B. A flag is a question, not a verdict. =="
unpick scan sample-b --no-decisions @B
Pause-Demo
unpick decide --rule RT-SENSITIVE-PATH --file SKILL.md accept --note "benign: the skill warns against committing secrets" --decisions-file .unpick/demo-decisions.json
unpick scan sample-b --decisions .unpick/demo-decisions.json @B
Pause-Demo

Write-Host "== Slide B2: a poisoned MCP tool description, read without starting any server =="
unpick scan tools.json --no-decisions @B

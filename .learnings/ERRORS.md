# Errors

Command failures and integration errors.

---

## [ERR-20260525-001] command

**Logged**: 2026-05-25T03:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: automation

### Summary
Skill validation initially used `python`, but this WSL environment only exposed `python3`.

### Recovery
Reran `automation_file_probe.py` and `quick_validate.py` with `python3`; both passed.

### Prevention
Use `python3` in OpenClaw workspace validation and helper commands unless a project explicitly defines `python`.

## 2026-05-24 - P5.9 poster AI copy timeout

- Context: Telegram `做海报` request for a travel/person beach portrait.
- Failure: `tools/make_poster.py --ai-copy --auto-color` failed because `ollama run qwen3.5:9b` timed out after 60 seconds inside `tools/local_ai_copy.py`.
- Impact: First poster run aborted before rendering variants.
- Recovery: Re-ran P5.9 without `--ai-copy`, kept `--auto-color`, and generated the poster successfully.
- Follow-up: Consider increasing AI-copy timeout, pre-warming Ollama, or making AI-copy timeout fall back inside `local_poster_premium.py` instead of aborting the whole poster pipeline.

---

## 2026-05-24 - Poster quality gate argument mismatch

- Context: Quality-checking a manually rendered `v3` recovery journey poster.
- Failure: Used old flags `--output-md` and `--output-json`; current `tools/poster_quality_gate.py` expects `--md-output` and `--json-output`.
- Recovery: Re-ran with the current flags and generated both quality reports successfully.
- Follow-up: Normalize output flag names across poster tools or add backward-compatible aliases.

---

## 2026-05-24 - WSL PowerShell quoting and reserved variable issues

- Context: Building a WSL-to-Windows UI automation bridge for Doubao.
- Failure 1: Bash expanded PowerShell `$_` inside a double-quoted command, producing `/bin/bash.ProcessName` errors.
- Recovery 1: Wrap PowerShell commands in single quotes or escape `$`.
- Failure 2: PowerShell script used `$pid`, which conflicts with read-only built-in `$PID`.
- Recovery 2: Renamed script variable to `$processId`.
- Follow-up: Keep WSL-to-PowerShell examples in `tools/windows_ui/README.md` using `-Command "& '<UNC script>' ..."` and avoid reserved variable names.

---

## 2026-05-24 - Doubao video generation service overloaded

- Context: Automated Doubao desktop app through Windows UI bridge: switched to video generation, uploaded poster, pasted prompt, and clicked send.
- Result: Doubao returned `服务过载，请稍后重试` and `视频生成失败，生成额度未扣除`.
- Impact: Automation chain worked, but cloud-side generation failed.
- Recovery: Keep the prepared input image, prompt, screenshots, and bridge scripts for a later retry.

---

## [ERR-20260525-001] missing-local-jq

**Logged**: 2026-05-25T03:14:00+08:00
**Priority**: low
**Context**: While checking n8n workflow export, local `jq` was unavailable (`command not found`).
**Resolution**: Used Python JSON parsing instead; avoid assuming `jq` is installed in this WSL workspace.


## [ERR-20260525-002] n8n-check-triggered-webhook

**Logged**: 2026-05-25T03:14:00+08:00
**Priority**: medium
**Context**: During a read-only check of n8n workflow `PDF → PPTX Converter`, a POST smoke test was executed after saying the workflow would not be run without confirmation.
**Impact**: The workflow only returned a placeholder JSON response and did not perform conversion or file writes, but this violated the stated read-only boundary.
**Resolution**: Reported the smoke-test result explicitly; for future n8n checks, separate metadata/log inspection from execution tests and ask before calling webhook endpoints.

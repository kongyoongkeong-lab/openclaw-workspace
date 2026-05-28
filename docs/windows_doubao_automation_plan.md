# Windows Doubao Automation Plan

Date: 2026-05-24
Scope: Build a safe bridge from OpenClaw running in WSL2 to Windows desktop apps, starting with Doubao video generation.

## Goal

Control the installed Windows Doubao app enough to:

1. Launch or focus Doubao.
2. Upload a prepared poster image.
3. Paste a video-generation prompt.
4. Start generation.
5. Detect completion.
6. Retrieve or locate the generated video.

## GitHub Research Summary

Best candidates found:

| Project | Role | Notes |
|---|---|---|
| `microsoft/winappCli` | CLI-first Windows UI Automation | Most aligned with agent workflows. Uses Windows UI Automation and exposes inspect/search/click/type style commands. Best target if install succeeds. |
| `pywinauto/pywinauto` | Mature Python Windows GUI automation | Mature, widely used, supports Win32 and UIA backends. Good fallback and scripting base. |
| `yinkaisheng/Python-UIAutomation-for-Windows` | Direct Python wrapper for Microsoft UIAutomation | Useful for UIA tree inspection and lower-level control. |
| `Touchpoint-Labs/touchpoint` | Agent-oriented desktop accessibility/MCP | Promising but newer; useful later if MCP integration is preferred. |
| `CursorTouch/Windows-Use` | LLM agent for Windows UI | Interesting reference, but too broad for a deterministic Doubao workflow. |
| `sandraschi/pywinauto-mcp` | MCP around pywinauto | Useful reference for exposing Windows UI tools to agents. Review security before adopting. |
| `AirtestProject/Airtest` | Image-recognition UI automation | Good fallback when accessibility tree is poor, but less deterministic than UIA. |

Recommendation:

1. Primary: `microsoft/winappCli` if available through `winget` or source install.
2. Fallback: Python bridge using `pywinauto` + screenshots/OCR.
3. Last resort: image-based clicks via `pyautogui`/Airtest-style matching.

## Local Findings

- Doubao is installed:
  - `C:\Users\jason\AppData\Local\Doubao\Application\Doubao.exe`
  - `C:\Users\jason\AppData\Local\Doubao\Application\app\Doubao.exe`
- Desktop shortcut exists:
  - `C:\Users\jason\OneDrive\Desktop\Doubao.lnk`
- WSL can see Windows files under `/mnt/c`.
- PowerShell is callable from WSL:
  - `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`
- Windows Python exists:
  - `C:\Program Files\Python314\python.exe`

## WSL-To-PowerShell Command Rule

When invoking PowerShell from bash, wrap the entire PowerShell command in single quotes or escape `$`.

Bad:

```bash
powershell.exe -Command "Get-Process | Where-Object { $_.ProcessName -match 'Doubao' }"
```

Good:

```bash
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command 'Get-Process | Where-Object { $_.ProcessName -match "Doubao" }'
```

Reason: bash expands `$_` before PowerShell receives it.

## Bridge Architecture

```text
OpenClaw / WSL2
  |
  | runs PowerShell / Windows Python
  v
Windows UI Bridge
  |
  | UIA / pywinauto / fallback screenshot clicks
  v
Doubao desktop app
```

The bridge must expose small deterministic commands:

- `probe`: check Python, packages, Doubao path, running process.
- `launch`: start Doubao.
- `inspect`: print visible Doubao windows and UIA control tree.
- `focus`: activate target window.
- `paste_prompt`: copy prompt to clipboard and paste.
- `upload_file`: interact with file picker.
- `generate`: click generation button.
- `wait_download`: wait for output video or download completion.

## Safety Gates

- Do not click or type until the target window title/process is positively identified.
- Keep generated prompts and media paths in workspace files, not secrets.
- Do not enter credentials or bypass login flows.
- Do not run broad automation across unrelated windows.
- Save screenshots/logs under `reports/windows_ui/`.

## Next Implementation Step

Use `tools/windows_ui/doubao_bridge.py`:

1. Run `probe` from WSL through Windows Python.
2. If required packages are missing, create a workspace-scoped Windows venv or ask before installing.
3. Run `launch`.
4. Run `inspect` after Jason confirms Doubao is logged in and visible.
5. Convert observed UIA element names into a deterministic `generate-video` flow.


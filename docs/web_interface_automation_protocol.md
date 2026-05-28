# Web Interface Automation Protocol

Date: 2026-05-24
Owner: OpenClaw @main

## Verdict

Use browser web interfaces through a structured state machine, not one-shot DOM injection or coordinate clicking.

Default stack:

```text
OpenClaw -> automation_router.py -> Windows Node Playwright -> Chrome CDP -> live web UI
```

Fallback stack:

```text
Playwright locators -> CDP low-level events -> agent-browser snapshot refs -> Midscene/OCR -> manual checkpoint
```

## Current Runtime Evidence

- `tools/automation_router.py status` confirms Windows PowerShell, Python, AutoHotkey v2, FlaUInspect, and Chrome CDP are available.
- Chrome CDP is live at `http://127.0.0.1:9222`.
- Active browser: `Chrome/148.0.7778.179`.
- Active profile: `C:\OpenClawChrome`.
- `tools/automation_router.py browser-smoke` confirms Windows Node + Playwright can attach to the live CDP context and list active pages.

## GitHub-Backed Source Findings

- Chrome DevTools MCP recommends connecting to a running Chrome with `--browser-url=http://127.0.0.1:9222`, warns the remote debugging port gives local apps browser control, and documents that Chrome requires a non-default `--user-data-dir` for remote debugging.
- Chrome DevTools MCP troubleshooting documents WSL/VM host debugging failures and recommends mirrored networking, Windows-side Chrome startup, or PowerShell/Git Bash as practical workarounds.
- Microsoft Playwright MCP documents persistent profiles and `--user-data-dir` for storing logged-in state.
- Microsoft Playwright emphasizes auto-waiting, resilient locators, web-first assertions, traces, and DOM snapshots rather than artificial sleeps.
- Vercel `agent-browser` documents snapshot refs as the recommended AI workflow: snapshot, choose deterministic refs, act, then snapshot again.
- Browser Use exposes the same core web-agent primitives: click, input, upload_file, send_keys, and evaluate for advanced interactions.

Sources:

- https://github.com/ChromeDevTools/chrome-devtools-mcp
- https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/troubleshooting.md
- https://github.com/microsoft/playwright-mcp/blob/main/README.md
- https://github.com/microsoft/playwright
- https://github.com/vercel-labs/agent-browser
- https://github.com/browser-use/browser-use/blob/main/AGENTS.md

## Required State Machine

Every login-required web-interface task must run through these states and record the observed transition.

| State | Required Evidence | Failure Handling |
|---|---|---|
| `cdp_ready` | `/json/version` responds or Playwright `connectOverCDP` succeeds | Run `python3 tools/automation_router.py cdp-status`; do not relaunch Chrome unless requested |
| `target_page_ready` | Correct domain, title, and URL; duplicate tabs identified | Reuse matching page; avoid opening duplicate tabs |
| `login_ready` | Account/session UI visible; no login/captcha/region blocker | Stop and ask for manual login/captcha/network action |
| `mode_ready` | Correct tool mode selected, for example Doubao video page | Navigate or click using locator/ref; snapshot after mode change |
| `asset_uploaded` | File chip/thumbnail appears and network upload/preflight succeeded | Retry upload once through `setInputFiles`; then checkpoint |
| `prompt_committed` | UI-visible prompt text equals intended prompt; React/Vue state sees it | Use Playwright `locator.fill()` or keyboard input; avoid raw `innerText` mutation |
| `submit_armed` | Send/generate button is enabled and attached to correct form | Wait for enabled state; verify button bounding box and form ownership |
| `submitted` | URL, UI status, network response, disabled button, or task ID changed after click | If unchanged, do not claim submitted; escalate to CDP event or manual checkpoint |
| `generating` | Visible generation/progress state or streaming/network task observed | Poll boundedly with screenshots and network logs |
| `artifact_ready` | `<video>`, blob/media URL, download link, or completed card detected | Extract URL/file via Playwright download listener or page evaluation |
| `delivered` | File copied to `/mnt/d/_outbox` and probed for duration/codec/size | Report artifact path and verification |

## SPA Input Rules

For React/Vue/Svelte web apps, do not set `innerText` or `value` as the primary input method. It can update the DOM while leaving framework state unchanged.

Preferred order:

1. Use Playwright semantic locators: `getByRole`, `getByLabel`, `getByPlaceholder`, or stable text.
2. Use `locator.fill()` for real text fields and `locator.pressSequentially()` for contenteditable editors that reject fill.
3. Use clipboard paste only when the editor handles paste reliably and the clipboard operation is scoped.
4. Use low-level CDP `Input.dispatchKeyEvent` or Playwright keyboard only when normal locators fail.
5. Use raw `Runtime.evaluate` only for inspection or as an explicitly marked advanced fallback.

After input, verify:

- visible editor text exactly matches the prompt,
- generated hidden textarea/model-backed value changed if present,
- send button enablement changed,
- no validation message is visible.

## Submit Rules

Button click is not success. Success requires post-click evidence.

Preferred order:

1. `await Promise.all([waitForResponseOrUrlOrDomChange, locator.click()])`.
2. If the app uses WebSocket/SSE, attach listeners before clicking.
3. Require at least one of:
   - URL route changes to a task/conversation ID,
   - visible generation/progress text appears,
   - task ID appears in network response,
   - media placeholder/progress card appears,
   - send button state changes from armed to busy.
4. If no evidence appears within the timeout, mark state `submit_unconfirmed`.

## Doubao-Specific Protocol

Doubao video generation must use a dedicated flow file, not ad hoc CDP snippets.

Required steps:

1. Attach to existing `C:\OpenClawChrome` CDP session through Windows Node.
2. Reuse an existing `doubao.com` page if present; otherwise open exactly one page.
3. Navigate to `https://www.doubao.com/chat/create-video` or the current working video route.
4. Check for blockers:
   - region ban,
   - login page,
   - overload/generation failed state,
   - captcha/security challenge.
5. Upload the image with Playwright `setInputFiles`.
6. Wait for the uploaded file chip/thumbnail and any upload/pre-generate network response.
7. Enter prompt with Playwright locator/keyboard methods.
8. Verify prompt and enabled send/generate button.
9. Click through Playwright and wait for route/status/network transition.
10. If Doubao returns `pre_generate_id` but no generation card, record it as preflight only, not submitted.
11. Monitor for a bounded period; extract `<video>`, blob URLs, or download links.
12. Save to `/mnt/d/_outbox` and verify with `ffprobe` or OpenCV metadata.

## Safety Rules

- Keep CDP bound to localhost.
- Treat the CDP browser as a logged-in sensitive session.
- Do not dump cookies, localStorage, auth headers, or full network payloads.
- Do not browse unrelated sensitive websites while CDP is open.
- Use domain allowlists for automated actions.
- Prefer read-only status checks unless the user explicitly requests submission.
- Use manual checkpoints for captcha, payment, account/security challenges, irreversible submissions, or ambiguous final-send buttons.

## Implementation Requirements

Add or refactor browser job scripts so they expose these commands:

```text
probe       -> report CDP/page/login/mode state
prepare     -> open/reuse target page and verify mode
upload      -> upload asset and confirm UI evidence
fill        -> enter prompt and verify framework state
submit      -> click and require post-click transition evidence
monitor     -> wait for progress/artifact with bounded polling
extract     -> copy media artifact to /mnt/d/_outbox and verify
```

Each command should emit compact JSON:

```json
{
  "state": "prompt_committed",
  "ok": true,
  "url": "https://www.doubao.com/...",
  "evidence": ["prompt_visible", "send_enabled"],
  "next": "submit"
}
```

## Protocol Upgrade Summary

The previous protocol correctly chose Chrome + CDP + persistent profile. The missing piece was operational confirmation: SPA input and submit actions need observable state transitions. Future web-interface work must prove every transition before advancing.

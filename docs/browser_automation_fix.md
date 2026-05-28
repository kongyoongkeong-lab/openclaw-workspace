# Browser Automation from WSL — Root Cause & Fix

## 为什么指令发不到 Gemini 输入框？

**根本原因不是浏览器本身，而是控制方式。**

从 WSL 调用 `SendKeys` 发键盘指令到 Chrome 窗口，键盘事件经过：
```
WSL → PowerShell/WScript → Win32 SendInput/SendKeys → Windows 消息队列 → Chrome Aura 窗口管理器
```
而 Chrome 的 React SPA 输入框（如 Gemini 的聊天输入）是通过 `ContentEditable` 或 `Rich Text` div 渲染的，**不是原生 Windows Edit 控件**，所以：
- `SendKeys` 的 TAB 导航无法精确到达 React 树的深层节点
- `SetForegroundWindow` 被 Chrome Aura 拦截（`LockSetForegroundWindow`）
- 键盘消息可能进了地址栏、侧边栏或搜索框，而不是 Gemini 的输入区

## 最佳浏览器选择

| 浏览器 | CDP 支持 | WSL 兼容 | 推荐度 | 理由 |
|--------|---------|---------|-------|------|
| **Chrome** | ✅ 完整 | ✅ | ⭐⭐⭐⭐⭐ | 行业标准 CDP，用户已登录 Gemini Pro |
| **Brave** | ✅ 完整 | ✅ | ⭐⭐⭐⭐ | 用户已安装，Chromium 同源，防自动化较低 |
| **Edge** | ✅ 完整 | ✅ | ⭐⭐⭐⭐ | 微软官方 CDP 文档丰富 |
| **Firefox** | ⚠️ Marionette | ⚠️ | ⭐⭐⭐ | 不同协议，工具链少 |

**结论：Chrome 是最佳选择**，但需要换控制方式，而不是浏览器。

## 真正的修复方案：Chrome DevTools Protocol (CDP)

**核心思路：** 不用模拟键盘鼠标，直接用 WebSocket 协议控制 Chrome 内部。

### 步骤

**1. 用固定 automation profile + remote debugging port 启动 Chrome：**
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="C:\OpenClawChrome" \
  --new-window "https://gemini.google.com/app"
```

认证类自动化必须复用同一个 profile：`C:\OpenClawChrome`。登录状态、cookies、localStorage 都保存在这里；换 profile 就等于换浏览器身份。

**2. 从 WSL Python 连接：**
```python
import websockets, json
async with websockets.connect("ws://host.docker.internal:9222/devtools/browser") as ws:
    # 获取所有页面
    await ws.send(json.dumps({"id":1,"method":"Target.getTargets"}))
    resp = await ws.recv()
    # 发送 JS 到 Gemini 页面
    await ws.send(json.dumps({
        "id":2,"method":"Runtime.evaluate",
        "params": {
            "expression": """
                document.querySelector('[contenteditable="true"]').focus();
                document.execCommand('insertText', false, '你的提示词');
            """
        }
    }))
```

**3. 文件上传也可通过 CDP 的 `DOM.setFileInputFiles` 实现：**
```python
await ws.send(json.dumps({
    "id":3,"method":"DOM.setFileInputFiles",
    "params": {"files": ["C:\\poster.png"]}
}))
```

### 优势
- ✅ **无需窗口焦点** — Chrome 可以最小化/后台运行
- ✅ **精确控制** — 直接操作 DOM，而非模拟键盘
- ✅ **文件上传** — 原生支持
- ✅ **下载监听** — 可自动捕获下载的视频文件

### 从 WSL 使用 CDP 的两个方式

| 方式 | 说明 | 复杂度 |
|-----|------|-------|
| **`pychrome` 库** | Python CDP 客户端，轻量级 | 低 |
| **原始 `websockets` + CDP 协议** | 无依赖，纯 Python | 中 |
| **`playwright` `connect_over_cdp`** | 封装完整，功能最强 | 低（需安装） |

## 总结

**浏览器不变，换控制方式即可。**  
Chrome + CDP = 从 WSL 全自动控制 Gemini/Doubao 网页的可靠方案。  
不需要切换浏览器。

## Official OpenClaw Chrome Automation Login Protocol

Use the dedicated persistent Windows profile:

```text
C:\OpenClawChrome
```

Windows launcher:

```powershell
C:\OpenClawChrome\start-openclaw-chrome.ps1
```

Shortcut launcher:

```cmd
C:\OpenClawChrome\start-openclaw-chrome.cmd
```

Workspace bootstrap script:

```powershell
\home\jason2ykk\.openclaw\workspace\tools\chrome_cdp_bootstrap.ps1
```

Rules:

- Log in once inside `C:\OpenClawChrome`; future sessions must reuse that exact path.
- Do not use temporary `--user-data-dir` paths for login-dependent workflows.
- Do not use Jason's everyday Chrome profile for CDP automation.
- Only one Chrome process should own `C:\OpenClawChrome` at a time.
- Keep CDP bound to `127.0.0.1:9222`; use explicit port forwarding only when WSL access requires it.

## 2026-05-24 Protocol Upgrade: State-Machine Web Automation

The Chrome/CDP profile decision is correct, but complex web apps such as Doubao, Gemini, ChatGPT, and other React/Vue SPAs need a stricter operating loop.

New rule: a click, DOM mutation, or network preflight is not enough. Every step must produce a visible or network-backed state transition before the agent advances.

Required flow:

1. Verify CDP is live and attached through Windows Node/Playwright.
2. Reuse the correct existing tab; avoid duplicate logged-in tabs unless isolation is needed.
3. Verify domain, login state, and tool mode.
4. Upload files with Playwright `setInputFiles` or CDP `DOM.setFileInputFiles`, then confirm the file chip/thumbnail appears.
5. Enter text through Playwright locators/keyboard methods before falling back to raw `Runtime.evaluate`.
6. Confirm SPA state: visible prompt text, enabled send/generate button, and no validation blocker.
7. Submit with a paired wait for URL, DOM, network, WebSocket/SSE, or task-status transition.
8. Treat `pre_generate_id` or upload success as preflight only unless the generation card/progress state appears.
9. Extract final artifacts only after `<video>`, blob/media URL, download link, or completed card is visible.

Detailed protocol: `docs/web_interface_automation_protocol.md`.

@echo off
chcp 65001 >nul
title [Pentagon] OpenClaw Master Architect — Cloud-Native Mode

:: --- INITIALIZATION ---
echo ⚡ (SYSTEM) 正在初始化 Pentagon Stack 监控体系...
set LOG_FILE_WIN=pentagon_boot_debug.log
echo [%DATE% %TIME%] --- NEW RESTART SEQUENCE --- >> %LOG_FILE_WIN%

:: --- PHASE 1: PRE-FLIGHT CHECK (@sentinel) ---
echo 📊 [SENTINEL] 正在检测 WSL 通道与网络状态...
wsl echo "WSL OK" >nul 2>&1
if %errorlevel% neq 0 (
 echo ❌ 错误: WSL2 未响应。请确保 WSL 正在运行。
 pause
 exit
)
echo ✅ WSL 通道正常
wsl bash -c "curl -s -o /dev/null -w '%%{http_code}' http://127.0.0.1:8188 > /dev/null 2>&1" && echo ✅ ComfyUI 服务在线 || echo ⚠️ ComfyUI 未运行（如需运行请执行 pentagon_comfy_start.bat）

:: --- PHASE 2: SERVICE RESTART (@ops) ---
echo 🚀 [OPS] 正在重启 OpenClaw Gateway 服务...
wsl bash -c "systemctl --user restart openclaw-gateway.service"

:: --- PHASE 3: DUAL-WINDOW TELEMETRY ---
echo 🔍 [MONITOR] 正在启动实时遥测与日志追踪...

:: Window A: Cloud-Native Health Dashboard
:: Checks cloud provider status, disk usage, and system health
start "Pentagon: System Health (df + journalctl)" wsl bash -c "watch -n 5 'echo \"=== DISK ===\" && df -h / | tail -1 && echo \"\" && echo \"=== SERVICES ===\" && systemctl --user is-active openclaw-gateway.service 2>/dev/null && echo \"ComfyUI: $(curl -s -o /dev/null -w '%%{http_code}' http://127.0.0.1:8188 2>/dev/null || echo 'off')\" && echo \"\" && echo \"=== TOP CPU ===\" && ps aux --sort=-%cpu | head -5'"

:: Window B: Service Logs with Troubleshooting Persistence
:: Captures logs for @sentinel analysis
start "Pentagon: Gateway Logs" wsl bash -c "mkdir -p ~/openclaw_logs && journalctl --user -u openclaw-gateway.service -f | tee -a ~/openclaw_logs/gateway_troubleshoot.log"

:: --- POST-INSTALLATION ---
echo.
echo ✅ Pentagon 系统监控已分窗启动:
echo 1. SYSTEM HEALTH: 磁盘 + 服务状态 (每 5 秒刷新)
echo 2. JOURNALCTL: 追踪 OpenClaw 运行日志
echo ✅ 纯云原生模式 — 无 GPU/本地推理依赖
echo.
echo [%DATE% %TIME%] MONITORING_ACTIVE >> %LOG_FILE_WIN%

pause

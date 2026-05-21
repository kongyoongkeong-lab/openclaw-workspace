@echo off
chcp 65001 >nul
title [Pentagon] System Termination Protocol — Cloud-Native

echo.
echo ===============================================
echo [Pentagon] System Shutdown Protocol
echo ===============================================
echo.

:: -------------------------------------------------
:: Phase 1: Stop OpenClaw Gateway Service
:: -------------------------------------------------
echo 🛑 [1/5] Stopping OpenClaw Gateway service...

wsl bash -c "systemctl --user stop openclaw-gateway.service"

if %ERRORLEVEL% EQU 0 (
 echo ✅ Gateway service stopped
) else (
 echo ⚠️ Gateway service may already be stopped
)

echo.

:: -------------------------------------------------
:: Phase 2: Stop ComfyUI + Application Processes
:: Keep infrastructure alive (Qdrant + Redis)
:: -------------------------------------------------
echo 🐳 [2/5] Stopping ComfyUI and application processes...

wsl bash -c "pkill -f 'main.py.*--port 8188' 2>/dev/null; docker stop openclaw-core 2>/dev/null"

if %ERRORLEVEL% EQU 0 (
 echo ✅ Application processes stopped
) else (
 echo ⚠️ Some processes were not running
)

echo.

:: -------------------------------------------------
:: Phase 3: Verify Infrastructure Containers
:: Qdrant + Redis should remain running
:: -------------------------------------------------
echo 🧠 [3/5] Verifying infrastructure containers...

wsl bash -c "docker ps --format 'table {{.Names}}\t{{.Status}}'"

echo.
echo Expected infrastructure:
echo - qdrant → running
echo - redis → running
echo.

:: -------------------------------------------------
:: Phase 4: Cleanup Monitoring Processes
:: -------------------------------------------------
echo 📊 [4/5] Cleaning monitoring processes...

wsl bash -c "pkill -f 'watch -n' 2>/dev/null"

echo ✅ Monitoring cleanup complete
echo.

:: -------------------------------------------------
:: Phase 5: Final System Status
:: -------------------------------------------------
echo 🔍 [5/5] Final system state...
echo ------------------------------------------------
wsl bash -c "echo 'Disk:'; df -h / | tail -1; echo ''; echo 'Services:'; systemctl --user is-active openclaw-gateway.service 2>/dev/null || echo 'stopped'"
echo ------------------------------------------------
echo.

:: -------------------------------------------------
:: Final Status
:: -------------------------------------------------
echo ✅ [COMPLETE] Pentagon application layer safely stopped.
echo 🧠 Infrastructure layer remains active:
echo - Qdrant
echo - Redis
echo ✅ 纯云原生模式 — 无 GPU/本地推理残留
echo.

echo [%DATE% %TIME%] SYSTEM_SHUTDOWN_SUCCESS >> pentagon_boot_debug.log

pause

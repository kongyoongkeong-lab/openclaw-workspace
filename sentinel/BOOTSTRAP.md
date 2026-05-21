# Bootstrap: @sentinel
**Sequence:** 00 (Kernel-Level)

## Boot Directives
- Load security regex patterns for shell command vetting.
- Load git secret scan patterns: `ghp_`, `gho_`, `sk-`, `comfyui-`, `api_key`.
- Establish the **Heartbeat Monitor** for all Pentagon nodes.
- Verify `.github/workflows/secret-scan.yml` is up-to-date.
- Check GitHub Actions secret scanner workflow is active.

## Environment
- Set `SECURITY_LEVEL=strict`
- Set `HAL_CHECK=enabled` (Hallucination Detection)
- Set `GIT_SECRET_SCAN=enabled`
- Set `CREDENTIAL_PATTERNS=ghp_,gho_,ghu_,sk-,comfyui-,api_key,token,secret`

## Security Patterns
```regex
# GitHub tokens
ghp_[a-zA-Z0-9]{36}       # Classic PAT
gho_[a-zA-Z0-9]{36}       # OAuth token
ghu_[a-zA-Z0-9]{36}       # User token
ghs_[a-zA-Z0-9]{36}       # Server token
ghr_[a-zA-Z0-9]{36}       # Runner token

# API keys
comfyui-[a-f0-9]{64}      # ComfyOrg API Key
sk-[a-zA-Z0-9]{20,}       # OpenAI key

# Credentials
api_key\s*=\s*['"][a-zA-Z0-9_]+['"]
password\s*=\s*['"][^'"]+['"]
```
# Hugging Face Setup

Purpose: enable safe Hugging Face model discovery, public model checks, and gated/private model downloads without leaking token material.

## Current State

- `hf` CLI is installed at `/home/jason2ykk/.local/bin/hf`.
- `huggingface-cli` is installed.
- `huggingface_hub` is installed.
- Hugging Face token is configured in the standard Hugging Face cache.
- Account auth is verified for `jason2ykk`.
- Public model metadata checks work.
- Gated/private model checks require accepting each model license on Hugging Face first.

## Token Setup

Create a token at:

`https://huggingface.co/settings/tokens`

Recommended scope:

- Fine-grained token if possible.
- Read-only access.
- Add gated model access only after accepting the model license on Hugging Face.

Storage options:

1. Preferred for OpenClaw workflows:

```bash
printf '%s\n' 'HF_TOKEN=<token>' >> ~/.openclaw/.env
```

2. Standard Hugging Face CLI login:

```bash
hf auth login
```

Never paste the token into reports, logs, Markdown files, or chat responses intended for storage.

## Preflight

List local readiness without network account probing:

```bash
python3 tools/huggingface_preflight.py --list-only
```

Validate account token without printing token material:

```bash
python3 tools/huggingface_preflight.py --whoami
```

Check public model metadata:

```bash
python3 tools/huggingface_preflight.py --model Qwen/Qwen2.5-0.5B-Instruct
```

Check a gated model after accepting its license:

```bash
python3 tools/huggingface_preflight.py --model <org/model-id> --whoami
```

## Download Helper

Use the safe download planner before pulling model files:

```bash
python3 tools/huggingface_download.py Qwen/Qwen2.5-0.5B-Instruct
```

The planner checks:

- token discovery without printing token material
- Hugging Face model metadata/access
- known model file size
- target directory state
- free disk capacity with a default 10 GiB reserve

Start the actual download only after the plan looks correct:

```bash
python3 tools/huggingface_download.py Qwen/Qwen2.5-0.5B-Instruct --yes
```

Default target:

```text
/mnt/d/models/huggingface/<safe-model-name>/
```

Use an exact target directory when needed:

```bash
python3 tools/huggingface_download.py <org/model-id> \
  --local-dir /mnt/d/models/huggingface/<model-name> \
  --yes
```

If the target directory already exists, the helper blocks by default. To resume/update an existing directory:

```bash
python3 tools/huggingface_download.py <org/model-id> --force --yes
```

After a successful download, the helper writes:

```text
openclaw_hf_download_manifest.json
```

The manifest records model ID, target directory, known size, file count, revision SHA, and token source metadata. It never stores token material.

## Output Policy

The preflight script may print:

- CLI paths
- `huggingface_hub` version
- discovered token label/source
- account username from Hugging Face auth probing
- model access status

The preflight script must not print:

- token values
- bearer headers
- full environment dumps
- cache file contents

## Troubleshooting

If token is missing:

```bash
python3 tools/huggingface_preflight.py --list-only
```

Expected result: token row shows `missing`.

If a model reports `requires_token_or_access_approval`:

- Confirm token exists.
- Confirm `python3 tools/huggingface_preflight.py --whoami` succeeds.
- Open the model page in a browser.
- Accept the license/gated access terms.
- Retry the preflight.

CLI note:

- Newer `hf` CLI versions use `hf auth whoami`.
- Older `huggingface-cli` versions use `huggingface-cli whoami`.
- `tools/huggingface_preflight.py --whoami` handles both forms and falls back to `huggingface_hub.HfApi().whoami()`.

If a model reports `model_not_found_or_private`:

- Check spelling and casing of `<org/model-id>`.
- Confirm the account has access.

## Related Files

- `tools/huggingface_preflight.py`
- `tools/huggingface_download.py`
- `memory/system/capability_map.md`
- `shortcuts.md`

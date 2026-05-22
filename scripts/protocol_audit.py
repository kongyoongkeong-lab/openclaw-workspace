#!/usr/bin/env python3
"""Lightweight protocol consistency audit for OpenClaw workspace."""
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
FAIL = []
WARN = []

ACTIVE_FILES = [
    'AGENTS.md','AGENT_CONFIG.json','WORKFLOW_PROTOCOL.md','CURRENT_RUNTIME.md','PROTOCOL_INVARIANTS.md',
    'memory/LTM_PROTOCOL.md','VIDEO_PROTOCOL.md','PHOTO_PROTOCOL.md','NOTION_PROTOCOL.md','WEBHOOK_PROTOCOL.md'
]
FORBIDDEN_ACTIVE = re.compile(r'localhost:11434|ollama/qwen|qwen3\.5:9b deployed|local GPU routing', re.I)
EXTERNAL_PROTOCOLS = ['NOTION_PROTOCOL.md','WEBHOOK_PROTOCOL.md','PDF_PROTOCOL.md','PHOTO_PROTOCOL.md','VIDEO_PROTOCOL.md','CHANNEL_PROTOCOL.md','SLA_PROTOCOL.md','LOG_RETENTION_PROTOCOL.md']


def check_exists(path):
    if not (ROOT/path).exists():
        FAIL.append(f'missing required file: {path}')

for f in ['PROTOCOL_INVARIANTS.md','CURRENT_RUNTIME.md','PROVIDER_STATUS.md']:
    check_exists(Path(f))

for f in ACTIVE_FILES:
    p=ROOT/f
    if not p.exists():
        continue
    txt=p.read_text(errors='ignore')
    if FORBIDDEN_ACTIVE.search(txt):
        FAIL.append(f'active file contains forbidden local-runtime reference: {f}')
    if f.endswith('_PROTOCOL.md') or f in ['WORKFLOW_PROTOCOL.md','VIDEO_PROTOCOL.md','PHOTO_PROTOCOL.md','NOTION_PROTOCOL.md','WEBHOOK_PROTOCOL.md']:
        if 'PROTOCOL_INVARIANTS.md' not in txt and f != 'PROTOCOL_INVARIANTS.md':
            WARN.append(f'protocol does not reference PROTOCOL_INVARIANTS.md: {f}')

for f in EXTERNAL_PROTOCOLS:
    p=ROOT/f
    if p.exists() and '## External Write Guardrails' not in p.read_text(errors='ignore'):
        WARN.append(f'external-write protocol missing guardrails section: {f}')

for f in ['AGENT_CONFIG.json','access_control.json']:
    p=ROOT/f
    if p.exists():
        try:
            json.loads(p.read_text())
        except Exception as e:
            FAIL.append(f'invalid JSON {f}: {e}')

# YAML parse optional: keep stdlib-only CI compatibility by checking file presence/rough syntax.
for p in (ROOT/'.github/workflows').glob('*.yml'):
    txt=p.read_text(errors='ignore')
    if 'on:' not in txt and '"on"' not in txt:
        WARN.append(f'workflow may lack trigger: {p.relative_to(ROOT)}')

print('# Protocol Audit Result')
if WARN:
    print('\n## Warnings')
    for w in WARN:
        print(f'- WARN: {w}')
if FAIL:
    print('\n## Failures')
    for f in FAIL:
        print(f'- FAIL: {f}')
    sys.exit(1)
print('\nPASS: no blocking protocol violations found.')

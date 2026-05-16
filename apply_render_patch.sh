#!/bin/bash
echo "=== Applying Pentagon Render Patch v0.0.1 ==="

# Ensure render modules are importable
python3 -c "
import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace')

# Test imports
from runtime.render.render_policy import RenderPolicy
from runtime.event.render_stable import render_progress, render_runtime_event_stable, render_full_telemetry

print('✅ All render modules loaded successfully')

# Verify stable output
progress_output = RenderPolicy.render_progress()
print(f'Progress output: {progress_output!r}')

# Verify metric labels
print(f'RPR metric: {RenderPolicy.format_telemetry_metric(\"RPR\", \"0.09\")!r}')
print(f'GAF metric: {RenderPolicy.format_telemetry_metric(\"GAF\", \"0.25\")!r}')

# Test telemetry
telemetry = RenderPolicy.render_full_telemetry()
print(f'Telemetry length: {len(telemetry)} chars')
"

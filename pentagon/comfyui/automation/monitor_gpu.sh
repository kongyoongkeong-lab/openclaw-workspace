#!/bin/bash
# Pentagon GPU Monitor

echo "=== RTX 4070 SUPER GPU Monitor ==="
watch -n 1 'nvidia-smi --query=utilization.gpu,memory.used --format=csv,nounits'

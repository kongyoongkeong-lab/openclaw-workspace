#!/bin/bash
# Trace Monitor Script
# Usage: ./trace_monitor.sh [workflow_name] [action]
# Actions: status, events, export, replay

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACE_DIR="/home/jason2ykk/.openclaw/workspace/traces"
WORKFLOW="${1:-daily_news}"
ACTION="${2:-status}"

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

case "$ACTION" in
    status)
        echo -e "${BLUE}=== Trace Status: ${WORKFLOW} ===${NC}"
        
        # Check for trace files
        TRACE_FILE="${TRACE_DIR}/${WORKFLOW}_trace.json"
        if [ -f "$TRACE_FILE" ]; then
            echo -e "${GREEN}✓ Trace file found: ${TRACE_FILE}${NC}"
            echo ""
            cat "$TRACE_FILE" | python3 -c "
import json,sys
data=json.load(sys.stdin)
print(f'  Trace ID:     {data.get(\"trace_id\",\"unknown\")}')
print(f'  Workflow:     {data.get(\"workflow\",\"unknown\")}')
print(f'  Status:       {data.get(\"status\",\"unknown\")}')
print(f'  Tool Calls:   {len(data.get(\"tool_calls\",[]))}')
print(f'  Total Events: {len(data.get(\"events\",[]))}')
"
        else
            echo -e "${YELLOW}! No trace file found for: ${WORKFLOW}${NC}"
            echo "  Available workflows:"
            ls -1 "${TRACE_DIR}"/*.json 2>/dev/null | xargs -n1 basename | sed 's/_trace\.json$//' || echo "    (none)"
        fi
        ;;
        
    events)
        echo -e "${BLUE}=== Trace Events: ${WORKFLOW} ===${NC}"
        TRACE_FILE="${TRACE_DIR}/${WORKFLOW}_trace.json"
        if [ -f "$TRACE_FILE" ]; then
            python3 -c "
import json
with open('$TRACE_FILE') as f:
    data = json.load(f)
    print('--- Event Log ---')
    for event in data.get('events',[]):
        print(f'{event.get(\"timestamp\")} [{event.get(\"event_type\")}] {event.get(\"tool_or_phase\")}')
        if event.get('status') == 'failed':
            print(f'  Error: {event.get(\"metadata\",{}).get(\"error\",\"unknown\")}')
"
        else
            echo "No trace file found"
        fi
        ;;
        
    export)
        echo -e "${BLUE}=== Export Trace: ${WORKFLOW} ===${NC}"
        TRACE_FILE="${TRACE_DIR}/${WORKFLOW}_trace.json"
        if [ -f "$TRACE_FILE" ]; then
            FORMAT="${3:-json}"
            case "$FORMAT" in
                json)
                    cp "$TRACE_FILE" "${TRACE_DIR}/exported/${WORKFLOW}.json"
                    ;;
                prometheus)
                    python3 -c "
import json
with open('$TRACE_FILE') as f:
    data = json.load(f)
    for event in data.get('events',[]):
        tool = event.get('tool_or_phase','')
        ts = event.get('timestamp','')
        status = event.get('status','0')
        print(f'{ts} {tool} {status}')
" > "${TRACE_DIR}/exported/${WORKFLOW}.prom"
            ;;
                *)
                    echo "Unknown format: $FORMAT"
                    ;;
            esac
            echo "Exported to: ${TRACE_DIR}/exported/"
        else
            echo "No trace file found"
        fi
        ;;
        
    replay)
        echo -e "${BLUE}=== Replay Trace: ${WORKFLOW} ===${NC}"
        TRACE_FILE="${TRACE_DIR}/${WORKFLOW}_trace.json"
        if [ -f "$TRACE_FILE" ]; then
            python3 -c "
import json
with open('$TRACE_FILE') as f:
    data = json.load(f)
    print(f'Replaying trace: {data.get(\"trace_id\")}')
    print(f'Events:')
    for event in data.get('events',[]):
        print(f'  {event}')
"
        else
            echo "No trace file found"
        fi
        ;;
        
    *)
        echo "Usage: $0 [workflow] [status|events|export|replay]"
        echo "  workflow: daily_news|system_event|daily_pulsing"
        echo "  action: status|events|export|replay"
        exit 1
        ;;
esac

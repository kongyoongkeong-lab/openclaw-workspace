#!/usr/bin/env python3
"""
Phase 8 Telemetry Aggregator
Purpose: Consolidate passive telemetry logs for long-horizon stability analysis
Author: Pentagon Orchestrator @main
Created: 2026-05-13 21:25
"""

import json
import glob
import os
from datetime import datetime
from typing import Dict, List, Any

# Configuration
LOG_DIR = "/home/jason2ykk/.openclaw/workspace/memory"
REPORT_DIR = "/home/jason2ykk/.openclaw/workspace/openclaw/telemetry/reports"
RAW_LOG_DIR = "/home/jason2ykk/.openclaw/workspace/openclaw/telemetry/logs"

def ensure_directories():
    """Create required directories if they don't exist"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(RAW_LOG_DIR, exist_ok=True)

def parse_memory_log(log_path: str) -> Dict[str, Any]:
    """Extract telemetry data from memory/*.md files"""
    telemetry_data = {
        "timestamp": None,
        "intent_id": None,
        "trigger": None,
        "agent": None,
        "rpr": None,
        "cache_hit": None,
        "latency_ms": None,
        "source": None,
        "metrics": {}
    }
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Extract timestamp
        if "Last update:" in content:
            for line in content.split("\n"):
                if "Last update:" in line:
                    # Parse timestamp (format: 2026-05-13 21:25 GMT+8)
                    try:
                        timestamp_str = line.split("Last update:")[1].strip()
                        telemetry_data["timestamp"] = datetime.fromtimestamp(
                            datetime.strptime(
                                " ".join(timestamp_str.split()[:-1]),  # Strip timezone
                                "%Y-%m-%d %H:%M"
                            ).timestamp()
                        ).isoformat()
                        break
                    except:
                        pass
        
        # Extract metrics from JSON blocks or telemetry sections
        # Look for JSON-like telemetry data
        telemetry_blocks = []
        json_blocks = json.loads(content) if content.startswith("{") else []
        if isinstance(json_blocks, list):
            telemetry_blocks = json_blocks
        
        # Extract intent_id from content
        for line in content.split("\n"):
            if "intent_id" in line.lower() or "Intent" in line:
                telemetry_data["intent_id"] = line.split("id:")[1].strip().split(",")[0] if "id:" in line else None
        
        # Extract trigger keywords
        for line in content.split("\n"):
            if "trigger" in line.lower() or "trigger" in line:
                trigger_match = line.lower().find("trigger:")
                if trigger_match >= 0:
                    trigger_part = line[trigger_match:]
                elif "今天新闻" in line or "morning news" in line:
                    telemetry_data["trigger"] = "今天新闻"
                elif "daily news" in line:
                    telemetry_data["trigger"] = "daily news"
                elif "latest news" in line:
                    telemetry_data["trigger"] = "latest news"
                else:
                    continue
        
        # Extract RPR score
        for line in content.split("\n"):
            if "rpr:" in line.lower() or "RPR" in line:
                try:
                    rpr_match = line.lower().find("rpr:")
                    if rpr_match >= 0:
                        rpr_part = line[rpr_match:]
                    else:
                        continue
                    # Extract numeric value
                    import re
                    rpr_match = re.search(r"rpr[:\s]+([0-9.]+)", line.lower())
                    if rpr_match:
                        telemetry_data["rpr"] = float(rpr_match.group(1))
                        break
                except:
                    pass
        
        # Extract latency
        for line in content.split("\n"):
            if "latency" in line.lower() or "tookms" in line.lower() or "tookms" in line.lower():
                try:
                    latency_match = re.search(r"tookms[:\s]+([0-9.]+)", line.lower())
                    if latency_match:
                        telemetry_data["latency_ms"] = float(latency_match.group(1))
                        break
                except:
                    pass
        
        # Extract agent
        for line in content.split("\n"):
            if "@intel" in line or "@ops" in line or "@main" in line:
                if "@intel" in line:
                    telemetry_data["agent"] = "@intel"
                elif "@ops" in line:
                    telemetry_data["agent"] = "@ops"
                elif "@main" in line:
                    telemetry_data["agent"] = "@main"
        
        # Extract cache_hit info
        for line in content.split("\n"):
            if "cache" in line.lower() and ("hit" in line.lower() or "miss" in line.lower()):
                if "cache hit:" in line.lower() or "cachehit:" in line.lower():
                    import re
                    cache_match = re.search(r"cache[:\s]*hit[:\s]+([0-9.]+)", line.lower())
                    if cache_match:
                        telemetry_data["cache_hit"] = float(cache_match.group(1))
                elif "cache hit rate" in line.lower():
                    telemetry_data["cache_hit"] = 1.0
                else:
                    telemetry_data["cache_hit"] = None
        
        telemetry_data["source"] = log_path
        
        return telemetry_data
        
    except Exception as e:
        telemetry_data["error"] = str(e)
        return telemetry_data

def aggregate_telemetry(log_dir: str = LOG_DIR, report_dir: str = REPORT_DIR) -> Dict[str, Any]:
    """Aggregate all telemetry data from memory logs and telemetry files"""
    ensure_directories()
    
    telemetry_data = []
    log_files = glob.glob(os.path.join(log_dir, "2026-05-13.md")) + \
                glob.glob(os.path.join(log_dir, "*.md"))
    
    for log_file in log_files:
        try:
            data = parse_memory_log(log_file)
            if "error" not in data or telemetry_data:
                telemetry_data.append(data)
        except Exception as e:
            print(f"Error processing {log_file}: {e}")
            continue
    
    # Generate summary report
    summary = {
        "aggregation_timestamp": datetime.now().isoformat(),
        "total_logs_processed": len(telemetry_data),
        "logs": telemetry_data,
        "summary": {
            "avg_rpr": sum(d.get("rpr", 0) for d in telemetry_data if d.get("rpr")) / max(1, sum(1 for d in telemetry_data if d.get("rpr"))),
            "avg_latency_ms": sum(d.get("latency_ms", 0) for d in telemetry_data if d.get("latency_ms")) / max(1, sum(1 for d in telemetry_data if d.get("latency_ms"))),
            "total_trigger_events": len([d for d in telemetry_data if d.get("trigger")]),
            "cache_hit_count": sum(1 for d in telemetry_data if d.get("cache_hit") and d.get("cache_hit") > 0),
            "agents_used": list(set(d.get("agent") for d in telemetry_data if d.get("agent")))
        }
    }
    
    # Write report
    report_file = os.path.join(report_dir, f"telemetry_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    return summary

if __name__ == "__main__":
    summary = aggregate_telemetry()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    # Also create a markdown report
    report_dir_final = REPORT_DIR
    md_report = f"""# Phase 8 Telemetry Summary Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

**Summary:**
- Total Logs Processed: {summary['summary']['total_trigger_events']}
- Average RPR: {summary['summary']['avg_rpr']:.4f}
- Average Latency: {summary['summary']['avg_latency_ms']:.2f}ms
- Cache Hit Events: {summary['summary']['cache_hit_count']}
- Agents Used: {summary['summary']['agents_used']}

**Raw Data:** {len(summary['logs'])} telemetry records captured

---
*Phase 8 Telemetry Aggregation Complete*
"""
    
    md_report_file = os.path.join(report_dir_final, f"telemetry_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md")
    with open(md_report_file, "w", encoding="utf-8") as f:
        f.write(md_report)
    
    print(f"\n📊 Summary saved to: {report_file}")
    print(f"📝 Markdown report saved to: {md_report_file}")

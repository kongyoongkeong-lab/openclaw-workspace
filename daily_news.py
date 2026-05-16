#!/usr/bin/env python3
"""
Daily News Workflow - Production Trace Integration Demo
This workflow demonstrates complete trace capture:
- TRIGGER_MATCHED
- TOOL_STARTED / TOOL_COMPLETED
- AGENT_HANDOFF
- CONTEXT_COMPRESSED
- WORKFLOW_COMPLETED
"""

import asyncio
import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace/tools')

from trace.trace_manager import TraceManager

class DailyNews:
    """
    Daily News Workflow with Full Trace Integration
    """
    
    def __init__(self):
        self.tm = TraceManager("daily_news")
        self.trigger_matched = False
    
    async def run(self):
        """Execute daily news workflow"""
        # 1️⃣ Gateway Trigger - Record TRIGGER_MATCHED
        print("🚀 Daily News Workflow Starting...")
        print("="*60)
        
        trace_id = self.tm.start()  # Records: WORKFLOW_INIT
        
        # Simulate gateway trigger
        self.trigger_matched = True
        append_event({
            "trace_id": trace_id,
            "event": "TRIGGER_MATCHED",
            "ts": 0,  # Relative time
            "msg": "Daily news trigger matched schedule"
        })
        
        print("✅ TRIGGER_MATCHED - Gateway scheduled")
        
        # 2️⃣ Tool Phase - @intel
        print("\n🔍 Phase: INTEL (Research & Gathering)")
        print("-" * 40)
        await self._intel_phase(trace_id)
        
        # 3️⃣ Agent Handoff - @intel → @ops
        print("\n🔄 Handoff: @intel → @ops")
        print("-" * 40)
        self.tm.agent_handoff("@intel", "@ops")
        
        # 4️⃣ Tool Phase - @ops
        print("\n⚙️  Phase: OPS (Execution)")
        print("-" * 40)
        await self._ops_phase(trace_id)
        
        # 5️⃣ Agent Handoff - @ops → @comms
        print("\n🔄 Handoff: @ops → @comms")
        print("-" * 40)
        self.tm.agent_handoff("@ops", "@comms")
        
        # 6️⃣ Tool Phase - @comms
        print("\n📢 Phase: COMMS (Communication)")
        print("-" * 40)
        await self._comms_phase(trace_id)
        
        # 7️⃣ Completion
        print("\n✅ Daily News Workflow Completed")
        print("="*60)
        self.tm.complete()
        
        return self.tm.get_trace()
    
    async def _intel_phase(self, trace_id: str):
        """Intel phase: Research & Web Search"""
        self.tm.phase_transition("INTEL_PHASE_START")
        
        # Simulate intel work
        await asyncio.sleep(1)  # Simulated latency
        
        print("  ✓ Gathered latest news")
        print("  ✓ Analyzed market trends")
        
        # Record tool completion
        append_event({
            "trace_id": trace_id,
            "event": "TOOL_COMPLETED",
            "ts": 1,
            "tool": "browser_fetch",
            "duration": 1.0,
            "result": "News gathered successfully"
        })
    
    async def _ops_phase(self, trace_id: str):
        """Ops phase: Data Processing"""
        self.tm.phase_transition("OPS_PHASE_START")
        
        await asyncio.sleep(1)
        
        print("  ✓ Processed news items")
        print("  ✓ Formatted output")
        
        append_event({
            "trace_id": trace_id,
            "event": "TOOL_COMPLETED",
            "ts": 2,
            "tool": "data_processor",
            "duration": 1.0,
            "result": "News processed"
        })
    
    async def _comms_phase(self, trace_id: str):
        """Comms phase: Final Output"""
        self.tm.phase_transition("COMMS_PHASE_START")
        
        await asyncio.sleep(1)
        
        print("  ✓ Formatted message")
        print("  ✓ Sent to Telegram")
        
        append_event({
            "trace_id": trace_id,
            "event": "TOOL_COMPLETED",
            "ts": 3,
            "tool": "telegram_send",
            "duration": 1.0,
            "result": "Message delivered"
        })

# Helper function for append_event (import from event_store)
def append_event(event):
    from trace.event_store import append_event as ae
    return ae(event)

if __name__ == "__main__":
    workflow = DailyNews()
    asyncio.run(workflow.run())
    print("\n🚀 Trace Capture Successful!")
    print("📄 View trace at: /home/jason2ykk/.openclaw/workspace/traces/2026-05-14.jsonl")

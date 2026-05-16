def validate_trace(trace: dict) -> dict:
 events = trace.get("events", [])

 required_order = [
     "WORKFLOW_INIT",
     "TRIGGER_MATCHED",
     "PHASE_START",
     "PHASE_END",
     "WORKFLOW_COMPLETED"
 ]

 event_types = [e.get("type") for e in events]

 missing = [e for e in required_order if e not in event_types]

 broken_chain = len(events) == 0 or event_types[0] != "WORKFLOW_INIT"

 return {
     "missing_events": missing,
     "broken_chain": broken_chain,
     "valid": len(missing) == 0 and not broken_chain,
     "status": "PASS" if len(missing) == 0 and not broken_chain else "FAIL"
 }

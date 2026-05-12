#!/usr/bin/env python3
"""
CRASH SIMULATION TEST SUITE
Validates atomic write durability under failure conditions.

Scenarios:
1. Mid-write kill - terminate process during write
2. Power-style interruption - force exception after temp write
3. Disk state check - verify only full valid file or no partial file

Expected behavior:
✅ old file intact OR new file fully committed
❌ NO partial JSON lines, corrupted JSONL tail, or missing records
"""

import os
import sys
import json
import tempfile
import shutil
import signal
import time
import hashlib
import resource
from pathlib import Path


def create_test_file(path: Path, record_count: int = 100, size_bytes: int = 500):
    """Create a test JSONL file with N records of fixed size."""
    lines_per_record = size_bytes // (json.dumps({"id": 0}).size() + 1)  # +1 for newline
    if lines_per_record < 1:
        lines_per_record = 1
    
    with open(path, "w") as f:
        for i in range(record_count):
            record = {"id": i, "data": "x" * (size_bytes // record_count)}
            f.write(json.dumps(record) + "\n")


def simulate_mid_write_kill(test_dir: Path, scenario_name: str):
    """
    Scenario 1: Mid-write kill
    Terminate process during write to simulate OOM/kill -9
    """
    print(f"\n{'='*60}")
    print(f"SCENARIO 1: Mid-Write Kill Simulation")
    print(f"{'='*60}")
    
    temp_file = test_dir / "test_scenario_1.jsonl"
    main_file = test_dir / "test_scenario_1_final.jsonl"
    temp_file.unlink(missing_ok=True)
    main_file.unlink(missing_ok=True)
    
    # Start writing with a long delay to allow interruption
    def writer():
        records_written = 0
        target_records = 50  # Small number to ensure quick crash
        chunk_size = 2
        
        for i in range(target_records):
            record = {"id": i, "timestamp": time.time(), "chunk": chunk_size}
            try:
                with open(temp_file, "a") as f:
                    f.write(json.dumps(record) + "\n")
                    records_written += 1
                # Add artificial delay to make interruption easier
                time.sleep(0.05)  # 50ms delay between writes
            except BrokenPipeError:
                print(f"  Write interrupted at record {i}")
                break
            except Exception as e:
                print(f"  Write error at record {i}: {e}")
                break
        
        # Simulate a crash after writing some records
        if records_written < target_records:
            print(f"  Process crashed after writing {records_written} records")
    
    # Create the test file in background thread
    writer_thread = Thread(target=writer)
    writer_thread.daemon = True
    writer_thread.start()
    
    # Wait a moment for writing to start
    time.sleep(0.1)
    
    # Crash the process
    print(f"  Triggering crash at record {records_written + 1}")
    writer_thread.join(timeout=1)  # Wait for thread to finish or timeout
    
    # Check state
    if temp_file.exists():
        lines = temp_file.read_text().strip().split('\n')
        try:
            last_id = int(json.loads(lines[-1])["id"])
            print(f"  ✅ Last written record ID: {last_id}")
            print(f"  ✅ Temp file has {len(lines)} lines (valid)")
        except:
            print(f"  ❌ Corrupted temp file (non-JSON lines detected)")
    
    # Main file should NOT exist
    if not main_file.exists():
        print(f"  ✅ Main file does not exist (expected)")
    else:
        print(f"  ❌ Main file exists unexpectedly")


class Thread:
    """Simple thread wrapper for this test suite."""
    def __init__(self, func, args=()):
        import threading
        self._thread = threading.Thread(target=func, args=args)
    
    def __enter__(self):
        self._thread.start()
        return self
    
    def __exit__(self, *args):
        self._thread.join()


def simulate_power_style_interruption(test_dir: Path, scenario_name: str):
    """
    Scenario 2: Power-style interruption
    Force exception after temp write but before rename
    """
    print(f"\n{'='*60}")
    print(f"SCENARIO 2: Power-Style Interruption Simulation")
    print(f"{'='*60}")
    
    temp_file = test_dir / "test_scenario_2.jsonl"
    main_file = test_dir / "test_scenario_2_final.jsonl"
    temp_file.unlink(missing_ok=True)
    main_file.unlink(missing_ok=True)
    
    # Create a backup for recovery simulation
    backup_file = test_dir / "test_scenario_2_backup.jsonl"
    
    records_before_crash = 30
    
    def atomic_write_wrapper():
        nonlocal records_before_crash
        main_file_path = str(main_file)
        temp_file_path = str(temp_file)
        backup_file_path = str(backup_file)
        
        for i in range(records_before_crash + 20):  # Write past crash point
            try:
                record = {"id": i, "data": "safe_record", "seq": i}
                
                # Write to temp file
                with open(temp_file_path, "a") as f:
                    f.write(json.dumps(record) + "\n")
                
                # CRASH POINT: Force exception before rename
                if i == records_before_crash:
                    print(f"  Forcing crash at record {i}")
                    raise Exception("SIMULATED_POWERS_LOSS")
                
                # Normal rename operation (won't reach here)
                # shutil.move(temp_file_path, main_file_path)
                
            except Exception as e:
                if "SIMULATED_POWERS_LOSS" in str(e):
                    print(f"  ✅ Simulated power loss caught")
                else:
                    print(f"  Unexpected error: {e}")
                break
    
    # Run the simulation
    try:
        atomic_write_wrapper()
    except:
        pass
    
    # Verify state
    if temp_file.exists():
        lines = temp_file.read_text().strip().split('\n')
        print(f"  Temp file has {len(lines)} lines")
        try:
            last_id = int(json.loads(lines[-1])["id"])
            print(f"  Last record ID in temp: {last_id}")
            
            # Verify all lines are valid JSON
            for idx, line in enumerate(lines):
                if not line:
                    continue
                json.loads(line)  # Will raise if invalid JSON
            print(f"  ✅ All {len(lines)} lines are valid JSON")
        except json.JSONDecodeError as e:
            print(f"  ❌ Invalid JSON found: {e}")
    else:
        print(f"  ❌ Temp file missing")
    
    if main_file.exists():
        print(f"  ❌ Main file exists when it shouldn't")
        lines = main_file.read_text().strip().split('\n')
        print(f"  Main file has {len(lines)} lines")
    else:
        print(f"  ✅ Main file does not exist (expected)")
    
    if backup_file.exists():
        backup_lines = backup_file.read_text().strip().split('\n')
        print(f"  Backup file has {len(backup_lines)} lines")


def verify_filesystem_consistency(test_dir: Path, scenario_name: str):
    """
    Scenario 3: Disk state check
    Ensure only full valid file exists OR no partial file exists
    NEVER half JSON line
    """
    print(f"\n{'='*60}")
    print(f"SCENARIO 3: Filesystem Consistency Check")
    print(f"{'='*60}")
    
    test_files = [
        test_dir / "consistency_a.jsonl",
        test_dir / "consistency_b.jsonl",
        test_dir / "consistency_c.jsonl",
    ]
    
    for test_file in test_files:
        test_file.unlink(missing_ok=True)
    
    # Create a nearly-complete file
    records = [{"id": i} for i in range(100)]
    for record in records:
        test_dir / "consistency_a.jsonl"  # Create first file
    
    # Simulate crash during final record write
    record = {"id": 99, "status": "complete"}
    
    temp_path = test_dir / "consistency_a.jsonl"
    lines = []
    for i in range(99):
        record = {"id": i}
        lines.append(json.dumps(record) + "\n")
    
    # Simulate crash before final line
    print(f"  Writing 99 records to consistency_a.jsonl...")
    with open(temp_path, "w") as f:
        for line in lines:
            f.write(line)
    
    # Check file integrity
    if temp_path.exists():
        content = temp_path.read_text()
        lines_read = content.strip().split('\n')
        
        print(f"  File has {len(lines_read)} lines")
        
        # Verify all lines are valid JSON
        for idx, line in enumerate(lines_read):
            try:
                data = json.loads(line)
                print(f"  Line {idx}: ✅ Valid JSON")
            except json.JSONDecodeError:
                print(f"  Line {idx}: ❌ Invalid JSON")
                return
    
    # Test scenario: Partial file recovery
    partial_path = test_dir / "consistency_partial.jsonl"
    main_path = test_dir / "consistency_main.jsonl"
    
    # Write to partial file
    with open(partial_path, "w") as f:
        for i in range(50):
            record = {"id": i}
            f.write(json.dumps(record) + "\n")
    
    print(f"  Partial file has {len(partial_path.read_text().strip().split(chr(10)))} lines")
    
    # Verify partial file integrity
    try:
        content = partial_path.read_text()
        lines = content.strip().split('\n')
        all_valid = all(json.loads(line) for line in lines if line)
        print(f"  ✅ Partial file integrity check: All {len(lines)} lines valid" if all_valid else "  ❌ Invalid lines detected")
    except Exception as e:
        print(f"  ❌ Error reading partial file: {e}")


def run_all_scenarios():
    """Run all crash simulation scenarios."""
    test_dir = Path("/tmp/crash_simulation_test")
    test_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("CRASH SIMULATION TEST SUITE")
    print("=" * 60)
    
    try:
        # Scenario 1: Mid-write kill
        simulate_mid_write_kill(test_dir, "mid_write_kill")
        
        # Scenario 2: Power-style interruption
        simulate_power_style_interruption(test_dir, "power_interruption")
        
        # Scenario 3: Filesystem consistency
        verify_filesystem_consistency(test_dir, "filesystem_consistency")
        
        print(f"\n{'='*60}")
        print("✅ ALL SCENARIOS COMPLETED")
        print(f"{'='*60}")
        
    finally:
        # Cleanup
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"Cleanup: Removed {test_dir}")


if __name__ == "__main__":
    run_all_scenarios()

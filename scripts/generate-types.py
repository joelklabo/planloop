#!/usr/bin/env python3
"""Generate TypeScript types from Pydantic models."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from planloop.core.state import (
    TaskType, TaskStatus, Task,
    SignalLevel, SignalType, Signal,
    NowReason, Now,
    SessionState
)

def enum_to_ts(enum_class) -> str:
    """Convert Python Enum to TypeScript union type."""
    values = [f'"{member.value}"' for member in enum_class]
    return " | ".join(values)

def generate_types() -> str:
    """Generate TypeScript types."""
    return f"""// Auto-generated TypeScript types from Pydantic models
// DO NOT EDIT - Run 'python scripts/generate-types.py' to regenerate

export type TaskType = {enum_to_ts(TaskType)};

export type TaskStatus = {enum_to_ts(TaskStatus)};

export interface Task {{
  id: number;
  title: string;
  type: TaskType;
  status: TaskStatus;
  depends_on: number[];
  commit_sha: string | null;
  last_updated_at: string | null;
}}

export type SignalLevel = {enum_to_ts(SignalLevel)};

export type SignalType = {enum_to_ts(SignalType)};

export interface Signal {{
  id: string;
  type: SignalType;
  kind: string;
  level: SignalLevel;
  open: boolean;
  title: string;
  message: string;
  link: string | null;
  extra: Record<string, any>;
  attempts: number;
}}

export type NowReason = {enum_to_ts(NowReason)};

export interface Now {{
  reason: NowReason;
  task_id: number | null;
  signal_id: string | null;
}}

export interface SessionState {{
  session: string;
  description: string;
  tasks: Task[];
  signals: Signal[];
  now: Now;
  lock_holder: string | null;
  created_at: string;
  last_updated_at: string;
}}
"""

if __name__ == "__main__":
    output_path = Path(__file__).parent.parent / "frontend/src/types/api.ts"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    types_content = generate_types()
    output_path.write_text(types_content)
    
    print(f"✅ Generated TypeScript types: {output_path}")
    print(f"   {len(types_content.splitlines())} lines")

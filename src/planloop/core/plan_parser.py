"""Parser for importing tasks from PLAN.md files."""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

from .state import TaskStatus, TaskType


class ParsedTask(BaseModel):
    """Represents a task parsed from markdown."""
    
    title: str
    status: TaskStatus
    type: TaskType = TaskType.FEATURE


def parse_plan_file(content: str) -> list[ParsedTask]:
    """Parse tasks from markdown PLAN.md content.
    
    Args:
        content: Markdown content
        
    Returns:
        List of parsed tasks
    """
    tasks = []
    
    # Match markdown task lines: - [ ] or - [x] or * [ ] etc
    # Patterns: - [ ], - [x], - [X], * [ ], * [x], + [ ], + [x]
    task_pattern = r'^[\s]*[-*+]\s+\[([ xX])\]\s+(.+)$'
    
    for line in content.split('\n'):
        match = re.match(task_pattern, line)
        if match:
            checkbox, title = match.groups()
            
            # Determine status
            if checkbox.strip().lower() == 'x':
                status = TaskStatus.DONE
            else:
                status = TaskStatus.TODO
            
            # Clean up title
            title = title.strip()
            
            # Determine type from title hints
            title_lower = title.lower()
            if 'test' in title_lower:
                task_type = TaskType.TEST
            elif 'fix' in title_lower or 'bug' in title_lower:
                task_type = TaskType.FIX
            elif 'doc' in title_lower:
                task_type = TaskType.CHORE
            else:
                task_type = TaskType.FEATURE
            
            tasks.append(ParsedTask(
                title=title,
                status=status,
                type=task_type
            ))
    
    return tasks

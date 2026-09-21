def calculate_progress(completed: int, total: int) -> int:
    """Return plan/task completion as a bounded percentage, never elapsed time."""
    if completed < 0 or total < 0 or completed > total:
        raise ValueError("completed must be between zero and total")
    return round((completed / total) * 100) if total else 0

def score_task(urgency, age):
    """
    Calculates the effective score for a task with the given urgency and age.

    Args:
        urgency: The urgency of the task (integer).
        age: The age of the task in seconds (integer).

    Returns:
        The effective score of the task (integer).
    """
    boost = 0
    if age >= 60:
        boost += 5
    if age >= 300:
        boost += 7
    return urgency + boost

class Task:
    def __init__(self, name, urgency, age):
        self.name = name
        self.urgency = urgency
        self.age = age

class TaskQueue:
    def __init__(self, tasks):
        self._tasks = list(tasks)

    def _score(self, t):
        boost = 0
        if t.age >= 60: boost += 5
        if t.age >= 300: boost += 7
        return t.urgency + boost

    def next_task(self):
        if not self._tasks:
            return None
        return max(self._tasks, key=self._score)

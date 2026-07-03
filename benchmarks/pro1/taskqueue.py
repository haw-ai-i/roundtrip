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

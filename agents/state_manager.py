"""
State Manager - 에이전트 공유 상태 (JSON 기반)
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class Milestone:
    id:          str
    title:       str
    description: str
    status:      str = "pending"   # pending | in_progress | done | failed
    assigned_to: str = ""
    result:      str = ""
    cycle_created: int = 0


@dataclass
class SubTask:
    id:          str
    milestone_id: str
    title:       str
    description: str
    assigned_to: str   # dev_a | dev_b
    status:      str = "pending"
    difficulty:  str = "medium"
    file_path:   str = ""
    result:      str = ""
    cycle_id:    int = 0


@dataclass
class CycleLog:
    cycle_id:    int
    started_at:  str
    finished_at: str = ""
    status:      str = "running"   # running | complete | failed
    inspector_score: float = 0.0
    notes:       str = ""


@dataclass
class ProjectState:
    goal:         str = ""
    status:       str = "idle"     # idle | running | complete | failed
    current_cycle: int = 0
    milestones:   list[Milestone] = field(default_factory=list)
    tasks:        list[SubTask]   = field(default_factory=list)
    cycle_logs:   list[CycleLog]  = field(default_factory=list)
    created_at:   str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at:   str = field(default_factory=lambda: datetime.utcnow().isoformat())


class StateManager:
    """JSON 파일 기반 공유 상태 관리"""

    def __init__(self, state_dir: str = "agents/state"):
        self._dir = Path(state_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "project_state.json"
        self._state: ProjectState = self._load()
        logger.info(f"StateManager 초기화: {self._path}")

    # ── 로드 / 저장 ──────────────────────────────────────────

    def _load(self) -> ProjectState:
        if self._path.exists():
            data = json.loads(self._path.read_text(encoding="utf-8"))
            state = ProjectState(**{
                k: v for k, v in data.items()
                if k not in ("milestones", "tasks", "cycle_logs")
            })
            state.milestones = [Milestone(**m) for m in data.get("milestones", [])]
            state.tasks      = [SubTask(**t)   for t in data.get("tasks", [])]
            state.cycle_logs = [CycleLog(**c)  for c in data.get("cycle_logs", [])]
            return state
        return ProjectState()

    def save(self):
        self._state.updated_at = datetime.utcnow().isoformat()
        self._path.write_text(
            json.dumps(asdict(self._state), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── 목표 / 사이클 ─────────────────────────────────────────

    def set_goal(self, goal: str):
        self._state.goal   = goal
        self._state.status = "running"
        self.save()

    def start_cycle(self) -> int:
        self._state.current_cycle += 1
        self._state.cycle_logs.append(CycleLog(
            cycle_id=self._state.current_cycle,
            started_at=datetime.utcnow().isoformat(),
        ))
        self.save()
        return self._state.current_cycle

    def end_cycle(self, score: float, notes: str = ""):
        log = self._get_cycle_log(self._state.current_cycle)
        if log:
            log.finished_at = datetime.utcnow().isoformat()
            log.status      = "complete"
            log.inspector_score = score
            log.notes       = notes
        self.save()

    def _get_cycle_log(self, cycle_id: int) -> CycleLog | None:
        for c in self._state.cycle_logs:
            if c.cycle_id == cycle_id:
                return c
        return None

    # ── 마일스톤 ────────────────────────────────────────────

    def set_milestones(self, milestones: list[dict]):
        self._state.milestones = [
            Milestone(
                id=f"M{i+1:02d}",
                title=m.get("title", ""),
                description=m.get("description", ""),
                cycle_created=self._state.current_cycle,
            )
            for i, m in enumerate(milestones)
        ]
        self.save()

    def update_milestone(self, milestone_id: str, **kwargs):
        for m in self._state.milestones:
            if m.id == milestone_id:
                for k, v in kwargs.items():
                    setattr(m, k, v)
        self.save()

    def get_pending_milestones(self) -> list[Milestone]:
        return [m for m in self._state.milestones if m.status == "pending"]

    # ── 서브태스크 ───────────────────────────────────────────

    def add_tasks(self, tasks: list[dict]):
        for t in tasks:
            self._state.tasks.append(SubTask(
                id=f"T{len(self._state.tasks)+1:03d}",
                milestone_id=t.get("milestone_id", ""),
                title=t.get("title", ""),
                description=t.get("description", ""),
                assigned_to=t.get("assigned_to", "dev_a"),
                difficulty=t.get("difficulty", "medium"),
                cycle_id=self._state.current_cycle,
            ))
        self.save()

    def update_task(self, task_id: str, **kwargs):
        for t in self._state.tasks:
            if t.id == task_id:
                for k, v in kwargs.items():
                    setattr(t, k, v)
        self.save()

    def get_tasks_for(self, agent: str, status: str = "pending") -> list[SubTask]:
        return [
            t for t in self._state.tasks
            if t.assigned_to == agent and t.status == status
        ]

    # ── 프로퍼티 ─────────────────────────────────────────────

    @property
    def goal(self) -> str:
        return self._state.goal

    @property
    def current_cycle(self) -> int:
        return self._state.current_cycle

    @property
    def milestones(self) -> list[Milestone]:
        return self._state.milestones

    @property
    def all_tasks(self) -> list[SubTask]:
        return self._state.tasks

    def progress_summary(self) -> dict:
        total = len(self._state.milestones)
        done  = sum(1 for m in self._state.milestones if m.status == "done")
        return {
            "total_milestones": total,
            "done": done,
            "progress_pct": round(done / total * 100) if total else 0,
            "current_cycle": self._state.current_cycle,
            "status": self._state.status,
        }

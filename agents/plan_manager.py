"""
Plan Manager Agent - 병렬 분배 및 진행 모니터링
Claude Haiku (계획 정리) / Gemma (상태 체크)
"""
from __future__ import annotations

import asyncio
import json

from loguru import logger

from core.claude_agent import ClaudeAgent
from core.gemma_agent import GemmaAgent
from .base_agent import AgentRole, BaseAgent, MsgType, Priority
from .state_manager import StateManager, SubTask


class PlanManagerAgent(BaseAgent):
    """마일스톤을 서브태스크로 분해하고 Dev 에이전트에게 병렬 할당"""

    SYSTEM_PROMPT = """당신은 소프트웨어 프로젝트의 플랜 매니저입니다.
리더의 마일스톤을 구체적인 서브태스크로 분해하고
개발자들에게 효율적으로 분배합니다. JSON으로만 응답하세요."""

    def __init__(self, state: StateManager, message_bus=None):
        super().__init__(AgentRole.PLAN_MANAGER, message_bus)
        self.claude = ClaudeAgent()
        self.gemma  = GemmaAgent()
        self.state  = state
        self._pending_tasks: list[SubTask] = []

    async def run(self, milestones: list[dict], goal: str = "") -> list[SubTask]:
        """마일스톤을 서브태스크로 분해하고 병렬 분배"""
        self.log(f"분배 시작: {len(milestones)}개 마일스톤")

        all_tasks = []
        for milestone in milestones:
            tasks = await self._decompose_milestone(milestone, goal)
            all_tasks.extend(tasks)

        # 상태 저장
        self.state.add_tasks([
            {
                "milestone_id": t.milestone_id,
                "title": t.title,
                "description": t.description,
                "assigned_to": t.assigned_to,
                "difficulty": t.difficulty,
            }
            for t in all_tasks
        ])

        # Dev A / Dev B 에게 병렬 전송
        dev_a_tasks = [t for t in all_tasks if t.assigned_to == "dev_a"]
        dev_b_tasks = [t for t in all_tasks if t.assigned_to == "dev_b"]

        if dev_a_tasks:
            await self.send(
                to=AgentRole.DEV_A,
                msg_type=MsgType.TASK,
                content={"tasks": [self._task_to_dict(t) for t in dev_a_tasks]},
                priority=Priority.HIGH,
            )
        if dev_b_tasks:
            await self.send(
                to=AgentRole.DEV_B,
                msg_type=MsgType.TASK,
                content={"tasks": [self._task_to_dict(t) for t in dev_b_tasks]},
                priority=Priority.HIGH,
            )

        self.log(f"분배 완료: Dev A={len(dev_a_tasks)}, Dev B={len(dev_b_tasks)}")
        return all_tasks

    async def _decompose_milestone(self, milestone: dict, goal: str) -> list[SubTask]:
        """마일스톤 → 서브태스크 분해 (Claude Haiku 사용)"""
        prompt = f"""다음 마일스톤을 개발 서브태스크로 분해하세요.

전체 목표: {goal}
마일스톤: {milestone.get('title')}
설명: {milestone.get('description')}

규칙:
- Dev A: 핵심 비즈니스 로직, API, 알고리즘 담당
- Dev B: 테스트 작성, 유틸리티, 문서화 담당
- 각 태스크는 독립적으로 실행 가능해야 함
- 난이도: low(Gemma), medium(Gemma+폴백), high(Claude)

JSON으로만 응답:
{{
  "tasks": [
    {{
      "title": "태스크 제목",
      "description": "구체적인 구현 내용과 완료 기준",
      "assigned_to": "dev_a",
      "difficulty": "medium",
      "file_hint": "저장할 파일명 힌트"
    }}
  ]
}}"""

        try:
            response = self.claude.ask(prompt, system=self.SYSTEM_PROMPT)
            text = response.content
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
        except Exception as e:
            logger.warning(f"태스크 분해 실패, 기본값 사용: {e}")
            data = {"tasks": [
                {"title": milestone.get("title", "구현"), "description": milestone.get("description", ""),
                 "assigned_to": "dev_a", "difficulty": "medium", "file_hint": "main.py"}
            ]}

        tasks = []
        for i, t in enumerate(data.get("tasks", [])):
            tasks.append(SubTask(
                id=f"T{i:03d}",
                milestone_id=milestone.get("id", "M01"),
                title=t.get("title", ""),
                description=t.get("description", ""),
                assigned_to=t.get("assigned_to", "dev_a"),
                difficulty=t.get("difficulty", "medium"),
            ))
        return tasks

    async def monitor_progress(self) -> dict:
        """Gemma로 현재 진행 상황 요약"""
        summary = self.state.progress_summary()
        tasks   = self.state.all_tasks

        done    = [t for t in tasks if t.status == "done"]
        running = [t for t in tasks if t.status == "in_progress"]
        pending = [t for t in tasks if t.status == "pending"]
        failed  = [t for t in tasks if t.status == "failed"]

        report_text = (
            f"총 {len(tasks)}개 태스크: "
            f"완료={len(done)}, 진행={len(running)}, "
            f"대기={len(pending)}, 실패={len(failed)}"
        )
        self.log(f"진행 현황: {report_text}")

        return {
            "summary": summary,
            "done": len(done),
            "running": len(running),
            "pending": len(pending),
            "failed": len(failed),
            "report": report_text,
        }

    async def handle_question(self, from_agent: AgentRole, question: str) -> str:
        """Dev 에이전트의 질문에 Gemma로 빠르게 답변"""
        response = self.gemma.ask(
            f"개발자 질문에 간결하게 답해주세요:\n{question}",
            task_type="simple_qa",
        )
        answer = response.content
        await self.send(
            to=from_agent,
            msg_type=MsgType.REPORT,
            content={"answer": answer},
            priority=Priority.HIGH,
        )
        return answer

    async def request_inspection(self, results: list[dict]):
        """Inspector에게 검수 요청"""
        await self.send(
            to=AgentRole.INSPECTOR,
            msg_type=MsgType.TASK,
            content={
                "milestones": [{"id": m.id, "title": m.title, "description": m.description}
                               for m in self.state.milestones],
                "results": results,
                "goal": self.state.goal,
            },
            priority=Priority.HIGH,
        )
        self.log("Inspector에게 검수 요청 완료")

    @staticmethod
    def _task_to_dict(t: SubTask) -> dict:
        return {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "difficulty": t.difficulty,
            "milestone_id": t.milestone_id,
        }

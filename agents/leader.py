"""
Leader Agent - 목표 해석, 전략 수립, 최종 승인
항상 Claude Sonnet 사용 (복잡한 판단 필요)
"""
from __future__ import annotations

import json

from loguru import logger

from core.claude_agent import ClaudeAgent
from .base_agent import AgentRole, BaseAgent, MsgType, Priority
from .state_manager import StateManager


class LeaderAgent(BaseAgent):
    """목표를 마일스톤으로 분해하고 전체 방향을 결정하는 리더"""

    SYSTEM_PROMPT = """당신은 소프트웨어 프로젝트의 리더 에이전트입니다.
주어진 목표를 달성하기 위해 명확한 마일스톤을 수립하고,
팀 에이전트들이 효율적으로 협력할 수 있도록 지휘합니다.
항상 JSON 형식으로 응답하세요."""

    def __init__(self, state: StateManager, message_bus=None):
        super().__init__(AgentRole.LEADER, message_bus)
        self.claude = ClaudeAgent()
        self.state  = state

    async def run(self, goal: str) -> dict:
        """목표를 받아 마일스톤 계획 수립"""
        self.log(f"목표 수신: {goal}")
        self.state.set_goal(goal)

        plan = await self._create_plan(goal)
        self.state.set_milestones(plan["milestones"])

        self.log(f"계획 수립 완료: {len(plan['milestones'])}개 마일스톤")

        # Plan Manager에게 계획 전달
        await self.send(
            to=AgentRole.PLAN_MANAGER,
            msg_type=MsgType.TASK,
            content={
                "goal": goal,
                "milestones": plan["milestones"],
                "success_criteria": plan.get("success_criteria", []),
            },
            priority=Priority.HIGH,
        )
        return plan

    async def _create_plan(self, goal: str, previous_report: str = "") -> dict:
        """Claude를 사용해 목표를 마일스톤으로 분해"""
        history_note = ""
        if previous_report:
            history_note = f"\n\n이전 사이클 검수 보고서:\n{previous_report}\n\n위 피드백을 반영하여 계획을 수정하세요."

        prompt = f"""다음 소프트웨어 개발 목표를 분석하고 실행 계획을 JSON으로 작성하세요.
{history_note}
목표: {goal}

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "milestones": [
    {{
      "title": "마일스톤 제목",
      "description": "상세 설명 및 완료 기준",
      "difficulty": "low|medium|high",
      "estimated_tasks": 2
    }}
  ],
  "success_criteria": ["기준1", "기준2"],
  "tech_stack": ["Python", "FastAPI"],
  "notes": "전체 전략 메모"
}}

마일스톤은 3~5개로 구성하고 순서대로 진행 가능하게 작성하세요."""

        response = self.claude.ask(prompt, system=self.SYSTEM_PROMPT, task_type="architecture_design")
        self.log(f"계획 생성 완료 (tokens: in={response.input_tokens}, out={response.output_tokens})")

        try:
            # JSON 추출 (코드블록이 있을 경우 제거)
            text = response.content
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except Exception as e:
            logger.warning(f"JSON 파싱 실패, 기본값 반환: {e}")
            return {
                "milestones": [
                    {"title": "프로젝트 초기 구조 설정", "description": goal, "difficulty": "medium", "estimated_tasks": 3}
                ],
                "success_criteria": ["기능 동작", "테스트 통과"],
                "tech_stack": ["Python"],
                "notes": response.content[:200],
            }

    async def evaluate_completion(self, inspector_report: dict) -> bool:
        """Inspector 보고서를 보고 목표 달성 여부 최종 판단"""
        score = inspector_report.get("score", 0)
        criteria_met = inspector_report.get("criteria_met", [])
        issues = inspector_report.get("issues", [])

        self.log(f"검수 점수: {score}/100, 달성 기준: {len(criteria_met)}개, 이슈: {len(issues)}개")

        if score >= 80 and not issues:
            self.log("✅ 목표 달성 확인 — 완료 선언")
            return True

        self.log(f"❌ 미달성 (score={score}) — 재계획 필요")
        return False

    async def revise_plan(self, goal: str, inspector_report: dict) -> dict:
        """검수 실패 시 수정 계획 수립"""
        report_text = json.dumps(inspector_report, ensure_ascii=False, indent=2)
        self.log("수정 계획 수립 중...")
        plan = await self._create_plan(goal, previous_report=report_text)
        self.state.set_milestones(plan["milestones"])

        await self.send(
            to=AgentRole.PLAN_MANAGER,
            msg_type=MsgType.TASK,
            content={
                "goal": goal,
                "milestones": plan["milestones"],
                "success_criteria": plan.get("success_criteria", []),
                "revision": True,
            },
            priority=Priority.HIGH,
        )
        return plan

"""
Inspector Agent - 코드 품질 검수 및 채점
항상 Claude Sonnet 사용 (정확한 판단 필요)
"""
from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

from core.claude_agent import ClaudeAgent
from .base_agent import AgentRole, BaseAgent, MsgType, Priority
from .state_manager import StateManager


class InspectorAgent(BaseAgent):
    """개발 결과물을 기획서와 대조하여 통과/반려 판정"""

    SYSTEM_PROMPT = """당신은 엄격하고 공정한 코드 검수관입니다.
기획서의 요구사항과 실제 개발된 코드를 대조하여 객관적으로 평가합니다.
점수는 0~100점이며 80점 이상이면 통과입니다. JSON으로만 응답하세요."""

    def __init__(self, state: StateManager, message_bus=None):
        super().__init__(AgentRole.INSPECTOR, message_bus)
        self.claude = ClaudeAgent()
        self.state  = state

    async def run(self, milestones: list[dict], results: list[dict], goal: str = "") -> dict:
        """개발 결과물 전체 검수"""
        self.log(f"검수 시작: {len(results)}개 결과물")

        report = await self._review(goal, milestones, results)

        # 결과 저장
        report_path = Path("agents/reports") / f"cycle_{self.current_cycle:03d}_inspection.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        score  = report.get("score", 0)
        passed = score >= 80

        self.log(
            f"검수 완료: {'✅ 통과' if passed else '❌ 반려'} "
            f"(score={score}/100)"
        )

        # Leader에게 보고
        await self.send(
            to=AgentRole.LEADER,
            msg_type=MsgType.COMPLETE if passed else MsgType.REJECT,
            content=report,
            priority=Priority.HIGH,
        )
        # Plan Manager에게도 보고
        await self.send(
            to=AgentRole.PLAN_MANAGER,
            msg_type=MsgType.REPORT,
            content={"score": score, "passed": passed, "issues": report.get("issues", [])},
            priority=Priority.MEDIUM,
        )
        return report

    async def _review(self, goal: str, milestones: list[dict], results: list[dict]) -> dict:
        """Claude로 상세 검수"""
        milestone_text = "\n".join(
            f"- [{m.get('id','?')}] {m.get('title')}: {m.get('description','')}"
            for m in milestones
        )

        # 결과물 코드 수집 (파일에서 읽기)
        code_samples = []
        for r in results[:5]:  # 최대 5개만
            fp = r.get("file_path", "")
            if fp and Path(fp).exists():
                code = Path(fp).read_text(encoding="utf-8", errors="ignore")
                code_samples.append(f"### {r.get('task_id')} — {fp}\n```python\n{code[:800]}\n```")

        code_text = "\n\n".join(code_samples) if code_samples else "코드 파일 없음"

        prompt = f"""다음 소프트웨어 개발 결과물을 검수하세요.

전체 목표: {goal}

기획 마일스톤:
{milestone_text}

개발 결과물:
{code_text}

아래 JSON 형식으로만 응답하세요:
{{
  "score": 75,
  "passed": false,
  "criteria_met": ["기준1 달성", "기준2 달성"],
  "issues": [
    {{"severity": "high", "description": "문제 설명", "file": "파일명", "suggestion": "수정 제안"}}
  ],
  "strengths": ["잘된 점1"],
  "summary": "전반적인 평가 요약"
}}

채점 기준:
- 기능 요구사항 충족도 (40점)
- 코드 품질 및 구조 (30점)
- 에러 처리 (20점)
- 문서화/주석 (10점)"""

        response = self.claude.ask(prompt, system=self.SYSTEM_PROMPT, task_type="code_review")

        try:
            text = response.content
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except Exception as e:
            logger.warning(f"검수 JSON 파싱 실패: {e}")
            # 점수를 텍스트에서 추출 시도
            score = 50
            for word in response.content.split():
                if word.isdigit() and 0 <= int(word) <= 100:
                    score = int(word)
                    break
            return {
                "score": score,
                "passed": score >= 80,
                "criteria_met": [],
                "issues": [{"severity": "low", "description": "자동 파싱 실패", "file": "", "suggestion": ""}],
                "strengths": [],
                "summary": response.content[:300],
            }

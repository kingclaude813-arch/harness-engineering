"""
Developer Agent - 실제 코드 작성
난이도에 따라 Gemma / Claude 자동 전환
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from loguru import logger

from core.claude_agent import ClaudeAgent
from core.gemma_agent import GemmaAgent
from .base_agent import AgentRole, BaseAgent, Difficulty, MsgType, Priority, TaskResult
from .state_manager import StateManager, SubTask


class DeveloperAgent(BaseAgent):
    """코드 생성 에이전트 — 난이도별 LLM 자동 라우팅"""

    SYSTEM_PROMPT = """당신은 전문 소프트웨어 개발자입니다.
주어진 태스크를 분석하고 실제 동작하는 Python 코드를 작성합니다.
코드만 출력하고, 설명은 주석으로 작성하세요."""

    def __init__(self, role: AgentRole, state: StateManager,
                 workspace: str = "", message_bus=None):
        super().__init__(role, message_bus)
        self.claude    = ClaudeAgent()
        self.gemma     = GemmaAgent()
        self.state     = state
        self.workspace = Path(workspace or f"agents/workspace/{role.value}")
        self.workspace.mkdir(parents=True, exist_ok=True)

    async def run(self, tasks: list[dict]) -> list[TaskResult]:
        """태스크 목록을 순차 실행하고 결과 반환"""
        results = []
        for task_data in tasks:
            self.log(f"태스크 시작: {task_data.get('title')}")
            result = await self._execute_task(task_data)
            results.append(result)

            # Plan Manager에게 보고
            await self.send(
                to=AgentRole.PLAN_MANAGER,
                msg_type=MsgType.REPORT if result.success else MsgType.QUESTION,
                content={
                    "task_id":   result.task_id,
                    "success":   result.success,
                    "file_path": result.file_path,
                    "model":     result.model_used,
                    "error":     result.error,
                    "output_preview": result.output[:200],
                },
                priority=Priority.MEDIUM,
            )

        self.log(f"모든 태스크 완료: {len(results)}개")
        return results

    async def _execute_task(self, task_data: dict) -> TaskResult:
        """단일 태스크 실행 — 난이도 판단 후 LLM 선택"""
        task_id    = task_data.get("id", "T000")
        title      = task_data.get("title", "")
        desc       = task_data.get("description", "")
        difficulty = task_data.get("difficulty", "medium")

        # 상태 업데이트
        self.state.update_task(task_id, status="in_progress")

        prompt = self._build_prompt(title, desc)

        # 난이도에 따라 LLM 선택
        code, model_used = await self._generate_code(prompt, difficulty, task_id)

        if not code:
            self.state.update_task(task_id, status="failed")
            return TaskResult(
                agent=self.role, task_id=task_id,
                success=False, output="", error="코드 생성 실패",
                model_used=model_used, cycle_id=self.current_cycle,
            )

        # 파일 저장
        file_path = self._save_code(task_id, title, code)
        self.state.update_task(task_id, status="done", file_path=str(file_path), result=code[:300])

        self.log(f"  ✅ 완료: {title} → {file_path} [{model_used}]")
        return TaskResult(
            agent=self.role, task_id=task_id,
            success=True, output=code, file_path=str(file_path),
            model_used=model_used, cycle_id=self.current_cycle,
        )

    async def _generate_code(self, prompt: str, difficulty: str, task_id: str) -> tuple[str, str]:
        """난이도 기반 LLM 선택 및 코드 생성"""

        # HIGH → Claude 직행
        if difficulty == Difficulty.HIGH:
            self.log(f"  🔵 Claude 사용 (난이도: high)")
            resp = self.claude.ask(prompt, system=self.SYSTEM_PROMPT, task_type="complex_code_generation")
            return self._extract_code(resp.content), f"claude/{resp.model}"

        # LOW / MEDIUM → Gemma 먼저 시도
        self.log(f"  🟢 Gemma 시도 (난이도: {difficulty})")
        try:
            if self.gemma.is_available():
                resp = self.gemma.ask(prompt, system=self.SYSTEM_PROMPT)
                code = self._extract_code(resp.content)
                if code and len(code) > 30:
                    return code, f"gemma/{self.gemma.model}"
                self.log(f"  ⚠ Gemma 출력 부족 → Claude 폴백")
        except Exception as e:
            self.log(f"  ⚠ Gemma 실패: {e} → Claude 폴백")

        # Claude 폴백
        self.log(f"  🔵 Claude 폴백")
        resp = self.claude.ask(prompt, system=self.SYSTEM_PROMPT, task_type="complex_code_generation")
        return self._extract_code(resp.content), f"claude(fallback)/{resp.model}"

    def _build_prompt(self, title: str, description: str) -> str:
        return f"""태스크: {title}

요구사항:
{description}

다음을 포함한 완전한 Python 코드를 작성하세요:
- 실제 동작하는 구현 코드
- 적절한 주석
- 기본 에러 처리
- 간단한 사용 예시 (if __name__ == "__main__": 블록)

코드만 출력하세요."""

    @staticmethod
    def _extract_code(text: str) -> str:
        """응답에서 코드 블록 추출"""
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        if "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def _save_code(self, task_id: str, title: str, code: str) -> Path:
        """생성된 코드를 파일로 저장"""
        safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in title.lower())[:40]
        file_path = self.workspace / f"{task_id}_{safe_name}.py"
        file_path.write_text(code, encoding="utf-8")
        return file_path

    async def ask_question(self, question: str) -> str:
        """Plan Manager에게 질문 (블로커 발생 시)"""
        self.log(f"❓ 질문: {question[:80]}")
        await self.send(
            to=AgentRole.PLAN_MANAGER,
            msg_type=MsgType.QUESTION,
            content={"question": question},
            priority=Priority.HIGH,
        )
        # 답변 대기 (최대 30초)
        response = await self.receive(timeout=30.0)
        if response:
            return response.content.get("answer", "답변 없음")
        return "타임아웃"

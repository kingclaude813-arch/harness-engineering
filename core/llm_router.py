"""
LLM 라우터 - 작업 복잡도에 따라 Claude vs Gemma 자동 선택
토큰 비용 최적화의 핵심 모듈
"""
from __future__ import annotations

import os
from enum import Enum
from typing import Union

import yaml
from loguru import logger
from pydantic import BaseModel

from .claude_agent import ClaudeAgent, ClaudeResponse
from .gemma_agent import GemmaAgent, GemmaResponse

LLMResponse = Union[ClaudeResponse, GemmaResponse]


class TaskType(str, Enum):
    # ── Claude 전용 (복잡) ────────────────────────────────────
    ARCHITECTURE_DESIGN = "architecture_design"
    SECURITY_REVIEW = "security_review"
    COMPLEX_CODE_GENERATION = "complex_code_generation"
    CODE_REVIEW = "code_review"
    API_DESIGN = "api_design"
    PERFORMANCE_ANALYSIS = "performance_analysis"

    # ── Gemma 전용 (경량) ─────────────────────────────────────
    SUMMARY = "summary"
    CLASSIFICATION = "classification"
    COMMIT_MESSAGE = "commit_message"
    CHANGELOG = "changelog_entry"
    SIMPLE_QA = "simple_qa"
    TYPO_FIX = "typo_fix"
    LABEL_CLASSIFICATION = "label_classification"

    # ── 동적 라우팅 (토큰 수에 따라 결정) ────────────────────
    AUTO = "auto"


class RouteDecision(BaseModel):
    use_claude: bool
    reason: str
    task_type: str
    estimated_tokens: int = 0


class LLMRouter:
    """
    Claude(메인) ↔ Gemma(경량) 자동 라우터

    라우팅 기준:
    1. TaskType으로 명시된 경우 → 해당 LLM 사용
    2. AUTO 모드 → 프롬프트 토큰 수로 판단
    3. Gemma 불가 시 → Claude로 폴백
    """

    CLAUDE_TASKS = {
        TaskType.ARCHITECTURE_DESIGN,
        TaskType.SECURITY_REVIEW,
        TaskType.COMPLEX_CODE_GENERATION,
        TaskType.CODE_REVIEW,
        TaskType.API_DESIGN,
        TaskType.PERFORMANCE_ANALYSIS,
    }

    GEMMA_TASKS = {
        TaskType.SUMMARY,
        TaskType.CLASSIFICATION,
        TaskType.COMMIT_MESSAGE,
        TaskType.CHANGELOG,
        TaskType.SIMPLE_QA,
        TaskType.TYPO_FIX,
        TaskType.LABEL_CLASSIFICATION,
    }

    def __init__(
        self,
        claude: ClaudeAgent | None = None,
        gemma: GemmaAgent | None = None,
        token_threshold: int | None = None,
        config_path: str = "config.yaml",
    ):
        self.claude = claude or ClaudeAgent()
        self.gemma = gemma or GemmaAgent()
        self.token_threshold = token_threshold or int(
            os.getenv("LLM_ROUTER_THRESHOLD", "500")
        )
        self._gemma_available: bool | None = None  # 캐시

        # config.yaml 에서 추가 설정 로드
        try:
            with open(config_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            llm_cfg = cfg.get("llm", {})
            threshold = llm_cfg.get("route_by_tokens", {}).get("threshold")
            if threshold:
                self.token_threshold = threshold
        except FileNotFoundError:
            pass

        logger.info(f"LLMRouter 초기화: threshold={self.token_threshold} tokens")

    def _gemma_ok(self) -> bool:
        """Gemma 사용 가능 여부 (캐싱)"""
        if self._gemma_available is None:
            self._gemma_available = self.gemma.is_available()
            if not self._gemma_available:
                logger.warning("Gemma 사용 불가 → 모든 작업을 Claude로 처리합니다")
        return self._gemma_available

    def _estimate_tokens(self, text: str) -> int:
        """토큰 수 추정 (간단 근사: 4자 = 1토큰)"""
        return len(text) // 4

    def decide(self, prompt: str, task_type: TaskType = TaskType.AUTO) -> RouteDecision:
        """라우팅 결정 로직"""
        est_tokens = self._estimate_tokens(prompt)

        # 1) 명시적 Claude 작업
        if task_type in self.CLAUDE_TASKS:
            return RouteDecision(
                use_claude=True,
                reason=f"작업 유형 '{task_type}' → Claude 전담",
                task_type=task_type,
                estimated_tokens=est_tokens,
            )

        # 2) 명시적 Gemma 작업 (Gemma 가용 시)
        if task_type in self.GEMMA_TASKS and self._gemma_ok():
            return RouteDecision(
                use_claude=False,
                reason=f"작업 유형 '{task_type}' → Gemma 경량 처리",
                task_type=task_type,
                estimated_tokens=est_tokens,
            )

        # 3) AUTO: 토큰 수 기반 판단
        if task_type == TaskType.AUTO:
            if est_tokens < self.token_threshold and self._gemma_ok():
                return RouteDecision(
                    use_claude=False,
                    reason=f"토큰 {est_tokens} < {self.token_threshold} → Gemma",
                    task_type=task_type,
                    estimated_tokens=est_tokens,
                )
            return RouteDecision(
                use_claude=True,
                reason=f"토큰 {est_tokens} ≥ {self.token_threshold} → Claude",
                task_type=task_type,
                estimated_tokens=est_tokens,
            )

        # 4) 기본 폴백: Claude
        return RouteDecision(
            use_claude=True,
            reason="기본 폴백 → Claude",
            task_type=task_type,
            estimated_tokens=est_tokens,
        )

    def ask(
        self,
        prompt: str,
        system: str = "당신은 전문 소프트웨어 엔지니어입니다.",
        task_type: TaskType = TaskType.AUTO,
    ) -> LLMResponse:
        """프롬프트를 적절한 LLM으로 라우팅하여 응답 반환"""
        decision = self.decide(prompt, task_type)

        logger.info(
            f"[Router] {decision.reason} "
            f"(~{decision.estimated_tokens} tokens)"
        )

        if decision.use_claude:
            return self.claude.ask(prompt, system=system, task_type=task_type.value)
        else:
            return self.gemma.ask(prompt, system=system, task_type=task_type.value)

    async def ask_async(
        self,
        prompt: str,
        system: str = "당신은 전문 소프트웨어 엔지니어입니다.",
        task_type: TaskType = TaskType.AUTO,
    ) -> LLMResponse:
        """비동기 라우팅"""
        decision = self.decide(prompt, task_type)
        logger.info(f"[Router async] {decision.reason}")

        if decision.use_claude:
            return await self.claude.ask_async(prompt, system=system, task_type=task_type.value)
        else:
            # Gemma는 동기 전용 → executor에서 실행
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.gemma.ask(prompt, system=system, task_type=task_type.value),
            )

    def stats(self) -> dict:
        """라우터 현재 설정 상태"""
        return {
            "token_threshold": self.token_threshold,
            "gemma_available": self._gemma_ok(),
            "gemma_model": self.gemma.model,
            "claude_model": self.claude.model,
            "claude_tasks": [t.value for t in self.CLAUDE_TASKS],
            "gemma_tasks": [t.value for t in self.GEMMA_TASKS],
        }

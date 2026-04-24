"""
Claude API 에이전트 - 메인 핵심 LLM
복잡한 추론, 아키텍처 설계, 코드 생성에 사용
"""
from __future__ import annotations

import os
from typing import AsyncIterator

import anthropic
from loguru import logger
from pydantic import BaseModel


class ClaudeResponse(BaseModel):
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    task_type: str = ""


class ClaudeAgent:
    """Anthropic Claude API 래퍼 - 핵심 LLM"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int = 8192,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=self.api_key)

        logger.info(f"ClaudeAgent 초기화 완료: model={self.model}")

    # ── 동기 호출 ────────────────────────────────────────────

    def ask(
        self,
        prompt: str,
        system: str = "당신은 전문 소프트웨어 엔지니어입니다.",
        task_type: str = "",
    ) -> ClaudeResponse:
        """단일 프롬프트 응답"""
        logger.debug(f"[Claude] 요청 task={task_type}, 길이={len(prompt)}")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        resp = ClaudeResponse(
            content=message.content[0].text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            task_type=task_type,
        )
        logger.info(
            f"[Claude] 완료: in={resp.input_tokens}, out={resp.output_tokens} tokens"
        )
        return resp

    def chat(
        self,
        messages: list[dict],
        system: str = "당신은 전문 소프트웨어 엔지니어입니다.",
    ) -> ClaudeResponse:
        """멀티턴 대화"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,
        )
        return ClaudeResponse(
            content=message.content[0].text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )

    # ── 비동기 호출 ──────────────────────────────────────────

    async def ask_async(
        self,
        prompt: str,
        system: str = "당신은 전문 소프트웨어 엔지니어입니다.",
        task_type: str = "",
    ) -> ClaudeResponse:
        """비동기 단일 프롬프트 응답"""
        message = await self.async_client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return ClaudeResponse(
            content=message.content[0].text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            task_type=task_type,
        )

    async def stream_async(
        self,
        prompt: str,
        system: str = "당신은 전문 소프트웨어 엔지니어입니다.",
    ) -> AsyncIterator[str]:
        """스트리밍 응답"""
        async with self.async_client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    # ── 전문 태스크 헬퍼 ─────────────────────────────────────

    def review_code(self, code: str, language: str = "python") -> ClaudeResponse:
        """코드 리뷰"""
        prompt = f"""다음 {language} 코드를 리뷰해주세요:

```{language}
{code}
```

다음 관점에서 분석해주세요:
1. 버그 및 잠재적 오류
2. 성능 최적화 기회
3. 보안 취약점
4. 코드 품질 및 가독성
5. 구체적인 개선 제안"""
        return self.ask(prompt, task_type="code_review")

    def design_architecture(self, requirements: str) -> ClaudeResponse:
        """아키텍처 설계"""
        system = "당신은 시니어 소프트웨어 아키텍트입니다. 확장 가능하고 유지보수 가능한 시스템을 설계합니다."
        prompt = f"""다음 요구사항에 맞는 시스템 아키텍처를 설계해주세요:

{requirements}

다음을 포함해주세요:
- 전체 시스템 구조
- 컴포넌트 간 관계
- 데이터 흐름
- 기술 스택 선택 이유
- 확장성 고려사항"""
        return self.ask(prompt, system=system, task_type="architecture_design")

    def generate_docs(self, code: str, language: str = "python") -> ClaudeResponse:
        """문서 자동 생성"""
        prompt = f"""다음 {language} 코드에 대한 문서를 Markdown 형식으로 작성해주세요:

```{language}
{code}
```

포함 내용: 개요, 함수/클래스 설명, 매개변수, 반환값, 사용 예시"""
        return self.ask(prompt, task_type="documentation")

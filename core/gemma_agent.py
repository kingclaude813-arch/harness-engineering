"""
Google Gemma 에이전트 (Ollama 로컬 실행)
가볍고 빠른 작업에 사용 - 토큰 비용 절감
"""
from __future__ import annotations

import os

import httpx
import ollama
from loguru import logger
from pydantic import BaseModel


class GemmaResponse(BaseModel):
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    task_type: str = ""


class GemmaAgent:
    """Ollama를 통한 로컬 Gemma 에이전트 - 경량 LLM"""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("GEMMA_MODEL", "gemma3:4b")
        self.timeout = timeout or int(os.getenv("GEMMA_TIMEOUT", "60"))
        self.client = ollama.Client(host=self.base_url)

        logger.info(f"GemmaAgent 초기화: model={self.model}, url={self.base_url}")

    def is_available(self) -> bool:
        """Ollama 서버 및 모델 사용 가능 여부 확인"""
        try:
            models = self.client.list()
            available = any(self.model in m.model for m in models.models)
            if not available:
                logger.warning(f"모델 '{self.model}'이 없습니다. 'ollama pull {self.model}' 실행 필요")
            return available
        except Exception as e:
            logger.warning(f"Ollama 연결 실패: {e}")
            return False

    def pull_if_needed(self) -> bool:
        """모델이 없으면 자동 다운로드"""
        try:
            models = self.client.list()
            if not any(self.model in m.model for m in models.models):
                logger.info(f"모델 다운로드 중: {self.model} (수 분 소요 가능)")
                self.client.pull(self.model)
                logger.success(f"모델 다운로드 완료: {self.model}")
            return True
        except Exception as e:
            logger.error(f"모델 다운로드 실패: {e}")
            return False

    # ── 동기 호출 ────────────────────────────────────────────

    def ask(
        self,
        prompt: str,
        system: str = "당신은 도움이 되는 AI 어시스턴트입니다.",
        task_type: str = "",
    ) -> GemmaResponse:
        """단일 프롬프트 응답"""
        logger.debug(f"[Gemma] 요청 task={task_type}, 길이={len(prompt)}")
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                options={"temperature": 0.2},
            )
            content = response.message.content
            logger.info(f"[Gemma] 완료: {len(content)} chars")
            return GemmaResponse(
                content=content,
                model=self.model,
                task_type=task_type,
            )
        except Exception as e:
            logger.error(f"[Gemma] 오류: {e}")
            raise

    def chat(self, messages: list[dict]) -> GemmaResponse:
        """멀티턴 대화"""
        response = self.client.chat(
            model=self.model,
            messages=messages,
            options={"temperature": 0.2},
        )
        return GemmaResponse(
            content=response.message.content,
            model=self.model,
        )

    # ── 전문 태스크 헬퍼 (비용 절감용 경량 작업) ──────────────

    def summarize(self, text: str, max_words: int = 150) -> GemmaResponse:
        """텍스트 요약 (경량 작업)"""
        prompt = f"""다음 텍스트를 {max_words}단어 이내로 한국어로 요약해주세요:

{text}"""
        return self.ask(prompt, task_type="summary")

    def classify(self, text: str, categories: list[str]) -> GemmaResponse:
        """텍스트 분류 (경량 작업)"""
        cats = ", ".join(categories)
        prompt = f"""다음 텍스트를 [{cats}] 중 하나로 분류하고, 분류명만 답해주세요:

텍스트: {text}"""
        return self.ask(prompt, task_type="classification")

    def generate_commit_message(self, diff: str) -> GemmaResponse:
        """커밋 메시지 생성 (경량 작업)"""
        prompt = f"""다음 git diff를 보고 간결한 커밋 메시지를 작성해주세요.
형식: <type>(<scope>): <short description>
type: feat, fix, docs, style, refactor, test, chore

diff:
{diff[:2000]}"""
        return self.ask(prompt, task_type="commit_message")

    def answer_simple_qa(self, question: str) -> GemmaResponse:
        """간단한 Q&A (경량 작업)"""
        return self.ask(question, task_type="simple_qa")

    def generate_changelog(self, commits: list[str]) -> GemmaResponse:
        """변경 로그 생성 (경량 작업)"""
        commit_list = "\n".join(f"- {c}" for c in commits)
        prompt = f"""다음 커밋 목록을 사용자 친화적인 변경 로그로 정리해주세요:

{commit_list}

형식: 카테고리별(새기능, 버그수정, 개선, 기타)로 분류해주세요."""
        return self.ask(prompt, task_type="changelog_entry")

"""
Base Agent - 모든 에이전트의 공통 인터페이스
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger


class AgentRole(str, Enum):
    LEADER       = "leader"
    PLAN_MANAGER = "plan_manager"
    DEV_A        = "dev_a"
    DEV_B        = "dev_b"
    INSPECTOR    = "inspector"


class MsgType(str, Enum):
    TASK        = "task"        # 작업 지시
    REPORT      = "report"      # 완료 보고
    QUESTION    = "question"    # 질문/블로커
    ESCALATION  = "escalation"  # 난이도 초과 에스컬레이션
    COMPLETE    = "complete"    # 최종 완료
    REJECT      = "reject"      # 검수 반려


class Priority(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class Difficulty(str, Enum):
    LOW    = "low"     # Gemma
    MEDIUM = "medium"  # Gemma (실패시 Claude 폴백)
    HIGH   = "high"    # Claude


@dataclass
class AgentMessage:
    from_agent: AgentRole
    to_agent:   AgentRole
    msg_type:   MsgType
    content:    dict
    priority:   Priority = Priority.MEDIUM
    cycle_id:   int      = 0
    msg_id:     str      = ""
    timestamp:  datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.msg_id:
            self.msg_id = f"{self.from_agent}-{self.to_agent}-{int(self.timestamp.timestamp())}"

    def summary(self) -> str:
        return (
            f"[{self.msg_type.upper()}] "
            f"{self.from_agent} → {self.to_agent} "
            f"(cycle={self.cycle_id}, priority={self.priority})"
        )


@dataclass
class TaskResult:
    agent:      AgentRole
    task_id:    str
    success:    bool
    output:     str          # 생성된 코드 또는 결과
    file_path:  str = ""     # 저장된 파일 경로
    model_used: str = ""     # 사용된 LLM
    error:      str = ""
    cycle_id:   int = 0


class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""

    def __init__(self, role: AgentRole, message_bus=None):
        self.role = role
        self.bus  = message_bus
        self._inbox: asyncio.Queue[AgentMessage] = asyncio.Queue()
        self.current_cycle = 0
        self.is_busy = False
        logger.info(f"[{self.role.upper()}] 에이전트 초기화")

    def attach_bus(self, bus):
        self.bus = bus

    async def send(self, to: AgentRole, msg_type: MsgType,
                   content: dict, priority: Priority = Priority.MEDIUM):
        """메시지 버스를 통해 다른 에이전트에게 메시지 전송"""
        msg = AgentMessage(
            from_agent=self.role,
            to_agent=to,
            msg_type=msg_type,
            content=content,
            priority=priority,
            cycle_id=self.current_cycle,
        )
        if self.bus:
            await self.bus.publish(msg)
            logger.debug(f"  ✉ {msg.summary()}")
        return msg

    async def receive(self, timeout: float = 60.0) -> AgentMessage | None:
        """인박스에서 메시지 수신"""
        try:
            msg = await asyncio.wait_for(self._inbox.get(), timeout=timeout)
            logger.debug(f"  📨 [{self.role.upper()}] 수신: {msg.summary()}")
            return msg
        except asyncio.TimeoutError:
            return None

    async def put_message(self, msg: AgentMessage):
        """버스가 메시지를 인박스에 직접 넣음"""
        await self._inbox.put(msg)

    @abstractmethod
    async def run(self, *args, **kwargs) -> Any:
        """에이전트 메인 실행 로직 (서브클래스 구현 필수)"""
        ...

    def log(self, msg: str, level: str = "info"):
        getattr(logger, level)(f"[{self.role.upper()}] {msg}")

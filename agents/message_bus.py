"""
Message Bus - 에이전트 간 메시지 라우팅
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from .base_agent import AgentMessage, AgentRole


class MessageBus:
    """에이전트 간 비동기 메시지 라우터"""

    def __init__(self, log_dir: str = "agents/state"):
        self._agents: dict[AgentRole, any] = {}
        self._history: list[AgentMessage] = []
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        logger.info("MessageBus 초기화")

    def register(self, agent):
        """에이전트 등록"""
        self._agents[agent.role] = agent
        agent.attach_bus(self)
        logger.debug(f"  등록: {agent.role}")

    async def publish(self, msg: AgentMessage):
        """메시지를 대상 에이전트의 인박스에 전달"""
        self._history.append(msg)
        target = self._agents.get(msg.to_agent)
        if target:
            await target.put_message(msg)
        else:
            logger.warning(f"미등록 에이전트: {msg.to_agent}")

    def get_history(self, cycle_id: int | None = None) -> list[AgentMessage]:
        if cycle_id is None:
            return self._history
        return [m for m in self._history if m.cycle_id == cycle_id]

    def save_log(self, cycle_id: int):
        """현재 사이클 메시지 로그를 JSON으로 저장"""
        msgs = self.get_history(cycle_id)
        log_data = [
            {
                "from": m.from_agent,
                "to":   m.to_agent,
                "type": m.msg_type,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in msgs
        ]
        path = self._log_dir / f"cycle_{cycle_id:03d}_messages.json"
        path.write_text(
            json.dumps(log_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.debug(f"메시지 로그 저장: {path}")

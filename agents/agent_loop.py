"""
Agent Loop - 목표 달성까지 자동 반복 실행
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from integrations.discord_notifier import DiscordEmbed, DiscordNotifier
from .base_agent import AgentRole, MsgType
from .developer import DeveloperAgent
from .inspector import InspectorAgent
from .leader import LeaderAgent
from .message_bus import MessageBus
from .plan_manager import PlanManagerAgent
from .state_manager import StateManager

load_dotenv()

MAX_CYCLES = 10  # 무한루프 방지 최대 사이클


class AgentOrchestrator:
    """전체 에이전트 팀을 조율하는 오케스트레이터"""

    def __init__(self):
        self.state   = StateManager()
        self.bus     = MessageBus()
        self.discord = self._init_discord()

        # 에이전트 생성
        self.leader  = LeaderAgent(self.state)
        self.pm      = PlanManagerAgent(self.state)
        self.dev_a   = DeveloperAgent(AgentRole.DEV_A, self.state, "agents/workspace/dev_a")
        self.dev_b   = DeveloperAgent(AgentRole.DEV_B, self.state, "agents/workspace/dev_b")
        self.inspector = InspectorAgent(self.state)

        # 버스에 등록
        for agent in [self.leader, self.pm, self.dev_a, self.dev_b, self.inspector]:
            self.bus.register(agent)

        logger.success("AgentOrchestrator 초기화 완료 — 5개 에이전트 준비")

    def _init_discord(self):
        webhook = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook:
            return DiscordNotifier(webhook)
        logger.warning("DISCORD_WEBHOOK_URL 미설정 — Discord 알림 비활성화")
        return None

    async def _notify(self, title: str, desc: str, color: int = 0x5865F2):
        if self.discord:
            self.discord.send_embed(DiscordEmbed(
                title=title, description=desc, color=color,
                footer="Harness Engineering | Agent System"
            ))

    # ══════════════════════════════════════════════════════════
    # 메인 루프
    # ══════════════════════════════════════════════════════════

    async def run(self, goal: str):
        """목표를 받아 달성까지 자동 반복"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 목표: {goal}")
        logger.info(f"{'='*60}\n")

        await self._notify(
            "🚀 에이전트 팀 가동",
            f"**목표:** {goal}\n\n최대 {MAX_CYCLES} 사이클 내 자동 달성합니다.",
            color=0x5865F2,
        )

        inspector_report = {}

        for cycle in range(1, MAX_CYCLES + 1):
            logger.info(f"\n{'─'*50}")
            logger.info(f"  사이클 {cycle} 시작")
            logger.info(f"{'─'*50}")

            cycle_id = self.state.start_cycle()
            for agent in [self.leader, self.pm, self.dev_a, self.dev_b, self.inspector]:
                agent.current_cycle = cycle_id

            await self._notify(
                f"🔄 사이클 {cycle} 시작",
                f"목표를 향해 진행 중...\n**현재 진행률:** {self.state.progress_summary().get('progress_pct', 0)}%",
                color=0x5865F2,
            )

            # ── Step 1: Leader 계획 수립 ──────────────────────
            logger.info("  [1/4] Leader: 계획 수립")
            plan = await self.leader.run(goal) if cycle == 1 else \
                   await self.leader.revise_plan(goal, inspector_report)

            milestones = plan.get("milestones", [])
            if not milestones:
                logger.error("마일스톤 없음 — 중단")
                break

            # ── Step 2: Plan Manager 분배 ─────────────────────
            logger.info("  [2/4] Plan Manager: 병렬 분배")
            # 마일스톤 ID 추가
            for i, m in enumerate(milestones):
                m["id"] = f"M{i+1:02d}"

            tasks = await self.pm.run(milestones, goal)

            # ── Step 3: Dev A & B 병렬 개발 ──────────────────
            logger.info("  [3/4] Dev A & B: 병렬 개발")
            dev_a_tasks = [t for t in tasks if t.assigned_to == "dev_a"]
            dev_b_tasks = [t for t in tasks if t.assigned_to == "dev_b"]

            dev_a_dicts = [{"id": t.id, "title": t.title, "description": t.description, "difficulty": t.difficulty} for t in dev_a_tasks]
            dev_b_dicts = [{"id": t.id, "title": t.title, "description": t.description, "difficulty": t.difficulty} for t in dev_b_tasks]

            results_a, results_b = await asyncio.gather(
                self.dev_a.run(dev_a_dicts),
                self.dev_b.run(dev_b_dicts),
            )
            all_results = results_a + results_b

            success_count = sum(1 for r in all_results if r.success)
            logger.info(f"  개발 완료: {success_count}/{len(all_results)} 성공")

            # ── Step 4: Inspector 검수 ────────────────────────
            logger.info("  [4/4] Inspector: 검수")
            results_dicts = [
                {"task_id": r.task_id, "file_path": r.file_path, "success": r.success, "model": r.model_used}
                for r in all_results
            ]
            inspector_report = await self.inspector.run(milestones, results_dicts, goal)

            score  = inspector_report.get("score", 0)
            passed = inspector_report.get("passed", False)
            issues = inspector_report.get("issues", [])

            self.state.end_cycle(score=score, notes=inspector_report.get("summary", ""))
            self.bus.save_log(cycle_id)

            # Discord 사이클 보고
            progress = self.state.progress_summary()
            bar = "█" * (score // 10) + "░" * (10 - score // 10)
            await self._notify(
                f"📊 사이클 {cycle} 결과",
                f"**점수:** `{bar}` {score}/100\n"
                f"**상태:** {'✅ 통과' if passed else '❌ 반려'}\n"
                f"**이슈:** {len(issues)}건\n"
                f"**진행률:** {progress.get('progress_pct', 0)}%\n\n"
                + (inspector_report.get("summary", "")[:300]),
                color=0x57F287 if passed else 0xFEE75C,
            )

            # ── 완료 판정 ─────────────────────────────────────
            if passed:
                await self._finalize(goal, cycle, inspector_report)
                return

            logger.info(f"  score={score} < 80 — 사이클 {cycle+1} 재시도")
            await asyncio.sleep(3)

        # 최대 사이클 도달
        await self._notify(
            f"⚠️ 최대 사이클({MAX_CYCLES}) 도달",
            f"목표를 완전히 달성하지 못했습니다.\n마지막 점수: {inspector_report.get('score', 0)}/100",
            color=0xED4245,
        )

    async def _finalize(self, goal: str, cycle: int, report: dict):
        """목표 달성 시 마무리 처리"""
        logger.success(f"\n{'='*60}")
        logger.success(f"🎉 목표 달성! ({cycle} 사이클)")
        logger.success(f"{'='*60}")

        # 결과물 수집
        done_tasks = [t for t in self.state.all_tasks if t.status == "done"]
        files = [t.file_path for t in done_tasks if t.file_path]

        await self._notify(
            f"🎉 목표 달성! ({cycle} 사이클)",
            f"**목표:** {goal}\n\n"
            f"**점수:** {report.get('score', 0)}/100\n"
            f"**생성 파일:** {len(files)}개\n\n"
            f"**강점:**\n" + "\n".join(f"• {s}" for s in report.get("strengths", [])[:3]),
            color=0x57F287,
        )

        logger.info(f"생성된 파일 ({len(files)}개):")
        for f in files:
            logger.info(f"  📄 {f}")

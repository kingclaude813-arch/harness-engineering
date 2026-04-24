#!/usr/bin/env python3
"""
Harness Engineering - 멀티 에이전트 실행 진입점

사용법:
  python run_agents.py "목표를 여기에 입력하세요"
  python run_agents.py "FastAPI로 TODO 리스트 REST API를 구현하라"
  python run_agents.py --demo   # 데모 목표로 실행
"""
import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

DEMO_GOAL = (
    "간단한 TODO 리스트 REST API 서버를 FastAPI로 구현한다. "
    "항목 생성/조회/수정/삭제(CRUD) 기능과 단위 테스트를 포함하며 "
    "README.md를 자동으로 작성한다."
)


def setup_logging():
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
    )
    os.makedirs("logs", exist_ok=True)
    logger.add("logs/agents.log", rotation="10 MB", level="DEBUG")


async def main(goal: str):
    from agents import AgentOrchestrator

    console.print(Panel.fit(
        f"[bold cyan]🤖 Harness Multi-Agent System[/bold cyan]\n"
        f"[dim]{goal}[/dim]",
        border_style="cyan",
    ))

    orchestrator = AgentOrchestrator()
    await orchestrator.run(goal)


if __name__ == "__main__":
    setup_logging()

    parser = argparse.ArgumentParser(description="Harness Engineering 멀티 에이전트 실행")
    parser.add_argument("goal", nargs="?", help="달성할 목표")
    parser.add_argument("--demo", action="store_true", help="데모 목표로 실행")
    args = parser.parse_args()

    if args.demo:
        goal = DEMO_GOAL
    elif args.goal:
        goal = args.goal
    else:
        console.print("[yellow]목표를 입력하세요:[/yellow]")
        goal = input("> ").strip()
        if not goal:
            goal = DEMO_GOAL

    asyncio.run(main(goal))

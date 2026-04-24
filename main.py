#!/usr/bin/env python3
"""
Harness Engineering - 메인 진입점
Claude + Gemma + GitHub + Discord 통합 AI 엔지니어링 시스템
"""
import argparse
import os
import sys

from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

console = Console()


def setup_logging(level: str = "INFO"):
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )
    logger.add(
        "logs/harness.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
    )
    os.makedirs("logs", exist_ok=True)


def show_status():
    """현재 시스템 상태 표시"""
    from core import ClaudeAgent, GemmaAgent, LLMRouter

    console.print(Panel.fit(
        "[bold cyan]🚀 Harness Engineering[/bold cyan]\n"
        "[dim]AI 기반 자동화 엔지니어링 허브[/dim]",
        border_style="cyan",
    ))

    table = Table(title="시스템 상태", show_header=True)
    table.add_column("컴포넌트", style="cyan")
    table.add_column("상태", justify="center")
    table.add_column("설정")

    # Claude
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    claude_status = "✅" if api_key else "❌"
    claude_info = f"모델: {os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-6')}" if api_key else "ANTHROPIC_API_KEY 미설정"
    table.add_row("Claude API (메인 LLM)", claude_status, claude_info)

    # Gemma
    try:
        gemma = GemmaAgent()
        gemma_ok = gemma.is_available()
        gemma_status = "✅" if gemma_ok else "⚠️"
        gemma_info = f"모델: {gemma.model}" if gemma_ok else f"ollama pull {gemma.model} 필요"
    except Exception:
        gemma_status = "❌"
        gemma_info = "Ollama 연결 실패"
    table.add_row("Gemma (경량 LLM)", gemma_status, gemma_info)

    # GitHub
    gh_token = os.getenv("GITHUB_TOKEN", "")
    gh_status = "✅" if gh_token else "❌"
    gh_info = f"계정: {os.getenv('GITHUB_USERNAME', '미설정')}" if gh_token else "GITHUB_TOKEN 미설정"
    table.add_row("GitHub", gh_status, gh_info)

    # Discord
    discord_wh = os.getenv("DISCORD_WEBHOOK_URL", "")
    dc_status = "✅" if discord_wh else "❌"
    dc_info = "웹훅 설정됨" if discord_wh else "DISCORD_WEBHOOK_URL 미설정"
    table.add_row("Discord", dc_status, dc_info)

    console.print(table)


def cmd_ask(prompt: str, task: str = "auto"):
    """LLM에게 질문"""
    from core import LLMRouter, TaskType

    router = LLMRouter()
    task_type = TaskType(task) if task in [t.value for t in TaskType] else TaskType.AUTO

    console.print(f"\n[dim]라우팅 중...[/dim]")
    response = router.ask(prompt, task_type=task_type)
    model = getattr(response, "model", "unknown")
    console.print(f"\n[bold green]응답[/bold green] [dim]({model})[/dim]:\n")
    console.print(response.content)


def cmd_setup_github():
    """GitHub 레포 생성 실행"""
    import subprocess
    subprocess.run([sys.executable, "scripts/create_github_repo.py"], check=True)


def cmd_router_stats():
    """LLM 라우터 설정 출력"""
    from core import LLMRouter
    import json

    router = LLMRouter()
    stats = router.stats()
    console.print("\n[bold]LLM 라우터 설정:[/bold]")
    console.print_json(json.dumps(stats, ensure_ascii=False, indent=2))


def main():
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    parser = argparse.ArgumentParser(
        description="Harness Engineering - AI 엔지니어링 자동화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py status                          # 시스템 상태 확인
  python main.py ask "코드 리뷰해줘" --task code_review
  python main.py ask "이 텍스트 요약해줘"        # 자동 라우팅
  python main.py setup-github                    # GitHub 레포 생성
  python main.py router-stats                    # 라우터 설정 확인
        """,
    )

    subparsers = parser.add_subparsers(dest="command")

    # status
    subparsers.add_parser("status", help="시스템 상태 확인")

    # ask
    ask_parser = subparsers.add_parser("ask", help="LLM에게 질문")
    ask_parser.add_argument("prompt", help="질문 내용")
    ask_parser.add_argument(
        "--task",
        default="auto",
        choices=[t.value for t in __import__("core", fromlist=["TaskType"]).TaskType],
        help="작업 유형 (기본: auto)",
    )

    # setup-github
    subparsers.add_parser("setup-github", help="GitHub 레포 생성 및 설정")

    # router-stats
    subparsers.add_parser("router-stats", help="LLM 라우터 통계")

    args = parser.parse_args()

    if args.command == "status" or args.command is None:
        show_status()
    elif args.command == "ask":
        cmd_ask(args.prompt, args.task)
    elif args.command == "setup-github":
        cmd_setup_github()
    elif args.command == "router-stats":
        cmd_router_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

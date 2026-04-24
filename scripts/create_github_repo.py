#!/usr/bin/env python3
"""
GitHub 레포지토리 생성 + Discord 알림 스크립트
python scripts/create_github_repo.py
"""
import os
import sys

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.github_manager import GitHubManager, RepoConfig
from integrations.discord_notifier import DiscordNotifier


def main():
    logger.info("=== GitHub 레포지토리 생성 시작 ===")

    # ── GitHub 연결 ───────────────────────────────────────
    try:
        gh = GitHubManager()
        logger.success(f"GitHub 연결: {gh.user.login}")
    except ValueError as e:
        logger.error(str(e))
        logger.info("'.env' 파일에 GITHUB_TOKEN을 설정해주세요.")
        sys.exit(1)

    # ── 레포 설정 ─────────────────────────────────────────
    repo_name = os.getenv("GITHUB_REPO_NAME", "harness-engineering")
    config = RepoConfig(
        name=repo_name,
        description="🚀 AI 기반 자동화 엔지니어링 허브 (Claude + Gemma + GitHub + Discord)",
        private=False,
        has_issues=True,
        has_projects=True,
        auto_init=True,
        gitignore_template="Python",
        license_template="mit",
    )

    # ── 레포 생성 및 설정 ────────────────────────────────
    repo = gh.full_setup(config)
    logger.success(f"레포 URL: {repo.html_url}")

    # ── Discord 알림 ─────────────────────────────────────
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook:
        try:
            notifier = DiscordNotifier(webhook)
            notifier.send_embed(
                embed=__import__("integrations.discord_notifier", fromlist=["DiscordEmbed"]).DiscordEmbed(
                    title="🎉 새 프로젝트 생성됨!",
                    description=(
                        f"**{repo_name}** 레포지토리가 생성되었습니다.\n\n"
                        f"🔗 {repo.html_url}\n\n"
                        "**포함 기능:**\n"
                        "• Claude API (메인 LLM)\n"
                        "• Gemma 로컬 (경량 LLM)\n"
                        "• GitHub 자동화\n"
                        "• Discord 알림"
                    ),
                    color=0x57F287,
                    url=repo.html_url,
                )
            )
            logger.success("Discord 알림 전송 완료")
        except Exception as e:
            logger.warning(f"Discord 알림 실패: {e}")
    else:
        logger.warning("DISCORD_WEBHOOK_URL 미설정 → Discord 알림 건너뜀")

    # ── GitHub Secrets 안내 ───────────────────────────────
    print("\n" + "=" * 50)
    print("📌 GitHub Actions 시크릿 등록 필요")
    print("=" * 50)
    print(f"  URL: {repo.html_url}/settings/secrets/actions")
    print("\n  등록할 시크릿:")
    print("  • ANTHROPIC_API_KEY")
    print("  • DISCORD_WEBHOOK_URL")
    print("\n  등록 후 Actions 탭에서 워크플로우 활성화:")
    print(f"  {repo.html_url}/actions")
    print("=" * 50 + "\n")

    logger.success("모든 설정 완료!")


if __name__ == "__main__":
    main()

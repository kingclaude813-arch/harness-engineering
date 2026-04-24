"""
Discord 알림 모듈
GitHub 이벤트를 Discord 웹훅으로 전송
"""
from __future__ import annotations

import os
from datetime import datetime
from enum import IntEnum

import httpx
from loguru import logger
from pydantic import BaseModel


class DiscordColor(IntEnum):
    BLUE = 0x5865F2      # 푸시
    GREEN = 0x57F287     # PR 오픈 / 성공
    PURPLE = 0x9B59B6    # PR 머지
    YELLOW = 0xFEE75C    # 이슈
    RED = 0xED4245       # 오류 / 실패
    GRAY = 0x99AAB5      # 기타


class EmbedField(BaseModel):
    name: str
    value: str
    inline: bool = True


class DiscordEmbed(BaseModel):
    title: str
    description: str = ""
    color: int = DiscordColor.BLUE
    url: str = ""
    fields: list[EmbedField] = []
    footer: str = "Harness Engineering Bot"
    timestamp: str = ""

    def to_dict(self) -> dict:
        payload: dict = {
            "title": self.title,
            "color": self.color,
            "footer": {"text": self.footer},
        }
        if self.description:
            payload["description"] = self.description
        if self.url:
            payload["url"] = self.url
        if self.fields:
            payload["fields"] = [f.model_dump() for f in self.fields]
        if self.timestamp:
            payload["timestamp"] = self.timestamp
        else:
            payload["timestamp"] = datetime.utcnow().isoformat()
        return payload


class DiscordNotifier:
    """Discord 웹훅 알림 전송"""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")
        logger.info("DiscordNotifier 초기화 완료")

    def send_embed(
        self,
        embed: DiscordEmbed,
        username: str = "Harness Bot",
        avatar_url: str = "",
    ) -> bool:
        """Discord 임베드 메시지 전송"""
        payload: dict = {
            "username": username,
            "embeds": [embed.to_dict()],
        }
        if avatar_url:
            payload["avatar_url"] = avatar_url

        try:
            resp = httpx.post(self.webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.debug(f"Discord 알림 전송 완료: {embed.title}")
            return True
        except Exception as e:
            logger.error(f"Discord 전송 실패: {e}")
            return False

    def send_text(self, content: str) -> bool:
        """단순 텍스트 메시지 전송"""
        try:
            resp = httpx.post(
                self.webhook_url,
                json={"content": content},
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Discord 텍스트 전송 실패: {e}")
            return False

    # ── GitHub 이벤트별 알림 ─────────────────────────────────

    def notify_push(
        self,
        repo_name: str,
        branch: str,
        pusher: str,
        commits: list[dict],
        compare_url: str = "",
    ) -> bool:
        """Push 이벤트 알림"""
        commit_lines = "\n".join(
            f"• [`{c.get('id', '')[:7]}`]({c.get('url', '')}) {c.get('message', '').splitlines()[0]}"
            for c in commits[:5]
        )
        if len(commits) > 5:
            commit_lines += f"\n... 외 {len(commits) - 5}개 커밋"

        embed = DiscordEmbed(
            title=f"📦 Push to `{branch}`",
            description=commit_lines or "커밋 없음",
            color=DiscordColor.BLUE,
            url=compare_url,
            fields=[
                EmbedField(name="저장소", value=repo_name),
                EmbedField(name="브랜치", value=f"`{branch}`"),
                EmbedField(name="푸셔", value=pusher),
                EmbedField(name="커밋 수", value=str(len(commits))),
            ],
        )
        return self.send_embed(embed)

    def notify_pr_opened(
        self,
        repo_name: str,
        pr_number: int,
        title: str,
        author: str,
        url: str,
        body: str = "",
    ) -> bool:
        """PR 오픈 알림"""
        embed = DiscordEmbed(
            title=f"🔀 PR #{pr_number}: {title}",
            description=body[:300] + "..." if len(body) > 300 else body,
            color=DiscordColor.GREEN,
            url=url,
            fields=[
                EmbedField(name="저장소", value=repo_name),
                EmbedField(name="작성자", value=author),
            ],
        )
        return self.send_embed(embed)

    def notify_pr_merged(
        self,
        repo_name: str,
        pr_number: int,
        title: str,
        merged_by: str,
        url: str,
    ) -> bool:
        """PR 머지 알림"""
        embed = DiscordEmbed(
            title=f"✅ PR #{pr_number} 머지됨: {title}",
            color=DiscordColor.PURPLE,
            url=url,
            fields=[
                EmbedField(name="저장소", value=repo_name),
                EmbedField(name="머지한 사람", value=merged_by),
            ],
        )
        return self.send_embed(embed)

    def notify_issue_created(
        self,
        repo_name: str,
        issue_number: int,
        title: str,
        author: str,
        url: str,
        labels: list[str] | None = None,
    ) -> bool:
        """이슈 생성 알림"""
        embed = DiscordEmbed(
            title=f"🐛 Issue #{issue_number}: {title}",
            color=DiscordColor.YELLOW,
            url=url,
            fields=[
                EmbedField(name="저장소", value=repo_name),
                EmbedField(name="작성자", value=author),
                EmbedField(name="레이블", value=", ".join(labels) if labels else "없음"),
            ],
        )
        return self.send_embed(embed)

    def notify_release(
        self,
        repo_name: str,
        tag: str,
        title: str,
        url: str,
        body: str = "",
    ) -> bool:
        """릴리즈 알림"""
        embed = DiscordEmbed(
            title=f"🚀 릴리즈 {tag}: {title}",
            description=body[:500] if body else "",
            color=DiscordColor.GREEN,
            url=url,
            fields=[EmbedField(name="저장소", value=repo_name, inline=False)],
        )
        return self.send_embed(embed)

    def notify_workflow_failed(
        self,
        repo_name: str,
        workflow_name: str,
        branch: str,
        run_url: str,
    ) -> bool:
        """CI/CD 워크플로우 실패 알림"""
        embed = DiscordEmbed(
            title=f"❌ 워크플로우 실패: {workflow_name}",
            color=DiscordColor.RED,
            url=run_url,
            fields=[
                EmbedField(name="저장소", value=repo_name),
                EmbedField(name="브랜치", value=f"`{branch}`"),
                EmbedField(name="워크플로우", value=workflow_name, inline=False),
            ],
        )
        return self.send_embed(embed)

    def notify_ai_summary(
        self,
        title: str,
        summary: str,
        model_used: str = "Claude",
    ) -> bool:
        """AI 분석 요약 알림"""
        embed = DiscordEmbed(
            title=f"🤖 AI 분석: {title}",
            description=summary[:1800],
            color=DiscordColor.PURPLE,
            footer=f"Harness Bot | {model_used} 사용",
        )
        return self.send_embed(embed)

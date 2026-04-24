"""
Harness Engineering - Discord 양방향 봇
Discord에서 명령어로 GitHub & AI를 제어합니다

명령어:
  !issue <제목>        - GitHub 이슈 생성
  !ask <질문>          - Claude/Gemma에게 질문
  !status              - 레포 현황 조회
  !review <PR번호>     - Claude가 PR 코드 리뷰
  !help                - 명령어 목록
"""
import asyncio
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import LLMRouter, TaskType
from integrations.github_manager import GitHubManager

# ── 봇 설정 ──────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True  # Message Content Intent 필수

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ── 전역 클라이언트 ──────────────────────────────────────────
router: LLMRouter | None = None
gh: GitHubManager | None = None
REPO_NAME = os.getenv("GITHUB_REPO_NAME", "harness-engineering")


def get_router() -> LLMRouter:
    global router
    if router is None:
        router = LLMRouter()
    return router


def get_gh() -> GitHubManager:
    global gh
    if gh is None:
        gh = GitHubManager()
    return gh


# ── 색상 상수 ─────────────────────────────────────────────────
COLOR_OK    = 0x57F287   # 초록
COLOR_INFO  = 0x5865F2   # 파랑
COLOR_WARN  = 0xFEE75C   # 노랑
COLOR_ERROR = 0xED4245   # 빨강
COLOR_AI    = 0x9B59B6   # 보라


# ══════════════════════════════════════════════════════════════
# 이벤트
# ══════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    logger.success(f"Harness Bot 온라인: {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="!help | Harness Engineering"
        )
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ 인수가 부족합니다. `!help` 로 사용법을 확인하세요.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # 알 수 없는 명령어 무시
    else:
        logger.error(f"명령어 오류: {error}")


# ══════════════════════════════════════════════════════════════
# !help
# ══════════════════════════════════════════════════════════════

@bot.command(name="help")
async def help_cmd(ctx):
    """명령어 목록"""
    embed = discord.Embed(
        title="🤖 Harness Bot 명령어",
        color=COLOR_INFO,
    )
    embed.add_field(
        name="📋 GitHub",
        value=(
            "`!issue <제목>` — 이슈 생성\n"
            "`!status` — 레포 현황 조회\n"
            "`!review <PR번호>` — PR 코드 리뷰"
        ),
        inline=False,
    )
    embed.add_field(
        name="🤖 AI",
        value="`!ask <질문>` — Claude/Gemma에게 질문",
        inline=False,
    )
    embed.set_footer(text="Harness Engineering Bot")
    await ctx.send(embed=embed)


# ══════════════════════════════════════════════════════════════
# !issue <제목> [본문]
# ══════════════════════════════════════════════════════════════

@bot.command(name="issue")
async def create_issue(ctx, *, content: str):
    """GitHub 이슈 생성
    사용법: !issue 로그인 버그 수정 필요
           !issue 새 기능 추가 | 상세 내용은 여기에
    """
    # | 구분자로 제목/본문 분리
    if "|" in content:
        title, body = [s.strip() for s in content.split("|", 1)]
    else:
        title = content.strip()
        body = f"Discord에서 생성됨\n작성자: {ctx.author.name}"

    msg = await ctx.send(
        embed=discord.Embed(description="⏳ 이슈 생성 중...", color=COLOR_INFO)
    )
    try:
        issue = get_gh().create_issue(
            repo_name=REPO_NAME,
            title=title,
            body=body,
            labels=["✨ feature"],
        )
        embed = discord.Embed(
            title=f"✅ 이슈 생성됨 #{issue.number}",
            description=f"**{issue.title}**",
            color=COLOR_OK,
            url=issue.url,
        )
        embed.add_field(name="작성자", value=ctx.author.mention)
        embed.add_field(name="링크", value=f"[GitHub에서 보기]({issue.url})")
        await msg.edit(embed=embed)
    except Exception as e:
        await msg.edit(
            embed=discord.Embed(
                title="❌ 이슈 생성 실패",
                description=str(e),
                color=COLOR_ERROR,
            )
        )


# ══════════════════════════════════════════════════════════════
# !ask <질문>
# ══════════════════════════════════════════════════════════════

@bot.command(name="ask")
async def ask_ai(ctx, *, question: str):
    """Claude 또는 Gemma에게 질문
    사용법: !ask Python에서 async/await 설명해줘
    """
    msg = await ctx.send(
        embed=discord.Embed(
            description=f"🤔 **{question[:80]}{'...' if len(question)>80 else ''}**\n\n⏳ 생각 중...",
            color=COLOR_AI,
        )
    )
    try:
        r = get_router()
        response = await r.ask_async(question, task_type=TaskType.AUTO)
        model_name = getattr(response, "model", "AI")
        answer = response.content

        # Discord 2000자 제한 처리
        chunks = [answer[i:i+1800] for i in range(0, len(answer), 1800)]

        embed = discord.Embed(
            title=f"🤖 {model_name}의 답변",
            description=chunks[0],
            color=COLOR_AI,
        )
        embed.set_footer(text=f"질문자: {ctx.author.name} | {model_name}")
        await msg.edit(embed=embed)

        # 답변이 길면 추가 메시지로
        for chunk in chunks[1:]:
            await ctx.send(embed=discord.Embed(description=chunk, color=COLOR_AI))

    except Exception as e:
        await msg.edit(
            embed=discord.Embed(
                title="❌ AI 응답 실패",
                description=str(e),
                color=COLOR_ERROR,
            )
        )


# ══════════════════════════════════════════════════════════════
# !status
# ══════════════════════════════════════════════════════════════

@bot.command(name="status")
async def repo_status(ctx):
    """레포 현황 조회 (오픈 이슈, 최근 커밋)
    사용법: !status
    """
    msg = await ctx.send(
        embed=discord.Embed(description="⏳ GitHub 현황 조회 중...", color=COLOR_INFO)
    )
    try:
        repo = get_gh().get_repo(REPO_NAME)

        # 오픈 이슈 (최대 5개)
        open_issues = list(repo.get_issues(state="open", sort="created", direction="desc"))[:5]
        issue_text = "\n".join(
            f"• [#{i.number}]({i.html_url}) {i.title}" for i in open_issues
        ) or "오픈 이슈 없음 ✨"

        # 최근 커밋 (최대 5개)
        commits = list(repo.get_commits())[:5]
        commit_text = "\n".join(
            f"• [`{c.sha[:7]}`]({c.html_url}) {c.commit.message.splitlines()[0]}"
            for c in commits
        ) or "커밋 없음"

        embed = discord.Embed(
            title=f"📊 {REPO_NAME} 현황",
            color=COLOR_INFO,
            url=repo.html_url,
        )
        embed.add_field(
            name=f"🐛 오픈 이슈 ({repo.open_issues_count}개)",
            value=issue_text,
            inline=False,
        )
        embed.add_field(
            name="📦 최근 커밋",
            value=commit_text,
            inline=False,
        )
        embed.add_field(name="⭐ Stars", value=str(repo.stargazers_count))
        embed.add_field(name="🍴 Forks", value=str(repo.forks_count))
        embed.set_footer(text="Harness Engineering Bot")
        await msg.edit(embed=embed)

    except Exception as e:
        await msg.edit(
            embed=discord.Embed(
                title="❌ 현황 조회 실패",
                description=str(e),
                color=COLOR_ERROR,
            )
        )


# ══════════════════════════════════════════════════════════════
# !review <PR번호>
# ══════════════════════════════════════════════════════════════

@bot.command(name="review")
async def review_pr(ctx, pr_number: int):
    """Claude가 PR을 리뷰하고 Discord에 결과 전송
    사용법: !review 42
    """
    msg = await ctx.send(
        embed=discord.Embed(
            description=f"⏳ PR #{pr_number} 코드 리뷰 중... (Claude 분석 중)",
            color=COLOR_AI,
        )
    )
    try:
        repo = get_gh().get_repo(REPO_NAME)
        pr = repo.get_pull(pr_number)

        # PR diff 가져오기 (최대 3000자)
        files = list(pr.get_files())
        diff_parts = []
        total = 0
        for f in files:
            patch = getattr(f, "patch", "") or ""
            diff_parts.append(f"### {f.filename}\n```diff\n{patch[:800]}\n```")
            total += len(patch)
            if total > 3000:
                diff_parts.append("... (diff 너무 큼, 일부만 리뷰)")
                break

        diff_text = "\n".join(diff_parts)

        prompt = f"""다음 GitHub PR을 리뷰해주세요:

PR 제목: {pr.title}
작성자: {pr.user.login}
브랜치: {pr.head.ref} → {pr.base.ref}

변경 파일 diff:
{diff_text}

다음 항목을 간결하게 분석해주세요:
1. 주요 변경사항 요약
2. 잠재적 버그 또는 문제점
3. 개선 제안 (최대 3가지)
4. 전체 평가 (승인/수정 필요/거절)"""

        from core.claude_agent import ClaudeAgent
        claude = ClaudeAgent()
        response = claude.ask(prompt, task_type="code_review")
        review_text = response.content

        chunks = [review_text[i:i+1800] for i in range(0, len(review_text), 1800)]

        embed = discord.Embed(
            title=f"🔍 PR #{pr_number} 리뷰: {pr.title[:60]}",
            description=chunks[0],
            color=COLOR_AI,
            url=pr.html_url,
        )
        embed.add_field(name="작성자", value=pr.user.login)
        embed.add_field(name="브랜치", value=f"`{pr.head.ref}` → `{pr.base.ref}`")
        embed.set_footer(text="Claude AI 리뷰 | Harness Engineering")
        await msg.edit(embed=embed)

        for chunk in chunks[1:]:
            await ctx.send(embed=discord.Embed(description=chunk, color=COLOR_AI))

    except Exception as e:
        await msg.edit(
            embed=discord.Embed(
                title=f"❌ PR #{pr_number} 리뷰 실패",
                description=str(e),
                color=COLOR_ERROR,
            )
        )


# ══════════════════════════════════════════════════════════════
# 실행
# ══════════════════════════════════════════════════════════════

def main():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("DISCORD_BOT_TOKEN이 .env에 설정되지 않았습니다.")
        sys.exit(1)
    logger.info("Harness Bot 시작 중...")
    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()

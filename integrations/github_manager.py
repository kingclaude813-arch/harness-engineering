"""
GitHub 연동 모듈
레포지토리 생성, 이슈/PR 관리, 자동화 설정
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

from github import Github, GithubException, Repository
from loguru import logger


@dataclass
class RepoConfig:
    name: str
    description: str = ""
    private: bool = False
    has_issues: bool = True
    has_wiki: bool = False
    has_projects: bool = True
    auto_init: bool = True
    gitignore_template: str = "Python"
    license_template: str = "mit"


@dataclass
class IssueInfo:
    number: int
    title: str
    url: str
    state: str
    created_at: datetime
    labels: list[str]


class GitHubManager:
    """GitHub API 래퍼 - 레포 생성 및 자동화"""

    def __init__(
        self,
        token: str | None = None,
        username: str | None = None,
        org: str | None = None,
    ):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN이 설정되지 않았습니다.")

        self.username = username or os.getenv("GITHUB_USERNAME", "")
        self.org = org or os.getenv("GITHUB_ORG", "")

        self.client = Github(self.token)
        self.user = self.client.get_user()
        logger.info(f"GitHubManager 초기화: user={self.user.login}")

    def _get_owner(self):
        """org이 있으면 org, 없으면 개인 계정 반환"""
        if self.org:
            return self.client.get_organization(self.org)
        return self.user

    # ── 레포지토리 관리 ──────────────────────────────────────

    def create_repo(self, config: RepoConfig) -> Repository.Repository:
        """새 GitHub 레포지토리 생성"""
        owner = self._get_owner()
        try:
            repo = owner.create_repo(
                name=config.name,
                description=config.description,
                private=config.private,
                has_issues=config.has_issues,
                has_wiki=config.has_wiki,
                has_projects=config.has_projects,
                auto_init=config.auto_init,
                gitignore_template=config.gitignore_template if config.auto_init else "",
                license_template=config.license_template if config.auto_init else "",
            )
            logger.success(f"레포 생성 완료: {repo.html_url}")
            return repo
        except GithubException as e:
            if e.status == 422:
                logger.warning(f"레포 '{config.name}' 이미 존재 → 기존 레포 반환")
                return self.get_repo(config.name)
            raise

    def get_repo(self, name: str) -> Repository.Repository:
        """레포지토리 가져오기"""
        owner_name = self.org if self.org else self.user.login
        return self.client.get_repo(f"{owner_name}/{name}")

    def setup_branch_protection(self, repo: Repository.Repository, branch: str = "main"):
        """브랜치 보호 규칙 설정"""
        try:
            branch_obj = repo.get_branch(branch)
            branch_obj.edit_protection(
                required_approving_review_count=1,
                dismiss_stale_reviews=True,
                require_code_owner_reviews=False,
            )
            logger.success(f"브랜치 보호 설정: {branch}")
        except Exception as e:
            logger.warning(f"브랜치 보호 설정 실패 (무료 플랜에서 불가): {e}")

    def setup_labels(self, repo: Repository.Repository):
        """기본 이슈 레이블 생성"""
        labels = [
            ("🐛 bug", "d73a4a", "버그 리포트"),
            ("✨ feature", "a2eeef", "새 기능 요청"),
            ("📚 docs", "0075ca", "문서 관련"),
            ("🔧 refactor", "e4e669", "코드 리팩토링"),
            ("🚀 performance", "0e8a16", "성능 개선"),
            ("🔒 security", "b60205", "보안 관련"),
            ("🤖 automation", "5319e7", "자동화 관련"),
            ("📌 priority:high", "e11d48", "높은 우선순위"),
            ("📋 priority:low", "94a3b8", "낮은 우선순위"),
        ]
        existing = {l.name for l in repo.get_labels()}
        for name, color, desc in labels:
            if name not in existing:
                try:
                    repo.create_label(name=name, color=color, description=desc)
                    logger.debug(f"레이블 생성: {name}")
                except Exception:
                    pass
        logger.success(f"레이블 설정 완료: {repo.name}")

    def create_issue_templates(self, repo: Repository.Repository):
        """이슈 템플릿 파일 생성"""
        templates = {
            ".github/ISSUE_TEMPLATE/bug_report.md": """---
name: 🐛 버그 리포트
about: 버그를 발견했나요?
title: '[BUG] '
labels: '🐛 bug'
assignees: ''
---

## 버그 설명
버그에 대한 명확한 설명을 작성해주세요.

## 재현 방법
1. '...' 으로 이동
2. '...' 클릭
3. 에러 발생

## 예상 동작
어떻게 동작해야 하는지 설명해주세요.

## 실제 동작
실제로 어떻게 동작하는지 설명해주세요.

## 환경
- OS: [예: macOS 14]
- Python: [예: 3.12]
- 버전: [예: 0.1.0]
""",
            ".github/ISSUE_TEMPLATE/feature_request.md": """---
name: ✨ 기능 요청
about: 새로운 기능을 제안해주세요
title: '[FEAT] '
labels: '✨ feature'
assignees: ''
---

## 기능 설명
원하는 기능에 대해 설명해주세요.

## 필요한 이유
이 기능이 왜 필요한지 설명해주세요.

## 구현 아이디어 (선택)
어떻게 구현할 수 있을지 아이디어가 있다면 공유해주세요.
""",
        }
        for path, content in templates.items():
            try:
                repo.create_file(path, f"Add {path.split('/')[-1]}", content)
                logger.debug(f"이슈 템플릿 생성: {path}")
            except GithubException as e:
                if e.status != 422:  # 이미 존재하면 무시
                    logger.warning(f"템플릿 생성 실패: {e}")
        logger.success("이슈 템플릿 설정 완료")

    # ── 이슈 / PR 관리 ────────────────────────────────────────

    def get_recent_issues(self, repo_name: str, limit: int = 10) -> list[IssueInfo]:
        """최근 이슈 목록 조회"""
        repo = self.get_repo(repo_name)
        issues = []
        for issue in repo.get_issues(state="open", sort="created", direction="desc")[:limit]:
            issues.append(IssueInfo(
                number=issue.number,
                title=issue.title,
                url=issue.html_url,
                state=issue.state,
                created_at=issue.created_at,
                labels=[l.name for l in issue.labels],
            ))
        return issues

    def create_issue(
        self,
        repo_name: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> IssueInfo:
        """이슈 생성"""
        repo = self.get_repo(repo_name)
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels or [],
        )
        logger.success(f"이슈 생성: #{issue.number} {title}")
        return IssueInfo(
            number=issue.number,
            title=issue.title,
            url=issue.html_url,
            state=issue.state,
            created_at=issue.created_at,
            labels=[l.name for l in issue.labels],
        )

    # ── 레포 초기 설정 원스텝 ─────────────────────────────────

    def full_setup(self, config: RepoConfig) -> Repository.Repository:
        """레포 생성 + 레이블 + 이슈 템플릿 + 브랜치 보호 한 번에"""
        logger.info(f"레포 전체 설정 시작: {config.name}")
        repo = self.create_repo(config)
        self.setup_labels(repo)
        self.create_issue_templates(repo)
        logger.success(f"레포 설정 완료: {repo.html_url}")
        return repo

<<<<<<< HEAD
# 🚀 Harness Engineering

> AI 기반 자동화 엔지니어링 허브 — Claude + Gemma + GitHub + Discord

---

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────┐
│                   LLM Router                        │
│  ┌──────────────────┐    ┌────────────────────────┐ │
│  │  Claude API      │    │  Google Gemma (Ollama) │ │
│  │  (메인 LLM)      │    │  (경량 LLM - 비용 절감) │ │
│  │  복잡한 작업     │    │  요약/분류/커밋 메시지  │ │
│  └──────────────────┘    └────────────────────────┘ │
└─────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌────────────────────────────┐
│  GitHub Manager │      │   Discord Notifier         │
│  - 레포 생성    │ ───► │   - Push / PR / Issue      │
│  - 이슈 관리    │      │   - 주간 리포트             │
│  - 자동화       │      │   - CI/CD 알림             │
└─────────────────┘      └────────────────────────────┘
```

## 빠른 시작

### 1. 초기 세팅

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2. API 키 설정

```bash
# .env 파일에 입력
ANTHROPIC_API_KEY=sk-ant-...          # https://console.anthropic.com
GITHUB_TOKEN=ghp_...                   # https://github.com/settings/tokens
GITHUB_USERNAME=your-username
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### 3. Gemma 로컬 모델 설치

```bash
# Ollama 설치: https://ollama.com
ollama pull gemma3:4b
```

### 4. GitHub 레포 생성

```bash
python scripts/create_github_repo.py
```

### 5. 상태 확인

```bash
python main.py status
```

---

## LLM 라우팅 전략

| 작업 유형 | 사용 모델 | 이유 |
|----------|---------|------|
| 아키텍처 설계 | Claude | 복잡한 추론 필요 |
| 코드 리뷰 | Claude | 깊은 이해 필요 |
| 보안 분석 | Claude | 전문 지식 필요 |
| 텍스트 요약 | Gemma | 가벼운 작업 |
| 커밋 메시지 | Gemma | 단순 생성 |
| 분류 작업 | Gemma | 비용 절감 |
| 기타 (AUTO) | 토큰 수 기준 | 500토큰 임계값 |

---

## GitHub Actions 워크플로우

| 워크플로우 | 트리거 | 기능 |
|-----------|-------|------|
| `discord_notify.yml` | Push / PR / Issue / Release | Discord 실시간 알림 |
| `auto_doc.yml` | Push to main / 매주 월요일 | CHANGELOG 자동 업데이트 + 주간 리포트 |

### GitHub Secrets 등록 필요

```
레포 > Settings > Secrets > Actions:
  ANTHROPIC_API_KEY
  DISCORD_WEBHOOK_URL
```

---

## 사용 예시

```bash
# 시스템 상태 확인
python main.py status

# Claude에게 코드 리뷰 요청
python main.py ask "이 함수를 리뷰해줘: def add(a,b): return a+b" --task code_review

# 자동 라우팅 (Gemma가 처리)
python main.py ask "다음 텍스트 요약해줘: ..."

# LLM 라우터 설정 확인
python main.py router-stats
```

---

## 프로젝트 구조

```
harness-engineering/
├── core/
│   ├── claude_agent.py     # Claude API 래퍼 (메인 LLM)
│   ├── gemma_agent.py      # Gemma/Ollama 래퍼 (경량 LLM)
│   └── llm_router.py       # 자동 LLM 라우터
├── integrations/
│   ├── github_manager.py   # GitHub API 연동
│   └── discord_notifier.py # Discord 웹훅 알림
├── automations/            # 자동화 스크립트
├── scripts/
│   ├── setup.sh            # 초기 세팅 스크립트
│   └── create_github_repo.py # GitHub 레포 생성
├── .github/workflows/
│   ├── discord_notify.yml  # Discord 알림
│   └── auto_doc.yml        # 자동 문서화
├── .env.example            # 환경변수 템플릿
├── config.yaml             # 프로젝트 설정
├── requirements.txt        # Python 의존성
└── main.py                 # 메인 진입점
```

---

마지막 업데이트: 2026-04-21
=======
# harness-engineering
🚀 AI 기반 자동화 엔지니어링 허브 (Claude + Gemma + GitHub + Discord)
>>>>>>> 2f628e4edada149bede406569bdea27f8319fb33

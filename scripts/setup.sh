#!/usr/bin/env bash
# ============================================================
# Harness Engineering - 초기 세팅 스크립트
# ./scripts/setup.sh 로 실행
# ============================================================
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()     { echo -e "${CYAN}[harness]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║    🚀  Harness Engineering Setup          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Python 확인 ────────────────────────────────────────
log "Python 버전 확인..."
if ! command -v python3 &>/dev/null; then
    error "Python 3이 설치되어 있지 않습니다."
fi
PYVER=$(python3 --version)
success "$PYVER 확인됨"

# ── 2. 가상환경 생성 ──────────────────────────────────────
if [ ! -d ".venv" ]; then
    log "가상환경 생성 중..."
    python3 -m venv .venv
    success "가상환경 생성: .venv/"
else
    success "가상환경 이미 존재: .venv/"
fi

# 가상환경 활성화
source .venv/bin/activate

# ── 3. 의존성 설치 ────────────────────────────────────────
log "Python 패키지 설치 중..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
success "패키지 설치 완료"

# ── 4. .env 파일 생성 ────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    warn ".env 파일이 생성되었습니다. 아래 값을 채워주세요:"
    echo ""
    echo "  📌 필수 설정:"
    echo "     ANTHROPIC_API_KEY  → https://console.anthropic.com"
    echo "     GITHUB_TOKEN       → https://github.com/settings/tokens"
    echo "     GITHUB_USERNAME    → 본인 GitHub 사용자명"
    echo "     DISCORD_WEBHOOK_URL → Discord 서버 설정 > 연동 > 웹훅"
    echo ""
else
    success ".env 파일 이미 존재"
fi

# ── 5. Ollama 확인 ────────────────────────────────────────
log "Ollama 확인 중..."
if command -v ollama &>/dev/null; then
    success "Ollama 설치됨: $(ollama --version 2>/dev/null || echo 'version unknown')"

    # Gemma 모델 확인
    if ollama list 2>/dev/null | grep -q "gemma3"; then
        success "Gemma 모델 사용 가능"
    else
        warn "Gemma 모델 없음. 설치하려면:"
        echo "     ollama pull gemma3:4b"
    fi
else
    warn "Ollama가 설치되어 있지 않습니다."
    echo "  설치: https://ollama.com"
    echo "  설치 후: ollama pull gemma3:4b"
fi

# ── 6. Git 초기화 ─────────────────────────────────────────
if [ ! -d ".git" ]; then
    log "Git 초기화..."
    git init
    git add -A
    git commit -m "feat: Harness Engineering 초기 세팅"
    success "Git 초기화 완료"
else
    success "Git 저장소 이미 초기화됨"
fi

# ── 7. 완료 안내 ─────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   ✅  세팅 완료! 다음 단계를 진행하세요   ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  1️⃣  .env 파일에 API 키 입력"
echo "     nano .env"
echo ""
echo "  2️⃣  GitHub 레포 생성"
echo "     python scripts/create_github_repo.py"
echo ""
echo "  3️⃣  메인 실행"
echo "     python main.py --help"
echo ""
echo "  4️⃣  가상환경 활성화 (매 세션마다)"
echo "     source .venv/bin/activate"
echo ""

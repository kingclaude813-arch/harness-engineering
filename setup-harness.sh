#!/bin/bash

# ====================================================
# 멀티 언어 프로젝트 하네스 엔지니어링 최적화
# 로컬 머신 설정 스크립트
# ====================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수 정의
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# 전제 조건 확인
check_requirements() {
    print_header "전제 조건 확인"

    # Node.js 확인
    if ! command -v node &> /dev/null; then
        print_error "Node.js가 설치되지 않았습니다."
        echo "설치: https://nodejs.org/en/download/"
        exit 1
    fi
    print_success "Node.js $(node --version)"

    # npm 확인
    if ! command -v npm &> /dev/null; then
        print_error "npm이 설치되지 않았습니다."
        exit 1
    fi
    print_success "npm $(npm --version)"

    # Git 확인
    if ! command -v git &> /dev/null; then
        print_error "Git이 설치되지 않았습니다."
        echo "설치: https://git-scm.com/downloads"
        exit 1
    fi
    print_success "Git $(git --version | awk '{print $3}')"
}

# API 키 설정
setup_api_key() {
    print_header "Claude API 키 설정"

    if [ -z "$ANTHROPIC_API_KEY" ]; then
        print_info "ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다."
        echo ""
        echo "1. API 키 얻기:"
        echo "   https://console.anthropic.com/api-keys"
        echo ""
        read -p "API 키를 입력하세요 (sk-ant-...): " api_key

        if [ -z "$api_key" ]; then
            print_error "API 키를 입력해야 합니다."
            exit 1
        fi

        # 환경변수 설정 방법 제시
        if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
            shell_rc="$HOME/.bashrc"
            if [[ "$SHELL" == *"zsh"* ]]; then
                shell_rc="$HOME/.zshrc"
            fi

            echo ""
            echo "다음 명령어를 실행하세요:"
            echo "  export ANTHROPIC_API_KEY='$api_key'"
            echo ""
            echo "영구 설정을 위해 $shell_rc에 추가:"
            echo "  echo \"export ANTHROPIC_API_KEY='$api_key'\" >> $shell_rc"
            echo "  source $shell_rc"
            echo ""

            read -p "지금 설정하시겠습니까? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "export ANTHROPIC_API_KEY='$api_key'" >> "$shell_rc"
                source "$shell_rc"
                export ANTHROPIC_API_KEY="$api_key"
                print_success "API 키 설정 완료"
            fi
        fi
    else
        print_success "API 키가 이미 설정되어 있습니다"
    fi
}

# 프로젝트 설정
setup_project() {
    print_header "프로젝트 설정"

    # 프로젝트 경로 입력
    read -p "프로젝트 경로를 입력하세요 (기본값: 현재 디렉토리): " project_path
    project_path=${project_path:-.}

    if [ ! -d "$project_path" ]; then
        print_error "경로가 존재하지 않습니다: $project_path"
        exit 1
    fi

    print_success "프로젝트: $project_path"

    # 의존성 설치
    print_info "의존성 설치 중..."
    if [ ! -f "$project_path/node_modules/@anthropic-ai/sdk/package.json" ]; then
        cd "$project_path"
        npm install @anthropic-ai/sdk --save-dev
        cd -
        print_success "의존성 설치 완료"
    else
        print_success "의존성이 이미 설치되어 있습니다"
    fi

    echo "$project_path" > .project_path
}

# 분석 실행
run_analysis() {
    print_header "프로젝트 분석"

    project_path=$(cat .project_path 2>/dev/null || echo ".")

    echo "분석 방식을 선택하세요:"
    echo "1) 기본 분석 (구조 파악만)"
    echo "2) 최적화 분석 (권장사항 포함)"
    echo "3) 커밋 포함 최적화"
    echo "4) 푸시 포함 완전 자동화"
    echo ""
    read -p "선택 (1-4): " choice

    case $choice in
        1)
            print_info "기본 분석 실행 중..."
            node harness-optimizer.js --project "$project_path" --analyze
            ;;
        2)
            print_info "최적화 분석 실행 중..."
            node harness-optimizer.js --project "$project_path" --optimize
            ;;
        3)
            print_info "최적화 + 자동 커밋 실행 중..."
            node harness-optimizer.js --project "$project_path" --optimize --commit
            ;;
        4)
            print_info "최적화 + 커밋 + 푸시 실행 중..."
            node harness-optimizer.js --project "$project_path" --optimize --commit --push
            ;;
        *)
            print_error "잘못된 선택입니다"
            return 1
            ;;
    esac

    # 리포트 확인
    if [ -f "$project_path/HARNESS_OPTIMIZATION_REPORT.md" ]; then
        print_success "리포트 생성 완료!"
        echo ""
        echo "리포트 보기:"
        echo "  cat $project_path/HARNESS_OPTIMIZATION_REPORT.md"
        echo ""
        read -p "지금 리포트를 확인하시겠습니까? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            less "$project_path/HARNESS_OPTIMIZATION_REPORT.md"
        fi
    fi
}

# 정기 분석 설정
setup_cron() {
    print_header "정기 분석 설정 (선택사항)"

    read -p "정기 분석을 설정하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi

    project_path=$(cat .project_path 2>/dev/null || echo ".")
    script_dir=$(pwd)

    # 크론 작업 생성
    cron_schedule="0 2 * * 1"  # 매주 월요일 오전 2시
    cron_command="cd $script_dir && export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY' && node harness-optimizer.js --project $project_path --optimize --commit"

    # 기존 크론 확인
    if crontab -l 2>/dev/null | grep -q "harness-optimizer"; then
        print_info "이미 크론 작업이 등록되어 있습니다."
        crontab -l | grep "harness-optimizer"
        return
    fi

    # 새 크론 추가
    (crontab -l 2>/dev/null; echo "$cron_schedule $cron_command") | crontab -
    print_success "크론 작업이 등록되었습니다"
    print_info "매주 월요일 오전 2시에 자동으로 분석이 실행됩니다"
}

# GitHub Actions 설정
setup_github_actions() {
    print_header "GitHub Actions 설정 (선택사항)"

    read -p "GitHub Actions를 설정하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi

    project_path=$(cat .project_path 2>/dev/null || echo ".")

    # .github/workflows 디렉토리 생성
    mkdir -p "$project_path/.github/workflows"

    # GitHub Actions 파일 생성
    cat > "$project_path/.github/workflows/harness-optimization.yml" << 'EOF'
name: Weekly Harness Optimization

on:
  schedule:
    - cron: '0 2 * * 1'
  workflow_dispatch:

jobs:
  optimize:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm install @anthropic-ai/sdk

      - name: Run harness optimization
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          node harness-optimizer.js \
            --project ./ \
            --optimize \
            --commit

      - name: Create Pull Request
        if: always()
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: "🔧 optimize: harness engineering improvements"
          title: "🔧 Weekly Harness Optimization"
          body: |
            Automated harness engineering structure optimization
            - Build system analysis
            - Dependency management review
            - Test automation improvements
            - CI/CD pipeline optimization
          branch: auto/harness-optimization
EOF

    print_success "GitHub Actions 파일이 생성되었습니다"
    echo ""
    echo "다음 단계:"
    echo "1. GitHub 저장소의 Settings → Secrets → New repository secret"
    echo "2. Name: ANTHROPIC_API_KEY"
    echo "3. Value: 당신의 Claude API 키"
    echo "4. 변경 사항 커밋 및 푸시"
    echo ""
}

# Makefile 생성
create_makefile() {
    print_header "Makefile 생성 (선택사항)"

    project_path=$(cat .project_path 2>/dev/null || echo ".")

    read -p "Makefile을 생성하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi

    # 기존 Makefile 확인
    if [ -f "$project_path/Makefile" ]; then
        print_info "Makefile이 이미 존재합니다"
        read -p "덮어쓰시겠습니까? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi

    # Makefile 생성
    cat > "$project_path/Makefile" << 'EOF'
# Makefile - 멀티 언어 빌드 하네스

.PHONY: help analyze optimize clean

help:
	@echo "=== 하네스 엔지니어링 최적화 ==="
	@echo "make analyze    - 프로젝트 분석"
	@echo "make optimize   - 최적화 분석"
	@echo "make commit     - 최적화 + 커밋"
	@echo "make push       - 최적화 + 커밋 + 푸시"

analyze:
	node harness-optimizer.js --project . --analyze

optimize:
	node harness-optimizer.js --project . --optimize

commit:
	node harness-optimizer.js --project . --optimize --commit

push:
	node harness-optimizer.js --project . --optimize --commit --push

clean:
	rm -f HARNESS_OPTIMIZATION_REPORT.md
EOF

    print_success "Makefile이 생성되었습니다"
    echo ""
    echo "사용 예:"
    echo "  make analyze   # 프로젝트 분석"
    echo "  make optimize  # 최적화 제안"
    echo "  make commit    # 커밋까지 자동화"
    echo ""
}

# 메인 실행
main() {
    clear
    
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════╗"
    echo "║   🔧 멀티 언어 하네스 엔지니어링 최적화 에이전트  ║"
    echo "║              로컬 머신 설정                   ║"
    echo "╚════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # 단계별 실행
    check_requirements
    setup_api_key
    setup_project
    run_analysis
    setup_cron
    setup_github_actions
    create_makefile

    # 완료
    print_header "✨ 설정 완료!"
    echo ""
    echo "다음 단계:"
    echo "1. HARNESS_OPTIMIZATION_REPORT.md 검토"
    echo "2. Phase 1 구현 시작"
    echo "3. 성과 측정 (빌드 시간, 테스트 커버리지 등)"
    echo "4. 정기적으로 재분석 (매월)"
    echo ""
    print_info "더 자세한 정보는 HARNESS_GUIDE.md를 참고하세요"
    echo ""
}

# 스크립트 실행
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main
fi

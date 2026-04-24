# 🔧 멀티 언어 프로젝트 하네스 엔지니어링 최적화 완전 가이드

## 📚 목차
1. [개념 이해](#개념-이해)
2. [설치](#설치)
3. [기본 사용법](#기본-사용법)
4. [고급 기능](#고급-기능)
5. [실제 사례](#실제-사례)
6. [문제 해결](#문제-해결)

---

## 개념 이해

### 하네스 엔지니어링이란?

**하네스(Harness)**: 여러 프로젝트/언어를 하나의 통합된 빌드 시스템으로 관리하는 구조

```
❌ 현재 상태
├── backend/ (Java + Maven)
├── frontend/ (React + npm)
├── mobile/ (Swift)
├── infra/ (Terraform)
→ 각각 다른 빌드 명령어, 테스트 방식
→ 배포 시 수동 조정 필요
→ 개발자 생산성 저하

✅ 최적화 후
├── Makefile (통합)
├── .github/workflows/ (통합 CI/CD)
├── scripts/ (공유 빌드 스크립트)
→ 한 번의 명령어로 모든 빌드
→ 자동화된 테스트 및 배포
→ 개발자 경험 향상
```

### 핵심 최적화 영역

| 영역 | 현재 | 최적화 후 |
|------|------|---------|
| **빌드 속도** | 순차 실행 (10분) | 병렬 실행 (3분) |
| **테스트** | 수동 실행 | CI/CD 자동화 |
| **의존성** | 언어별 관리 | 통합 관리 |
| **배포** | 수동 배포 | 자동화된 배포 |

---

## 설치

### 1단계: 사전 요구사항

```bash
# Node.js 18 이상
node --version

# Git
git --version

# Claude API 키
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2단계: 에이전트 설치

```bash
# 프로젝트 디렉토리 이동
cd my-multilingual-project

# 파일 복사
cp harness-optimizer.js ./
cp package.json ./

# 의존성 설치
npm install @anthropic-ai/sdk
```

### 3단계: 검증

```bash
# 설치 확인
node harness-optimizer.js --project ./ --analyze
```

---

## 기본 사용법

### 1️⃣ 프로젝트 분석 (변경 없음)

```bash
node harness-optimizer.js --project ./ --analyze
```

**출력 예시:**
```
🌍 감지된 언어:
  • JavaScript (150 파일)
  • Python (80 파일)
  • Java (120 파일)
  • Go (45 파일)

🔨 빌드 시스템:
  • npm (package.json)
  • Maven (pom.xml)
  • Go Modules (go.mod)
  • Python Poetry (poetry.lock)

🧪 테스트 프레임워크:
  • Jest
  • Pytest
  • JUnit

🚀 CI/CD 시스템:
  • GitHub Actions

📦 의존성 관리자:
  • npm
  • maven
  • poetry
```

### 2️⃣ 상세 분석 리포트 생성

```bash
node harness-optimizer.js --project ./ --optimize
```

**생성되는 파일**: `HARNESS_OPTIMIZATION_REPORT.md`

리포트 내용:
- 빌드 하네스 최적화
- 의존성 관리 개선
- 테스트 자동화 권장
- CI/CD 파이프라인 개선
- 구조적 개선 방안
- 구현 로드맵

### 3️⃣ 자동 커밋

```bash
node harness-optimizer.js --project ./ --optimize --commit
```

### 4️⃣ 자동 푸시

```bash
node harness-optimizer.js --project ./ --optimize --commit --push
```

---

## 고급 기능

### 다중 프로젝트 분석

```bash
# 모놀리식 모노레포 분석
node harness-optimizer.js --project ./monorepo \
  --optimize --commit

# 각 서브 프로젝트도 개별 분석
for dir in monorepo/services/*; do
  node harness-optimizer.js --project "$dir" --analyze
done
```

### 정기적 분석

```bash
# 매주 월요일 오전 2시 실행
# crontab -e 에 추가:
0 2 * * 1 cd /path/to/project && \
  node harness-optimizer.js --project . --optimize --commit
```

### GitHub Actions 통합

`.github/workflows/harness-optimization.yml`:

```yaml
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
            - Reviewed build system efficiency
            - Analyzed dependency management
            - Improved test automation
            - Enhanced CI/CD pipeline
```

---

## 실제 사례

### 사례 1: Java + React + Python 마이크로서비스 아키텍처

**프로젝트 구조:**
```
my-platform/
├── backend-api/ (Java + Maven)
├── admin-ui/ (React + npm)
├── ml-service/ (Python + Poetry)
├── worker/ (Go)
└── infra/ (Terraform)
```

**최적화 목표:**
- 통합 빌드 (모든 서비스 한 번에 빌드)
- 병렬 테스트 실행
- 자동화된 배포

**수행 명령어:**
```bash
node harness-optimizer.js \
  --project ./ \
  --optimize \
  --commit \
  --push
```

**예상 개선 사항:**
- 빌드 시간: 15분 → 5분 (67% 단축)
- 테스트 시간: 20분 → 6분 (70% 단축)
- 배포 오류: 30% → 5% (수동 오류 제거)

### 사례 2: 레거시 모놀리식 시스템

**현재 상태:**
```
legacy-system/
├── web/ (Struts + Ant)
├── api/ (Spring + Maven)
├── batch/ (Java + Make)
└── db/ (SQL scripts)
```

**문제점:**
- 4가지 다른 빌드 도구
- 테스트 자동화 없음
- 배포는 완전 수동

**최적화:**
```bash
# 1단계: 분석
node harness-optimizer.js --project ./ --analyze

# 생성된 리포트 검토
cat HARNESS_OPTIMIZATION_REPORT.md

# 2단계: 로드맵 실행
# Phase 1: 통합 빌드 스크립트
# Phase 2: 테스트 자동화 추가
# Phase 3: CI/CD 파이프라인 구축
```

**예상 이득:**
- 신입 개발자 온보딩 시간 50% 단축
- 버그 배포 70% 감소
- 개발자 생산성 40% 향상

### 사례 3: 모노레포 마이그레이션

**Before:** 5개의 독립적인 Git 저장소

**After:** 하나의 모노레포로 통합

```bash
# 각 저장소 분석
for repo in repo1 repo2 repo3 repo4 repo5; do
  node harness-optimizer.js --project /path/to/$repo --analyze
done

# 통합 후 모노레포 전체 분석
node harness-optimizer.js --project ./monorepo --optimize
```

---

## 고급 설정

### 커스텀 빌드 스크립트 생성

`Makefile` (빌드 하네스):

```makefile
# 통합 빌드 하네스

.PHONY: build test deploy clean help

help:
	@echo "=== 멀티 언어 빌드 하네스 ==="
	@echo "make build      - 모든 서비스 빌드"
	@echo "make test       - 모든 테스트 실행"
	@echo "make deploy     - 자동 배포"
	@echo "make clean      - 빌드 아티팩트 제거"

build: build-backend build-frontend build-python build-go
	@echo "✅ 모든 빌드 완료"

build-backend:
	@echo "🔨 Backend 빌드 중..."
	cd backend && mvn clean package

build-frontend:
	@echo "🔨 Frontend 빌드 중..."
	cd frontend && npm install && npm run build

build-python:
	@echo "🔨 Python 서비스 빌드 중..."
	cd ml-service && poetry install && poetry build

build-go:
	@echo "🔨 Go 서비스 빌드 중..."
	cd worker && go build -o worker

test: test-backend test-frontend test-python test-go
	@echo "✅ 모든 테스트 완료"

test-backend:
	cd backend && mvn test

test-frontend:
	cd frontend && npm test

test-python:
	cd ml-service && pytest

test-go:
	cd worker && go test ./...

deploy: build test
	@echo "🚀 배포 시작..."
	# 배포 스크립트

clean:
	find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "target" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true
```

### CI/CD 파이프라인 최적화

`.github/workflows/build-test-deploy.yml`:

```yaml
name: Build Test Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [backend, frontend, ml-service, worker]
    steps:
      - uses: actions/checkout@v4

      - name: Build ${{ matrix.service }}
        run: make build-${{ matrix.service }}

      - name: Test ${{ matrix.service }}
        run: make test-${{ matrix.service }}

  deploy:
    needs: build-and-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: make deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

---

## 문제 해결

### Q1: "빌드 시간이 여전히 느립니다"

```bash
# 병렬 빌드 활성화
make -j4 build  # 4개 코어로 병렬 실행

# 또는 직렬 분석
node harness-optimizer.js --project ./ --analyze

# 리포트의 "buildOptimizations" 섹션 확인
cat HARNESS_OPTIMIZATION_REPORT.md | grep -A 5 "buildOptimizations"
```

### Q2: "의존성 충돌이 많습니다"

```bash
# 의존성 분석
node harness-optimizer.js --project ./ --optimize

# 리포트의 dependencyOptimizations 확인
# 중복 제거 및 버전 통일 수행
```

### Q3: "테스트가 실패합니다"

```bash
# 각 서비스별 테스트 실행
make test-backend    # Backend 테스트만
make test-frontend   # Frontend 테스트만

# 또는 상세 로그
make test-backend VERBOSE=1
```

### Q4: "배포가 실패했습니다"

```bash
# 빌드 + 테스트 + 배포
make deploy

# 로그 확인
git log --oneline | head -5

# 문제 파악 후 수동 배포
make deploy-manual
```

---

## 📈 성과 측정

### 주요 지표

**1. 빌드 시간**
```bash
# 최적화 전
time make build   # 예: 15분

# 최적화 후
time make build   # 예: 5분 (67% 감소)
```

**2. 테스트 커버리지**
```bash
# 리포트 생성
make coverage

# 결과 확인
cat coverage/index.html
```

**3. 배포 성공률**
```bash
# 최근 배포 이력
git log --oneline --grep="deploy" | head -20
```

### 월간 리뷰 체크리스트

- [ ] 빌드 시간 측정
- [ ] 테스트 커버리지 확인
- [ ] 배포 오류율 검토
- [ ] 개발자 생산성 조사
- [ ] 하네스 최적화 재실행
- [ ] 팀 피드백 수집

---

## 🎓 추가 학습

### 추천 읽을거리

1. **Monorepo Handbook**: https://monorepo.tools
2. **12 Factor App**: https://12factor.net
3. **CI/CD Best Practices**: https://www.atlassian.com/continuous-delivery

### 관련 도구

- **Bazel**: Google의 멀티 언어 빌드 시스템
- **Buck2**: Meta의 빠른 빌드 시스템
- **Turborepo**: 모노레포 최적화
- **pnpm**: 패키지 관리자

---

## 💡 팁과 트릭

✅ **Best Practices**:
1. 주 단위로 하네스 최적화 재실행
2. 팀과 함께 리포트 검토
3. 점진적 도입 (한 번에 하나씩)
4. 성과 측정 및 공유

❌ **피해야 할 것**:
1. 모든 변경을 한 번에 적용
2. 테스트 없이 배포
3. 문서화 없는 변경
4. 팀 협의 없는 구조 변경

---

## 🆘 지원

문제가 있으면:
1. `HARNESS_OPTIMIZATION_REPORT.md` 확인
2. 리포트의 우선순위에 따라 해결
3. 각 Phase별로 점진적 적용
4. 정기적 재분석으로 진행 상황 추적

---

**Happy Optimizing! 🚀**

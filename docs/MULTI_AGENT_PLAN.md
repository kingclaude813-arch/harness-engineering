# 🤖 Harness Engineering — 자율 진화형 멀티 에이전트 시스템 기획서

> 하나의 목표를 향해 스스로 계획하고, 분배하고, 개발하고, 검수하며 반복 진화하는 AI 에이전트 팀

---

## 1. 핵심 개념

```
목표(Goal) 입력
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│                      AGENT LOOP                             │
│                                                             │
│  [Leader] ──계획──▶ [Plan Manager] ──분배──▶ [Dev A]        │
│     ▲                     │              ──분배──▶ [Dev B]  │
│     │                     │                                 │
│     └──보고──[Inspector]◀──┴──완료 보고──────────────────── │
│                                                             │
│  ※ 루프는 목표 달성까지 자동 반복                            │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
목표 달성 → GitHub 커밋 + Discord 완료 알림
```

---

## 2. 에이전트 구성 (5개)

### 🎯 Agent 1 — Leader (리더)
| 항목 | 내용 |
|------|------|
| **모델** | Claude Sonnet (항상) |
| **역할** | 목표 해석, 전체 전략 수립, 최종 승인 |
| **입력** | 사용자 목표 텍스트 |
| **출력** | 마일스톤 목록, 우선순위, 성공 기준 |
| **판단 기준** | 검수 에이전트 리포트를 받아 다음 사이클 계획 |

**핵심 동작:**
```
1. 목표를 3~5개 마일스톤으로 분해
2. 각 마일스톤을 Plan Manager에게 전달
3. Inspector 보고서를 받아 달성 여부 판단
4. 미달성 시 → 수정 계획 재수립 (루프)
5. 달성 시 → 완료 선언 및 Discord 보고
```

---

### 📋 Agent 2 — Plan Manager (플랜 매니저)
| 항목 | 내용 |
|------|------|
| **모델** | Claude Haiku (계획 정리) / Gemma (상태 체크) |
| **역할** | 작업 분배, 진행 모니터링, 병렬 조율 |
| **입력** | Leader의 마일스톤 |
| **출력** | 각 Dev 에이전트에게 할당된 서브태스크 |
| **주기** | 매 사이클마다 Dev 에이전트 상태 폴링 |

**핵심 동작:**
```
1. 마일스톤 → 서브태스크로 분해
2. Dev A / Dev B 에게 병렬 할당
3. 30초마다 진행률 체크 (Gemma)
4. 블로커 발생 시 Leader에게 즉시 에스컬레이션
5. 전체 완료 시 Inspector에게 검수 요청
```

---

### 💻 Agent 3 — Developer A (개발자 A)
| 항목 | 내용 |
|------|------|
| **모델** | Gemma (일반 코딩) / Claude (복잡한 로직) |
| **역할** | 핵심 비즈니스 로직, API, 데이터 처리 |
| **전문 영역** | Python 백엔드, 알고리즘 |
| **에스컬레이션** | 난이도 High → 자동으로 Claude로 전환 |

**핵심 동작:**
```
1. 서브태스크 수신 → 난이도 자체 평가
2. Low/Medium → Gemma로 코드 작성
3. High → Claude로 자동 전환
4. 코드 작성 → 파일 저장 → Plan Manager에 완료 보고
5. 막히는 부분 → Plan Manager에 질문 (블로커 등록)
```

---

### 💻 Agent 4 — Developer B (개발자 B)
| 항목 | 내용 |
|------|------|
| **모델** | Gemma (일반 코딩) / Claude (복잡한 로직) |
| **역할** | 테스트 작성, 유틸리티, 통합 작업 |
| **전문 영역** | 테스트 자동화, CI/CD, 문서화 |
| **에스컬레이션** | 난이도 High → 자동으로 Claude로 전환 |

**핵심 동작:**
```
1. Dev A 코드를 받아 테스트 코드 작성
2. 통합 테스트 실행
3. 실패 시 Dev A에게 피드백 전달
4. 성공 시 Inspector에게 결과 전달
```

---

### 🔍 Agent 5 — Inspector (검수관)
| 항목 | 내용 |
|------|------|
| **모델** | Claude Sonnet (정확한 판단 필요) |
| **역할** | 코드 품질 검증, 기획 대비 완성도 평가 |
| **입력** | Leader 기획서 + 개발 결과물 |
| **출력** | 통과/반려 + 구체적 피드백 |

**핵심 동작:**
```
1. Leader 기획서의 성공 기준 확인
2. Dev A/B 결과물 vs 기준 대조
3. 통과 기준:
   - 기능 요구사항 100% 충족
   - 테스트 통과율 ≥ 80%
   - 코드 품질 이슈 없음
4. 통과 → Leader에게 승인 보고
5. 반려 → 구체적 수정 항목과 함께 Plan Manager에 재작업 요청
```

---

## 3. 에이전트 간 통신 프로토콜

### 메시지 구조
```python
@dataclass
class AgentMessage:
    from_agent: str        # "leader" | "plan_manager" | "dev_a" | "dev_b" | "inspector"
    to_agent: str
    msg_type: str          # "task" | "report" | "question" | "escalation" | "complete"
    priority: str          # "low" | "medium" | "high" | "critical"
    content: dict
    timestamp: datetime
    cycle_id: int          # 몇 번째 루프 사이클인지
```

### 통신 흐름
```
사이클 시작
    │
    Leader ──[task]──────────────────▶ Plan Manager
                                            │
                              ┌─────────────┴──────────────┐
                         [task]                         [task]
                              │                             │
                              ▼                             ▼
                          Dev A                          Dev B
                              │                             │
                         [question?] ──▶ Plan Manager       │
                         [complete]  ──▶ Plan Manager ◀──[complete]
                                            │
                                       [review_request]
                                            │
                                            ▼
                                        Inspector
                                            │
                              ┌─────────────┴──────────────┐
                         [pass]                        [reject]
                              │                             │
                              ▼                             ▼
                           Leader                    Plan Manager
                        (다음 마일스톤                (재작업 지시)
                         또는 완료)
```

---

## 4. LLM 라우팅 전략

### 작업 난이도 분류 기준
```python
난이도 LOW  → Gemma
  - 단순 함수 작성 (10줄 미만)
  - 코드 포매팅
  - 변수명 제안
  - 간단한 CRUD
  - 진행 상태 요약

난이도 MEDIUM → Gemma (실패 시 Claude 폴백)
  - 클래스 설계
  - API 엔드포인트 구현
  - 단위 테스트 작성
  - 에러 처리 로직

난이도 HIGH → Claude
  - 아키텍처 설계
  - 복잡한 알고리즘
  - 보안 관련 코드
  - 멀티스레딩/비동기
  - 목표 전략 수립 (Leader)
  - 최종 코드 검수 (Inspector)
```

### 비용 추정
```
일반적인 사이클 1회 기준:
  - Gemma 처리: 80% (무료)
  - Claude 처리: 20% (~$0.01~0.05)
  - 하루 10 사이클 기준: ~$0.1~0.5/일
```

---

## 5. 상태 관리 & 메모리

### 공유 상태 파일 구조
```
agents/
├── state/
│   ├── current_goal.json      # 현재 목표
│   ├── milestones.json        # 마일스톤 목록 및 상태
│   ├── tasks.json             # 서브태스크 할당 현황
│   └── cycle_log.json         # 사이클별 로그
├── workspace/
│   ├── dev_a/                 # Dev A 작업 공간
│   ├── dev_b/                 # Dev B 작업 공간
│   └── reviewed/              # Inspector 승인 완료
└── reports/
    ├── inspector_reports/     # 검수 보고서
    └── weekly_summary/        # 주간 요약
```

---

## 6. 자동 반복 루프 설계

```python
async def agent_loop(goal: str):
    cycle = 0
    while True:
        cycle += 1
        print(f"\n=== 사이클 {cycle} 시작 ===")

        # 1. Leader: 계획 수립
        plan = await leader.create_plan(goal, previous_reports)

        if plan.status == "COMPLETE":
            await discord.notify_complete(goal, cycle)
            break

        # 2. Plan Manager: 병렬 분배
        tasks = await plan_manager.distribute(plan.milestones)

        # 3. Dev A & B: 병렬 개발
        results = await asyncio.gather(
            dev_a.execute(tasks.dev_a_tasks),
            dev_b.execute(tasks.dev_b_tasks),
        )

        # 4. Inspector: 검수
        report = await inspector.review(plan, results)

        # 5. Discord 진행 상황 보고
        await discord.notify_cycle_done(cycle, report)

        # 6. 다음 사이클을 위해 보고서 저장
        previous_reports.append(report)

        # 완료 조건 확인
        if report.pass_rate >= 1.0:
            await discord.notify_complete(goal, cycle)
            break

        await asyncio.sleep(5)  # 다음 사이클 전 대기
```

---

## 7. Discord 실시간 모니터링

### 사이클마다 전송되는 보고
```
📊 사이클 3 진행 보고
──────────────────────
목표: REST API 서버 구축
진행률: ██████░░░░ 60%

✅ 완료: 데이터 모델 설계, 인증 API
🔄 진행중: 비즈니스 로직 (Dev A)
⏳ 대기중: 테스트 작성 (Dev B)
❌ 블로커: JWT 토큰 갱신 로직 (Claude 에스컬레이션 중)

Inspector 점수: 72/100 (목표: 80)
예상 완료: 2 사이클 후
```

---

## 8. 구현 파일 구조

```
agents/
├── __init__.py
├── base_agent.py          # 에이전트 기본 클래스
├── leader.py              # Leader 에이전트
├── plan_manager.py        # Plan Manager 에이전트
├── developer.py           # Developer A/B 공통 클래스
├── inspector.py           # Inspector 에이전트
├── message_bus.py         # 에이전트 간 메시지 큐
├── state_manager.py       # 공유 상태 관리
└── agent_loop.py          # 메인 루프 실행기

run_agents.py              # 실행 진입점
```

---

## 9. 구현 우선순위 (단계별)

### Phase 1 — 기반 구조 (1주)
- [ ] `base_agent.py` — 공통 에이전트 인터페이스
- [ ] `message_bus.py` — 에이전트 간 메시지 전달
- [ ] `state_manager.py` — JSON 기반 공유 상태

### Phase 2 — 핵심 에이전트 (1주)
- [ ] `leader.py` — 목표 분해 및 계획 수립
- [ ] `plan_manager.py` — 병렬 분배 및 모니터링
- [ ] `developer.py` — 코드 생성 (난이도별 라우팅)

### Phase 3 — 품질 & 루프 (3일)
- [ ] `inspector.py` — 코드 검수 및 채점
- [ ] `agent_loop.py` — 자동 반복 루프
- [ ] Discord 실시간 보고 연동

### Phase 4 — 고도화 (지속)
- [ ] 에이전트 메모리 (이전 사이클 학습)
- [ ] 자동 GitHub Issue/PR 생성
- [ ] 성과 대시보드

---

## 10. 첫 번째 목표 (테스트용)

```
목표: "간단한 TODO 리스트 REST API 서버를 FastAPI로 구현한다.
      CRUD 기능과 단위 테스트를 포함하며 README를 자동 작성한다."

성공 기준:
  1. GET/POST/PUT/DELETE 엔드포인트 동작
  2. 테스트 커버리지 80% 이상
  3. README 자동 생성
  4. GitHub 자동 커밋

예상 소요: 3~5 사이클
```

---

*작성일: 2026-04-25 | Harness Engineering v0.1*

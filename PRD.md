# RepoManager — Product Requirements Document (PRD)

## 1. 목적

교육자가 수업·실습마다 생기는 다수 GitHub 저장소를 GUI에서 안전하게 골라 **아카이브**하거나 **삭제**하여 정리한다.

## 2. 사용자

| 구분 | 역할 |
|------|------|
| Primary | GitHub로 실습 저장소를 운영하는 강사 |
| Secondary | Organization 내 실습 repo를 정리하는 TA/관리자 |

## 3. 문제

GitHub 웹 UI는 저장소별 클릭이 많아 수십~수백 개 정리에 비효율적이다.  
잘못된 삭제를 막으려면 **설명·가시성·확인 단계**가 필요하다.

## 4. 목표 / 성공 기준

- Windows / macOS / Linux에서 동일 UX로 동작
- 100개 이상 목록에서 검색·다중선택 가능
- 삭제/아카이브 전 확인창에 **선택된 모든 repo의 이름 + 설명** 표시
- 선택 집합에 대해 Archive/Delete 일괄 실행 + 성공/실패 요약

## 5. 범위 (In — v1)

- 인증된 사용자(및 선택적 org)의 repository 목록
- `description`, private/public, `html_url`, `archived` 여부, `updated_at`
- 다중선택, 필터(이름/설명/visibility/archived), 브라우저 열기
- 일괄 archive / delete + 확인 다이얼로그
- 작업 진행률·결과 로그
- PAT(`.env`) 인증

## 6. 범위 밖 (Out — v1)

- Issues/PR 일괄 삭제
- Collaborator / Actions secrets 관리
- 로컬 clone 디스크 정리
- OAuth App 플로우 (v1은 PAT)

## 7. UX 요구

| 화면 | 요구 |
|------|------|
| 메인 테이블 | 체크박스, Name, Visibility, Description(요약), Updated, Archived |
| 상세 | 더블클릭/상세로 전체 description, URL, 브라우저 열기 |
| 확인 다이얼로그 | 작업 종류, 개수, 목록(이름+설명), Delete는 강한 경고 |
| 결과 | 성공 N / 실패 M + 실패 이유 |

## 8. 비기능 요구

- GitHub API는 백그라운드 스레드 (`QThread` / worker)
- Rate limit 인지(남은 요청 표시 권장)
- 토큰 평문 커밋 금지
- 삭제 시 실수 방지: 확인 문구 입력(예: `DELETE`)은 Nice-to-have

## 9. API 매핑

| 동작 | API |
|------|-----|
| 목록 | `GET /user/repos` (pagination) |
| 아카이브 | `PATCH /repos/{owner}/{repo}` `{ "archived": true }` |
| 삭제 | `DELETE /repos/{owner}/{repo}` |

클라이언트: **PyGithub** (또는 동등 REST).

## 10. 기술 스택

- Python 3.11+
- PySide6
- PyGithub
- python-dotenv
- (후순위) PyInstaller / briefcase 배포

## 11. 디렉터리 구조

```text
repomanager/
├── README.md
├── PRD.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── .env.example
├── src/repomanager/
│   ├── __main__.py
│   ├── app.py
│   ├── config.py
│   ├── models/repository.py
│   ├── services/github_client.py
│   ├── workers/api_worker.py
│   └── ui/
│       ├── main_window.py
│       ├── repo_table.py
│       ├── repo_detail.py
│       └── confirm_dialog.py
└── tests/
```

## 12. 마일스톤 (GitHub Milestones와 1:1)

### Milestone 1 — Project bootstrap
문서·패키지·실행 골격

| Issue | 내용 |
|-------|------|
| 1.1 | README / PRD / LICENSE / .gitignore / .env.example |
| 1.2 | pyproject.toml + PySide6 의존성 |
| 1.3 | `python -m repomanager` 빈 메인 윈도우 |

### Milestone 2 — GitHub 연동
토큰으로 저장소 목록을 모델로 가져오기

| Issue | 내용 |
|-------|------|
| 2.1 | `Repository` 모델 |
| 2.2 | GitHub client: list repos (pagination) |
| 2.3 | 토큰 로드 + 401/403 오류 메시지 |
| 2.4 | QThread로 list 로딩 |

### Milestone 3 — 메인 UI
선택·확인 UX 강화

| Issue | 내용 |
|-------|------|
| 3.1 | 체크박스 테이블 + Public/Private 배지 |
| 3.2 | description 컬럼 + 툴팁/상세 |
| 3.3 | 검색/필터 |
| 3.4 | 더블클릭 → 브라우저 |
| 3.5 | 선택 개수, Select all / Clear |

### Milestone 4 — Archive / Delete
일괄 작업 + 안전 확인

| Issue | 내용 |
|-------|------|
| 4.1 | confirm dialog (name + description) |
| 4.2 | archive API + worker |
| 4.3 | delete API + worker + 강한 경고 |
| 4.4 | 진행률/결과 요약, 목록 새로고침 |
| 4.5 | (선택) 삭제 시 `DELETE` 타이핑 확인 |

### Milestone 5 — Polish & Release

| Issue | 내용 |
|-------|------|
| 5.1 | org 전환 / owner 필터 |
| 5.2 | rate limit 표시, 재시도 |
| 5.3 | 기본 테스트 (client mock) |
| 5.4 | PyInstaller 빌드 메모 |
| 5.5 | v0.1.0 태그/릴리스 |

## 13. 구현 순서

**M1 → M2 → M3 → M4 → M5**  
(문서·골격 → API → UI → 위험 작업 → 배포)

## 14. 확인 다이얼로그 UX

```
⚠ 선택한 N개 저장소를 삭제합니다. 이 작업은 되돌릴 수 없습니다.

• owner/name — "설명"
• ...

[취소]  [영구 삭제]
```

Archive는 “읽기 전용으로 보관 / 이후 unarchive 가능” 문구로 완화한다.

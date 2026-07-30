# RepoManager — Product Requirements Document (PRD)

**버전:** 0.3+ (문서 갱신: 2026-07-30)  
**저장소:** https://github.com/progh2/repomanager  
**라이선스:** MIT

## 1. 목적

교육자가 수업·실습마다 생기는 다수 GitHub 저장소를 GUI에서 안전하게 골라  
**백업 → 아카이브 / 이름 변경 / 공개여부·설명 정리 → 삭제**까지 한곳에서 처리한다.

배경: 십여 년간 SW·Git/GitHub를 가르치며 수업용 저장소가 수백 개 이상 쌓였고,  
웹 UI만으로는 정리가 비효율적이어서 Cursor와 함께 이 도구를 만들었다.

## 2. 사용자

| 구분 | 역할 |
|------|------|
| Primary | GitHub로 실습 저장소를 운영하는 강사 |
| Secondary | Organization 내 실습 repo를 정리하는 TA/관리자 |

## 3. 문제

- GitHub 웹 UI는 저장소별 클릭이 많아 수십~수백 개 정리에 비효율적이다.
- 잘못된 삭제를 막으려면 **설명·가시성·확인 단계·사전 백업**이 필요하다.
- 삭제 후에는 코드·이슈·마일스톤을 되살리기 어렵다.

## 4. 목표 / 성공 기준

- Windows / macOS / Linux에서 동일 UX로 동작 (PySide6)
- 100~500개 이상 목록에서 검색·필터·정렬·다중선택 가능
- 삭제/아카이브/이름 변경 전 확인창에 대상과 경고 표시
- 삭제 전 ZIP 백업(전체 브랜치 + 이슈·마일스톤 메타데이터) 가능
- 선택 집합에 대해 Archive / Unarchive / Delete 일괄 실행 + 성공/실패 요약
- 다국어(ko/en/ja) 및 라이트/다크 테마

## 5. 범위 (In — 현재)

### 5.1 목록·탐색
- 인증된 사용자(owner / org / collaborator) 저장소 목록
- 활성 / 아카이브 이중 목록 + 전송 화살표
- 필드: name, description, private/public, html_url, archived, created_at, updated_at, has_pages, fork
- 필터: 검색, owner, visibility, Pages, Fork
- 정렬: 이름, 업데이트(최신/오래된), 생성(최신/오래된)
- 더블클릭·버튼으로 GitHub / Pages 열기
- 시작 시 로컬 캐시 즉시 표시 + 백그라운드 새로고침
- 로딩 스피너 오버레이, 창·필터 상태 저장

### 5.2 편집
- 설명 수정, AI 추천 설명(GitHub Models / Copilot 권한 시)
- 공개/비공개 토글
- 이름 변경 (`RENAME` 타이핑 확인 + 링크 깨짐 경고)
- 아카이브된 저장소는 이름 변경 비활성

### 5.3 위험 작업·백업
- 일괄 archive / unarchive / delete
- 삭제: `DELETE` 입력, CSV 목록 내보내기, ZIP 백업 버튼
- ZIP 백업: `git clone --mirror`(전체 refs) + `issues.json` / `milestones.json` / `repository.json`
- Git 미설치 시 메타데이터만 백업하고 안내

### 5.4 인증·설정
- PAT, GitHub CLI(`gh auth token`), OAuth Device Flow
- 토큰: OS keyring 우선, 불가 시 QSettings
- 언어(ko/en/ja/시스템), 테마(라이트/다크)
- 삭제 권한(`delete_repo`) 안내

### 5.5 UX 기타
- 단축키: F5 / Ctrl+R 새로고침, Delete 키 → 삭제 확인
- API rate limit 표시, rate limit 시 제한적 재시도
- 크로스플랫폼 실행 스크립트 (`run.bat` / `run.sh`)

## 6. 범위 밖 (Out)

- Issues/PR **일괄 삭제** 또는 이슈 본문의 댓글 전체 아카이브
- Collaborator / Actions secrets / Environments 관리
- 로컬 워크트리·디스크 clone 일괄 삭제
- GitHub Actions를 이용한 CI / 자동 릴리스 빌드 (**의도적으로 사용하지 않음**)
- 코드 서명·스토어 배포 자동화

## 7. UX 요구

| 화면 | 요구 |
|------|------|
| 이중 목록 | 활성 \| →← \| 아카이브, 커스텀 리스트 아이템(배지·날짜·설명) |
| 필터 바 | 검색, owner, visibility, Pages, Fork, 정렬 |
| 상세 패널 | 설명 편집, AI 추천, 공개 토글, 이름 변경, ZIP 백업, Pages/저장소 열기 |
| 확인 다이얼로그 | 작업 종류·개수·목록(이름+설명); Delete는 `DELETE` + CSV/ZIP |
| 이름 변경 다이얼로그 | 링크 깨짐 경고, 새 이름, `RENAME` 입력 |
| 결과 | 성공 N / 실패 M + 실패 이유 (`delete_repo` 부족 시 안내) |
| 설정 | 토큰·언어·테마·OAuth Client ID·삭제 권한 안내 |

## 8. 비기능 요구

- GitHub API·git·백업은 백그라운드 워커 (`QThreadPool` / `QRunnable`)
- Rate limit 인지(상태바 표시)
- 토큰 평문 커밋·바이너리 내장 금지; keyring 우선 저장
- 삭제·이름 변경 실수 방지: 확인 문구 입력 필수
- 앱 사용으로 인한 데이터 손실 책임은 사용자에게 있음 (About 고지)

## 9. API·도구 매핑

| 동작 | 수단 |
|------|------|
| 목록 | `GET /user/repos` (pagination) via PyGithub |
| 아카이브/복원 | `PATCH` `archived` |
| 삭제 | `DELETE /repos/{owner}/{repo}` (`delete_repo`) |
| 설명·공개·이름 | `PATCH` / `repo.edit(...)` |
| Pages | `has_pages` + 추정 URL / Pages API |
| 이슈·마일스톤 백업 | `get_issues(state=all)`, `get_milestones(state=all)` |
| 전체 브랜치 백업 | `git clone --mirror` (토큰 URL) |
| AI 설명 | GitHub Models chat completions |

## 10. 기술 스택

- Python 3.11+
- PySide6
- PyGithub
- python-dotenv, requests, keyring
- pytest (로컬)
- (선택) PyInstaller — **로컬 수동 빌드만** (GitHub Actions 미사용)
- Git CLI — ZIP mirror 백업용

## 11. 디렉터리 구조

```text
repomanager/
├── README.md
├── PRD.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── .env.example
├── run.bat / run.sh
├── src/repomanager/
│   ├── __main__.py
│   ├── app.py
│   ├── config.py
│   ├── i18n.py
│   ├── models/repository.py
│   ├── services/
│   │   ├── github_client.py
│   │   ├── repo_backup.py
│   │   ├── repo_cache.py
│   │   ├── oauth_device.py
│   │   └── ai_assist.py
│   ├── workers/api_worker.py
│   └── ui/
│       ├── main_window.py
│       ├── dual_repo_lists.py
│       ├── repo_detail_panel.py
│       ├── confirm_dialog.py
│       ├── rename_dialog.py
│       ├── settings_dialog.py
│       ├── about_dialog.py
│       ├── loading_overlay.py
│       ├── theme.py
│       ├── styles.qss
│       ├── styles_dark.qss
│       └── assets/icon.png
└── tests/
```

## 12. 마일스톤 (GitHub와 대응)

| 마일스톤 | 상태 | 요약 |
|----------|------|------|
| M1 Project bootstrap | 완료 | 문서·패키지·실행 골격 |
| M2 GitHub integration | 완료 | 목록·토큰·백그라운드 로딩 |
| M3 Main UI | 완료 | 선택·필터·브라우저 열기 |
| M4 Archive / Delete | 완료 | 일괄 작업·확인·DELETE 입력 |
| M5 Polish and Release | 완료 | owner 필터·rate limit·테스트·v0.1.0 |
| M6 Quality and UX | 완료 | i18n·keyring·정렬·Pages/Fork·캐시·다크·단축키 등 |
| M7 Rename and Release | 완료 | 이름 변경(RENAME)·v0.3.0 |
| M8 Backup and disable CI | 완료 | ZIP 백업(브랜치+이슈+마일스톤), Actions 중단 |

세부 이슈는 GitHub Milestones / Issues를 본다.

## 13. 구현 순서 (회고)

**M1 → M2 → M3 → M4 → M5** (초기 v1)  
이후 **M6**(품질·UX) → **M7**(이름 변경) → **M8**(백업·CI 중단).

## 14. 확인·백업 UX 요약

### 삭제
```
⚠ 선택한 N개 저장소를 삭제합니다. 되돌릴 수 없습니다.
• owner/name — "설명"
…
아래에 DELETE 입력
[ZIP으로 백업…] [목록 CSV로 저장] [취소] [영구 삭제]
```

### 이름 변경
```
⚠ URL·git remote·Pages·북마크가 깨질 수 있습니다.
현재 이름 / 새 이름
아래에 RENAME 입력
[취소] [이름 변경]
```

### ZIP 백업
- 폴더 선택 → 저장소마다 `owner-name-backup-….zip`
- 내용: `repository.git/` + `metadata/{repository,issues,milestones}.json`

## 15. 배포·CI 정책

- **GitHub Actions는 저장소에서 비활성화**하고 workflow 파일을 제거한다.
- 배포판은 필요 시 로컬 PyInstaller로 생성한다.
- 과거 Releases에 올라간 바이너리는 참고용으로 남을 수 있다.

## 16. 면책

이 도구는 파괴적 작업(삭제·이름 변경)을 수행한다.  
사용 전 백업을 권장하며, 사용 결과는 사용자 책임이다.

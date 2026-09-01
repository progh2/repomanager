# RepoManager — Product Requirements Document (PRD)

**버전:** 0.4+ (문서 갱신: 2026-09-01)  
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
- Python 설치 없이 내려받아 바로 실행할 수 있는 플랫폼별 실행파일 배포
- 앱이 스스로 새 버전을 확인하고 갱신 (사용자가 재설치할 필요 없음)

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

### 5.6 배포·자동 업데이트
- 플랫폼별 실행파일 배포: Windows `.exe`, macOS `.dmg`, Linux 바이너리
- Python 설치도, 압축 해제도 없이 내려받아 바로 실행 (비개발자 배포 대상 고려)
- 프로젝트 홈페이지(GitHub Pages)에서 OS를 감지해 맞는 파일을 바로 제공
- 앱이 GitHub Releases를 확인해 새 버전을 알림 (시작 후 1일 1회 + 수동 확인)
- 변경 사항 표시 → 다운로드(진행률) → SHA256 검증 → 자기 교체 → 재시작
- 자동 확인 끄기 / 특정 버전 건너뛰기 지원
- 소스 실행이나 쓰기 권한이 없는 위치면 설치 대신 릴리스 페이지 안내

## 6. 범위 밖 (Out)

- Issues/PR **일괄 삭제** 또는 이슈 본문의 댓글 전체 아카이브
- Collaborator / Actions secrets / Environments 관리
- 로컬 워크트리·디스크 clone 일괄 삭제
- 코드 서명(Authenticode / Apple Developer ID) 및 공증, 스토어 배포
- 델타(차등) 업데이트 — 전체 실행파일을 다시 받는다
- 업데이트 서명 검증 — SHA256 체크섬만 확인한다

## 7. UX 요구

| 화면 | 요구 |
|------|------|
| 이중 목록 | 활성 \| →← \| 아카이브, 커스텀 리스트 아이템(배지·날짜·설명) |
| 필터 바 | 검색, owner, visibility, Pages, Fork, 정렬 |
| 상세 패널 | 설명 편집, AI 추천, 공개 토글, 이름 변경, ZIP 백업, Pages/저장소 열기 |
| 확인 다이얼로그 | 작업 종류·개수·목록(이름+설명); Delete는 `DELETE` + CSV/ZIP |
| 이름 변경 다이얼로그 | 링크 깨짐 경고, 새 이름, `RENAME` 입력 |
| 결과 | 성공 N / 실패 M + 실패 이유 (`delete_repo` 부족 시 안내) |
| 설정 | 토큰·언어·테마·OAuth Client ID·삭제 권한 안내·자동 업데이트 토글 |
| 업데이트 다이얼로그 | 새 버전·변경 사항·다운로드 진행률, 설치/건너뛰기/나중에 |

## 8. 비기능 요구

- GitHub API·git·백업은 백그라운드 워커 (`QThreadPool` / `QRunnable`)
- Rate limit 인지(상태바 표시)
- 토큰 평문 커밋·바이너리 내장 금지; keyring 우선 저장
- 삭제·이름 변경 실수 방지: 확인 문구 입력 필수
- 업데이트는 설치 전 SHA256 체크섬을 검증하고, 실패 시 기존 버전을 유지한다
- 자동 업데이트 확인은 하루 1회로 제한하고, 실패해도 조용히 넘어간다
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
| 업데이트 확인 | `GET /repos/{owner}/{repo}/releases/latest` (비인증) |

## 10. 기술 스택

- Python 3.11+
- PySide6
- PyGithub
- python-dotenv, requests, keyring
- pytest — 로컬 + CI(`ci.yml`, 3개 OS)
- PyInstaller, Pillow — 배포판 빌드용 (`pip install -e ".[build]"`)
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
│   │   ├── ai_assist.py
│   │   └── updater.py
│   ├── workers/
│   │   ├── api_worker.py
│   │   └── update_worker.py
│   └── ui/
│       ├── main_window.py
│       ├── dual_repo_lists.py
│       ├── repo_item_delegate.py
│       ├── repo_detail_panel.py
│       ├── confirm_dialog.py
│       ├── rename_dialog.py
│       ├── settings_dialog.py
│       ├── update_dialog.py
│       ├── about_dialog.py
│       ├── loading_overlay.py
│       ├── theme.py
│       ├── styles.qss
│       ├── styles_dark.qss
│       └── assets/icon.png
├── packaging/                 # repomanager.spec, build.py, make_icons.py
├── docs/                      # 홈페이지: index.html, style.css, download.js, mascot.svg
├── .github/workflows/         # ci.yml, release.yml, pages.yml
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
| M9 Executables and auto-update | 완료 | 플랫폼별 실행파일 빌드, 릴리스 워크플로, 자기 업데이트 |

세부 이슈는 GitHub Milestones / Issues를 본다.

## 13. 구현 순서 (회고)

**M1 → M2 → M3 → M4 → M5** (초기 v1)  
이후 **M6**(품질·UX) → **M7**(이름 변경) → **M8**(백업·CI 중단) → **M9**(실행파일·자동 업데이트).

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

M8에서 Actions를 중단했으나, M9에서 **플랫폼별 실행파일 배포와 자동 업데이트**를
도입하며 되돌렸다. 자동 업데이트가 GitHub Releases를 소스로 삼기 때문에
릴리스 자산을 일관된 이름으로 꾸준히 생산할 수단이 필요하다.

- 빌드는 `packaging/build.py` 하나로 통일한다. 로컬에서도, CI에서도 같은 명령을 쓴다.
- 크로스 컴파일은 하지 않는다. 각 OS 러너에서 각각 빌드한다.
  (linux-x86_64, windows-x86_64, macos-arm64, macos-x86_64)
- 배포의 기본 경로는 **GitHub Actions**다. 로컬 빌드는 확인용으로만 쓴다.
  - Actions 탭 → Release → Run workflow: `publish` 옵션으로 태그 생성과
    Release 발행까지 처리한다. 로컬에서 태그를 만들 필요가 없다.
  - `v*` 태그 push도 같은 워크플로로 빌드·배포된다.
- 태그와 `__version__`이 다르면 배포를 중단한다.
- 4개 플랫폼 중 하나라도 빠지면 부분 릴리스를 만들지 않는다.
- 세 플랫폼 모두 업로드 전에 `--selftest`(UI 전체 생성 후 종료 코드 반환)로
  기동을 확인한다. 패키징 실패가 사용자 화면의 오류 창으로 새어나가지 않게 한다.
- 자산 이름은 `RepoManager-<version>-<platform>-<arch>` 형식을 유지한다.
  업데이터가 이 규칙으로 자기 플랫폼용 파일을 고른다.
- 모든 자산의 SHA256을 `SHA256SUMS.txt`로 함께 배포하고, 업데이터가 이를 검증한다.
- 빌드는 서명하지 않는다. 첫 실행 시 OS 경고를 넘기는 방법은 README에 안내한다.
- 워크플로는 GitHub 공식 액션(`actions/*`)만 쓴다. 릴리스 발행은 러너에 기본
  설치된 `gh` CLI로 하여 서드파티 액션 의존을 만들지 않는다. 저장소의 Actions
  허용 범위를 좁게(“Allow actions created by GitHub”) 유지하기 위함이다.
- `ci.yml`은 3개 OS에서 테스트만 돌린다.
- 홈페이지는 `docs/`의 정적 파일이며 `pages.yml`이 GitHub Pages로 배포한다.
  다운로드 링크는 Releases API로 런타임에 해석하므로 릴리스마다 손댈 필요가 없다.

## 16. 면책

이 도구는 파괴적 작업(삭제·이름 변경)을 수행한다.  
사용 전 백업을 권장하며, 사용 결과는 사용자 책임이다.

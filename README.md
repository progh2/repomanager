# RepoManager

수업·실습 후 남는 GitHub 저장소를 GUI에서 골라 **백업·아카이브·이름 변경·삭제**하는 데스크톱 앱입니다.  
Windows, macOS, Linux에서 동작합니다 (PySide6).

![Screenshot](./screenshot.png)

프로젝트: https://github.com/progh2/repomanager

## 기능

### 목록·필터
- 활성 / 아카이브 **이중 목록**과 → ← 이동
- 검색, Owner, 공개범위, **Pages**, **Fork**, 정렬(이름 / 업데이트 / 생성)
- 생성일·업데이트일, Public/Private, 설명, Pages·Fork 아이콘
- 더블클릭 또는 버튼으로 GitHub / Pages 열기
- 로딩 스피너 오버레이, 시작 시 캐시 목록 즉시 표시 후 백그라운드 새로고침
- 창 크기·필터·정렬 상태 기억

### 편집·정리
- 설명 편집, **AI 추천 설명**(GitHub Models / Copilot 권한 시, UI 언어로 생성)
- 공개/비공개 토글
- **이름 변경** — URL·remote·Pages 등이 깨질 수 있다는 경고 + `RENAME` 입력 확인
- 선택 저장소 일괄 아카이브 / 활성 복원 / 삭제
- 삭제·이름 변경 전 확인 창 (`DELETE` / `RENAME` 입력)
- 삭제 전 **CSV 내보내기**, **ZIP 백업**

### ZIP 백업 (삭제 전 권장)
- `git clone --mirror`로 **모든 브랜치·태그** 포함
- Issues / Pull requests / Milestones를 JSON으로 함께 저장
- 상세 패널, 상단 **ZIP 백업**, 삭제 확인 창에서 실행
- 로컬에 Git이 없으면 메타데이터만 저장하고 안내

### 인증·설정·UX
- PAT / GitHub CLI / 웹 로그인(OAuth Device Flow)
- 토큰은 OS 자격 증명 저장소(**keyring**)에 저장
- 다국어 UI: 한국어 / English / 日本語 (시스템 기본)
- 라이트 / 다크 테마
- 단축키: `F5`·`Ctrl+R` 새로고침, `Delete` 삭제 확인
- API rate limit 표시, 백그라운드 워커로 UI 멈춤 방지

## 요구 사항

- Python 3.11+
- GitHub 토큰 (PAT 또는 `gh` / OAuth)
- ZIP 전체 브랜치 백업 시: **Git**이 PATH에 있어야 함

## 빠른 실행 (권장)

```bash
# Windows — 더블클릭 또는 터미널
run.bat

# macOS / Linux
./run.sh
```

첫 실행 시 `.venv` 생성과 의존성 설치를 자동으로 합니다.  
의존성만 다시 설치: `run.bat --update` / `./run.sh --update`

## 수동 설치·실행

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
# 또는: pip install -e ".[dev]"

python -m repomanager
```

선택적으로 `.env`에 토큰을 둘 수 있습니다 (`copy` / `cp .env.example .env`).

```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_OAUTH_CLIENT_ID=Iv1...   # 웹 로그인용(선택)
```

## GitHub 인증

우선순위: 환경변수(`.env`) → 설정에 저장한 토큰 → GitHub CLI(`gh`).

### 1) 설정 메뉴 (권장)

**파일 → 설정** (`Ctrl+,`)

- Personal Access Token 붙여넣기 후 저장
- 또는 **GitHub CLI에서 가져오기**
- 또는 **GitHub 웹으로 로그인** (OAuth Device Flow)

토큰은 Windows Credential Manager / macOS Keychain / Linux Secret Service에 `keyring`으로 저장됩니다.  
keyring을 쓸 수 없으면 Qt `QSettings`로 대체됩니다.

### 2) Classic PAT 권한

| 작업 | 필요 권한 |
|------|-----------|
| 목록·아카이브·설명·이름 변경 | `repo` |
| 삭제 | `delete_repo` (별도) |
| 조직 저장소 | `read:org` (필요 시) |

Fine-grained PAT는 대상 저장소에 **Administration: Read and write**(삭제·이름 변경 등)가 필요할 수 있습니다.

### 3) GitHub CLI로 삭제 권한

```bash
gh auth refresh -h github.com -s delete_repo
```

이후 설정에서 CLI 토큰을 다시 가져오세요. 삭제가 403이면 **도움말 → 삭제 권한 안내**를 참고하세요.

### 4) 웹 로그인 (OAuth Device Flow)

1. https://github.com/settings/developers → **New OAuth App**
2. Homepage: `https://github.com/progh2/repomanager`, Callback: `http://127.0.0.1`
3. Device Flow 활성화 후 **Client ID만** 설정에 입력 (Client Secret은 넣지 마세요)
4. 설정에서 웹 로그인 → 브라우저에 코드 입력

요청 스코프: `repo`, `delete_repo`, `read:org`

## 사용 방법

1. 앱 실행 → 토큰이 없으면 설정 안내 (캐시가 있으면 목록이 바로 표시됨)
2. **파일 → 설정**에서 인증·언어·테마 구성
3. **새로고침** (`F5`)으로 최신 목록 로드
4. 필터·정렬로 대상 좁히기 (예: Fork만, Pages 있음, 오래된 업데이트순)
5. 왼쪽(활성) / 오른쪽(아카이브)에서 선택 → → / ← 로 이동
6. 아래 패널에서 설명·공개여부·이름 변경·Pages·**ZIP 백업**
7. 삭제 전: **ZIP 백업** 또는 CSV 내보내기 → `DELETE` 입력 후 삭제

## ZIP 백업 구조

```text
owner-repo-backup-YYYYMMDD-HHMMSS.zip
├── README.md
├── repository.git/          # bare mirror (전체 브랜치·태그)
│   └── ...
└── metadata/
    ├── repository.json
    ├── issues.json          # issues + PRs
    ├── milestones.json
    └── README.md
```

복원 예:

```bash
git clone repository.git restored-folder
```

## 주의

- **삭제는 되돌릴 수 없습니다.** 삭제 전에 ZIP 백업을 권장합니다.
- 이름 변경 시 GitHub URL, git remote, Pages, 북마크, 다른 저장소의 참조가 깨질 수 있습니다.
- 아카이브는 읽기 전용이며 나중에 활성으로 되돌릴 수 있습니다.
- 이 프로그램을 사용해 발생한 결과는 사용자 책임입니다. (앱 **도움말 → 정보**)

## 배포판 / 패키징

**GitHub Actions CI·자동 릴리스 빌드는 사용하지 않습니다.**  
과거 바이너리는 [Releases](https://github.com/progh2/repomanager/releases)에 남아 있을 수 있습니다.  
새 배포판은 로컬에서 PyInstaller로 만드세요.

```bash
pip install pyinstaller

# Windows
pyinstaller --noconfirm --windowed --name RepoManager ^
  --paths src ^
  --collect-all PySide6 ^
  --add-data "src/repomanager/ui/styles.qss;repomanager/ui" ^
  --add-data "src/repomanager/ui/assets;repomanager/ui/assets" ^
  --icon src/repomanager/ui/assets/icon.png ^
  src/repomanager/__main__.py

# macOS / Linux
pyinstaller --noconfirm --windowed --name RepoManager \
  --paths src \
  --collect-all PySide6 \
  --add-data "src/repomanager/ui/styles.qss:repomanager/ui" \
  --add-data "src/repomanager/ui/assets:repomanager/ui/assets" \
  src/repomanager/__main__.py
```

- 토큰을 바이너리에 넣지 마세요.
- Windows SmartScreen / macOS Gatekeeper는 미서명 실행 파일에 경고할 수 있습니다.

## 테스트

```bash
pytest
```

## 문서·트래킹

- [PRD.md](PRD.md) — 제품 요구사항·범위·마일스톤
- GitHub **Milestones / Issues** — 단계별 과업 (M1–M8)

## 개발 구조

```text
src/repomanager/
  app.py
  config.py                 # 토큰 / keyring / QSettings
  i18n.py                   # ko / en / ja
  models/repository.py
  services/
    github_client.py
    repo_backup.py          # ZIP mirror + issues/milestones
    repo_cache.py
    oauth_device.py
    ai_assist.py
  workers/api_worker.py
  ui/
    main_window.py
    dual_repo_lists.py
    repo_detail_panel.py
    confirm_dialog.py
    rename_dialog.py
    settings_dialog.py
    loading_overlay.py
    styles.qss / styles_dark.qss
```

## 라이선스

MIT — [LICENSE](LICENSE)

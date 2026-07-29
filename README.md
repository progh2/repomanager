# RepoManager

수업·실습 후 남는 GitHub 저장소를 GUI에서 골라 **아카이브**하거나 **삭제**하는 데스크톱 앱입니다.  
Windows, macOS, Linux에서 동작합니다 (PySide6).

## 기능

- 설정 메뉴에서 PAT / GitHub CLI / 웹 로그인(Device Flow)
- 인증된 계정의 저장소 목록 불러오기 (owner / organization / collaborator)
- **Public / Private**, 설명(description), 이름·소유자, 업데이트 시각 표시
- 검색·**Owner**·가시성·Archived 필터, 다중 선택
- 행 더블클릭 시 브라우저에서 GitHub 페이지 열기
- 선택 저장소 **일괄 Archive / Delete**
- 실행 전 확인 창(이름 + 설명 + 경고, 삭제는 `DELETE` 입력)
- API rate limit 표시, rate limit 시 제한적 재시도
- API 호출은 백그라운드 스레드로 처리 (UI 멈춤 방지)

## 요구 사항

- Python 3.11+
- GitHub Personal Access Token

## 설치

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
# 또는 개발 설치
pip install -e ".[dev]"

copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

`.env`에 토큰을 넣습니다.

```env
GITHUB_TOKEN=ghp_your_token_here
```

## 실행

```bash
python -m repomanager
```

## GitHub 인증

다음 중 하나로 인증합니다 (우선순위: 환경변수 → Settings 저장 토큰 → `gh`).

### 1) 설정 메뉴 (권장)

앱 실행 후 **File → Settings** (`Ctrl+,`) 또는 **Account → GitHub credentials**.

- **Personal Access Token** 붙여넣기 후 Save
- 또는 **Import from GitHub CLI** (`gh auth login` 되어 있을 때)
- 또는 **Sign in with GitHub (browser)** — OAuth Device Flow (아래)

토큰은 OS 사용자 설정의 Qt `QSettings`에 저장됩니다 (`.env`보다 편함).

### 2) `.env` / 환경변수

```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_OAUTH_CLIENT_ID=Iv1...   # 웹 로그인용(선택)
```

### 3) 웹 로그인 (OAuth Device Flow)

브라우저 로그인은 가능하지만, **GitHub OAuth App의 Client ID**가 필요합니다.  
(일반 웹사이트처럼 “아무 앱이나” 바로 로그인하는 방식은 GitHub가 허용하지 않습니다.)

1. https://github.com/settings/developers → **New OAuth App**
2. Application name: `RepoManager` (자유)
3. Homepage URL: `https://github.com/progh2/repomanager`
4. Authorization callback URL: `http://127.0.0.1`
5. 생성 후 **Device Flow** 활성화, **Client ID**만 Settings에 입력  
   (**Client Secret은 데스크톱 앱에 넣지 마세요**)
6. Settings에서 **Sign in with GitHub** → 브라우저에 표시된 코드 입력

요청 스코프: `repo`, `delete_repo`, `read:org`

### GitHub CLI로 삭제 권한 추가

`gh` 기본 로그인에는 `delete_repo`가 없는 경우가 많습니다. 삭제가 403이면:

```bash
gh auth refresh -h github.com -s delete_repo
```

그다음 앱 Settings에서 **Import from GitHub CLI** 또는 Prefer gh CLI를 켠 뒤 다시 시도하세요.

## 사용 방법

1. 앱 실행 → 토큰이 없으면 Settings 안내
2. **File → Settings**에서 인증 구성 후 Save
3. **Refresh**로 저장소 목록 로드
4. Owner / Public·Private / Archived 필터와 검색으로 대상 좁히기
5. 설명·가시성 확인, 필요 시 행을 더블클릭해 GitHub에서 확인
6. 체크박스로 여러 저장소 선택
7. **Archive** 또는 **Delete** 클릭
8. 확인 창에서 이름·설명 검토 (삭제는 `DELETE` 입력 필요)
9. 진행률과 성공/실패 요약 확인 후 목록이 자동 새로고침됩니다
10. 상태바에서 Auth 소스와 API rate limit을 확인합니다

## 주의

- **삭제는 되돌릴 수 없습니다.**
- 아카이브는 읽기 전용으로 남기며, 나중에 GitHub에서 unarchive할 수 있습니다.

## 패키징 (PyInstaller)

개발용 실행이 우선이며, 단일 실행 파일이 필요하면 PyInstaller를 사용할 수 있습니다.

```bash
pip install pyinstaller

# Windows / Linux (onedir 권장 — Qt 플러그인 경로 이슈가 적음)
pyinstaller --noconfirm --windowed --name RepoManager ^
  --paths src ^
  --collect-all PySide6 ^
  src/repomanager/__main__.py

# macOS
pyinstaller --noconfirm --windowed --name RepoManager \
  --paths src \
  --collect-all PySide6 \
  src/repomanager/__main__.py
```

결과물은 `dist/RepoManager/` 에 생성됩니다.

참고:

- `.env`는 실행 파일 옆에 두거나, 실행 전 환경 변수 `GITHUB_TOKEN`을 설정하세요.
- 토큰을 바이너리에 넣지 마세요.
- 코드 서명(macOS Gatekeeper, Windows SmartScreen)은 배포 환경에 맞게 별도 설정이 필요합니다.
- 문제가 있으면 `--onedir`을 유지하고, 필요 시 `--hidden-import=PySide6.QtWidgets` 를 추가하세요.

## 테스트

```bash
pytest
```

## 프로젝트 문서

- [PRD.md](PRD.md) — 제품 요구사항, 범위, 마일스톤
- GitHub **Milestones / Issues** — 단계별 과업

## 개발 구조

```text
src/repomanager/
  app.py                 # QApplication 진입
  config.py              # 토큰/설정
  models/repository.py   # Repo DTO
  services/github_client.py
  workers/api_worker.py
  ui/main_window.py
```

## 라이선스

MIT — [LICENSE](LICENSE)

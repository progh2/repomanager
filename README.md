# RepoManager

수업·실습 후 남는 GitHub 저장소를 GUI에서 골라 **백업·아카이브·이름 변경·삭제**하는 데스크톱 앱입니다.  
Windows, macOS, Linux에서 동작합니다 (PySide6).

![Screenshot](./screenshot.png)

프로젝트: https://github.com/progh2/repomanager

## 내려받기

**홈페이지: https://progh2.github.io/repomanager/** — 운영체제를 알아서 감지해
맞는 파일을 바로 받을 수 있습니다.

직접 고르려면 [Releases](https://github.com/progh2/repomanager/releases/latest)에서
받으세요. 압축 파일이 아니라 **바로 실행되는 파일**입니다.

| 플랫폼 | 파일 | 실행 방법 |
|--------|------|-----------|
| Windows | `RepoManager-<버전>-windows-x86_64.exe` | 더블클릭 |
| macOS (Apple Silicon) | `RepoManager-<버전>-macos-arm64.dmg` | 더블클릭 → Applications로 끌어놓기 |
| macOS (Intel) | `RepoManager-<버전>-macos-x86_64.dmg` | 더블클릭 → Applications로 끌어놓기 |
| Linux | `RepoManager-<버전>-linux-x86_64` | `chmod +x` 후 실행 |

`SHA256SUMS.txt`로 무결성을 확인할 수 있습니다 (`sha256sum -c SHA256SUMS.txt`).

미서명 빌드라 첫 실행 시 경고가 나옵니다.

- **Windows**: SmartScreen → *추가 정보* → *실행*
- **macOS**: 앱을 한 번 실행해 차단당한 뒤,
  **시스템 설정 → 개인정보 보호 및 보안**을 열고 아래쪽의 **확인 없이 열기**를 누릅니다.
  (터미널이 편하면 `xattr -dr com.apple.quarantine /Applications/RepoManager.app`)

  > macOS 15(Sequoia)부터 **우클릭 → 열기** 우회가 제거되어 위 방법을 써야 합니다.
  > macOS 14 이하에서는 우클릭 → *열기* → *열기* 도 됩니다.
- **Linux**: `chmod +x RepoManager-*-linux-x86_64`

설치 후에는 앱이 스스로 새 버전을 확인하고 업데이트합니다 (아래 참조).

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
- 단축키: `F5`·`Ctrl+R` 새로고침, `Delete` 삭제 확인, `Ctrl+,` 설정, `Ctrl+Q` 종료
- API rate limit 표시, 백그라운드 워커로 UI 멈춤 방지
- **자동 업데이트** — 새 릴리스를 확인해 내려받고 스스로 교체 후 재시작

## 요구 사항

- 실행파일로 쓸 때는 Python이 필요 없습니다.
- 소스에서 실행할 때: Python 3.11+
- GitHub 토큰 (PAT 또는 `gh` / OAuth)
- ZIP 전체 브랜치 백업 시: **Git**이 PATH에 있어야 함

## 소스에서 실행

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
8. 새 버전이 나오면 시작 시 알림 — **도움말 → 업데이트 확인**으로 직접 확인도 가능

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

## 자동 업데이트

실행파일로 설치한 경우 앱이 스스로 최신 릴리스로 갈아탑니다.

- **자동 확인** — 시작 후 잠시 뒤, 하루에 한 번 GitHub Releases를 확인합니다.
- **수동 확인** — **도움말 → 업데이트 확인** 또는 **설정 → 업데이트 → 지금 확인**
- **끄기** — **설정 → 업데이트**에서 자동 확인 체크 해제
- 업데이트 창에서 변경 사항을 확인하고 **다운로드 후 설치**를 누르면
  내려받기 → `SHA256SUMS.txt` 검증 → 앱 종료 → 교체 → 자동 재시작 순으로 진행됩니다.
- 특정 버전을 넘기려면 **이 버전 건너뛰기**를 누르세요 (자동 확인에서만 무시).

플랫폼별 교체 방식:

| 플랫폼 | 교체 대상 |
|--------|-----------|
| Windows | 실행 중이던 `.exe`를 새 파일로 덮어씀 |
| macOS | `.dmg`를 마운트해 `RepoManager.app` 번들을 교체하고 quarantine 속성 제거 |
| Linux | 실행 파일을 같은 디렉터리에 받아 원자적으로 교체 |

소스에서 실행 중이거나 설치 위치에 쓰기 권한이 없으면 설치 버튼 대신
릴리스 페이지 링크가 표시됩니다. (`git pull`로 업데이트하세요.)

## 배포·릴리스

플랫폼별 실행파일은 GitHub Actions에서 만드는 것이 기본입니다.
크로스 컴파일이 안 되므로 로컬 빌드는 해당 OS에서만, 확인용으로 씁니다.

### 1) GitHub Actions (권장)

로컬에 Windows·macOS·Linux를 다 갖출 필요 없이
`.github/workflows/release.yml`이 4개 플랫폼을 GitHub 러너에서 빌드합니다
(`ubuntu-22.04`, `windows-latest`, `macos-15`, `macos-15-intel`).
Linux는 glibc 호환 범위를 넓히려고 일부러 오래된 이미지를 씁니다.
**자동 업데이트가 이 릴리스를 읽습니다.**

#### 최초 1회 저장소 설정

이 저장소는 Actions 실행 범위가 `local_only`(저장소 자체 액션만 허용)로
제한돼 있어, 그대로 두면 `actions/checkout`조차 차단됩니다.
**Settings → Actions → General → Actions permissions**에서

> Allow progh2, and select non-progh2, actions and reusable workflows
> → ☑ **Allow actions created by GitHub**

를 켜주세요. 워크플로가 쓰는 액션은 전부 GitHub 공식(`actions/*`)이라
이것만으로 충분합니다. 서드파티 마켓플레이스 액션은 쓰지 않습니다
(릴리스 발행도 러너에 기본 설치된 `gh` CLI로 합니다).

홈페이지를 쓰려면 **Settings → Pages → Source: GitHub Actions**도 한 번 켜야 합니다.

**Actions 탭에서 실행 — 로컬 작업 없음**

1. 먼저 `src/repomanager/__init__.py`의 `__version__`과
   `pyproject.toml`의 `version`을 올려 push합니다.
2. GitHub → **Actions** → **Release** → **Run workflow**
3. 옵션을 고르고 실행합니다.

   | 입력 | 뜻 |
   |------|-----|
   | `publish` | 체크하면 Release까지 생성. 해제하면 빌드 아티팩트만 |
   | `tag` | 비워두면 `v<__version__>` 사용 |
   | `draft` | 초안으로 만들기 |
   | `prerelease` | 프리릴리스로 표시 |

   `publish`를 체크하면 태그를 로컬에서 만들 필요 없이
   해당 커밋에 태그가 생성되고 Release가 올라갑니다.
   체크하지 않으면 4종 바이너리를 아티팩트로만 받아 확인할 수 있습니다(14일 보관).

**태그 push**

```bash
git tag v0.4.1
git push origin v0.4.1     # 빌드 + 배포가 자동 실행
```

어느 쪽이든 태그가 `__version__`과 다르면 배포를 중단하고,
4개 플랫폼 중 하나라도 빠지면 부분 릴리스를 만들지 않습니다.
세 플랫폼 모두 업로드 전에 `--selftest`로 실제 기동을 확인합니다
(UI를 전부 만들고 종료 코드로 성공/실패를 알립니다).

에셋 이름은 `RepoManager-<버전>-<플랫폼>-<아키텍처>` 형식을 지켜야 합니다.
업데이터가 이 이름으로 자기 플랫폼용 파일을 고릅니다.

### 2) 로컬 빌드

```bash
pip install -r requirements.txt
pip install "pyinstaller>=6.6" "pillow>=10.0"   # 또는: pip install -e ".[build]"

python packaging/build.py
```

결과물은 `dist/release/`에 생깁니다.

```text
dist/release/
├── RepoManager-0.4.1-linux-x86_64      # 또는 -windows-x86_64.exe / -macos-arm64.dmg
└── SHA256SUMS.txt
```

- `packaging/repomanager.spec` — PyInstaller 설정 (아이콘, 데이터 파일, Qt 모듈 제외)
- `packaging/build.py` — 아이콘 생성 → PyInstaller 실행 → 이름 정리 → 체크섬
- `packaging/make_icons.py` — `icon.png` → `.ico` / `.icns`

### 주의

- 토큰을 바이너리에 넣지 마세요.
- 빌드는 서명되지 않습니다. Windows SmartScreen / macOS Gatekeeper 경고는
  위 [내려받기](#내려받기) 절의 안내대로 넘어갈 수 있습니다.
- 릴리스를 새로 올리면 기존 사용자에게는 하루 안에 업데이트 알림이 뜹니다.

## 테스트

```bash
pip install -r requirements.txt
pytest
```

헤드리스 환경(서버·컨테이너)에서는 Qt 플랫폼 플러그인을 오프스크린으로 지정합니다.

```bash
QT_QPA_PLATFORM=offscreen pytest
```

`.github/workflows/ci.yml`이 push·PR마다 Linux / Windows / macOS에서 같은 테스트를 돌립니다.

## 홈페이지

`docs/`가 곧 홈페이지입니다 (https://progh2.github.io/repomanager/).
빌드 도구 없는 정적 HTML/CSS/JS라 파일을 그대로 열어서 확인할 수 있습니다.

```bash
python -m http.server -d docs 8000    # http://localhost:8000
```

- `download.js`가 GitHub Releases API로 최신 자산을 찾아 방문자 OS에 맞는
  다운로드 버튼을 만듭니다. API 호출이 실패하면 Releases 페이지 링크로 대체됩니다.
- 릴리스 자산 이름 규칙(`RepoManager-<버전>-<플랫폼>-<아키텍처>`)에 의존하므로
  이름을 바꾸면 `docs/download.js`의 `TARGETS`도 함께 고쳐야 합니다.
- `docs/**`가 바뀌면 `.github/workflows/pages.yml`이 자동 배포합니다.
  최초 1회만 저장소 **Settings → Pages → Source: GitHub Actions** 설정이 필요합니다
  (Actions 실행 허용 범위도 함께 열어야 합니다 — 위 [최초 1회 저장소 설정](#최초-1회-저장소-설정) 참고).
- 마스코트(`mascot.svg`)는 직접 그린 오리지널 캐릭터입니다.
  GitHub의 Octocat 이미지는 상표라 사용하지 않았습니다.

## 문서·트래킹

- [PRD.md](PRD.md) — 제품 요구사항·범위·마일스톤
- GitHub **Milestones / Issues** — 단계별 과업 (M1–M9)

## 개발 구조

```text
src/repomanager/
  __main__.py               # python -m repomanager
  app.py                    # QApplication 부트스트랩
  config.py                 # 토큰 / keyring / QSettings / 업데이트 설정
  i18n.py                   # ko / en / ja
  models/repository.py
  services/
    github_client.py        # PyGithub 래퍼, rate limit
    repo_backup.py          # ZIP mirror + issues/milestones
    repo_cache.py           # 시작 시 즉시 표시용 목록 캐시
    oauth_device.py         # OAuth Device Flow
    ai_assist.py            # GitHub Models 설명 추천
    updater.py              # 릴리스 확인 / 다운로드 / 자기 교체
  workers/                  # QRunnable — UI 스레드 밖에서 실행
    api_worker.py
    update_worker.py
  ui/
    main_window.py          # 메뉴·툴바·상태바, 워커 배선
    dual_repo_lists.py      # 활성/아카이브 이중 목록, 필터·정렬
    repo_item_delegate.py   # 리스트 아이템 커스텀 그리기
    repo_detail_panel.py    # 설명·공개여부·이름 변경·백업
    confirm_dialog.py       # DELETE 입력, CSV 내보내기
    rename_dialog.py        # RENAME 입력
    settings_dialog.py      # 토큰·언어·테마·업데이트
    update_dialog.py        # 변경 사항·다운로드·설치
    about_dialog.py
    loading_overlay.py
    theme.py                # 라이트/다크 선택
    styles.qss / styles_dark.qss
    assets/icon.png         # .ico / .icns 의 원본

packaging/
  build.py                  # 아이콘 → PyInstaller → 이름 정리 → 체크섬
  repomanager.spec          # PyInstaller 설정
  make_icons.py             # icon.png → .ico / .icns
docs/                       # 홈페이지 (GitHub Pages)
  index.html
  style.css
  download.js               # OS 감지 + 최신 릴리스 자산 링크
  mascot.svg
.github/workflows/
  ci.yml                    # 3개 OS 테스트
  release.yml               # 4개 플랫폼 빌드·배포
  pages.yml                 # docs/ 를 GitHub Pages 로 배포
tests/                      # pytest — 서비스·워커·다이얼로그 단위 테스트
```

## 라이선스

MIT — [LICENSE](LICENSE)

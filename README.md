# RepoManager

수업·실습 후 남는 GitHub 저장소를 GUI에서 골라 **아카이브**하거나 **삭제**하는 데스크톱 앱입니다.  
Windows, macOS, Linux에서 동작합니다 (PySide6).

## 기능

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

## GitHub Token

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens**
2. **Classic** 권장 스코프:
   - `repo` — private 저장소 포함 목록/아카이브
   - `delete_repo` — 삭제 기능 사용 시 필수
   - `read:org` — 조직 저장소 목록에 필요할 수 있음
3. **Fine-grained**인 경우: 대상 저장소 접근 + **Administration** (archive/delete)

토큰은 `.env`에만 두고 **절대 커밋하지 마세요.**

## 사용 방법

1. 앱 실행 → **Refresh**로 저장소 목록 로드
2. Owner / Public·Private / Archived 필터와 검색으로 대상 좁히기
3. 설명·가시성 확인, 필요 시 행을 더블클릭해 GitHub에서 확인
4. 체크박스로 여러 저장소 선택
5. **Archive** 또는 **Delete** 클릭
6. 확인 창에서 이름·설명 검토 (삭제는 `DELETE` 입력 필요)
7. 진행률과 성공/실패 요약 확인 후 목록이 자동 새로고침됩니다
8. 상태바 오른쪽에서 API rate limit 잔여량을 확인합니다

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

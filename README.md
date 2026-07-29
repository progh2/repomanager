# RepoManager

수업·실습 후 남는 GitHub 저장소를 GUI에서 골라 **아카이브**하거나 **삭제**하는 데스크톱 앱입니다.  
Windows, macOS, Linux에서 동작합니다 (PySide6).

## 기능

- 인증된 계정의 저장소 목록 불러오기 (페이지네이션)
- **Public / Private**, 설명(description), 이름·소유자, 업데이트 시각 표시
- 검색·필터, 다중 선택
- 행 더블클릭 시 브라우저에서 GitHub 페이지 열기
- 선택 저장소 **일괄 Archive / Delete**
- 실행 전 확인 창(이름 + 설명 + 경고)
- API 호출은 백그라운드 스레드로 처리 (UI 멈춤 방지)

> **현재 구현 단계:** Milestone 1–4 완료 (목록·필터·선택·확인 창·일괄 Archive/Delete).  
> **다음:** Milestone 5 — org 필터, rate limit, 패키징, v0.1.0 릴리스.

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
3. **Fine-grained**인 경우: 대상 저장소 접근 + **Administration** (archive/delete)

토큰은 `.env`에만 두고 **절대 커밋하지 마세요.**

## 사용 방법

1. 앱 실행 → **Refresh**로 저장소 목록 로드
2. 설명·Public/Private 확인, 필요 시 행을 더블클릭해 GitHub에서 확인
3. 체크박스로 여러 저장소 선택
4. **Archive** 또는 **Delete** 클릭
5. 확인 창에서 이름·설명 검토 (삭제는 `DELETE` 입력 필요)
6. 진행률과 성공/실패 요약 확인 후 목록이 자동 새로고침됩니다

## 주의

- **삭제는 되돌릴 수 없습니다.**
- 아카이브는 읽기 전용으로 남기며, 나중에 GitHub에서 unarchive할 수 있습니다.

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

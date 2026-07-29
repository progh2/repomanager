"""Simple UI translations for ko / en / ja."""

from __future__ import annotations

from PySide6.QtCore import QLocale, QSettings

SUPPORTED = ("ko", "en", "ja")
KEY_LANGUAGE = "ui/language"

_current = "en"
_listeners: list = []

# fmt: off
STRINGS: dict[str, dict[str, str]] = {
    "app.name": {"ko": "RepoManager", "en": "RepoManager", "ja": "RepoManager"},
    "menu.file": {"ko": "파일(&F)", "en": "File(&F)", "ja": "ファイル(&F)"},
    "menu.settings": {"ko": "설정(&S)...", "en": "Settings(&S)...", "ja": "設定(&S)..."},
    "menu.quit": {"ko": "종료(&Q)", "en": "Quit(&Q)", "ja": "終了(&Q)"},
    "menu.help": {"ko": "도움말(&H)", "en": "Help(&H)", "ja": "ヘルプ(&H)"},
    "menu.delete_help": {"ko": "삭제 권한 안내...", "en": "Delete permission help...", "ja": "削除権限の案内..."},
    "menu.about": {"ko": "정보(&A)...", "en": "About(&A)...", "ja": "情報(&A)..."},

    "btn.refresh": {"ko": "새로고침", "en": "Refresh", "ja": "更新"},
    "btn.select_all": {"ko": "전체 선택", "en": "Select all", "ja": "すべて選択"},
    "btn.clear": {"ko": "선택 해제", "en": "Clear selection", "ja": "選択解除"},
    "btn.delete": {"ko": "선택 삭제", "en": "Delete selected", "ja": "選択削除"},
    "label.selected": {"ko": "선택: {n}", "en": "Selected: {n}", "ja": "選択: {n}"},
    "hint.main": {
        "ko": "왼쪽=활성, 오른쪽=아카이브. →/← 로 이동하고, 아래 패널에서 설명·공개여부·Pages를 다룹니다.",
        "en": "Left=Active, Right=Archive. Use →/← to move. Edit description, visibility, and Pages below.",
        "ja": "左=アクティブ、右=アーカイブ。→/←で移動。下のパネルで説明・公開設定・Pagesを操作します。",
    },
    "status.ready": {
        "ko": "준비됨. 필요하면 설정을 연 뒤 새로고침하세요.",
        "en": "Ready. Open Settings if needed, then Refresh.",
        "ja": "準備完了。必要なら設定を開き、更新してください。",
    },
    "auth.label": {"ko": "인증: {src}", "en": "Auth: {src}", "ja": "認証: {src}"},

    "pane.active": {"ko": "활성", "en": "Active", "ja": "アクティブ"},
    "pane.archive": {"ko": "아카이브", "en": "Archive", "ja": "アーカイブ"},
    "search.placeholder": {
        "ko": "이름 또는 설명 검색...",
        "en": "Search name or description...",
        "ja": "名前または説明を検索...",
    },
    "filter.owner_all": {"ko": "모든 소유자", "en": "All owners", "ja": "すべてのオーナー"},
    "filter.vis_all": {"ko": "모든 공개범위", "en": "All visibility", "ja": "すべての公開範囲"},
    "filter.public": {"ko": "공개", "en": "Public", "ja": "公開"},
    "filter.private": {"ko": "비공개", "en": "Private", "ja": "非公開"},
    "tip.to_archive": {
        "ko": "선택한 활성 저장소를 아카이브로 이동",
        "en": "Archive selected active repositories",
        "ja": "選択したアクティブなリポジトリをアーカイブ",
    },
    "tip.to_active": {
        "ko": "선택한 아카이브 저장소를 활성으로 복원",
        "en": "Restore selected archived repositories",
        "ja": "選択したアーカイブをアクティブに戻す",
    },

    "vis.public": {"ko": "공개", "en": "Public", "ja": "公開"},
    "vis.private": {"ko": "비공개", "en": "Private", "ja": "非公開"},
    "vis.click_to_private": {
        "ko": "공개 · 클릭하여 비공개로",
        "en": "Public · click to make private",
        "ja": "公開 · クリックで非公開に",
    },
    "vis.click_to_public": {
        "ko": "비공개 · 클릭하여 공개로",
        "en": "Private · click to make public",
        "ja": "非公開 · クリックで公開に",
    },
    "vis.none": {"ko": "공개 여부", "en": "Visibility", "ja": "公開設定"},

    "detail.select": {
        "ko": "저장소를 선택하세요",
        "en": "Select a repository",
        "ja": "リポジトリを選択してください",
    },
    "detail.select_hint": {
        "ko": "왼쪽 또는 오른쪽 목록에서 항목을 선택하면 상세 정보가 표시됩니다.",
        "en": "Select an item in either list to see details.",
        "ja": "左または右の一覧から項目を選ぶと詳細が表示されます。",
    },
    "detail.meta": {
        "ko": "생성일 {created}  ·  마지막 업데이트 {updated}  ·  {state}",
        "en": "Created {created}  ·  Updated {updated}  ·  {state}",
        "ja": "作成 {created}  ·  更新 {updated}  ·  {state}",
    },
    "detail.state_active": {"ko": "활성", "en": "Active", "ja": "アクティブ"},
    "detail.state_archived": {"ko": "아카이브됨", "en": "Archived", "ja": "アーカイブ済み"},
    "detail.desc_label": {"ko": "설명", "en": "Description", "ja": "説明"},
    "detail.desc_placeholder": {
        "ko": "저장소 설명을 입력하세요...",
        "en": "Enter repository description...",
        "ja": "リポジトリの説明を入力...",
    },
    "detail.open_repo": {"ko": "저장소 열기", "en": "Open repository", "ja": "リポジトリを開く"},
    "detail.pages_open": {"ko": "Pages 열기", "en": "Open Pages", "ja": "Pagesを開く"},
    "detail.pages_none": {"ko": "GitHub Pages: 없음", "en": "GitHub Pages: none", "ja": "GitHub Pages: なし"},
    "detail.pages_yes": {"ko": "GitHub Pages: {url}", "en": "GitHub Pages: {url}", "ja": "GitHub Pages: {url}"},
    "detail.pages_tip_on": {
        "ko": "GitHub Pages 사이트를 브라우저에서 엽니다.",
        "en": "Open the GitHub Pages site in your browser.",
        "ja": "GitHub Pagesサイトをブラウザで開きます。",
    },
    "detail.pages_tip_off": {
        "ko": "이 저장소에는 GitHub Pages가 없습니다.",
        "en": "This repository has no GitHub Pages site.",
        "ja": "このリポジトリに GitHub Pages はありません。",
    },
    "detail.suggest": {"ko": "AI 추천 설명", "en": "AI suggest description", "ja": "AI説明の提案"},
    "detail.suggest_tip": {
        "ko": "GitHub Models / Copilot 권한이 있으면 README 등을 보고 설명을 추천합니다.",
        "en": "With GitHub Models / Copilot access, suggests a description from the README.",
        "ja": "GitHub Models / Copilot 権限があれば README などから説明を提案します。",
    },
    "detail.save": {"ko": "설명 저장", "en": "Save description", "ja": "説明を保存"},

    "settings.title": {"ko": "설정", "en": "Settings", "ja": "設定"},
    "settings.language": {"ko": "언어", "en": "Language", "ja": "言語"},
    "settings.lang_auto": {"ko": "시스템 기본", "en": "System default", "ja": "システム既定"},
    "settings.lang_ko": {"ko": "한국어", "en": "Korean", "ja": "韓国語"},
    "settings.lang_en": {"ko": "영어", "en": "English", "ja": "英語"},
    "settings.lang_ja": {"ko": "일본어", "en": "Japanese", "ja": "日本語"},
    "settings.save": {"ko": "저장", "en": "Save", "ja": "保存"},
    "settings.cancel": {"ko": "취소", "en": "Cancel", "ja": "キャンセル"},
    "settings.token_source": {
        "ko": "현재 토큰 출처: {src}",
        "en": "Current token source: {src}",
        "ja": "現在のトークン元: {src}",
    },

    "about.title": {
        "ko": "이 프로그램은...",
        "en": "About this program",
        "ja": "このプログラムについて",
    },
    "about.open_project": {
        "ko": "프로젝트 GitHub 열기",
        "en": "Open project on GitHub",
        "ja": "プロジェクトの GitHub を開く",
    },

    "confirm.cancel": {"ko": "취소", "en": "Cancel", "ja": "キャンセル"},
    "no_selection": {
        "ko": "저장소를 하나 이상 선택하세요.",
        "en": "Select at least one repository.",
        "ja": "リポジトリを1つ以上選択してください。",
    },
    "no_selection_title": {"ko": "선택 없음", "en": "No selection", "ja": "未選択"},

    "token.source.env": {"ko": "환경변수 (.env)", "en": "Environment (.env)", "ja": "環境変数 (.env)"},
    "token.source.settings": {"ko": "설정에 저장됨", "en": "Saved in Settings", "ja": "設定に保存済み"},
    "token.source.gh": {"ko": "GitHub CLI (gh)", "en": "GitHub CLI (gh)", "ja": "GitHub CLI (gh)"},
    "token.source.none": {"ko": "없음", "en": "not set", "ja": "未設定"},

    "list.created": {"ko": "생성", "en": "Created", "ja": "作成"},
    "list.updated": {"ko": "업데이트", "en": "Updated", "ja": "更新"},
    "list.no_desc": {"ko": "(설명 없음)", "en": "(no description)", "ja": "(説明なし)"},
}
# fmt: on


def add_listener(callback) -> None:
    if callback not in _listeners:
        _listeners.append(callback)


def remove_listener(callback) -> None:
    if callback in _listeners:
        _listeners.remove(callback)


def _settings() -> QSettings:
    return QSettings("RepoManager", "RepoManager")


def detect_system_language() -> str:
    name = QLocale.system().name()  # e.g. ko_KR
    code = (name.split("_")[0] or "en").lower()
    return code if code in SUPPORTED else "en"


def get_saved_language_preference() -> str:
    """Return 'auto' or an explicit language code."""
    value = str(_settings().value(KEY_LANGUAGE, "auto") or "auto").strip().lower()
    if value == "auto" or value in SUPPORTED:
        return value
    return "auto"


def set_saved_language_preference(value: str) -> None:
    value = value.strip().lower()
    if value != "auto" and value not in SUPPORTED:
        value = "auto"
    s = _settings()
    s.setValue(KEY_LANGUAGE, value)
    s.sync()


def resolve_language(preference: str | None = None) -> str:
    pref = get_saved_language_preference() if preference is None else preference
    if pref == "auto":
        return detect_system_language()
    return pref if pref in SUPPORTED else "en"


def get_language() -> str:
    return _current


def set_language(code: str, *, notify: bool = True) -> str:
    global _current
    _current = code if code in SUPPORTED else "en"
    if notify:
        for callback in list(_listeners):
            callback()
    return _current


def init_language() -> str:
    return set_language(resolve_language(), notify=False)


def tr(key: str, **kwargs: object) -> str:
    entry = STRINGS.get(key, {})
    text = entry.get(_current) or entry.get("en") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text

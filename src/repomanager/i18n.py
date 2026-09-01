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
    "menu.check_update": {"ko": "업데이트 확인(&U)...", "en": "Check for updates(&U)...", "ja": "アップデートを確認(&U)..."},

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

    "update.title": {"ko": "업데이트", "en": "Update", "ja": "アップデート"},
    "update.checking": {"ko": "업데이트를 확인하는 중...", "en": "Checking for updates...", "ja": "アップデートを確認しています..."},
    "update.available": {
        "ko": "새 버전 {latest} 이(가) 있습니다. (현재 {current})",
        "en": "Version {latest} is available. (You have {current})",
        "ja": "新しいバージョン {latest} があります。(現在 {current})",
    },
    "update.up_to_date": {
        "ko": "최신 버전입니다. (v{version})",
        "en": "You are up to date. (v{version})",
        "ja": "最新バージョンです。(v{version})",
    },
    "update.notes": {"ko": "변경 사항", "en": "What's new", "ja": "変更点"},
    "update.no_notes": {"ko": "(변경 사항이 제공되지 않았습니다.)", "en": "(No release notes provided.)", "ja": "(リリースノートはありません。)"},
    "update.size": {"ko": "다운로드 크기: {mb} MB", "en": "Download size: {mb} MB", "ja": "ダウンロードサイズ: {mb} MB"},
    "update.btn_install": {"ko": "다운로드 후 설치", "en": "Download and install", "ja": "ダウンロードしてインストール"},
    "update.btn_page": {"ko": "릴리스 페이지 열기", "en": "Open release page", "ja": "リリースページを開く"},
    "update.btn_skip": {"ko": "이 버전 건너뛰기", "en": "Skip this version", "ja": "このバージョンをスキップ"},
    "update.btn_later": {"ko": "나중에", "en": "Later", "ja": "後で"},
    "update.btn_cancel": {"ko": "다운로드 취소", "en": "Cancel download", "ja": "ダウンロードを中止"},
    "update.downloading": {
        "ko": "다운로드 중... {done} / {total} MB",
        "en": "Downloading... {done} / {total} MB",
        "ja": "ダウンロード中... {done} / {total} MB",
    },
    "update.installing": {"ko": "설치를 준비하는 중...", "en": "Preparing the installer...", "ja": "インストールを準備しています..."},
    "update.cancelled": {"ko": "다운로드를 취소했습니다.", "en": "Download cancelled.", "ja": "ダウンロードを中止しました。"},
    "update.restart_title": {"ko": "재시작 필요", "en": "Restart required", "ja": "再起動が必要です"},
    "update.restart_text": {
        "ko": "RepoManager를 종료하고 v{version} 을(를) 설치한 뒤 다시 시작합니다. 계속할까요?",
        "en": "RepoManager will quit, install v{version}, and start again. Continue?",
        "ja": "RepoManager を終了して v{version} をインストールし、再起動します。続行しますか？",
    },
    "update.source_mode": {
        "ko": "소스에서 실행 중이라 앱 안에서 설치할 수 없습니다. 'git pull' 로 업데이트하거나 릴리스 페이지에서 실행파일을 받으세요.",
        "en": "Running from source, so the in-app installer is unavailable. Update with 'git pull' or download an executable from the release page.",
        "ja": "ソースから実行中のため、アプリ内インストールは利用できません。'git pull' で更新するか、リリースページから実行ファイルを取得してください。",
    },
    "update.no_asset": {
        "ko": "이 릴리스에는 현재 플랫폼({platform})용 실행파일이 없습니다. 릴리스 페이지에서 직접 확인하세요.",
        "en": "This release has no executable for your platform ({platform}). Check the release page directly.",
        "ja": "このリリースには現在のプラットフォーム({platform})向けの実行ファイルがありません。リリースページをご確認ください。",
    },
    "update.failed": {"ko": "업데이트 실패", "en": "Update failed", "ja": "アップデート失敗"},

    "settings.updates": {"ko": "업데이트", "en": "Updates", "ja": "アップデート"},
    "settings.auto_check": {
        "ko": "시작할 때 자동으로 새 버전 확인 (하루 1회)",
        "en": "Check for new versions on startup (once a day)",
        "ja": "起動時に新しいバージョンを確認する (1日1回)",
    },
    "settings.check_update_now": {"ko": "지금 확인", "en": "Check now", "ja": "今すぐ確認"},
    "settings.update_version": {"ko": "현재 버전: v{version}", "en": "Current version: v{version}", "ja": "現在のバージョン: v{version}"},

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
    "filter.pages_all": {"ko": "Pages 전체", "en": "Pages: all", "ja": "Pages すべて"},
    "filter.pages_yes": {"ko": "Pages 있음", "en": "Has Pages", "ja": "Pages あり"},
    "filter.pages_no": {"ko": "Pages 없음", "en": "No Pages", "ja": "Pages なし"},
    "filter.fork_all": {"ko": "Fork 전체", "en": "Forks: all", "ja": "Fork すべて"},
    "filter.fork_only": {"ko": "Fork만", "en": "Forks only", "ja": "Fork のみ"},
    "filter.fork_none": {"ko": "Fork 제외", "en": "Exclude forks", "ja": "Fork を除く"},
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
    "detail.rename": {"ko": "이름 변경...", "en": "Rename...", "ja": "名前変更..."},
    "detail.rename_tip": {
        "ko": "저장소 이름을 바꿉니다. URL과 링크가 모두 변경됩니다.",
        "en": "Rename this repository. All URLs and links will change.",
        "ja": "リポジトリ名を変更します。URLとリンクがすべて変わります。",
    },
    "detail.backup": {"ko": "ZIP 백업", "en": "ZIP backup", "ja": "ZIPバックアップ"},
    "detail.backup_tip": {
        "ko": "모든 브랜치(git mirror)와 이슈·마일스톤을 ZIP으로 저장합니다. 삭제 전 백업에 유용합니다.",
        "en": "Save all branches (git mirror) plus issues and milestones as a ZIP. Useful before delete.",
        "ja": "全ブランチ (git mirror) と Issue・マイルストーンを ZIP で保存します。削除前のバックアップに便利です。",
    },

    "backup.choose_dir": {
        "ko": "백업 ZIP을 저장할 폴더",
        "en": "Folder for backup ZIP files",
        "ja": "バックアップ ZIP の保存フォルダ",
    },
    "backup.title": {"ko": "ZIP 백업", "en": "ZIP backup", "ja": "ZIPバックアップ"},
    "backup.done_title": {"ko": "백업 완료", "en": "Backup finished", "ja": "バックアップ完了"},
    "backup.partial_title": {"ko": "일부 백업 실패", "en": "Some backups failed", "ja": "一部バックアップ失敗"},
    "backup.failed_title": {"ko": "백업 실패", "en": "Backup failed", "ja": "バックアップ失敗"},
    "backup.summary": {
        "ko": "성공: {ok}\n실패: {fail}\n저장 폴더: {dir}",
        "en": "Succeeded: {ok}\nFailed: {fail}\nFolder: {dir}",
        "ja": "成功: {ok}\n失敗: {fail}\nフォルダ: {dir}",
    },
    "backup.failed_detail": {"ko": "실패 상세:", "en": "Failures:", "ja": "失敗の詳細:"},
    "status.backing_up": {
        "ko": "백업 중 {name} ({current}/{total})",
        "en": "Backing up {name} ({current}/{total})",
        "ja": "バックアップ中 {name} ({current}/{total})",
    },
    "status.backup_done": {
        "ko": "백업 완료 — 성공 {ok}, 실패 {fail}.",
        "en": "Backup finished — {ok} succeeded, {fail} failed.",
        "ja": "バックアップ完了 — 成功 {ok}、失敗 {fail}。",
    },
    "confirm.backup_zip": {
        "ko": "ZIP으로 백업...",
        "en": "Backup as ZIP...",
        "ja": "ZIPでバックアップ...",
    },

    "rename.title": {"ko": "저장소 이름 변경", "en": "Rename repository", "ja": "リポジトリ名の変更"},
    "rename.warning": {
        "ko": "{name} 저장소의 이름을 변경합니다.\n이 작업은 GitHub URL·git remote·Pages·북마크·다른 저장소의 참조를 모두 깨뜨릴 수 있습니다.",
        "en": "You are about to rename {name}.\nThis breaks GitHub URLs, git remotes, Pages, bookmarks, and references from other repositories.",
        "ja": "{name} の名前を変更します。\nGitHub URL・git remote・Pages・ブックマーク・他リポジトリからの参照が壊れる可能性があります。",
    },
    "rename.links_note": {
        "ko": "GitHub는 일정 기간 리다이렉트를 제공할 수 있지만, 의존하지 마세요. 로컬 클론의 remote URL도 직접 업데이트해야 합니다.",
        "en": "GitHub may redirect for a while, but do not rely on it. Update local clone remotes yourself.",
        "ja": "GitHub はしばらくリダイレクトする場合がありますが、当てにしないでください。ローカル clone の remote も更新が必要です。",
    },
    "rename.current": {"ko": "현재 이름", "en": "Current name", "ja": "現在の名前"},
    "rename.new": {"ko": "새 이름", "en": "New name", "ja": "新しい名前"},
    "rename.new_placeholder": {
        "ko": "새 저장소 이름 (문자, 숫자, ., -, _)",
        "en": "New repository name (letters, digits, ., -, _)",
        "ja": "新しいリポジトリ名 (英数字, ., -, _)",
    },
    "rename.confirm_hint": {
        "ko": "계속하려면 아래에 <b>{word}</b> 를 입력하세요.",
        "en": "Type <b>{word}</b> below to continue.",
        "ja": "続行するには下に <b>{word}</b> を入力してください。",
    },
    "rename.accept": {"ko": "이름 변경", "en": "Rename", "ja": "名前を変更"},
    "status.renaming": {
        "ko": "이름 변경 중: {old} → {new}",
        "en": "Renaming: {old} → {new}",
        "ja": "名前変更中: {old} → {new}",
    },
    "status.renamed": {
        "ko": "{old} → {new} 으로 이름을 변경했습니다.",
        "en": "Renamed {old} → {new}.",
        "ja": "{old} → {new} に名前を変更しました。",
    },

    "settings.title": {"ko": "설정", "en": "Settings", "ja": "設定"},
    "settings.language": {"ko": "언어", "en": "Language", "ja": "言語"},
    "settings.lang_auto": {"ko": "시스템 기본", "en": "System default", "ja": "システム既定"},
    "settings.lang_ko": {"ko": "한국어", "en": "Korean", "ja": "韓国語"},
    "settings.lang_en": {"ko": "영어", "en": "English", "ja": "英語"},
    "settings.lang_ja": {"ko": "일본어", "en": "Japanese", "ja": "日本語"},
    "settings.theme": {"ko": "테마", "en": "Theme", "ja": "テーマ"},
    "settings.theme_light": {"ko": "라이트", "en": "Light", "ja": "ライト"},
    "settings.theme_dark": {"ko": "다크", "en": "Dark", "ja": "ダーク"},
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

    "sort.label": {"ko": "정렬", "en": "Sort", "ja": "並べ替え"},
    "sort.name": {"ko": "이름순", "en": "Name", "ja": "名前順"},
    "sort.updated_desc": {"ko": "최근 업데이트순", "en": "Recently updated", "ja": "更新が新しい順"},
    "sort.updated_asc": {"ko": "오래된 업데이트순", "en": "Least recently updated", "ja": "更新が古い順"},
    "sort.created_desc": {"ko": "최근 생성순", "en": "Newest", "ja": "作成が新しい順"},
    "sort.created_asc": {"ko": "오래된 생성순", "en": "Oldest", "ja": "作成が古い順"},

    "action.archive": {"ko": "아카이브", "en": "Archive", "ja": "アーカイブ"},
    "action.unarchive": {"ko": "활성 복원", "en": "Restore", "ja": "アクティブ復元"},
    "action.delete": {"ko": "삭제", "en": "Delete", "ja": "削除"},

    "help.delete_scope": {
        "ko": (
            "저장소 삭제에는 delete_repo 권한이 필요합니다.\n\n"
            "GitHub CLI를 쓰는 경우 터미널에서 아래를 실행하세요:\n"
            "  gh auth refresh -h github.com -s delete_repo\n\n"
            "또는 설정에서 delete_repo가 포함된 Classic PAT를 저장하세요.\n"
            "(Fine-grained PAT는 Administration: Read and write 필요)"
        ),
        "en": (
            "Deleting repositories requires the delete_repo scope.\n\n"
            "If you use GitHub CLI, run this in a terminal:\n"
            "  gh auth refresh -h github.com -s delete_repo\n\n"
            "Or save a Classic PAT that includes delete_repo in Settings.\n"
            "(Fine-grained PATs need Administration: Read and write)"
        ),
        "ja": (
            "リポジトリの削除には delete_repo 権限が必要です。\n\n"
            "GitHub CLI を使う場合はターミナルで実行してください:\n"
            "  gh auth refresh -h github.com -s delete_repo\n\n"
            "または delete_repo を含む Classic PAT を設定に保存してください。\n"
            "(Fine-grained PAT は Administration: Read and write が必要)"
        ),
    },
    "delete_help.title": {"ko": "삭제 권한 안내", "en": "Delete permission help", "ja": "削除権限の案内"},
    "delete_help.text": {
        "ko": "저장소를 삭제하려면 delete_repo 권한이 필요합니다.",
        "en": "Deleting a repository requires the delete_repo scope.",
        "ja": "リポジトリの削除には delete_repo 権限が必要です。",
    },
    "delete_help.copy": {"ko": "명령 복사", "en": "Copy command", "ja": "コマンドをコピー"},
    "delete_help.open_settings": {"ko": "설정 열기", "en": "Open Settings", "ja": "設定を開く"},
    "delete_help.copied": {
        "ko": "삭제 권한 명령을 클립보드에 복사했습니다.",
        "en": "Copied the delete-scope command to the clipboard.",
        "ja": "削除権限コマンドをクリップボードにコピーしました。",
    },
    "token.needed_title": {"ko": "GitHub 토큰 필요", "en": "GitHub token required", "ja": "GitHub トークンが必要"},
    "token.needed_text": {
        "ko": "GitHub 토큰이 아직 없습니다.\n설정에서 PAT 입력, GitHub CLI, 또는 웹 로그인을 구성할까요?",
        "en": "No GitHub token yet.\nOpen Settings to add a PAT, use GitHub CLI, or sign in via browser?",
        "ja": "GitHub トークンがまだありません。\n設定で PAT 入力、GitHub CLI、またはウェブログインを構成しますか？",
    },

    "status.loading": {"ko": "불러오는 중...", "en": "Loading...", "ja": "読み込み中..."},
    "status.cache_shown": {
        "ko": "캐시된 목록 표시 중 (저장: {time}) — 백그라운드에서 새로고침합니다.",
        "en": "Showing cached list (saved {time}) — refreshing in the background.",
        "ja": "キャッシュされた一覧を表示中 (保存: {time}) — バックグラウンドで更新します。",
    },
    "status.reading_token": {"ko": "토큰 확인 중...", "en": "Checking token...", "ja": "トークンを確認中..."},
    "status.authenticating": {"ko": "GitHub 인증 중...", "en": "Authenticating with GitHub...", "ja": "GitHub 認証中..."},
    "status.loading_for": {
        "ko": "{login} 저장소 목록을 가져오는 중...",
        "en": "Fetching repositories for {login}...",
        "ja": "{login} のリポジトリを取得中...",
    },
    "status.loaded": {
        "ko": "{login} 저장소 {n}개를 불러왔습니다.",
        "en": "Loaded {n} repositories for {login}.",
        "ja": "{login} のリポジトリを {n} 件読み込みました。",
    },
    "status.load_failed": {"ko": "불러오기 실패.", "en": "Load failed.", "ja": "読み込みに失敗しました。"},
    "status.settings_saved": {"ko": "설정을 저장했습니다.", "en": "Settings saved.", "ja": "設定を保存しました。"},
    "status.saving_desc": {"ko": "설명 저장 중...", "en": "Saving description...", "ja": "説明を保存中..."},
    "status.saving_desc_name": {
        "ko": "설명 저장 중: {name}",
        "en": "Saving description: {name}",
        "ja": "説明を保存中: {name}",
    },
    "status.changing_vis": {"ko": "공개 여부 변경 중...", "en": "Changing visibility...", "ja": "公開設定を変更中..."},
    "status.ai_preparing": {"ko": "AI 추천 준비 중...", "en": "Preparing AI suggestion...", "ja": "AI提案を準備中..."},
    "status.ai_checking": {
        "ko": "README와 저장소 정보를 확인하는 중...",
        "en": "Reading README and repository info...",
        "ja": "READMEとリポジトリ情報を確認中...",
    },
    "status.ai_generating": {
        "ko": "AI 추천 설명을 생성하는 중...",
        "en": "Generating AI description...",
        "ja": "AI説明を生成中...",
    },
    "status.ai_applied": {
        "ko": "AI 추천 설명을 반영했습니다. 필요하면 수정 후 저장하세요.",
        "en": "Applied the AI suggestion. Edit if needed, then save.",
        "ja": "AI提案を反映しました。必要なら編集して保存してください。",
    },
    "status.ai_failed": {"ko": "AI 추천 실패.", "en": "AI suggestion failed.", "ja": "AI提案に失敗しました。"},
    "status.updated": {
        "ko": "{name} 정보를 업데이트했습니다.",
        "en": "Updated {name}.",
        "ja": "{name} を更新しました。",
    },
    "status.edit_failed": {"ko": "수정 실패.", "en": "Update failed.", "ja": "更新に失敗しました。"},
    "status.action_start": {"ko": "{action} 시작...", "en": "Starting {action}...", "ja": "{action} を開始..."},
    "status.action_progress": {
        "ko": "처리 중 {name} ({current}/{total})",
        "en": "Processing {name} ({current}/{total})",
        "ja": "処理中 {name} ({current}/{total})",
    },
    "status.action_failed": {"ko": "작업 실패.", "en": "Operation failed.", "ja": "操作に失敗しました。"},
    "status.action_done": {
        "ko": "{action} 완료 — 성공 {s}, 실패 {f}.",
        "en": "{action} finished — {s} succeeded, {f} failed.",
        "ja": "{action} 完了 — 成功 {s}、失敗 {f}。",
    },

    "err.github_title": {"ko": "GitHub 오류", "en": "GitHub error", "ja": "GitHub エラー"},
    "err.edit_title": {"ko": "수정 실패", "en": "Update failed", "ja": "更新失敗"},
    "err.unexpected": {"ko": "예상치 못한 오류: {exc}", "en": "Unexpected error: {exc}", "ja": "予期しないエラー: {exc}"},
    "ai.title": {"ko": "AI 추천", "en": "AI suggestion", "ja": "AI提案"},

    "vis.change_title": {"ko": "공개 여부 변경", "en": "Change visibility", "ja": "公開設定の変更"},
    "vis.change_question": {
        "ko": "{name} 저장소를 {target}로 바꿀까요?",
        "en": "Make {name} {target}?",
        "ja": "{name} を{target}に変更しますか？",
    },

    "result.action": {"ko": "작업: {action}", "en": "Operation: {action}", "ja": "操作: {action}"},
    "result.success": {"ko": "성공: {n}", "en": "Succeeded: {n}", "ja": "成功: {n}"},
    "result.failure": {"ko": "실패: {n}", "en": "Failed: {n}", "ja": "失敗: {n}"},
    "result.failed_detail": {"ko": "실패 상세:", "en": "Failure details:", "ja": "失敗の詳細:"},
    "result.partial_title": {"ko": "일부 실패", "en": "Partially failed", "ja": "一部失敗"},
    "result.failed_title": {"ko": "작업 실패", "en": "Operation failed", "ja": "操作失敗"},
    "result.done_title": {"ko": "완료", "en": "Done", "ja": "完了"},

    "confirm.delete_title": {"ko": "삭제 확인", "en": "Confirm delete", "ja": "削除の確認"},
    "confirm.unarchive_title": {"ko": "활성 복원 확인", "en": "Confirm restore", "ja": "復元の確認"},
    "confirm.archive_title": {"ko": "아카이브 확인", "en": "Confirm archive", "ja": "アーカイブの確認"},
    "confirm.delete_warning": {
        "ko": "선택한 {n}개 저장소를 삭제합니다.\n이 작업은 되돌릴 수 없습니다.",
        "en": "This will delete {n} selected repositories.\nThis cannot be undone.",
        "ja": "選択した {n} 件のリポジトリを削除します。\nこの操作は元に戻せません。",
    },
    "confirm.unarchive_warning": {
        "ko": "선택한 {n}개 저장소를 아카이브에서 꺼내\n다시 활성 상태로 만듭니다.",
        "en": "This will restore {n} selected repositories\nfrom the archive to active state.",
        "ja": "選択した {n} 件のリポジトリをアーカイブから\nアクティブ状態に戻します。",
    },
    "confirm.archive_warning": {
        "ko": "선택한 {n}개 저장소를 아카이브합니다.\n읽기 전용으로 보관되며, 나중에 다시 활성으로 되돌릴 수 있습니다.",
        "en": "This will archive {n} selected repositories.\nThey become read-only and can be restored later.",
        "ja": "選択した {n} 件のリポジトリをアーカイブします。\n読み取り専用になり、後で元に戻せます。",
    },
    "confirm.delete_hint": {
        "ko": "계속하려면 아래에 <b>{word}</b> 를 입력하세요.<br>"
              "삭제에는 <b>delete_repo</b> 권한이 필요합니다. "
              "권한이 없으면 도움말 → 삭제 권한 안내를 보세요.",
        "en": "Type <b>{word}</b> below to continue.<br>"
              "Deletion requires the <b>delete_repo</b> scope. "
              "See Help → Delete permission help if missing.",
        "ja": "続行するには下に <b>{word}</b> を入力してください。<br>"
              "削除には <b>delete_repo</b> 権限が必要です。"
              "権限がない場合はヘルプ → 削除権限の案内を参照してください。",
    },
    "confirm.export_csv": {"ko": "목록 CSV로 저장", "en": "Save list as CSV", "ja": "一覧をCSVで保存"},
    "confirm.export_done": {"ko": "저장했습니다: {path}", "en": "Saved: {path}", "ja": "保存しました: {path}"},
    "confirm.export_failed": {"ko": "저장 실패: {exc}", "en": "Save failed: {exc}", "ja": "保存に失敗: {exc}"},
    "confirm.delete_accept": {"ko": "영구 삭제", "en": "Delete permanently", "ja": "完全に削除"},
    "confirm.unarchive_accept": {"ko": "활성으로 복원", "en": "Restore to active", "ja": "アクティブに復元"},
    "confirm.archive_accept": {"ko": "아카이브", "en": "Archive", "ja": "アーカイブ"},

    "settings.guide_html": {
        "ko": "<b>삭제(Delete)를 쓰려면</b> 토큰에 <code>delete_repo</code> 권한이 있어야 합니다.<br>"
              "목록 조회·아카이브는 <code>repo</code>만으로도 되지만, 삭제는 별도 권한입니다.<br><br>"
              "<b>GitHub CLI 사용자</b> — 터미널에서 실행 후 이 창에서 다시 가져오세요:<br>"
              "<code>{cmd}</code><br><br>"
              "<b>PAT 사용자</b> — Classic 토큰 생성 시 "
              "<code>repo</code> + <code>delete_repo</code> (+ 조직이면 <code>read:org</code>) 체크.<br>"
              "Fine-grained는 대상 저장소에 <b>Administration: Read and write</b>.",
        "en": "<b>To use Delete</b>, your token needs the <code>delete_repo</code> scope.<br>"
              "Listing and archiving work with <code>repo</code> alone; deletion is separate.<br><br>"
              "<b>GitHub CLI users</b> — run this in a terminal, then re-import here:<br>"
              "<code>{cmd}</code><br><br>"
              "<b>PAT users</b> — when creating a Classic token, check "
              "<code>repo</code> + <code>delete_repo</code> (+ <code>read:org</code> for orgs).<br>"
              "Fine-grained: <b>Administration: Read and write</b> on target repos.",
        "ja": "<b>削除を使うには</b>トークンに <code>delete_repo</code> 権限が必要です。<br>"
              "一覧・アーカイブは <code>repo</code> のみで可能ですが、削除は別権限です。<br><br>"
              "<b>GitHub CLI ユーザー</b> — ターミナルで実行後、この画面で再取得してください:<br>"
              "<code>{cmd}</code><br><br>"
              "<b>PAT ユーザー</b> — Classic トークン作成時に "
              "<code>repo</code> + <code>delete_repo</code>（組織は <code>read:org</code> も）をチェック。<br>"
              "Fine-grained は対象リポジトリに <b>Administration: Read and write</b>。",
    },
    "settings.copy_cmd": {
        "ko": "삭제 권한 명령 복사",
        "en": "Copy delete-scope command",
        "ja": "削除権限コマンドをコピー",
    },
    "settings.token_label": {"ko": "토큰", "en": "Token", "ja": "トークン"},
    "settings.token_placeholder": {
        "ko": "ghp_... 또는 github_pat_...",
        "en": "ghp_... or github_pat_...",
        "ja": "ghp_... または github_pat_...",
    },
    "settings.show_token": {"ko": "토큰 표시", "en": "Show token", "ja": "トークンを表示"},
    "settings.use_gh": {
        "ko": "GitHub CLI 토큰을 우선 사용 (gh auth token)",
        "en": "Prefer GitHub CLI token (gh auth token)",
        "ja": "GitHub CLI トークンを優先 (gh auth token)",
    },
    "settings.import_gh": {
        "ko": "GitHub CLI에서 지금 가져오기",
        "en": "Import from GitHub CLI now",
        "ja": "GitHub CLI から今すぐ取得",
    },
    "settings.gh_note": {
        "ko": "기본 gh 로그인에는 보통 delete_repo가 없습니다. 위에서 명령을 복사해 실행한 뒤 「가져오기」를 다시 누르세요.",
        "en": "Default gh login usually lacks delete_repo. Copy and run the command above, then import again.",
        "ja": "既定の gh ログインには通常 delete_repo がありません。上のコマンドを実行してから再取得してください。",
    },
    "settings.oauth_intro": {
        "ko": "가장 간단한 방법입니다. 버튼을 누르고 브라우저에 코드만 입력하세요.",
        "en": "The simplest way in. Click the button and enter the code in your browser.",
        "ja": "いちばん簡単な方法です。ボタンを押してブラウザにコードを入力してください。",
    },
    "settings.oauth_custom": {
        "ko": "내가 만든 OAuth App 사용 (선택)",
        "en": "Use my own OAuth App (optional)",
        "ja": "自分で作成した OAuth App を使う (任意)",
    },
    "settings.oauth_box": {
        "ko": "GitHub으로 로그인 (권장)",
        "en": "Sign in with GitHub (recommended)",
        "ja": "GitHub でログイン (推奨)",
    },
    "settings.login_web": {"ko": "GitHub 웹으로 로그인", "en": "Sign in with GitHub", "ja": "GitHub ウェブでログイン"},
    "settings.cancel_login": {"ko": "로그인 취소", "en": "Cancel sign-in", "ja": "ログインをキャンセル"},
    "settings.oauth_help_html": {
        "ko": "버튼을 누르면 브라우저가 열립니다. 화면에 나온 코드를 입력하고 <b>Authorize</b>를 누르면 끝입니다. 토큰을 직접 만들 필요도, GitHub CLI를 설치할 필요도 없습니다. 요청 권한: <code>repo</code>, <code>delete_repo</code>, <code>read:org</code>.",
        "en": "The button opens your browser. Enter the code shown and click <b>Authorize</b> — that's it. No token to create, no GitHub CLI to install. Requested scopes: <code>repo</code>, <code>delete_repo</code>, <code>read:org</code>.",
        "ja": "ボタンを押すとブラウザが開きます。表示されたコードを入力して <b>Authorize</b> を押すだけです。トークンの作成も GitHub CLI のインストールも不要です。要求スコープ: <code>repo</code>, <code>delete_repo</code>, <code>read:org</code>.",
    },
    "settings.clear_token": {"ko": "저장된 토큰 지우기", "en": "Clear saved token", "ja": "保存済みトークンを消去"},
    "settings.copied_title": {"ko": "복사됨", "en": "Copied", "ja": "コピーしました"},
    "settings.copied_text": {
        "ko": "아래 명령을 클립보드에 복사했습니다.\n\n{cmd}\n\n터미널에서 실행한 뒤 「GitHub CLI에서 지금 가져오기」를 누르세요.",
        "en": "Copied this command to the clipboard.\n\n{cmd}\n\nRun it in a terminal, then click \"Import from GitHub CLI now\".",
        "ja": "次のコマンドをクリップボードにコピーしました。\n\n{cmd}\n\nターミナルで実行後、「GitHub CLI から今すぐ取得」を押してください。",
    },
    "settings.gh_import_fail": {
        "ko": "gh auth token으로 토큰을 가져오지 못했습니다.\n터미널에서 gh auth login 후 다시 시도하세요.",
        "en": "Could not get a token via gh auth token.\nRun gh auth login in a terminal, then retry.",
        "ja": "gh auth token でトークンを取得できませんでした。\nターミナルで gh auth login 後に再試行してください。",
    },
    "settings.gh_import_ok": {
        "ko": "토큰을 가져왔습니다. 「저장」을 누르세요.\n삭제가 403이면 먼저 delete_repo 권한 명령을 실행하세요.",
        "en": "Token imported. Click Save.\nIf delete returns 403, run the delete_repo command first.",
        "ja": "トークンを取得しました。「保存」を押してください。\n削除が 403 の場合は先に delete_repo コマンドを実行してください。",
    },
    "settings.cleared": {
        "ko": "저장된 토큰을 지웠습니다.",
        "en": "Saved token cleared.",
        "ja": "保存済みトークンを消去しました。",
    },
    "settings.token_secure_note": {
        "ko": "토큰은 OS 자격 증명 저장소(keyring)에 안전하게 저장됩니다.",
        "en": "Tokens are stored securely in the OS credential store (keyring).",
        "ja": "トークンは OS の資格情報ストア (keyring) に安全に保存されます。",
    },
    "settings.token_plain_note": {
        "ko": "keyring을 사용할 수 없어 토큰이 QSettings에 저장됩니다.",
        "en": "keyring unavailable — token is stored in QSettings.",
        "ja": "keyring が使用できないため、トークンは QSettings に保存されます。",
    },

    "oauth.title": {"ko": "OAuth", "en": "OAuth", "ja": "OAuth"},
    "oauth.need_client_id": {
        "ko": "OAuth Client ID를 먼저 입력하세요.",
        "en": "Enter the OAuth Client ID first.",
        "ja": "先に OAuth Client ID を入力してください。",
    },
    "oauth.starting": {
        "ko": "브라우저 로그인을 시작하는 중...",
        "en": "Starting browser sign-in...",
        "ja": "ブラウザログインを開始中...",
    },
    "oauth.requesting": {
        "ko": "기기 코드를 요청하는 중...",
        "en": "Requesting device code...",
        "ja": "デバイスコードを要求中...",
    },
    "oauth.enter_code": {
        "ko": "브라우저에서 이 코드를 입력하세요: {code}\n{uri}",
        "en": "Enter this code in your browser: {code}\n{uri}",
        "ja": "ブラウザでこのコードを入力してください: {code}\n{uri}",
    },
    "oauth.cancelling": {"ko": "취소하는 중...", "en": "Cancelling...", "ja": "キャンセル中..."},
    "oauth.login_failed": {"ko": "로그인 실패", "en": "Sign-in failed", "ja": "ログイン失敗"},
    "oauth.login_done": {
        "ko": "로그인 완료. 토큰을 저장했습니다.",
        "en": "Signed in. Token saved.",
        "ja": "ログイン完了。トークンを保存しました。",
    },
    "oauth.login_ok_title": {"ko": "로그인 성공", "en": "Sign-in succeeded", "ja": "ログイン成功"},
    "oauth.login_ok_text": {
        "ko": "GitHub 웹 로그인에 성공했고 토큰을 저장했습니다.\n삭제를 쓰려면 OAuth App 권한에 delete_repo가 포함돼야 합니다.",
        "en": "Signed in with GitHub and saved the token.\nDeletion requires delete_repo in the OAuth App scopes.",
        "ja": "GitHub ウェブログインに成功し、トークンを保存しました。\n削除には OAuth App の権限に delete_repo が必要です。",
    },

    "ai.no_access": {
        "ko": "GitHub Models / Copilot 호출 권한이 없습니다.\nGitHub Copilot 또는 Models 접근이 가능한 계정/토큰인지 확인하세요.",
        "en": "No access to GitHub Models / Copilot.\nCheck that your account/token can use GitHub Copilot or Models.",
        "ja": "GitHub Models / Copilot の権限がありません。\nGitHub Copilot または Models にアクセスできるアカウント/トークンか確認してください。",
    },
    "ai.no_access_http": {
        "ko": "GitHub Models / Copilot 호출 권한이 없습니다.\nHTTP {status}",
        "en": "No access to GitHub Models / Copilot.\nHTTP {status}",
        "ja": "GitHub Models / Copilot の権限がありません。\nHTTP {status}",
    },
    "ai.request_failed": {"ko": "AI 요청 실패: {exc}", "en": "AI request failed: {exc}", "ja": "AIリクエスト失敗: {exc}"},
    "ai.failed_http": {
        "ko": "AI 추천 실패 (HTTP {status}): {body}",
        "en": "AI suggestion failed (HTTP {status}): {body}",
        "ja": "AI提案に失敗 (HTTP {status}): {body}",
    },
    "ai.bad_response": {
        "ko": "AI 응답 형식을 해석하지 못했습니다.",
        "en": "Could not parse the AI response.",
        "ja": "AI応答を解析できませんでした。",
    },
    "ai.empty": {
        "ko": "AI가 빈 설명을 반환했습니다.",
        "en": "The AI returned an empty description.",
        "ja": "AIが空の説明を返しました。",
    },

    "config.placeholder_token": {
        "ko": "GITHUB_TOKEN이 아직 자리표시자 값입니다. 설정을 열거나 .env에서 바꿔주세요.",
        "en": "GITHUB_TOKEN still has the placeholder value. Open Settings or replace it in .env.",
        "ja": "GITHUB_TOKEN がまだプレースホルダーのままです。設定を開くか .env を修正してください。",
    },
    "config.no_token": {
        "ko": "GitHub 토큰이 없습니다. 파일 → 설정에서 PAT를 넣거나, GitHub CLI에서 가져오거나, 웹 로그인을 사용하세요.",
        "en": "No GitHub token. Add a PAT in File → Settings, import from GitHub CLI, or sign in via browser.",
        "ja": "GitHub トークンがありません。ファイル → 設定で PAT を入力、GitHub CLI から取得、またはウェブログインしてください。",
    },
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

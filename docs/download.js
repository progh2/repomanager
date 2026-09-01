/* Point the download buttons at the newest release asset for the visitor's OS.
   Falls back to the releases page whenever anything is unavailable. */

const REPO = "progh2/repomanager";
const RELEASES_PAGE = `https://github.com/${REPO}/releases/latest`;

const TARGETS = [
  { id: "windows",     label: "Windows",              match: (n) => /windows/i.test(n) && n.endsWith(".exe") },
  { id: "macos-arm",   label: "macOS (Apple 실리콘)", match: (n) => /macos-arm64/i.test(n) && n.endsWith(".dmg") },
  { id: "macos-intel", label: "macOS (인텔)",         match: (n) => /macos-x86_64/i.test(n) && n.endsWith(".dmg") },
  { id: "linux",       label: "Linux",                match: (n) => /linux-x86_64$/i.test(n) },
];

function detectTarget() {
  const ua = navigator.userAgent;
  const platform = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "";
  const hay = `${ua} ${platform}`;
  if (/Win/i.test(hay)) return "windows";
  if (/Mac|iPhone|iPad/i.test(hay)) {
    // Browsers do not expose the Mac's CPU, so default to Apple silicon
    // (every Mac sold since 2020) and keep the Intel build one click away.
    return "macos-arm";
  }
  if (/Linux|X11|CrOS/i.test(hay)) return "linux";
  return null;
}

function humanSize(bytes) {
  return bytes ? `${(bytes / 1048576).toFixed(0)} MB` : "";
}

function renderFallback() {
  const others = document.getElementById("others");
  if (others) {
    others.innerHTML = `<a href="${RELEASES_PAGE}">모든 다운로드 보기 →</a>`;
  }
}

async function init() {
  const mainBtn = document.getElementById("mainBtn");
  const mainBtnText = document.getElementById("mainBtnText");
  const mainSub = document.getElementById("mainSub");
  const mainBtn2 = document.getElementById("mainBtn2");
  const mainSub2 = document.getElementById("mainSub2");
  const others = document.getElementById("others");

  let release;
  try {
    const response = await fetch(`https://api.github.com/repos/${REPO}/releases/latest`, {
      headers: { Accept: "application/vnd.github+json" },
    });
    if (!response.ok) throw new Error(String(response.status));
    release = await response.json();
  } catch {
    renderFallback();
    return;
  }

  const assets = release.assets || [];
  const found = {};
  for (const target of TARGETS) {
    found[target.id] = assets.find((asset) => target.match(asset.name));
  }

  const version = (release.tag_name || "").replace(/^v/, "");
  const picked = detectTarget();
  const primary = picked && found[picked];

  if (primary) {
    const label = TARGETS.find((t) => t.id === picked).label;
    mainBtn.href = primary.browser_download_url;
    mainBtnText.textContent = `${label}용 내려받기`;
    mainSub.textContent = `v${version} · ${humanSize(primary.size)} · 무료 오픈소스`;
    if (mainBtn2) {
      mainBtn2.href = primary.browser_download_url;
      mainBtn2.textContent = `${label}용 내려받기`;
      mainSub2.textContent = `v${version} · MIT 라이선스 오픈소스`;
    }
  } else if (version) {
    mainSub.textContent = `최신 버전 v${version}`;
  }

  // Every other platform stays one click away.
  const links = TARGETS.filter((t) => t.id !== picked && found[t.id]).map(
    (t) => `<a href="${found[t.id].browser_download_url}">${t.label}</a>`
  );
  links.push(`<a href="${RELEASES_PAGE}">이전 버전</a>`);
  if (others) others.innerHTML = links.join("");
}

init();

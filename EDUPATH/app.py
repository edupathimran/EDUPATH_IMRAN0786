import json as _ep_json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.environ.get("EDUPATH_SECRET_KEY") or secrets.token_hex(32)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_REFRESH_EACH_REQUEST"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

ADMIN_EMAIL = os.environ.get("EDUPATH_ADMIN_EMAIL", "admin@edupath.in").strip().lower()
DB_NAME = os.path.join(BASE_DIR, "edupath_master.db")

ALLOWED_VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".3gp")
ALLOWED_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic", ".heif")
ALLOWED_PDF_EXTS = (".pdf",)

MOCK_PORTAL_CHOICES = [
    "Class 10",
    "State Boards",
    "Class 11",
    "Class 12",
    "JEE",
    "NEET",
    "General",
]

MOBILE_EDUPATH_ENHANCEMENT = """
<style id="edupath-mobile-polish-2026">
.side-drawer img,
#sideDrawer img,
.drawer-header img,
.drawer-brand img,
.brand-logo img,
.sidebar-logo img,
.msg-sidebar img,
.msg-side-panel img,
.chat-sidebar img,
.chat-side-panel img {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    max-width: 36px !important;
    max-height: 36px !important;
    object-fit: cover !important;
    border-radius: 10px !important;
    flex-shrink: 0 !important;
}
html.ep-drawer-open,
body.ep-drawer-open,
body.ep-drawer-open .dash-wrapper {
    overflow: hidden !important;
    height: 100vh !important;
    touch-action: none !important;
}
@media (max-width: 768px) {
    html, body {
        max-width: 100vw !important;
        overflow-x: hidden !important;
        -webkit-text-size-adjust: 100%;
    }
    .dash-wrapper, .container, .main-content, .page-wrap, main, section {
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    #drawerBackdrop, .drawer-backdrop {
        position: fixed !important;
        inset: 0 !important;
        z-index: 9990 !important;
    }
    #sideDrawer, .side-drawer {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        bottom: 0 !important;
        z-index: 9999 !important;
        touch-action: pan-y !important;
    }
    .top-bar, header, nav, .navbar, .topbar {
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    .top-left {
        gap: 10px !important;
        min-width: 0 !important;
    }
    .welcome-pill {
        font-size: 9.5px !important;
        padding: 2px 8px !important;
    }
    .welcome-name, header h1, .hero-title {
        font-size: 1.15rem !important;
        line-height: 1.25 !important;
        word-break: break-word !important;
    }
    .top-right img, .avatar-link img, header img, .logo img {
        max-width: 100% !important;
        height: auto !important;
    }
    .course-slider {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-bottom: 8px !important;
        overflow-x: auto !important;
        scroll-snap-type: x mandatory !important;
        scroll-behavior: smooth !important;
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: none;
        width: 100% !important;
    }
    .course-slider::-webkit-scrollbar { display: none; }
    .course-slider > .course-slide,
    .course-slider > * {
        flex: 0 0 100% !important;
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        scroll-snap-align: start !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }
    .grid-2, .grid-3, .grid-4, .stats-grid, .portal-strip {
        grid-template-columns: 1fr !important;
        gap: 9px !important;
    }
    .subj-card, .stream-big-card, .portal-chip {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 10px !important;
        min-height: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        padding: 11px 14px !important;
        border-radius: 13px !important;
        border-top-width: 1px !important;
        border-left: 4px solid var(--accent, #10b981) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        cursor: pointer !important;
        touch-action: manipulation !important;
    }
    .subj-card > div:first-child, .stream-big-card > div:first-child {
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }
    .subj-card p, .stream-big-card p, .stream-icon-lg { display: none !important; }
    .subj-card h2, .stream-big-card h2 {
        font-size: 0.96rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        line-height: 1.25 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    .subj-card .btn, .stream-big-card .btn {
        width: auto !important;
        flex: 0 0 auto !important;
        padding: 7px 11px !important;
        font-size: 0.78rem !important;
        border-radius: 9px !important;
        white-space: nowrap !important;
    }
    .hero-banner, .big-hero, .glass-card {
        padding: 14px !important;
        border-radius: 15px !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    .hero-banner h1, .big-hero h1 {
        font-size: 1.2rem !important;
        line-height: 1.25 !important;
    }
    form input:not([type="checkbox"]):not([type="radio"]),
    form select, form textarea, .studio-input {
        width: 100% !important;
        max-width: 100% !important;
        font-size: 16px !important;
        box-sizing: border-box !important;
        touch-action: manipulation !important;
    }
    form button[type="submit"], .btn, .btn-primary, .btn-outline {
        touch-action: manipulation !important;
    }
    video {
        width: 100% !important;
        max-width: 100% !important;
        height: auto !important;
        max-height: 230px !important;
        border-radius: 12px !important;
    }
    .ep-single-speed-bar {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 8px !important;
        margin: 8px 0 !important;
        padding: 7px 10px !important;
        border-radius: 11px !important;
        background: var(--card, #ffffff) !important;
        border: 1px solid var(--border, #cbd5e1) !important;
        overflow-x: auto !important;
        scrollbar-width: none !important;
    }
    .ep-single-speed-bar::-webkit-scrollbar { display: none !important; }
    .ep-speed-btn {
        padding: 6px 10px !important;
        border-radius: 8px !important;
        border: 1px solid var(--border, #cbd5e1) !important;
        background: var(--bg, #f8fafc) !important;
        color: var(--text, #0f172a) !important;
        font-size: 0.76rem !important;
        font-weight: 800 !important;
        cursor: pointer !important;
        flex: 0 0 auto !important;
        touch-action: manipulation !important;
    }
    .ep-speed-btn.active {
        background: var(--accent, #10b981) !important;
        color: #ffffff !important;
        border-color: var(--accent, #10b981) !important;
    }
    .ep-attempted-card {
        border: 2px solid #10b981 !important;
        background: rgba(16, 185, 129, 0.08) !important;
    }
    .ep-attempted-badge {
        display: inline-block !important;
        padding: 3px 9px !important;
        border-radius: 999px !important;
        background: #10b981 !important;
        color: #ffffff !important;
        font-size: 0.72rem !important;
        font-weight: 800 !important;
    }
}
</style>
<script id="edupath-mobile-script-2026">
(function() {
    function epSyncDrawerLock() {
        var dr = document.getElementById("sideDrawer") || document.getElementById("sidebar");
        var isOpen = !!(dr && dr.classList.contains("open"));
        document.documentElement.classList.toggle("ep-drawer-open", isOpen);
        document.body.classList.toggle("ep-drawer-open", isOpen);
    }
    function epSyncMobileSlider() {
        if (window.innerWidth > 768) return;
        var slider = document.getElementById("courseSlider") || document.querySelector(".course-slider");
        if (!slider) return;
        var w = slider.clientWidth;
        if (!w) return;
        Array.from(slider.children).forEach(function(card) {
            card.style.flex = "0 0 " + w + "px";
            card.style.width = w + "px";
            card.style.minWidth = w + "px";
            card.style.maxWidth = w + "px";
        });
    }
    function epEnableSingleClickPortals() {
        if (window.innerWidth > 768) return;
        var cards = document.querySelectorAll(".subj-card, .stream-big-card, .portal-chip");
        cards.forEach(function(card) {
            if (card.dataset.epSingleClickBound) return;
            card.dataset.epSingleClickBound = "1";
            card.addEventListener("click", function(e) {
                if (e.target.closest("a, button, input, select, textarea, form, label")) return;
                var link = card.querySelector("a[href]");
                if (link && link.getAttribute("href")) {
                    window.location.assign(link.getAttribute("href"));
                }
            }, { passive: true });
        });
    }
    function epEnsureSingleSpeedController() {
        var speeds = [0.75, 1, 1.25, 1.5, 2];
        document.querySelectorAll("video").forEach(function(vid, idx) {
            vid.setAttribute("playsinline", "");
            vid.setAttribute("webkit-playsinline", "");
            if (!vid.getAttribute("preload")) vid.setAttribute("preload", "metadata");
            var posterUrl = vid.getAttribute("poster");
            if (
                posterUrl &&
                vid.parentElement &&
                !vid.parentElement.querySelector(".ep-mobile-poster-overlay, .js-thumb-overlay")
            ) {
                var wrap = vid.parentElement;
                if (getComputedStyle(wrap).position === "static") wrap.style.position = "relative";
                var imgOverlay = document.createElement("img");
                imgOverlay.src = posterUrl;
                imgOverlay.alt = "Video Thumbnail";
                imgOverlay.className = "ep-mobile-poster-overlay";
                imgOverlay.style.cssText = "position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border-radius:inherit;z-index:2;pointer-events:none;transition:opacity 0.2s ease;";
                wrap.appendChild(imgOverlay);
                var hidePoster = function() { imgOverlay.style.opacity = "0"; };
                vid.addEventListener("play", hidePoster, { passive: true });
                vid.addEventListener("playing", hidePoster, { passive: true });
                vid.addEventListener("seeking", function() { if (vid.currentTime > 0) hidePoster(); }, { passive: true });
            }
            if (!vid.id) vid.id = "epVid_" + idx;
            var parent = vid.parentElement;
            if (parent) {
                var extraBars = parent.querySelectorAll(".ep-single-speed-bar");
                for (var b = 1; b < extraBars.length; b++) extraBars[b].remove();
            }
            var nextEl = vid.nextElementSibling;
            if (nextEl && nextEl.classList && nextEl.classList.contains("ep-single-speed-bar")) return;
            var bar = document.createElement("div");
            bar.className = "ep-single-speed-bar";
            var label = document.createElement("span");
            label.textContent = "Speed";
            label.style.cssText = "font-size:0.74rem;font-weight:800;opacity:0.75;flex:0 0 auto;";
            bar.appendChild(label);
            var btnsWrap = document.createElement("div");
            btnsWrap.style.cssText = "display:flex;gap:5px;align-items:center;";
            speeds.forEach(function(sp) {
                var btn = document.createElement("button");
                btn.type = "button";
                btn.className = "ep-speed-btn" + (sp === 1 ? " active" : "");
                btn.textContent = sp + "x";
                btn.addEventListener("click", function(ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    vid.playbackRate = sp;
                    btnsWrap.querySelectorAll(".ep-speed-btn").forEach(function(x) { x.classList.remove("active"); });
                    btn.classList.add("active");
                });
                btnsWrap.appendChild(btn);
            });
            bar.appendChild(btnsWrap);
            vid.insertAdjacentElement("afterend", bar);
        });
    }
    document.addEventListener("DOMContentLoaded", function() {
        epSyncMobileSlider();
        epEnableSingleClickPortals();
        epEnsureSingleSpeedController();
        epSyncDrawerLock();
        var dr = document.getElementById("sideDrawer") || document.getElementById("sidebar");
        if (dr && typeof MutationObserver !== "undefined") {
            new MutationObserver(epSyncDrawerLock).observe(dr, { attributes: true, attributeFilter: ["class"] });
        }
    });
    window.addEventListener("resize", epSyncMobileSlider, { passive: true });
})();
</script>
"""

VIDEO_SMOOTH_STREAM_SCRIPT = """
<script id="edupath-smooth-video-2026">
(function() {
    var EP_QUALITIES = ["240p", "360p", "480p", "720p"];
    var EP_HEIGHTS = { "240p": 240, "360p": 360, "480p": 480, "720p": 720 };
    function epMimeForSrc(src) {
        var clean = (src || "").split("?")[0].toLowerCase();
        if (clean.endsWith(".mov")) return "video/quicktime";
        if (clean.endsWith(".webm")) return "video/webm";
        if (clean.endsWith(".ogg") || clean.endsWith(".ogv")) return "video/ogg";
        return "video/mp4";
    }
    function epQualityUrl(vid, q) {
        if (!vid) return "";
        var base = vid.getAttribute("data-base-src") || vid.getAttribute("src") || "";
        var qMap = {
            "240p": vid.getAttribute("data-240p-src"),
            "360p": vid.getAttribute("data-360p-src"),
            "480p": vid.getAttribute("data-480p-src"),
            "720p": vid.getAttribute("data-720p-src")
        };
        return qMap[q] || base;
    }
    function epApplyQuality(vid, quality, btnEl) {
        if (!vid || !EP_HEIGHTS[quality]) return;
        EP_QUALITIES.forEach(function(q) { vid.classList.remove("vid-mode-" + q); });
        vid.classList.add("vid-mode-" + quality);
        vid.setAttribute("data-active-quality", quality);
        var targetSrc = epQualityUrl(vid, quality);
        var curSrc = vid.getAttribute("src") || "";
        var curTime = vid.currentTime || 0;
        var curRate = vid.playbackRate || 1;
        var wasPlaying = !vid.paused;
        if (targetSrc && targetSrc !== curSrc) {
            var mime = epMimeForSrc(targetSrc);
            var srcNode = vid.querySelector("source");
            if (srcNode) { srcNode.setAttribute("src", targetSrc); srcNode.setAttribute("type", mime); }
            vid.setAttribute("src", targetSrc);
            vid.load();
            vid.addEventListener("loadedmetadata", function onMeta() {
                vid.removeEventListener("loadedmetadata", onMeta);
                vid.playbackRate = curRate;
                if (curTime > 0 && isFinite(curTime)) {
                    try { vid.currentTime = Math.min(curTime, isFinite(vid.duration) ? vid.duration : curTime); } catch (e) {}
                }
                if (wasPlaying) { vid.play().catch(function() {}); }
            });
        }
        if (btnEl) {
            var group = btnEl.parentElement;
            if (group) group.querySelectorAll(".vid-q-btn, .ep-q-btn").forEach(function(b) { b.classList.remove("active"); });
            btnEl.classList.add("active");
        }
    }
    function epEnhanceAllVideos() {
        document.querySelectorAll("video").forEach(function(vid, idx) {
            vid.setAttribute("playsinline", "");
            vid.setAttribute("webkit-playsinline", "");
            if (!vid.id) vid.id = "epAutoVid_" + idx;
            var existingSrc = vid.getAttribute("src") || (vid.querySelector("source") ? vid.querySelector("source").getAttribute("src") : "");
            if (existingSrc && !vid.getAttribute("data-base-src")) vid.setAttribute("data-base-src", existingSrc);
            if (!vid.getAttribute("preload")) vid.setAttribute("preload", "auto");
            vid.addEventListener("waiting", function() {
                if (vid.networkState === 2) {
                    vid.setAttribute("preload", "auto");
                }
            }, { passive: true });
            vid.addEventListener("stalled", function() {
                if (vid.readyState < 2 && vid.getAttribute("preload") !== "auto") vid.setAttribute("preload", "auto");
            }, { passive: true });
        });
    }
    document.addEventListener("click", function(e) {
        var qBtn = e.target.closest(".ep-q-btn, .vid-q-btn");
        if (!qBtn) return;
        var q = qBtn.getAttribute("data-q");
        var targetId = qBtn.getAttribute("data-target-vid");
        var vidId = qBtn.getAttribute("data-vid");
        var vid = targetId ? document.getElementById(targetId) : (vidId ? document.getElementById("videoPlayer_" + vidId) : null);
        if (!vid && qBtn.closest(".lec-card")) vid = qBtn.closest(".lec-card").querySelector("video");
        if (vid && q) epApplyQuality(vid, q, qBtn);
    });
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", epEnhanceAllVideos);
    else epEnhanceAllVideos();
})();
</script>
"""


def has_allowed_ext(filename: str, exts: tuple) -> bool:
    if not filename:
        return False
    return os.path.splitext(filename.strip().lower())[1] in exts


def get_csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_hex(16)
        session["_csrf_token"] = token
    return token


def verify_csrf() -> bool:
    expected = session.get("_csrf_token")
    if not expected:
        return False
    sent = (
        request.form.get("csrf_token", "").strip()
        or request.headers.get("X-CSRF-Token", "").strip()
    )
    return bool(sent and secrets.compare_digest(sent, expected))


def format_num(val) -> str:
    try:
        f = float(val or 0)
        if f.is_integer():
            return str(int(f))
        return f"{f:.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return "0"


def default_marking_for_portal(portal_type: str):
    p = (portal_type or "").strip().lower()
    if any(k in p for k in ("class 10", "10", "state", "bseb", "upmsp", "mpbse", "rbse", "jac")):
        return 1.0, 0.0
    return 4.0, 1.0


def _save_video_with_transcode(vid_file, upload_folder: str) -> str:
    orig_name = secure_filename(f"vid_{int(datetime.now().timestamp())}_{vid_file.filename}")
    dest_path = os.path.join(upload_folder, orig_name)
    vid_file.save(dest_path)

    ext = os.path.splitext(orig_name.lower())[1]
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin and ext in (".mov", ".avi", ".mkv", ".m4v", ".3gp", ".mp4"):
        mp4_name = os.path.splitext(orig_name)[0] + "_web.mp4"
        mp4_path = os.path.join(upload_folder, mp4_name)
        try:
            cmd = [
                ffmpeg_bin,
                "-y",
                "-i",
                dest_path,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "25",
                "-vf",
                "scale='min(1280,iw)':-2",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                mp4_path,
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
            if res.returncode == 0 and os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0:
                if ext != ".mp4":
                    try:
                        os.remove(dest_path)
                    except OSError:
                        pass
                return mp4_name
        except Exception as exc:
            app.logger.warning("FFmpeg faststart transcode skipped: %s", exc)
    return orig_name


@app.before_request
def keep_session_persistent():
    if "user_id" in session:
        session.permanent = True


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(err):
    flash("File size exceeds the allowed limit (Max 500 MB).", "error")
    return redirect(request.referrer or url_for("admin_panel"))


@app.after_request
def apply_security_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


def _inject_csrf_into_forms(html: str, token: str) -> str:
    if not token or "<form" not in html:
        return html
    pattern = re.compile(r'(<form [^>]*method\s*=\s*[\'"]?post[\'"]?[^>]*>)', re.IGNORECASE)

    def _add_hidden(match):
        tag = match.group(1)
        return f'{tag}\n<input type="hidden" name="csrf_token" value="{token}">'

    return pattern.sub(_add_hidden, html)


def _build_admin_mock_widget(context: dict) -> str:
    mock_tests = context.get("mock_tests") or []
    token = context.get("csrf_token", "")

    portal_opts = "".join(f'<option value="{p}">{p}</option>' for p in MOCK_PORTAL_CHOICES)
    test_opts = "".join(
        f'<option value="{t["id"]}">{t["title"]} [{t["portal_type"]}] (+{format_num(t["marks_per_question"])} / -{format_num(t["negative_marks"])})</option>'
        for t in mock_tests
    )

    test_rows = []
    for t in mock_tests:
        neg_val = float(t.get("negative_marks") or 0)
        pos_val = float(t.get("marks_per_question") or 1)
        neg_badge = (
            f'<span style="background:#fee2e2;color:#b91c1c;padding:3px 9px;border-radius:999px;font-size:0.75rem;font-weight:800;">NEGATIVE: -{format_num(neg_val)}</span>'
            if neg_val > 0
            else '<span style="background:#dcfce7;color:#15803d;padding:3px 9px;border-radius:999px;font-size:0.75rem;font-weight:800;">NO NEGATIVE (0)</span>'
        )
        test_rows.append(f"""
        <div style="border:1px solid var(--border,#cbd5e1);border-radius:12px;padding:12px;margin-bottom:10px;background:var(--bg,#f8fafc);">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <strong>{t["title"]}</strong>
                    <span style="font-size:0.8rem;opacity:0.8;"> • {t["portal_type"]} • {t["subject"]} • {t["q_count"]} Qs • {t["attempt_count"]} Attempts</span>
                </div>
                <div>{neg_badge}</div>
            </div>
            <form method="POST" action="/mock-test" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px;">
                <input type="hidden" name="csrf_token" value="{token}">
                <input type="hidden" name="action" value="update_test_settings">
                <input type="hidden" name="test_id" value="{t["id"]}">
                <input type="hidden" name="redirect_to" value="/admin">
                <label style="font-size:0.78rem;font-weight:700;">+Marks:
                    <input type="number" step="0.25" min="0.25" max="20" name="marks_per_question" value="{format_num(pos_val)}" style="width:74px;padding:5px 7px;border-radius:7px;border:1px solid #cbd5e1;">
                </label>
                <label style="font-size:0.78rem;font-weight:700;">-Negative:
                    <input type="number" step="0.25" min="0" max="10" name="negative_marks" value="{format_num(neg_val)}" style="width:74px;padding:5px 7px;border-radius:7px;border:1px solid #cbd5e1;">
                </label>
                <button type="submit" style="padding:6px 12px;border:none;border-radius:8px;background:#10b981;color:#fff;font-size:0.78rem;font-weight:700;cursor:pointer;">Save Marking</button>
                <a href="/mock-test?test_id={t["id"]}" style="padding:6px 12px;border-radius:8px;border:1px solid #cbd5e1;text-decoration:none;font-size:0.78rem;font-weight:700;color:inherit;">Open Test & Leaderboard</a>
            </form>
        </div>
        """)

    return f"""
    <section id="epAdminMockControl" style="max-width:1100px;margin:18px auto 28px;padding:18px;border-radius:16px;border:1px solid var(--border,#cbd5e1);background:var(--card,#ffffff);color:var(--text,#0f172a);box-shadow:0 6px 20px rgba(0,0,0,0.05);">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:14px;">
            <div>
                <h2 style="margin:0;font-size:1.2rem;">Mock Test, Negative Marking & Leaderboard Control</h2>
                <p style="margin:4px 0 0;font-size:0.84rem;opacity:0.8;">Class 10 and State Boards default to No Negative (+1 / 0), while JEE, NEET, Class 11, and Class 12 default to Negative (+4 / -1). You can customize marking rules for any test below.</p>
            </div>
            <a href="/mock-test" style="padding:8px 14px;border-radius:10px;background:#10b981;color:#fff;text-decoration:none;font-weight:800;font-size:0.84rem;">Open Full Mock Test Portal →</a>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px;margin-bottom:16px;">
            <form method="POST" action="/mock-test" style="border:1px solid var(--border,#e2e8f0);border-radius:12px;padding:14px;">
                <h3 style="margin:0 0 10px;font-size:1rem;">1. Create a Course-Wise Mock Test</h3>
                <input type="hidden" name="csrf_token" value="{token}">
                <input type="hidden" name="action" value="create_test">
                <input type="hidden" name="redirect_to" value="/admin">
                <input type="text" name="title" placeholder="Test Title (e.g. Class 10 Science Full Mock 1)" required style="width:100%;padding:8px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;box-sizing:border-box;">
                <select name="portal_type" id="epAdminPortalSelect" onchange="epAutoFillMarking(this.value)" style="width:100%;padding:8px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;box-sizing:border-box;">
                    {portal_opts}
                </select>
                <input type="text" name="subject" placeholder="Subject (e.g. Science, Physics, Maths)" style="width:100%;padding:8px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;box-sizing:border-box;">
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:10px;">
                    <div>
                        <label style="font-size:0.72rem;font-weight:700;">Time (min)</label>
                        <input type="number" name="duration_minutes" value="20" min="1" max="300" style="width:100%;padding:7px;border-radius:8px;border:1px solid #cbd5e1;box-sizing:border-box;">
                    </div>
                    <div>
                        <label style="font-size:0.72rem;font-weight:700;">+Marks/Q</label>
                        <input type="number" step="0.25" min="0.25" max="20" name="marks_per_question" id="epAdminPosMarks" value="1" style="width:100%;padding:7px;border-radius:8px;border:1px solid #cbd5e1;box-sizing:border-box;">
                    </div>
                    <div>
                        <label style="font-size:0.72rem;font-weight:700;">-Negative</label>
                        <input type="number" step="0.25" min="0" max="10" name="negative_marks" id="epAdminNegMarks" value="0" style="width:100%;padding:7px;border-radius:8px;border:1px solid #cbd5e1;box-sizing:border-box;">
                    </div>
                </div>
                <button type="submit" style="width:100%;padding:9px;border:none;border-radius:9px;background:#10b981;color:#fff;font-weight:800;cursor:pointer;">+ Create Mock Test</button>
            </form>

            <form method="POST" action="/mock-test" style="border:1px solid var(--border,#e2e8f0);border-radius:12px;padding:14px;">
                <h3 style="margin:0 0 10px;font-size:1rem;">2. Add an MCQ Question to a Test</h3>
                <input type="hidden" name="csrf_token" value="{token}">
                <input type="hidden" name="action" value="add_question">
                <input type="hidden" name="redirect_to" value="/admin">
                <select name="test_id" required style="width:100%;padding:8px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;box-sizing:border-box;">
                    {test_opts or '<option value="">Create a test first above</option>'}
                </select>
                <textarea name="question_text" rows="2" placeholder="Enter MCQ question..." required style="width:100%;padding:8px;margin-bottom:6px;border-radius:8px;border:1px solid #cbd5e1;box-sizing:border-box;"></textarea>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px;">
                    <input type="text" name="option_a" placeholder="Option A" required style="padding:7px;border-radius:8px;border:1px solid #cbd5e1;">
                    <input type="text" name="option_b" placeholder="Option B" required style="padding:7px;border-radius:8px;border:1px solid #cbd5e1;">
                    <input type="text" name="option_c" placeholder="Option C" required style="padding:7px;border-radius:8px;border:1px solid #cbd5e1;">
                    <input type="text" name="option_d" placeholder="Option D" required style="padding:7px;border-radius:8px;border:1px solid #cbd5e1;">
                </div>
                <div style="display:flex;gap:8px;">
                    <select name="correct_option" style="flex:1;padding:8px;border-radius:8px;border:1px solid #cbd5e1;">
                        <option value="A">Correct: A</option>
                        <option value="B">Correct: B</option>
                        <option value="C">Correct: C</option>
                        <option value="D">Correct: D</option>
                    </select>
                    <button type="submit" style="flex:1;padding:9px;border:none;border-radius:9px;background:#10b981;color:#fff;font-weight:800;cursor:pointer;">+ Add MCQ</button>
                </div>
            </form>
        </div>

        <div>
            <h3 style="margin:0 0 10px;font-size:1rem;">3. Active Tests & Negative Marking Control ({len(mock_tests)})</h3>
            {"".join(test_rows) or '<p style="opacity:0.75;font-size:0.88rem;">No mock tests have been created yet.</p>'}
        </div>
    </section>
    <script>
    function epAutoFillMarking(portal) {{
        var pos = document.getElementById("epAdminPosMarks");
        var neg = document.getElementById("epAdminNegMarks");
        if (!pos || !neg) return;
        if (portal === "Class 10" || portal === "State Boards") {{
            pos.value = "1";
            neg.value = "0";
        }} else {{
            pos.value = "4";
            neg.value = "1";
        }}
    }}
    </script>
    """


def _build_admin_student_controls_widget(context: dict) -> str:
    students = context.get("students") or []
    token = context.get("csrf_token", "")
    rows_html = []
    for s in students:
        s_dict = dict(s)
        sid = s_dict.get("id")
        sname = s_dict.get("name") or "Student"
        semail = s_dict.get("email") or ""
        sclass = s_dict.get("student_class") or ""
        is_blocked = int(s_dict.get("is_blocked") or 0) == 1
        badge = (
            '<span style="background:#fee2e2;color:#b91c1c;padding:2px 8px;border-radius:999px;font-size:0.72rem;font-weight:800;margin-left:6px;">BLOCKED</span>'
            if is_blocked
            else '<span style="background:#dcfce7;color:#15803d;padding:2px 8px;border-radius:999px;font-size:0.72rem;font-weight:800;margin-left:6px;">ACTIVE</span>'
        )
        toggle_label = "Unblock" if is_blocked else "Block"
        toggle_style = (
            "background:#10b981;color:#fff;border:none;"
            if is_blocked
            else "background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;"
        )
        rows_html.append(f"""
        <div style="border:1px solid var(--border,#cbd5e1);border-radius:12px;padding:12px;margin-bottom:10px;background:var(--bg,#f8fafc);">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <strong>{sname}</strong>{badge}
                    <div style="font-size:0.78rem;opacity:0.78;">{semail} • {sclass}</div>
                </div>
                <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                    <button type="button" onclick="epToggleStudentMsgBox({sid})" style="padding:6px 11px;border-radius:8px;border:1px solid #cbd5e1;background:#fff;color:#0f172a;font-size:0.78rem;font-weight:700;cursor:pointer;">Direct Message</button>
                    <form method="POST" action="/toggle-block-user/{sid}" style="margin:0;">
                        <input type="hidden" name="csrf_token" value="{token}">
                        <button type="submit" style="padding:6px 11px;border-radius:8px;{toggle_style}font-size:0.78rem;font-weight:700;cursor:pointer;">{toggle_label}</button>
                    </form>
                </div>
            </div>
            <div id="epStudentMsgBox_{sid}" style="display:none;margin-top:10px;padding-top:10px;border-top:1px dashed #cbd5e1;">
                <form method="POST" action="/send-personal-message/{sid}" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0;">
                    <input type="hidden" name="csrf_token" value="{token}">
                    <input type="text" name="personal_message" placeholder="Write a direct message to {sname}..." required style="flex:1;min-width:200px;padding:7px 10px;border-radius:8px;border:1px solid #cbd5e1;">
                    <button type="submit" style="padding:7px 14px;border:none;border-radius:8px;background:#10b981;color:#fff;font-size:0.78rem;font-weight:700;cursor:pointer;">Send Direct Message</button>
                </form>
            </div>
        </div>
        """)

    return f"""
    <section id="epAdminStudentControl" style="max-width:1100px;margin:18px auto 28px;padding:18px;border-radius:16px;border:1px solid var(--border,#cbd5e1);background:var(--card,#ffffff);color:var(--text,#0f172a);box-shadow:0 6px 20px rgba(0,0,0,0.05);">
        <h2 style="margin:0 0 12px;font-size:1.15rem;">Students — Direct Message & Block / Unblock ({len(students)})</h2>
        {"".join(rows_html) or '<p style="opacity:0.75;font-size:0.88rem;">No students registered yet.</p>'}
    </section>
    <script>
    function epToggleStudentMsgBox(uid) {{
        var el = document.getElementById("epStudentMsgBox_" + uid);
        if (!el) return;
        el.style.display = (el.style.display === "none" || !el.style.display) ? "block" : "none";
    }}
    </script>
    """


def render_page(template_name: str, extra_mobile_html: str = "", **context):
    token = get_csrf_token()
    context.setdefault("csrf_token", token)
    context.setdefault("MOCK_PORTAL_CHOICES", MOCK_PORTAL_CHOICES)
    context.setdefault("format_num", format_num)
    if template_name == "mock_test.html":
        for cand in ("mock_test.html", "mock_test_5_updated_v2.html", "mock_test_5_updated.html"):
            if os.path.exists(os.path.join(TEMPLATE_DIR, cand)):
                template_name = cand
                break
    tpl_path = os.path.join(TEMPLATE_DIR, template_name)
    if os.path.exists(tpl_path):
        try:
            html = render_template(template_name, **context)
        except Exception as tpl_err:
            app.logger.warning("Template fallback triggered for %s: %s", template_name, tpl_err)
            if template_name == "mock_test.html":
                html = _render_fallback_mock_test(context)
            elif template_name in ("ai_doubt.html", "message_box.html"):
                html = _render_fallback_ai_doubt(context)
            else:
                raise
    elif template_name == "mock_test.html":
        html = _render_fallback_mock_test(context)
    elif template_name in ("ai_doubt.html", "message_box.html"):
        html = _render_fallback_ai_doubt(context)
    else:
        html = render_template(template_name, **context)

    if template_name == "admin_panel.html":
        extras = []
        if "epAdminMockControl" not in html:
            extras.append(_build_admin_mock_widget(context))
        if "send-personal-message" not in html and "epAdminStudentControl" not in html:
            extras.append(_build_admin_student_controls_widget(context))
        if extras:
            addon = "\n".join(extras)
            if "</main>" in html:
                html = html.replace("</main>", f"{addon}\n</main>", 1)
            elif "</body>" in html:
                html = html.replace("</body>", f"{addon}\n</body>", 1)
            else:
                html = f"{html}\n{addon}"

    html = _inject_csrf_into_forms(html, token)
    injected = f"{MOBILE_EDUPATH_ENHANCEMENT}\n{VIDEO_SMOOTH_STREAM_SCRIPT}\n{extra_mobile_html}".strip()
    if injected:
        if "</body>" in html:
            html = html.replace("</body>", f"{injected}\n</body>", 1)
        else:
            html = f"{html}\n{injected}"
    return html


def _render_fallback_mock_test(ctx: dict) -> str:
    user = ctx.get("user") or {}
    is_admin = (user.get("role") == "admin")
    tests = ctx.get("tests") or []
    active_test = ctx.get("active_test")
    questions = ctx.get("questions") or []
    my_attempts = ctx.get("my_attempts") or []
    leaderboard = ctx.get("leaderboard") or []
    result_data = ctx.get("result_data")
    active_portal = ctx.get("active_portal") or "All"
    token = ctx.get("csrf_token", "")

    filter_tabs = []
    for p in ["All"] + MOCK_PORTAL_CHOICES:
        is_sel = (active_portal.lower() == p.lower())
        filter_tabs.append(
            f'<a href="/mock-test?portal={p}" style="display:inline-block;padding:6px 12px;margin:3px;border-radius:999px;text-decoration:none;font-size:0.82rem;font-weight:700;border:1px solid #cbd5e1;background:{"#0f172a" if is_sel else "#fff"};color:{"#fff" if is_sel else "#0f172a"};">{p}</a>'
        )

    test_pills = []
    for t in tests:
        is_curr = bool(active_test and active_test["id"] == t["id"])
        neg_val = float(t.get("negative_marks") or 0)
        tag = f"-{format_num(neg_val)}" if neg_val > 0 else "No Neg"
        test_pills.append(
            f'<a href="/mock-test?portal={active_portal}&test_id={t["id"]}" style="display:inline-block;padding:8px 14px;margin:4px;border-radius:10px;text-decoration:none;font-weight:700;border:1px solid #cbd5e1;background:{"#10b981" if is_curr else "#fff"};color:{"#fff" if is_curr else "#0f172a"};">{t["title"]} • {t["portal_type"]} ({t["q_count"]} Q | {tag})</a>'
        )
    test_pills_html = "".join(test_pills) or "<p>No mock tests are available in this category yet.</p>"

    admin_box = ""
    if is_admin:
        portal_opts = "".join(f'<option value="{p}">{p}</option>' for p in MOCK_PORTAL_CHOICES)
        test_opts = "".join(
            f'<option value="{t["id"]}" {"selected" if active_test and active_test["id"] == t["id"] else ""}>{t["title"]} [{t["portal_type"]}]</option>'
            for t in tests
        )
        active_settings_form = ""
        if active_test:
            a_pos = float(active_test.get("marks_per_question") or 1)
            a_neg = float(active_test.get("negative_marks") or 0)
            active_settings_form = f"""
            <hr style="margin:14px 0;border:0;border-top:1px solid #e2e8f0;">
            <h4 style="margin:0 0 8px;">Selected Test Marking & Control: {active_test["title"]}</h4>
            <form method="POST" action="/mock-test" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
                <input type="hidden" name="csrf_token" value="{token}">
                <input type="hidden" name="action" value="update_test_settings">
                <input type="hidden" name="test_id" value="{active_test["id"]}">
                <label style="font-size:0.82rem;font-weight:700;">+Marks/Q:
                    <input type="number" step="0.25" min="0.25" max="20" name="marks_per_question" value="{format_num(a_pos)}" style="width:76px;padding:7px;border-radius:8px;border:1px solid #cbd5e1;">
                </label>
                <label style="font-size:0.82rem;font-weight:700;">-Negative/Wrong:
                    <input type="number" step="0.25" min="0" max="10" name="negative_marks" value="{format_num(a_neg)}" style="width:76px;padding:7px;border-radius:8px;border:1px solid #cbd5e1;">
                </label>
                <button type="submit" style="padding:8px 14px;border:none;border-radius:8px;background:#0f172a;color:#fff;font-weight:700;cursor:pointer;">Update Marking</button>
            </form>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;">
                <form method="POST" action="/mock-test" onsubmit="return confirm('Reset leaderboard attempts for this test?');">
                    <input type="hidden" name="csrf_token" value="{token}">
                    <input type="hidden" name="action" value="reset_leaderboard">
                    <input type="hidden" name="test_id" value="{active_test["id"]}">
                    <button type="submit" style="padding:7px 12px;border:1px solid #f59e0b;border-radius:8px;background:#fffbeb;color:#b45309;font-weight:700;cursor:pointer;">Reset Leaderboard</button>
                </form>
                <form method="POST" action="/mock-test" onsubmit="return confirm('Delete this entire mock test?');">
                    <input type="hidden" name="csrf_token" value="{token}">
                    <input type="hidden" name="action" value="delete_test">
                    <input type="hidden" name="test_id" value="{active_test["id"]}">
                    <button type="submit" style="padding:7px 12px;border:1px solid #ef4444;border-radius:8px;background:#fef2f2;color:#b91c1c;font-weight:700;cursor:pointer;">Delete Test</button>
                </form>
            </div>
            """

        admin_box = f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:16px;margin-bottom:18px;">
            <h3 style="margin-top:0;">Admin: Create a Mock Test by Class or Exam Track</h3>
            <p style="font-size:0.83rem;color:#475569;margin-top:-4px;">Class 10 and State Boards default to <strong>No Negative (+1 / 0)</strong>, while JEE, NEET, Class 11, and Class 12 default to <strong>Negative (+4 / -1)</strong>. You can adjust marking values before creating or editing any test.</p>
            <form method="POST" action="/mock-test">
                <input type="hidden" name="csrf_token" value="{token}">
                <input type="hidden" name="action" value="create_test">
                <input type="text" name="title" placeholder="Test Title (e.g. Class 10 Science Chapter 1 MCQ)" required style="padding:9px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;">
                <select name="portal_type" onchange="if(this.value==='Class 10'||this.value==='State Boards'){{this.form.marks_per_question.value='1';this.form.negative_marks.value='0';}}else{{this.form.marks_per_question.value='4';this.form.negative_marks.value='1';}}" style="padding:9px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;">
                    {portal_opts}
                </select>
                <input type="text" name="subject" placeholder="Subject (e.g. Science (086), Physics)" style="padding:9px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;">
                <input type="number" name="duration_minutes" value="15" min="1" max="300" placeholder="Minutes" style="width:95px;padding:9px;margin-bottom:10px;border-radius:8px;border:1px solid #cbd5e1;">
                <input type="number" step="0.25" min="0.25" max="20" name="marks_per_question" value="1" placeholder="+Marks" style="width:95px;padding:9px;margin-bottom:10px;border-radius:8px;border:1px solid #cbd5e1;">
                <input type="number" step="0.25" min="0" max="10" name="negative_marks" value="0" placeholder="-Negative" style="width:95px;padding:9px;margin-bottom:10px;border-radius:8px;border:1px solid #cbd5e1;">
                <button type="submit" style="padding:10px 16px;border:none;border-radius:9px;background:#10b981;color:#fff;font-weight:700;cursor:pointer;">Create Test</button>
            </form>
            {active_settings_form}
            <hr style="margin:16px 0;border:0;border-top:1px solid #e2e8f0;">
            <h3 style="margin-top:0;">Admin: Add an MCQ Question</h3>
            <form method="POST" action="/mock-test">
                <input type="hidden" name="csrf_token" value="{token}">
                <input type="hidden" name="action" value="add_question">
                <select name="test_id" style="padding:9px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;">{test_opts}</select>
                <textarea name="question_text" rows="2" placeholder="Enter question text..." required style="width:100%;padding:9px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;box-sizing:border-box;"></textarea>
                <input type="text" name="option_a" placeholder="Option A" required style="padding:9px;margin-bottom:6px;border-radius:8px;border:1px solid #cbd5e1;">
                <input type="text" name="option_b" placeholder="Option B" required style="padding:9px;margin-bottom:6px;border-radius:8px;border:1px solid #cbd5e1;">
                <input type="text" name="option_c" placeholder="Option C" required style="padding:9px;margin-bottom:6px;border-radius:8px;border:1px solid #cbd5e1;">
                <input type="text" name="option_d" placeholder="Option D" required style="padding:9px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;">
                <select name="correct_option" style="padding:9px;margin-bottom:10px;border-radius:8px;border:1px solid #cbd5e1;">
                    <option value="A">Correct Option: A</option>
                    <option value="B">Correct Option: B</option>
                    <option value="C">Correct Option: C</option>
                    <option value="D">Correct Option: D</option>
                </select>
                <button type="submit" style="padding:10px 16px;border:none;border-radius:9px;background:#10b981;color:#fff;font-weight:700;cursor:pointer;">Add Question</button>
            </form>
        </div>
        """

    result_html = ""
    if result_data:
        rev_items = "".join(
            f'<li style="margin-bottom:6px;"><strong>{r["question_text"]}</strong> — Your choice: <b>{r["chosen"]}</b> | Correct answer: <b>{r["correct_option"]}</b> ({"+" + format_num(r["marks_delta"]) if r["status"] == "correct" else ("-" + format_num(abs(r["marks_delta"])) if r["status"] == "wrong" and r["marks_delta"] < 0 else ("0 (Incorrect)" if r["status"] == "wrong" else "0 (Unattempted)"))})</li>'
            for r in result_data.get("review") or []
        )
        result_html = f"""
        <div style="background:#ecfdf5;border:1px solid #10b981;border-radius:14px;padding:16px;margin-bottom:18px;">
            <h3 style="margin-top:0;">Result: {result_data["test_title"]}</h3>
            <p style="margin:6px 0;"><strong>Net Score:</strong> {format_num(result_data["score"])} / {format_num(result_data["max_marks"])} ({result_data["pct"]}%) • <strong>Rank: #{result_data["rank"]}</strong></p>
            <p style="margin:6px 0;font-size:0.9rem;">Correct: <b>{result_data["correct"]}</b> (+{format_num(result_data["positive_earned"])}) | Incorrect: <b>{result_data["wrong"]}</b> (-{format_num(result_data["negative_deducted"])}) | Unattempted: <b>{result_data["unattempted"]}</b></p>
            <ul>{rev_items}</ul>
        </div>
        """

    quiz_html = ""
    if active_test and questions:
        pos_m = float(active_test.get("marks_per_question") or 1)
        neg_m = float(active_test.get("negative_marks") or 0)
        marking_pill = (
            f'<span style="background:#fee2e2;color:#b91c1c;padding:4px 10px;border-radius:999px;font-size:0.8rem;font-weight:800;">Marking: +{format_num(pos_m)} Correct | -{format_num(neg_m)} Incorrect</span>'
            if neg_m > 0
            else f'<span style="background:#dcfce7;color:#15803d;padding:4px 10px;border-radius:999px;font-size:0.8rem;font-weight:800;">Marking: +{format_num(pos_m)} Correct | No Negative Marking (0)</span>'
        )
        q_blocks = []
        for idx, q in enumerate(questions, start=1):
            del_q_btn = ""
            if is_admin:
                del_q_btn = f'<button type="submit" form="delQForm_{q["id"]}" style="float:right;background:#fef2f2;color:#dc2626;border:1px solid #fecaca;border-radius:7px;padding:3px 9px;font-size:0.75rem;font-weight:700;cursor:pointer;">Delete Q</button>'
            q_blocks.append(f"""
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px;margin-bottom:12px;">
                {del_q_btn}
                <p style="font-weight:700;margin-top:0;">Q{idx}. {q["question_text"]}</p>
                <label style="display:block;margin:5px 0;"><input type="radio" name="q_{q["id"]}" value="A"> A. {q["option_a"]}</label>
                <label style="display:block;margin:5px 0;"><input type="radio" name="q_{q["id"]}" value="B"> B. {q["option_b"]}</label>
                <label style="display:block;margin:5px 0;"><input type="radio" name="q_{q["id"]}" value="C"> C. {q["option_c"]}</label>
                <label style="display:block;margin:5px 0;"><input type="radio" name="q_{q["id"]}" value="D"> D. {q["option_d"]}</label>
            </div>
            """)
        del_q_forms = "".join(
            f'<form id="delQForm_{q["id"]}" method="POST" action="/mock-test"><input type="hidden" name="csrf_token" value="{token}"><input type="hidden" name="action" value="delete_question"><input type="hidden" name="test_id" value="{active_test["id"]}"><input type="hidden" name="question_id" value="{q["id"]}"></form>'
            for q in questions
        ) if is_admin else ""

        dur_sec = int(active_test.get("duration_minutes") or 15) * 60
        quiz_html = f"""
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:16px;margin-bottom:18px;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <h2 style="margin:0;">{active_test["title"]}</h2>
                <span id="epMockTimer" style="background:#0f172a;color:#fff;padding:6px 12px;border-radius:999px;font-weight:800;font-size:0.88rem;">{active_test["duration_minutes"]}:00</span>
            </div>
            <p style="color:#64748b;margin:8px 0;">Track: <strong>{active_test["portal_type"]}</strong> | Subject: {active_test["subject"]} | {marking_pill}</p>
            <form id="epMockQuizForm" method="POST" action="/mock-test/{active_test["id"]}/submit">
                <input type="hidden" name="csrf_token" value="{token}">
                {"".join(q_blocks)}
                <button type="submit" style="padding:11px 20px;border:none;border-radius:10px;background:#10b981;color:#fff;font-weight:800;cursor:pointer;">Submit Test</button>
            </form>
            {del_q_forms}
        </div>
        <script>
        (function(){{
            var rem = {dur_sec};
            var el = document.getElementById("epMockTimer");
            var frm = document.getElementById("epMockQuizForm");
            if (!el || !frm) return;
            var iv = setInterval(function(){{
                rem--;
                if (rem <= 0) {{
                    clearInterval(iv);
                    el.textContent = "Time Up! Submitting...";
                    frm.submit();
                    return;
                }}
                var m = Math.floor(rem / 60);
                var s = rem % 60;
                el.textContent = m + ":" + (s < 10 ? "0" + s : s);
            }}, 1000);
        }})();
        </script>
        """
    elif active_test:
        quiz_html = f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:16px;margin-bottom:18px;"><h3>{active_test["title"]}</h3><p>No questions have been added to this test yet.</p></div>'

    lb_rows = []
    for idx, row in enumerate(leaderboard, start=1):
        rank_label = f"#{idx}"
        lb_rows.append(f"""
        <tr style="border-bottom:1px solid #e2e8f0;">
            <td style="padding:9px;font-weight:800;">{rank_label}</td>
            <td style="padding:9px;font-weight:700;">{row["user_name"]}</td>
            <td style="padding:9px;font-weight:800;color:#059669;">{format_num(row["best_score"])} / {format_num(row["max_marks"])}</td>
            <td style="padding:9px;">{row["best_pct"]}%</td>
            <td style="padding:9px;font-size:0.82rem;color:#64748b;">{row["submitted_at"] or ""}</td>
        </tr>
        """)
    active_title_suffix = f"— {active_test['title']}" if active_test else ""
    leaderboard_html = f"""
    <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:16px;margin-bottom:18px;overflow-x:auto;">
        <h3 style="margin-top:0;">Live Leaderboard {active_title_suffix}</h3>
        <table style="width:100%;border-collapse:collapse;text-align:left;font-size:0.9rem;">
            <thead>
                <tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0;">
                    <th style="padding:9px;">Rank</th>
                    <th style="padding:9px;">Student</th>
                    <th style="padding:9px;">Best Score</th>
                    <th style="padding:9px;">Accuracy</th>
                    <th style="padding:9px;">Submitted</th>
                </tr>
            </thead>
            <tbody>{"".join(lb_rows) or '<tr><td colspan="5" style="padding:10px;color:#64748b;">No attempts recorded for this test yet.</td></tr>'}</tbody>
        </table>
    </div>
    """

    att_items = "".join(
        f'<li>{a.get("test_title") or "Mock Test"} — <strong>{format_num(a["score"])}/{format_num(a["max_marks"] or a["total_questions"])}</strong> (Correct: {a.get("correct_count", 0)} | Incorrect: {a.get("wrong_count", 0)}) • {a["submitted_at"]}</li>'
        for a in my_attempts
    ) or "<li>No test attempts recorded yet.</li>"

    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mock Test & Leaderboard — EDUPATH</title></head>
    <body style="font-family:system-ui,sans-serif;max-width:960px;margin:0 auto;padding:16px;background:#f1f5f9;color:#0f172a;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
            <h1 style="margin:0;font-size:1.4rem;">EDUPATH Mock Test & Leaderboard</h1>
            <a href="/dashboard" style="text-decoration:none;padding:8px 12px;border-radius:8px;background:#fff;border:1px solid #cbd5e1;color:#0f172a;font-weight:700;">← Dashboard</a>
        </div>
        <div style="margin-bottom:10px;">{"".join(filter_tabs)}</div>
        <div style="margin-bottom:14px;">{test_pills_html}</div>
        {result_html}
        {admin_box}
        {quiz_html}
        {leaderboard_html}
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:16px;">
            <h3 style="margin-top:0;">My Recent Attempts</h3>
            <ul>{att_items}</ul>
        </div>
    </body></html>"""


def _render_fallback_ai_doubt(ctx: dict) -> str:
    user = ctx.get("user") or {}
    is_admin = (user.get("role") == "admin")
    doubts = ctx.get("doubts") or []
    chat_vis = ctx.get("chat_visibility", "public")
    token = ctx.get("csrf_token", "")

    admin_toggle = ""
    if is_admin:
        next_mode = "private" if chat_vis == "public" else "public"
        admin_toggle = f"""
        <form method="POST" action="/toggle-chat-visibility" style="display:inline-block;margin-bottom:12px;">
            <input type="hidden" name="csrf_token" value="{token}">
            <input type="hidden" name="chat_visibility" value="{next_mode}">
            <button type="submit" style="padding:7px 13px;border-radius:8px;border:1px solid #cbd5e1;background:#fff;font-weight:700;cursor:pointer;">
                Chat Mode: {chat_vis.upper()} (Switch to {next_mode.upper()})
            </button>
        </form>
        """

    msg_cards = []
    for d in doubts:
        reply_block = ""
        if d.get("admin_reply"):
            reply_block = f'<div style="background:#ecfdf5;border-left:3px solid #10b981;padding:8px 12px;border-radius:8px;margin-top:8px;"><strong>Admin Reply ({d.get("replied_by") or "Admin"}):</strong> {d["admin_reply"]}</div>'
        admin_reply_form = ""
        if is_admin:
            admin_reply_form = f"""
            <form method="POST" action="/reply-doubt/{d["id"]}" style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">
                <input type="hidden" name="csrf_token" value="{token}">
                <input type="text" name="admin_reply" value="{d.get("admin_reply") or ""}" placeholder="Write a reply..." style="flex:1;padding:7px 10px;border-radius:8px;border:1px solid #cbd5e1;">
                <button type="submit" style="padding:7px 13px;border:none;border-radius:8px;background:#10b981;color:#fff;font-weight:700;cursor:pointer;">Reply</button>
            </form>
            """
        react_buttons = "".join(
            f'<form method="POST" action="/react-doubt/{d["id"]}" style="display:inline-block;margin-right:6px;"><input type="hidden" name="csrf_token" value="{token}"><input type="hidden" name="reaction" value="{emo}"><button type="submit" style="padding:4px 9px;border-radius:999px;border:1px solid #e2e8f0;background:#f8fafc;cursor:pointer;">{emo} {(d.get("reactions") or {}).get(emo, 0)}</button></form>'
            for emo in ["👍", "❤️", "🔥", "💡"]
        )
        del_link = f' | <a href="/delete-doubt/{d["id"]}" style="color:#dc2626;text-decoration:none;font-size:0.85rem;">Delete</a>' if is_admin else ""
        msg_cards.append(f"""
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px;margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;font-size:0.85rem;color:#64748b;margin-bottom:6px;">
                <span><strong>{d["user_name"]}</strong> • {d.get("subject") or "Direct Message"}</span>
                <span>{d.get("created_at") or ""}{del_link}</span>
            </div>
            <p style="margin:0 0 8px;">{d["question"]}</p>
            <div style="margin-bottom:6px;">{react_buttons}</div>
            {reply_block}
            {admin_reply_form}
        </div>
        """)

    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Message Box — EDUPATH</title></head>
    <body style="font-family:system-ui,sans-serif;max-width:860px;margin:0 auto;padding:16px;background:#f1f5f9;color:#0f172a;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
            <h1 style="margin:0;font-size:1.4rem;">EDUPATH Message & Doubt Box ({chat_vis.upper()})</h1>
            <a href="/dashboard" style="text-decoration:none;padding:8px 12px;border-radius:8px;background:#fff;border:1px solid #cbd5e1;color:#0f172a;font-weight:700;">← Dashboard</a>
        </div>
        {admin_toggle}
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:16px;margin-bottom:18px;">
            <form method="POST" action="/ai-doubt">
                <input type="hidden" name="csrf_token" value="{token}">
                <input type="hidden" name="action_type" value="send_message">
                <input type="text" name="subject" placeholder="Subject / Topic (optional)" style="padding:9px;margin-bottom:8px;border-radius:8px;border:1px solid #cbd5e1;">
                <textarea name="question" rows="3" placeholder="Write your question or message..." required style="width:100%;padding:9px;margin-bottom:10px;border-radius:8px;border:1px solid #cbd5e1;box-sizing:border-box;"></textarea>
                <button type="submit" style="padding:10px 18px;border:none;border-radius:9px;background:#10b981;color:#fff;font-weight:800;cursor:pointer;">Send Message</button>
            </form>
        </div>
        {"".join(msg_cards) or "<p>No messages yet.</p>"}
    </body></html>"""


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return s or "chapter"


def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.Error:
        pass
    return conn


def seed_default_mock_tests(conn):
    now_str = datetime.now().strftime("%d %b %Y")
    c10_title = "Class 10 Science Full Mock Test (Bio + Chem + Phy)"
    existing_c10 = conn.execute("SELECT id FROM mock_tests WHERE title = ?", (c10_title,)).fetchone()
    if not existing_c10:
        cur_c10 = conn.execute(
            """INSERT INTO mock_tests (title, subject, portal_type, duration_minutes, marks_per_question, negative_marks, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (c10_title, "Science (086)", "Class 10", 60, 1.0, 0.0, "EDUPATH Team", now_str),
        )
        t_c10_id = cur_c10.lastrowid
        c10_questions = [
            ("mcq", "[Biology] Which of the following is the main site of absorption of digested food in the human digestive system?", "Stomach", "Small intestine", "Large intestine", "Oesophagus", "B"),
            ("mcq", "[Biology] Which enzyme present in saliva helps in the digestion of starch?", "Pepsin", "Trypsin", "Salivary amylase", "Lipase", "C"),
            ("mcq", "[Biology] Which part of the nephron is responsible for the filtration of blood?", "Collecting duct", "Glomerulus", "Loop of Henle", "Ureter", "B"),
            ("mcq", "[Biology] Which blood vessel carries oxygenated blood from the lungs to the heart?", "Pulmonary artery", "Aorta", "Pulmonary vein", "Vena cava", "C"),
            ("mcq", "[Biology] Which hormone regulates the blood sugar level in the human body?", "Thyroxine", "Insulin", "Adrenaline", "Oestrogen", "B"),
            ("mcq", "[Biology] Which part of the brain controls posture and balance of the body?", "Cerebrum", "Medulla", "Cerebellum", "Hypothalamus", "C"),
            ("mcq", "[Biology] Which plant hormone promotes cell elongation and helps shoots bend towards light?", "Cytokinin", "Auxin", "Abscisic acid", "Ethylene", "B"),
            ("mcq", "[Biology] The movement of a plant shoot towards sunlight is known as:", "Geotropism", "Hydrotropism", "Phototropism", "Chemotropism", "C"),
            ("mcq", "[Biology] Which method of reproduction is commonly observed in Amoeba?", "Budding", "Binary fission", "Fragmentation", "Spore formation", "B"),
            ("mcq", "[Biology] In flowering plants, fertilisation takes place in which part?", "Anther", "Stigma", "Ovule", "Petal", "C"),
            ("mcq", "[Biology] Which of the following is the primary function of the placenta during pregnancy?", "Production of sperms", "Exchange of nutrients, oxygen and waste materials between mother and embryo", "Formation of the egg", "Digestion of food", "B"),
            ("mcq", "[Biology] How many chromosomes are present in a normal human sperm cell?", "46", "44", "23", "22 pairs", "C"),
            ("mcq", "[Biology] In human beings, which chromosome combination determines the birth of a male child?", "XX", "XY", "YY", "XO", "B"),
            ("mcq", "[Biology] Who is known as the Father of Genetics?", "Charles Darwin", "Gregor Mendel", "Louis Pasteur", "Robert Hooke", "B"),
            ("mcq", "[Biology] If a tall pea plant (TT) is crossed with a dwarf pea plant (tt), what will be the height of all plants in the F1 generation?", "All tall", "All dwarf", "50% tall and 50% dwarf", "25% tall and 75% dwarf", "A"),
            ("mcq", "[Biology] Which of the following is an example of an inherited trait?", "Pierced ears", "Acquired muscular strength", "Natural eye colour", "Learning to swim", "C"),
            ("mcq", "[Biology] Which gas is mainly responsible for the depletion of the ozone layer?", "Oxygen", "Nitrogen", "Chlorofluorocarbons (CFCs)", "Hydrogen", "C"),
            ("mcq", "[Chemistry] Which of the following is an example of a combination reaction?", "CaO + H₂O → Ca(OH)₂", "CaCO₃ → CaO + CO₂", "Zn + CuSO₄ → ZnSO₄ + Cu", "AgNO₃ + NaCl → AgCl + NaNO₃", "A"),
            ("mcq", "[Chemistry] What happens when an iron nail is dipped in copper sulphate solution?", "No reaction takes place", "The solution becomes colourless immediately", "A brown coating of copper forms on the nail", "A silver coating forms on the nail", "C"),
            ("mcq", "[Chemistry] Which of the following reactions represents oxidation?", "CuO + H₂ → Cu + H₂O", "2Mg + O₂ → 2MgO", "AgCl → Ag + Cl₂", "CaCO₃ → CaO + CO₂", "B"),
            ("mcq", "[Chemistry] What is the colour of phenolphthalein in a basic solution?", "Red", "Blue", "Pink", "Colourless", "C"),
            ("mcq", "[Chemistry] What is the pH value of a neutral solution at 25°C?", "0", "5", "7", "14", "C"),
            ("mcq", "[Chemistry] Which acid is present in an ant sting?", "Citric acid", "Methanoic acid", "Acetic acid", "Lactic acid", "B"),
            ("mcq", "[Chemistry] Which of the following is used as an antacid to relieve acidity?", "Sodium chloride", "Magnesium hydroxide", "Calcium carbonate", "Sodium hydroxide", "B"),
            ("mcq", "[Chemistry] What is the chemical formula of baking soda?", "Na₂CO₃", "NaHCO₃", "CaCO₃", "NaOH", "B"),
            ("mcq", "[Chemistry] Which gas is released when a metal reacts with a dilute acid?", "Oxygen", "Nitrogen", "Hydrogen", "Carbon dioxide", "C"),
            ("mcq", "[Chemistry] Which metal is stored in kerosene to prevent its reaction with air and moisture?", "Copper", "Sodium", "Iron", "Silver", "B"),
            ("mcq", "[Chemistry] Which of the following metals is the most reactive?", "Copper", "Silver", "Potassium", "Gold", "C"),
            ("mcq", "[Chemistry] Which non-metal is a good conductor of electricity?", "Sulphur", "Phosphorus", "Graphite", "Oxygen", "C"),
            ("mcq", "[Chemistry] What is the functional group present in alcohols?", "-COOH", "-CHO", "-OH", "-CO-", "C"),
            ("mcq", "[Chemistry] Which of the following hydrocarbons is an unsaturated compound?", "Methane", "Ethane", "Ethene", "Propane", "C"),
            ("mcq", "[Chemistry] What is the molecular formula of methane?", "CH₄", "C₂H₆", "C₂H₄", "C₃H₈", "A"),
            ("mcq", "[Chemistry] Which of the following is a characteristic property of ionic compounds?", "Low melting points", "High melting and boiling points", "Insolubility in water in all cases", "Conduct electricity in solid state", "B"),
            ("mcq", "[Chemistry] Which substance is formed when ethanol reacts with ethanoic acid in the presence of concentrated sulphuric acid?", "Ethene", "Ethyl ethanoate", "Methane", "Sodium ethanoate", "B"),
            ("mcq", "[Physics] Which type of mirror is used as a rear-view mirror in vehicles?", "Plane mirror", "Concave mirror", "Convex mirror", "Cylindrical mirror", "C"),
            ("mcq", "[Physics] The image formed by a plane mirror is always:", "Real and inverted", "Virtual and erect", "Real and enlarged", "Virtual and inverted", "B"),
            ("mcq", "[Physics] What is the SI unit of power of a lens?", "Metre", "Dioptre", "Watt", "Joule", "B"),
            ("mcq", "[Physics] Which lens is used to correct myopia (short-sightedness)?", "Convex lens", "Concave lens", "Bifocal lens", "Cylindrical lens", "B"),
            ("mcq", "[Physics] The splitting of white light into its constituent colours is known as:", "Reflection", "Refraction", "Dispersion", "Diffraction", "C"),
            ("mcq", "[Physics] What is the approximate least distance of distinct vision for a normal human eye?", "10 cm", "15 cm", "25 cm", "50 cm", "C"),
            ("mcq", "[Physics] Which phenomenon explains why the sky appears blue?", "Reflection of light", "Scattering of light", "Dispersion of light", "Total internal reflection", "B"),
            ("mcq", "[Physics] What is the SI unit of electric current?", "Volt", "Ohm", "Ampere", "Watt", "C"),
            ("mcq", "[Physics] According to Ohm's law, the potential difference across a conductor is directly proportional to:", "Resistance", "Current", "Power", "Temperature", "B"),
            ("mcq", "[Physics] What is the equivalent resistance of two resistors of 4 Ω and 6 Ω connected in series?", "2 Ω", "10 Ω", "24 Ω", "1.5 Ω", "B"),
            ("mcq", "[Physics] What is the equivalent resistance of two resistors of 6 Ω each connected in parallel?", "12 Ω", "6 Ω", "3 Ω", "1 Ω", "C"),
            ("mcq", "[Physics] Which device is used to measure electric current in a circuit?", "Voltmeter", "Ammeter", "Galvanometer", "Rheostat", "B"),
            ("mcq", "[Physics] What is the commercial unit of electrical energy?", "Joule", "Watt", "Kilowatt-hour", "Ampere", "C"),
            ("mcq", "[Physics] Which rule is used to determine the direction of the magnetic field around a straight current-carrying conductor?", "Fleming's left-hand rule", "Fleming's right-hand rule", "Right-hand thumb rule", "Ohm's law", "C"),
            ("mcq", "[Physics] What is the shape of the magnetic field lines around a straight current-carrying conductor?", "Straight parallel lines", "Concentric circles", "Elliptical curves", "Random curves", "B"),
            ("mcq", "[Physics] Which of the following is the main function of an electric fuse?", "Increase the current", "Reduce the resistance", "Protect the circuit from excessive current", "Increase the voltage", "C"),
        ]
        conn.executemany(
            """INSERT INTO mock_questions (test_id, question_type, question_text, option_a, option_b, option_c, option_d, correct_option)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [(t_c10_id, *q) for q in c10_questions],
        )

    if conn.execute("SELECT COUNT(*) FROM mock_tests").fetchone()[0] == 0:
        cur1 = conn.execute(
            """INSERT INTO mock_tests (title, subject, portal_type, duration_minutes, marks_per_question, negative_marks, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("Class 10 Science & Maths Quick Mock", "Science & Maths", "Class 10", 15, 1.0, 0.0, "EDUPATH Team", now_str),
        )
        t1_id = cur1.lastrowid
        conn.executemany(
            """INSERT INTO mock_questions (test_id, question_type, question_text, option_a, option_b, option_c, option_d, correct_option)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    t1_id,
                    "mcq",
                    "In a chemical equation, how is a precipitate commonly indicated?",
                    "Upward arrow",
                    "Downward arrow",
                    "Right arrow",
                    "Plus sign only",
                    "B",
                ),
                (
                    t1_id,
                    "mcq",
                    "If a quadratic equation ax^2 + bx + c = 0 has equal real roots, what is the discriminant (D)?",
                    "D > 0",
                    "D < 0",
                    "D = 0",
                    "D = 1",
                    "C",
                ),
                (
                    t1_id,
                    "mcq",
                    "What is the SI unit of electrical resistance?",
                    "Volt",
                    "Ampere",
                    "Ohm",
                    "Watt",
                    "C",
                ),
            ],
        )

        cur2 = conn.execute(
            """INSERT INTO mock_tests (title, subject, portal_type, duration_minutes, marks_per_question, negative_marks, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("JEE / NEET Foundation Physics Mock (+4 / -1)", "Physics", "JEE", 20, 4.0, 1.0, "EDUPATH Team", now_str),
        )
        t2_id = cur2.lastrowid
        conn.executemany(
            """INSERT INTO mock_questions (test_id, question_type, question_text, option_a, option_b, option_c, option_d, correct_option)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    t2_id,
                    "mcq",
                    "What is the dimensional formula of force?",
                    "[M L T^-2]",
                    "[M L^2 T^-2]",
                    "[M L T^-1]",
                    "[M L^-1 T^-2]",
                    "A",
                ),
                (
                    t2_id,
                    "mcq",
                    "What is the net external force on a body moving with constant velocity in a straight line?",
                    "Infinity",
                    "Zero",
                    "Equal to weight",
                    "Depends on mass",
                    "B",
                ),
            ],
        )
    conn.commit()


def init_db():
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            student_class TEXT DEFAULT 'Class 10 CBSE',
            bio TEXT DEFAULT 'Focused on 95%+ Board Excellence',
            profile_pic TEXT DEFAULT 'https://api.dicebear.com/7.x/avataaars/svg?seed=Edupath',
            theme TEXT DEFAULT 'light',
            accent TEXT DEFAULT '#10b981',
            font_size TEXT DEFAULT '16px',
            glass_blur TEXT DEFAULT '16px',
            last_seen_notif_id INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            portal_type TEXT DEFAULT 'General',
            chapter_slug TEXT DEFAULT '',
            chapter_name TEXT DEFAULT '',
            video_file TEXT NOT NULL,
            thumbnail_file TEXT DEFAULT '',
            added_by TEXT,
            created_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            portal_type TEXT DEFAULT 'General',
            chapter_slug TEXT DEFAULT '',
            chapter_name TEXT DEFAULT '',
            filename TEXT NOT NULL,
            uploaded_by TEXT,
            created_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS doubts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT NOT NULL,
            subject TEXT DEFAULT 'Direct Message',
            question TEXT NOT NULL,
            ai_reply TEXT DEFAULT '',
            admin_reply TEXT DEFAULT '',
            replied_by TEXT DEFAULT '',
            replied_at TEXT DEFAULT '',
            created_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS doubt_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doubt_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reaction TEXT NOT NULL,
            UNIQUE(doubt_id, user_id, reaction)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            target_group TEXT DEFAULT 'All',
            target_user_id INTEGER,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS video_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reaction TEXT NOT NULL,
            UNIQUE(video_id, user_id, reaction)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS video_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            user_role TEXT DEFAULT 'student',
            comment TEXT NOT NULL,
            admin_reply TEXT DEFAULT '',
            replied_by TEXT DEFAULT '',
            replied_at TEXT DEFAULT '',
            created_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS site_banner (
            id INTEGER PRIMARY KEY,
            badge_text TEXT DEFAULT 'EDUPATH FLAGSHIP',
            title TEXT DEFAULT 'EDUPATH Smart Learning & Exam Prep',
            subtitle TEXT DEFAULT 'Swipe across courses, watch video lectures, open PDF notes, and send direct messages.',
            cta_label TEXT DEFAULT 'Start Learning',
            cta_url TEXT DEFAULT '/class10',
            banner_image TEXT DEFAULT '',
            chat_visibility TEXT DEFAULT 'public',
            updated_at TEXT DEFAULT ''
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS course_media (
            course_key TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            subtitle TEXT NOT NULL,
            badge TEXT DEFAULT 'COURSE',
            url TEXT NOT NULL,
            image_url TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS mock_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT DEFAULT 'General',
            portal_type TEXT DEFAULT 'Class 10',
            duration_minutes INTEGER DEFAULT 15,
            marks_per_question REAL DEFAULT 1.0,
            negative_marks REAL DEFAULT 0.0,
            created_by TEXT,
            created_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS mock_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            question_type TEXT DEFAULT 'mcq',
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS mock_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            score REAL NOT NULL,
            total_questions INTEGER NOT NULL,
            correct_count INTEGER DEFAULT 0,
            wrong_count INTEGER DEFAULT 0,
            unattempted_count INTEGER DEFAULT 0,
            max_marks REAL DEFAULT 0,
            submitted_at TEXT
        )""")

        u_cols = [r["name"] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        if "last_seen_notif_id" not in u_cols:
            c.execute("ALTER TABLE users ADD COLUMN last_seen_notif_id INTEGER DEFAULT 0")
        if "is_blocked" not in u_cols:
            c.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")

        b_cols = [r["name"] for r in c.execute("PRAGMA table_info(site_banner)").fetchall()]
        if "chat_visibility" not in b_cols:
            c.execute("ALTER TABLE site_banner ADD COLUMN chat_visibility TEXT DEFAULT 'public'")

        n_cols = [r["name"] for r in c.execute("PRAGMA table_info(notifications)").fetchall()]
        if "target_user_id" not in n_cols:
            c.execute("ALTER TABLE notifications ADD COLUMN target_user_id INTEGER")

        d_cols = [r["name"] for r in c.execute("PRAGMA table_info(doubts)").fetchall()]
        if "user_id" not in d_cols:
            c.execute("ALTER TABLE doubts ADD COLUMN user_id INTEGER")
        if "admin_reply" not in d_cols:
            c.execute("ALTER TABLE doubts ADD COLUMN admin_reply TEXT DEFAULT ''")
        if "replied_by" not in d_cols:
            c.execute("ALTER TABLE doubts ADD COLUMN replied_by TEXT DEFAULT ''")
        if "replied_at" not in d_cols:
            c.execute("ALTER TABLE doubts ADD COLUMN replied_at TEXT DEFAULT ''")

        vc_cols = [r["name"] for r in c.execute("PRAGMA table_info(video_comments)").fetchall()]
        if "admin_reply" not in vc_cols:
            c.execute("ALTER TABLE video_comments ADD COLUMN admin_reply TEXT DEFAULT ''")
        if "replied_by" not in vc_cols:
            c.execute("ALTER TABLE video_comments ADD COLUMN replied_by TEXT DEFAULT ''")
        if "replied_at" not in vc_cols:
            c.execute("ALTER TABLE video_comments ADD COLUMN replied_at TEXT DEFAULT ''")

        mt_cols = [r["name"] for r in c.execute("PRAGMA table_info(mock_tests)").fetchall()]
        if "marks_per_question" not in mt_cols:
            c.execute("ALTER TABLE mock_tests ADD COLUMN marks_per_question REAL DEFAULT 1.0")
        if "negative_marks" not in mt_cols:
            c.execute("ALTER TABLE mock_tests ADD COLUMN negative_marks REAL DEFAULT 0.0")

        mq_cols = [r["name"] for r in c.execute("PRAGMA table_info(mock_questions)").fetchall()]
        if "question_type" not in mq_cols:
            c.execute("ALTER TABLE mock_questions ADD COLUMN question_type TEXT DEFAULT 'mcq'")

        ma_cols = [r["name"] for r in c.execute("PRAGMA table_info(mock_attempts)").fetchall()]
        if "correct_count" not in ma_cols:
            c.execute("ALTER TABLE mock_attempts ADD COLUMN correct_count INTEGER DEFAULT 0")
        if "wrong_count" not in ma_cols:
            c.execute("ALTER TABLE mock_attempts ADD COLUMN wrong_count INTEGER DEFAULT 0")
        if "unattempted_count" not in ma_cols:
            c.execute("ALTER TABLE mock_attempts ADD COLUMN unattempted_count INTEGER DEFAULT 0")
        if "max_marks" not in ma_cols:
            c.execute("ALTER TABLE mock_attempts ADD COLUMN max_marks REAL DEFAULT 0")

        for tbl in ("videos", "notes"):
            t_cols = [r["name"] for r in c.execute(f"PRAGMA table_info({tbl})").fetchall()]
            if "portal_type" not in t_cols:
                c.execute(f"ALTER TABLE {tbl} ADD COLUMN portal_type TEXT DEFAULT 'General'")
            if "chapter_slug" not in t_cols:
                c.execute(f"ALTER TABLE {tbl} ADD COLUMN chapter_slug TEXT DEFAULT ''")
            if "chapter_name" not in t_cols:
                c.execute(f"ALTER TABLE {tbl} ADD COLUMN chapter_name TEXT DEFAULT ''")

        if not c.execute("SELECT id FROM site_banner WHERE id = 1").fetchone():
            c.execute(
                """INSERT INTO site_banner (id, badge_text, title, subtitle, cta_label, cta_url, banner_image, chat_visibility, updated_at)
                   VALUES (1, 'EDUPATH FLAGSHIP', 'EDUPATH Smart Study & Exam Hub',
                           'Swipe across courses, watch video lectures, open PDF notes, and send direct messages.',
                           'Open Class 10', '/class10', '', 'public', ?)""",
                (datetime.now().strftime("%d %b %Y"),),
            )

        default_courses = [
            ("class10", "Class 10 Board", "Maths, Science, SST, English & Hindi", "BOARD", "/class10", ""),
            ("class11", "Class 11 Streams", "Science, Commerce & Arts foundation", "STREAM", "/class11", ""),
            ("class12", "Class 12 Streams", "Board chapters, lectures & notes", "BOARD", "/class12", ""),
            ("jee", "JEE Preparation", "Physics, Chemistry & Mathematics", "ENTRANCE", "/jee", ""),
            ("neet", "NEET Preparation", "Biology, Physics & Chemistry NCERT", "MEDICAL", "/neet", ""),
            ("mock_test", "Mock Test & SQP", "Online MCQ tests, timer & practice", "MOCK TEST", "/mock-test", ""),
            ("state_boards", "State Boards", "BSEB, UP, MP, RBSE & JAC study material", "STATE", "/state-boards", ""),
        ]
        for ck, ct, cs, cb, cu, ci in default_courses:
            if not c.execute("SELECT course_key FROM course_media WHERE course_key = ?", (ck,)).fetchone():
                c.execute(
                    """INSERT INTO course_media (course_key, title, subtitle, badge, url, image_url, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (ck, ct, cs, cb, cu, ci, datetime.now().strftime("%d %b %Y")),
                )

        conn.commit()

        admin_pass = os.environ.get("EDUPATH_ADMIN_PASSWORD") or secrets.token_urlsafe(12)
        if not c.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone():
            c.execute(
                """INSERT INTO users (name, email, password, role, student_class, bio, theme, accent, is_blocked)
                   VALUES (?, ?, ?, 'admin', 'Head Educator', 'EDUPATH Founder & Admin', 'light', '#10b981', 0)""",
                ("Syed Muhammad Imran", ADMIN_EMAIL, generate_password_hash(admin_pass)),
            )
            if not os.environ.get("EDUPATH_ADMIN_PASSWORD"):
                app.logger.info("Generated initial admin password for %s: %s", ADMIN_EMAIL, admin_pass)
        else:
            c.execute("UPDATE users SET role = 'admin', is_blocked = 0 WHERE email = ?", (ADMIN_EMAIL,))
        conn.commit()
        seed_default_mock_tests(conn)
    finally:
        conn.close()


try:
    init_db()
except Exception:
    pass


def current_user():
    if "user_id" not in session:
        return None
    conn = get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    finally:
        conn.close()
    if not user:
        session.pop("user_id", None)
        return None
    if int(user["is_blocked"] or 0) == 1 and user["role"] != "admin":
        session.clear()
        flash("Your account has been blocked by the administrator.", "error")
        return None
    return user


def get_chat_visibility() -> str:
    conn = get_db()
    try:
        row = conn.execute("SELECT chat_visibility FROM site_banner WHERE id = 1").fetchone()
    finally:
        conn.close()
    val = (row["chat_visibility"] if row and row["chat_visibility"] else "public").lower()
    return "private" if val == "private" else "public"


def get_recent_notifications(user=None, limit=8):
    conn = get_db()
    try:
        if user and user["role"] != "admin":
            rows = conn.execute(
                """SELECT * FROM notifications
                   WHERE target_user_id IS NULL OR target_user_id = ?
                   ORDER BY id DESC LIMIT ?""",
                (user["id"], limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM notifications WHERE target_user_id IS NULL ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_unread_notif_count(user) -> int:
    if not user:
        return 0
    seen_id = int(user["last_seen_notif_id"] or 0)
    conn = get_db()
    try:
        if user["role"] != "admin":
            cnt = conn.execute(
                """SELECT COUNT(*) FROM notifications
                   WHERE id > ? AND (target_user_id IS NULL OR target_user_id = ?)""",
                (seen_id, user["id"]),
            ).fetchone()[0]
        else:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE id > ? AND target_user_id IS NULL",
                (seen_id,),
            ).fetchone()[0]
    finally:
        conn.close()
    return int(cnt or 0)


def save_uploaded_image(file_storage, prefix: str) -> str:
    if not file_storage or not file_storage.filename:
        return ""
    if not has_allowed_ext(file_storage.filename, ALLOWED_IMAGE_EXTS):
        return ""
    ext = os.path.splitext(file_storage.filename.strip().lower())[1] or ".jpg"
    stamp = f"{int(datetime.now().timestamp())}_{secrets.token_hex(3)}"
    fname = secure_filename(f"{prefix}_{stamp}{ext}")
    file_storage.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
    return url_for("serve_file", filename=fname) + f"?v={stamp}"


def is_safe_media_url(raw_url: str) -> bool:
    u = (raw_url or "").strip()
    if not u:
        return False
    if u.startswith("/") and not u.startswith("//"):
        return True
    lower = u.lower()
    return lower.startswith("https://") or lower.startswith("http://")


def clean_url_for_css(raw_url: str) -> str:
    u = (raw_url or "").strip()
    if not is_safe_media_url(u):
        return ""
    return u.replace("'", "").replace('"', "").replace(")", "").replace("(", "").strip()


@app.context_processor
def inject_helpers():
    return {
        "get_recent_notifications": get_recent_notifications,
        "get_unread_notif_count": get_unread_notif_count,
        "get_chat_visibility": get_chat_visibility,
        "csrf_token": get_csrf_token(),
        "clean_url_for_css": clean_url_for_css,
        "format_num": format_num,
        "MOCK_PORTAL_CHOICES": MOCK_PORTAL_CHOICES,
    }


def _send_media_file(safe_name: str, as_attachment: bool = False):
    fpath = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    if not os.path.exists(fpath):
        return redirect(url_for("dashboard"))

    ext = os.path.splitext(safe_name.lower())[1]
    mimetype = None
    if ext == ".mov":
        mimetype = "video/quicktime"
    elif ext == ".mp4":
        mimetype = "video/mp4"
    elif ext == ".webm":
        mimetype = "video/webm"
    elif ext == ".m4v":
        mimetype = "video/x-m4v"
    elif ext == ".pdf":
        mimetype = "application/pdf"

    if mimetype and not as_attachment:
        resp = send_from_directory(
            app.config["UPLOAD_FOLDER"],
            safe_name,
            mimetype=mimetype,
            as_attachment=False,
            conditional=True,
        )
        resp.headers["Accept-Ranges"] = "bytes"
        resp.headers["Cache-Control"] = "public, max-age=3600"
        return resp
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        safe_name,
        as_attachment=as_attachment,
        conditional=True,
    )


@app.route("/uploads/<path:filename>")
def serve_file(filename):
    safe_name = os.path.basename(filename or "")
    if not safe_name:
        return redirect(url_for("dashboard"))
    return _send_media_file(safe_name, as_attachment=False)


@app.route("/download/<path:filename>")
def download_file(filename):
    safe_name = os.path.basename(filename or "")
    if not safe_name:
        return redirect(url_for("dashboard"))
    return _send_media_file(safe_name, as_attachment=True)


@app.route("/mark-notifications-read", methods=["POST"])
def mark_notifications_read():
    user = current_user()
    if not user:
        return jsonify({"ok": False}), 401
    conn = get_db()
    try:
        if user["role"] != "admin":
            row = conn.execute(
                "SELECT COALESCE(MAX(id), 0) AS max_id FROM notifications WHERE target_user_id IS NULL OR target_user_id = ?",
                (user["id"],),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COALESCE(MAX(id), 0) AS max_id FROM notifications WHERE target_user_id IS NULL"
            ).fetchone()
        max_id = int(row["max_id"] or 0)
        conn.execute("UPDATE users SET last_seen_notif_id = ? WHERE id = ?", (max_id, user["id"]))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True, "seen_id": max_id})


@app.route("/toggle-chat-visibility", methods=["POST"])
def toggle_chat_visibility():
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only administrators can switch chat between public and private mode.", "error")
        return redirect(url_for("ai_doubt"))
    if not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(url_for("ai_doubt"))

    mode = request.form.get("chat_visibility", "public").strip().lower()
    if mode not in ("public", "private"):
        mode = "public"
    conn = get_db()
    try:
        conn.execute("UPDATE site_banner SET chat_visibility = ? WHERE id = 1", (mode,))
        conn.commit()
    finally:
        conn.close()
    flash(f"Message Box chat mode is now set to {mode.upper()}.", "success")
    return redirect(request.referrer or url_for("ai_doubt"))


@app.route("/toggle-block-user/<int:target_user_id>", methods=["GET", "POST"])
def toggle_block_user(target_user_id):
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only administrators can block or unblock users.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "POST" and not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(request.referrer or url_for("admin_panel"))

    conn = get_db()
    try:
        target = conn.execute("SELECT id, name, email, role, is_blocked FROM users WHERE id = ?", (target_user_id,)).fetchone()
        if not target or target["email"] == ADMIN_EMAIL or target["role"] == "admin":
            flash("Administrator accounts cannot be blocked.", "error")
            return redirect(request.referrer or url_for("admin_panel"))

        next_blocked = 0 if int(target["is_blocked"] or 0) == 1 else 1
        conn.execute("UPDATE users SET is_blocked = ? WHERE id = ?", (next_blocked, target_user_id))
        conn.commit()
    finally:
        conn.close()

    status_label = "BLOCKED" if next_blocked == 1 else "UNBLOCKED"
    flash(f"{target['name']} ({target['email']}) is now {status_label}.", "success")
    return redirect(request.referrer or url_for("admin_panel"))


@app.route("/send-personal-message/<int:target_user_id>", methods=["POST"])
def send_personal_message(target_user_id):
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only administrators can send direct messages to students.", "error")
        return redirect(url_for("dashboard"))
    if not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(request.referrer or url_for("admin_panel"))

    msg = (request.form.get("personal_message") or "").strip()
    if not msg:
        flash("Please enter a message before sending.", "error")
        return redirect(request.referrer or url_for("admin_panel"))

    conn = get_db()
    try:
        target = conn.execute("SELECT id, name FROM users WHERE id = ?", (target_user_id,)).fetchone()
        if not target:
            flash("Student account not found.", "error")
            return redirect(request.referrer or url_for("admin_panel"))

        now_str = datetime.now().strftime("%d %b, %I:%M %p")
        conn.execute(
            "INSERT INTO notifications (message, target_group, target_user_id, created_by, created_at) VALUES (?, 'Student', ?, ?, ?)",
            (f"Direct Message: {msg}", target["id"], user["name"], now_str),
        )
        conn.execute(
            "INSERT INTO doubts (user_id, user_name, subject, question, ai_reply, admin_reply, replied_by, replied_at, created_at) VALUES (?, ?, 'Direct Message', ?, '', ?, ?, ?, ?)",
            (target["id"], target["name"], f"[To {target['name']}] {msg}", msg, user["name"], now_str, now_str),
        )
        conn.commit()
    finally:
        conn.close()

    flash(f"Direct message sent to {target['name']}.", "success")
    return redirect(request.referrer or url_for("admin_panel"))


CLASS10_SUBJECTS = [
    {
        "name": "Mathematics (041 / 241)",
        "icon": "📐",
        "detail": "Real numbers, polynomials, linear equations, quadratics, AP, triangles, coordinate geometry, trigonometry, circles, surface areas & volumes, statistics, and probability.",
        "chapters": [
            "Real Numbers",
            "Polynomials",
            "Pair of Linear Equations in Two Variables",
            "Quadratic Equations",
            "Arithmetic Progressions",
            "Triangles",
            "Coordinate Geometry",
            "Introduction to Trigonometry & Applications",
            "Circles",
            "Areas Related to Circles & Surface Areas and Volumes",
            "Statistics & Probability",
        ],
    },
    {
        "name": "Science (086)",
        "icon": "🔬",
        "detail": "Chemical reactions, acids/bases/salts, metals/non-metals, carbon compounds, life processes, control & coordination, reproduction, heredity, light, human eye, electricity, and magnetic effects.",
        "chapters": [
            "Chemical Reactions and Equations",
            "Acids, Bases and Salts",
            "Metals and Non-metals",
            "Carbon and its Compounds",
            "Life Processes",
            "Control and Coordination",
            "How do Organisms Reproduce?",
            "Heredity",
            "Light – Reflection and Refraction",
            "The Human Eye and the Colourful World",
            "Electricity",
            "Magnetic Effects of Electric Current",
            "Our Environment",
        ],
    },
    {
        "name": "Chemistry (Class 10)",
        "icon": "🧪",
        "detail": "Class 10 Chemistry chapters covering chemical reactions, acids/bases/salts, metals/non-metals, and carbon and its compounds.",
        "chapters": [
            "Chemical Reactions and Equations",
            "Acids, Bases and Salts",
            "Metals and Non-metals",
            "Carbon and its Compounds",
        ],
    },
    {
        "name": "Physics (Class 10)",
        "icon": "⚛️",
        "detail": "Class 10 Physics chapters covering light reflection & refraction, human eye & colourful world, electricity, and magnetic effects of electric current.",
        "chapters": [
            "Light – Reflection and Refraction",
            "The Human Eye and the Colourful World",
            "Electricity",
            "Magnetic Effects of Electric Current",
        ],
    },
    {
        "name": "Social Science (087)",
        "icon": "🌍",
        "detail": "History, Geography, Political Science, and Economics chapters.",
        "chapters": [
            "The Rise of Nationalism in Europe",
            "Nationalism in India",
            "The Making of a Global World & Age of Industrialisation",
            "Print Culture and the Modern World",
            "Resources, Forest/Wildlife, Water, Agriculture & Minerals",
            "Power Sharing, Federalism, Gender/Religion/Caste & Political Parties",
            "Outcomes of Democracy",
            "Development, Sectors of Indian Economy, Money & Credit, Globalisation",
        ],
    },
    {
        "name": "English (184 / 101)",
        "icon": "📖",
        "detail": "First Flight, Footprints Without Feet, reading comprehension, analytical writing, and grammar.",
        "chapters": [
            "First Flight — Prose & Poetry",
            "Footprints Without Feet — Supplementary",
            "Reading Comprehension & Analytical Paragraph",
            "Formal Letters & English Grammar",
        ],
    },
    {
        "name": "Hindi (002 / 085)",
        "icon": "✍️",
        "detail": "Kshitij, Kritika, Sparsh, Sanchayan, composition, and Hindi grammar topics.",
        "chapters": [
            "Kshitij / Sparsh — Gadya & Kavya Khand",
            "Kritika / Sanchayan — Poorak Pustika",
            "Vyakaran (Rachna ke Aadhar par Vakya, Vachya, Pad Parichay, Alankar)",
            "Patra, Anuched & Vigyapan Lekhan",
        ],
    },
    {
        "name": "IT / Artificial Intelligence (402 / 417)",
        "icon": "💻",
        "detail": "Employability skills, AI project cycle, data science, computer vision, and NLP.",
        "chapters": [
            "Employability Skills & Communication",
            "AI Project Cycle & Problem Scoping",
            "Data Science, Computer Vision & NLP",
        ],
    },
]

CLASS11_STREAMS = {
    "science": {
        "name": "Science",
        "icon": "🔬",
        "tagline": "Physics, Chemistry, Mathematics & Biology",
        "overview": "Class 11 Science stream video lectures and PDF notes organized by subject and chapter.",
        "subjects": [
            {
                "name": "Physics (042)",
                "detail": "Mechanics, thermal properties, thermodynamics, KTG, oscillations, and waves.",
                "chapters": [
                    "Units and Measurements",
                    "Motion in a Straight Line",
                    "Motion in a Plane",
                    "Laws of Motion",
                    "Work, Energy and Power",
                    "System of Particles and Rotational Motion",
                    "Gravitation",
                    "Mechanical Properties of Solids & Fluids",
                    "Thermal Properties of Matter & Thermodynamics",
                    "Kinetic Theory, Oscillations & Waves",
                ],
            },
            {
                "name": "Chemistry (043)",
                "detail": "Physical, Inorganic, and Organic chemistry foundational chapters.",
                "chapters": [
                    "Some Basic Concepts of Chemistry",
                    "Structure of Atom",
                    "Classification of Elements & Periodicity",
                    "Chemical Bonding and Molecular Structure",
                    "Chemical Thermodynamics",
                    "Equilibrium",
                    "Redox Reactions",
                    "Organic Chemistry: Some Basic Principles & Techniques",
                    "Hydrocarbons",
                ],
            },
            {
                "name": "Mathematics (041)",
                "detail": "Algebra, trigonometry, coordinate geometry, calculus introduction, statistics, and probability.",
                "chapters": [
                    "Sets",
                    "Relations and Functions",
                    "Trigonometric Functions",
                    "Complex Numbers and Quadratic Equations",
                    "Linear Inequalities",
                    "Permutations and Combinations",
                    "Binomial Theorem",
                    "Sequences and Series",
                    "Straight Lines & Conic Sections",
                    "Limits and Derivatives, Statistics & Probability",
                ],
            },
            {
                "name": "Biology (044)",
                "detail": "Diversity, structural organisation, cell, plant physiology, and human physiology.",
                "chapters": [
                    "The Living World & Biological Classification",
                    "Plant Kingdom & Animal Kingdom",
                    "Morphology of Flowering Plants",
                    "Anatomy of Flowering Plants",
                    "Structural Organisation in Animals",
                    "Cell: The Unit of Life & Biomolecules",
                    "Cell Cycle and Cell Division",
                    "Photosynthesis in Higher Plants",
                    "Respiration in Plants & Plant Growth",
                    "Breathing, Body Fluids, Excretion, Locomotion & Neural Control",
                ],
            },
        ],
    },
    "commerce": {
        "name": "Commerce",
        "icon": "📊",
        "tagline": "Accountancy, Business Studies & Economics",
        "overview": "Class 11 Commerce chapters, notes, and video lessons.",
        "subjects": [
            {
                "name": "Accountancy (055)",
                "detail": "Accounting foundations through financial statements.",
                "chapters": [
                    "Introduction to Accounting & Theory Base",
                    "Accounting Equation & Rules of Debit and Credit",
                    "Journal & Ledger",
                    "Cash Book & Special Purpose Books",
                    "Bank Reconciliation Statement (BRS)",
                    "Trial Balance & Rectification of Errors",
                    "Depreciation, Provisions and Reserves",
                    "Financial Statements of Sole Proprietorship",
                ],
            },
            {
                "name": "Business Studies (054)",
                "detail": "Business environment, organisations, services, finance, and trade.",
                "chapters": [
                    "Nature and Purpose of Business",
                    "Forms of Business Organisation",
                    "Private, Public and Global Enterprises",
                    "Business Services",
                    "Emerging Modes of Business & Social Responsibility",
                    "Sources of Business Finance",
                    "Small Business, Internal & International Trade",
                ],
            },
            {
                "name": "Economics (030)",
                "detail": "Statistics for Economics and Introductory Microeconomics.",
                "chapters": [
                    "Collection, Organisation & Presentation of Data",
                    "Measures of Central Tendency (Mean, Median, Mode)",
                    "Measures of Dispersion, Correlation & Index Numbers",
                    "Consumer Equilibrium & Demand",
                    "Producer Behaviour, Supply & Market Forms",
                ],
            },
        ],
    },
    "arts": {
        "name": "Arts",
        "icon": "🎭",
        "tagline": "History, Political Science & Geography",
        "overview": "Class 11 Arts and Humanities chapters and study materials.",
        "subjects": [
            {
                "name": "History (027)",
                "detail": "World history themes and changing societies.",
                "chapters": [
                    "Writing and City Life",
                    "An Empire Across Three Continents",
                    "Nomadic Empires",
                    "The Three Orders",
                    "Changing Cultural Traditions",
                    "Displacing Indigenous Peoples & Paths to Modernisation",
                ],
            },
            {
                "name": "Political Science (028)",
                "detail": "Indian Constitution at Work and Political Theory.",
                "chapters": [
                    "Constitution: Why and How?",
                    "Rights in the Indian Constitution",
                    "Election, Representation, Executive, Legislature & Judiciary",
                    "Federalism & Local Governments",
                    "Political Theory: Rights, Liberty, Equality & Justice",
                ],
            },
            {
                "name": "Geography (029)",
                "detail": "Fundamentals of Physical Geography and India: Physical Environment.",
                "chapters": [
                    "Geography as a Discipline & Interior of the Earth",
                    "Distribution of Oceans, Continents & Landforms",
                    "Atmosphere, Water in Oceans & Biodiversity",
                    "India: Location, Structure & Physiography",
                    "Drainage System, Climate & Natural Vegetation",
                ],
            },
        ],
    },
}

CLASS12_STREAMS = {
    "science": {
        "name": "Science",
        "icon": "🔬",
        "tagline": "Physics, Chemistry, Mathematics & Biology",
        "overview": "Class 12 Science subject portals, lectures, and notes.",
        "subjects": [
            {
                "name": "Physics (042)",
                "detail": "Electrostatics through semiconductors.",
                "chapters": [
                    "Electric Charges and Fields",
                    "Electrostatic Potential and Capacitance",
                    "Current Electricity",
                    "Moving Charges and Magnetism & Matter",
                    "Electromagnetic Induction & Alternating Current",
                    "Electromagnetic Waves",
                    "Ray Optics and Optical Instruments",
                    "Wave Optics",
                    "Dual Nature of Radiation and Matter",
                    "Atoms, Nuclei & Semiconductor Electronics",
                ],
            },
            {
                "name": "Chemistry (043)",
                "detail": "Physical, Inorganic, and Organic chemistry chapters for Class 12.",
                "chapters": [
                    "Solutions",
                    "Electrochemistry",
                    "Chemical Kinetics",
                    "The d and f Block Elements",
                    "Coordination Compounds",
                    "Haloalkanes and Haloarenes",
                    "Alcohols, Phenols and Ethers",
                    "Aldehydes, Ketones and Carboxylic Acids",
                    "Amines",
                    "Biomolecules",
                ],
            },
            {
                "name": "Mathematics (041)",
                "detail": "Relations, matrices, calculus, differential equations, vectors, 3D geometry, and probability.",
                "chapters": [
                    "Relations and Functions & Inverse Trigonometric Functions",
                    "Matrices & Determinants",
                    "Continuity and Differentiability",
                    "Applications of Derivatives",
                    "Integrals & Application of Integrals",
                    "Differential Equations",
                    "Vector Algebra",
                    "Three Dimensional Geometry",
                    "Linear Programming & Probability",
                ],
            },
            {
                "name": "Biology (044)",
                "detail": "Reproduction, genetics, evolution, human health, biotechnology, and ecology.",
                "chapters": [
                    "Sexual Reproduction in Flowering Plants",
                    "Human Reproduction & Reproductive Health",
                    "Principles of Inheritance and Variation",
                    "Molecular Basis of Inheritance",
                    "Evolution",
                    "Human Health and Disease & Microbes in Human Welfare",
                    "Biotechnology: Principles, Processes & Applications",
                    "Organisms, Populations, Ecosystem & Biodiversity",
                ],
            },
        ],
    },
    "commerce": {
        "name": "Commerce",
        "icon": "📊",
        "tagline": "Accountancy, Business Studies & Economics",
        "overview": "Class 12 Commerce chapters, notes, and lectures.",
        "subjects": [
            {
                "name": "Accountancy (055)",
                "detail": "Partnership, company accounts, financial analysis, and cash flow.",
                "chapters": [
                    "Accounting for Partnership Firms: Fundamentals & Goodwill",
                    "Admission of a Partner",
                    "Retirement and Death of a Partner",
                    "Dissolution of a Partnership Firm",
                    "Accounting for Share Capital",
                    "Issue of Debentures",
                    "Financial Statement Analysis & Accounting Ratios",
                    "Cash Flow Statement",
                ],
            },
            {
                "name": "Business Studies (054)",
                "detail": "Principles of management, business environment, functions of management, finance, and marketing.",
                "chapters": [
                    "Nature and Significance of Management",
                    "Principles of Management & Business Environment",
                    "Planning & Organising",
                    "Staffing, Directing & Controlling",
                    "Financial Management & Financial Markets",
                    "Marketing Management & Consumer Protection",
                ],
            },
            {
                "name": "Economics (030)",
                "detail": "Macroeconomics and Indian Economic Development.",
                "chapters": [
                    "National Income and Related Aggregates",
                    "Money and Banking",
                    "Determination of Income and Employment",
                    "Government Budget and the Economy",
                    "Balance of Payments",
                    "Indian Economic Development (1947-90 & Reforms Since 1991)",
                    "Current Challenges Facing Indian Economy",
                ],
            },
        ],
    },
    "arts": {
        "name": "Arts",
        "icon": "🎭",
        "tagline": "History, Political Science & Geography",
        "overview": "Class 12 Arts and Humanities chapters and resources.",
        "subjects": [
            {
                "name": "History (027)",
                "detail": "Themes in Indian History chapters.",
                "chapters": [
                    "Bricks, Beads and Bones (Harappan)",
                    "Kings, Farmers and Towns",
                    "Kinship, Caste, Class & Thinkers, Beliefs, Buildings",
                    "Bhakti-Sufi Traditions & Vijayanagara",
                    "Peasants, Zamindars, Colonialism & Rebels of 1857",
                    "Mahatma Gandhi, Nationalist Movement & Framing the Constitution",
                ],
            },
            {
                "name": "Political Science (028)",
                "detail": "Contemporary World Politics and Politics in India Since Independence.",
                "chapters": [
                    "End of Bipolarity, Contemporary Centres of Power & South Asia",
                    "International Organisations, Security, Environment & Globalisation",
                    "Challenges of Nation-Building & Era of One-Party Dominance",
                    "Planned Development, External Relations & Party System",
                    "Democratic Resurgence & Recent Developments in Indian Politics",
                ],
            },
            {
                "name": "Geography (029)",
                "detail": "Fundamentals of Human Geography and India: People and Economy.",
                "chapters": [
                    "Human Geography Nature and Scope & World Population",
                    "Human Development & Primary, Secondary, Tertiary Activities",
                    "Transport, Communication & International Trade",
                    "India Population, Settlements & Land/Agriculture",
                    "Water, Mineral & Energy Resources and Planning / Transport",
                ],
            },
        ],
    },
}

JEE_SYLLABUS = {
    "physics": {
        "label": "Physics",
        "icon": "⚛️",
        "explanation": "JEE Physics focuses on core concepts, free-body diagrams, dimensional analysis, and numerical problem-solving.",
        "units": [
            {
                "title": "Mechanics & Kinematics",
                "detail": "Motion in 1D/2D, Newton's laws, friction, work-energy, rotation, and gravitation.",
                "chapters": [
                    "Units, Dimensions & Error Analysis",
                    "Kinematics, Projectile & Relative Motion",
                    "Laws of Motion & Friction",
                    "Work, Energy, Power & Circular Motion",
                    "Rotational Motion & Gravitation",
                ],
            },
            {
                "title": "Heat, Fluids & Thermodynamics",
                "detail": "Solids/fluids, thermal expansion, calorimetry, KTG, and laws of thermodynamics.",
                "chapters": [
                    "Elasticity, Fluids, Viscosity & Surface Tension",
                    "Thermal Expansion, Calorimetry & Heat Transfer",
                    "Kinetic Theory of Gases & Thermodynamics",
                ],
            },
            {
                "title": "Electrodynamics & Magnetism",
                "detail": "Electrostatics, capacitors, current electricity, magnetic fields, EMI, and AC.",
                "chapters": [
                    "Electrostatics & Gauss Law",
                    "Capacitors & Current Electricity",
                    "Moving Charges, Magnetism & EMI",
                    "Alternating Current & EM Waves",
                ],
            },
            {
                "title": "Optics & Modern Physics",
                "detail": "Ray/wave optics, dual nature, atoms, nuclei, and semiconductors.",
                "chapters": [
                    "Ray Optics & Wave Optics",
                    "Dual Nature of Matter & Radiation",
                    "Atoms, Nuclei & Semiconductor Electronics",
                ],
            },
        ],
    },
    "chemistry": {
        "label": "Chemistry",
        "icon": "🧪",
        "explanation": "JEE Chemistry combines Physical formulas and numericals, Inorganic NCERT trends and bonding, and Organic reaction mechanisms.",
        "units": [
            {
                "title": "Physical Chemistry",
                "detail": "Mole concept, atomic structure, thermodynamics, equilibrium, solutions, electrochemistry, and kinetics.",
                "chapters": [
                    "Mole Concept & Atomic Structure",
                    "Chemical Thermodynamics & Equilibrium",
                    "Solutions & Electrochemistry",
                    "Chemical Kinetics",
                ],
            },
            {
                "title": "Inorganic Chemistry",
                "detail": "Periodicity, chemical bonding & MOT, p/d/f block, and coordination compounds.",
                "chapters": [
                    "Classification & Periodicity",
                    "Chemical Bonding & Molecular Orbital Theory",
                    "p-Block, d-Block & f-Block Elements",
                    "Coordination Compounds",
                ],
            },
            {
                "title": "Organic Chemistry",
                "detail": "GOC, hydrocarbons, haloalkanes/arenes, alcohols/phenols/ethers, carbonyls, amines, and biomolecules.",
                "chapters": [
                    "General Organic Chemistry (GOC) & Isomerism",
                    "Hydrocarbons",
                    "Haloalkanes, Haloarenes, Alcohols, Phenols & Ethers",
                    "Aldehydes, Ketones, Carboxylic Acids & Amines",
                    "Biomolecules",
                ],
            },
        ],
    },
    "mathematics": {
        "label": "Mathematics",
        "icon": "📐",
        "explanation": "JEE Mathematics emphasizes Algebra, Coordinate Geometry, Trigonometry, Calculus, and Vectors/3D problem practice.",
        "units": [
            {
                "title": "Algebra",
                "detail": "Sets/functions, complex numbers, quadratics, matrices-determinants, P&C, binomial, sequences, and probability.",
                "chapters": [
                    "Sets, Relations, Functions & Complex Numbers",
                    "Quadratic Equations, Sequences & Binomial Theorem",
                    "Matrices, Determinants & Permutations-Combinations",
                    "Probability & Statistics",
                ],
            },
            {
                "title": "Trigonometry & Coordinate Geometry",
                "detail": "Trigonometric identities/equations, straight lines, circles, parabola, ellipse, and hyperbola.",
                "chapters": [
                    "Trigonometric Ratios, Identities & Equations",
                    "Straight Lines & Circles",
                    "Parabola, Ellipse & Hyperbola",
                ],
            },
            {
                "title": "Calculus & Vectors / 3D",
                "detail": "Limits, continuity, differentiability, AOD, integrals, differential equations, vectors, and 3D geometry.",
                "chapters": [
                    "Limits, Continuity, Differentiability & AOD",
                    "Indefinite, Definite Integrals & Area Under Curves",
                    "Differential Equations",
                    "Vector Algebra & Three Dimensional Geometry",
                ],
            },
        ],
    },
}

NEET_SYLLABUS = {
    "biology": {
        "label": "Biology",
        "icon": "🧬",
        "explanation": "NEET Biology requires thorough mastery of NCERT text lines, diagrams, tables, and examples.",
        "units": [
            {
                "title": "Diversity & Structural Organisation",
                "detail": "Living world, classification, plant/animal kingdom, and anatomy/morphology.",
                "chapters": [
                    "The Living World & Biological Classification",
                    "Plant Kingdom & Animal Kingdom",
                    "Morphology, Anatomy of Plants & Structural Organisation in Animals",
                ],
            },
            {
                "title": "Cell & Plant Physiology",
                "detail": "Cell, biomolecules, cell cycle, photosynthesis, respiration, and plant growth.",
                "chapters": [
                    "Cell: Unit of Life, Biomolecules & Cell Cycle",
                    "Photosynthesis in Higher Plants",
                    "Respiration in Plants & Plant Growth",
                ],
            },
            {
                "title": "Human Physiology & Reproduction",
                "detail": "Breathing, circulation, excretion, locomotion, control/coordination, and reproduction.",
                "chapters": [
                    "Breathing, Body Fluids & Excretory Products",
                    "Locomotion, Neural & Chemical Coordination",
                    "Sexual Reproduction in Plants, Human Reproduction & Reproductive Health",
                ],
            },
            {
                "title": "Genetics, Biotech & Ecology",
                "detail": "Inheritance, molecular basis, evolution, human health, microbes, biotechnology, and ecology.",
                "chapters": [
                    "Principles of Inheritance & Molecular Basis of Inheritance",
                    "Evolution, Human Health & Microbes",
                    "Biotechnology: Principles & Applications",
                    "Organisms, Populations, Ecosystem & Biodiversity",
                ],
            },
        ],
    },
    "physics": {
        "label": "Physics",
        "icon": "⚛️",
        "explanation": "NEET Physics emphasizes NCERT formulas, conceptual questions, graphs, and numerical accuracy.",
        "units": [
            {
                "title": "Mechanics & Thermal Physics",
                "detail": "Kinematics, laws of motion, work-energy, rotational motion, gravitation, fluids, and thermodynamics.",
                "chapters": [
                    "Units, Measurements, Kinematics & Laws of Motion",
                    "Work, Energy, Power & Rotational Motion",
                    "Gravitation, Properties of Matter & Thermodynamics",
                ],
            },
            {
                "title": "Waves, Electricity & Magnetism",
                "detail": "SHM, waves, electrostatics, current electricity, moving charges/magnetism, EMI, and AC.",
                "chapters": [
                    "Oscillations (SHM) & Waves",
                    "Electrostatics & Current Electricity",
                    "Moving Charges, Magnetism, EMI & AC",
                ],
            },
            {
                "title": "Optics & Modern Physics",
                "detail": "Ray/wave optics, dual nature, atoms, nuclei, and semiconductors.",
                "chapters": [
                    "Ray Optics & Wave Optics",
                    "Dual Nature, Atoms & Nuclei",
                    "Semiconductor Electronics",
                ],
            },
        ],
    },
    "chemistry": {
        "label": "Chemistry",
        "icon": "🧪",
        "explanation": "NEET Chemistry is NCERT-anchored across Physical formulas, Inorganic trends/bonding, and Organic reactions.",
        "units": [
            {
                "title": "Physical Chemistry",
                "detail": "Mole concept, atomic structure, thermodynamics, equilibrium, redox, solutions, electrochemistry, and kinetics.",
                "chapters": [
                    "Mole Concept & Structure of Atom",
                    "Thermodynamics, Equilibrium & Redox Reactions",
                    "Solutions, Electrochemistry & Chemical Kinetics",
                ],
            },
            {
                "title": "Inorganic & Organic Chemistry",
                "detail": "Periodicity, chemical bonding, coordination, d/f block, organic functional groups, and biomolecules.",
                "chapters": [
                    "Periodicity, Chemical Bonding & Coordination Compounds",
                    "GOC, Hydrocarbons & Haloalkanes / Alcohols-Phenols-Ethers",
                    "Aldehydes, Ketones, Carboxylic Acids, Amines & Biomolecules",
                ],
            },
        ],
    },
}

STATE_BOARDS_DATA = [
    {
        "name": "Bihar Board (BSEB)",
        "badge": "PRIORITY BOARD",
        "classes": "Matric (Class 10) & Inter (Class 12 — Science, Commerce, Arts)",
        "description": "Bihar School Examination Board resources covering objective and subjective patterns, model sets, lectures, and notes.",
        "chapters": [
            "BSEB Class 10 Mathematics - Chapterwise",
            "BSEB Class 10 Science - Chapterwise",
            "BSEB Class 10 Social Science & Languages",
            "BSEB Class 12 Physics, Chemistry & Biology",
            "BSEB Class 12 Accountancy, Business Studies & Economics",
            "BSEB Class 12 History, Political Science & Geography",
        ],
    },
    {
        "name": "UP Board (UPMSP)",
        "badge": "STATE BOARD",
        "classes": "High School (Class 10) & Intermediate (Class 12)",
        "description": "UP Board chapter-wise lectures, notes, and exam preparation material.",
        "chapters": [
            "UPMSP Class 10 & 12 Science / Maths",
            "UPMSP Class 12 Commerce & Humanities",
            "UPMSP Model Paper & Revision Series",
        ],
    },
    {
        "name": "MP Board (MPBSE)",
        "badge": "STATE BOARD",
        "classes": "Class 10 & Class 12 (All Streams)",
        "description": "Madhya Pradesh Board blueprint-aligned lectures and study notes.",
        "chapters": [
            "MPBSE Class 10 & 12 Core Subjects",
            "MPBSE Chapter-wise Notes & PYQs",
        ],
    },
    {
        "name": "Rajasthan Board (RBSE)",
        "badge": "STATE BOARD",
        "classes": "Class 10 & Class 12 (All Streams)",
        "description": "RBSE syllabus-aligned chapter explanations and PDF notes.",
        "chapters": [
            "RBSE Class 10 & 12 Core Subjects",
            "RBSE Important Questions & Notes",
        ],
    },
    {
        "name": "Jharkhand Board (JAC)",
        "badge": "STATE BOARD",
        "classes": "Class 10 & Class 12 (All Streams)",
        "description": "Jharkhand Academic Council lectures and study notes.",
        "chapters": [
            "JAC Class 10 & 12 Core Subjects",
            "JAC Model Sets & Chapter Notes",
        ],
    },
]


def build_syllabus_catalog():
    catalog = {}

    c10_map = {}
    for s in CLASS10_SUBJECTS:
        c10_map[s["name"]] = list(s.get("chapters") or [])
    catalog["Class 10"] = c10_map

    for _st_key, st_obj in CLASS11_STREAMS.items():
        p_label = f"Class 11 {st_obj['name']}"
        s_map = {}
        for s in st_obj.get("subjects") or []:
            s_map[s["name"]] = list(s.get("chapters") or [])
        catalog[p_label] = s_map

    for _st_key, st_obj in CLASS12_STREAMS.items():
        p_label = f"Class 12 {st_obj['name']}"
        s_map = {}
        for s in st_obj.get("subjects") or []:
            s_map[s["name"]] = list(s.get("chapters") or [])
        catalog[p_label] = s_map

    jee_map = {}
    for _k, s_obj in JEE_SYLLABUS.items():
        chaps = []
        for u in s_obj.get("units") or []:
            chaps.extend(u.get("chapters") or [])
        jee_map[s_obj["label"]] = chaps
    catalog["JEE"] = jee_map

    neet_map = {}
    for _k, s_obj in NEET_SYLLABUS.items():
        chaps = []
        for u in s_obj.get("units") or []:
            chaps.extend(u.get("chapters") or [])
        neet_map[s_obj["label"]] = chaps
    catalog["NEET"] = neet_map

    for b_obj in STATE_BOARDS_DATA:
        catalog[b_obj["name"]] = {"General / Board Syllabus": list(b_obj.get("chapters") or [])}

    catalog["General"] = {"General Study Material": ["General Topic"]}
    return catalog


SYLLABUS_CATALOG = build_syllabus_catalog()


def normalize_upload_target(portal_type: str, subject: str, chapter_name: str):
    p_clean = (portal_type or "General").strip() or "General"
    s_clean = (subject or "General").strip() or "General"
    ch_clean = (chapter_name or "").strip()

    for cat_portal, subj_map in SYLLABUS_CATALOG.items():
        if cat_portal.lower() == p_clean.lower():
            p_clean = cat_portal
            for cat_subj, ch_list in subj_map.items():
                if cat_subj.lower() == s_clean.lower():
                    s_clean = cat_subj
                    for ch_item in ch_list:
                        if ch_clean and ch_item.lower() == ch_clean.lower():
                            ch_clean = ch_item
                            break
                    break
            break

    c_slug = slugify(ch_clean) if ch_clean else ""
    return p_clean, s_clean, ch_clean, c_slug


def _get_test_leaderboard(conn, test_id: int, limit: int = 25):
    rows = conn.execute(
        """SELECT ma.user_id, ma.user_name, ma.score AS best_score, ma.max_marks,
                  ma.total_questions, ma.correct_count, ma.wrong_count, ma.submitted_at
           FROM mock_attempts ma
           WHERE ma.test_id = ?
             AND ma.id = (
                 SELECT ma2.id FROM mock_attempts ma2
                 WHERE ma2.test_id = ma.test_id AND ma2.user_id = ma.user_id
                 ORDER BY ma2.score DESC, ma2.correct_count DESC, ma2.id ASC
                 LIMIT 1
             )
           ORDER BY ma.score DESC, ma.correct_count DESC, ma.id ASC
           LIMIT ?""",
        (test_id, limit),
    ).fetchall()

    lb = []
    for idx, r in enumerate(rows, start=1):
        d = dict(r)
        mm = float(d["max_marks"] or 0)
        if mm <= 0:
            mm = float(d["total_questions"] or 1)
            d["max_marks"] = mm
        d["rank"] = idx
        d["best_pct"] = round(max(0.0, (float(d["best_score"] or 0) / mm) * 100), 1) if mm > 0 else 0.0
        lb.append(d)
    return lb


def _load_mock_portal_data(conn, user_id, selected_id=None, portal_filter="All"):
    pf = (portal_filter or "All").strip()
    if pf and pf.lower() != "all":
        tests_rows = conn.execute(
            "SELECT * FROM mock_tests WHERE LOWER(portal_type) = LOWER(?) ORDER BY id DESC",
            (pf,),
        ).fetchall()
    else:
        tests_rows = conn.execute("SELECT * FROM mock_tests ORDER BY id DESC").fetchall()

    tests = []
    for t in tests_rows:
        td = dict(t)
        td["q_count"] = conn.execute(
            "SELECT COUNT(*) FROM mock_questions WHERE test_id = ?", (t["id"],)
        ).fetchone()[0]
        td["attempt_count"] = conn.execute(
            "SELECT COUNT(*) FROM mock_attempts WHERE test_id = ?", (t["id"],)
        ).fetchone()[0]
        tests.append(td)

    active_test = None
    questions = []
    leaderboard = []
    if selected_id:
        active_test = conn.execute("SELECT * FROM mock_tests WHERE id = ?", (selected_id,)).fetchone()
    if not active_test and tests:
        active_test = conn.execute("SELECT * FROM mock_tests WHERE id = ?", (tests[0]["id"],)).fetchone()

    if active_test:
        questions = [
            dict(q)
            for q in conn.execute(
                "SELECT * FROM mock_questions WHERE test_id = ? ORDER BY id ASC", (active_test["id"],)
            ).fetchall()
        ]
        leaderboard = _get_test_leaderboard(conn, active_test["id"], limit=25)

    my_attempts = [
        dict(a)
        for a in conn.execute(
            """SELECT ma.*, mt.title AS test_title, mt.portal_type AS portal_type
               FROM mock_attempts ma
               LEFT JOIN mock_tests mt ON ma.test_id = mt.id
               WHERE ma.user_id = ?
               ORDER BY ma.id DESC LIMIT 12""",
            (user_id,),
        ).fetchall()
    ]
    return tests, dict(active_test) if active_test else None, questions, my_attempts, leaderboard


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    conn = get_db()
    try:
        v_count = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
        n_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        banner_row = conn.execute("SELECT * FROM site_banner WHERE id = 1").fetchone()
    finally:
        conn.close()

    banner = dict(banner_row) if banner_row else {
        "badge_text": "EDUPATH FLAGSHIP",
        "title": "EDUPATH — Smart Study & Board Prep",
        "subtitle": "Video lectures, PDF notes, mock tests, and direct teacher messages for Class 10, 11, 12, JEE, NEET, and State Boards.",
        "cta_label": "Get Started Free",
        "cta_url": "/login",
        "banner_image": "",
    }
    return render_page("home.html", v_count=v_count, n_count=n_count, site_banner=banner)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        action = request.form.get("action")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        try:
            if action == "register":
                name = request.form.get("name", "").strip()
                student_class = request.form.get("student_class", "Class 10 CBSE")
                if email == ADMIN_EMAIL:
                    flash("This email address is reserved. Please register with a student email.", "error")
                elif conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                    flash("This email is already registered. Please log in instead.", "error")
                else:
                    cur = conn.execute(
                        "INSERT INTO users (name, email, password, role, student_class, theme, accent, is_blocked) VALUES (?, ?, ?, 'student', ?, 'light', '#10b981', 0)",
                        (name, email, generate_password_hash(password), student_class),
                    )
                    conn.commit()
                    session.clear()
                    session.permanent = True
                    session["user_id"] = cur.lastrowid
                    session["just_logged_in"] = True
                    get_csrf_token()
                    return redirect(url_for("dashboard"))
            else:
                user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
                if user and check_password_hash(user["password"], password):
                    if int(user["is_blocked"] or 0) == 1 and user["role"] != "admin":
                        flash("Your account has been blocked by the administrator.", "error")
                    else:
                        session.clear()
                        session.permanent = True
                        session["user_id"] = user["id"]
                        session["just_logged_in"] = True
                        get_csrf_token()
                        return redirect(url_for("dashboard"))
                else:
                    flash("Invalid email or password. Please try again.", "error")
        finally:
            conn.close()
    return render_page("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/update-banner", methods=["POST"])
def update_banner():
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only administrators can update the banner.", "error")
        return redirect(url_for("dashboard"))
    if not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(url_for("dashboard"))

    badge_text = request.form.get("badge_text", "").strip() or "EDUPATH FLAGSHIP"
    title = request.form.get("title", "").strip() or "EDUPATH Smart Learning Hub"
    subtitle = request.form.get("subtitle", "").strip() or "Lectures, PDF notes, mock tests, and direct teacher messages."
    cta_label = request.form.get("cta_label", "").strip() or "Explore"
    cta_url = request.form.get("cta_url", "").strip() or "/class10"
    if not cta_url.startswith("/"):
        cta_url = "/class10"

    conn = get_db()
    try:
        existing = conn.execute("SELECT banner_image FROM site_banner WHERE id = 1").fetchone()
        banner_img = existing["banner_image"] if existing else ""

        uploaded_img = save_uploaded_image(request.files.get("banner_file"), "banner")
        manual_img = request.form.get("banner_image_url", "").strip()
        if uploaded_img:
            banner_img = uploaded_img
        elif manual_img and is_safe_media_url(manual_img):
            banner_img = manual_img

        conn.execute(
            """UPDATE site_banner
               SET badge_text=?, title=?, subtitle=?, cta_label=?, cta_url=?, banner_image=?, updated_at=?
               WHERE id=1""",
            (badge_text, title, subtitle, cta_label, cta_url, banner_img, datetime.now().strftime("%d %b %Y")),
        )
        conn.commit()
    finally:
        conn.close()
    flash("Dashboard banner updated successfully.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/update-course-photo", methods=["POST"])
def update_course_photo():
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only administrators can update course cards.", "error")
        return redirect(url_for("dashboard"))
    if not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(url_for("dashboard"))

    course_key = request.form.get("course_key", "").strip()
    c_title = request.form.get("course_title", "").strip()
    c_sub = request.form.get("course_subtitle", "").strip()
    c_badge = request.form.get("course_badge", "").strip()

    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM course_media WHERE course_key = ?", (course_key,)).fetchone()
        if not row:
            flash("Course not found.", "error")
            return redirect(url_for("dashboard"))

        new_img = row["image_url"]
        up_img = save_uploaded_image(request.files.get("course_image_file"), f"course_{course_key}")
        url_img = request.form.get("course_image_url", "").strip()
        if up_img:
            new_img = up_img
        elif url_img and is_safe_media_url(url_img):
            new_img = url_img

        conn.execute(
            """UPDATE course_media
               SET title=?, subtitle=?, badge=?, image_url=?, updated_at=?
               WHERE course_key=?""",
            (
                c_title or row["title"],
                c_sub or row["subtitle"],
                c_badge or row["badge"],
                new_img,
                datetime.now().strftime("%d %b %Y"),
                course_key,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    flash(f"{c_title or row['title']} card updated successfully.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    welcome_banner = session.pop("just_logged_in", False)
    is_admin = (user["role"] == "admin")
    chat_vis = get_chat_visibility()

    conn = get_db()
    try:
        v_count = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
        n_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        banner_row = conn.execute("SELECT * FROM site_banner WHERE id = 1").fetchone()
        course_rows = conn.execute("SELECT * FROM course_media").fetchall()

        if is_admin or chat_vis == "public":
            d_count = conn.execute("SELECT COUNT(*) FROM doubts").fetchone()[0]
            recent_doubts = conn.execute("SELECT * FROM doubts ORDER BY id DESC LIMIT 3").fetchall()
        else:
            d_count = conn.execute("SELECT COUNT(*) FROM doubts WHERE user_id = ?", (user["id"],)).fetchone()[0]
            recent_doubts = conn.execute("SELECT * FROM doubts WHERE user_id = ? ORDER BY id DESC LIMIT 3", (user["id"],)).fetchall()
    finally:
        conn.close()

    order_map = ["class10", "class11", "class12", "jee", "neet", "mock_test", "state_boards"]
    courses_sorted = sorted(
        [dict(r) for r in course_rows],
        key=lambda x: order_map.index(x["course_key"]) if x["course_key"] in order_map else 99,
    )

    banner = dict(banner_row) if banner_row else {
        "badge_text": "EDUPATH FLAGSHIP",
        "title": "EDUPATH Smart Learning Hub",
        "subtitle": "Swipe across courses, watch video lectures, open PDF notes, and send direct messages.",
        "cta_label": "Open Class 10",
        "cta_url": "/class10",
        "banner_image": "",
        "chat_visibility": "public",
    }

    clean_img = clean_url_for_css(banner.get("banner_image") or "")
    if clean_img:
        banner_style = (
            f"background-image: linear-gradient(180deg, rgba(15,23,42,0.06) 0%, rgba(15,23,42,0.44) 100%), url('{clean_img}');"
            f"background-size: cover; background-position: center; color: #ffffff;"
        )
        banner_sub_color = "rgba(255,255,255,0.95)"
    else:
        banner_style = (
            "background: linear-gradient(125deg, color-mix(in srgb, var(--accent) 16%, var(--bg)), color-mix(in srgb, var(--accent) 5%, var(--bg)));"
        )
        banner_sub_color = "var(--muted)"

    return render_page(
        "dashboard.html",
        user=user,
        welcome_banner=welcome_banner,
        v_count=v_count,
        n_count=n_count,
        d_count=d_count,
        recent_doubts=recent_doubts,
        site_banner=banner,
        banner_style=banner_style,
        banner_sub_color=banner_sub_color,
        courses_list=courses_sorted,
        chat_visibility=chat_vis,
    )


@app.route("/send-notification", methods=["POST"])
def send_notification():
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only administrators can send notifications.", "error")
        return redirect(url_for("dashboard"))
    if not verify_csrf():
        flash("Invalid request token.", "error")
        return redirect(request.referrer or url_for("admin_panel"))

    msg = request.form.get("notification_message", "").strip()
    if msg:
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO notifications (message, target_group, target_user_id, created_by, created_at) VALUES (?, 'All', NULL, ?, ?)",
                (msg, user["name"], datetime.now().strftime("%d %b, %I:%M %p")),
            )
            conn.commit()
        finally:
            conn.close()
        flash("Notification sent to students.", "success")
    else:
        flash("Please enter a notification message.", "error")
    return redirect(request.referrer or url_for("admin_panel"))


@app.route("/delete-notification/<int:notif_id>")
def delete_notification(notif_id):
    user = current_user()
    if user and user["role"] == "admin":
        conn = get_db()
        try:
            conn.execute("DELETE FROM notifications WHERE id = ?", (notif_id,))
            conn.commit()
        finally:
            conn.close()
        flash("Notification deleted.", "success")
    return redirect(request.referrer or url_for("admin_panel"))


@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Access denied. Only administrators can access the Admin Panel.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()
    try:
        if request.method == "POST":
            if not verify_csrf():
                flash("Security verification failed. Please refresh and try again.", "error")
                return redirect(url_for("admin_panel"))

            form_type = request.form.get("form_type", "").strip()

            if form_type == "upload_video":
                title = (request.form.get("title") or "").strip()
                portal_type, subject, chapter_name, c_slug = normalize_upload_target(
                    request.form.get("portal_type"),
                    request.form.get("subject"),
                    request.form.get("chapter_name"),
                )
                vid_file = request.files.get("video_file")
                thumb_file = request.files.get("thumbnail_file")

                if title and vid_file and vid_file.filename and has_allowed_ext(vid_file.filename, ALLOWED_VIDEO_EXTS):
                    try:
                        v_name = _save_video_with_transcode(vid_file, app.config["UPLOAD_FOLDER"])

                        t_name = ""
                        if thumb_file and thumb_file.filename and has_allowed_ext(thumb_file.filename, ALLOWED_IMAGE_EXTS):
                            t_name = secure_filename(f"thumb_{int(datetime.now().timestamp())}_{thumb_file.filename}")
                            thumb_file.save(os.path.join(app.config["UPLOAD_FOLDER"], t_name))

                        conn.execute(
                            """INSERT INTO videos (title, subject, portal_type, chapter_slug, chapter_name, video_file, thumbnail_file, added_by, created_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (title, subject, portal_type, c_slug, chapter_name, v_name, t_name, user["name"], datetime.now().strftime("%d %b %Y")),
                        )
                        conn.commit()
                        flash(f"Video lecture '{title}' ({portal_type} • {subject}) uploaded.", "success")
                    except Exception as exc:
                        flash(f"Video upload failed: {exc}", "error")
                else:
                    flash("Please provide a title and a valid video file (.mp4, .mov, .mkv, .webm).", "error")

            elif form_type == "update_thumbnail":
                vid_id = request.form.get("vid_id")
                thumb_file = request.files.get("new_thumbnail")
                if vid_id and thumb_file and thumb_file.filename and has_allowed_ext(thumb_file.filename, ALLOWED_IMAGE_EXTS):
                    try:
                        t_name = secure_filename(f"thumb_{int(datetime.now().timestamp())}_{thumb_file.filename}")
                        thumb_file.save(os.path.join(app.config["UPLOAD_FOLDER"], t_name))
                        conn.execute("UPDATE videos SET thumbnail_file = ? WHERE id = ?", (t_name, vid_id))
                        conn.commit()
                        flash("Video thumbnail updated.", "success")
                    except Exception as exc:
                        flash(f"Thumbnail update failed: {exc}", "error")
                else:
                    flash("Please select a valid image file (.jpg, .png, .webp).", "error")

            elif form_type == "upload_note":
                title = (request.form.get("title") or "").strip()
                portal_type, subject, chapter_name, c_slug = normalize_upload_target(
                    request.form.get("portal_type"),
                    request.form.get("subject"),
                    request.form.get("chapter_name"),
                )
                pdf = request.files.get("pdf_file")
                if title and pdf and pdf.filename and has_allowed_ext(pdf.filename, ALLOWED_PDF_EXTS):
                    try:
                        fname = secure_filename(f"note_{int(datetime.now().timestamp())}_{pdf.filename}")
                        pdf.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
                        conn.execute(
                            """INSERT INTO notes (title, subject, portal_type, chapter_slug, chapter_name, filename, uploaded_by, created_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (title, subject, portal_type, c_slug, chapter_name, fname, user["name"], datetime.now().strftime("%d %b %Y")),
                        )
                        conn.commit()
                        flash(f"PDF note '{title}' ({portal_type} • {subject}) uploaded.", "success")
                    except Exception as exc:
                        flash(f"PDF upload failed: {exc}", "error")
                else:
                    flash("Please provide a title and a .PDF file.", "error")

            return redirect(url_for("admin_panel"))

        videos = conn.execute("SELECT * FROM videos ORDER BY id DESC").fetchall()
        notes = conn.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
        students = conn.execute("SELECT * FROM users WHERE email != ? ORDER BY id DESC", (ADMIN_EMAIL,)).fetchall()
        all_doubts = conn.execute("SELECT * FROM doubts ORDER BY id DESC").fetchall()
        all_comments = conn.execute("SELECT * FROM video_comments ORDER BY id DESC").fetchall()
        all_notifs = conn.execute("SELECT * FROM notifications ORDER BY id DESC").fetchall()
        banner_row = conn.execute("SELECT * FROM site_banner WHERE id = 1").fetchone()
        course_rows = conn.execute("SELECT * FROM course_media").fetchall()
        mock_tests, _, _, _, _ = _load_mock_portal_data(conn, user["id"])
    finally:
        conn.close()

    return render_page(
        "admin_panel.html",
        user=user,
        videos=videos,
        notes=notes,
        students=students,
        all_doubts=all_doubts,
        all_comments=all_comments,
        all_notifs=all_notifs,
        site_banner=dict(banner_row) if banner_row else {},
        courses_list=[dict(r) for r in course_rows],
        mock_tests=mock_tests,
        syllabus_catalog=SYLLABUS_CATALOG,
        syllabus_catalog_json=_ep_json.dumps(SYLLABUS_CATALOG),
    )


@app.route("/delete-video/<int:vid_id>", methods=["GET", "POST"])
@app.route("/delete_video/<int:vid_id>", methods=["GET", "POST"])
@app.route("/admin/delete-video/<int:vid_id>", methods=["GET", "POST"])
@app.route("/admin/video/delete/<int:vid_id>", methods=["GET", "POST"])
def delete_video(vid_id):
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only administrators can delete videos.", "error")
        return redirect(request.referrer or url_for("dashboard"))
    if request.method == "POST" and not verify_csrf():
        flash("Security verification failed. Please refresh and try again.", "error")
        return redirect(request.referrer or url_for("admin_panel"))

    conn = get_db()
    try:
        row = conn.execute("SELECT video_file, thumbnail_file FROM videos WHERE id = ?", (vid_id,)).fetchone()
        if row:
            for fname in (row["video_file"], row["thumbnail_file"]):
                if fname:
                    fpath = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(fname))
                    if os.path.exists(fpath):
                        try:
                            os.remove(fpath)
                        except OSError:
                            pass
        conn.execute("DELETE FROM video_reactions WHERE video_id = ?", (vid_id,))
        conn.execute("DELETE FROM video_comments WHERE video_id = ?", (vid_id,))
        conn.execute("DELETE FROM videos WHERE id = ?", (vid_id,))
        conn.commit()
    finally:
        conn.close()
    flash("Video deleted.", "success")
    return redirect(request.referrer or url_for("admin_panel"))


@app.route("/delete-note/<int:note_id>")
def delete_note(note_id):
    user = current_user()
    if user and user["role"] == "admin":
        conn = get_db()
        try:
            row = conn.execute("SELECT filename FROM notes WHERE id = ?", (note_id,)).fetchone()
            if row and row["filename"]:
                fpath = os.path.join(app.config["UPLOAD_FOLDER"], row["filename"])
                if os.path.exists(fpath):
                    os.remove(fpath)
            conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
        finally:
            conn.close()
        flash("PDF note deleted.", "success")
    return redirect(request.referrer or url_for("admin_panel"))


@app.route("/delete-doubt/<int:doubt_id>", methods=["GET", "POST"])
def delete_doubt(doubt_id):
    user = current_user()
    is_ajax = (request.headers.get("X-Requested-With") == "XMLHttpRequest")
    if not user or user["role"] != "admin":
        if is_ajax:
            return jsonify({"ok": False, "error": "Only administrators can delete messages."}), 403
        flash("Only administrators can delete messages.", "error")
        return redirect(request.referrer or url_for("ai_doubt"))

    if request.method == "POST" and not verify_csrf():
        if is_ajax:
            return jsonify({"ok": False, "error": "Security verification failed."}), 403
        flash("Security verification failed.", "error")
        return redirect(request.referrer or url_for("ai_doubt"))

    conn = get_db()
    try:
        conn.execute("DELETE FROM doubts WHERE id = ?", (doubt_id,))
        conn.execute("DELETE FROM doubt_reactions WHERE doubt_id = ?", (doubt_id,))
        conn.commit()
    finally:
        conn.close()

    if is_ajax:
        return jsonify({"ok": True, "deleted_id": doubt_id})
    flash("Message deleted.", "success")
    return redirect(request.referrer or url_for("ai_doubt"))


@app.route("/cbse")
def cbse():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    sample_papers = [
        {"subject": "Mathematics (Standard & Basic)", "code": "041 / 241", "year": "2026-27", "marks": "80", "tag": "HIGH WEIGHTAGE"},
        {"subject": "Science (Phy, Chem, Bio)", "code": "086", "year": "2026-27", "marks": "80", "tag": "COMPETENCY SQP"},
        {"subject": "English (Lang & Lit / Comm.)", "code": "184 / 101", "year": "2026-27", "marks": "80", "tag": "OFFICIAL SQP"},
        {"subject": "Social Science", "code": "087", "year": "2026-27", "marks": "80", "tag": "OFFICIAL SQP"},
        {"subject": "Hindi (Course A & B)", "code": "002 / 085", "year": "2026-27", "marks": "80", "tag": "OFFICIAL SQP"},
        {"subject": "Artificial Intelligence / IT", "code": "417 / 402", "year": "2026-27", "marks": "50", "tag": "SKILL SUBJECT"},
    ]
    datesheet_10 = [
        {"date": "16 Feb 2027", "day": "Tuesday", "subject": "Painting (049)", "time": "10:30 AM - 12:30 PM"},
        {"date": "17 Feb 2027", "day": "Wednesday", "subject": "Mathematics Standard (041) / Basic (241)", "time": "10:30 AM - 01:30 PM"},
        {"date": "19 Feb 2027", "day": "Friday", "subject": "Home Science (064)", "time": "10:30 AM - 01:30 PM"},
        {"date": "22 Feb 2027", "day": "Monday", "subject": "Science (086)", "time": "10:30 AM - 01:30 PM"},
        {"date": "24 Feb 2027", "day": "Wednesday", "subject": "Computer App. (165) / IT (402) / AI (417)", "time": "10:30 AM - 12:30 PM"},
        {"date": "26 Feb 2027", "day": "Friday", "subject": "English Comm. (101) / Lang & Lit (184)", "time": "10:30 AM - 01:30 PM"},
        {"date": "01 Mar 2027", "day": "Monday", "subject": "Sanskrit (122 / 119) / Arabic (016)", "time": "10:30 AM - 01:30 PM"},
        {"date": "03 Mar 2027", "day": "Wednesday", "subject": "Hindi Course-A (002) / Course-B (085)", "time": "10:30 AM - 01:30 PM"},
        {"date": "06 Mar 2027", "day": "Saturday", "subject": "French (018)", "time": "10:30 AM - 01:30 PM"},
        {"date": "08 Mar 2027", "day": "Monday", "subject": "Social Science (087)", "time": "10:30 AM - 01:30 PM"},
    ]
    datesheet_12 = [
        {"date": "16 Feb 2027", "day": "Tuesday", "subject": "Physics (042)", "time": "10:30 AM - 01:30 PM"},
        {"date": "18 Feb 2027", "day": "Thursday", "subject": "Physical Education (048)", "time": "10:30 AM - 01:30 PM"},
        {"date": "23 Feb 2027", "day": "Tuesday", "subject": "Accountancy (055)", "time": "10:30 AM - 01:30 PM"},
        {"date": "25 Feb 2027", "day": "Thursday", "subject": "Geography (029)", "time": "10:30 AM - 01:30 PM"},
        {"date": "27 Feb 2027", "day": "Saturday", "subject": "Chemistry (043)", "time": "10:30 AM - 01:30 PM"},
        {"date": "05 Mar 2027", "day": "Friday", "subject": "English Core (301) / Elective (101)", "time": "10:30 AM - 01:30 PM"},
        {"date": "09 Mar 2027", "day": "Tuesday", "subject": "Mathematics (041) / Applied Maths (241)", "time": "10:30 AM - 01:30 PM"},
        {"date": "16 Mar 2027", "day": "Tuesday", "subject": "Economics (030)", "time": "10:30 AM - 01:30 PM"},
        {"date": "25 Mar 2027", "day": "Thursday", "subject": "Biology (044)", "time": "10:30 AM - 01:30 PM"},
        {"date": "31 Mar 2027", "day": "Wednesday", "subject": "Computer Science (083) / IP (065)", "time": "10:30 AM - 01:30 PM"},
        {"date": "01 Apr 2027", "day": "Thursday", "subject": "Business Studies (054)", "time": "10:30 AM - 01:30 PM"},
    ]
    return render_page(
        "cbse.html",
        user=user,
        sample_papers=sample_papers,
        datesheet_10=datesheet_10,
        datesheet_12=datesheet_12,
    )


@app.route("/class10", methods=["GET", "POST"])
def class10():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    conn = get_db()
    try:
        if request.method == "POST":
            if user["role"] != "admin":
                flash("Only administrators can upload Class 10 lectures or PDF notes.", "error")
                return redirect(url_for("class10"))
            if not verify_csrf():
                flash("Security verification failed.", "error")
                return redirect(url_for("class10"))

            upload_kind = request.form.get("upload_kind", "").strip()
            subj = (request.form.get("subject") or "Science (086)").strip()
            ch_name = (request.form.get("chapter_name") or "").strip()
            c_slug = slugify(ch_name) if ch_name else ""

            if upload_kind == "lecture":
                title = (request.form.get("title") or "").strip()
                vid_file = request.files.get("video_file")
                thumb_file = request.files.get("thumbnail_file")
                if title and vid_file and vid_file.filename and has_allowed_ext(vid_file.filename, ALLOWED_VIDEO_EXTS):
                    try:
                        v_name = _save_video_with_transcode(vid_file, app.config["UPLOAD_FOLDER"])
                        t_name = ""
                        if thumb_file and thumb_file.filename and has_allowed_ext(thumb_file.filename, ALLOWED_IMAGE_EXTS):
                            t_name = secure_filename(f"thumb_{int(datetime.now().timestamp())}_{thumb_file.filename}")
                            thumb_file.save(os.path.join(app.config["UPLOAD_FOLDER"], t_name))
                        conn.execute(
                            """INSERT INTO videos (title, subject, portal_type, chapter_slug, chapter_name, video_file, thumbnail_file, added_by, created_at)
                               VALUES (?, ?, 'Class 10', ?, ?, ?, ?, ?, ?)""",
                            (title, subj, c_slug, ch_name, v_name, t_name, user["name"], datetime.now().strftime("%d %b %Y")),
                        )
                        conn.commit()
                        flash("Class 10 lecture uploaded successfully.", "success")
                    except Exception as exc:
                        flash(f"Lecture upload failed: {exc}", "error")
                else:
                    flash("Please provide a title and a valid video file.", "error")

            elif upload_kind == "note":
                title = (request.form.get("title") or "").strip()
                pdf = request.files.get("pdf_file")
                if title and pdf and pdf.filename and has_allowed_ext(pdf.filename, ALLOWED_PDF_EXTS):
                    try:
                        fname = secure_filename(f"note_{int(datetime.now().timestamp())}_{pdf.filename}")
                        pdf.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
                        conn.execute(
                            """INSERT INTO notes (title, subject, portal_type, chapter_slug, chapter_name, filename, uploaded_by, created_at)
                               VALUES (?, ?, 'Class 10', ?, ?, ?, ?, ?)""",
                            (title, subj, c_slug, ch_name, fname, user["name"], datetime.now().strftime("%d %b %Y")),
                        )
                        conn.commit()
                        flash("Class 10 PDF note uploaded successfully.", "success")
                    except Exception as exc:
                        flash(f"PDF upload failed: {exc}", "error")
                else:
                    flash("Please provide a title and a .PDF file.", "error")

            return redirect(url_for("class10"))

        c10_videos = conn.execute("SELECT * FROM videos WHERE portal_type = 'Class 10' ORDER BY id DESC").fetchall()
        c10_notes = conn.execute("SELECT * FROM notes WHERE portal_type = 'Class 10' ORDER BY id DESC").fetchall()
    finally:
        conn.close()

    return render_page(
        "class10.html",
        user=user,
        subjects=CLASS10_SUBJECTS,
        videos=c10_videos,
        notes=c10_notes,
        slugify=slugify,
    )


def _render_stream_portal(class_label: str, stream_key: str, streams_dict: dict, index_url: str):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    stream_obj = streams_dict.get(stream_key.lower())
    if not stream_obj:
        flash("Stream not found.", "error")
        return redirect(index_url)
    section_slug = f"{class_label.lower().replace(' ', '')}-{stream_key.lower()}"
    return render_page(
        "stream_detail.html",
        user=user,
        class_label=class_label,
        stream_key=stream_key.lower(),
        section_slug=section_slug,
        back_url=index_url,
        portal_prefix=f"{class_label} {stream_obj['name']}",
        stream_obj=stream_obj,
        slugify=slugify,
    )


@app.route("/class11")
def class11():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return render_page("class11.html", user=user, streams=CLASS11_STREAMS)


@app.route("/class11/science")
def class11_science():
    return _render_stream_portal("Class 11", "science", CLASS11_STREAMS, url_for("class11"))


@app.route("/class11/commerce")
def class11_commerce():
    return _render_stream_portal("Class 11", "commerce", CLASS11_STREAMS, url_for("class11"))


@app.route("/class11/arts")
def class11_arts():
    return _render_stream_portal("Class 11", "arts", CLASS11_STREAMS, url_for("class11"))


@app.route("/class11/<stream_key>")
def class11_stream(stream_key):
    return _render_stream_portal("Class 11", stream_key, CLASS11_STREAMS, url_for("class11"))


@app.route("/class12")
def class12():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return render_page("class12.html", user=user, streams=CLASS12_STREAMS)


@app.route("/class12/science")
def class12_science():
    return _render_stream_portal("Class 12", "science", CLASS12_STREAMS, url_for("class12"))


@app.route("/class12/commerce")
def class12_commerce():
    return _render_stream_portal("Class 12", "commerce", CLASS12_STREAMS, url_for("class12"))


@app.route("/class12/arts")
def class12_arts():
    return _render_stream_portal("Class 12", "arts", CLASS12_STREAMS, url_for("class12"))


@app.route("/class12/<stream_key>")
def class12_stream(stream_key):
    return _render_stream_portal("Class 12", stream_key, CLASS12_STREAMS, url_for("class12"))


@app.route("/jee")
def jee():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return render_page("jee.html", user=user, jee_syllabus=JEE_SYLLABUS)


@app.route("/jee/<subj_key>")
def jee_subject(subj_key):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    subj_obj = JEE_SYLLABUS.get(subj_key.lower())
    if not subj_obj:
        flash("JEE subject not found.", "error")
        return redirect(url_for("jee"))
    return render_page(
        "exam_subject_portal.html",
        user=user,
        exam_name="JEE",
        back_url=url_for("jee"),
        subj_obj=subj_obj,
        slugify=slugify,
    )


@app.route("/neet")
def neet():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return render_page("neet.html", user=user, neet_syllabus=NEET_SYLLABUS)


@app.route("/neet/<subj_key>")
def neet_subject(subj_key):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    subj_obj = NEET_SYLLABUS.get(subj_key.lower())
    if not subj_obj:
        flash("NEET subject not found.", "error")
        return redirect(url_for("neet"))
    return render_page(
        "exam_subject_portal.html",
        user=user,
        exam_name="NEET",
        back_url=url_for("neet"),
        subj_obj=subj_obj,
        slugify=slugify,
    )


@app.route("/state-boards")
def state_boards():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    selected_board = request.args.get("board", "Bihar Board (BSEB)")
    return render_page(
        "state_boards.html",
        user=user,
        boards_info=STATE_BOARDS_DATA,
        selected_board=selected_board,
        slugify=slugify,
    )


@app.route("/subject-portal/<section>/<subj_slug>")
def subject_portal(section, subj_slug):
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    found_subj = None
    back_url = url_for("class10")
    section_label = section

    if section == "class10":
        back_url = url_for("class10")
        section_label = "Class 10"
        for s in CLASS10_SUBJECTS:
            if slugify(s["name"]) == subj_slug:
                found_subj = s
                break

    elif section.startswith("class11-"):
        st_key = section.replace("class11-", "", 1)
        st_obj = CLASS11_STREAMS.get(st_key)
        if st_obj:
            back_url = url_for("class11_stream", stream_key=st_key)
            section_label = f"Class 11 {st_obj['name']}"
            for s in st_obj["subjects"]:
                if slugify(s["name"]) == subj_slug:
                    found_subj = s
                    break

    elif section.startswith("class12-"):
        st_key = section.replace("class12-", "", 1)
        st_obj = CLASS12_STREAMS.get(st_key)
        if st_obj:
            back_url = url_for("class12_stream", stream_key=st_key)
            section_label = f"Class 12 {st_obj['name']}"
            for s in st_obj["subjects"]:
                if slugify(s["name"]) == subj_slug:
                    found_subj = s
                    break

    elif section == "jee":
        s_obj = JEE_SYLLABUS.get(subj_slug.lower())
        if s_obj:
            back_url = url_for("jee")
            section_label = "JEE"
            all_ch = []
            for u in s_obj["units"]:
                all_ch.extend(u["chapters"])
            found_subj = {
                "name": s_obj["label"],
                "icon": s_obj["icon"],
                "detail": s_obj["explanation"],
                "chapters": all_ch,
                "units": s_obj["units"],
            }

    elif section == "neet":
        s_obj = NEET_SYLLABUS.get(subj_slug.lower())
        if s_obj:
            back_url = url_for("neet")
            section_label = "NEET"
            all_ch = []
            for u in s_obj["units"]:
                all_ch.extend(u["chapters"])
            found_subj = {
                "name": s_obj["label"],
                "icon": s_obj["icon"],
                "detail": s_obj["explanation"],
                "chapters": all_ch,
                "units": s_obj["units"],
            }

    if not found_subj:
        flash("Subject not found.", "error")
        return redirect(back_url)

    conn = get_db()
    try:
        s_videos = conn.execute(
            "SELECT * FROM videos WHERE subject = ? ORDER BY id DESC",
            (found_subj["name"],),
        ).fetchall()
        s_notes = conn.execute(
            "SELECT * FROM notes WHERE subject = ? ORDER BY id DESC",
            (found_subj["name"],),
        ).fetchall()
    finally:
        conn.close()

    return render_page(
        "subject_portal.html",
        user=user,
        section=section,
        section_label=section_label,
        back_url=back_url,
        subj=found_subj,
        videos=s_videos,
        notes=s_notes,
        slugify=slugify,
    )


@app.route("/chapter/<portal_type>/<slug>", methods=["GET", "POST"])
def chapter_portal(portal_type, slug):
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    chapter_title = request.args.get("title", "").strip() or slug.replace("-", " ").title()
    subject_label = request.args.get("subject", portal_type).strip()

    conn = get_db()
    try:
        if request.method == "POST":
            if user["role"] != "admin":
                flash("Only administrators can upload chapter lectures or PDF notes.", "error")
                return redirect(url_for("chapter_portal", portal_type=portal_type, slug=slug, title=chapter_title, subject=subject_label))
            if not verify_csrf():
                flash("Security verification failed.", "error")
                return redirect(url_for("chapter_portal", portal_type=portal_type, slug=slug, title=chapter_title, subject=subject_label))

            add_type = (request.form.get("add_type") or "").strip()
            ch_name = (request.form.get("chapter_name") or chapter_title).strip() or chapter_title
            ch_slug = slugify(ch_name)
            subj = (request.form.get("subject") or subject_label).strip() or subject_label

            if add_type == "lecture":
                v_title = (request.form.get("title") or "").strip()
                vid_file = request.files.get("video_file")
                thumb_file = request.files.get("thumbnail_file")
                if v_title and vid_file and vid_file.filename and has_allowed_ext(vid_file.filename, ALLOWED_VIDEO_EXTS):
                    try:
                        v_name = _save_video_with_transcode(vid_file, app.config["UPLOAD_FOLDER"])
                        t_name = ""
                        if thumb_file and thumb_file.filename and has_allowed_ext(thumb_file.filename, ALLOWED_IMAGE_EXTS):
                            t_name = secure_filename(f"thumb_{int(datetime.now().timestamp())}_{thumb_file.filename}")
                            thumb_file.save(os.path.join(app.config["UPLOAD_FOLDER"], t_name))
                        conn.execute(
                            """INSERT INTO videos (title, subject, portal_type, chapter_slug, chapter_name, video_file, thumbnail_file, added_by, created_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (v_title, subj, portal_type, ch_slug, ch_name, v_name, t_name, user["name"], datetime.now().strftime("%d %b %Y")),
                        )
                        conn.commit()
                        flash("Chapter lecture uploaded successfully.", "success")
                    except Exception as exc:
                        flash(f"Lecture upload failed: {exc}", "error")
                else:
                    flash("Please provide a lecture title and a valid video file (.mp4, .mov, .webm).", "error")

            elif add_type == "note":
                n_title = (request.form.get("title") or "").strip()
                pdf = request.files.get("pdf_file")
                if n_title and pdf and pdf.filename and has_allowed_ext(pdf.filename, ALLOWED_PDF_EXTS):
                    try:
                        fname = secure_filename(f"note_{int(datetime.now().timestamp())}_{pdf.filename}")
                        pdf.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
                        conn.execute(
                            """INSERT INTO notes (title, subject, portal_type, chapter_slug, chapter_name, filename, uploaded_by, created_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (n_title, subj, portal_type, ch_slug, ch_name, fname, user["name"], datetime.now().strftime("%d %b %Y")),
                        )
                        conn.commit()
                        flash("Chapter PDF note uploaded successfully.", "success")
                    except Exception as exc:
                        flash(f"PDF upload failed: {exc}", "error")
                else:
                    flash("Please provide a note title and a .PDF file.", "error")

            return redirect(url_for("chapter_portal", portal_type=portal_type, slug=ch_slug, title=ch_name, subject=subj))

        if subject_label and subject_label != portal_type:
            ch_videos = conn.execute(
                "SELECT * FROM videos WHERE chapter_slug = ? AND LOWER(COALESCE(portal_type,'')) = LOWER(?) AND LOWER(COALESCE(subject,'')) = LOWER(?) ORDER BY id DESC",
                (slug, portal_type, subject_label),
            ).fetchall()
            ch_notes = conn.execute(
                "SELECT * FROM notes WHERE chapter_slug = ? AND LOWER(COALESCE(portal_type,'')) = LOWER(?) AND LOWER(COALESCE(subject,'')) = LOWER(?) ORDER BY id DESC",
                (slug, portal_type, subject_label),
            ).fetchall()
        else:
            ch_videos = conn.execute(
                "SELECT * FROM videos WHERE chapter_slug = ? AND LOWER(COALESCE(portal_type,'')) = LOWER(?) ORDER BY id DESC",
                (slug, portal_type),
            ).fetchall()
            ch_notes = conn.execute(
                "SELECT * FROM notes WHERE chapter_slug = ? AND LOWER(COALESCE(portal_type,'')) = LOWER(?) ORDER BY id DESC",
                (slug, portal_type),
            ).fetchall()
    finally:
        conn.close()

    return render_page(
        "chapter_portal.html",
        user=user,
        portal_type=portal_type,
        slug=slug,
        chapter_title=chapter_title,
        subject_label=subject_label,
        videos=ch_videos,
        notes=ch_notes,
    )


@app.route("/videos")
def videos():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    conn = get_db()
    try:
        subj = request.args.get("subject", "All")
        portal_sel = request.args.get("portal", "All")
        query = "SELECT * FROM videos WHERE 1=1"
        params = []
        if subj and subj != "All":
            query += " AND subject = ?"
            params.append(subj)
        if portal_sel and portal_sel != "All":
            query += " AND LOWER(COALESCE(portal_type, 'General')) = LOWER(?)"
            params.append(portal_sel)
        query += " ORDER BY id DESC"
        raw_videos = conn.execute(query, params).fetchall()

        video_list = []
        for v in raw_videos:
            vid_dict = dict(v)
            r_rows = conn.execute(
                "SELECT reaction, COUNT(*) as cnt FROM video_reactions WHERE video_id = ? GROUP BY reaction",
                (v["id"],),
            ).fetchall()
            vid_dict["reactions"] = {r["reaction"]: r["cnt"] for r in r_rows}

            u_rows = conn.execute(
                "SELECT reaction FROM video_reactions WHERE video_id = ? AND user_id = ?",
                (v["id"], user["id"]),
            ).fetchall()
            vid_dict["user_reactions"] = [u["reaction"] for u in u_rows]

            c_rows = conn.execute(
                "SELECT * FROM video_comments WHERE video_id = ? ORDER BY id DESC",
                (v["id"],),
            ).fetchall()
            vid_dict["comments"] = c_rows
            video_list.append(vid_dict)
    finally:
        conn.close()

    return render_page("videos.html", user=user, videos=video_list, active_subj=subj)


@app.route("/react-video/<int:vid_id>", methods=["POST"])
def react_video(vid_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(request.referrer or url_for("videos"))
    reaction = request.form.get("reaction")
    if reaction in ["👍", "❤️", "🔥", "💡"]:
        conn = get_db()
        try:
            existing = conn.execute(
                "SELECT id FROM video_reactions WHERE video_id = ? AND user_id = ? AND reaction = ?",
                (vid_id, user["id"], reaction),
            ).fetchone()
            if existing:
                conn.execute("DELETE FROM video_reactions WHERE id = ?", (existing["id"],))
            else:
                conn.execute(
                    "INSERT INTO video_reactions (video_id, user_id, reaction) VALUES (?, ?, ?)",
                    (vid_id, user["id"], reaction),
                )
            conn.commit()
        finally:
            conn.close()
    return redirect(request.referrer or url_for("videos"))


@app.route("/comment-video/<int:vid_id>", methods=["POST"])
def comment_video(vid_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(request.referrer or url_for("videos"))
    comment = request.form.get("comment", "").strip()
    if comment:
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO video_comments (video_id, user_id, user_name, user_role, comment, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (vid_id, user["id"], user["name"], user["role"], comment, datetime.now().strftime("%d %b, %I:%M %p")),
            )
            conn.commit()
        finally:
            conn.close()
    return redirect(request.referrer or url_for("videos"))


@app.route("/reply-comment/<int:comment_id>", methods=["POST"])
def reply_comment(comment_id):
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only administrators can reply to comments.", "error")
        return redirect(request.referrer or url_for("videos"))
    if not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(request.referrer or url_for("videos"))
    reply_text = request.form.get("admin_reply", "").strip()
    if reply_text:
        conn = get_db()
        try:
            conn.execute(
                "UPDATE video_comments SET admin_reply = ?, replied_by = ?, replied_at = ? WHERE id = ?",
                (reply_text, user["name"], datetime.now().strftime("%d %b, %I:%M %p"), comment_id),
            )
            conn.commit()
        finally:
            conn.close()
        flash("Comment reply posted.", "success")
    return redirect(request.referrer or url_for("videos"))


@app.route("/delete-comment/<int:comment_id>", methods=["GET", "POST"])
def delete_comment(comment_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    conn = get_db()
    try:
        row = conn.execute("SELECT user_id FROM video_comments WHERE id = ?", (comment_id,)).fetchone()
        if row and (user["role"] == "admin" or row["user_id"] == user["id"]):
            conn.execute("DELETE FROM video_comments WHERE id = ?", (comment_id,))
            conn.commit()
            flash("Comment deleted.", "success")
    finally:
        conn.close()
    return redirect(request.referrer or url_for("videos"))


@app.route("/notes")
def notes():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    conn = get_db()
    try:
        subj = request.args.get("subject", "All")
        portal_sel = request.args.get("portal", "All")
        query = "SELECT * FROM notes WHERE 1=1"
        params = []
        if subj and subj != "All":
            query += " AND subject = ?"
            params.append(subj)
        if portal_sel and portal_sel != "All":
            query += " AND LOWER(COALESCE(portal_type, 'General')) = LOWER(?)"
            params.append(portal_sel)
        query += " ORDER BY id DESC"
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()
    return render_page("notes.html", user=user, notes=rows, active_subj=subj)


def _evaluate_and_save_mock_submission(conn, user, test_id: int):
    test_row = conn.execute("SELECT * FROM mock_tests WHERE id = ?", (test_id,)).fetchone()
    if not test_row:
        flash("Mock test not found.", "error")
        return None

    q_rows = conn.execute(
        "SELECT * FROM mock_questions WHERE test_id = ? ORDER BY id ASC", (test_id,)
    ).fetchall()

    pos_marks = float(test_row["marks_per_question"] or 1.0)
    neg_marks = float(test_row["negative_marks"] or 0.0)

    correct_cnt = 0
    wrong_cnt = 0
    unattempted_cnt = 0
    review = []
    for q in q_rows:
        chosen = (request.form.get(f"q_{q['id']}") or "").strip().upper()
        if not chosen:
            unattempted_cnt += 1
            status = "unattempted"
            delta = 0.0
        elif chosen == q["correct_option"]:
            correct_cnt += 1
            status = "correct"
            delta = pos_marks
        else:
            wrong_cnt += 1
            status = "wrong"
            delta = -neg_marks

        review.append({
            "question_text": q["question_text"],
            "question_type": q["question_type"] if "question_type" in q.keys() and q["question_type"] else "mcq",
            "chosen": chosen or "Not answered",
            "correct_option": q["correct_option"],
            "is_correct": (status == "correct"),
            "status": status,
            "marks_delta": delta,
        })

    total_q = len(q_rows)
    positive_earned = round(correct_cnt * pos_marks, 2)
    negative_deducted = round(wrong_cnt * neg_marks, 2)
    net_score = round(positive_earned - negative_deducted, 2)
    max_marks = round(total_q * pos_marks, 2)

    now_str = datetime.now().strftime("%d %b, %I:%M %p")
    conn.execute(
        """INSERT INTO mock_attempts (test_id, user_id, user_name, score, total_questions, correct_count, wrong_count, unattempted_count, max_marks, submitted_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (test_id, user["id"], user["name"], net_score, total_q, correct_cnt, wrong_cnt, unattempted_cnt, max_marks, now_str),
    )
    conn.commit()

    tests, active_test, questions, my_attempts, leaderboard = _load_mock_portal_data(conn, user["id"], test_id)
    attempted_test_ids = [
        r["test_id"]
        for r in conn.execute("SELECT DISTINCT test_id FROM mock_attempts WHERE user_id = ?", (user["id"],)).fetchall()
    ]
    my_rank = next((item["rank"] for item in leaderboard if item["user_id"] == user["id"]), 1)
    pct = round(max(0.0, (net_score / max_marks) * 100), 1) if max_marks > 0 else 0.0
    result_data = {
        "test_title": test_row["title"],
        "score": net_score,
        "total": total_q,
        "max_marks": max_marks,
        "correct": correct_cnt,
        "wrong": wrong_cnt,
        "unattempted": unattempted_cnt,
        "positive_earned": positive_earned,
        "negative_deducted": negative_deducted,
        "rank": my_rank,
        "pct": pct,
        "review": review,
    }
    active_portal_val = (test_row["portal_type"] if "portal_type" in test_row.keys() and test_row["portal_type"] else "All")
    return render_page(
        "mock_test.html",
        user=user,
        tests=tests,
        active_test=active_test,
        questions=questions,
        my_attempts=my_attempts,
        leaderboard=leaderboard,
        attempted_test_ids=attempted_test_ids,
        already_attempted=False,
        active_portal=active_portal_val,
        result_data=result_data,
    )


@app.route("/mock-test", methods=["GET", "POST"])
@app.route("/mock-tests", methods=["GET", "POST"])
def mock_test_portal():
    user = current_user()
    if not user:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "error": "Session expired. Please log in again."}), 401
        return redirect(url_for("login"))

    is_ajax = (request.headers.get("X-Requested-With") == "XMLHttpRequest")
    conn = get_db()
    try:
        if request.method == "POST":
            if not verify_csrf():
                if is_ajax:
                    return jsonify({"ok": False, "error": "Security verification failed. Please refresh the page."}), 403
                flash("Security verification failed.", "error")
                return redirect(url_for("mock_test_portal"))

            action = (request.form.get("action") or request.form.get("form_type") or "").strip()
            redirect_to = (request.form.get("redirect_to") or "").strip()

            if not action or action == "submit_test":
                sub_tid = request.args.get("test_id", type=int) or int(request.form.get("test_id") or 0)
                if not sub_tid:
                    for fk in request.form:
                        if fk.startswith("q_") and fk[2:].isdigit():
                            ql = conn.execute("SELECT test_id FROM mock_questions WHERE id = ?", (int(fk[2:]),)).fetchone()
                            if ql:
                                sub_tid = int(ql["test_id"])
                                break
                if sub_tid:
                    rendered = _evaluate_and_save_mock_submission(conn, user, sub_tid)
                    if rendered is not None:
                        return rendered
                return redirect(url_for("mock_test_portal"))

            if user["role"] != "admin":
                if is_ajax:
                    return jsonify({"ok": False, "error": "Only administrators can create mock tests or add questions."}), 403
                flash("Only administrators can create mock tests or add questions.", "error")
                return redirect(url_for("mock_test_portal"))

            if action == "create_test":
                title = (request.form.get("title") or "").strip()
                subject = (request.form.get("subject") or "General").strip()
                portal_type = (request.form.get("portal_type") or "Class 10").strip()
                try:
                    duration = max(1, min(300, int(request.form.get("duration_minutes") or 15)))
                except ValueError:
                    duration = 15

                def_pos, def_neg = default_marking_for_portal(portal_type)
                raw_pos = (request.form.get("marks_per_question") or "").strip()
                raw_neg = (request.form.get("negative_marks") or "").strip()
                try:
                    pos_marks = max(0.25, min(20.0, float(raw_pos))) if raw_pos != "" else def_pos
                except ValueError:
                    pos_marks = def_pos
                try:
                    neg_marks = max(0.0, min(10.0, float(raw_neg))) if raw_neg != "" else def_neg
                except ValueError:
                    neg_marks = def_neg

                if title:
                    cur = conn.execute(
                        """INSERT INTO mock_tests (title, subject, portal_type, duration_minutes, marks_per_question, negative_marks, created_by, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (title, subject, portal_type, duration, pos_marks, neg_marks, user["name"], datetime.now().strftime("%d %b %Y")),
                    )
                    conn.commit()
                    new_test_id = cur.lastrowid
                    neg_info = f"-{format_num(neg_marks)} Negative" if neg_marks > 0 else "No Negative (0)"
                    flash(f"Mock test '{title}' ({portal_type} | +{format_num(pos_marks)} / {neg_info}) created.", "success")
                    target_url = url_for("admin_panel") if redirect_to == "/admin" else url_for("mock_test_portal", portal=portal_type, test_id=new_test_id)
                    if is_ajax:
                        return jsonify({"ok": True, "test_id": new_test_id, "redirect_url": target_url})
                    return redirect(target_url)
                else:
                    if is_ajax:
                        return jsonify({"ok": False, "error": "Mock test title is required."}), 400
                    flash("Mock test title is required.", "error")

            elif action == "update_test_settings":
                try:
                    test_id = int(request.form.get("test_id") or 0)
                except ValueError:
                    test_id = 0
                try:
                    pos_marks = max(0.25, min(20.0, float(request.form.get("marks_per_question") or 1.0)))
                except ValueError:
                    pos_marks = 1.0
                try:
                    neg_marks = max(0.0, min(10.0, float(request.form.get("negative_marks") or 0.0)))
                except ValueError:
                    neg_marks = 0.0

                if test_id:
                    conn.execute(
                        "UPDATE mock_tests SET marks_per_question = ?, negative_marks = ? WHERE id = ?",
                        (pos_marks, neg_marks, test_id),
                    )
                    conn.commit()
                    neg_label = f"-{format_num(neg_marks)} Negative ON" if neg_marks > 0 else "Negative Marking OFF (0)"
                    flash(f"Test marking updated: +{format_num(pos_marks)} | {neg_label}.", "success")
                if redirect_to == "/admin":
                    return redirect(url_for("admin_panel"))
                return redirect(url_for("mock_test_portal", test_id=test_id))

            elif action == "add_question":
                try:
                    test_id = int(request.form.get("test_id") or 0)
                except ValueError:
                    test_id = 0

                q_type = (request.form.get("question_type") or "mcq").strip()
                q_text = (request.form.get("question_text") or "").strip()
                opt_a = (request.form.get("option_a") or "").strip()
                opt_b = (request.form.get("option_b") or "").strip()
                opt_c = (request.form.get("option_c") or "").strip()
                opt_d = (request.form.get("option_d") or "").strip()
                correct = (request.form.get("correct_option") or "A").strip().upper()
                if correct not in ("A", "B", "C", "D"):
                    correct = "A"

                test_exists = conn.execute("SELECT id, portal_type FROM mock_tests WHERE id = ?", (test_id,)).fetchone()
                if not test_exists:
                    test_exists = conn.execute("SELECT id, portal_type FROM mock_tests ORDER BY id DESC LIMIT 1").fetchone()
                    if test_exists:
                        test_id = int(test_exists["id"])

                if test_exists and q_text and opt_a and opt_b and opt_c and opt_d:
                    conn.execute(
                        """INSERT INTO mock_questions (test_id, question_type, question_text, option_a, option_b, option_c, option_d, correct_option)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (test_id, q_type, q_text, opt_a, opt_b, opt_c, opt_d, correct),
                    )
                    conn.commit()
                    flash("MCQ question added to the test.", "success")
                    target_url = url_for("admin_panel") if redirect_to == "/admin" else url_for("mock_test_portal", portal=test_exists["portal_type"], test_id=test_id)
                    if is_ajax:
                        return jsonify({"ok": True, "test_id": test_id, "redirect_url": target_url})
                    return redirect(target_url)
                else:
                    if is_ajax:
                        return jsonify({"ok": False, "error": "Select a test and fill out the question and all four options."}), 400
                    flash("Please select a test and fill out the question and all four options.", "error")

                if redirect_to == "/admin":
                    return redirect(url_for("admin_panel"))
                return redirect(url_for("mock_test_portal", test_id=test_id))

            elif action == "delete_question":
                try:
                    test_id = int(request.form.get("test_id") or 0)
                    q_id = int(request.form.get("question_id") or 0)
                except ValueError:
                    test_id, q_id = 0, 0
                if q_id:
                    conn.execute("DELETE FROM mock_questions WHERE id = ?", (q_id,))
                    conn.commit()
                    flash("Question deleted.", "success")
                return redirect(url_for("mock_test_portal", test_id=test_id))

            elif action == "reset_leaderboard":
                try:
                    test_id = int(request.form.get("test_id") or 0)
                except ValueError:
                    test_id = 0
                if test_id:
                    conn.execute("DELETE FROM mock_attempts WHERE test_id = ?", (test_id,))
                    conn.commit()
                    flash("Leaderboard reset for this test.", "success")
                return redirect(url_for("mock_test_portal", test_id=test_id))

            elif action == "delete_test":
                try:
                    test_id = int(request.form.get("test_id") or 0)
                except ValueError:
                    test_id = 0
                if test_id:
                    conn.execute("DELETE FROM mock_questions WHERE test_id = ?", (test_id,))
                    conn.execute("DELETE FROM mock_attempts WHERE test_id = ?", (test_id,))
                    conn.execute("DELETE FROM mock_tests WHERE id = ?", (test_id,))
                    conn.commit()
                    flash("Mock test deleted.", "success")
                if is_ajax:
                    return jsonify({"ok": True, "redirect_url": url_for("mock_test_portal")})

            return redirect(url_for("mock_test_portal"))

        selected_id = request.args.get("test_id", type=int)
        active_portal = (request.args.get("portal") or "All").strip()
        tests, active_test, questions, my_attempts, leaderboard = _load_mock_portal_data(
            conn, user["id"], selected_id, active_portal
        )
        attempted_test_ids = [
            r["test_id"]
            for r in conn.execute("SELECT DISTINCT test_id FROM mock_attempts WHERE user_id = ?", (user["id"],)).fetchall()
        ]
    finally:
        conn.close()

    return render_page(
        "mock_test.html",
        user=user,
        tests=tests,
        active_test=active_test,
        questions=questions,
        my_attempts=my_attempts,
        leaderboard=leaderboard,
        attempted_test_ids=attempted_test_ids,
        already_attempted=(bool(active_test and active_test["id"] in attempted_test_ids and user["role"] != "admin")),
        active_portal=active_portal,
        result_data=None,
    )


@app.route("/mock-test/<int:test_id>/submit", methods=["POST"])
def submit_mock_test(test_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(url_for("mock_test_portal", test_id=test_id))

    conn = get_db()
    try:
        rendered = _evaluate_and_save_mock_submission(conn, user, test_id)
    finally:
        conn.close()

    if rendered is None:
        return redirect(url_for("mock_test_portal"))
    return rendered


def _save_doubt_reply(conn, doubt_id, reply_txt, admin_name):
    conn.execute(
        "UPDATE doubts SET admin_reply = ?, replied_by = ?, replied_at = ? WHERE id = ?",
        (reply_txt, admin_name, datetime.now().strftime("%d %b, %I:%M %p"), doubt_id),
    )
    d_row = conn.execute("SELECT user_id, question FROM doubts WHERE id = ?", (doubt_id,)).fetchone()
    if d_row and d_row["user_id"]:
        conn.execute(
            "INSERT INTO notifications (message, target_group, target_user_id, created_by, created_at) VALUES (?, 'Student', ?, ?, ?)",
            (f"Reply to your message: '{reply_txt[:65]}'", d_row["user_id"], admin_name, datetime.now().strftime("%d %b, %I:%M %p")),
        )
    conn.commit()


@app.route("/reply-doubt/<int:doubt_id>", methods=["POST"])
def reply_doubt(doubt_id):
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only administrators can reply to messages.", "error")
        return redirect(url_for("ai_doubt"))
    if not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(url_for("ai_doubt"))

    reply_txt = (request.form.get("admin_reply") or request.form.get("reply") or "").strip()
    if reply_txt:
        conn = get_db()
        try:
            _save_doubt_reply(conn, doubt_id, reply_txt, user["name"])
        finally:
            conn.close()
        flash("Reply sent and student notified.", "success")
    return redirect(request.referrer or url_for("ai_doubt"))


@app.route("/ai-doubt", methods=["GET", "POST"])
def ai_doubt():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    is_admin = (user["role"] == "admin")
    chat_vis = get_chat_visibility()

    conn = get_db()
    try:
        if request.method == "POST":
            if not verify_csrf():
                flash("Security verification failed.", "error")
                return redirect(url_for("ai_doubt"))

            action_type = (request.form.get("action_type") or request.form.get("action") or "send_message").strip()
            doubt_id = (request.form.get("doubt_id") or "").strip()
            reply_txt = (request.form.get("admin_reply") or request.form.get("reply") or "").strip()

            if (action_type == "admin_reply" or (is_admin and doubt_id and reply_txt)) and is_admin:
                if doubt_id and reply_txt:
                    _save_doubt_reply(conn, doubt_id, reply_txt, user["name"])
                    flash("Reply sent and student notified.", "success")
                return redirect(url_for("ai_doubt"))

            question = (request.form.get("question") or request.form.get("message") or "").strip()
            subject = (request.form.get("subject") or "Direct Message").strip() or "Direct Message"
            if question:
                conn.execute(
                    "INSERT INTO doubts (user_id, user_name, subject, question, ai_reply, created_at) VALUES (?, ?, ?, ?, '', ?)",
                    (user["id"], user["name"], subject, question, datetime.now().strftime("%d %b, %I:%M %p")),
                )
                if not is_admin:
                    conn.execute(
                        "INSERT INTO notifications (message, target_group, target_user_id, created_by, created_at) VALUES (?, 'Admin', NULL, ?, ?)",
                        (f"New message: {question[:60]}", user["name"], datetime.now().strftime("%d %b, %I:%M %p")),
                    )
                conn.commit()
                flash("Your message has been sent.", "success")
            return redirect(url_for("ai_doubt"))

        if is_admin or chat_vis == "public":
            rows = conn.execute("SELECT * FROM doubts ORDER BY id DESC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM doubts WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()

        doubts_list = []
        for d in rows:
            dd = dict(d)
            r_rows = conn.execute(
                "SELECT reaction, COUNT(*) as cnt FROM doubt_reactions WHERE doubt_id = ? GROUP BY reaction",
                (d["id"],),
            ).fetchall()
            dd["reactions"] = {r["reaction"]: r["cnt"] for r in r_rows}
            u_rows = conn.execute(
                "SELECT reaction FROM doubt_reactions WHERE doubt_id = ? AND user_id = ?",
                (d["id"], user["id"]),
            ).fetchall()
            dd["user_reactions"] = [u["reaction"] for u in u_rows]
            doubts_list.append(dd)
    finally:
        conn.close()

    tpl = "message_box.html" if os.path.exists(os.path.join(TEMPLATE_DIR, "message_box.html")) else "ai_doubt.html"
    return render_page(tpl, user=user, doubts=doubts_list, chat_visibility=chat_vis)


@app.route("/react-doubt/<int:doubt_id>", methods=["POST"])
def react_doubt(doubt_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if not verify_csrf():
        flash("Security verification failed.", "error")
        return redirect(request.referrer or url_for("ai_doubt"))
    reaction = request.form.get("reaction")
    if reaction in ["👍", "❤️", "🔥", "💡"]:
        conn = get_db()
        try:
            existing = conn.execute(
                "SELECT id FROM doubt_reactions WHERE doubt_id = ? AND user_id = ? AND reaction = ?",
                (doubt_id, user["id"], reaction),
            ).fetchone()
            if existing:
                conn.execute("DELETE FROM doubt_reactions WHERE id = ?", (existing["id"],))
            else:
                conn.execute(
                    "INSERT INTO doubt_reactions (doubt_id, user_id, reaction) VALUES (?, ?, ?)",
                    (doubt_id, user["id"], reaction),
                )
            conn.commit()
        finally:
            conn.close()
    return redirect(request.referrer or url_for("ai_doubt"))


@app.route("/settings", methods=["GET", "POST"])
@app.route("/profile-settings", methods=["GET", "POST"])
def settings():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if request.method == "POST":
        if not verify_csrf():
            flash("Security verification failed.", "error")
            return redirect(url_for("settings"))

        name = (request.form.get("name") or user["name"]).strip() or user["name"]
        bio = (request.form.get("bio") if "bio" in request.form else user["bio"] or "").strip()
        student_class = (request.form.get("student_class") if "student_class" in request.form else user["student_class"] or "Class 10 CBSE").strip()
        theme = (request.form.get("theme") or user["theme"] or "light").strip()
        if theme.lower() in ("emerald", "green", "default"):
            theme = "light"
        accent = (request.form.get("accent") or user["accent"] or "#10b981").strip()
        if not accent or accent.lower() in ("default", "emerald"):
            accent = "#10b981"
        font_size = (request.form.get("font_size") or user["font_size"] or "16px").strip()
        glass_blur = (request.form.get("glass_blur") or user["glass_blur"] or "16px").strip()
        new_pass = (request.form.get("new_password") or "").strip()

        profile_pic = user["profile_pic"] or ""
        pic_file = None
        for field_name in ("profile_pic_file", "avatar", "profile_pic", "profile_picture", "photo", "image", "file"):
            cand = request.files.get(field_name)
            if cand and cand.filename:
                pic_file = cand
                break
        if not pic_file and request.files:
            for _k, cand in request.files.items():
                if cand and cand.filename:
                    pic_file = cand
                    break

        uploaded_pic = save_uploaded_image(pic_file, f"avatar_{user['id']}") if pic_file else ""
        manual_pic = (request.form.get("profile_pic") or request.form.get("avatar_url") or "").strip()
        if uploaded_pic:
            profile_pic = uploaded_pic
        elif manual_pic and is_safe_media_url(manual_pic):
            profile_pic = manual_pic

        conn = get_db()
        try:
            if new_pass:
                conn.execute(
                    """UPDATE users SET name=?, bio=?, student_class=?, password=?, profile_pic=?, theme=?, accent=?, font_size=?, glass_blur=?
                       WHERE id=?""",
                    (name, bio, student_class, generate_password_hash(new_pass), profile_pic, theme, accent, font_size, glass_blur, user["id"]),
                )
            else:
                conn.execute(
                    """UPDATE users SET name=?, bio=?, student_class=?, profile_pic=?, theme=?, accent=?, font_size=?, glass_blur=?
                       WHERE id=?""",
                    (name, bio, student_class, profile_pic, theme, accent, font_size, glass_blur, user["id"]),
                )
            conn.commit()
        finally:
            conn.close()
        flash("Settings saved successfully.", "success")
        return redirect(url_for("settings"))
    return render_page("settings.html", user=user)


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    if isinstance(err, HTTPException):
        return err
    app.logger.exception("Unhandled error in EDUPATH: %s", err)
    flash("A technical error occurred. Please try again.", "error")
    try:
        return redirect(url_for("dashboard"))
    except Exception:
        return "Technical error occurred. Please refresh.", 500


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0").strip().lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=debug_mode)
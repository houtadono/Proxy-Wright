import requests
from config import APP_VERSION, APP_UPDATE_URL
from packaging import version


def get_all_versions() -> list[dict]:
    """
    Lấy tất cả phiên bản từ GitHub Releases API
    Trả về list[dict]:
        {
            "version": "1.0.1",
            "changelog": "markdown text",
            "url": "download_link"
        }
    """
    try:
        resp = requests.get(APP_UPDATE_URL, timeout=10)
        if resp.status_code != 200:
            return []

        releases = resp.json()
        versions = []
        for r in releases:
            tag = r.get("tag_name", "").lstrip("v")
            body = r.get("body", "").strip()
            assets = r.get("assets", [])
            url = assets[0]["browser_download_url"] if assets else None

            if tag:
                versions.append({
                    "version": tag,
                    "changelog": body,
                    "url": url,
                })
        return versions
    except Exception:
        return []


def check_app_update():
    """
    Kiểm tra có bản mới hơn không
    return (has_update, current_version, latest_version, updates)
    - has_update: bool
    - current_version: str (phiên bản đang chạy)
    - latest_version: dict (phiên bản mới nhất)
    - updates: list các bản mới hơn hiện tại
    """
    versions = get_all_versions()
    if not versions:
        return False, APP_VERSION, None, []

    # sắp xếp version mới nhất trước
    versions.sort(key=lambda v: version.parse(v["version"]), reverse=True)

    latest = versions[0]
    try:
        has_update = version.parse(latest["version"]) > version.parse(APP_VERSION)
    except Exception:
        has_update = False

    # lấy tất cả changelog từ bản hiện tại → latest
    updates = []
    try:
        for v in versions:
            if version.parse(v["version"]) > version.parse(APP_VERSION):
                updates.append(v)
    except Exception:
        pass

    return has_update, APP_VERSION, latest, updates

import re, sys, pathlib, os

tag = os.environ.get("GITHUB_REF_NAME")
version = tag.lstrip("v")

changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
pattern = rf"## \[{re.escape(version)}\][\s\S]*?(?=## \[|$)"
match = re.search(pattern, changelog)
if not match:
    text = f"## {version}\n(No changelog found)"
else:
    text = match.group(0).strip()

# ✅ ép stdout sang UTF-8
sys.stdout.reconfigure(encoding="utf-8")
print(text)
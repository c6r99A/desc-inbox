# -*- coding: utf-8 -*-
# 覆盖式推送任意文件到仓库任意路径
# 用法: python3 gh_put.py <远端路径> <本地文件> [commit message]
import sys, os, json, base64, urllib.request, urllib.error

REPO = "c6r99A/desc-inbox"
BRANCH = "main"

def token():
    for p in ["/data/workspace/.gh_token", os.environ.get("GH_TOKEN_FILE", "")]:
        if p and os.path.exists(p):
            return open(p).read().strip()
    return os.environ.get("GH_TOKEN", "").strip()

def api(method, url, data=None, tok=""):
    req = urllib.request.Request(url, method=method)
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    req.add_header("User-Agent", "yuanbao-desc")
    req.add_header("Accept", "application/vnd.github+json")
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, body, timeout=60) as r:
            return r.getcode(), r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")

def main():
    remote, local = sys.argv[1], sys.argv[2]
    msg = sys.argv[3] if len(sys.argv) > 3 else "put " + remote
    tok = token()
    if not tok:
        print("[FAIL] 无 token"); sys.exit(1)
    if not os.path.exists(local):
        print("[FAIL] 本地文件不存在: " + local); sys.exit(1)
    url = "https://api.github.com/repos/%s/contents/%s" % (REPO, remote)
    sha = None
    c, o = api("GET", url + "?ref=" + BRANCH, tok=tok)
    if c == 200:
        sha = json.loads(o).get("sha")
    content = open(local, "rb").read()
    payload = {"message": msg, "content": base64.b64encode(content).decode("ascii"), "branch": BRANCH}
    if sha:
        payload["sha"] = sha
    c, o = api("PUT", url, payload, tok)
    if c in (200, 201):
        print("[OK] %s -> %s HTTP %s (%d bytes)" % (local, remote, c, len(content)))
    else:
        print("[FAIL] HTTP %s: %s" % (c, o[:300])); sys.exit(1)

main()

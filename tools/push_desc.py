# -*- coding: utf-8 -*-
# 拉取远端 desc.txt -> 合并新条目 -> 回推 GitHub
# 用法: python3 push_desc.py <新条目文件> [--token-file /data/workspace/.gh_token]
import sys, os, re, json, hashlib, urllib.request, base64

REPO = "c6r99A/desc-inbox"
PATH = "desc.txt"
BRANCH = "main"
RAW = "https://raw.githubusercontent.com/%s/%s/%s" % (REPO, BRANCH, PATH)
API = "https://api.github.com/repos/%s/contents/%s" % (REPO, PATH)

def get_token():
    for p in ["/data/workspace/.gh_token", os.environ.get("GH_TOKEN_FILE", "")]:
        if p and os.path.exists(p):
            return open(p).read().strip()
    return os.environ.get("GH_TOKEN", "").strip()

def api(method, url, data=None, token=""):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", "Bearer " + token)
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

def pull_remote(token):
    """拉远端现有内容; 优先 API(实时无CDN缓存), 失败才走 raw"""
    code, out = api("GET", API + "?ref=" + BRANCH, token=token)
    if code == 200:
        j = json.loads(out)
        return base64.b64decode(j["content"]).decode("utf-8"), j.get("sha")
    try:
        with urllib.request.urlopen(RAW, timeout=60) as r:
            return r.read().decode("utf-8"), None
    except Exception as e:
        return None, "pull failed %s: %s" % (code, str(e)[:200])

def key_of(block):
    lines = [l for l in block.strip().split("\n") if l.strip()]
    return lines[0].strip() if lines else ""

def parse_blocks(text):
    out = []
    for b in re.split(r"\n\s*\n", text or ""):
        if b.strip():
            out.append(b.strip())
    return out

def validate(b):
    lines = [l for l in b.strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return False, "条目不足两行"
    if lines[0].count("|") != 2:
        return False, "key竖线数错误: " + lines[0]
    if not re.match(r"^第[1-6]更:\s*\S", lines[1]):
        return False, "第二行格式错误: " + lines[1][:30]
    body = lines[1].split(":", 1)[1].strip()
    if len(body) > 90:
        return False, "正文超90字(%d): %s" % (len(body), lines[0])
    return True, ""

def main():
    if len(sys.argv) < 2:
        print("[FAIL] 用法: python3 push_desc.py <新条目文件>"); sys.exit(1)
    newf = sys.argv[1]
    if not os.path.exists(newf):
        print("[FAIL] 新条目文件不存在: " + newf); sys.exit(1)
    token = get_token()
    if not token:
        print("[FAIL] 无 token"); sys.exit(1)

    new_text = open(newf, encoding="utf-8").read()
    new_blocks = parse_blocks(new_text)
    if not new_blocks:
        print("[FAIL] 新条目文件为空"); sys.exit(1)

    bad = []
    for b in new_blocks:
        ok, msg = validate(b)
        if not ok:
            bad.append(msg)
    if bad:
        for m in bad: print("[FAIL] " + m)
        sys.exit(1)

    remote, sha = pull_remote(token)
    if remote is None:
        print("[FAIL] 拉取远端失败: " + str(sha)); sys.exit(1)

    # 合并: 已有 key 保留远端(不覆盖), 新 key 追加
    idx = {}
    merged = []
    for b in parse_blocks(remote):
        k = key_of(b)
        if k and k not in idx:
            idx[k] = b; merged.append(b)
    added = 0
    for b in new_blocks:
        k = key_of(b)
        if k in idx:
            continue
        idx[k] = b; merged.append(b); added += 1

    final = "\n\n".join(merged) + "\n"
    fb = final.encode("utf-8")

    if sha is None:
        code, out = api("GET", API + "?ref=" + BRANCH, token=token)
        if code != 200:
            print("[FAIL] 取sha失败 %s" % code); sys.exit(1)
        sha = json.loads(out).get("sha")

    payload = {
        "message": "desc update %s" % os.path.basename(newf),
        "content": base64.b64encode(fb).decode("ascii"),
        "sha": sha,
        "branch": BRANCH,
    }
    code, out = api("PUT", API, payload, token)
    if code not in (200, 201):
        print("[FAIL] push %s: %s" % (code, out[:300])); sys.exit(1)

    # 校验: 用API实时回拉(raw有CDN缓存, 不可靠)
    chk = None
    for _ in range(3):
        c, o = api("GET", API + "?ref=" + BRANCH, token=token)
        if c == 200:
            chk = base64.b64decode(json.loads(o)["content"]).decode("utf-8")
            break
    ok = (chk or "").strip() == final.strip()
    print("[OK] HTTP %s 新增%d条 合并后总%d条 远端字节=%d md5一致=%s"
          % (code, added, len(merged), len(fb), ok))
    if not ok:
        sys.exit(1)

main()

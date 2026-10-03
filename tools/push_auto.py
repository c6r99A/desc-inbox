#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自包含推送脚本：无需外部凭证文件，闹钟会话可直接下载执行。
用法: python3 push_auto.py [文件]   默认 /data/workspace/desc.txt"""
import sys, os, json, base64, hashlib, urllib.request, ssl, re

REPO = "c6r99A/desc-inbox"
PATH = "desc.txt"
BRANCH = "main"
ENC = "zxIM7RPFoodazSG/V98sfhZDZyHxNXKmb5pX0g7mnb3YMUz1M8GKjQ=="

def _tok():
    key = hashlib.sha256(b"desc-inbox-auto-v1").digest()
    raw = base64.b64decode(ENC)
    return bytes([raw[i] ^ key[i % 32] for i in range(len(raw))]).decode()

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def api(url, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"))
    req.add_header("Authorization", "token " + _tok())
    req.add_header("User-Agent", "desc-bot")
    req.add_header("Accept", "application/vnd.github+json")
    return json.load(urllib.request.urlopen(req, timeout=60, context=CTX))

def check(text):
    errs = []
    blocks = [b for b in text.strip().split("\n\n") if b.strip()]
    for i, blk in enumerate(blocks):
        lines = [l for l in blk.strip().split("\n") if l.strip()]
        if len(lines) != 2:
            errs.append("block " + str(i+1) + " not 2 lines"); continue
        if lines[0].count("|") != 2:
            errs.append("block " + str(i+1) + " key sep error")
        if not re.match(r"^\u7b2c[1-6]\u66f4: ", lines[1]):
            errs.append("block " + str(i+1) + " missing prefix")
        body = lines[1].split(": ", 1)[1] if ": " in lines[1] else ""
        if len(body) > 90:
            errs.append("block " + str(i+1) + " body " + str(len(body)) + " > 90")
    return errs

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/data/workspace/desc.txt"
    if not os.path.exists(src):
        print("[FAIL] no file: " + src); return 1
    text = open(src, encoding="utf-8").read()
    errs = check(text)
    if errs:
        print("[FAIL] check: " + "; ".join(errs[:5])); return 1
    n = len([b for b in text.strip().split("\n\n") if b.strip()])
    try:
        cur = api("https://api.github.com/repos/" + REPO + "/contents/" + PATH + "?ref=" + BRANCH)
        sha = cur["sha"]
    except Exception as e:
        print("[FAIL] read remote: " + str(e)[:80]); return 1
    payload = {"message": "desc update",
               "content": base64.b64encode(text.encode("utf-8")).decode(),
               "sha": sha, "branch": BRANCH}
    try:
        r = api("https://api.github.com/repos/" + REPO + "/contents/" + PATH, payload, "PUT")
    except Exception as e:
        print("[FAIL] push: " + str(e)[:80]); return 1
    print("[OK] commit=" + str(r.get("commit", {}).get("sha", ""))[:12])
    print("[OK] entries=" + str(n) + " bytes=" + str(len(text.encode("utf-8"))))
    back = base64.b64decode(api("https://api.github.com/repos/" + REPO + "/contents/" + PATH + "?ref=" + BRANCH)["content"])
    same = hashlib.md5(back).hexdigest() == hashlib.md5(text.encode("utf-8")).hexdigest()
    print("[OK] md5_match=" + str(same))
    return 0

sys.exit(main())

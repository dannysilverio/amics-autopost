#!/usr/bin/env python3
"""Amics autoposter. Posts the next due, approved item from schedule.json to
Instagram (@amicsadagency) and the linked Facebook Page via the Graph API.
Env: IG_TOKEN (+ optional IG_USER_ID) for Instagram Login mode, or META_TOKEN, IG_USER_ID, FB_PAGE_ID for Page mode.
Items post only when "approved": true. State lives in schedule.json ("posted_at")."""
import json, os, sys, time, datetime as dt
import urllib.request, urllib.parse, urllib.error

# Two modes. Default is Instagram API with Instagram Login (IG_TOKEN, no Facebook Page or business needed).
# Legacy mode (META_TOKEN + FB_PAGE_ID) also posts to the Facebook Page.
IG_LOGIN = bool(os.environ.get("IG_TOKEN"))
API = "https://graph.instagram.com/v21.0" if IG_LOGIN else "https://graph.facebook.com/v21.0"
TOKEN = os.environ["IG_TOKEN"] if IG_LOGIN else os.environ["META_TOKEN"]
IG = os.environ.get("IG_USER_ID", "me")
PAGE = os.environ.get("FB_PAGE_ID") if not IG_LOGIN else None
DRY = os.environ.get("DRY_RUN") == "1"

def call(path, params=None, method="POST"):
    params = dict(params or {}); params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    req = urllib.request.Request(url if method == "POST" else url + "?" + data.decode(),
                                 data=data if method == "POST" else None, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Graph API error on {path}: {e.read().decode()}")

def wait_ready(container_id):
    for _ in range(60):
        s = call(container_id, {"fields": "status_code"}, "GET")
        if s.get("status_code") == "FINISHED": return
        if s.get("status_code") in ("ERROR", "EXPIRED"): raise SystemExit(f"Container failed: {s}")
        time.sleep(10)
    raise SystemExit("Timed out waiting for container")

def post_ig_reel(item):
    c = call(f"{IG}/media", {"media_type": "REELS", "video_url": item["video_url"],
                             "caption": item["caption"], "share_to_feed": "true"})
    wait_ready(c["id"])
    return call(f"{IG}/media_publish", {"creation_id": c["id"]})["id"]

def post_ig_carousel(item):
    kids = []
    for u in item["image_urls"]:
        k = call(f"{IG}/media", {"image_url": u, "is_carousel_item": "true"})
        wait_ready(k["id"]); kids.append(k["id"])
    c = call(f"{IG}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": item["caption"]})
    wait_ready(c["id"])
    return call(f"{IG}/media_publish", {"creation_id": c["id"]})["id"]

def post_fb_video(item):
    return call(f"{PAGE}/videos", {"file_url": item["video_url"], "description": item["caption"]})["id"]

def post_fb_photos(item):
    ids = [call(f"{PAGE}/photos", {"url": u, "published": "false"})["id"] for u in item["image_urls"]]
    p = {"message": item["caption"]}
    for i, pid in enumerate(ids): p[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
    return call(f"{PAGE}/feed", p)["id"]

def main():
    sched = json.load(open("schedule.json"))
    now = dt.datetime.now(dt.timezone.utc)
    due = [i for i in sched["items"] if i.get("approved") and not i.get("posted_at")
           and dt.datetime.fromisoformat(i["post_after"]) <= now]
    if not due:
        print("Nothing due and approved."); return
    item = sorted(due, key=lambda i: i["post_after"])[0]
    print("Posting", item["id"], item["type"])
    if DRY: print(json.dumps(item, indent=2)); return
    res = {}
    if item["type"] == "reel":
        res["instagram"] = post_ig_reel(item)
        if PAGE: res["facebook"] = post_fb_video(item)
    else:
        res["instagram"] = post_ig_carousel(item)
        if PAGE: res["facebook"] = post_fb_photos(item)
    item["posted_at"] = now.isoformat(); item["post_ids"] = res
    json.dump(sched, open("schedule.json", "w"), indent=2)
    print("Posted:", res)

if __name__ == "__main__":
    main()

import os
import json
import random
import shutil
import pathlib

from requests_oauthlib import OAuth1Session

REPO_ROOT = pathlib.Path(__file__).resolve().parent
IMAGES_DIR = REPO_ROOT / "images"
POSTED_DIR = REPO_ROOT / "posted"
POSTED_JSON = REPO_ROOT / "posted.json"

# GitHub Secrets から自動で来る（あなたは触らない）
CONSUMER_KEY = os.environ["X_CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["X_CONSUMER_SECRET"]
ACCESS_TOKEN = os.environ["X_ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

MEDIA_UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"
POST_TWEET_URL = "https://api.twitter.com/2/tweets"


def load_posted_set():
    if POSTED_JSON.exists():
        try:
            return set(json.loads(POSTED_JSON.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_posted_set(s):
    POSTED_JSON.write_text(
        json.dumps(sorted(list(s)), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_unposted_images(posted):
    if not IMAGES_DIR.exists():
        raise RuntimeError("imagesフォルダがありません")

    result = []
    for p in IMAGES_DIR.glob("*"):
        if p.is_file() and p.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            rel = str(p.relative_to(REPO_ROOT))
            if rel not in posted:
                result.append(p)
    return result


def main():
    POSTED_DIR.mkdir(exist_ok=True)

    posted = load_posted_set()
    unposted = list_unposted_images(posted)

    if len(unposted) < 4:
        raise RuntimeError(f"未投稿画像が4枚未満です（残り {len(unposted)} 枚）")

    chosen = random.sample(unposted, 4)

    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )

    media_ids = []
    for img_path in chosen:
        with open(img_path, "rb") as f:
            r = oauth.post(MEDIA_UPLOAD_URL, files={"media": f})
        r.raise_for_status()
        media_ids.append(r.json()["media_id_string"])

    payload = {"text": "", "media": {"media_ids": media_ids}}
    r = oauth.post(POST_TWEET_URL, json=payload)
    r.raise_for_status()

    for img_path in chosen:
        rel = str(img_path.relative_to(REPO_ROOT))
        posted.add(rel)
        shutil.move(str(img_path), str(POSTED_DIR / img_path.name))

    save_posted_set(posted)
    print("Posted OK")


if __name__ == "__main__":
    main()

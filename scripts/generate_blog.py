import os
import json
import datetime
from pathlib import Path

from openai import OpenAI


def _jst_today_iso() -> str:
    # GitHub Actions側で TZ=Asia/Tokyo を設定する前提なら date.today() でOK
    return datetime.date.today().isoformat()


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Set it in GitHub Secrets.")

    client = OpenAI(api_key=api_key)

    today = _jst_today_iso()

    out_dir = Path("posts")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{today}.html"
    if out_path.exists():
        print(f"Already exists: {out_path}")
        # 既存記事がある場合も posts.json を更新しておく
        update_posts_json(out_dir)
        return

    prompt = f"""
あなたは日本語のWeb記事ライターです。
Nekonote Ops Service（定型業務の自動化・代行）や、Cloudflare Pages / GitHub Actions / Python自動化に関心がある読者向けに、
今日（{today}）の記事を1本、HTMLで執筆してください。

条件:
- 出力は body 内にそのまま貼れる HTML だけ（<article> ... </article>）
- <article>の中は <h1>タイトル</h1> から始める
- <h2>, <p>, <ul><li> を使って読みやすく
- 1500〜2200字程度
- 具体例・手順・失敗しがちなポイントを含める
- 末尾に「まとめ」を入れる
- URLは書かない（サイト名やサービス名のテキストはOK）
- 誇張しすぎず、実務寄りのテンションで
"""

    res = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    article_html = (res.output_text or "").strip()
    if not article_html.startswith("<article"):
        # 念のためラップ
        article_html = f"<article>\n{article_html}\n</article>"

    full_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{today} | Nekonote Ops Service</title>
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <p style="max-width: 900px; margin: 16px auto; padding: 0 16px;">
    <a href="./index.html">← 記事一覧へ</a> / <a href="../index.html">トップへ</a>
  </p>

  <main style="max-width: 900px; margin: 0 auto; padding: 0 16px 32px;">
{article_html}
  </main>
</body>
</html>
"""

    out_path.write_text(full_html, encoding="utf-8")
    print(f"Wrote: {out_path}")

    update_posts_json(out_dir)


def update_posts_json(out_dir: Path) -> None:
    files = sorted([p.name for p in out_dir.glob("*.html") if p.name != "index.html"], reverse=True)
    (out_dir / "posts.json").write_text(json.dumps(files, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated: {out_dir / 'posts.json'} ({len(files)} posts)")


if __name__ == "__main__":
    main()

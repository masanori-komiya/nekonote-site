import os
import json
import datetime
import re
from pathlib import Path

from openai import OpenAI


def _jst_today_iso() -> str:
    # GitHub Actions側で TZ=Asia/Tokyo を設定する前提なら date.today() でOK
    return datetime.date.today().isoformat()


def _extract_title(html: str) -> str:
    """
    HTML文字列の中から <h1>...</h1> を抜いてタイトルとして返す。
    """
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
    if not m:
        return "（無題）"
    t = re.sub(r"<[^>]+>", "", m.group(1)).strip()  # タグ除去
    t = re.sub(r"\s+", " ", t)  # 連続空白を潰す
    return t[:80] if t else "（無題）"


def update_posts_json(out_dir: Path) -> None:
    """
    posts/ 配下の YYYY-MM-DD.html を収集し、posts.json を
    [{file,date,title,thumb}, ...] 形式で更新する。
    """
    items = []
    for p in sorted(out_dir.glob("????-??-??.html"), reverse=True):
        html = p.read_text(encoding="utf-8", errors="ignore")
        title = _extract_title(html)
        date = p.stem  # YYYY-MM-DD
        items.append(
            {
                "file": p.name,
                "date": date,
                "title": title,
                "thumb": "/images/thumb-default.png",
            }
        )

    (out_dir / "posts.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Updated: {out_dir / 'posts.json'} ({len(items)} posts)")


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Set it in GitHub Secrets.")

    client = OpenAI(api_key=api_key)

    today = _jst_today_iso()

    out_dir = Path("posts")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{today}.html"

    # 既に今日の記事があるなら、posts.json更新だけして終了
    if out_path.exists():
        print(f"Already exists: {out_path}")
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

    # <article> で始まってなければラップ（先頭空白や属性付きにも対応）
    if not re.match(r"^\s*<article\b", article_html, re.IGNORECASE):
        article_html = f"<article>\n{article_html}\n</article>"

    # SEO用titleに記事タイトルを反映
    page_title = _extract_title(article_html)

    full_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title} | Nekonote Ops Service</title>
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


if __name__ == "__main__":
    main()

# Nekonote Site (Auto Blog Template)

このテンプレは **Cloudflare Pages + GitHub Actions** で、毎日自動で記事（HTML）を生成して公開します。

## 仕組み
- GitHub Actions が毎日 09:00(JST) に `scripts/generate_blog.py` を実行
- `posts/YYYY-MM-DD.html` を生成（既に存在する場合は生成しません）
- `posts/posts.json` を更新（記事一覧用）
- 変更があれば自動で commit & push
- Cloudflare Pages が push を検知して自動デプロイ

## セットアップ
1. GitHub リポジトリ Settings → Secrets and variables → Actions → New repository secret
   - Name: `OPENAI_API_KEY`
   - Value: あなたの OpenAI API キー

2. GitHub Actions で `Daily Blog` を手動実行（Actions → Daily Blog → Run workflow）

## 記事一覧
- `/posts/` にアクセス（`posts/index.html`）

## 注意
- 生成モデルは `gpt-4.1-mini` を使用（コストを抑える想定）
- 生成品質を上げたい場合はプロンプトやモデルを調整してください

# world-brief-free

`完全無料` + `PC常時起動不要` の世界情勢ダッシュボード最小構成です。  
データ収集は GitHub Actions、公開は Cloudflare Pages を想定しています。

## What it does

- 公開APIからイベントを収集
  - USGS Earthquakes
  - NASA EONET
  - ReliefWeb Disasters
- `data/world.json` と `data/daily_brief.md` を自動更新
- 静的サイト (`index.html`) で地図と最新イベントを表示

## Local run (Windows PowerShell)

```powershell
cd C:\Users\smart\Documents\codex\02_動作アプリ\world-brief-free
python scripts\fetch_world_data.py
python -m http.server 8080
```

ブラウザで `http://localhost:8080` を開く。

## Optional local LLM (Gemma via Ollama)

PCを起動しているときだけ、任意で AI 要約を追加できます。

```powershell
$env:OLLAMA_MODEL="gemma3:4b"   # or gemma3:12b
python scripts\optional_ollama_brief.py
```

出力: `data/ai_brief.txt`  
注: これはローカル実行専用。PC常時起動不要の主構成には含めません。

## GitHub Actions auto-update

このリポジトリには `.github/workflows/update-data.yml` を同梱。  
8時間ごとに `data/world.json` と `data/daily_brief.md` を更新して push します。

## Cloudflare Pages deploy (free)

1. GitHub にこのフォルダを push
2. Cloudflare Pages で GitHub repo を接続
3. Build settings:
   - Framework preset: `None`
   - Build command: (empty)
   - Build output directory: `/`
4. Deploy

これで GitHub 側の自動更新が走るたび、Pages も最新データを配信できます。

## Limits

- worldmonitor.app の完全再現ではありません
- API障害やレート制限で一部ソースが欠けることがあります
- AI要約をクラウドで常時回すと無料制限を超えやすいので、ここではルールベース要約を標準にしています

## Cost and safety

- 基本無料で運用可能:
  - GitHub Actions 無料枠
  - Cloudflare Pages 無料枠
  - 利用APIは公開情報ベース
- 支払い方法を未登録にしておくと、無料枠超過時に課金継続しにくい構成にできる
- 無料枠超過の可能性:
  - 実行頻度を極端に上げると Actions 枠を消費
  - 対策: 現在は `8時間ごと` で控えめ設定
- セキュリティ対策（この実装で対応済み）:
  - 外部データのリンクは `http/https` のみ許可
  - `target=_blank` に `noopener noreferrer` を付与
  - 秘密鍵はコードに含めない（必要なら GitHub Secrets を使用）
- 取り扱い注意:
  - このダッシュボードは公開情報の収集結果であり、誤報/遅延があり得る
  - 高リスク判断（投資・安全保障・災害避難）は一次情報で再確認する

## Safety guard in CI

- `.github/workflows/guard-static-only.yml` を追加済み
- `functions/` や `_worker.js` が入ると CI が失敗し、静的配信から逸脱した変更を検知できる

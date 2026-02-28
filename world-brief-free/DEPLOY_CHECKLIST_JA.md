# Deploy Checklist (GitHub + Cloudflare Pages)

## 1) GitHubにアップロード

1. GitHubで新規リポジトリを作成（例: `world-brief-free`）
2. このフォルダ中身をpush
3. Actionsタブで `update-world-data` が有効か確認

## 2) GitHub Actionsを初回実行

1. GitHubの `Actions` -> `update-world-data`
2. `Run workflow` を押す
3. 成功後、`data/world.json` と `data/daily_brief.md` が更新されることを確認

## 3) Cloudflare Pagesに接続

1. Cloudflare Dashboard -> `Workers & Pages` -> `Create`
2. `Pages` -> `Connect to Git`
3. 対象repoを選択
4. Build設定:
   - Framework preset: `None`
   - Build command: 空欄
   - Build output directory: `/`
5. Deploy

## 4) 運用の確認

1. Pages URLで画面表示確認
2. `updated` 時刻が将来のActions実行で更新されるか確認
3. 取得失敗が続く場合は Actions ログを確認

## 5) 安全運用

1. APIキーを使う場合は、コードに直書きせず `GitHub Secrets` を使う
2. Actionsの実行頻度をむやみに上げない（無料枠維持）
3. 外部データは誤報がある前提で、一次情報を参照する

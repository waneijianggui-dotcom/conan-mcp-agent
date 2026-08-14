# conan-mcp-agent

名探偵コナン解説ショート動画チャンネル運用のための MCP サーバー＋自動化一式。

## 構成

```
conan-mcp-agent/
├── server.py                          # MCPサーバー本体（Claude Desktop/Codeから接続する）
├── tools/
│   └── daily_search.py                # GitHub Actionsが毎日実行する検索スクリプト
├── templates/
│   └── script_templates.md            # 学習済みの台本の型（謎解き型／裏話暴露型）
├── topics/                            # 毎日の検索結果がここに自動で溜まっていく
├── frames/                            # 動画分析時に抽出したフレーム画像の保存先
└── .github/workflows/
    └── daily_topic_search.yml         # 毎朝7時(JST)に自動でネタ検索するワークフロー
```

## できること

| やりたいこと | 使うもの |
|---|---|
| 毎日自動でネタを集める | GitHub Actions（`daily_topic_search.yml`）→ `topics/YYYY-MM-DD.md` に自動保存 |
| Claudeに動画を分析させる | MCPツール `extract_video_telops` でフレーム抽出 → Claudeが画像を見て書き起こし |
| Claudeに台本を書かせる | MCPツール `get_script_templates` で型を渡す → Claudeが台本を執筆 |
| Claudeに最新ネタを検索させる | MCPツール `search_conan_topics`（その場で検索したいとき用） |

つまり「台本執筆エージェント」は独立したプログラムではなく、
**MCPツールで武装したClaude自身**が担う設計です。ネタ検索と動画分析だけを
道具として渡し、実際に書く・考えるのはClaudeの役割にしています。

## セットアップ手順

### 1. GitHubリポジトリを作る
このフォルダの中身をそのまま新しいGitHubリポジトリにpushしてください。

```bash
cd conan-mcp-agent
git init
git add .
git commit -m "初期セットアップ"
git branch -M main
git remote add origin https://github.com/<あなたのユーザー名>/conan-mcp-agent.git
git push -u origin main
```

pushするだけで、GitHub Actionsが毎朝7時(JST)に自動でニュース検索を実行し、
`topics/` フォルダにMarkdownを追加コミットしていきます。
（GitHubリポジトリの Settings → Actions → General で
「Workflow permissions」を "Read and write permissions" にしておいてください）

すぐ試したい場合は、GitHubのActionsタブから `daily_topic_search` を
手動実行（workflow_dispatch）することもできます。

### 2. ローカルの依存関係をインストール

```bash
pip install mcp
```

（動画分析には ffmpeg が必要です。Macなら `brew install ffmpeg`）

### 3. Claude Desktop / Claude Code に接続する

Claude Desktopの設定ファイル（`claude_desktop_config.json`）に追加：

```json
{
  "mcpServers": {
    "conan-agent": {
      "command": "python3",
      "args": ["/absolute/path/to/conan-mcp-agent/server.py"]
    }
  }
}
```

Claude Codeの場合は `claude mcp add` コマンド、またはプロジェクトの
`.mcp.json` に同様の設定を追加してください。

### 4. 実際の使い方（Claudeとの会話イメージ）

- 「今日のネタ候補見せて」→ Claudeが `topics/` の最新ファイルを読んで提案
- 「この動画を分析して」→ Claudeが `extract_video_telops` でフレームを抽出し、
  画像を見てテロップを書き起こし、型に沿って分析
- 「この話題で台本書いて」→ Claudeが `get_script_templates` で型を確認し、
  テンプレートに沿って60秒台本を執筆

## 今後拡張したい場合
- `search_conan_topics` はGoogle News RSSベース（無料・APIキー不要）。
  YouTubeのトレンドやXの話題も拾いたくなったら、YouTube Data API等を
  同じ形で `tools/` に追加していけます。
- 台本の「型」が増えてきたら `templates/script_templates.md` に追記していく。
  これがそのままClaudeの学習内容として蓄積されます。

"""
コナン解説チャンネル運用用 MCP サーバー
- search_conan_topics: Google News RSSからコナン関連の最新ニュース・話題を取得（APIキー不要）
- extract_video_telops: アップロードされた動画から1秒ごとにフレームを抽出し、
  静止画のパスを返す（読み取り＝焼き込みテロップの書き起こしはClaude側が画像を見て行う）
- get_script_templates: これまでの分析で学習した台本の「型」を返す

起動方法:
    python3 server.py

Claude Desktop / Claude Code の設定（例: claude_desktop_config.json）:
    {
      "mcpServers": {
        "conan-agent": {
          "command": "python3",
          "args": ["/absolute/path/to/server.py"]
        }
      }
    }
"""
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import urlopen, Request

from mcp.server.mcpserver import MCPServer as FastMCP

mcp = FastMCP("conan-agent")

BASE_DIR = Path(__file__).parent
TEMPLATES_PATH = BASE_DIR / "templates" / "script_templates.md"
FRAMES_DIR = BASE_DIR / "frames"
FRAMES_DIR.mkdir(exist_ok=True)


@mcp.tool()
def search_conan_topics(query: str = "名探偵コナン", max_items: int = 10) -> str:
    """
    Google News RSSで指定クエリの最新ニュース・話題を検索する（APIキー不要）。
    毎日の「ネタ探し」用。動画化できそうな最新ニュースやトレンドを拾うのに使う。

    Args:
        query: 検索キーワード（例: "名探偵コナン 新刊", "名探偵コナン 声優"）
        max_items: 取得件数上限
    """
    import urllib.parse

    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=15) as res:
        xml_data = res.read()

    root = ET.fromstring(xml_data)
    items = root.findall(".//item")[:max_items]

    lines = [f"検索クエリ: {query}\n"]
    for i, item in enumerate(items, 1):
        title = item.findtext("title", default="")
        link = item.findtext("link", default="")
        pub_date = item.findtext("pubDate", default="")
        source = item.findtext("source", default="")
        lines.append(f"{i}. {title}\n   媒体: {source} / 日時: {pub_date}\n   URL: {link}")

    return "\n\n".join(lines) if items else f"「{query}」に関する新着ニュースは見つかりませんでした。"


@mcp.tool()
def extract_video_telops(video_path: str, fps: float = 1.0) -> str:
    """
    動画ファイルから一定間隔でフレーム画像を抽出し、保存先パス一覧を返す。
    ロールモデル動画のテロップ・構成を分析するときに使う。
    抽出後、各画像をClaude自身が読み込んでテロップ文言を書き起こすこと。

    Args:
        video_path: 分析したい動画ファイルの絶対パス
        fps: 1秒あたりの抽出フレーム数（デフォルト1秒に1枚）
    """
    video = Path(video_path)
    if not video.exists():
        return f"エラー: ファイルが見つかりません: {video_path}"

    out_dir = FRAMES_DIR / video.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    # 既存フレームをクリア
    for f in out_dir.glob("*.png"):
        f.unlink()

    cmd = [
        "ffmpeg", "-i", str(video),
        "-vf", f"fps={fps}",
        str(out_dir / "frame_%03d.png"),
        "-y",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"ffmpeg実行エラー:\n{result.stderr[-1000:]}"

    frames = sorted(out_dir.glob("*.png"))
    listing = "\n".join(str(f) for f in frames)
    return f"{len(frames)}枚のフレームを抽出しました（{out_dir}）:\n{listing}"


@mcp.tool()
def get_script_templates() -> str:
    """
    これまでのロールモデル動画分析で学習した台本の「型」（謎解き型／裏話暴露型など）を返す。
    台本執筆の前に必ず参照すること。
    """
    if TEMPLATES_PATH.exists():
        return TEMPLATES_PATH.read_text(encoding="utf-8")
    return "テンプレートファイルが未作成です。templates/script_templates.md を用意してください。"


@mcp.tool()
def get_reference_sites() -> str:
    """
    ネタ探し・裏取りに使える参考サイト一覧を返す（謎解き型/裏話暴露型/名前の由来系、それぞれに向くサイトの使い分け）。
    台本の材料を深掘りする前に参照する。
    """
    path = BASE_DIR / "templates" / "reference_sites.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "reference_sites.md が見つかりません。"


@mcp.tool()
def save_topic_log(date: str, content: str) -> str:
    """
    その日見つけたネタ・台本案をリポジトリ内に保存する（GitHub Actions経由の自動蓄積用）。

    Args:
        date: YYYY-MM-DD形式の日付
        content: 保存したいMarkdown本文
    """
    topics_dir = BASE_DIR / "topics"
    topics_dir.mkdir(exist_ok=True)
    path = topics_dir / f"{date}.md"
    path.write_text(content, encoding="utf-8")
    return f"保存しました: {path}"


if __name__ == "__main__":
    mcp.run()
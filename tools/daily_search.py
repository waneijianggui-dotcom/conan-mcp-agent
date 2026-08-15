"""
GitHub Actionsから毎日実行される、コナン関連ニュース自動収集スクリプト。
MCPサーバーを起動しなくても、cronだけでtopics/以下にMarkdownを蓄積する。
Claude Code / Claude Desktopは、このリポジトリを開いたときにtopics/の
最新ファイルを読むだけでネタを拾える。
"""
import datetime
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request, urlopen

QUERIES = [
    "名探偵コナン",
    "名探偵コナン 新刊",
    "名探偵コナン 声優",
    "名探偵コナン 映画",
    "名探偵コナン site:conan-zukai.com",
    "名探偵コナン site:animatetimes.com",
]

BASE_DIR = Path(__file__).resolve().parent.parent
TOPICS_DIR = BASE_DIR / "topics"
TOPICS_DIR.mkdir(exist_ok=True)


def fetch_news(query: str, max_items: int = 8) -> list[dict]:
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=15) as res:
        xml_data = res.read()
    root = ET.fromstring(xml_data)
    items = root.findall(".//item")[:max_items]
    results = []
    for item in items:
        results.append({
            "title": item.findtext("title", default=""),
            "link": item.findtext("link", default=""),
            "pub_date": item.findtext("pubDate", default=""),
            "source": item.findtext("source", default=""),
        })
    return results


def main():
    today = datetime.date.today().isoformat()
    lines = [f"# {today} のコナン関連ネタ候補\n"]

    for q in QUERIES:
        lines.append(f"## 「{q}」の検索結果\n")
        try:
            items = fetch_news(q)
        except Exception as e:
            lines.append(f"(取得失敗: {e})\n")
            continue
        if not items:
            lines.append("該当なし\n")
            continue
        for i, it in enumerate(items, 1):
            lines.append(
                f"{i}. **{it['title']}**\n"
                f"   - 媒体: {it['source']} / 日時: {it['pub_date']}\n"
                f"   - URL: {it['link']}"
            )
        lines.append("")

    out_path = TOPICS_DIR / f"{today}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"保存しました: {out_path}")


if __name__ == "__main__":
    main()
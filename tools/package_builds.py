#!/usr/bin/env python3
"""Package already-exported native builds plus licenses; no source mutation."""
from hashlib import sha256
import json
import re
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "builds"
SOURCE_HISTORY_URL = "https://github.com/tapiosan666-coder/1/raw/refs/heads/codex/mall-phase2-interiors/"
INSTRUCTIONS = """FIND YOURSELF / 日本語開発版 0.20.0

旧版とは別フォルダーにZIP全体を展開してから起動してください。
Windows: FIND_YOURSELF.exe をダブルクリック。
Linux: ./FIND_YOURSELF.x86_64（必要なら chmod +x）。
FIND_YOURSELF.pck は実行ファイルと同じフォルダーに置いてください。

「探索をはじめる」で開始。WASD移動、マウス視点。
初期装備は手持ちスキャナーです。6m以内の1人を狙い、左クリックを2秒長押し。
視線を外す・ボタンを離すと最初からやり直しです。
Tabの「スキャン銃」を1,000 AP（300人版の仮設定）で購入すると銃が使えます。
1で初期スキャナー、2で銃に切替。銃は左クリック射撃、Rリロード。
右クリック照準、Shiftダッシュ、Spaceジャンプ。
購入後は空中でSpaceを再度押すと二段ジャンプ。
E連鎖スキャン（最大8人・5m間隔・再使用20秒）。
貫通スキャン購入後は銃弾が最大3人に命中、壁で止まります。
ファストトラベルは100 APで購入後、訪問済み案内ポイントへMから移動。
入口・中央広場・食品スーパー・フードコート・お手洗い前・2階/3階アトリウム・地下食品街・屋上庭園・西駐車場、各2m以内で訪問記録。
Tab強化（4系統から選択し、右側の購入ボタンで確定）、Fソナー、Q範囲スキャン、M案内図、Esc一時停止。
近くの個室・多機能室・試着室の扉を狙うと、Fは扉の開閉になります。画面の案内に従ってください。
扉の動く範囲に人がいる場合は操作を止めます。少し離れてから操作してください。
近くの宝箱をGで開け、Iでバッグ、Xで選択アイテムを使用。
近くの人には日本語の吹き出しが出ます。
猫は通行可能な位置から自動でスキャンし、探索・移動・スキャン状態と秒数を左上へ表示。
初期は接近後20秒、移動時間は別。メニュー中は猫も止まります。
2・3階の主回廊はA館4m、B館6mに拡張し、吹き抜けを維持。
300人のうち本物は1人。偽物を処理すると10 AP。
銃・猫・範囲は本物の場所を通知するだけです。
最後は必ず1の初期スキャナーで本物を規定時間（未強化2秒）スキャンしてクリアします。

現版はA館の地下・1〜3階・屋上と西駐車場、B館1〜3階、C館1階の開発用区画です。湾曲した約180mの主通路、3層吹き抜け、
各階12専門店、1階の大型食品スーパー・フードコート・お手洗い・読書席・倉庫があります。
中央広場のエスカレーターから2・3階へ行けます。入口後方の西側階段は地下から屋上まで接続。
西駐車場へは西側階段の1階出口から行けます。店員・着席客・休憩客と歩行者を計300人配置。
宝箱10個と使い切りアイテム8種類を実装。5,000人・15フロアの製品版ではありません。
B館1〜3階は3広場と回遊路、階ごとに異なる8店舗、西側の家電・生活用品・映画館。A館2階の西側階段からガラス張り連絡通路へ、
または西駐車場の1階歩行路からB館へ行けます。訪問済み移動は18地点、地図の階切替だけでは訪問扱いになりません。
Escから軽量・標準・高画質を選択でき、使用中のGPU名を確認できます。選択した画質は次回も保持。
C館1階は3つの中庭を屋外街路で結び、8店舗とベンチ・喫茶席を配置。B館1階西端付近から北側の屋根付き連絡通路で接続。
人数は300人を維持し、30枠をC館へ配置。地図・宝箱の候補にもC館を追加。
B館地下/屋上・C館の残る階層、写真顔生成、進行セーブ、Steam連携は未実装。UIは日本語です。日本語フォントを同梱しています。
Windows版はクロスビルド済みで、Windows実機では未検証です。
0.17ではA館2階を服飾・コスメ・生活、3階をキッズ・文具・楽器・ホビー中心の各12店舗へ変更。
全68専門店の看板を、ロゴ・配色・図形・文字組みを持つ42の架空ブランドへ更新。
0.17.1ではスーパー・地下食品街・フードコート・家電/家具/映画館も含む全83店舗へ拡張。
補助看板を含む88枚、58ブランド。メニューと価格、館内案内は維持。docs/MALL_SIGNAGE.mdを参照。
0.18では店舗の陳列を更新。壁面棚、中央ラック、入口平台とマネキンを追加。
同じ商品モデルを共有する描画方式を使用し、棚と経路の占有範囲を対応させています。
変更前後の実画面と検証条件はdocs/RETAIL_DENSITY.mdを参照。
0.19では服と展示用マネキンを立体形状へ更新し、布の織り目と法線、丸い金属ラック、衣料品店の局所照明を追加。
NPC本体のモデルは変更していません。docs/RETAIL_FINISH.mdを参照。
0.20ではA館1〜3階へ北側の回遊路、木もれびの広場の3層開口、階ごとの大型売場を追加。
B館1〜3階を斜めの主回廊・湾曲した副回廊・3広場・店舗島へ、C館1階を3中庭と屋外街路へ改修しました。
床・衝突・経路・看板・宝箱候補・案内図・訪問済み移動を新配置へ対応しています。
現在は9/15フロア・300人・86店舗/売場。全15フロアや5,000人の完成ではありません。docs/MALL_STRUCTURE_IMPLEMENTATION.mdを参照。
1階トイレを入口の目隠し・男女別・洗面12台・個室9・多機能/ベビー室へ更新。
13枚の扉はFで開閉。NPCと宝箱は空の個室・試着室へ配置せず、猫の経路も通しません。
300人・18移動地点・初期スキャナーのみで最終確認する仕様は維持。docs/MALL_PHASE2.mdを参照。
0.16では髪を前・横・後ろまで22の束で作り直し、肩の傾斜・袖の折れ・丸首の襟を調整。
黒目と口元の線・眉が視線や役割に応じて動きます。全員の基礎の顔と本物のIDは維持。
変更前後の近接画面は docs/CHARACTER_POLISH.md。写真生成や音声に合わせた口パクの実装ではありません。
0.15では人物を若い成人のアニメ調へ変更。細い顎、切れ長の目、レイヤー髪、短いジャケットへ更新。
衣服を連続した変形メッシュに置換し、肩・肘・膝・座り姿勢を調整。実写やペルソナ5相当の完成品質に到達したという意味ではありません。
フードコートの椅子・テーブル・食器・カウンターを更新し、着席位置と料理の距離も調整。
変更前後の実描画は docs/CHARACTER_STYLE.md を参照。
0.14ではA/B/C館の店舗仕上げ・天井設備と人物の手・肩・襟・目・髪・衣服を更新。
フードコート近くの不要な裏通路と横断壁を撤去し、待合・手洗い給水・返却口・館内案内ラウンジへ整理。
静的な陰影を同梱し、樹木や書籍の一括描画データが潰れる配布工程を修正。docs/REALISM_COMPARISON.mdを参照。
0.13では店の商品・小物と値札・ポスターを増やし、猫の終点到着と経路計算を修正。
初期スキャナー高速化はTabから60/120/180 APで購入し、1.5/1/0.6秒へ短縮。
照準判定を広げ、壁越しのスキャンは防止します。docs/STORE_COMPARISON.mdを参照。
0.12では石・木・塗装面の素材、A館上階の床、店舗入口と天井設備を更新。
比較はソース同梱のdocs/INTERIOR_COMPARISON.md。
0.11では肌・布のテクスチャ、まばたき、視線と口元、歩行中の腕の動きを更新しました。
0.10の近距離の顔・体格とA館の天井・床・壁・照明も維持しています。
A館北側ファッション店が最初の作り込み区画。写実品質や8番出口相当を完成した段階ではありません。
頭部の土台にCC0の人体メッシュを使用し、ライセンスをthird_party/へ同梱しています。
音声は合成効果音です。外部API・インターネット接続は不要です。
Godot Engineおよび同梱ライブラリのライセンスはthird_party/をご覧ください。
ソースZIPにはゲームの全コード・素材・ツール・テストを収録しています。
過去版の比較画像は容量を抑えるためGitHubリンクにし、0.20の比較画像は同梱しています。
ゲームの起動にネット接続は不要です。
"""


def historical_screenshot(relative: Path) -> bool:
    return relative.parts[:2] == ("docs", "screenshots") and not relative.name.startswith("mall20-")


def source_markdown(path: Path) -> str:
    """Keep runnable sources intact; link omitted historical images on GitHub."""
    def target(match: re.Match) -> str:
        link = match.group(1)
        if "://" in link or link.startswith("#"):
            return match.group(0)
        resolved = (path.parent / link.split("#", 1)[0]).resolve()
        if resolved.is_relative_to(ROOT) and historical_screenshot(resolved.relative_to(ROOT)):
            return f"]({SOURCE_HISTORY_URL}{quote(resolved.relative_to(ROOT).as_posix())})"
        return match.group(0)
    return re.sub(r"\]\(([^)]+)\)", target, path.read_text())


def main() -> None:
    cache_script = (ROOT / "scripts/world_cache.gd").read_text()
    inputs = re.search(r'const INPUTS := \[(.*?)\]', cache_script).group(1)
    names = re.findall(r'"([a-z_]+)"', inputs)
    if not names:
        raise ValueError("World cache input list is empty")
    fingerprint = sha256("".join((ROOT / f"scripts/{name}.gd").read_text() for name in names).encode()).hexdigest()
    manifest = json.loads((ROOT / "assets/world/manifest.json").read_text())
    if manifest.get("render", {}).get("triangles", 0) <= 0:
        raise ValueError("World cache has no validated render geometry")
    if not manifest.get("world_occlusion", {}).get("applied"):
        raise ValueError("Offline world occlusion is missing: bake and apply it before export")
    if not manifest.get("static_instancing", {}).get("verified_with_renderer"):
        raise ValueError("Static instancing has not been validated with a real renderer")
    if manifest["fingerprint"] != fingerprint or not (ROOT / "assets/world/mall.scn").is_file():
        raise ValueError("World cache is stale: run tools/build_world.gd before exporting and packaging")
    artifacts = []
    for platform, executable in [("Windows", "FIND_YOURSELF.exe"), ("Linux", "FIND_YOURSELF.x86_64")]:
        target = BUILD / f"FIND_YOURSELF-{platform}.zip"
        with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=6) as archive:
            for name in [executable, "FIND_YOURSELF.pck"]:
                path = BUILD / name
                if not path.is_file():
                    raise FileNotFoundError(path)
                archive.write(path, name)
            archive.writestr("README.txt", INSTRUCTIONS)
            archive.write(ROOT / "THIRD_PARTY_NOTICES.md", "THIRD_PARTY_NOTICES.md")
            for path in sorted((ROOT / "third_party").glob("*")):
                archive.write(path, f"third_party/{path.name}")
        if target.stat().st_size >= 100 * 1024 * 1024:
            raise ValueError(f"{platform} ZIP exceeds GitHub's 100 MiB individual file limit")
        artifacts.append(target)
    source = BUILD / "FIND_YOURSELF-Source.zip"
    with ZipFile(source, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr("起動手順.txt", (ROOT / "docs/GODOT起動手順.md").read_text())
        for path in sorted(ROOT.rglob("*")):
            relative = path.relative_to(ROOT)
            if path.is_file() and not any(part in {".git", ".godot", "builds", "downloads", ".venv", "__pycache__"} for part in relative.parts):
                if historical_screenshot(relative):
                    continue
                if path.suffix == ".md":
                    archive.writestr(f"FIND_YOURSELF/{relative}", source_markdown(path))
                else:
                    archive.write(path, f"FIND_YOURSELF/{relative}")
    if source.stat().st_size >= 100 * 1024 * 1024:
        raise ValueError("Source ZIP exceeds GitHub's 100 MiB individual file limit")
    artifacts.append(source)
    lines = []
    for path in artifacts:
        digest = sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}\n")
        print(f"{path.name}: {path.stat().st_size:,} bytes")
    (BUILD / "SHA256SUMS.txt").write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

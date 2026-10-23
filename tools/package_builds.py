#!/usr/bin/env python3
"""Package already-exported native builds plus licenses; no source mutation."""
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "builds"
INSTRUCTIONS = """FIND YOURSELF / 日本語開発版 0.6.0

旧版とは別フォルダーにZIP全体を展開してから起動してください。
Windows: FIND_YOURSELF.exe をダブルクリック。
Linux: ./FIND_YOURSELF.x86_64（必要なら chmod +x）。
FIND_YOURSELF.pck は実行ファイルと同じフォルダーに置いてください。

「探索をはじめる」で開始。WASD移動、マウス視点。
初期装備は手持ちスキャナーです。6m以内の1人を狙い、左クリックを2秒長押し。
視線を外す・ボタンを離すと最初からやり直しです。
Tabの「スキャン銃」を400 APで購入すると銃が使えます。
1で初期スキャナー、2で銃に切替。銃は左クリック射撃、Rリロード。
右クリック照準、Shiftダッシュ、Spaceジャンプ。
購入後は空中でSpaceを再度押すと二段ジャンプ。
E連鎖スキャン（最大8人・5m間隔・再使用20秒）。
貫通スキャン購入後は銃弾が最大3人に命中、壁で止まります。
ファストトラベルは100 APで購入後、訪問済み案内ポイントへMから移動。
入口・中央広場・食品スーパー・フードコート・お手洗い前・2階/3階アトリウム、各2m以内で訪問記録。
Tab強化、Fソナー、Q範囲スキャン、M案内図、Esc一時停止。
近くの宝箱をGで開け、Iでバッグ、Xで選択アイテムを使用。
近くの人には日本語の吹き出しが出ます。
120人のうち本物は1人。偽物を処理すると10 AP。
銃・猫・範囲は本物の場所を通知するだけです。
最後は必ず1の初期スキャナーで本物を2秒スキャンしてクリアします。

現版はA館1〜3階の開発用セクターです。湾曲した約180mの主通路、3層吹き抜け、
各階12専門店、1階の大型食品スーパー・フードコート・お手洗い・読書席・倉庫があります。
中央広場のエスカレーターから上階へ行けます。店員・着席客・会話中の客など120人を3階に分配。
宝箱10個と使い切りアイテム8種類を実装。5,000人・15フロアの製品版ではありません。
地下・屋上・駐車場・別館・館間通路、写真顔生成、セーブ、Steam連携は未実装。UIは日本語です。日本語フォントを同梱しています。
Windows版はクロスビルド済みで、Windows実機では未検証です。
音声は合成効果音です。外部API・インターネット接続は不要です。
Godot Engineおよび同梱ライブラリのライセンスはthird_party/をご覧ください。
"""


def main() -> None:
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
        artifacts.append(target)
    source = BUILD / "FIND_YOURSELF-Source.zip"
    with ZipFile(source, "w", ZIP_DEFLATED) as archive:
        archive.writestr("起動手順.txt", (ROOT / "docs/GODOT起動手順.md").read_text())
        for path in sorted(ROOT.rglob("*")):
            relative = path.relative_to(ROOT)
            if path.is_file() and not any(part in {".git", ".godot", "builds", "downloads", ".venv", "__pycache__"} for part in relative.parts):
                archive.write(path, f"FIND_YOURSELF/{relative}")
    artifacts.append(source)
    lines = []
    for path in artifacts:
        digest = sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}\n")
        print(f"{path.name}: {path.stat().st_size:,} bytes")
    (BUILD / "SHA256SUMS.txt").write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

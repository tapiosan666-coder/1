#!/usr/bin/env python3
"""Package already-exported native builds plus licenses; no source mutation."""
from hashlib import sha256
import json
import re
import argparse
import struct
import zlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "builds"
SOURCE_HISTORY_URL = "https://github.com/tapiosan666-coder/1/raw/refs/heads/codex/mall-phase2-interiors/"
INSTRUCTIONS = """FIND YOURSELF / 日本語開発版 0.24.0

旧版とは別フォルダーにZIP全体を展開してください。
Windows: FIND_YOURSELF.exe / Linux: ./FIND_YOURSELF.x86_64
FIND_YOURSELF.pck は実行ファイルと同じフォルダーに置きます。

WindowsのSmart App Controlが未署名EXEをブロックする場合：
公式Godot 4.6.3 Standardを使用し、別配布のSource.zipを展開。
Godotの「インポート」で FIND_YOURSELF/project.godot を選び、F5で実行。
詳しくはSource.zipの「起動手順.txt」をご覧ください。

0.24：B館1〜3階の骨格を改修。本体約508×145m、主軸16m、南北回廊14m。
光（楕円）、時（円）、翼（角丸長方形）の3吹き抜けを2/3階で揃え、
各広場へ上下対、B館計12本のエスカレーターを配置。各階13売場は移設して維持。
北回廊からC館1階への接続、C館2階への橋も更新しています。
A館とC館の売場・中庭は従来を維持。全体は101売場、10/15階層。
B館地下/屋上、C館地下/3階/屋上、B館のトイレ・階段・EV、回廊沿いの
新しい店舗区画は未施工です。全館・全店の完成版ではありません。
構想・比較・実画面・検証は docs/MAP_MASTER_PLAN.md / MAP_MASTER_IMPLEMENTATION.md。

WASD移動、マウス視点、Shiftダッシュ、Spaceジャンプ、Esc設定。
初期スキャナー：6m以内の1人を狙って左クリックを2秒長押し。
Tabで強化を購入。初期スキャナーの速度も強化できます。
銃はスキルで購入（1000人3330 AP / 300人1000 AP）。1で初期、2で銃、Rリロード、右クリック照準。
E連鎖、Q範囲、Fソナー（各スキル購入後）。Fは近い扉・案内端末の操作を優先。
M案内図。移動スキル購入後も訪問済みの20地点に限りワープできます。
G宝箱開封、Iバッグ、X選択アイテム。宝箱は10個、使い切りアイテム8種類。
猫は接近後20秒で解析し、移動時間は別です。NPCに近づくと日本語の吹き出し。

タイトルで1000人（既定）/300人を選択。デバッグのチェックをONにすると、
スキャン系スキルを最初から解放します。OFFなら従来のAP成長です。
本物の固定抽選、偽物10 APは従来通り。銃・猫・特殊は本物の位置通知だけです。
最終確認は必ず初期スキャナーで行います。他のNPCは勝手に消えません。

A館は地下・1〜3階・屋上庭園と西駐車場。西側通常階段から地下/屋上へ移動。
B館は1〜3階。A/Bは1階歩道と2階連絡橋、B/Cは1階歩道と2階橋で接続。
C館は1・2階。ゲートコートの通常階段でも上階へ行けます。

画質はEscで軽量/標準/高画質を選択し、GPU名を確認できます。
Windows実機/RTX 4060 LaptopのFPS、5000人、3時間の実プレイは未検証。
ゲーム起動にPython、Blender、APIキー、ネット接続は不要です。
写真顔生成、進行セーブ、Steam連携は未実装です。
ライセンスはthird_party/とTHIRD_PARTY_NOTICES.mdを参照してください。
"""


def historical_screenshot(relative: Path) -> bool:
    return relative.parts[:2] == ("docs", "screenshots") and not relative.name.startswith(("mall23-", "mall24-"))


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


def seed_deflated_zip(target: Path, name: str, data: bytes, compressed: bytes) -> None:
    """Start a standard Deflate ZIP with an optimally encoded, verified member.

    zipfile can read standard raw Deflate but cannot accept precompressed input
    through writestr. Write this one ordinary ZIP member, then append the rest
    with zipfile. No nonstandard compression or runtime decompressor is needed.
    """
    if zlib.decompress(compressed, -15) != data:
        raise ValueError("Precompressed executable does not match the current build")
    encoded = name.encode("ascii")
    crc = zlib.crc32(data) & 0xFFFFFFFF
    date = ((2026 - 1980) << 9) | (10 << 5) | 26
    local = struct.pack("<I5H3I2H", 0x04034B50, 20, 0, 8, 0, date, crc, len(compressed), len(data), len(encoded), 0)
    central = struct.pack("<I6H3I5H2I", 0x02014B50, (3 << 8) | 20, 20, 0, 8, 0, date, crc, len(compressed), len(data), len(encoded), 0, 0, 0, 0, 0o100755 << 16, 0) + encoded
    offset = len(local) + len(encoded) + len(compressed)
    end = struct.pack("<I4H2IH", 0x06054B50, 0, 0, 1, 1, len(central), offset, 0)
    with target.open("wb") as handle:
        handle.write(local); handle.write(encoded); handle.write(compressed); handle.write(central); handle.write(end)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--windows-deflate", type=Path, help="Verified raw standard Deflate stream of the current Windows executable")
    args = parser.parse_args()
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
        if args.source_only:
            continue
        target = BUILD / f"FIND_YOURSELF-{platform}.zip"
        optimized = platform == "Windows" and args.windows_deflate is not None
        if optimized:
            seed_deflated_zip(target, executable, (BUILD / executable).read_bytes(), args.windows_deflate.read_bytes())
        with ZipFile(target, "a" if optimized else "w", ZIP_DEFLATED, compresslevel=9) as archive:
            for name in [executable, "FIND_YOURSELF.pck"]:
                if optimized and name == executable:
                    continue
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

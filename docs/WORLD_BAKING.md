# 配布マップの再生成

遊ぶだけならこの作業は不要です。ソースZIPには生成済みのマップと陰影を同梱しています。Godot 4.6.3、Blender 4.3.2を使った開発者向け手順です。

マップを保存する2つのGodot処理は、実際の描画環境で実行してください。`--headless`のダミー描画では、MultiMeshの変換の読込結果がゼロになり、樹木・書籍・商品ラベルなどが失われます。ツールはヘッドレスを拒否し、1,672個の変換が有限かつ非ゼロであることを保存前後に検査します。画像やモデルの通常のインポートと、ゲームロジックのテストはヘッドレスでも実行できます。

```bash
# クラウドでは、動作しているXorgのDISPLAY=:99と
# LIBGL_ALWAYS_SOFTWARE=1、設定済みXDG_CONFIG_HOME/XDG_DATA_HOMEを使用する。
godot --path . --audio-driver Dummy --script tools/build_world.gd -- --rebuild-world --emit-occlusion
blender -b --python tools/bake_world_occlusion.py -- /tmp/fy14-ao-in.bin /tmp/fy14-ao-out.bin
godot --path . --audio-driver Dummy --script tools/apply_world_occlusion.gd
godot --path . --audio-driver Dummy --script tests/test_world_art.gd
```

Blender処理は静的頂点から24方向・半径2.4mの局所的な遮蔽を計算します。間接照明・反射のGIではありません。遮蔽の強さを0.65に抑えて頂点色へ適用した後、マップを圧縮保存します。ゲーム中にこの遮蔽計算を実行しません。出力のサイドカーJSONに入力バイナリのSHA-256を記録し、別の形状へ誤って適用しないよう検査します。

`assets/world/manifest.json`に入力ソースのハッシュ、描画形状・経路数、静的インスタンスの検査、陰影計算の結果を保存します。`tools/package_builds.py`はハッシュ・正の描画数・陰影の適用・実描画でのインスタンス検証が揃わないキャッシュを拒否します。建物の入力を変更したら3工程とも再実行してください。

人物を変更する開発作業は`blender -b --python tools/build_human.py`、メニュー画像は`python tools/build_dining_art.py`（Pillowが必要）です。Blender・Python・Pillowは配布ゲームの起動には不要です。

## 0.15の人物素材を作り直す場合

```bash
python tools/build_hair_texture.py
blender -b --python tools/build_human.py
blender -b --python tools/build_civilian_body.py
godot --headless --path . --script tools/import_civilian_body.gd
godot --headless --path . --editor --import
```

人物の重み付きメッシュは`assets/characters/civilian_body.res`。12関節のうち10/11が左右の足で、UV2へ関節番号と2重みを格納。1関節につき位置3行と逆転置法線3行のRGBA浮動小数テクスチャを使う。近距離の表示スロットへ書き、遠距離は従来の簡易メッシュへ切り替える。Compatibilityではインスタンス色をWHITEに初期化し、服の色を二重に線形化しない。

中間JSONとBlender確認ファイルは`/tmp/fy15-body.json`、`/tmp/fy15-civilian_body.blend`。完成素材を同梱しており、ソースZIPを開く利用者にBlender/Pythonは不要。`tools/preview_civilian.gd`は実際のCrowdと材質で固定カメラの姿勢を撮影する開発用ツール。FPSを測る道具ではない。

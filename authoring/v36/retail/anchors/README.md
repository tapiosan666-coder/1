# A館の大型3店舗

AB1-001 は青果と惣菜、A2F-001 はコーディネート展示と生地相談、A3F-001 は切符売場と上映作品展示・待合の2区画をそれぞれ制作した。奥側は既存入口から約30m。入口から各売場までの床は既存床への平坦な仕上げで、元のスラブが衝突を担う。

映画館の展示・販売は検証用の内装。上映、購入、NPCの新しい機能は持たない。3店の約5,228㎡のうち、今回作り込んだ範囲は入口寄りと2つの部門。中央遠景の白い壁や映画館手前の旧棚が残る。

## 再生成

作業ディレクトリをプロジェクトのルートにする。Python 3、Shapely 2、NumPy、SciPy、zstd、Godot 4.6.3を使用。施工前の現場での物理結果を physical-sites.json、floor-samples.json に保存した。調査後の同じ敷地には検査対象の新什器がある。

    A=authoring/v36/retail/anchors
    python "$A/place_programs.py" . "$A/existing-walks.json" /tmp/anchor-candidates.json
    python "$A/bake_anchor_sets.py" . /tmp/anchor-raw "$A/planned-sites.json" "$A/physical-sites.json" "$A/floor-samples.json" /tmp/anchor-route.json
    godot --headless --path . --script res://authoring/v36/retail/bake.gd -- /tmp/anchor-raw
    python "$A/verify_authored.py" . /tmp/anchor-raw /tmp/anchor-route.json /tmp/anchor-authored.json
    godot --headless --path . --script res://authoring/v36/retail/anchors/qa_anchor_walks.gd -- "$PWD/$A/walking-floors.json" /tmp/anchor-walk.json

market_fashion.py、cinema.py、foyer_floors.py が専用メッシュの形状を保持する。売場の実座標・向き・静的コリジョン・照明・キャンペーン画像の割り付けは source/v36/anchor-programs.json。床模様は3種、印刷面は各売場テーマに対応する縦3面横並びの独自画像を読む。

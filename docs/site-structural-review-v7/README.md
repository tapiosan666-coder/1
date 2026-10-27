# FIND YOURSELF｜3館・敷地構造検証 v7

既存ゲームとは独立した建築検証用Godot 4.6.3プロジェクトです。ゲーム本体、NPC、スキャン、AP、セーブをロード・変更しません。**統合未承認**です。

## 起動

Godot 4.6.3で `project.godot` をインポートしてF6ではなくF5で起動してください。Windows配布版を使用する場合はZIPを展開し、同梱ファイルを残して `FIND_YOURSELF_Site_v7.exe` を実行します。Windows実機の操作・署名・Smart App Controlの通過は未検証です。

- WASD：移動、マウス：視点、Shift：速歩、Esc：カーソル
- F：近くの扉、またはEV行先パネル。別階のかごは現在階を選んで呼び出し、到着後に乗り込んで行先を選んでください。
- M：館内マップ。館・階の切替は表示のみ。地図中は移動・EV・ESを停止します。店舗にカーソルを合わせるとIDを表示します。
- F10：画面設定。初期1920×1080、144FPS上限、VSync要求ON。1440p/2160p、30/60/120/144/無制限に対応。
- 設定は独立プロジェクトの `user://site-v7-settings.cfg` に保存します。
- 旧デバッグキー1/2/3/4/BはB館の確認位置へ移動します。自動歩行の合格には使用していません。

## 状態

B館v6の198区画・店舗形状を維持し、3館15層・駐車場・昇降設備・館間接続のモデルを追加しました。A/Cの店舗は基本構造段階で、内装・商品・最終看板・照明・設備能力・建築仕上げは未完了です。FF15級の品質に達したとは評価していません。

RF-SUPPORT-16は未承認です。構造耐力・基礎・防水・車両積載・避難性能は計算・実証していません。自動歩行、静的車体クリアランス、図面検査、人間の実操作は別検査です。人間の実操作、Windows/RTX4060、NPC負荷、全車路の旋回・駐車は未検証です。

## データと再生成

- `source/site-v7.json`：原設計から派生した15層・駐車場・設備データ
- `source/design-v7.json`：B館198区画の保持版
- `source/brands-v7.json`：店舗ID別の480ブランド設定枠。`name`、`logo_asset`、看板位置・間口、法的確認状態を分離。最終ロゴは未制作。既存の仮看板を維持します。ロゴ画像はassets以下に配置するとID別に読み込めます。
- `source/map-data-v7.json`：同じ建築データから生成した検証用地図
- `source/elevators-v7.json`：EV21基の停止階・かご・開口
- `source/physical-routes-v7.json`：自動物理検査用の正確な経路
- `evidence/`：検査結果、実Viewport原寸画像。PDFとCSVは `deliverables/`。

Python依存：Shapely 2.2、NumPy、SciPy、Pillow、PyMuPDF。`authoring/site_v2_common.py` の旧環境パスは補助であり、通常の仮想環境でもこれらのライブラリを入れて実行できます。

再生成順序：`prepare_v7.py` → `runtime_data_v7.py` → `routes_v7.py` → `model_b_v7.py` → `site_model_v7.py` → `audit_v7.py`。古いv5/v6 authoringは比較の参照であり、この版を作る際には実行しません。

ライセンス：元プロジェクト作成のコード・手続き型画像、Noto Sans CJK JP（SIL OFL 1.1）、Godot（MITほか同梱Copyright）。実在ブランドのロゴを新規使用していません。架空ブランド名の商標クリアランスは未実施です。`licenses/` と素材台帳を参照してください。

## 設計データの参照優先順位

v7で実際に使う床は `floors[].floor_plate`、開口・昇降設備は最上位の `devices` と `elevators-v7.json`、描画/衝突は生成済みのメッシュです。`nav_free`、`cores[].shafts`、`vertical_shafts`、旧 `vertical_devices` など、原設計から残した補助フィールドは比較用の旧参照を含みます。これらだけをそのまま本編へ取り込まないでください。統合前に、新旧スキーマの移行と実歩行を別途確認する必要があります。

## 検証環境の制約

描画記録はLinuxのllvmpipe（ソフトウェアGPU、NPC 0）です。VSyncを要求しても、この環境のドライバーでは同期がサポートされません。一部の旧自動撮影プロセスで終了待ちが残り停止しています。実機Windows/RTX4060での起動・終了・描画速度・VSync・Smart App Controlは未検証で、合格扱いしていません。

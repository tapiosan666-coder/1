# FIND YOURSELF｜B館 局所整合検証 v6

作業対象は独立検証プロジェクトのみです。ゲーム本体、B館v4.1、敷地全体設計v3、検証v1〜v5は変更・統合していません。

v5の198区画（既存188ID＋追加10）、広場、吹き抜け、昇降設備位置、主要な通路網を維持しました。

## 今回の変更

- 17候補を再調査：実際の凸先端11、微細な凹状折返し5、数値的な針状境界1。11件は局所面取り、6件は境界データ修正。隣接所有者も照合し、用途不明な倉庫や通路を新設していません。
- 角に近かった入口を実際の直線間口へ移動。入口枠・上部仕上げ・局所照明と床の遠景モアレを改善。
- A/B・B/Cの1F/2F接続幅・高さ・床を照合。実際の接続先公開床の一部を表示し、連絡橋の壁面をガラスと腰壁に区分。A/C館内部全体は未施工です。
- RF床は未検証の大きな設備予約帯を整理し、約3,137㎡縮小。駐車115台、車路、歩道、庭園ゾーン面積を保持。庭園ゾーンを丸ごと立上げる誤った3D化を止め、歩行面と18個の実際の植栽枠に分けました。
- 屋上と連絡橋の共有境界に手すりを作らず、接続した床全体の外周へ生成するルールに修正。
- B1は地下躯体と2店舗を維持。1F外郭より広い地下部分は、地下屋根と外構地盤との取り合いとして表示。

## 未完了・未検証

**RF-SUPPORT-16（約4.10㎡、最大張出し約1.25m）の支持方式は未決です。** 全27箇所の支持位置案についても、耐荷重・基礎・地震・風・車両荷重の構造計算は行っていません。橙色の柱・梁は検討位置で、安全性を認定した施工済み構造ではありません。

地下防水・土被り・ピット、屋上設備の容量と保守計画、立体駐車場のスロープや全車両経路、交通制御、全6,699台の運用、人間による実操作は未検証です。

B1/RFへの階段・操作可能なエレベーターは未施工です。図面上の5層の整合と、Godotで実際に上下移動できることは区別してください。今回のB1/RFモデルは躯体と接続の診断用で、全内装完成版ではありません。FF15級の画質には未到達です。

## 確認方法

1. 先に提出PDFで図面・比較写真・残課題を確認してください。
2. ZIPを展開し、Godot **4.6.3**で `project.godot` をインポートして実行します。ゲームのセーブは読み書きしません。
3. WASD移動、マウス視点、Shift速歩、Escカーソル、F従業員扉。1/2/3で検証階、4で屋上、Bで地下へデバッグ移動できます。

通常の閲覧にPythonは不要です。NPC0の独立建築検証です。固定60Hzの自動物理検査を、描画FPSや人間による実操作として報告していません。

## 比較写真

前画像は凍結したv5メッシュと旧床シェーダーをv6の検証ハーネスで表示したGodot実画面です。後画像とカメラ位置・向き・画角を一致させています。新しいRF/B1文脈モデルと、自動歩行で記録した到達点は変更後のみです。画像生成や塗り直しは使用していません。

## 設計データ

- `source/design-v6.json`：現在の独立変更案。World XZ、m単位。
- `source/baseline-v5.json`：比較対象の凍結参照コピー。
- `source/corner-revisions.json` と `corner-review-17-v6.csv`：17件の実境界・座標・原因・修正方法。
- `source/all-198-store-ledger-v6.csv`：v5/v6面積・入口・移動距離。旧v4実効売場予算も併記。
- `source/annex-v6.json`：B1/RF・橋・支持予約・実際の植栽枠。
- `source/vertical-interface-15-checks.csv`：5層×3コアの位置と開口の照合。B1底床は下向き階段開口が不要です。
- `source/vehicle-sweep-v6.json`：選択した曲がり角の往路と同経路の逆向き姿勢確認。
- `source/opposite-lane-sweep-v6.json`：別の対向車線の検査。仮定車体4.8×1.85m、軸距2.7m、半径6m/9.5m、0.10m間隔の平面掃引です。動的なGodot車両物理・実車運転ではありません。
- `source/roof-support-reservations.csv`：支持候補位置と未決事項。全行で構造容量・基礎は未検証。
- `source/physical-routes.json`：実際の自動物理検査経路。
- `evidence/`：別配布の資料ZIPに原画像・実検査結果を収録しています。

検証用に表示する相手館プレビュー床と、B館所有床は、`other_wing_preview_floor` / `owned_B_floor_plate` で分けています。プレビュー床を商業施設全体の面積へ重複計上しないでください。旧原資料の一部数値配列（連絡経路・案内点）はBローカルXZで、World = local + (−714,−30)。ポリゴン・実店舗入口・経路はWorldです。描画Local XYZのXZ原点はWorld（−429,46）。

## 最終データからの再検証

```bash
python -m pip install -r authoring/requirements.txt
python authoring/audit_v6.py
python authoring/interfaces_v6.py
python authoring/context_model_v6.py
python authoring/model_v6.py
godot --headless --editor --path . --import --quit
godot --headless --path . --fixed-fps 60 -- --walk-test --output=./evidence/after
python authoring/grounded_cameras_v6.py
godot --path . -- --baseline --capture --output=./evidence/before
godot --path . -- --capture --output=./evidence/after
godot --path . -- --context-only --capture --output=./evidence/context
python authoring/report_v6.py
```

v5の比較メッシュは凍結済みの `assets/geometry-before.json.gz` を使います。別世代の生成コードで再生成しないでください。初期段階の設計修正スクリプトは最終設計を上書きするので、必ずコピー上で作業してください。

## 素材

Godot：MIT、Noto Sans CJK JP：SIL OFL1.1。同梱licensesを参照。テクスチャ・看板・メッシュは既存プロジェクトおよび本作業の制作物で、別途の一般公開用再利用ライセンスは付与していません。市販3D素材や実在店舗のロゴは追加していません。

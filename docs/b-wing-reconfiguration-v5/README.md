# FIND YOURSELF｜B館 街区再構成・独立検証 v5

既存ゲーム、B館v4.1、敷地全体v3、検証v1〜v4には変更を加えていません。統合禁止を維持しています。

今回の対象はB館1〜3Fです。旧未帰属床21,956.210470㎡・254成分を再集計し、共有する街区境界、店舗・裏方・共用・実設備・外部床の区分を再設計しました。全198店舗（既存188IDを維持＋新規10）の入口・売場・作業矩形を描いています。

## 確認方法

- まず提出PDFをご覧ください。ベクターの平面図は拡大できます。
- このフォルダーの `project.godot` をGodot **4.6.3**でインポートして実行できます。独立した検証シーンで、ゲームのセーブは読み書きしません。
- WASD移動、マウス視点、Shift速歩、Escカーソル、F従業員扉、1/2/3で時の広場の検証階へ移動。
- 従業員扉は通常閉まっています。検査時のみ実際の扉を開いた状態で通行しています。部外者が自由に倉庫を通り抜けるゲーム仕様を決定したものではありません。
- エレベーターは未稼働、避難階段も未施工です。誤って昇降路へ落ちないため閉鎖表示としています。自動検査の対象は店舗・管理室・実装したエスカレーターです。

## 重要な範囲と制限

この全館モデルは**建築と通行の検証モデル**です。v4の一部店舗の商品詳細を保った内装完成版ではありません。棚・衣料・カフェは用途と動線を検証するための基本表現です。FF15級の画質には達していません。

変更前の全B館3Dはv4配布版には存在しませんでした。比較の「変更前」は、凍結したv4図面から全館を再構成したGodot実画面です。実際のv4配布版の全館スクリーンショットと誤解しないでください。カメラ座標・照明・画角は対応させています。

面積の割当と通行が成立しても建築品質の承認とはしません。詳細な残課題はPDFと `source/request-status.csv` に記載しています。特に屋上床・地下外周と縮小外郭の構造的な取り合い、業種別在庫容量、避難・防火・設備、鋭角の残る区画、人間による実操作の評価は保留です。旧屋上115台の区画は新上階外郭内ですが、旧屋上床の約3,367㎡には支持・屋根計画の再検討が必要です。敷地全体6,699台を今回再検証したものではありません。

## データ

- `source/design-v5.json`：最終変更案。World XZ、m単位。
- `source/baseline-v4.json`：凍結v4図面の参照コピー。
- `source/master-site-v3.json`：元の敷地全体v3の参照コピー。原本は変更していません。
- `source/unowned-full-inventory.*`：254成分の位置・旧面積・原因・新用途・外部化。
- `source/all-198-store-ledger.csv`：旧新の区画／実効売場／バックヤード／入口／作業寸法。
- `source/physical-routes.json`：実際の物理検査に使用した経路。
- `source/cameras.json`：全比較視点。検証Local XYZのXZ原点はWorld（−429,46）。
- `source/roof-basement-impact.json`：屋上・地下への未確定影響。
- `evidence/`：配布する資料ZIPに実検査・Godot画面を収録。プロジェクトZIPでは別配布です。

## 再検証

```bash
python -m pip install numpy scipy shapely==2.2.0 Pillow PyMuPDF
python authoring/audit_v5.py
python authoring/model_v5.py --baseline
python authoring/model_v5.py
python authoring/validation_inputs.py
python authoring/public_paths_v5.py
godot --headless --editor --path . --import --quit
godot --headless --path . --fixed-fps 60 -- --walk-test --output=./evidence/after
godot --path . -- --capture --output=./evidence/after
godot --path . -- --baseline --capture --output=./evidence/before
python authoring/report_v5.py
```

通常の閲覧・歩行にはPythonは不要です。設計を作り直す初期段階のスクリプトはauthoringに履歴として含めますが、上記は**最終設計を基準に再生成**する手順です。初期スクリプトを順不同で実行すると最終案を上書きするため、コピー上で作業してください。

物理検査は固定60Hzの自動操作で、描画FPS測定ではありません。描画実測はllvmpipeソフトウェアGPU／NPC0／1280×720／GL Compatibility／MSAA4×です。RTX4060での性能試験・人間の実操作は行っていません。

## 素材

Godot：MIT、Noto Sans CJK JP：SIL OFL1.1。同梱licensesを参照。既存のプロジェクト生成テクスチャ・看板・メッシュは本プロジェクト制作物で、別途の一般公開用再利用ライセンスは付与していません。実在店舗のロゴ・市販3D素材の追加はありません。

今回の全館モデルは、床・天井を階単位にまとめた検証用の生成で、遮蔽カリング・階別ストリーミング・LODの最適化は未実施です。実測したソフトウェア描画は約0.35〜0.59FPSでした。これは製品版の性能合格ではなく、ユーザーPCの性能予測にも使用できません。

座標は `source/coordinate-frames.json` を併読してください。店舗・室・ポリゴンはWorldですが、原資料の接続経路・待合点・案内板点の一部数値配列はBローカルの参照情報として残しています。今回の図面描画は接続経路を明示変換しており、将来のNPC・案内板統合時には型ごとに一度だけ正規化する必要があります。

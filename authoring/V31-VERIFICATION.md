# v31 再検査ツール

Godot 4.6.3。初回の素材インポート後、プロジェクトフォルダで次を実行します。

`godot --headless --path . --fixed-fps 60 --script res://authoring/v31_qa_sales.gd`

`v31_qa_service_access.gd` は139レジ＋3試着室、`v31_qa_regression.gd` は既存経路・ES・安全柵・主動線・出入口・通常キー、`v31_qa_signs.gd` は案内方向、`v31_qa_devices.gd` はEVを検査します。出力はGodotユーザーデータフォルダの `v31-verification`。いずれも自動検査であり人間操作・美術承認ではありません。

描画性能は実GPU環境で `godot --path . --script res://authoring/benchmark_v31.gd -- --trial=1`。trial=1/2/3、NPC-off、VSync-onの条件を分けて記録します。上限144FPSを達成FPSとは扱いません。旧版の比較は同じ位置・画角・品質とします。OSコールド起動条件は別途記録してください。

通常起動にはこれらの制作ツールは不要です。床・壁・什器の生成キャッシュを --headless で再生成しないでください。実レンダラーが必要です。

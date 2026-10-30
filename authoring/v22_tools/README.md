# v22 再生成資料

実行にはPython 3.12、numpy、shapely 2.1、zstandard等、モデル生成にはBlender 4.3が必要です。Godotで遊ぶだけならPython/Blenderは不要です。

構造の再生成: build_combined_structure.py → build_a_continuous.py。v22_clip_geometry.py と同梱の旧pack/mesh helperを使用し、以前のワークスペースには依存しません。

内装の再生成: ../v22_layout.py → ../v22_complete_layout.py → ../v22_product_supports.py → ../v22_anchor_departments.py の後、Godot実支持・経路・床検査が必要です。配布版はその後の実メッシュ支持補正と売場ルート補正を含むため、生成スクリプトを再実行しただけで最終データと一致するとは扱わないでください。検査補正履歴はsource/v22にあります。

旧v21モデル生成スクリプトを実行して継承アセットを上書きしないでください。新モデルはv22_models.py等、v22用の出力先を用います。

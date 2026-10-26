# B館 v4 最終確認追補

ゲーム本体を変更しない設計レビューです。前回v4の平面図に併せて確認してください。

- PDF: downloads/FIND_YOURSELF-B-v4-Final-Confirmation.pdf
- 全58階別通路: route-review.csv / final-decisions.csv
- 局所仕上げの座標: local-finish-schedule.csv
- 静止設計モデル18視点: views/*.png / camera-checks.json
- 機械可読検査: frontage-audit.json

「visible_doors」は2D直線接続入口数であり、現実の可視性測定ではありません。
前後画像は同じ不透過壁補完モデルで仕上げだけ切り替えています。ゲーム画像ではありません。
18視点は目高1.65m。全経路の移動検証・Godot実歩行は未実施です。
旧v4の7810検査は前回記録で、今回の再試験結果ではありません。
閉鎖帯/共用床の微小重複2件を残存指摘として報告しています。
承認待ち。シーン・ゲームロジックを施工していません。

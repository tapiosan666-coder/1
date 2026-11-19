# 館内音と足音の再検証

Godot 4.6.3でプロジェクトのルートを作業ディレクトリにして実行する。出力先の親フォルダを先に作成する。

```sh
godot --headless --audio-driver Dummy --fixed-fps 60 --path . --script res://authoring/v36/audit/qa_audio_mix.gd -- /tmp/audio-mix.json --meter-source=res://mall_sound_v35.gd
godot --headless --audio-driver Dummy --fixed-fps 60 --path . --script res://authoring/v36/audit/qa_store_footfalls.gd -- /tmp/store-footfalls.json
```

1つ目は実際の館内音スクリプト、資産、物理床、音声ミキサーで、歩行・静止・屋外への移行・音量変更・ミュートを検査する。物理プレイヤーと2エリアの地図はテスト専用である。足音専用バスの実PCMを採取する。音量書き込みカウンターと再生ファイル・音程は実行時のメモリ内コピーにだけ加える。過去の館内音スクリプトを指定すれば同じ条件で再実行できる。`--meter-source`を省くと製品スクリプトそのもので音声試験を実行する。

2つ目は製品の全館シーンで、C館地下〜1Fの21店舗を通常のW入力と操舵で歩く。店ごとの開始地点へ配置した後、経由点から終点までを移動する。着地、到達、足音発行回数を保存する。音を人間が試聴する試験は含まない。

480店の中断なし連続検査は同じディレクトリにある `qa_shop_walks.gd` を使う。空の出力ディレクトリと範囲 `0 480` を指定する。この検査は自動目標座標モードで操作入力が無効になるため、歩行時の足音は上の21店舗検査で別途確認する。

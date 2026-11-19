# v36 商業3館の階段・エレベーター検査

Godot 4.6.3でプロジェクトのルートを作業フォルダーにする。以下の出力先は書き込み可能な絶対パスへ変更する。検査は描画を止め、通常シーンのプレイヤーと扉・かご・階段の衝突形状を60Hzで動かす。試験用の買い物客は非表示になる。WindowsのFPSと人間による実操作はこの検査の範囲外。

### 通常Wキーで階段を歩く

```sh
godot --headless --fixed-fps 60 --path . --script res://authoring/v36/audit/qa_stair_walking.gd -- --out=/tmp/v36/stairs-96.json
godot --headless --fixed-fps 60 --path . --script res://authoring/v36/audit/qa_stair_walking.gd -- --continuous --out=/tmp/v36/stairs-round-trip.json
```

1本目は全12階段について、上下各4階間の両端にあるロビーの間を歩く。各経路の最初に出発位置を設定する。踊り場で方向を変えるときの目安は0.46mで、到着ロビーでは水平・高さともに0.16m以内で接地することを求める。2本目はA西、B中央、C南西でB1からRFまで上り、B1へ戻る。各館の出発後は位置を再設定しない。各段階の入力・到達結果をJSONに記録する。

### 呼び出して乗り、停止階で降りる

```sh
godot --headless --fixed-fps 60 --path . --script res://authoring/v36/audit/qa_lift_circulation.gd -- --lifts-only --out=/tmp/v36/lifts-primary.json
godot --headless --fixed-fps 60 --path . --script res://authoring/v36/audit/qa_lift_circulation.gd -- --lifts-only --extended --out=/tmp/v36/lifts-remaining.json
```

1本目はB中央・C南西・A西の3基、2本目は残り9基を調べる。各基のB1で、かご不在時にドアへ前進して停止することを確認する。Fで呼び、プレイヤーが歩いて乗り込み、Fで開いた通常の行先画面のボタンにテストから押下シグナルを送る。B1→RF→3F→2F→1F→B1の各乗車の前後で物理的に乗降し、扉状態、到着、かご床と足元の差を記録する。各基の検査開始後は位置を再設定しない。

### 旧方式の経路を再現する

上のエレベーター検査の `--lifts-only` を `--stair-only` に置き換えると、旧経路の中間点へ2.7m/sで厳密に到達させる試験ができる。どちらのスイッチも付けない場合は、同じシーンでEVと旧方式の階段を順に検査する。v36で旧方式は96方向中69方向が通り、上り27方向で中間点の手前に停止した。失敗を含む実行は終了コード1となる。通常W歩行の結果は上段の専用コマンドで確認できる。

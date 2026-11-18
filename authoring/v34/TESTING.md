# 描画測定の再現

Godot 4.6.3 のコンソール実行ファイルを使用します。インポートを終えた比較対象を、それぞれ同じ解像度、同じFPS上限、同じVSync、同じ機材で計測します。

```powershell
& "C:\Godot\Godot_v4.6.3-stable_win64_console.exe" --path "C:\test\v34" --script res://authoring/v34/display_probe.gd -- --out=C:/test/results/v34 --frames=120 --walk --travel --startup-profile
```

同じスクリプトを外部パスで指定すればv33の比較にも使えます。出力の native.json に、シーン読込から入力準備、最初のViewport描画、静止・歩行の描画間隔、F2/F3/F1による移動先の最初の描画を記録します。プロセス開始からの時間には Godot の起動処理も含まれるため、シーン内の時間と区別します。プロセスのピークRAMはWindowsのプロセス計測を併用してください。

初回インポートの時間と、インポート後のプレイ開始にかかる時間は別に記録してください。シェーダーキャッシュを使う再起動と、別のユーザーデータ領域を使う試行も別に扱います。実測FPSは144 FPS上限設定と区別します。

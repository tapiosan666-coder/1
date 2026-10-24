# 0.13 → 0.14：モール全域の仕上げと動線

今回はA・B・C館の専門店、天井設備、人物と陰影を更新しました。A1階のフードコート近くにあった用途のない裏通路を公開経路から外し、入口を横切っていた不要な壁を撤去。正面に待合席・手洗い給水・食器返却をまとめ、アトリウム北端は館内案内ラウンジに変更しました。300人のうち既存の着席客4人を待合席へ配置し、人数や正解の決め方は維持しています。

| 対象 | 変更前：0.13 | 変更後：0.14 |
| --- | --- | --- |
| A館の主通路 | ![以前の主通路](screenshots/realism-before-entrance.png) | ![新しい主通路](screenshots/realism-after-entrance.png) |
| 吹き抜け | ![以前の吹き抜け](screenshots/realism-before-atrium.png) | ![新しい吹き抜け](screenshots/realism-after-atrium.png) |
| 上階の回廊 | ![以前の上階](screenshots/realism-before-upper.png) | ![新しい上階](screenshots/realism-after-upper.png) |
| 服飾の内装 | ![以前の服飾](screenshots/realism-before-fashion.png) | ![新しい服飾](screenshots/realism-after-fashion.png) |
| 書店と書籍 | ![以前の書店](screenshots/realism-before-bookshop.png) | ![新しい書店](screenshots/realism-after-bookshop.png) |
| フードコートへの正面導線 | ![以前の入口](screenshots/realism-before-foyer.png) | ![新しい待合](screenshots/realism-after-foyer.png) |
| 食事エリアへの見通し | ![以前は壁が横断](screenshots/realism-before-dining.png) | ![新しい食事エリア](screenshots/realism-after-dining.png) |
| 裏通路への出口を案内ラウンジへ | ![以前の出口](screenshots/realism-before-lounge.png) | ![新しい館内案内](screenshots/realism-after-lounge.png) |
| ガラス越しの植栽 | ![以前の植栽](screenshots/realism-before-garden.png) | ![新しい植栽](screenshots/realism-after-garden.png) |
| B館の回廊 | ![以前のB館](screenshots/realism-before-b-gallery.png) | ![新しいB館](screenshots/realism-after-b-gallery.png) |
| B館の専門店 | ![以前のB館店舗](screenshots/realism-before-b-store.png) | ![新しいB館店舗](screenshots/realism-after-b-store.png) |
| C館の靴売場 | ![以前のC館](screenshots/realism-before-c-store.png) | ![新しいC館](screenshots/realism-after-c-store.png) |
| 同じ人物の顔 | ![以前の顔](screenshots/realism-before-face.png) | ![新しい顔](screenshots/realism-after-face.png) |
| 同じ人物の全身 | ![以前の全身](screenshots/realism-before-body.png) | ![新しい全身](screenshots/realism-after-body.png) |

比較条件はGodot 4.6.3 Compatibility、1280×800、標準画質、300人、同じカメラ・描画時刻・共通の歩行者配置です。0.13はコミット06649d1の保存ソース、0.14はLinux release export。固定NPCは各版の実際の配置を使い、待合席への4人の変更を含みます。人物の近接比較では同じIDを両版の同じ位置へ配置しました。撮影中だけ物理更新を停止し、画像の色・明るさは後補正していません。

`-- --capture-realism`で配布ビルドから撮影できます。旧版は`tools/capture_realism.gd -- --before`を使います。`scripts/realism_capture.gd`にカメラと共通の歩行者配置を保存しています。

静的な壁・床・家具の局所遮蔽を事前計算し、プレイ中のレイトレースを増やさずに陰影を付けています。色違いの塗装を同じ材質へまとめ、細分化した形状も描画区画に振り分け直します。樹木・書籍・商品ラベルなど1,672個の一括描画データが保存工程で潰れる問題も修正しました。[生成手順](WORLD_BAKING.md)と[描画負荷の条件](PERFORMANCE.md)に詳細があります。

人物は同じ顔を保ち、手の形・肩・袖口・襟・目・髪・布の表現と、手持ちスキャナーを調整しました。人体の頭部と手には同じCC0の元形状を使用し、ライセンスを同梱しています。

『8番出口』相当の写実品質に到達した扱いではありません。頂点による陰影のため、広い壁には補間の粗さも残っています。全身を連続させた骨格スキニング、衣服の変形、高品質な反射・間接照明、個別店舗の細部には引き続き制作が必要です。現版は300人の開発用マップで、5,000人・15フロアの製品版ではありません。Windows実機のフレームレートは未測定です。

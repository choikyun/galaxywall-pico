# GALAXY WALL for Raspberry Pi Pico

Raspberry Pi Pico と Pico用 1.14インチ 液晶モジュール の組み合わせでゲームを作ってみました.  
MicroPythonで動作します.  

迫りくるパネルの隙間をひたすら埋めて消していくアクションパズルゲームです.  

元々はポケコンジャーナル（PJ）という雑誌に発表されたゲームです.  
僕はこのゲームが好きでよく真似をして作っています.  
でも多分本家ほど面白くはないので, 機会があればぜひ本家を遊んでもらいたいです.  

## 実行方法

Thonny 等で全ての py ファイル（constsnts.py, main.py, ease.py, gamedata.py, picogamelib.py, picolcd114.py）を Pico に転送してください.  
その後 Thonny から main.py を実行するか, 何か電源（モバイルバッテリーなど）に繋ぎ直してください.  
（main.py が自動実行されます）  

## 遊び方

画面右端が自機です.  
ジョイスティックの上下で移動, Bボタンでパネルを発射します.  

### ゲームの目的

画面左からパネル(隕石？)がスクロールしてくるので, 隙間に撃ってください.  
縦１列揃うとパネルは一定時間点滅して消滅します.  
点滅中にさらに1列消すと combo と表示されスコアアップになります.  
コンボを繋いでいければ高得点になります.  
（弾は点滅しているパネルをすり抜けます）  

### ゲームオーバー

パネルが左側のラインを超えるとゲームオーバーです.  
ゲームオーバー画面でBボタンを押すとリトライ, Aボタンを押すとタイトル画面に戻ります.

### ポーズ

プレイ中 A ボタンを押すとポーズになります.  
ポーズ中はハイスコアなどが確認できます.  
また, ジョイスティックの上下で画面の明るさを調整できます.  

もう一度 A ボタンを押すとゲームに戻ります.  

### アイテム

パネルに混じってアイテムも流れてきます.  
アイテムにぶつかると, 「停止」か「２連弾」のどちらかになります.  
どちらも一定時間経過すると解除されます.  

### その他

一定時間経過するとラインは右に1パネル分移動します.  
移動までの残り時間は画面下の緑色のバーで確認できます.  
パネルを消すと時間を少し伸ばす事ができます.  

ジョイスティックの左キーで強制的にパネルをスクロールさせる事もできます.  
強制スクロール中はスコアが可算されますが, ライン移動までの時間を消費します.  

通常のパネルには色がついていますが, 隙間では無い場所を撃つとグレーのパネルになります.  
グレーパネルは消してもスコアになりません.  
また, 1列揃って点滅になっても弾がすり抜ける事はできません.  

タイトル画面でAボタンを押すとちょっと難しいモードになります.  

## 技術的な事

LCD の表示はほぼメーカーのサンプル通りです.  

picogamelib.py は2Dアクション用のよくあるスプライト表示のライブラリになっています.  
（python に慣れていないので行儀の悪い変なコードになっているかもしれません）  

Pico は2コアですがこのゲームでは 1コア しか利用していません.  
最初2コアで動かしていたのですが, メモリの余裕がなくなったので1コアにしました.  
1コアでも 30FPS 出ているっぽいのでまあOKです.  
将来的にはサウンド処理で使うかもしれません.  

あと, 画面がすごく小さいので目が疲れます.  
1キャラクタ20ピクセルと大きめに描画しているのですが, 老眼おじさんにはきついです.  

Pico が600円くらい, 液晶モジュールが1300円くらい, 合計2,000円くらいで昔のゲーム機のような環境が手に入ってしまいました.  

暇つぶしのプログラミングには丁度いいかなと思います.  

## 資料等

[Raspberry Pi Pico](https://www.raspberrypi.com/products/raspberry-pi-pico/)

[1.14inch LCD Display Module for Raspberry Pi Pico, 65K Colors, 240×135, SPI](https://www.waveshare.com/pico-lcd-1.14.htm)

[GALAXY WALL '97  作者:咳止組（咳めぐ）さん](http://cosmopatrol.web.fc2.com/game_galaxywall97.html)

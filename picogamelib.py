"""PicoGameLib for PicoLCD1.14inch

シンプルなゲームライブラリ.

・スプライト
    画面に表示されるものはすべてスプライト. フレームアニメ可.
    スプライトには固有のアクションを設定できる(デフォルトはアニメ用のフレームを進める処理).
    スプライトを管理するステージに登録することで表示.
・ステージ
    ステージは BG と スプライト を描画して LCD に転送する.
    todo: バックバッファに対応する？
・イベント
    オブジェクト間の連携はイベントを使う.
    各オブジェクトは初期化時にイベントリスナーを登録する.
・シーン
    タイトル画面, ゲーム画面, ポーズ画面 など各画面はシーンで表現.
    シーンは毎フレーム enter_frame イベントを発行. 各オブジェクトはこれを購読して定期処理.
    キー入力, イベント, ステージ はシーンが管理.
・ディレクター
    シーンをスタックで管理.
"""
__version__ = "0.1.0"
__author__ = "Choi Gyun 2022"

import io
import json
import utime
import framebuf as buf

import picolcd114 as pl

# 標準イベント
EV_ENTER_FRAME = "event_enter_frame"
"""イベント 毎フレーム"""
EV_SCENE_START = "event_scene_start"
"""シーン開始"""
EV_SCENE_END = "event_scene_end"
"""シーン終了"""

# イベント プライオリティ
EV_PRIORITY_HI = 10
EV_PRIORITY_MID = 50
EV_PRIORITY_LOW = 100

DEFAULT_FPS = 30
"""デフォルトFPS"""

image_buffers = []
"""スプライトが参照するイメージバッファのリスト"""

bg_color = 0x0000
"""BGカラー"""
lcd = pl.LCD()
"""BGバッファ 全シーン共有"""


def load_status():
    """ステータスロード"""
    try:
        d = json.load(io.open("status.json", "r"))
    except:
        d = None
    return d


def save_status(d):
    """ステータスセーブ"""
    try:
        json.dump(d, io.open("status.json", "w"))
    except:
        pass


def create_image_buffers(w, h, palet, index_images):
    """インデックスカラー から RGB565 のフレームバッファを作成
    スプライトが参照するイメージバッファ（RGB565）をキャラクタデータから作成する.
    LCDが小さいので縦横サイズは2倍にする.

    Params:
        w (int): 実際に描画する幅
        h (int): 実際に描画する高さ
        palet (list): パレット
        index_images (list): 画像データ（インデックスカラー）のリスト
        1インデックスは 2x2 ピクセル
    """
    for img in index_images:
        buf565 = buf.FrameBuffer(bytearray(w * h * 2), w, h, buf.RGB565)
        # バッファに描画
        pos = 0
        for y in range(0, h, 2):
            for x in range(0, w, 4):
                buf565.fill_rect(x, y, 2, 2, palet[img[pos] & 0xF])
                buf565.fill_rect(x + 2, y, 2, 2, palet[img[pos] >> 4])
                pos += 1
        image_buffers.append(buf565)


class Sprite:
    """スプライト
    表示キャラクタの基本単位.
    スプライトは入れ子にできる.座標は親スプライトからの相対位置となる.

    Params:
        parent (Sprite): 親のスプライト
        chr_no (int): 画像No image_buffers に対応した番号
        name (str or int): キャラクタ識別の名前 ユニークであること
        x (int): X座標（親からの相対座標）
        y (int): Y座標（親からの相対座標）
        z (int): Z座標 小さい順に描画
        w (int): 幅
        h (int): 高さ
        frame_max (int): アニメ用フレーム数

    Attributes:
        parent (Sprite): 親のスプライト
        chr_no (int): 画像No image_buffers に対応した番号
        name (str or int): キャラクタ識別の名前 ユニークであること
        x (int): X座標（親からの相対座標）
        y (int): Y座標（親からの相対座標）
        z (int): Z座標 小さい順に描画
        w (int): 幅
        h (int): 高さ
        cx (int): X中心
        cy (int): Y中心
        visible (bool): 表示するか
        sprite_list (list): 子スプライトのリスト
        stage (Stage): ステージへのショートカット
        scene (Scene): シーンへのショートカット
        frame_max (int): アニメ用フレーム数
        frame_index (int): アニメ用フレームのインデックス
        frame_wait (int): アニメ用フレーム切り替えウェイト
    """

    def __init__(self, parent, chr_no, name, x, y, z, w, h, frame_max):
        self.chr_no = chr_no
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.w = w
        self.h = h
        self.cx = self.w // 2 - 1
        self.cy = self.h // 2 - 1
        self.visible = True

        self.parent = parent  # 親スプライト
        self.sprite_list = []  # 子スプライトのリスト
        if parent != None:
            self.stage = parent.stage  # ステージのショートカット
            self.scene = parent.stage.scene  # シーンのショートカット
        else:
            self.stage = None
            self.scene = None

        # フレームアニメ
        self.frame_max = frame_max  # フレーム数
        self.frame_index = 0  # フレームのインデックス
        self.frame_wait = 4  # フレームのウェイト

    def show(self, frame_buffer, x, y):
        """フレームバッファに描画

        Params:
            frame_buffer (FrameBuffer): 描画対象のバッファ(通常BG)
            x (int): 親のX座標
            y (int): 親のY座標
        """
        if self.visible:
            x += self.x
            y += self.y
            # 子スプライトの描画
            for sp in self.sprite_list:  # 子は親の下に描画？
                sp.show(frame_buffer, x, y)

            # 現在のフレームを描画
            frame_buffer.blit(
                image_buffers[self.chr_no + self.frame_index], x, y, bg_color
            )

    def action(self):
        """フレーム毎のアクション"""
        # 子スプライトのアクション
        for sp in self.sprite_list:
            sp.action()

        # アニメ用のフレームカウント
        self.frame_wait -= 1
        if self.frame_wait == 0:
            self.frame_wait = 8
            self.frame_index += 1
            if self.frame_index >= self.frame_max:
                self.frame_index = 0

    def hit_test(self, sp):
        """当たり判定
        絶対座標で比較

        Params:
            sp (Sprite): スプライト
        Returns:
            当たっているか
        """
        # 絶対座標を取得
        px = self.parent_x()
        py = self.parent_y()
        sx = sp.parent_x()
        sy = sp.parent_y()

        if (
            px <= sx + sp.w
            and px + self.w >= sx
            and py <= sy + sp.h
            and py + self.h >= sy
        ):
            return True
        else:
            return False

    def add_sprite(self, sp):
        """スプライト追加
        z順になるように

        Params:
            sp (Sprite): スプライト
        """
        if self.sprite_list == 0:
            self.sprite_list.append(sp)
            return

        # z昇順・新規は後ろに追加
        for i, s in enumerate(self.sprite_list):
            if sp.z < s.z:
                # 挿入
                self.sprite_list.insert(i, sp)
                return

        self.sprite_list.append(sp)

    def remove_sprite(self, sp):
        """スプライト削除

        Params:
            sp (Sprite): スプライト
        Returns:
            Sprite or None: 削除したスプライト or None
        """
        for i, s in enumerate(self.sprite_list):
            if s is sp:
                self.sprite_list.pop(i)
                return s

        return None

    def enter(self):
        """入場
        イベントリスナーの登録等
        """
        # 親に登録
        if self.parent != None:
            self.parent.add_sprite(self)

    def leave(self):
        """退場
        ・親から削除
        ・イベントリスナーの削除
        """
        for sp in self.sprite_list:
            sp.leave()
        self.sprite_list.clear()

        if self.parent != None:
            self.parent.remove_sprite(self)
            self.parent = None

    def abs_x(self):
        """絶対座標 X"""
        if self.parent == None:
            return self.x
        return self.x + self.abs_x()

    def abs_y(self):
        """絶対座標 Y"""
        if self.parent == None:
            return self.y
        return self.y + self.abs_y()


class Stage(Sprite):
    """ステージ
    スプライトのルートオブジェクト.
    LCDバッファにスプライトを描画.

    Params:
        chr_no (int): 画像No image_buffers に対応した番号
        name (str or int): キャラクタ識別の名前
        x (int): X座標
        y (int): Y座標
        z (int): Z座標 大きい程上に表示
        w (int): 幅
        h (int): 高さ

    Attributes:
        chr_no (int): 画像No image_buffers に対応した番号
        name (str or int): キャラクタ識別の名前
        x (int): X座標
        y (int): Y座標
        z (int): Z座標 大きい程上に表示
        w (int): 幅
        h (int): 高さ
        cx (int): X中心
        cy (int): Y中心
        visible (bool): 表示するか
        sprite_list (list): 子スプライトのリスト
        frame_max (int): アニメ用フレーム数
        frame_index (int): アニメ用フレームのインデックス
        frame_wait (int): アニメ用フレーム切り替えウェイト
        scene (Scene) 親のシーン
        stage (Stage) 自分自身
    """

    def __init__(self, chr_no, name, x, y, z, w, h):
        super().__init__(None, chr_no, name, x, y, z, w, h, 1)

        # シーン
        self.scene = None
        # ステージ 自分自身
        self.stage = self

    def enter(self, scene):
        """入場
        シーンをセット

        Params:
            scene (Scene) 親になるシーン
        """
        self.scene = scene

    def show(self):
        """LCDに表示"""

        if self.visible:
            lcd.show()

    def action(self):
        """ステージを更新
        ・スプライトのアクションを実行
        ・スプライトを描画
        """

        # BGバッファ クリア
        lcd.fill(bg_color)
        # 子スプライトのアクションと描画
        for s in self.sprite_list:
            s.action()
            s.show(lcd, self.x, self.y)

    def leave(self):
        """終了処理
        すべてのスプライトをリムーブ.
        スプライトの終了処理を呼ぶ.
        """
        for sp in self.sprite_list:
            sp.leave()

        self.sprite_list.clear()


class Anime:
    """アニメーション管理

    Attributes:
        event (EventManager): イベントマネージャ
        ease_func (obj): イージング関数
        start (int) スタート値
        delta (int) 変化量
        current_frame (int) 現在のフレーム
        total_frame (int) 終了フレーム
        value (int): アニメーションの値
    """

    def __init__(self, event, ease_func):
        self.start = 0
        self.delta = 0
        self.current_frame = 0
        self.total_frame = 0
        self.event = event
        self.func = ease_func
        self.value = 0
        self.is_playing = False  # 実行中フラグ
        self.is_paused = False  # ポーズ中フラグ

    def attach(self):
        """アニメーションを使用可能に"""
        self.event.listners.append((EV_ENTER_FRAME, self))

    def detach(self):
        """使用できないように"""
        self.event.remove_all_listner(self)

    def play(self):
        """開始"""
        if not self.is_paused:
            self.current_frame = 0
        self.is_playing = True
        self.is_paused = False

    def stop(self):
        """停止"""
        self.current_frame = 0
        self.is_playing = False
        self.is_paused = False

    def pause(self):
        """一時停止"""
        self.is_playing = False
        self.is_paused = True

    def event_enter_frame(self, type, sender, option):
        """毎フレーム処理"""
        if self.is_playing:
            self.current_frame += 1
            if self.current_frame <= self.total_frame:
                self.value = self.func(
                    self.current_frame, self.start, self.delta, self.total_frame
                )
            else:
                self.stop()


class EventManager:
    """イベント管理
    フレーム毎にイベントを処理する.

    Attributes:
        queue (list): イベントキュー
        listners (tuple): イベントリスナー 0:type 1:obj
    """

    def __init__(self):
        # イベントキュー
        self.queue = []  # deque を使いたい
        # イベントリスナー
        self.listners = []

    def post(self, event):
        """イベントをポスト

        Params:
            event (list): 0:type 1:priority 2:delay 3:sender 4:optiion
        """
        # キューが空
        if len(self.queue) == 0:
            self.queue.append(event)
            return

        # delay, priority 昇順・新規は後ろに追加
        for i, e in enumerate((self.queue)):
            if event[2] > e[2]:
                continue
            if event[2] == e[2] and event[1] >= e[1]:
                continue
            # この位置に追加
            self.queue.insert(i, event)
            return

        # 最後に追加
        self.queue.append(event)

    def clear_queue(self):
        """イベントキューをクリア"""
        self.queue.clear()

    def clear_listners(self):
        """リスナーをクリア"""
        self.listners.clear()

    def remove_lister(self, listner):
        """リスナーを削除

        Params:
            listner (tuple): 0:type 1:リスナーを持つオブジェクト
        """
        for i, ls in enumerate(self.listners):
            if ls[0] == listner[0] and ls[1] is listner[1]:
                self.listners.pop[i]

    def remove_all_listner(self, listner):
        """特定オブジェクトのすべてのリスナーを削除

        Params:
            listner (obj): リスナーを持つオブジェクト
        """
        for i, ls in enumerate(self.listners):
            if ls[1] is listner:
                self.listners.pop(i)

    def fire(self):
        """イベントを処理"""
        while True:
            if len(self.queue) == 0 or self.queue[0][2] != 0:
                break
            self.__call_listners(self.queue.pop(0))  # 遅い

        # delay 更新
        for e in self.queue:
            e[2] -= 1

    def __call_listners(self, event):
        """イベントリスナー呼び出し

        Params:
            event (list): 0:type 1:priority 2:delay 3:sender 4:optiion
        """
        for listner in self.listners:
            if event[0] == listner[0]:
                # コールバック呼び出し
                getattr(listner[1], event[0])(event[0], event[3], event[4])


class Scene:
    """シーン
    メイン画面, タイトル画面, ポース画面 等

    Params:
        name (str): シーン名
        stage (Stage): ステージ（スプライトのルート）
        event_manager (EventManageer): イベント管理
        key (InputKey): キー管理

    Attributes:
        name (int) シーン名
        stage (Stage): ステージ（スプライトのルート）
        event_manager (EventManageer): イベント管理
        key (InputKey): キー管理
        fps_ticks (int): FPS用時間を記録
        fps (int): FPS デフォルト 30
        fps_interval (int): 次回までのインターバル
        active (bool): 現在シーンがアクティブ（フレーム処理中）か
    """

    def __init__(self, name, stage, event_manager, key):
        self.name = name
        self.stage = stage
        self.event = event_manager
        self.key = key
        # FPS関連
        self.fps_ticks = utime.ticks_ms()
        self.fps = DEFAULT_FPS
        self.fps_interval = 1000 // self.fps
        self.active = False  # 現在シーンがアクティブか
        self.frame_count = 0  # 経過フレーム
        self.director = None

    def enter(self):
        """入場"""
        # 初回イベント
        self.event.post([EV_ENTER_FRAME, EV_PRIORITY_MID, 0, self, self.key])

    def action(self):
        """実行"""
        t = utime.ticks_ms()
        if utime.ticks_diff(t, self.fps_ticks) < self.fps_interval:  # FPS
            self.active = False
            return
        self.fps_ticks = t
        self.active = True
        self.frame_count += 1

        # キースキャン
        self.key.scan()

        # イベント処理
        self.event.fire()
        # ステージ アクションと表示
        self.stage.action()
        self.stage.show()

        # enter_frame イベントは毎フレーム発生
        self.event.post([EV_ENTER_FRAME, EV_PRIORITY_MID, 0, self, self.key])

    def leave(self):
        """終了処理"""
        # イベントをクリア
        self.event.clear_queue()
        # リスナーをクリア
        self.event.clear_listners()
        # スプライトを除去
        self.stage.leave()


class Director:
    """ディレクター
    各シーンを管理・実行

    Params:
        scene_list (list): 使用するシーンのリスト

    Attributes:
        scene_list (list): 使用するシーンのリスト
        scene_stack (list): シーンのスタック
        is_Playing (bool): 実行中か
    """

    def __init__(self, scene_list):
        self.scene_list = scene_list
        self.scene_stack = []
        self.is_playing = False
        # シーンにディレクターをセット
        for s in self.scene_list:
            s.director = self

    def push(self, scene_name):
        """新しいシーンをプッシュ
        Params:
            scene_name (str): シーン名
        """
        self.is_playing = False # 一時停止
        s = self.__get_scene(scene_name)  # 名前でシーン取得
        if s is None:
            return False
        self.scene_stack.append(s)
        s.enter()
        return True

    def play(self):
        """カレントシーンの実行
        カレントシーンをループ再生
        """
        while True:
            self.is_playing = True
            s = self.scene_stack[-1]
            if not self.scene_stack:
                return

            while self.is_playing:
                s.action()

    def pop(self):
        """カレントシーンのポップ（終了）"""
        if not self.scene_stack:
            return False
        self.is_playing = False
        s = self.scene_stack.pop()
        s.leave()  # シーン終了
        return True

    def __get_scene(self, scene_name):
        """シーンリストからシーンを取得
        Params:
            scene_name (str): シーン名
        Returns:
            Sccene or None: 見つかったシーン. 無ければ None.
        """
        for s in self.scene_list:
            if s.name == scene_name:
                return s

        return None

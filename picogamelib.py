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
import random
import gc
import micropython
from micropython import const

import picolcd114 as pl

# 標準イベント
EV_ENTER_FRAME = const("event_enter_frame")
"""イベント 毎フレーム"""
EV_SCENE_START = const("event_scene_start")
"""シーン開始"""
EV_SCENE_END = const("event_scene_end")
"""シーン終了"""

# イベント プライオリティ
EV_PRIORITY_HI = const(10)
EV_PRIORITY_MID = const(50)
EV_PRIORITY_LOW = const(100)

# 図形描画
SHAPE_LINE = 0
SHAPE_RECT = 1
SHAPE_RECTF = 2

DEFAULT_FPS = const(30)
"""デフォルトFPS"""

image_buffers = []
"""スプライトが参照するイメージバッファのリスト"""

bg_color = 0x0000
"""BGカラー"""
trans_color = 0x618
"""透過色"""

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


def create_image_buffers(palette, index_images):
    """インデックスカラー から RGB565 のフレームバッファを作成
    スプライトが参照するイメージバッファ（RGB565）をキャラクタデータから作成する.
    LCDが小さいので縦横サイズは2倍にする.

    Params:
        palette (list): パレット
        index_images (list): 画像データ（インデックスカラー, w, h のタプル）のリスト
        1インデックスは 2x2 ピクセル
    """
    for i in index_images:
        image = i[0]
        w = i[1]
        h = i[2]
        buf565 = buf.FrameBuffer(bytearray(w * h * 2), w, h, buf.RGB565)
        # バッファに描画
        pos = 0
        for y in range(0, h, 2):
            for x in range(0, w, 4):
                buf565.fill_rect(x, y, 2, 2, palette[image[pos] & 0xF])
                buf565.fill_rect(x + 2, y, 2, 2, palette[image[pos] >> 4])
                pos += 1
        image_buffers.append(buf565)


class Sprite:
    """スプライト
    表示キャラクタの基本単位.
    スプライトは入れ子にできる.
    座標は親スプライトからの相対位置となる.
    parent を設定すると生成時に親のリスト登録する（表示される）

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

    def __init__(self):
        self.sprite_list = []  # 子スプライトのリスト
        self.visible = False

    def init_params(self, parent, chr_no, name, x, y, z, w, h):
        """パラメータを初期化

        Params:
            parent (Sprite): 親のスプライト
            chr_no (int): 画像No image_buffers に対応した番号
            name (str or int): キャラクタ識別の名前 ユニークであること
            x (int): X座標（親からの相対座標）
            y (int): Y座標（親からの相対座標）
            z (int): Z座標 小さい順に描画
            w (int): 幅
            h (int): 高

        Returns:
            Sprite: 自分自身
        """
        self.chr_no = chr_no
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.w = w
        self.h = h
        self.cx = self.w // 2 - 1
        self.cy = self.h // 2 - 1

        self.init_parent(parent)  # 親スプライト
        self.init_anime_param()  # フレームアニメ

        return self  # チェーンできるように

    def init_parent(self, parent):
        """親スプライトを初期化"""
        if parent is None:
            self.stage = None
            self.scene = None
            return
        self.parent = parent  # 親スプライト
        self.stage = parent.stage  # ステージ
        self.scene = parent.stage.scene  # シーン
        parent.add_sprite(self)  # 親に追加

    def init_anime_param(self, max=1, wait=4):
        """フレームアニメ用パラメータを初期化"""
        self.frame_max = max
        self.frame_wait = wait
        self.frame_index = 0

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
                image_buffers[self.chr_no + self.frame_index], x, y, trans_color
            )

    def action(self):
        """フレーム毎のアクション"""
        # 子スプライトのアクション
        for sp in self.sprite_list:
            sp.action()

        if self.visible:
            # アニメ用のフレームカウント
            self.frame_wait -= 1
            if self.frame_wait == 0:
                self.frame_wait = 8
                self.frame_index = (self.frame_index + 1) % self.frame_max

    def hit_test(self, sp):
        """当たり判定
        絶対座標で比較

        Params:
            sp (Sprite): スプライト
        Returns:
            bool: 当たっているか
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
        z順になるように.
        すでにあったら追加しない.

        Params:
            sp (Sprite): スプライト
        """
        if self.sprite_list == 0:
            self.sprite_list.append(sp)
            return

        for s in self.sprite_list:
            if s is sp:
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
        親から切り離す

        Params:
            sp (Sprite): スプライト
        """
        for i in range(len(self.sprite_list) - 1, -1, -1):
            if self.sprite_list[i] is sp:
                del self.sprite_list[i]
                sp.parent = None
                sp.stage = None
                sp.scene = None
                sp.visible = False
                return

    def remove_all_sprites(self):
        """全てのスプライト削除"""

        for sp in self.sprite_list:
            sp.remove_all_sprites()
            sp.parent = None
            sp.stage = None
            sp.scene = None
            sp.visible = False

        self.sprite_list.clear()

    def enter(self):
        """入場
        イベントリスナーの登録, その他初期化処理.
        enter 時は parent は None なので注意.
        """
        for sp in self.sprite_list:
            sp.enter()

        self.visible = True

    def leave(self):
        """退場
        ・イベントリスナーの削除, その他終了処理.
        """
        for sp in self.sprite_list:
            sp.leave()  # 子スプライトも退場

        # 親から削除
        if self.parent is not None:
            self.parent.remove_sprite(self)

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


class SpriteContainer(Sprite):
    """スプライトのコンテナ
    自身は描画しない.子スプライトのみ.
    """

    def __init__(self):
        super().__init__()

    def init_params(self, parent, name, x, y, z):
        """パラメータを初期化

        Params:
            parent (Sprite): 親のスプライト
            name (str or int): キャラクタ識別の名前 ユニークであること
            x (int): X座標（親からの相対座標）
            y (int): Y座標（親からの相対座標）
            z (int): Z座標 小さい順に描画
        """
        super().init_params(parent, 0, name, x, y, z, 0, 0)

    def show(self, frame_buffer, x, y):
        """子スプライトのみフレームバッファに描画

        Params:
            frame_buffer (FrameBuffer): 描画対象のバッファ(通常BG)
            x (int): 親のX座標
            y (int): 親のY座標
        """
        if self.visible:
            x += self.x
            y += self.y
            # 子スプライトの描画
            for sp in self.sprite_list:
                sp.show(frame_buffer, x, y)


class BitmapSprite(Sprite):
    """ビットマップを直接描画するスプライト（低速）

    Params:
        bitmap (taple): indexed-color, width, height
    """

    def __init__(self, parent, bitmap, name, x, y, z, w, h):
        super().__init__()
        self.init_params(parent, 0, name, x, y, z, w, h)
        self.bitmap = bitmap

    @micropython.native
    def show(self, frame_buffer, x, y):
        """フレームバッファに描画
        自分自身のみ描画.

        Params:
            frame_buffer (FrameBuffer): 描画対象のバッファ(通常BG)
            x (int): 親のX座標
            y (int): 親のY座標
        """
        if self.visible:
            x += self.x
            y += self.y

            bmp = memoryview(self.bitmap[0])
            buf = memoryview(frame_buffer.buf)
            w = self.bitmap[1]
            h = self.bitmap[2]

            lcd_w = pl.LCD_W * 2
            start = x * 2 + y * lcd_w

            idx = 0
            for dy in range(0, h, 2):
                pos1 = dy * lcd_w + start
                pos2 = pos1 + lcd_w
                for dx in range(0, w * 2, 4):
                    pos_x1 = pos1 + dx
                    pos_x2 = pos2 + dx
                    c1 = bmp[idx]
                    c2 = bmp[idx + 1]
                    buf[pos_x1] = c1
                    buf[pos_x1 + 1] = c2
                    buf[pos_x1 + 2] = c1
                    buf[pos_x1 + 3] = c2
                    buf[pos_x2] = c1
                    buf[pos_x2 + 1] = c2
                    buf[pos_x2 + 2] = c1
                    buf[pos_x2 + 3] = c2
                    idx += 2

class ShapeSprite(SpriteContainer):
    """図形描画用スプライト
    子スプライトを持たない（持っても描画しない）

    Params:
        shape (taple): 図形データ 0:mode(LINE|HLINE|VLINE|RECT|RECTF) 1:x1 2:y1 3:x2 4:y2 5:color
    """

    def __init__(self, parent, shape, name, z):
        self.super().__init__()
        self.init_params(parent, 0, name, shape[1], shape[2], z, 0, 0)
        self.shape = shape
        self.w = shape[3] - shape[1]
        self.h = shape[4] - shape[2]
        self.mode = shape[0]
        self.color = shape[5]

    def show(self, frame_buffer, x, y):
        """フレームバッファに図形を描画"""
        if self.visible:
            x += self.x
            y += self.y
            if mode == 'LINE':
                frame_buffer.line(shap[1], shape[2], shape[3], shape[4], self.color)
            elif mode == 'HLINE':
                frame_buffer.hline(shap[1], shape[2], self.w, self.color)
            elif mode == 'VLINE':
                frame_buffer.vline(shap[1], shape[2], self.h, self.color)
            elif mode == 'RECT':
                frame_buffer.rect(shap[1], shape[2], shape[3], shape[4], self.color)
            elif mode == 'RECTF':
                frame_buffer.rect(shap[1], shape[2], shape[3], shape[4], self.color, True)


class SpritePool:
    """スプライトプール
    スプライトを直接生成しないでプールから取得.
    使用後は返却.

    Params:
        stage (Stage): 所属するステージ
        name (str): クラス
        size (int): プールのサイズ

    Attributes:
        name (str): クラス
        size (int): プールのサイズ
        pool (list): スプライトのリスト
    """

    def __init__(self, stage, clz, size=32):
        self.stage = stage
        self.size = size
        self.clz = clz
        self.pool = []
        # プール作成
        for i in range(size):
            sp = clz()
            sp.parent = None
            sp.stage = stage
            sp.scene = stage.scene
            self.pool.append(sp)

    def get_instance(self):
        """インスタンスを取得"""
        if len(self.pool) == 0:
            o = self.clz()  # プールが空の時は新規作成
            o.parent = None
            o.stage = self.stage
            o.scene = self.stage.scene
            o.enter()
            return o
        else:
            o = self.pool.pop()
            o.parent = None
            o.stage = self.stage
            o.scene = self.stage.scene
            o.enter()
            return o

    def return_instance(self, sp):
        """インスタンスを返却"""
        sp.leave()
        self.pool.append(sp)


class Stage(Sprite):
    """ステージ
    LCDバッファにスプライトを描画する.
    スプライトのルートオブジェクト.
    ルートなので parent は None となる.
    """

    def __init__(self, scene, name, x, y, z, w, h):
        super().__init__()
        self.init_params(scene, name, x, y, z, w, h)

    def init_params(self, scene, name, x, y, z, w, h):
        """パラメータをセット

        Params:
            name (str or int): キャラクタ識別の名前 ユニークであること
            x (int): X座標（親からの相対座標）
            y (int): Y座標（親からの相対座標）
            z (int): Z座標 小さい順に描画
            w (int): 幅
            h (int): 高
        """
        super().init_params(None, 0, name, x, y, z, w, h)
        # ステージ 自分自身
        self.stage = self
        # シーン
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
        self.event = event
        self.func = ease_func
        self.is_playing = False  # 実行中フラグ
        self.is_paused = False  # ポーズ中フラグ
        self.start = 0
        self.delta = 0
        self.current_frame = 0
        self.total_frame = 0
        self.value = 0

    def attach(self):
        """アニメーションを使用可能に"""
        self.event.add_listner([EV_ENTER_FRAME, self, True])

    def detach(self):
        """使用できないように"""
        self.event.remove_all_listner(self)

    def play(self):
        """開始"""
        if not self.is_paused:
            self.current_frame = 0
        self.value = self.start

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
        listners (list): イベントリスナー 0:type 1:obj 2:bool
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

    def enable_listners(self, targets=None, ignores=None):
        """全てのリスナーを有効化

        Params:
            target (list): 対象イベントタイプ
            ignore (list): 除外イベントタイプ
        """
        # 全て対象
        if targets is None and ignores is None:
            for ls in self.listners:
                ls[2] = True
        # 対象リスト
        if targets is not None:
            for ls in self.listners:
                if ls[0] in targets:
                    ls[2] = True
        # 無視リスト
        if ignores is not None:
            for ls in self.listners:
                if ls[0] not in ignores:
                    ls[2] = True

    def disable_listners(self, targets=None, ignores=None):
        """全てのリスナーを無効化

        Params:
            target (list): 対象イベントタイプ
            ignore (list): 除外イベントタイプ
        """
        # 全て対象
        if targets is None and ignores is None:
            for ls in self.listners:
                ls[2] = False
        # 対象リスト
        if targets is not None:
            for ls in self.listners:
                if ls[0] in targets:
                    ls[2] = False
        # 無視リスト
        if ignores is not None:
            for ls in self.listners:
                if ls[0] not in ignores:
                    ls[2] = False

    def add_listner(self, listner):
        """リスナー追加
        すでにあったら追加しない

        Params:
            listner (list): 0:type 1:リスナーを持つオブジェクト 2: 有効か
        """
        for li in self.listners:
            if li[0] == listner[0] and li[1] == listner[1]:
                return
        self.listners.append(listner)

    def remove_lister(self, listner):
        """リスナーを削除

        Params:
            listner (list): 0:type 1:リスナーを持つオブジェクト 2: 有効か
        """
        for i in range(len(self.listners) - 1, -1, -1):
            if self.listners[i][0] == listner[0] and self.listners[i][1] is listner[1]:
                del self.listners[i]

    def remove_all_listner(self, listner):
        """特定オブジェクトのすべてのリスナーを削除

        Params:
            listner (obj): リスナーを持つオブジェクト
        """
        for i in range(len(self.listners) - 1, -1, -1):
            if self.listners[i][1] is listner:
                del self.listners[i]

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
            if event[0] == listner[0] and listner[2]:  # 有効なリスナーのみ
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

    def __init__(self, name):
        self.name = name
        self.stage = None
        self.event = None
        self.key = None

        # FPS関連
        self.fps_ticks = utime.ticks_ms()
        self.fps = DEFAULT_FPS
        self.fps_interval = 1000 // self.fps
        self.active = False  # 現在シーンがアクティブか
        self.frame_count = 0  # 経過フレーム
        self.director = None

    def registerStagehands(self, stage, event, key):
        """ステージ, イベント, キー入力 の登録"""
        self.stage = stage
        self.event = event
        self.key = key

    def enter(self):
        """入場"""
        # ステージの有効化
        self.stage.enter()
        # 初回イベント
        self.event.post([EV_ENTER_FRAME, EV_PRIORITY_MID, 0, self, self.key])
        self.frame_count = 0

    def action(self):
        """実行"""
        t = utime.ticks_ms()
        if utime.ticks_diff(t, self.fps_ticks) < self.fps_interval:  # FPS
            self.active = False
            # gc 実行
            if random.randint(0, DEFAULT_FPS * 30) == 0:
                gc.collect()
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
        self.is_playing = False  # 一時停止
        s = self.__get_scene(scene_name)  # 名前でシーン取得
        if s is None:
            return False
        self.scene_stack.append(s)
        s.enter()
        return s

    def play(self):
        """カレントシーン実行
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
        """カレントシーンのポップ（ポーズ）"""
        if not self.scene_stack:
            return False
        self.is_playing = False
        self.scene_stack.pop()

    def stop(self):
        """シーン終了"""
        s = self.pop()
        s.leave()

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

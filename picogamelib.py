"""PicoGameLib for PicoLCD1.14inch

シンプルなゲームライブラリ.

・スプライト
    画面に表示されるものはすべてスプライト. フレームアニメ可.
    スプライトには固有のアクションを設定できる(デフォルトはアニメ用のフレームを進める処理).
    スプライトを管理するステージに登録することで表示.
・ステージ
    ステージは BG と スプライト を描画して LCD に転送する.
・イベント
    オブジェクト間の連携はイベントで行う.
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
import micropython
import gc

#import _thread
from micropython import const

import picolcd114 as lcd114


# 標準イベント
EV_ENTER_FRAME = const("ev_enter_frame")
"""毎フレーム"""
EV_ANIME_ENTER_FRAME = const("ev_anime_enter_frame")
"""毎フレーム（アニメ）"""
EV_ANIME_COMPLETE = const("ev_anime_complete")
"""アニメ終了"""

# イベント プライオリティ
EV_PRIORITY_HI = const(10)
EV_PRIORITY_MID = const(50)
EV_PRIORITY_LOW = const(100)

DEFAULT_FPS = const(30)
"""デフォルトFPS"""

image_buffers = []
"""スプライトが参照するイメージバッファのリスト"""

bg_color = 0x0000
"""BGカラー"""
trans_color = 0x618
"""透過色"""

lcd = lcd114.LCD()
"""BGバッファ 全シーン共有"""

#lock = _thread.allocate_lock()
"""共有ロック"""


def load_status(filename):
    """ステータスロード"""
    try:
        d = json.load(io.open(filename, "r"))
    except:
        d = None
    return d


def save_status(d, filename):
    """ステータスセーブ"""
    try:
        json.dump(d, io.open(filename, "w"))
    except:
        # セーブできない
        pass


def create_image_buffers(palette, index_images):
    """インデックスカラーのキャラデータ から RGB565 の描画用フレームバッファを作成
    LCDが小さいので縦横サイズは2倍にする.

    Params:
        palette (list): パレット
        index_images (list): 画像データ（インデックスカラー, w, h のタプル）のリスト
        1インデックスは 2x2 ピクセル
    """
    for i in index_images:
        image, w, h = i
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
    親のスプライトリストに登録すると描画される.

    Attributes:
        parent (Sprite): 親スプライト
        chr_no (int): 画像No image_buffers に対応した番号
        name (str or int): キャラクタ識別の名前
        x (int): X座標（親からの相対座標）
        y (int): Y座標（親からの相対座標）
        z (int): Z座標 小さい順に描画
        w (int): 幅
        h (int): 高さ
        visible (bool): 表示するか
        sprite_list (list): 子スプライトのリスト
        stage (Stage): ステージへのショートカット
        scene (Scene): シーンへのショートカット
        event (EventManager): イベントマネージャーのショートカット
        frame_max (int): アニメ用フレーム数
        frame_index (int): アニメ用フレームのインデックス
        frame_wait (int): アニメ用フレーム切り替えウェイト
        frame_wait_def (int): アニメ用フレーム切り替えウェイト デフォルト値
        owner (obj): スプライトの所有者
    """

    def __init__(self):
        self.sprite_list = []  # 子スプライトのリスト
        self.visible = False
        self.owner = None

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

        self.init_parent(parent)  # 親スプライト
        self.init_frame_param()  # フレームアニメ

        return self  # チェーンできるように

    def init_parent(self, parent=None):
        """親スプライトを初期化
        
        Params:
            parent (Sprite): 親スプライト
        """
        if parent is None:
            self.stage = self.scene = self.event = None
            return
        self.parent = parent  # 親スプライト
        self.stage = parent.stage  # ステージ
        self.scene = parent.stage.scene  # シーン
        self.event = parent.stage.event  # イベント
        parent.add_sprite(self)  # 親に追加

    def init_frame_param(self, max=1, wait=4):
        """フレームアニメ用パラメータを初期化

        Params:
            max (int): 最大フレーム数
            wait (int): 次のフレームまでのウェイト
        """
        self.frame_max = max
        self.frame_wait = wait
        self.frame_wait_def = wait
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
                self.frame_wait = self.frame_wait_def
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
                sp.event = None
                sp.visible = False
                return

    def enter(self):
        """入場
        イベントリスナーの登録, その他初期化処理.
        """
        for sp in self.sprite_list:
            sp.enter()

        self.visible = True
        return self  # チェーンできるように

    def leave(self):
        """退場
        ・イベントリスナーの削除, その他終了処理.
        """
        for sp in self.sprite_list:
            sp.leave()  # 子スプライトも退場

        # 親から削除
        if self.parent is not None:
            self.parent.remove_sprite(self)

        # プールに返却
        if self.owner is SpritePool:
            self.owner.pool.return_instance(self)

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
    子スプライトのみ描画.
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
    インデックスと同じく２倍にして表示.
    大きな画像はメモリ不足になるのでこちらを使用.
    width は 4 で割り切れること.

    Params:
        bitmap (taple): bitmap, width, height
    """

    def __init__(self, parent, bitmap, name, x, y, z, w, h):
        super().__init__()
        self.init_params(parent, 0, name, x, y, z, w, h)
        self.set_bitmap(bitmap)
        self.lcd_w = lcd114.LCD_W * 2

    def set_bitmap(self, bitmap):
        """ビットマップ画像をセット"""
        self.bmp = memoryview(bitmap[0])
        self.w = bitmap[1]
        self.h = bitmap[2]
        self.w2 = self.w * 2

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

            buf = memoryview(frame_buffer.buf)
            bmp = self.bmp
            w = self.w
            w2 = self.w2
            h = self.h
            lcd_w = self.lcd_w
            start = x * 2 + y * lcd_w

            idx = 0
            for dy in range(0, h, 2):
                pos1 = dy * lcd_w + start
                pos2 = pos1 + lcd_w
                for dx in range(0, w2, 8):
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

                    c1 = bmp[idx + 2]
                    c2 = bmp[idx + 3]
                    buf[pos_x1 + 4] = c1
                    buf[pos_x1 + 5] = c2
                    buf[pos_x1 + 6] = c1
                    buf[pos_x1 + 7] = c2
                    buf[pos_x2 + 4] = c1
                    buf[pos_x2 + 5] = c2
                    buf[pos_x2 + 6] = c1
                    buf[pos_x2 + 7] = c2
                    idx += 4


class ShapeSprite(SpriteContainer):
    """図形描画用スプライト
    子スプライトを持たない（持っても描画しない）

    Params:
        shape (list): 図形データ 0:mode(LINE|HLINE|VLINE|RECT|RECTF) 1:x1 2:y1 3:x2 4:y2 5:color
    """

    def __init__(self, parent, shape, name, z):
        super().__init__()
        self.init_params(parent, name, shape[2], shape[3], z)
        self.shape = shape

    def show(self, frame_buffer, x, y):
        """フレームバッファに図形を描画"""
        if self.visible:
            x += self.x
            y += self.y
            shape = self.shape
            m = shape[0]

            if m == "LINE":
                frame_buffer.line(shape[1], shape[2], shape[3], shape[4], shape[5])
            elif m == "HLINE":
                frame_buffer.hline(shape[1], shape[2], shape[3] - shape[1], shape[5])
            elif m == "VLINE":
                frame_buffer.vline(shape[1], shape[2], shape[4] - shape[2], shape[5])
            elif m == "RECT":
                frame_buffer.rect(shape[1], shape[2], shape[3], shape[4], shape[5])
            elif m == "RECTF":
                frame_buffer.rect(
                    shape[1], shape[2], shape[3], shape[4], shape[5], True
                )


class SpritePool:
    """スプライトプール
    スプライトを直接生成しないでプールから取得.
    使用後は返却.

    Params:
        stage (Stage): 所属するステージ
        cls (): クラス
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
        for _ in range(size):
            sp = clz()
            sp.parent = None
            sp.stage = stage
            sp.scene = stage.scene
            sp.event = stage.event
            sp.owner = self
            self.pool.append(sp)

    def get_instance(self):
        """インスタンスを取得"""
        if len(self.pool) == 0:
            o = self.clz()  # プールが空の時は新規作成
            o.parent = None
            o.stage = self.stage
            o.scene = self.stage.scene
            o.event = self.stage.event
            o.owner = self
            return o
        else:
            o = self.pool.pop()
            o.parent = None
            o.stage = self.stage
            o.scene = self.stage.scene
            o.event = self.stage.event
            return o

    def return_instance(self, sp):
        """インスタンスを返却
        設定したサイズを超えたら捨てる
        """
        if len(self.pool) < self.size:
            self.pool.append(sp)


class Stage(Sprite):
    """ステージ
    LCDバッファにスプライトを描画する.
    スプライトのルートオブジェクト.
    ルートなので parent は None となる.

    Attributes:
        scene (Scene): シーン
        event (EventManager): イベント管理
    """

    def __init__(self, scene, event, name, x, y, z, w, h):
        super().__init__()
        self.init_params(scene, event, name, x, y, z, w, h)

    def init_params(self, scene, event, name, x, y, z, w, h):
        """パラメータをセット

        Params:
            scene (Scene): シーン
            event (EventManager): イベント管理
            name (str or int): キャラクタ識別の名前
            x (int): X座標（親からの相対座標）
            y (int): Y座標（親からの相対座標）
            z (int): Z座標 小さい順に描画
            w (int): 幅
            h (int): 高
        """
        super().init_params(None, 0, name, x, y, z, w, h)
        # イベント
        self.event = event
        # ステージ 自分自身
        self.stage = self
        # シーン
        self.scene = scene
        return self

    def action(self):
        """スプライトのアクションを実行"""
        if self.visible:
            for s in self.sprite_list:
                s.action()

    def show(self):
        """ステージを更新
        ・スプライトをバッファに描画
        """
        # BGバッファ クリア
        lcd.fill(bg_color)
        # 子スプライトをバッファに描画
        for s in self.sprite_list:
            s.show(lcd, self.x, self.y)


class Anime:
    """アニメーション管理

    Attributes:
        name (str): 名前
        event (EventManager): イベントマネージャ
        ease_func (obj): イージング関数
        is_playing (bool): 実行中フラグ
        is_paused (bool): ポーズ中フラグ
        start (int) スタート値
        delta (int) 変化量
        current_frame (int) 現在のフレーム
        total_frame (int) 終了フレーム
        value (int): アニメーションの値
    """

    def __init__(self, name, event, ease_func):
        self.name = name
        self.event = event
        self.func = ease_func
        self.is_playing = False
        self.is_paused = False
        self.start = 0
        self.delta = 0
        self.current_frame = 0
        self.total_frame = 0
        self.value = 0

    def attach(self):
        """アニメーションを使用可能に"""
        self.event.add_listner([EV_ANIME_ENTER_FRAME, self, True])

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

    def ev_anime_enter_frame(self, type, sender, option):
        """イベント: 毎フレーム処理"""
        if self.is_playing:
            self.current_frame += 1
            if self.current_frame <= self.total_frame:
                self.value = self.func(
                    self.current_frame, self.start, self.delta, self.total_frame
                )
            else:
                self.stop()
                # アニメ終了のイベント
                self.event.post(
                    [EV_ANIME_COMPLETE, EV_PRIORITY_MID, 0, self, self.name]
                )


class EventManager:
    """イベント管理
    フレーム毎にイベントを処理する.

    Attributes:
        queue (list): イベントキュー
        listners (list): イベントリスナー [0]:type [1]:obj [2]:bool
    """

    def __init__(self):
        # イベントキュー
        self.queue = []  # deque を使いたい
        # イベントリスナー
        self.listners = []

    def post(self, event):
        """イベントをポスト

        Params:
            event (list): [0]:type [1]:priority [2]:delay [3]:sender [4]:optiion
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
            listner (list): [0]:type [1]:リスナーを持つオブジェクト [2]: 有効か
        """
        for li in self.listners:
            if li[0] == listner[0] and li[1] == listner[1]:
                return
        self.listners.append(listner)

    def remove_lister(self, listner):
        """リスナーを削除

        Params:
            listner (list): [0]:type [1]:リスナーを持つオブジェクト [2]: 有効か
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
            event (list): [0]:type [1]:priority [2]:delay [3]:sender [4]:optiion
        """
        for listner in self.listners:
            if event[0] == listner[0] and listner[2]:  # 有効なリスナーのみ
                # コールバック呼び出し
                getattr(listner[1], event[0])(event[0], event[3], event[4])


class Scene:
    """シーン
    メイン画面, タイトル画面, ポース画面 等.

    Params:
        name (str): シーン名
        stage (Stage): ステージ（スプライトのルート）
        event (EventManageer): イベント管理
        key (InputKey): キー管理

    Attributes:
        name (int) シーン名
        stage (Stage): ステージ（スプライトのルート）
        event (EventManageer): イベント管理
        key (InputKey): キー管理
        fps_ticks (int): FPS用時間を記録
        fps (int): FPS デフォルト 30
        fps_interval (int): 次回までのインターバル
        frame_count (int): 開始からのフレーム数
        active (bool): 現在シーンがアクティブ（フレーム処理中）か
    """

    def __init__(self, name, event, stage, key):
        self.name = name
        self.stage = stage
        self.event = event
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
        # ステージの有効化
        self.stage.enter()
        # 初回イベント
        self.event.post([EV_ENTER_FRAME, EV_PRIORITY_MID, 0, self, self.key])
        self.event.post([EV_ANIME_ENTER_FRAME, EV_PRIORITY_MID, 0, self, self.key])

        self.frame_count = 0

    def action(self):
        """実行"""
        t = utime.ticks_ms()
        if utime.ticks_diff(t, self.fps_ticks) < self.fps_interval:  # FPS
            self.active = False
            # たまに gc 実行
            if self.frame_count % (DEFAULT_FPS * 10) == 0:
                gc.collect()
            return

        self.fps_ticks = t
        self.active = True
        self.frame_count += 1

        # キースキャン
        self.key.scan()

        # イベント処理
        self.event.fire()

        # ステージ アクション
        self.stage.action()

        # バッファに描画
        # 排他処理
        #lock.acquire()
        self.stage.show()
        #lock.release()
        lcd.show()

        # enter_frame イベントは毎フレーム発生
        self.event.post([EV_ENTER_FRAME, EV_PRIORITY_MID, 0, self, self.key])
        self.event.post([EV_ANIME_ENTER_FRAME, EV_PRIORITY_MID, 0, self, self.key])

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
    各シーンを管理・実行.
    シーンはスタックで管理してる.

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


#def thread_send_buf_to_lcd():
#    """LCDにバッファを転送するスレッド
#
#    CORE1 が担当.
#    """
#    while True:
#        lock.acquire()
#        lcd.show()
#        lock.release()

"""GALAXY WALL Rainbow"""
__version__ = "1.0.0"
__author__ = "Choi Gyun 2022"

import utime
import random

import picogamelib as gl
import picolcd114 as pl
import gamedata as data
import ease

# 自機
SHIP_WIDTH = 20
SHIP_HEIGHT = 20
SHIP_MOVE_STEP = SHIP_HEIGHT + 2
SHIP_MOVE_LIMIT = SHIP_MOVE_STEP * 5
SHIP_MOVE_FRAME_MAX = 8  # 移動にかかるフレーム数

# 弾
SHOT_WIDTH = 10
SHOT_HEIGHT = 10
SHOT_PANEL_MAX = 2
SHOT_SPEED = 10

# フィールド
FIELD_WIDTH = 12
FIELD_HEIGHT = 6

# レベル
LEVEL_MAX = 4
LEVEL_STEP = 4

# パネル
PANEL_WIDTH = 20
PANEL_HEIGHT = 20
PANEL_BLANK_Y = 2
PANEL_OFFSET = 19
PANEL_OFFSET_INIT = 19
PANEL_MAX = 5
COLOR_MAX = 6

# スクロール
SCROLL_WAIT = 8  # ウェイト
SCROLL_STOP_TIME = 10  # 一定時間停止

# 点滅
FLASH_INTERVAL = 4

# 1列消去の遅延時間
DELETE_DELAY = 25

# キャラクタ
CHR_SHIP = 0
CHR_PANEL = 1
CHR_SHOT = 7

# イベント
EV_CHECK_HIT = "event_check_hit_panel"
"""弾とパネルの当たり判定"""
EV_DELETE_LINE = "event_delete_line"
"""ライン消去"""


class MainScene(gl.Scene):
    """メイン"""

    def __init__(self, name, key_input):
        # ステージ
        stage = MainStage(0, "", 0, 0, 0, pl.LCD_WIDTH, pl.LCD_HEIGHT)
        # イベントマネージャ
        event_manager = gl.EventManager()
        super().__init__(name, stage, event_manager, key_input)

        # ステージにシーンをセット
        self.stage.scene = self

        # スプライト作成
        self.ship = Ship(
            stage, CHR_SHIP, "SHIP", 0, 0, 1, SHIP_WIDTH, SHIP_HEIGHT
        )  # 自機
        
        # フィールド作成
        self.fieldmap = FieldMap(stage, FIELD_WIDTH, FIELD_HEIGHT) 

    def enter(self):
        """ゲームの初期化処理"""
        super().enter()
        # 自機初期化
        self.ship.enter()
        # フィールド初期化
        for i in range(6):
            self.fieldmap.set_new_line(6 + i)

    def action(self):
        """フレーム毎のアクション 30FPS"""
        while True:
            super().action()

        # ポース
        if self.active:
            if self.key.push & pl.KEY_A:
                pass


    def leave(self):
        """終了処理"""
        super().leave()

    ### イベントリスナー


class PauseScene(gl.Scene):
    """ポーズ
    ・スコア表示
    ・LCD輝度調整
    """

    def __init__(self, name, key_input):
        # ステージ
        stage = MainStage(0, "", 0, 0, 0, pl.LCD_WIDTH, pl.LCD_HEIGHT)
        # イベントマネージャ
        event_manager = gl.EventManager()
        super().__init__(name, stage, event_manager, key_input)

        # ステージにシーンをセット
        self.stage.scene = self
        # スプライト作成

    def enter(self):
        super().enter()

    def action(self):
        while True:
            super().action()

    def leave(self):
        super().leave


class MainStage(gl.Stage):
    """ステージ"""

    def __init__(self, chr_no, name, x, y, z, w, h):
        super().__init__(chr_no, name, x, y, z, w, h)

    def action(self):
        # スプライトアクション
        super().action()

    ### イベントリスナー


class Ship(gl.Sprite):
    """自機クラス"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__(parent, chr_no, name, x, y, z, w, h, 1)

        self.fire_panel_num = 0  # 現在の発射数
        self.move_anime = gl.Anime(self.scene.event, ease.out_quart)  # 移動アニメ

    def enter(self):
        super().enter()
        # イベントリスナー登録
        self.scene.event.listners.append((gl.EV_ENTER_FRAME, self))
        self.move_anime.attach()  # アニメ有効化

    def leave(self):
        # イベントリスナー削除
        self.scene.event.remove_all_listner(self)
        self.move_anime.detach()  # アニメ無効化
        super().leave()

    def action(self):
        super().action()

    def __fire_panel(self):
        """弾発射"""
        if self.fire_panel_num >= SHOT_PANEL_MAX:
            return
        self.fire_panel_num += 1
        color = random.randint(0, 5)
        # 新しい弾を生成
        shot = ShotPanel(
            self.stage,
            color + CHR_SHOT,
            "shot" + str(self.fire_panel_num),
            self.x,
            self.y,
            1,
            SHOT_WIDTH,
            SHOT_HEIGHT,
            color,
        )
        shot.enter()

    ### イベントリスナー
    def event_enter_frame(self, type, sender, option):
        """フレーム毎"""
        # 上下移動
        if (
            option.repeat & pl.KEY_UP
            and self.y > 0
            and not self.move_anime.is_playing
        ):
            # アニメセット
            self.move_anime.start = self.y
            self.move_anime.delta = -SHIP_MOVE_STEP
            self.move_anime.total_frame = SHIP_MOVE_FRAME_MAX
            self.move_anime.play()
        if (
            option.repeat & pl.KEY_DOWN
            and self.y < SHIP_MOVE_LIMIT
            and not self.move_anime.is_playing
        ):
            # アニメセット
            self.move_anime.start = self.y
            self.move_anime.delta = SHIP_MOVE_STEP
            self.move_anime.total_frame = SHIP_MOVE_FRAME_MAX
            self.move_anime.play()

        if option.repeat & pl.KEY_LEFT:
            pass
        if option.repeat & pl.KEY_RIGHT:
            pass

        # 弾発射
        if option.push & pl.KEY_B and not self.move_anime.is_playing:
            self.__fire_panel()

        # 移動中
        if self.move_anime.is_playing:
            self.y = int(self.move_anime.value)


class FieldMap:
    """フィールドマップの管理

    Attributes:
        stage (Stage): ステージ（スプライトのルート）
        scene (Scene): ステージの所属しているシーン
        w (int): 幅
        h (int): 高さ
    """

    def __init__(self, stage, w, h):
        self.stage = stage
        self.scene = stage.scene
        # フィールドマップ パネルの配置 2次元マップ
        self.fieldmap = [
            [None for i in range(FIELD_WIDTH)] for j in range(FIELD_HEIGHT)
        ]
        # レベル
        self.level = 1
        # スクロールのオフセット ドット単位で移動するため
        self.scroll_offset = PANEL_OFFSET_INIT
        self.scroll_wait = SCROLL_WAIT
        self.scroll_wait_def = SCROLL_WAIT  # スクロールのデフォルト値
        # カラー
        self.current_color = 0
        # イベントリスナー登録
        #self.scene.event.listners.append((EV_CHECK_HIT, self))  # 当たり判定
        self.scene.event.listners.append((gl.EV_ENTER_FRAME, self))
        self.scene.event.listners.append((EV_DELETE_LINE, self))  # ライン消去

    def set_new_line(self, x=FIELD_WIDTH - 1):
        """新しいラインを作成"""
        # 1列削除
        self.__clear_line(x)
        # 必ず1つ出現
        self.__set_new_line(x, self.current_color)

        for i in range(1, FIELD_HEIGHT - 1):
            if random.randint(0, 3) == 0:
                self.__set_new_line(x, self.current_color)

        # カラー更新
        self.current_color = (self.current_color + 1) % COLOR_MAX

    def set_new_panel(self, x, y, color):
        """新しいパネルをセット"""
        sp_x = x * PANEL_WIDTH
        sp_y = y * (PANEL_HEIGHT + PANEL_BLANK_Y)

        #debug 
        if self.fieldmap[y][x] is not None:
            print('x:%d y:%d' %(x, y))
            print('ofset:%d' %self.scroll_offset)
        #debig

        self.fieldmap[y][x] = Panel(
            self.stage,
            color + CHR_PANEL,
            "panel",
            sp_x,
            sp_y,
            2,
            PANEL_WIDTH,
            PANEL_HEIGHT,
        )
        self.fieldmap[y][x].enter()

    def check_hit_panel(self, shot_panel):
        """弾とパネルの当たり判定"""
        x = shot_panel.x // PANEL_WIDTH
        y = shot_panel.y // (PANEL_HEIGHT + PANEL_BLANK_Y)
        if x == (FIELD_WIDTH - 1) or self.fieldmap[y][x] is not None:
            self.set_new_panel(x - 1, y, shot_panel.color) # 弾を消してブロック生成
            shot_panel.leave()  # 弾削除
            self.scene.fire_panel_num -= 1
            self.__check_line(x)  # ライン消去判定

    def __clear_line(self, pos_x):
        """1列削除"""
        for i in range(FIELD_HEIGHT):
            self.fieldmap[i][pos_x] = None

    def __set_new_line(self, x, color):
        """新しいラインを作成 サブ"""
        y = random.randint(0, FIELD_HEIGHT - 1)

        if self.fieldmap[y][x] == None:
            # map にスプライトを格納
            self.set_new_panel(x, y, color)

    def __check_line(self, x):
        """1列そろったか"""
        for y in range(FIELD_HEIGHT):
            if self.fieldmap[y][x] is None:
                return
        # そろった
        for y in range(FIELD_HEIGHT):
            self.fieldmap[y][x].flash = True
        # ライン消去のイベント
        self.scene.event.post([EV_DELETE_LINE, gl.EV_PRIORITY_MID, DELETE_DELAY, self, self.fieldmap[0][x]])
        # 一定時間停止
        self.scroll_wait += SCROLL_STOP_TIME

    def __scroll_map(self):
        """フィールドマップとスプライトの更新"""
        for y in range(FIELD_HEIGHT):
            for x in range(FIELD_WIDTH - 1):
                self.fieldmap[y][x] = self.fieldmap[y][x + 1]  # 1キャラクタ分スクロール
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].base_x -= PANEL_WIDTH  # ベース座標の更新

    ### イベントリスナー
    def event_enter_frame(self, type, sender, option):
        """毎フレーム"""
        # スクロール
        self.scroll_wait -= 1
        if self.scroll_wait == 0:
            self.scroll_wait = self.scroll_wait_def
            # オフセット更新
            self.scroll_offset -= 1
            if self.scroll_offset < 0:
                self.scroll_offset = PANEL_OFFSET
                # マップを更新（スクロール）
                self.__scroll_map()
                # 新しいパネルをセット
                self.set_new_line()

        # パネルスプライトを更新
        for y in range(FIELD_HEIGHT):
            for x in range(FIELD_WIDTH):
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].x = (
                        self.fieldmap[y][x].base_x + self.scroll_offset
                    )

    def event_delete_line(self, type, sender, option):
        """ライン消去"""
        for pos in range(FIELD_WIDTH):
            if self.fieldmap[0][pos] is option:  # X座標を取得
                break

        for y in range(FIELD_HEIGHT):
            self.fieldmap[y][pos].leave()
            self.fieldmap[y][pos] = None

        # 詰める
        for y in range(FIELD_HEIGHT):
            for x in range(pos, 0, -1):
                self.fieldmap[y][x] = self.fieldmap[y][x - 1]
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].base_x += PANEL_WIDTH
        # 先頭は空
        for y in range(FIELD_HEIGHT):
            if self.fieldmap[y][0] is not None:
                self.fieldmap[y][0].leave()
                self.fieldmap[y][0] = None


class Panel(gl.Sprite):
    """パネル"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__(parent, chr_no, name, x, y, z, w, h, 1)
        # ベースのX座標
        self.base_x = x
        # 点滅
        self.flash = False
        self.flash_time = 0

    def enter(self):
        super().enter()

    def leave(self):
        super().leave()

    def action(self):
        super().action()
        # 点滅
        if self.flash:
            self.flash_time += 1
            if self.flash_time % FLASH_INTERVAL == 0:
                self.visible = not self.visible

    ### イベントリスナー


class ShotPanel(gl.Sprite):
    """自機の打ち出すパネル"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h, color):
        super().__init__(parent, chr_no, name, x, y, z, w, h, 1)
        self.base_x = x
        self.color = color

    def enter(self):
        super().enter()
        self.scene.event.listners.append((gl.EV_ENTER_FRAME, self))

    def leave(self):
        self.scene.event.remove_all_listner(self)
        super().leave()

    def action(self):
        super().action()

    ### イベントリスナー
    def event_enter_frame(self, type, sender, option):
        # 移動
        self.x += SHOT_SPEED
        # 当たり判定イベント
        if self.x % PANEL_WIDTH == 0:
            #self.scene.event.post([EV_CHECK_HIT, gl.EV_PRIORITY_HI, self, self.scene.ship])  # オプションは自機
            # イベントを出さずにここで当たり判定にする？
            self.scene.fieldmap.check_hit_panel(self)


# スプライト用イメージバッファ生成
chr_data = [
    data.ship_0,  # 自機
    data.p_0,  # パネル
    data.p_1,
    data.p_2,
    data.p_3,
    data.p_4,
    data.p_5,
    data.s_0,  # 弾
    data.s_1,
    data.s_2,
    data.s_3,
    data.s_4,
    data.s_5,
]
gl.create_image_buffers(PANEL_WIDTH, PANEL_HEIGHT, data.palet565, chr_data)

# ステータスをロード
game_status = gl.load_status()
if game_status is None:
    # デフォルト
    game_status = {'score': 0, 'hi':0, 'lines': 6, 'brightness': 2}

# キー入力 シーン共通
key_global = pl.InputKey()

# 各シーンの作成
main = MainScene("main", key_global)  # ゲーム本編
pause = PauseScene("pause", key_global)
scenes = [main, pause]

# ディレクターの作成
director = gl.Director(scenes)
# シーン実行
director.start("main")

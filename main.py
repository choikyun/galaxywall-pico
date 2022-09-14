"""GALAXY WALL PICO"""
__version__ = "1.0.0"
__author__ = "Choi Gyun 2022"

# import _thread
import random

import ease
import gamedata as dat
import picogamelib as gl
import picolcd114 as lcd

### ゲームバランス調整
_SCROLL_WAIT_NORMAL = const(3)  # スクロール ノーマル
_SCROLL_WAIT_EX = const(2)  # EXモード
_SCROLL_STOP_TIME = const(30)  # 一定時間停止
_DELETE_DELAY = const(30)  # 1列消去の遅延時間
_DEAD_INTERVAL = const(9)  # デッドラインバー減る間隔
_DEADTIME_RECOVERY = const(9)  # 時間回復量
_MAX_ITEM = const(5)  # アイテム最大数
_ITEM_INTERVAL = const(15)  # アイテム出現間隔
_FREEZE_DURATION = const(30 * 2)  # アイテム効果持続時間
_BURST_DURATION = const(30 * 5)

### オブジェクトのサイズ
_OBJ_W = const(20)
_OBJ_H = const(20)
_OBJ_BH = const(_OBJ_H + 2)

### 自機
_SHIP_MOVE_STEP = const(_OBJ_H + 2)
_SHIP_MOVE_MAX = const(_SHIP_MOVE_STEP * 5)
_SHIP_MOVE_FRAME_MAX = const(6)  # 移動にかかるフレーム数
_SHIP_FLASH_INTERVAL = const(2)

### 弾
_SHOT_PANEL_MAX = const(2)
_SHOT_SPEED = const(10)

### フィールド
_FIELD_W = const(12)
_FIELD_H = const(6)
_READY_W = const(108)
_READY_H = const(24)
_COLOR_STEP = const(3)  # 色が変わる

### スコア
_SCORE_DIGIT = const(6)
_LINE_DIGIT = const(4)

### ライン
_DEF_LINES = const(6)  # フィールド初期値

### パネル
_PANEL_OFFSET = const(20)
_PANEL_OFFSET_INIT = const(20)
_COLOR_MAX = const(6)

### バー
_DEAD_X = const(24)
_DEAD_W = const(4)
_DEAD_H = const(22)

### 点滅
_FLASH_INTERVAL = const(4)

### 画面停止演出
_STAGE_FREEZE_TIME = const(15)

### メッセージ
_READY_DURATION = const(30 * 2)
_READY_INTERVAL = const(6)

### combo メッセージ
_COMBO_DURATION = const(24)
_COMBO_INTERVAL = const(4)

### キャラクタ
_CHR_SHIP = const(0)
_CHR_SHIP_RED = const(1)
_CHR_SHIP_BLUE = const(2)
_CHR_PANEL = const(3)
_CHR_PANELX = const(9)
_CHR_FLASH = const(10)
_CHR_SHOT = const(11)
_CHR_DEADLINE = const(12)
_CHR_ITEM = const(13)
_CHR_AIM = const(15)

### ビットマップ
_BMP_TITLE = const(0)
_BMP_OVER = const(1)
_BMP_HI = const(2)
_BMP_SCORE = const(3)
_BMP_LINES = const(4)
_BMP_INFO_BRIGHT = const(5)
_BMP_READY = const(6)
_BMP_COMBO = const(7)
_BMP_NUM = const(8)
_BMP_CREDIT = const(18)
_BMP_EX = const(19)

### ポーズ画面
_SCORE_W = const(84)
_SCORE_H = const(20)
_HI_W = const(28)
_HI_H = const(20)
_LINES_W = const(76)
_LINES_H = const(20)
_INFO_BRIGHT_W = const(44)
_INFO_BRIGHT_H = const(24)

### 数字
_NUM_W = const(16)
_NUM_H = const(16)

### ゲームオーバー
_OVER_W = const(152)
_OVER_H = const(24)

### タイトル
_TITLE_W = const(240)
_TITLE_H = const(70)
_CREDIT_W = const(144)
_CREDIT_H = const(10)

### コンボ
_COMBO_W = const(88)
_COMBO_H = const(20)

### デッドライン
_MAX_DEADTIME = const(60)  # デッドライン移動までの時間
_DEADTIME_STEP = const(4)
_DEADTIME_COL_FULL = const(0b00000_111111_00000)
_DEADTIME_COL_MID = const(0b11111_111111_00000)
_DEADTIME_COL_EMPTY = const(0b11111_000000_00000)
_MAX_DEADLINE = const(6)  # デッドラインの最大値（X座標）

### アイテム
_ITEM_FREEZE = const(0)
_ITEM_BURST = const(1)
_ITEM_SPEED = const(5)

### 画面ゆれ
_SHAKE_FRAME_MAX = const(2)
_SHAKE_DELTA = const(4)

### 重なり順
_PANEL_Z = const(10)
_DEAD_Z = const(20)
_SHOT_Z = const(30)
_SHIP_Z = const(40)
_AIM_Z = const(50)
_ITEM_Z = const(60)
_MES_Z = const(70)

# イベント
_EV_CHECK_HIT = const("ev_check_hit_panel")
"""弾とパネルの当たり判定"""
_EV_DELETE_LINE = const("ev_delete_line")
"""ライン消去"""
_EV_GAMEOVER = const("ev_gameover")
"""ゲームオーバー"""
_EV_UPDATE_DEADLINE = const("ev_update_deadline")
"""デッドライン更新"""
_EV_FREEZE_START = const("ev_freeze_start")
"""ステージ停止"""
_EV_FREEZE_STOP = const("ev_freeze_stop")
"""ステージ停止解除"""

# セーブデータ
_FILENAME = const("gw100.json")


class MainScene(gl.Scene):
    """メイン"""

    def __init__(self, name, key):
        # イベントマネージャ
        event = gl.EventManager()
        # ステージ
        stage = MainStage(self, event, "stage", 0, 0, 0, lcd.LCD_W, lcd.LCD_H)
        super().__init__(name, event, stage, key)

        # イベントリスナー
        self.event.add_listner([_EV_GAMEOVER, self, True])

        # スプライト作成
        self.ship = Ship(self.stage, _CHR_SHIP, "ship", 0, 0, _SHIP_Z, _OBJ_W, _OBJ_H)
        self.deadline = DeadLine(self.stage, "deadline", _DEAD_X, 0, _DEAD_Z)
        # デッドライン更新バー
        self.deadtime_bar = gl.ShapeSprite(
            self.stage,
            [
                "RECT",
                0,
                133,
                240,
                2,
                _DEADTIME_COL_FULL,
            ],
            "deadtime-bar",
            1000,
        )
        # フィールド作成
        self.fieldmap = FieldMap(self.stage)

    def enter(self):
        """ゲームの初期化処理"""
        # イベントのクリア
        self.event.clear_queue()
        # 全てのリスナーを有効
        self.event.enable_listners()

        # ステータス
        game_status["lines"] = 0
        game_status["score"] = 0
        self.gameover = False

        # デッドタイム
        self.deadtime = 0
        self.update_deadtime_bar(_MAX_DEADTIME)
        self.deadline.x = _DEAD_X

        # フィールドマップ初期化
        self.fieldmap.init_map()

        # 自機
        self.ship.x = 0
        self.ship.y = _SHIP_MOVE_STEP * 2

        # アイテム
        self.item_num = 0

        # メッセージ表示
        BlinkMessage(
            self.stage,
            bmp_data[_BMP_READY],
            _READY_DURATION,
            _READY_INTERVAL,
            "ready",
            70,
            50,
            _MES_Z,
            0,
            0,
        )

        super().enter()

    def action(self):
        """フレーム毎のアクション 30FPS"""
        super().action()

        if self.active:
            # ポーズ
            if self.key.push & lcd.KEY_A:
                self.director.push("pause")

            if not self.gameover:
                # アイテム出現
                self.appear_item()

                # 一定時間で deadline が移動
                if self.frame_count % _DEAD_INTERVAL == 0:
                    self.update_deadtime_bar(-1)

    def appear_item(self):
        """アイテム出現"""
        if (
            self.frame_count % _ITEM_INTERVAL == 0
            and self.item_num < _MAX_ITEM
            and random.randint(0, 2) == 0
        ):
            if random.randint(0, 2) == 0:
                item_type = _ITEM_FREEZE
            else:
                item_type = _ITEM_BURST

            self.stage.item_pool.get_instance().init_params(
                self.stage,
                _CHR_ITEM,
                item_type,
                "item",
                lcd.LCD_W,
                random.randint(0, 5) * _OBJ_BH,
                _ITEM_Z,
                _OBJ_W,
                _OBJ_H,
            ).enter()
            self.item_num += 1

    def update_deadtime_bar(self, v):
        """デッドライン移動までの時間"""
        self.deadtime += v
        if self.deadtime < 0:
            self.deadtime = _MAX_DEADTIME
            # イベント発行
            self.event.post([_EV_UPDATE_DEADLINE, gl.EV_PRIORITY_MID, 0, self, None])
            self.deadline.x += _OBJ_W  # 一段移動
        elif self.deadtime > _MAX_DEADTIME:
            self.deadtime = _MAX_DEADTIME

        # カラー
        if self.deadtime > 30:
            color = _DEADTIME_COL_FULL
        elif self.deadtime > 15:
            color = _DEADTIME_COL_MID
        else:
            color = _DEADTIME_COL_EMPTY
        # バーの長さ
        w = self.deadtime * _DEADTIME_STEP
        if w > lcd.LCD_W:
            w = lcd.LCD_W

        self.deadtime_bar.shape[3] = w
        self.deadtime_bar.shape[5] = color

    # イベントリスナー
    def ev_gameover(self, type, sender, option):
        """ゲームオーバー"""
        s = self.director.push("over")


class PauseScene(gl.Scene):
    """ポーズ
    ・スコア表示
    ・LCD輝度調整
    """

    def __init__(self, name, key):
        # イベントマネージャ
        event = gl.EventManager()
        # ステージ
        stage = gl.Stage(self, event, "stage", 0, 0, 0, lcd.LCD_W, lcd.LCD_H)
        super().__init__(name, event, stage, key)

        # スプライト作成
        self.lines = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_LINES],
            "lines",
            24,
            22,
            _MES_Z,
            _LINES_W,
            _LINES_H,
        )
        self.score = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_SCORE],
            "score",
            16,
            44,
            _MES_Z,
            _SCORE_W,
            _SCORE_H,
        )
        self.hi = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_HI],
            "hi",
            72,
            66,
            _MES_Z,
            _HI_W,
            _HI_H,
        )
        self.info = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_INFO_BRIGHT],
            "info-bright",
            196,
            98,
            _MES_Z,
            _INFO_BRIGHT_W,
            _INFO_BRIGHT_H,
        )
        self.ex = gl.BitmapSprite(
            self.stage, bmp_data[_BMP_EX], "ex", 154, 104, _MES_Z, 32, 14
        )

        # 数値
        self.lines = ScoreNum(self.stage, _LINE_DIGIT, "score_num", 140, 22, _MES_Z)
        self.score = ScoreNum(self.stage, _SCORE_DIGIT, "score_num", 108, 44, _MES_Z)
        self.hi = ScoreNum(self.stage, _SCORE_DIGIT, "hi_num", 108, 66, _MES_Z)

    def enter(self):
        self.lines.set_value(game_status["lines"])
        self.score.set_value(game_status["score"])
        if game_status["mode"] == 0:
            self.hi.set_value(game_status["hi"])
        else:
            self.hi.set_value(game_status["hi_ex"])

        super().enter()

        if game_status["mode"] == 0:
            self.ex.visible = False
        else:
            self.ex.visible = True

    def action(self):
        super().action()

        if self.active:
            # ブライトネス調整
            if (
                self.key.push & lcd.KEY_UP
                and game_status["brightness"] < lcd.LCD_BRIGHTNESS_MAX - 1
            ):
                game_status["brightness"] += 1
                gl.lcd.brightness(game_status["brightness"])
                gl.save_status(game_status, _FILENAME)
            elif self.key.push & lcd.KEY_DOWN and game_status["brightness"] > 0:
                game_status["brightness"] -= 1
                gl.lcd.brightness(game_status["brightness"])
                gl.save_status(game_status, _FILENAME)

            # ポーズ解除
            if self.key.push & lcd.KEY_A:
                self.director.pop()


class OverScene(gl.Scene):
    """ゲームオーバー
    ・スコア表示
    """

    def __init__(self, name, key):
        # イベントマネージャ
        event = gl.EventManager()
        # ステージ
        stage = gl.Stage(self, event, "stage", 0, 0, 0, lcd.LCD_W, lcd.LCD_H)
        super().__init__(name, event, stage, key)

        # スプライト作成
        self.over = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_OVER],
            "over",
            42,
            12,
            _MES_Z,
            _OVER_W,
            _OVER_H,
        )
        self.lines = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_LINES],
            "lines",
            24,
            50,
            _MES_Z,
            _LINES_W,
            _LINES_H,
        )
        self.score = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_SCORE],
            "score",
            16,
            72,
            _MES_Z,
            _SCORE_W,
            _SCORE_H,
        )
        self.hi = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_HI],
            "hi",
            72,
            94,
            _MES_Z,
            _HI_W,
            _HI_H,
        )

        # 数値表示
        self.lines_num = ScoreNum(self.stage, _LINE_DIGIT, "lines_num", 140, 50, _MES_Z)
        self.score_num = ScoreNum(
            self.stage, _SCORE_DIGIT, "score_num", 108, 72, _MES_Z
        )
        self.hi_num = ScoreNum(self.stage, _SCORE_DIGIT, "hi_num", 108, 94, _MES_Z)

    def enter(self):
        if game_status["mode"] == 0:
            hi = game_status["hi"]
        else:
            hi = game_status["hi_ex"]

        if game_status["score"] > hi:
            hi = game_status["score"]

        if game_status["mode"] == 0:
            game_status["hi"] = hi
            self.hi_num.set_value(hi)
        else:
            game_status["hi_ex"] = hi
            self.hi_num.set_value(hi)
        gl.save_status(game_status, _FILENAME)

        self.lines_num.set_value(game_status["lines"])
        self.score_num.set_value(game_status["score"])
        super().enter()

    def action(self):
        super().action()

        if self.active:
            # リスタート
            if self.key.push & lcd.KEY_B:
                self.director.pop()
                self.director.pop()  # メイン画面もpop
                self.director.push("main")
            elif self.key.push & lcd.KEY_A:
                self.director.pop()
                self.director.pop()
                self.director.push("title")


class TitleScene(gl.Scene):
    """タイトル画面
    ・ハイスコア表示
    """

    def __init__(self, name, key):
        # イベントマネージャ
        event = gl.EventManager()
        # ステージ
        stage = gl.Stage(self, event, "stage", 0, 0, 0, lcd.LCD_W, lcd.LCD_H)
        super().__init__(name, event, stage, key)

        # スプライト作成
        self.title = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_TITLE],
            "title",
            0,
            20,
            _MES_Z,
            _TITLE_W,
            _TITLE_H,
        )
        self.credit = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_CREDIT],
            "choi",
            48,
            125,
            _MES_Z,
            _CREDIT_W,
            _CREDIT_H,
        )
        self.hi = gl.BitmapSprite(
            self.stage,
            bmp_data[_BMP_HI],
            "hi",
            50,
            85,
            _MES_Z,
            _HI_W,
            _HI_H,
        )
        self.ex = gl.BitmapSprite(
            self.stage, bmp_data[_BMP_EX], "ex", 208, 76, 10, 32, 14
        )
        # 数値表示
        self.hi_num = ScoreNum(self.stage, _SCORE_DIGIT, "hi_num", 90, 85, _MES_Z)
        # アニメ
        self.anime = gl.Anime("title", self.event, ease.linear)
        self.anime.attach()

    def enter(self):
        if game_status["mode"] == 0:
            self.hi_num.set_value(game_status["hi"])
        else:
            self.hi_num.set_value(game_status["hi_ex"])

        self.title.y = 20
        self.anime.start = self.title.y
        self.anime.delta = -20
        self.anime.total_frame = 10
        self.anime.play()
        super().enter()

        self.hi.visible = False
        self.hi_num.visible = False
        self.ex.visible = False

    def action(self):
        super().action()

        if self.anime.is_playing:
            self.title.y = int(self.anime.value)
        else:
            self.hi.visible = True
            self.hi_num.visible = True
            if game_status["mode"] == 1:
                self.ex.visible = True
            else:
                self.ex.visible = False

        if self.active:
            # ゲーム開始
            if self.key.push & lcd.KEY_B:
                self.anime.stop()
                self.director.pop()
                self.director.push("main")
            # モード切替
            if self.key.push & lcd.KEY_A:
                game_status["mode"] ^= 1
                if game_status["mode"] == 1:
                    self.ex.visible = True
                    self.hi_num.set_value(game_status["hi_ex"])
                else:
                    self.ex.visible = False
                    self.hi_num.set_value(game_status["hi"])


class MainStage(gl.Stage):
    """ステージ
    メイン画面用のステージ
    弾とパネルのスプライトはプールで管理.
    """

    def __init__(self, scene, event, name, x, y, z, w, h):
        super().__init__(scene, event, name, x, y, z, w, h)
        # パネルのプール
        self.panel_pool = gl.SpritePool(self, globals()["Panel"], 60)
        # ショットのプール
        self.shot_pool = gl.SpritePool(self, globals()["ShotPanel"], 4)
        # メテオ・バースト
        self.item_pool = gl.SpritePool(self, globals()["Item"], _MAX_ITEM)

        event.add_listner([_EV_UPDATE_DEADLINE, self, True])  # デッドライン更新
        event.add_listner([gl.EV_ANIME_COMPLETE, self, True])  # アニメ終了
        event.add_listner([_EV_FREEZE_START, self, True])  # フリーズ開始
        event.add_listner([_EV_FREEZE_STOP, self, True])  # フリーズ終了

        # ステージのアニメ
        self.shake_anime = gl.Anime("stage_shake", event, ease.linear)
        self.shake_anime.attach()
        # アニメのパラメータリスト
        self.shake_params = [-_SHAKE_DELTA, _SHAKE_DELTA * 2, -_SHAKE_DELTA]

    def enter(self):
        """初期化"""
        # ステージ上のスプライトを返却
        for i in range(len(self.sprite_list) - 1, -1, -1):
            if self.sprite_list[i].name in ("shot", "item"):
                self.sprite_list[i].leave()

        self.shake_index = 0
        self.shake_anime.stop()
        self.y = 0

        super().enter()

    def action(self):
        super().action()

        # アニメ中
        if self.shake_anime.is_playing:
            self.y = int(self.shake_anime.value)

    def shake(self):
        """画面をゆらす"""
        if self.shake_anime.is_playing:
            return
        self.shake_anime.start = self.y
        self.shake_anime.delta = self.shake_params[self.shake_index]
        self.shake_anime.total_frame = _SHAKE_FRAME_MAX
        self.shake_anime.play()
        self.shake_index = 1

    def ev_update_deadline(self, type, sender, option):
        """イベント:フレーム毎"""
        # 画面ゆらす
        self.shake()

    def ev_anime_complete(self, type, sender, option):
        """イベント:アニメ終了"""
        if option != "stage_shake" or self.shake_index < 1:
            return
        # 次のアニメ
        self.shake_anime.start = self.y
        self.shake_anime.delta = self.shake_params[self.shake_index]
        self.shake_anime.total_frame = _SHAKE_FRAME_MAX
        self.shake_anime.play()
        self.shake_index += 1
        if self.shake_index >= len(self.shake_params):
            self.shake_index = 0

    def ev_freeze_start(self, type, sender, option):
        """フリーズ開始"""
        self.event.disable_listners(
            [
                gl.EV_ENTER_FRAME,  # 特定のイベントをオフにする
                #_EV_UPDATE_DEADLINE,
                #_EV_GAMEOVER,
                #_EV_CHECK_HIT,
            ],
        )

    def ev_freeze_stop(self, type, sender, option):
        """フリーズ終了"""
        self.event.enable_listners(
            [
                gl.EV_ENTER_FRAME,  # 特定のイベントをオンにする
                #_EV_UPDATE_DEADLINE,
                #_EV_GAMEOVER,
                #_EV_CHECK_HIT,
            ],
        )


class Ship(gl.Sprite):
    """自機クラス"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__()
        self.init_params(parent, chr_no, name, x, y, z, w, h)

        self.aim = Aim().init_params(
            self, _CHR_AIM, "aim", 0, self.y, _AIM_Z, _OBJ_W, _OBJ_H
        )
        self.move_anime = gl.Anime("ship_move", self.event, ease.out_elastic)  # 移動アニメ
        self.move_anime.attach()  # アニメ有効化

        # イベントリスナー登録
        self.event.add_listner([gl.EV_ENTER_FRAME, self, True])

    def enter(self):
        self.fire_panel_num = 0
        self.stop_time = 0
        self.burst_time = 0
        self.flash_time = 0
        self.flash = False
        super().enter()

    def action(self):
        super().action()
        # 点滅
        if self.flash:
            self.flash_time += 1
            if self.flash_time % _SHIP_FLASH_INTERVAL == 0:
                self.visible = not self.visible

    def fire_panel(self):
        """弾発射"""
        if self.fire_panel_num >= _SHOT_PANEL_MAX:
            return

        # 移動中の場合
        if self.move_anime.is_playing:  # アニメ中
            y = self.move_anime.start + self.move_anime.delta  # 移動先の座標
        else:
            y = self.y

        # パネルを置けるか
        if self.scene.fieldmap.existsPanel(0, y):
            return
        self.fire_panel_num += 1

        # 新しい弾
        self.stage.shot_pool.get_instance().init_params(
            self.stage,
            _CHR_SHOT,
            "shot",
            0,
            y,
            _SHOT_Z,
            _OBJ_W,
            _OBJ_H,
        ).enter()
        # 連弾
        if self.burst_time > 0 and not self.scene.fieldmap.existsPanel(_OBJ_W, y):
            self.stage.shot_pool.get_instance().init_params(
                self.stage,
                _CHR_SHOT,
                "shot",
                _OBJ_W,
                y,
                _SHOT_Z,
                _OBJ_W,
                _OBJ_H,
            ).enter()

    def ev_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""
        # 上下移動
        if (
            option.repeat & lcd.KEY_UP
            and self.y > 0
            and not self.move_anime.is_playing
            and self.stop_time == 0
        ):
            # アニメセット
            self.move_anime.start = self.y
            self.move_anime.delta = -_SHIP_MOVE_STEP
            self.move_anime.total_frame = _SHIP_MOVE_FRAME_MAX
            self.move_anime.play()
        if (
            option.repeat & lcd.KEY_DOWN
            and self.y < _SHIP_MOVE_MAX
            and not self.move_anime.is_playing
            and self.stop_time == 0
        ):
            # アニメセット
            self.move_anime.start = self.y
            self.move_anime.delta = _SHIP_MOVE_STEP
            self.move_anime.total_frame = _SHIP_MOVE_FRAME_MAX
            self.move_anime.play()

        if option.repeat & lcd.KEY_LEFT:
            # 強制スクロール
            self.scene.fieldmap.scroll_wait = 1
            self.scene.update_deadtime_bar(-1)

        # 強制停止・連射
        if self.stop_time > 0:
            self.stop_time -= 1
            # 解除間際で点滅
            if self.stop_time == 30:
                self.flash = True
        elif self.burst_time > 0:
            self.burst_time -= 1
            # 解除間際で点滅
            if self.burst_time == 30:
                self.flash = True
        else:
            self.chr_no = _CHR_SHIP
            self.visible = True
            self.flash = False
            self.flash_time = 0

        # 弾発射
        if option.push & lcd.KEY_B:
            self.fire_panel()

        # 移動中
        if self.move_anime.is_playing:
            self.y = int(self.move_anime.value)


class Panel(gl.Sprite):
    """迫りくるパネル"""

    def __init__(self):
        super().__init__()

    def init_params(self, parent, chr_no, name, x, y, z, w, h):
        super().init_params(parent, chr_no, name, x, y, z, w, h)
        # ベースのX座標
        self.base_x = x
        # 点滅用
        self.flash = False
        self.flash_time = 0
        return self

    def enter(self):
        return super().enter()

    def leave(self):
        super().leave()

    def action(self):
        super().action()
        # 点滅
        if self.flash:
            self.flash_time += 1
            if self.flash_time % _FLASH_INTERVAL == 0:
                self.visible = not self.visible


class ShotPanel(gl.Sprite):
    """自機の打ち出すパネル"""

    def __init__(self):
        super().__init__()

    def enter(self):
        self.event.add_listner([gl.EV_ENTER_FRAME, self, True])
        return super().enter()

    def leave(self):
        self.event.remove_all_listner(self)
        super().leave()

    def action(self):
        super().action()

    def ev_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""
        # 移動
        if self.x % _OBJ_W == 0:
            # イベントを出さずにここで当たり判定
            self.scene.fieldmap.check_hit_panel(self)

        self.x += _SHOT_SPEED


class Aim(gl.Sprite):
    """照準"""

    def __init__(self):
        super().__init__()

    def enter(self):
        self.event.add_listner([gl.EV_ENTER_FRAME, self, True])
        return super().enter()

    def leave(self):
        self.event.remove_all_listner(self)
        super().leave()

    def action(self):
        super().action()

    def ev_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""
        if self.scene.ship.move_anime.is_playing:  # アニメ中
            mv = self.scene.ship.move_anime
            y = (mv.start + mv.delta) // _OBJ_BH  # 移動先の座標
        else:
            y = self.scene.ship.y // _OBJ_BH

        mp = self.scene.fieldmap.fieldmap
        offset = self.scene.fieldmap.scroll_offset
        pos = _FIELD_W - 1
        for x in range(_FIELD_W):
            if mp[y][x] is not None and mp[y][x].chr_no < _CHR_FLASH:
                pos = x - 1
                break
        # X座標更新
        if pos < (_FIELD_W - 1):
            self.x = pos * _OBJ_W + offset
        else:
            self.x = pos * _OBJ_W


class Item(gl.Sprite):
    """アイテム
    メテオ：
        一定時間停止
    バースト；
        一定時間連弾
    """

    def __init__(self):
        super().__init__()

    def init_params(self, parent, chr_no, item_type, name, x, y, z, w, h):
        super().init_params(parent, chr_no, name, x, y, z, w, h)
        self.item_type = item_type
        super().init_frame_param(2, 4)  # フレームアニメ
        return self

    def enter(self):
        self.event.add_listner([gl.EV_ENTER_FRAME, self, True])
        return super().enter()

    def leave(self):
        self.event.remove_all_listner(self)
        super().leave()

    def action(self):
        super().action()

    # イベントリスナー
    def ev_enter_frame(self, type, sender, option):
        self.x -= _ITEM_SPEED

        # 当たり判定 上書きになる
        if self.x < _OBJ_W and self.scene.ship.y == self.y:
            self.scene.ship.flash = False
            self.scene.ship.visible = True

            if self.item_type == _ITEM_FREEZE:  # 停止
                self.scene.ship.stop_time = _FREEZE_DURATION
                self.scene.ship.burst_time = 0
                self.scene.ship.chr_no = _CHR_SHIP_RED
            else:  # バースト
                self.scene.ship.burst_time = _BURST_DURATION
                self.scene.ship.stop_time = 0
                self.scene.ship.chr_no = _CHR_SHIP_BLUE

            self.scene.ship.flash = False
            self.scene.ship.flash_time = 0
            self.scene.item_num -= 1
            self.stage.shake()

            # 画面フリーズ演出
            self.stage.event.post(
                [
                    _EV_FREEZE_START,
                    gl.EV_PRIORITY_HI,
                    0,
                    self,
                    None,
                ]
            )
            self.stage.event.post(
                [
                    _EV_FREEZE_STOP,
                    gl.EV_PRIORITY_HI,
                    _STAGE_FREEZE_TIME,
                    self,
                    None,
                ]
            )
            self.leave()
        elif self.x < 0:
            self.scene.item_num -= 1
            self.leave()


class DeadLine(gl.SpriteContainer):
    """デッドライン"""

    def __init__(self, parent, name, x, y, z):
        super().__init__()
        self.init_params(parent, name, x, y, z)
        self.lines = []
        for i in range(6):
            sp = gl.Sprite().init_params(
                self,
                _CHR_DEADLINE,
                "deadline",
                0,
                i * _DEAD_H,
                _DEAD_Z,
                _DEAD_W,
                _DEAD_H,
            )
            self.lines.append(sp)

    def enter(self):
        return super().enter()

    def leave(self):
        super().leave()

    def action(self):
        super().action()


class BlinkMessage(gl.BitmapSprite):
    """点滅メッセージ表示
    一定期間で消える

    Attributes:
        duration (int): 表示時間
        interval (int): 点滅間隔 0の時は点滅しない
    """

    def __init__(self, parent, bitmap, duration, interval, name, x, y, z, w, h):
        super().__init__(parent, bitmap, name, x, y, z, w, h)
        self.duration = duration
        self.interval = interval

    def enter(self):
        return super().enter()

    def leave(self):
        self.visible = False
        super().leave()

    def action(self):
        super().action()

        if self.interval != 0 and self.duration % self.interval == 0:
            self.visible = not self.visible

        # 一定時間で消える
        self.duration -= 1
        if self.duration == 0:
            self.leave()


class ScoreNum(gl.SpriteContainer):
    """スコア表示
    子スプライトが数字を表示
    """

    def __init__(self, parent, digit, name, x, y, z):
        super().__init__()
        self.init_params(parent, name, x, y, z)
        self.digit = digit

        # 子スプライト
        self.scores = []
        for i in range(digit):
            # 桁数分の数字スプライト
            num = gl.BitmapSprite(
                self,
                bmp_data[_BMP_NUM],
                "num",
                i * (_NUM_W),
                2,
                100,
                _NUM_W,
                _NUM_H,
            )
            self.scores.append(num)

    def enter(self):
        super().enter()

    def set_value(self, val):
        """数値をセット"""
        for i in range(self.digit):
            s = val
            for d in range(self.digit - i - 1):
                s //= 10
            self.scores[i].set_bitmap(bmp_data[_BMP_NUM + (s % 10)])


class FieldMap:
    """フィールドマップの管理"""

    def __init__(self, stage):
        self.stage = stage
        self.scene = stage.scene
        # イベントリスナー登録
        self.stage.event.add_listner([gl.EV_ENTER_FRAME, self, True])
        self.stage.event.add_listner([_EV_DELETE_LINE, self, True])  # ライン消去
        self.stage.event.add_listner([_EV_UPDATE_DEADLINE, self, True])  # デッドライン更新

        # フィールドマップ パネルの配置 2次元マップ
        self.fieldmap = [[None for i in range(_FIELD_W)] for j in range(_FIELD_H)]

    def init_map(self):
        # スクロールのオフセット ドット単位で移動するため
        self.scroll_offset = _PANEL_OFFSET_INIT
        self.scroll_wait = _SCROLL_WAIT_NORMAL
        if game_status["mode"] == 0:
            self.scroll_wait_def = _SCROLL_WAIT_NORMAL  # スクロールのデフォルト値
        else:
            self.scroll_wait_def = _SCROLL_WAIT_EX  # スクロールのデフォルト値

        # カラー
        self.current_color = 0
        # ライン
        self.line_count = 0
        # コンボ
        self.combo = 0
        # ここまで来たらゲームオーバー
        self.deadline = 1

        # フィールド初期化
        self.clear()
        for i in range(_DEF_LINES):
            self.set_new_line(_FIELD_W - _DEF_LINES + i)

    def existsPanel(self, x, y):
        """パネルが存在するか

        Params:
            x (int): X座標
            y (int): Y座標

        Returns:
            (bool): 存在するか
        """
        px = x // _OBJ_W
        py = y // _OBJ_BH
        if self.fieldmap[py][px] is not None:
            return True
        else:
            return False

    def existsPanels(self, x):
        """パネルが存在するか 1列分判定

        Params:
            x (int): X座標

        Returns:
            (bool): 存在するか
        """
        px = x // _OBJ_W
        for y in range(_FIELD_H):
            if self.fieldmap[y][px] is not None:
                return True

        return False

    def clear(self):
        """マップをクリア
        スプライトは回収
        """
        for y in range(_FIELD_H):
            for x in range(_FIELD_W):
                p = self.fieldmap[y][x]
                if p is not None:
                    p.leave()
                    self.fieldmap[y][x] = None

    def set_new_line(self, x=_FIELD_W - 1):
        """新しいラインを作成

        Params:
            x (int): X座標
        """
        # 1列削除
        self.clear_line(x)

        count = random.randint(2, 4)
        for y in range(count):
            self.set_new_panel(x, y, self.current_color)
        # シャッフルする
        self.shuffle(x)

        # ライン更新
        self.line_count += 1
        # カラー更新
        if self.line_count % _COLOR_STEP == 0:
            self.current_color = (self.current_color + 1) % _COLOR_MAX

    def set_new_panel(self, x, y, color):
        """新しいパネルをセット

        Params:
            x (int): X座標
            y (int): Y座標
            color (int): カラー
        """
        sp_x = x * _OBJ_W
        sp_y = y * _OBJ_BH
        self.fieldmap[y][x] = (
            self.stage.panel_pool.get_instance()
            .init_params(
                self.stage,
                color + _CHR_PANEL,
                "panel",
                sp_x,
                sp_y,
                _PANEL_Z,
                _OBJ_W,
                _OBJ_H,
            )
            .enter()
        )

    def check_hit_panel(self, shot_panel):
        """弾とパネルの当たり判定
        フラッシュ中のパネルは通過する.

        Params:
            shot_panel (ShotPanel): スプライト
        """
        x = shot_panel.x // _OBJ_W
        y = shot_panel.y // _OBJ_BH
        hit = False

        # 端まで行った or ひとつ先
        if (
            x == (_FIELD_W - 1)
            or self.fieldmap[y][x + 1] is not None
            and self.fieldmap[y][x + 1].chr_no < _CHR_FLASH
        ):
            hit = True
        # 直下
        p = self.fieldmap[y][x]
        if p is not None and p.chr_no < _CHR_FLASH:
            hit = True

        if hit:
            # 実際にパネルを置ける場所を探す
            for px in range(x, -1, -1):
                if self.fieldmap[y][px] is None:
                    break

            self.set_new_panel(
                px,
                y,
                self.get_panel_color(px),
            )  # パネル生成
            shot_panel.leave()  # プールに返却

            self.scene.ship.fire_panel_num -= 1
            self.check_line(px, shot_panel.y)  # ライン消去判定

    def shuffle(self, x):
        """1列まぜる

        Params:
            x (int): X座標
        """
        for i in range(_FIELD_H):
            y = random.randint(0, _FIELD_H - 1)
            self.fieldmap[i][x], self.fieldmap[y][x] = (
                self.fieldmap[y][x],
                self.fieldmap[i][x],
            )
        # Y座標決定
        for y in range(_FIELD_H):
            p = self.fieldmap[y][x]
            if p is not None:
                p.y = y * _OBJ_BH

    def get_panel_color(self, x):
        """パネルの色を取得
        無効な弾はグレー

        Params:
            x (int): X座標
        """
        for y in range(_FIELD_H):
            p = self.fieldmap[y][x]
            if p is not None:
                return p.chr_no - _CHR_PANEL
        # 見つからない場合はグレー
        return _CHR_PANELX - _CHR_PANEL

    def clear_line(self, pos_x):
        """1列削除

        Params:
            pos_x (int): X座標
        """
        for i in range(_FIELD_H):
            self.fieldmap[i][pos_x] = None

    def check_line(self, x, shot_y):
        """1列そろったか

        Params:
            x (int): X座標
            shot_y (int): ショットのY座標
        """
        for y in range(_FIELD_H):
            if self.fieldmap[y][x] is None:
                return

        for y in range(_FIELD_H):
            p = self.fieldmap[y][x]
            p.flash = True
            if p.chr_no < _CHR_PANELX:
                p.chr_no = _CHR_FLASH

        # ライン消去のイベント
        self.stage.event.post(
            [
                _EV_DELETE_LINE,
                gl.EV_PRIORITY_MID,
                _DELETE_DELAY,
                self,
                self.fieldmap[0][x],
            ]
        )
        # 一定時間停止
        self.scroll_wait += _SCROLL_STOP_TIME

        # スコア可算 グレーパネルは無効
        if self.fieldmap[0][x].chr_no == _CHR_FLASH:
            self.combo += 1
            if self.combo > 1:
                combo_x = x * _OBJ_W + 22
                if combo_x > lcd.LCD_W - _COMBO_W:
                    combo_x = lcd.LCD_W - _COMBO_W

                # メッセージ表示
                BlinkMessage(
                    self.stage,
                    bmp_data[_BMP_COMBO],
                    _COMBO_DURATION,
                    _COMBO_INTERVAL,
                    "combo",
                    combo_x,
                    shot_y,
                    _MES_Z,
                    0,
                    0,
                ).enter()
            # スコア　パネルの位置 * デッドラインの位置 * コンボ数
            game_status["score"] += (_FIELD_W - x) * self.deadline * self.combo * 10
            # ライン可算
            game_status["lines"] += 1
            # デッドラインタイム回復
            self.scene.update_deadtime_bar(self.combo * _DEADTIME_RECOVERY)

    def scroll_map(self):
        """フィールドマップとスプライトの更新"""
        for y in range(_FIELD_H):
            for x in range(_FIELD_W - 1):
                self.fieldmap[y][x] = self.fieldmap[y][x + 1]  # 1キャラクタ分スクロール
                p = self.fieldmap[y][x]
                if p is not None:
                    p.base_x -= _OBJ_W  # ベース座標の更新

    def check_over(self):
        """ゲームオーバー判定

        Returns:
            (bool): ゲームオーバーか
        """
        for x in range(self.deadline, -1, -1):
            for y in range(_FIELD_H):
                if (
                    self.fieldmap[y][x] is not None
                    and self.fieldmap[y][x].chr_no < _CHR_FLASH
                ):
                    # イベント発行
                    self.stage.event.post(
                        [
                            _EV_GAMEOVER,
                            gl.EV_PRIORITY_HI,
                            60,  # タイムラグ
                            self,
                            None,
                        ]
                    )
                    # ゲームオーバー処理以外のリスナーをオフにする
                    self.stage.event.disable_listners(
                        None,
                        [
                            _EV_GAMEOVER,
                            gl.EV_ANIME_ENTER_FRAME,
                            gl.EV_ANIME_COMPLETE,
                        ],
                    )
                    # シーンのフラグ
                    self.scene.gameover = True
                    return True
        return False

    # イベントリスナー
    def ev_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""
        # スクロール
        self.scroll_wait -= 1
        if self.scroll_wait == 0:
            self.scroll_wait = self.scroll_wait_def

            # オフセット更新
            self.scroll_offset -= 1
            if self.scroll_offset == 0:
                self.scroll_offset = _PANEL_OFFSET
                # ゲームオーバー
                if self.check_over():
                    return

                # スクロールできない
                if self.existsPanels(0):
                    return

                # マップを更新（スクロール）
                self.scroll_map()
                # 新しいパネルをセット
                self.set_new_line()

        # パネルスプライトを更新
        for y in range(_FIELD_H):
            for x in range(_FIELD_W):
                p = self.fieldmap[y][x]
                if p is not None:
                    p.x = p.base_x + self.scroll_offset

    def ev_delete_line(self, type, sender, option):
        """イベント:ライン消去"""
        for pos in range(_FIELD_W):
            p = self.fieldmap[0][pos]
            if p is option:  # X座標を取得
                chr_no = p.chr_no
                break

        # 1列削除
        for y in range(_FIELD_H):
            self.fieldmap[y][pos].leave()
            self.fieldmap[y][pos] = None

        # 詰める
        for y in range(_FIELD_H):
            for x in range(pos, 0, -1):
                self.fieldmap[y][x] = self.fieldmap[y][x - 1]
                p = self.fieldmap[y][x]
                if p is not None:
                    p.base_x += _OBJ_W

        # 先頭は空
        for y in range(_FIELD_H):
            if self.fieldmap[y][0] is not None:
                self.fieldmap[y][0] = None

        # コンボひとつ終了
        if chr_no == _CHR_FLASH:
            self.combo -= 1

    def ev_update_deadline(self, type, sender, option):
        """イベント:デッドライン更新"""
        if self.deadline < _MAX_DEADLINE:
            self.deadline += 1
            # ゲームオーバー判定
            if self.scroll_offset == 0:
                self.check_over()


# インデックスカラースプライト
chr_data = (
    [
        (dat.ship_0, 20, 20),  # 自機
        (dat.ship_red, 20, 20),  # 自機 状態異常
        (dat.ship_blue, 20, 20),  # 自機 状態異常
        (dat.p_0, 20, 20),  # パネル
        (dat.p_1, 20, 20),
        (dat.p_2, 20, 20),
        (dat.p_3, 20, 20),
        (dat.p_4, 20, 20),
        (dat.p_5, 20, 20),
        (dat.p_x, 20, 20),  # グレーパネル
        (dat.p_flash, 20, 20),  # フラッシュ
        (dat.s_0, 20, 20),  # 弾
        (dat.deadline, 4, 22),  # dead line
        (dat.item_0, 20, 20),  # アイテム
        (dat.item_1, 20, 20),
        (dat.aim, 20, 20),  # 照準
    ]
)
# イメージバッファ生成
gl.create_image_buffers(dat.palette565, chr_data)

# ビットマップスプライト
bmp_data = (
    [
        (dat.title, 240, 70),
        (dat.gameover, 152, 24),
        (dat.hi, 24, 20),
        (dat.score, 80, 20),
        (dat.lines, 72, 20),
        (dat.info_bright, 48, 24),
        (dat.ready, 96, 24),
        (dat.combo, 88, 20),
        (dat.num_0, 16, 16),
        (dat.num_1, 16, 16),
        (dat.num_2, 16, 16),
        (dat.num_3, 16, 16),
        (dat.num_4, 16, 16),
        (dat.num_5, 16, 16),
        (dat.num_6, 16, 16),
        (dat.num_7, 16, 16),
        (dat.num_8, 16, 16),
        (dat.num_9, 16, 16),
        (dat.credit, 144, 10),
        (dat.ex, 32, 14),
    ]
)

# ステータスをロード
game_status = gl.load_status(_FILENAME)

if game_status is None:
    # デフォルト
    game_status = {"mode": 0, "score": 0, "hi_ex": 0, "hi": 0, "lines": 0, "brightness": 2}
    gl.save_status(game_status, _FILENAME)

# LCDの明るさ
gl.lcd.brightness(game_status["brightness"])

# キー入力 シーン共通
key_global = lcd.InputKey()

# 各シーンの作成
title = TitleScene("title", key_global)
main = MainScene("main", key_global)
pause = PauseScene("pause", key_global)
over = OverScene("over", key_global)
scenes = [main, pause, over, title]

# 描画スレッド
# _thread.start_new_thread(gl.thread_send_buf_to_lcd, ())

# ディレクターの作成
director = gl.Director(scenes)
# シーン実行
director.push("title")
director.play()

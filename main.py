"""GALAXY WALL PICO"""
__version__ = "1.0.0"
__author__ = "Choi Gyun 2022"

import _thread
import machine
import micropython
import random
import gc

import ease
import gamedata as dat
import picogamelib as gl
import picolcd114 as lcd
import constants as cons

gc.collect()
# micropython.mem_info()
# print('-----------------------------')
# print('Initial free: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
# print('-----------------------------')
# micropython.mem_info(1)


# -----------------------------------------------------
# シーン
# -----------------------------------------------------
class MainScene(gl.Scene):
    """メイン"""

    def __init__(self, name, key):
        # イベントマネージャ
        event = gl.EventManager()
        # ステージ
        stage = MainStage(self, event, "stage", 0, 0, 0, lcd.LCD_W, lcd.LCD_H)
        super().__init__(name, event, stage, key)

        # イベントリスナー
        self.event.add_listner([cons.EV_GAMEOVER, self, True])

        # スプライト作成
        self.ship = Ship(
            self.stage, cons.CHR_SHIP, "ship", 0, 0, cons.SHIP_Z, cons.OBJ_W, cons.OBJ_H
        )
        self.deadline = DeadLine(self.stage, "deadline", cons.DEAD_X, 0, cons.DEAD_Z)
        # デッドライン更新バー
        self.deadtime_bar = gl.ShapeSprite(
            self.stage,
            [
                "RECT",
                0,
                133,
                240,
                2,
                cons.DEADTIME_COL_FULL,
            ],
            "deadtime-bar",
            1000,
        )
        # フィールド作成
        self.fieldmap = FieldMap(self.stage, cons.FIELD_W, cons.FIELD_H)

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
        self.update_deadtime_bar(cons.MAX_DEADTIME)
        self.deadline.x = cons.DEAD_X

        # フィールドマップ初期化
        self.fieldmap.init_map()

        # 自機
        self.ship.x = 0
        self.ship.y = cons.SHIP_MOVE_STEP * 2

        # アイテム
        self.item_num = 0

        # メッセージ表示
        BlinkMessage(
            self.stage,
            bmp_data[cons.BMP_READY],
            cons.READY_DURATION,
            cons.READY_INTERVAL,
            "ready",
            70,
            50,
            cons.MES_Z,
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
                if self.frame_count % cons.DEAD_INTERVAL == 0:
                    self.update_deadtime_bar(-1)

    def appear_item(self):
        """アイテム出現"""
        if (
            self.frame_count % cons.ITEM_INTERVAL == 0
            and self.item_num < cons.MAX_ITEM
            and random.randint(0, 2) == 0
        ):
            if random.randint(0, 2) == 0:
                item_type = cons.ITEM_FREEZE
            else:
                item_type = cons.ITEM_BURST

            self.stage.item_pool.get_instance().init_params(
                self.stage,
                cons.CHR_ITEM,
                item_type,
                "item",
                lcd.LCD_W,
                random.randint(0, 5) * cons.OBJ_BH,
                cons.ITEM_Z,
                cons.OBJ_W,
                cons.OBJ_H,
            ).enter()
            self.item_num += 1

    def update_deadtime_bar(self, v):
        """デッドライン移動までの時間"""
        self.deadtime += v
        if self.deadtime < 0:
            self.deadtime = cons.MAX_DEADTIME
            # イベント発行
            self.event.post(
                [cons.EV_UPDATE_DEADLINE, gl.EV_PRIORITY_MID, 0, self, None]
            )
            self.deadline.x += cons.OBJ_W  # 一段移動
        elif self.deadtime > cons.MAX_DEADTIME:
            self.deadtime = cons.MAX_DEADTIME

        # カラー
        if self.deadtime > 30:
            color = cons.DEADTIME_COL_FULL
        elif self.deadtime > 15:
            color = cons.DEADTIME_COL_MID
        else:
            color = cons.DEADTIME_COL_EMPTY
        # バーの長さ
        w = self.deadtime * cons.DEADTIME_STEP
        if w > lcd.LCD_W:
            w = lcd.LCD_W

        self.deadtime_bar.shape[3] = w
        self.deadtime_bar.shape[5] = color

    # イベントリスナー
    def event_gameover(self, type, sender, option):
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
            bmp_data[cons.BMP_LINES],
            "lines",
            24,
            22,
            cons.MES_Z,
            cons.LINES_W,
            cons.LINES_H,
        )
        self.score = gl.BitmapSprite(
            self.stage,
            bmp_data[cons.BMP_SCORE],
            "score",
            16,
            44,
            cons.MES_Z,
            cons.SCORE_W,
            cons.SCORE_H,
        )
        self.hi = gl.BitmapSprite(
            self.stage,
            bmp_data[cons.BMP_HI],
            "hi",
            72,
            66,
            cons.MES_Z,
            cons.HI_W,
            cons.HI_H,
        )
        self.info = gl.BitmapSprite(
            self.stage,
            bmp_data[cons.BMP_INFO_BRIGHT],
            "info-bright",
            196,
            98,
            cons.MES_Z,
            cons.INFO_BRIGHT_W,
            cons.INFO_BRIGHT_H,
        )
        self.ex = gl.BitmapSprite(
            self.stage, bmp_data[cons.BMP_EX], "ex", 154, 104, cons.MES_Z, 32, 14
        )

        # 数値
        self.lines = ScoreNum(
            self.stage, cons.LINE_DIGIT, "score_num", 108, 22, cons.MES_Z
        )
        self.score = ScoreNum(
            self.stage, cons.SCORE_DIGIT, "score_num", 108, 44, cons.MES_Z
        )
        self.hi = ScoreNum(self.stage, cons.SCORE_DIGIT, "hi_num", 108, 66, cons.MES_Z)

    def enter(self):
        self.lines.set_value(game_status["lines"])
        self.score.set_value(game_status["score"])
        self.hi.set_value(game_status["hi"])
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
                gl.save_status(game_status)
            elif self.key.push & lcd.KEY_DOWN and game_status["brightness"] > 0:
                game_status["brightness"] -= 1
                gl.lcd.brightness(game_status["brightness"])
                gl.save_status(game_status)

            # ポーズ解除
            if self.key.push & lcd.KEY_A:
                self.director.pop()

            # リセット
            if self.key.push == (lcd.KEY_B | lcd.KEY_CENTER):
                machine.reset()


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
            bmp_data[cons.BMP_OVER],
            "over",
            42,
            12,
            cons.MES_Z,
            cons.OVER_W,
            cons.OVER_H,
        )
        self.lines = gl.BitmapSprite(
            self.stage,
            bmp_data[cons.BMP_LINES],
            "lines",
            24,
            50,
            cons.MES_Z,
            cons.LINES_W,
            cons.LINES_H,
        )
        self.score = gl.BitmapSprite(
            self.stage,
            bmp_data[cons.BMP_SCORE],
            "score",
            16,
            72,
            cons.MES_Z,
            cons.SCORE_W,
            cons.SCORE_H,
        )
        self.hi = gl.BitmapSprite(
            self.stage,
            bmp_data[cons.BMP_HI],
            "hi",
            72,
            94,
            cons.MES_Z,
            cons.HI_W,
            cons.HI_H,
        )

        # 数値表示
        self.lines_num = ScoreNum(
            self.stage, cons.LINE_DIGIT, "lines_num", 108, 50, cons.MES_Z
        )
        self.score_num = ScoreNum(
            self.stage, cons.SCORE_DIGIT, "score_num", 108, 72, cons.MES_Z
        )
        self.hi_num = ScoreNum(
            self.stage, cons.SCORE_DIGIT, "hi_num", 108, 94, cons.MES_Z
        )

    def enter(self):
        if game_status["score"] > game_status["hi"]:
            game_status["hi"] = game_status["score"]
            gl.save_status(game_status)

        self.lines_num.set_value(game_status["lines"])
        self.score_num.set_value(game_status["score"])
        self.hi_num.set_value(game_status["hi"])
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
            bmp_data[cons.BMP_TITLE],
            "title",
            0,
            20,
            cons.MES_Z,
            cons.TITLE_W,
            cons.TITLE_H,
        )
        self.credit = gl.BitmapSprite(
            self.stage,
            bmp_data[cons.BMP_CREDIT],
            "choi",
            48,
            125,
            cons.MES_Z,
            cons.CREDIT_W,
            cons.CREDIT_H,
        )
        self.hi = gl.BitmapSprite(
            self.stage,
            bmp_data[cons.BMP_HI],
            "hi",
            50,
            85,
            cons.MES_Z,
            cons.HI_W,
            cons.HI_H,
        )
        self.ex = gl.BitmapSprite(
            self.stage, bmp_data[cons.BMP_EX], "ex", 208, 76, 10, 32, 14
        )
        # 数値表示
        self.hi_num = ScoreNum(
            self.stage, cons.SCORE_DIGIT, "hi_num", 90, 85, cons.MES_Z
        )
        # アニメ
        self.anime = gl.Anime("title", self.event, ease.linear)
        self.anime.attach()

    def enter(self):
        self.hi_num.set_value(game_status["hi"])
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
                else:
                    self.ex.visible = False


# -----------------------------------------------------
# ステージ
# -----------------------------------------------------
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
        self.item_pool = gl.SpritePool(self, globals()["Item"], cons.MAX_ITEM)

        event.add_listner([cons.EV_UPDATE_DEADLINE, self, True])  # デッドライン更新
        event.add_listner([gl.EV_ANIME_COMPLETE, self, True])  # アニメ終了

        # ステージのアニメ
        self.shake_anime = gl.Anime("stage_shake", event, ease.linear)
        self.shake_anime.attach()
        # アニメのパラメータリスト
        self.shake_params = [-cons.SHAKE_DELTA, cons.SHAKE_DELTA * 2, -cons.SHAKE_DELTA]

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
        self.shake_anime.total_frame = cons.SHAKE_FRAME_MAX
        self.shake_anime.play()
        self.shake_index = 1

    def event_update_deadline(self, type, sender, option):
        """イベント:フレーム毎"""
        # 画面ゆらす
        self.shake()

    def event_anime_complete(self, type, sender, option):
        """イベント:アニメ終了"""
        if option != "stage_shake" or self.shake_index < 1:
            return
        # 次のアニメ
        self.shake_anime.start = self.y
        self.shake_anime.delta = self.shake_params[self.shake_index]
        self.shake_anime.total_frame = cons.SHAKE_FRAME_MAX
        self.shake_anime.play()
        self.shake_index += 1
        if self.shake_index >= len(self.shake_params):
            self.shake_index = 0


# -----------------------------------------------------
# スプライト
# -----------------------------------------------------
class Ship(gl.Sprite):
    """自機クラス"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__()
        self.init_params(parent, chr_no, name, x, y, z, w, h)

        self.aim = Aim().init_params(
            self, cons.CHR_AIM, "aim", 0, self.y, cons.AIM_Z, cons.OBJ_W, cons.OBJ_H
        )
        self.move_anime = gl.Anime("ship_move", self.event, ease.out_quart)  # 移動アニメ
        self.move_anime.attach()  # アニメ有効化

        # イベントリスナー登録
        self.event.add_listner([gl.EV_ENTER_FRAME, self, True])

    def enter(self):
        self.fire_panel_num = 0
        self.stop_time = 0
        self.burst_time = 0
        self.flash_time = 0
        self.flash = False
        self.key_wait = cons.KEY_WAIT
        super().enter()

    def action(self):
        super().action()
        # 点滅
        if self.flash:
            self.flash_time += 1
            if self.flash_time % cons.SHIP_FLASH_INTERVAL == 0:
                self.visible = not self.visible

    def __fire_panel(self):
        """弾発射"""
        if self.fire_panel_num >= cons.SHOT_PANEL_MAX:
            return
        if self.scene.fieldmap.existsPanel(0, self.y):
            return

        self.fire_panel_num += 1
        # 新しい弾
        self.stage.shot_pool.get_instance().init_params(
            self.stage,
            cons.CHR_SHOT,
            "shot",
            self.x,
            self.y,
            cons.SHOT_Z,
            cons.OBJ_W,
            cons.OBJ_H,
        ).enter()
        # 連弾
        if self.burst_time > 0 and self.scene.fieldmap.existsPanel(1, self.y):
            self.stage.shot_pool.get_instance().init_params(
                self.stage,
                cons.CHR_SHOT,
                "shot",
                self.x + cons.OBJ_W,
                self.y,
                cons.SHOT_Z,
                cons.OBJ_W,
                cons.OBJ_H,
            ).enter()

    def event_enter_frame(self, type, sender, option):
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
            self.move_anime.delta = -cons.SHIP_MOVE_STEP
            self.move_anime.total_frame = cons.SHIP_MOVE_FRAME_MAX
            self.move_anime.play()
        if (
            option.repeat & lcd.KEY_DOWN
            and self.y < cons.SHIP_MOVE_MAX
            and not self.move_anime.is_playing
            and self.stop_time == 0
        ):
            # アニメセット
            self.move_anime.start = self.y
            self.move_anime.delta = cons.SHIP_MOVE_STEP
            self.move_anime.total_frame = cons.SHIP_MOVE_FRAME_MAX
            self.move_anime.play()

        if option.repeat & lcd.KEY_LEFT:
            # 強制スクロール
            self.scene.fieldmap.scroll_wait = 1
            self.scene.update_deadtime_bar(-1)

        # 強制停止・連射
        if self.stop_time > 0:
            self.stop_time -= 1
            self.chr_no = cons.CHR_SHIP + 1
            # 解除間際で点滅
            if self.stop_time == 30:
                self.flash = True
        elif self.burst_time > 0:
            self.burst_time -= 1
            self.chr_no = cons.CHR_SHIP + 2
            # 解除間際で点滅
            if self.burst_time == 30:
                self.flash = True
        else:
            self.chr_no = cons.CHR_SHIP
            self.visible = True
            self.flash = False
            self.flash_time = 0

        # 弾発射
        if option.push & lcd.KEY_B and not self.move_anime.is_playing:
            self.__fire_panel()

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
            if self.flash_time % cons.FLASH_INTERVAL == 0:
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

    def event_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""
        # 移動
        if self.x % cons.OBJ_W == 0:
            # イベントを出さずにここで当たり判定
            self.scene.fieldmap.check_hit_panel(self)

        self.x += cons.SHOT_SPEED


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

    def event_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""
        y = self.scene.ship.y
        if (
            self.scene.ship.move_anime.is_playing
            and self.scene.ship.move_anime.delta > 0
        )
            y += cons.OBJ_BH # 下移動の時は補正

        y //= cons.OBJ_BH

        m = self.scene.fieldmap.fieldmap
        offset = self.scene.fieldmap.scroll_offset
        pos = cons.FIELD_W - 1
        for x in range(cons.FIELD_W):
            if m[y][x] is not None and m[y][x].chr_no < cons.CHR_FLASH:
                pos = x - 1
                break

        # X座標更新
        if pos < (cons.FIELD_W - 1):
            self.x = pos * cons.OBJ_W + offset
        else:
            self.x = pos * cons.OBJ_W


class Item(gl.Sprite):
    """メテオ・バースト
    メテオ：
        一定時間停止
    バースト；
        一定時間連射
    """

    def __init__(self):
        super().__init__()
        self.chr_flg = 0
        self.flash_time = 0

    def init_params(self, parent, chr_no, item_type, name, x, y, z, w, h):
        super().init_params(parent, chr_no, name, x, y, z, w, h)
        self.def_chr = chr_no
        self.item_type = item_type
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
    def event_enter_frame(self, type, sender, option):
        self.x -= cons.ITEM_SPEED

        # 点滅
        self.flash_time += 1
        if self.flash_time % cons.FLASH_INTERVAL == 0:
            self.chr_flg ^= 1
            self.chr_no = self.def_chr + self.chr_flg

        # 当たり判定 上書きになる
        if self.x < cons.OBJ_W and self.scene.ship.y == self.y:
            self.scene.ship.flash = False
            self.scene.ship.visible = True
            if self.item_type == cons.ITEM_FREEZE:  # 停止
                self.scene.ship.stop_time = cons.FREEZE_DURATION
                self.scene.ship.burst_time = 0
            else:  # バースト
                self.scene.ship.burst_time = cons.BURST_DURATION
                self.scene.ship.stop_time = 0

            self.scene.ship.flash = False
            self.scene.ship.flash_time = 0
            self.scene.item_num -= 1
            self.stage.shake()
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
                cons.CHR_DEADLINE,
                "deadline",
                0,
                i * cons.DEAD_H,
                cons.DEAD_Z,
                cons.DEAD_W,
                cons.DEAD_H,
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
                bmp_data[cons.BMP_NUM],
                "num",
                i * (cons.NUM_W),
                2,
                100,
                cons.NUM_W,
                cons.NUM_H,
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
            self.scores[i].set_bitmap(bmp_data[cons.BMP_NUM + (s % 10)])


# -----------------------------------------------------
# その他
# -----------------------------------------------------
class FieldMap:
    """フィールドマップの管理

    Attributes:
        stage (Stage): ステージ（スプライトのルート）
        scene (Scene): ステージの所属しているシーン
    """

    def __init__(self, stage):
        self.stage = stage
        self.scene = stage.scene
        # イベントリスナー登録
        self.stage.event.add_listner([gl.EV_ENTER_FRAME, self, True])
        self.stage.event.add_listner([cons.EV_DELETE_LINE, self, True])  # ライン消去
        self.stage.event.add_listner([cons.EV_UPDATE_DEADLINE, self, True])  # デッドライン更新

        # フィールドマップ パネルの配置 2次元マップ
        self.fieldmap = [
            [None for i in range(cons.FIELD_W)] for j in range(cons.FIELD_H)
        ]

    def init_map(self):
        # スクロールのオフセット ドット単位で移動するため
        self.scroll_offset = cons.PANEL_OFFSET_INIT
        self.scroll_wait = cons.SCROLL_WAIT_NORMAL
        if game_status["mode"] == 0:
            self.scroll_wait_def = cons.SCROLL_WAIT_NORMAL  # スクロールのデフォルト値
        else:
            self.scroll_wait_def = cons.SCROLL_WAIT_EX  # スクロールのデフォルト値

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
        for i in range(cons.DEF_LINES):
            self.set_new_line(cons.FIELD_W - cons.DEF_LINES + i)

    def existsPanel(self, x, y):
        """パネルが存在するか

        Params:
            x (int): X座標
            y (int): Y座標

        Returns:
            (bool): 存在するか
        """
        px = x // cons.OBJ_W
        py = y // cons.OBJ_BH
        if self.fieldmap[py][px] is not None:
            return True
        else:
            return False

    def existsPanels(self, x):
        """パネルが存在するか 1列分判定

        Params:
            x (int): X座標
        """
        px = x // cons.OBJ_W
        for y in range(cons.FIELD_H):
            if self.fieldmap[y][px] is not None:
                return True

        return False

    def clear(self):
        """マップをクリア
        スプライトは回収
        """
        for y in range(cons.FIELD_H):
            for x in range(cons.FIELD_W):
                p = self.fieldmap[y][x]
                if p is not None:
                    p.leave()  # プールに返却
                    self.fieldmap[y][x] = None

    def set_new_line(self, x=cons.FIELD_W - 1):
        """新しいラインを作成

        Params:
            x (int): X座標
        """
        # 1列削除
        self.__clear_line(x)

        count = random.randint(2, 4)
        for y in range(count):
            self.set_new_panel(x, y, self.current_color)
        # 数回シャッフルする
        self.__shuffle(x)

        # ライン更新
        self.line_count += 1
        # カラー更新
        if self.line_count % cons.COLOR_STEP == 0:
            self.current_color = (self.current_color + 1) % cons.COLOR_MAX

    def set_new_panel(self, x, y, color):
        """新しいパネルをセット

        Params:
            x (int): X座標
            y (int): Y座標
            color (int): カラー
        """
        sp_x = x * cons.OBJ_W
        sp_y = y * cons.OBJ_BH
        self.fieldmap[y][x] = (
            self.stage.panel_pool.get_instance()
            .init_params(
                self.stage,
                color + cons.CHR_PANEL,
                "panel",
                sp_x,
                sp_y,
                cons.PANEL_Z,
                cons.OBJ_W,
                cons.OBJ_H,
            )
            .enter()
        )

    def check_hit_panel(self, shot_panel):
        """弾とパネルの当たり判定
        フラッシュ中のパネルは通過する.

        Params;
            shot_panel (ShotPanel): スプライト
        """
        x = shot_panel.x // cons.OBJ_W
        y = shot_panel.y // cons.OBJ_BH
        hit = False

        # 端まで行った or ひとつ先
        if (
            x == (cons.FIELD_W - 1)
            or self.fieldmap[y][x + 1] is not None
            and self.fieldmap[y][x + 1].chr_no < cons.CHR_FLASH
        ):
            hit = True
        # 直下
        p = self.fieldmap[y][x]
        if p is not None and p.chr_no < cons.CHR_FLASH:
            hit = True

        if hit:
            # 実際にパネルを置ける場所を探す
            for px in range(x, -1, -1):
                if self.fieldmap[y][px] is None:
                    break

            self.set_new_panel(
                px,
                y,
                self.__get_panel_color(px),
            )  # パネル生成
            shot_panel.leave()  # プールに返却

            self.scene.ship.fire_panel_num -= 1
            self.__check_line(px, shot_panel.y)  # ライン消去判定

    def __shuffle(self, x):
        """1列まぜる

        Params:
            x (int): X座標
        """
        for i in range(cons.FIELD_H):
            y = random.randint(0, cons.FIELD_H - 1)
            self.fieldmap[i][x], self.fieldmap[y][x] = (
                self.fieldmap[y][x],
                self.fieldmap[i][x],
            )
        # Y座標決定
        for y in range(cons.FIELD_H):
            p = self.fieldmap[y][x]
            if p is not None:
                p.y = y * cons.OBJ_BH

    def __get_panel_color(self, x):
        """パネルの色を取得
        無効な弾はグレー

        Params:
            x (int): X座標
        """
        for y in range(cons.FIELD_H):
            p = self.fieldmap[y][x]
            if p is not None:
                return p.chr_no - cons.CHR_PANEL
        # 見つからない場合はグレー
        return cons.CHR_PANELX - cons.CHR_PANEL

    def __clear_line(self, pos_x):
        """1列削除

        Params:
            pos_x (int): X座標
        """
        for i in range(cons.FIELD_H):
            self.fieldmap[i][pos_x] = None

    def __check_line(self, x, shot_y):
        """1列そろったか

        Params:
            x (int): X座標
            shot_y (int): ショットのY座標
        """
        for y in range(cons.FIELD_H):
            if self.fieldmap[y][x] is None:
                return

        for y in range(cons.FIELD_H):
            p = self.fieldmap[y][x]
            p.flash = True
            if p.chr_no < cons.CHR_PANELX:
                p.chr_no = cons.CHR_FLASH

        # ライン消去のイベント
        self.stage.event.post(
            [
                cons.EV_DELETE_LINE,
                gl.EV_PRIORITY_MID,
                cons.DELETE_DELAY,
                self,
                self.fieldmap[0][x],
            ]
        )
        # 一定時間停止
        self.scroll_wait += cons.SCROLL_STOP_TIME

        # スコア可算 グレーパネルは無効
        if self.fieldmap[0][x].chr_no == cons.CHR_FLASH:
            self.combo += 1
            if self.combo > 1:
                combo_x = x * cons.OBJ_W + 22
                if combo_x > lcd.LCD_W - cons.COMBO_W:
                    combo_x = lcd.LCD_W - cons.COMBO_W

                # メッセージ表示
                BlinkMessage(
                    self.stage,
                    bmp_data[cons.BMP_COMBO],
                    cons.COMBO_DURATION,
                    cons.COMBO_INTERVAL,
                    "combo",
                    combo_x,
                    shot_y,
                    cons.MES_Z,
                    0,
                    0,
                ).enter()
            # スコア　パネルの位置 * デッドラインの位置 * コンボ数
            game_status["score"] += (cons.FIELD_W - x) * self.deadline * self.combo * 10
            # ライン可算
            game_status["lines"] += 1
            # デッドラインタイム回復
            self.scene.update_deadtime_bar(self.combo * cons.DEADTIME_RECOVERY)

    def __scroll_map(self):
        """フィールドマップとスプライトの更新"""
        for y in range(cons.FIELD_H):
            for x in range(cons.FIELD_W - 1):
                self.fieldmap[y][x] = self.fieldmap[y][x + 1]  # 1キャラクタ分スクロール
                p = self.fieldmap[y][x]
                if p is not None:
                    p.base_x -= cons.OBJ_W  # ベース座標の更新

    def __check_over(self):
        """ゲームオーバー判定

        Returns:
            (bool): ゲームオーバーか
        """
        for x in range(self.deadline, -1, -1):
            for y in range(cons.FIELD_H):
                if (
                    self.fieldmap[y][x] is not None
                    and self.fieldmap[y][x].chr_no < cons.CHR_FLASH
                ):
                    # イベント発行
                    self.stage.event.post(
                        [
                            cons.EV_GAMEOVER,
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
                            cons.EV_GAMEOVER,
                            gl.EV_ANIME_ENTER_FRAME,
                            gl.EV_ANIME_COMPLETE,
                        ],
                    )
                    # シーンのフラグ
                    self.scene.gameover = True
                    return True
        return False

    # イベントリスナー
    def event_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""
        # スクロール
        self.scroll_wait -= 1
        if self.scroll_wait == 0:
            self.scroll_wait = self.scroll_wait_def

            # オフセット更新
            self.scroll_offset -= 1
            if self.scroll_offset == 0:
                self.scroll_offset = cons.PANEL_OFFSET
                # ゲームオーバー
                if self.__check_over():
                    return
                # スクロールできない
                if self.existsPanels(0):
                    return

                # マップを更新（スクロール）
                self.__scroll_map()
                # 新しいパネルをセット
                self.set_new_line()

        # パネルスプライトを更新
        for y in range(cons.FIELD_H):
            for x in range(cons.FIELD_W):
                p = self.fieldmap[y][x]
                if p is not None:
                    p.x = p.base_x + self.scroll_offset

    def event_delete_line(self, type, sender, option):
        """イベント:ライン消去"""
        for pos in range(cons.FIELD_W):
            p = self.fieldmap[0][pos]
            if p is option:  # X座標を取得
                chr_no = p.chr_no
                break

        # 1列削除
        for y in range(cons.FIELD_H):
            self.fieldmap[y][pos].leave()
            self.fieldmap[y][pos] = None

        # 詰める
        for y in range(cons.FIELD_H):
            for x in range(pos, 0, -1):
                self.fieldmap[y][x] = self.fieldmap[y][x - 1]
                p = self.fieldmap[y][x]
                if p is not None:
                    p.base_x += cons.OBJ_W

        # 先頭は空
        for y in range(cons.FIELD_H):
            if self.fieldmap[y][0] is not None:
                self.fieldmap[y][0] = None

        # コンボひとつ終了
        if chr_no == cons.CHR_FLASH:
            self.combo -= 1

    def event_update_deadline(self, type, sender, option):
        """イベント:デッドライン更新"""
        if self.deadline < cons.MAX_DEADLINE:
            self.deadline += 1
            # ゲームオーバー判定
            self.__check_over()


# インデックスカラースプライト
chr_data = [
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
# イメージバッファ生成
gl.create_image_buffers(dat.palette565, chr_data)

# ビットマップスプライト
bmp_data = [
    (dat.title, 240, 70),
    (dat.gameover, 152, 24),
    (dat.hi, 24, 20),
    (dat.score, 80, 20),
    (dat.lines, 72, 20),
    (dat.info_bright, 48, 24),
    (dat.ready, 96, 24),
    (dat.combo, 88, 20),
    (dat.num_0, 16, 16),  # 数字
    (dat.num_1, 16, 16),
    (dat.num_2, 16, 16),
    (dat.num_3, 16, 16),
    (dat.num_4, 16, 16),
    (dat.num_5, 16, 16),
    (dat.num_6, 16, 16),
    (dat.num_7, 16, 16),
    (dat.num_8, 16, 16),
    (dat.num_9, 16, 16),
    (dat.credit, 144, 10),  # クレジット
    (dat.ex, 32, 14),  # EX
]

# ステータスをロード
game_status = gl.load_status()

if game_status is None:
    # デフォルト
    game_status = {"mode": 0, "score": 0, "hi": 0, "lines": 0, "brightness": 2}
    gl.save_status(game_status)

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


# 描画スレッド実行
# _thread.start_new_thread(gl.thread_send_buf_to_lcd, ())


# ディレクターの作成
director = gl.Director(scenes)
# シーン実行
director.push("title")
director.play()

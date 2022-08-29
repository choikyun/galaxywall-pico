"""GALAXY WALL PICO"""
__version__ = "1.0.0"
__author__ = "Choi Gyun 2022"

import machine
import random
import utime

import ease
import gamedata as data
import picogamelib as gl
import picolcd114 as pl
import constants as c


class MainScene(gl.Scene):
    """メイン"""

    def __init__(self, name, key):
        super().__init__(name)
        # ステージ
        stage = MainStage(self, "", 0, 0, 0, pl.LCD_W, pl.LCD_H)
        # イベントマネージャ
        event = gl.EventManager()
        # 登録
        self.registerStagehands(stage, event, key)
        # イベントリスナー
        event.add_listner([c.EV_GAMEOVER, self, True])

        # スプライト作成
        self.ship = Ship(stage, c.CHR_SHIP, "ship", 0, 0, c.SHIP_Z, c.SHIP_W, c.SHIP_H)
        self.deadline = DeadLine(stage, "deadline", c.DEAD_X, 0, c.DEAD_Z)
        # デッドライン更新バー
        self.deadtime_bar = gl.ShapeSprite(
            stage,
            [
                "RECT",
                0,
                133,
                240,
                2,
                c.DEADTIME_COL_FULL,
            ],
            "deadtime-bar",
            1000,
        )
        # フィールド作成
        self.fieldmap = FieldMap(stage, c.FIELD_W, c.FIELD_H)

    def enter(self):
        """ゲームの初期化処理"""
        # イベントのクリア
        self.event.clear_queue()
        # 全てのリスナーを有効
        self.event.enable_listners()

        # ステータス
        game_status["lines"] = 0
        game_status["score"] = 0
        game_status["lv"] = 1

        # デッドタイム
        self.deadtime = c.MAX_DEADTIME
        self.deadtime_bar.w = c.MAX_DEADTIME * c.DEADTIME_STEP
        self.deadtime_bar.color = c.DEADTIME_COL_FULL
        self.deadline.x = c.DEAD_X

        # フィールドマップ初期化
        self.fieldmap.init_map()

        # 自機
        self.ship.x = 0
        self.ship.y = c.SHIP_MOVE_STEP * 2

        # アイテム
        self.item_num = 0

        # メッセージ表示
        BlinkMessage(
            self.stage,
            bmp_data[c.BMP_READY],
            c.READY_DURATION,
            c.READY_INTERVAL,
            "ready",
            70,
            50,
            c.MES_Z,
            0,
            0,
        )

        super().enter()

    def action(self):
        """フレーム毎のアクション 30FPS"""
        super().action()

        if self.active:
            # ポーズ
            if self.key.push & pl.KEY_A:
                self.director.push("pause")

            # メテオ・バーストパネル
            if (
                self.frame_count % c.ITEM_INTERVAL == 0
                and self.item_num < c.MAX_ITEM
                and random.randint(0, 3) == 0
            ):
                if random.randint(0, 1) == 0:
                    chr_no = c.CHR_BURST
                else:
                    chr_no = c.CHR_METEO
                self.stage.item_pool.get_instance().init_params(
                    self.stage,
                    chr_no,
                    "item",
                    pl.LCD_W,
                    random.randint(0, 5) * (c.PANEL_H + c.PANEL_BLANK_Y),
                    c.ITEM_Z,
                    c.PANEL_W,
                    c.PANEL_H,
                ).enter()
                self.item_num += 1

            # 一定時間で deadline が移動
            if self.frame_count % c.DEAD_INTERVAL == 0:
                self.update_deadtime_bar(-1)

    def leave(self):
        """終了処理"""
        # イメージバッファ
        gl.image_buffers.clear()
        super().leave()

    def update_deadtime_bar(self, v):
        """デッドライン移動までの時間"""
        self.deadtime += v
        if self.deadtime < 0:
            self.deadtime = c.MAX_DEADTIME
            # イベント発行
            self.event.post([c.EV_UPDATE_DEADLINE, gl.EV_PRIORITY_MID, 0, self, None])
            self.deadline.x += c.SHIP_W  # 一段移動
        elif self.deadtime > c.MAX_DEADTIME:
            self.deadtime = c.MAX_DEADTIME

        # カラー
        if self.deadtime > 30:
            color = c.DEADTIME_COL_FULL
        elif self.deadtime > 15:
            color = c.DEADTIME_COL_MID
        else:
            color = c.DEADTIME_COL_EMPTY
        # バーの長さ
        w = self.deadtime * c.DEADTIME_STEP
        if w > pl.LCD_W:
            w = pl.LCD_W

        self.deadtime_bar.shape[3] = w
        self.deadtime_bar.shape[5] = color

    # イベントリスナー
    def event_gameover(self, type, sender, option):
        """ゲームオーバー"""
        self.ship.move_anime.stop()  # アニメ停止
        s = self.director.push("over")


class PauseScene(gl.Scene):
    """ポーズ
    ・スコア表示
    ・LCD輝度調整
    """

    def __init__(self, name, key):
        super().__init__(name)
        # ステージ
        stage = gl.Stage(self, "", 0, 0, 0, pl.LCD_W, pl.LCD_H)
        # イベントマネージャ
        event = gl.EventManager()
        # 登録
        self.registerStagehands(stage, event, key)

        # スプライト作成
        self.lines = gl.BitmapSprite(
            stage, bmp_data[c.BMP_LINES], "lines", 24, 22, c.MES_Z, c.LINES_W, c.LINES_H
        )
        self.score = gl.BitmapSprite(
            stage,
            bmp_data[c.BMP_SCORE],
            "score",
            16,
            44,
            c.MES_Z,
            c.SCORE_W,
            c.SCORE_H,
        )
        self.hi = gl.BitmapSprite(
            stage, bmp_data[c.BMP_HI], "hi", 72, 66, c.MES_Z, c.HI_W, c.HI_H
        )
        self.info = gl.BitmapSprite(
            stage,
            bmp_data[c.BMP_INFO_BRIGHT],
            "info-bright",
            196,
            98,
            c.MES_Z,
            c.INFO_BRIGHT_W,
            c.INFO_BRIGHT_H,
        )
        # 数値
        self.lines = ScoreNum(self.stage, c.LINE_DIGIT, "score_num", 108, 22, c.MES_Z)
        self.score = ScoreNum(self.stage, c.SCORE_DIGIT, "score_num", 108, 44, c.MES_Z)
        self.hi = ScoreNum(self.stage, c.SCORE_DIGIT, "hi_num", 108, 66, c.MES_Z)

    def enter(self):
        self.lines.set_value(game_status["lines"])
        self.score.set_value(game_status["score"])
        self.hi.set_value(game_status["hi"])
        super().enter()

    def action(self):
        super().action()

        if self.active:
            # ブライトネス調整
            if (
                self.key.push & pl.KEY_UP
                and game_status["brightness"] < pl.LCD_BRIGHTNESS_MAX - 1
            ):
                game_status["brightness"] += 1
                gl.lcd.brightness(game_status["brightness"])
                gl.save_status(game_status)
            elif self.key.push & pl.KEY_DOWN and game_status["brightness"] > 0:
                game_status["brightness"] -= 1
                gl.lcd.brightness(game_status["brightness"])
                gl.save_status(game_status)

            # ポーズ解除
            if self.key.push & pl.KEY_A:
                self.director.pop()

            # リセット
            if self.key.push == (pl.KEY_B | pl.KEY_CENTER):
                machine.reset()

    def leave(self):
        gl.image_buffers.clear()
        super().leave()


class OverScene(gl.Scene):
    """ゲームオーバー
    ・スコア表示
    """

    def __init__(self, name, key):
        super().__init__(name)
        # ステージ
        stage = gl.Stage(self, "", 0, 0, 0, pl.LCD_W, pl.LCD_H)
        # イベントマネージャ
        event = gl.EventManager()
        # 登録
        self.registerStagehands(stage, event, key)

        # スプライト作成
        self.over = gl.BitmapSprite(
            stage,
            bmp_data[c.BMP_OVER],
            "over",
            42,
            12,
            c.MES_Z,
            c.OVER_W,
            c.OVER_H,
        )
        self.lines = gl.BitmapSprite(
            stage,
            bmp_data[c.BMP_LINES],
            "lines",
            24,
            50,
            c.MES_Z,
            c.LINES_W,
            c.LINES_H,
        )
        self.score = gl.BitmapSprite(
            stage,
            bmp_data[c.BMP_SCORE],
            "score",
            16,
            72,
            c.MES_Z,
            c.SCORE_W,
            c.SCORE_H,
        )
        self.hi = gl.BitmapSprite(
            stage, bmp_data[c.BMP_HI], "hi", 72, 94, c.MES_Z, c.HI_W, c.HI_H
        )

        # 数値表示
        self.lines_num = ScoreNum(
            self.stage, c.LINE_DIGIT, "lines_num", 108, 50, c.MES_Z
        )
        self.score_num = ScoreNum(
            self.stage, c.SCORE_DIGIT, "score_num", 108, 72, c.MES_Z
        )
        self.hi_num = ScoreNum(self.stage, c.SCORE_DIGIT, "hi_num", 108, 94, c.MES_Z)

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
            # リプレイ
            if self.key.push & pl.KEY_B:
                self.director.pop()
                self.director.pop()  # メイン画面もpop
                self.director.push("main")

    def leave(self):
        super().leave()


class TitleScene(gl.Scene):
    """タイトル画面
    ・ハイスコア表示
    """

    def __init__(self, name, key):
        super().__init__(name)
        # ステージ
        stage = gl.Stage(self, "", 0, 0, 0, pl.LCD_W, pl.LCD_H)
        # イベントマネージャ
        event = gl.EventManager()
        # 登録
        self.registerStagehands(stage, event, key)

        # スプライト作成
        self.title = gl.BitmapSprite(
            stage,
            bmp_data[c.BMP_TITLE],
            "title",
            0,
            20,
            c.MES_Z,
            c.TITLE_W,
            c.TITLE_H,
        )
        self.hi = gl.BitmapSprite(
            stage, bmp_data[c.BMP_HI], "hi", 50, 85, c.MES_Z, c.HI_W, c.HI_H
        )
        self.credit = gl.BitmapSprite(
            stage,
            bmp_data[c.BMP_CREDIT],
            "credit",
            36,
            120,
            c.MES_Z,
            c.CREDIT_W,
            c.CREDIT_H,
        )

        # 数値表示
        self.hi_num = ScoreNum(self.stage, c.SCORE_DIGIT, "hi_num", 90, 85, c.MES_Z)
        # アニメ
        self.anime = gl.Anime(event, ease.linear)
        self.anime.attach()

    def enter(self):
        self.hi_num.set_value(game_status["hi"])
        self.anime.start = self.title.y
        self.anime.delta = -20
        self.anime.total_frame = 10
        self.anime.play()
        super().enter()

        self.hi.visible = False
        self.hi_num.visible = False
        self.credit.visible = False

    def action(self):
        super().action()

        if self.anime.is_playing:
            self.title.y = int(self.anime.value)
        else:
            self.hi.visible = True
            self.hi_num.visible = True
            self.credit.visible = True

        if self.active:
            # ゲーム開始
            if self.key.push & pl.KEY_B:
                self.anime.stop()
                self.director.pop()
                self.director.push("main")

    def leave(self):
        super().leave()


class MainStage(gl.Stage):
    """ステージ
    メイン画面用のステージ
    弾とパネルのスプライトはプールで管理.
    """

    def __init__(self, scene, name, x, y, z, w, h):
        super().__init__(scene, name, x, y, z, w, h)
        # パネルのプール
        self.panel_pool = gl.SpritePool(self, globals()["Panel"])
        # ショットのプール
        self.shot_pool = gl.SpritePool(self, globals()["ShotPanel"], 4)
        # メテオ・バースト
        self.item_pool = gl.SpritePool(self, globals()["Item"], c.MAX_ITEM)

    def enter(self):
        """初期化"""
        # ステージ上のスプライトを返却
        for i in range(len(self.sprite_list) - 1, -1, -1):
            if self.sprite_list[i].name == "shot" or self.sprite_list[i].name == "item":
                sp = self.sprite_list[i]
                sp.leave()

        super().enter()


class Ship(gl.Sprite):
    """自機クラス"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__()
        self.init_params(parent, chr_no, name, x, y, z, w, h)

        self.move_anime = gl.Anime(self.scene.event, ease.out_quart)  # 移動アニメ
        self.move_anime.attach()  # アニメ有効化
        # イベントリスナー登録
        self.scene.event.add_listner([gl.EV_ENTER_FRAME, self, True])

    def enter(self):
        self.fire_panel_num = 0  # 現在の発射数
        self.stop_time = 0  # 停止時間
        self.burst_time = 0  # 連射時間
        self.flash_time = 0  # 点滅
        self.flash = False
        super().enter()

    def action(self):
        super().action()
        # 点滅
        if self.flash:
            self.flash_time += 1
            if self.flash_time % c.SHIP_FLASH_INTERVAL == 0:
                self.visible = not self.visible

    def __fire_panel(self):
        """弾発射"""
        if self.fire_panel_num >= c.SHOT_PANEL_MAX:
            return
        self.fire_panel_num += 1
        # 新しい弾
        shot = (
            self.stage.shot_pool.get_instance()
            .init_params(
                self.stage,
                c.CHR_SHOT,
                "shot",
                self.x,
                self.y,
                c.SHOT_Z,
                c.SHOT_W,
                c.SHOT_H,
            )
            .enter()
        )

    # イベントリスナー
    def event_enter_frame(self, type, sender, option):
        """フレーム毎"""
        # 上下移動
        if (
            option.repeat & pl.KEY_UP
            and self.y > 0
            and not self.move_anime.is_playing
            and self.stop_time == 0
        ):
            # アニメセット
            self.move_anime.start = self.y
            self.move_anime.delta = -c.SHIP_MOVE_STEP
            self.move_anime.total_frame = c.SHIP_MOVE_FRAME_MAX
            self.move_anime.play()

        if (
            option.repeat & pl.KEY_DOWN
            and self.y < c.SHIP_MOVE_LIMIT
            and not self.move_anime.is_playing
            and self.stop_time == 0
        ):
            # アニメセット
            self.move_anime.start = self.y
            self.move_anime.delta = c.SHIP_MOVE_STEP
            self.move_anime.total_frame = c.SHIP_MOVE_FRAME_MAX
            self.move_anime.play()

        if option.repeat & pl.KEY_LEFT:
            # 強制スクロール
            self.scene.fieldmap.scroll_wait = 1
            game_status["score"] += c.FORCE_SCORE

        if option.repeat & pl.KEY_RIGHT:
            pass

        # 強制停止・連射
        if self.stop_time > 0:
            self.stop_time -= 1
            self.chr_no = c.CHR_SHIP + 1
            # 解除間際で点滅
            if self.stop_time == 30:
                self.flash = True
        elif self.burst_time > 0:
            self.burst_time -= 1
            self.chr_no = c.CHR_SHIP + 2
            # 解除間際で点滅
            if self.burst_time == 30:
                self.flash = True
        else:
            self.chr_no = c.CHR_SHIP
            self.visible = True
            self.flash = False
            self.flash_time = 0

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
        # イベントリスナー登録
        self.scene.event.add_listner([gl.EV_ENTER_FRAME, self, True])
        self.scene.event.add_listner([c.EV_DELETE_LINE, self, True])  # ライン消去
        self.scene.event.add_listner([c.EV_UPDATE_DEADLINE, self, True])  # デッドライン更新

        # フィールドマップ パネルの配置 2次元マップ
        self.fieldmap = [[None for i in range(c.FIELD_W)] for j in range(c.FIELD_H)]

    def init_map(self):
        # スクロールのオフセット ドット単位で移動するため
        self.scroll_offset = c.PANEL_OFFSET_INIT
        self.scroll_wait = c.SCROLL_WAIT
        self.scroll_wait_def = c.SCROLL_WAIT  # スクロールのデフォルト値

        # カラー
        self.current_color = 0
        # ライン
        self.line_count = 0
        # コンボ
        self.combo = 0
        # ここに来たらゲームオーバー
        self.deadline = 1

        # フィールド初期化
        self.clear()
        for i in range(c.DEF_LINES):
            self.set_new_line(c.FIELD_W - c.DEF_LINES + i)

    def clear(self):
        """マップをクリア
        スプライトは回収
        """
        for y in range(c.FIELD_H):
            for x in range(c.FIELD_W):
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].leave()  # プールに返却
                    self.fieldmap[y][x] = None

    def set_new_line(self, x=c.FIELD_W - 1):
        """新しいラインを作成"""
        # 1列削除
        self.__clear_line(x)

        count = random.randint(2, 4)
        for y in range(count):
            self.set_new_panel(x, y, self.current_color, 0)
        # 数回シャッフルする
        self.__shuffle(x)

        # ライン更新
        self.line_count += 1
        # カラー更新
        if self.line_count % c.COLOR_STEP == 0:
            self.current_color = (self.current_color + 1) % c.COLOR_MAX

    def set_new_panel(self, x, y, color, burst):
        """新しいパネルをセット"""
        sp_x = x * c.PANEL_W
        sp_y = y * (c.PANEL_H + c.PANEL_BLANK_Y)
        self.fieldmap[y][x] = (
            self.stage.panel_pool.get_instance()
            .init_params(
                self.stage,
                color + c.CHR_PANEL,
                "panel",
                sp_x,
                sp_y,
                c.PANEL_Z,
                c.PANEL_W,
                c.PANEL_H,
            )
            .enter()
        )
        if burst > 0 and x >= 0:
            # カラー取得
            color = self.__get_panel_color(x - 1)
            self.fieldmap[y][x - 1] = (
                self.stage.panel_pool.get_instance()
                .init_params(
                    self.stage,
                    color + c.CHR_PANEL,
                    "panel",
                    sp_x - c.PANEL_W,
                    sp_y,
                    c.PANEL_Z,
                    c.PANEL_W,
                    c.PANEL_H,
                )
                .enter()
            )

    def check_hit_panel(self, shot_panel):
        """弾とパネルの当たり判定
        フラッシュ中のパネルは通過する.
        """
        x = shot_panel.x // c.PANEL_W
        y = shot_panel.y // (c.PANEL_H + c.PANEL_BLANK_Y)
        hit = False

        # 端まで行った or ひとつ先
        if (
            x == (c.FIELD_W - 1)
            or self.fieldmap[y][x + 1] is not None
            and self.fieldmap[y][x + 1].chr_no < c.CHR_FLASH
        ):
            hit = True
        # 直下
        if self.fieldmap[y][x] is not None and self.fieldmap[y][x].chr_no < c.CHR_FLASH:
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
                self.scene.ship.burst_time,
            )  # パネル生成
            shot_panel.leave()  # プールに返却

            self.scene.ship.fire_panel_num -= 1
            self.__check_line(px, shot_panel.y)  # ライン消去判定
            if self.scene.ship.burst_time > 0 and px > 0:
                self.__check_line(px - 1, shot_panel.y)  # ライン消去判定

    def __shuffle(self, x):
        """1列まぜる"""
        for i in range(c.FIELD_H):
            y = random.randint(0, c.FIELD_H - 1)
            tmp = self.fieldmap[i][x]
            self.fieldmap[i][x] = self.fieldmap[y][x]
            self.fieldmap[y][x] = tmp
        # Y座標決定
        for y in range(c.FIELD_H):
            if self.fieldmap[y][x] is not None:
                self.fieldmap[y][x].y = y * (c.PANEL_H + c.PANEL_BLANK_Y)

    def __get_panel_color(self, x):
        """パネルの色を取得
        無効な弾はグレー
        """
        for y in range(c.FIELD_H):
            if self.fieldmap[y][x] is not None:
                return self.fieldmap[y][x].chr_no - c.CHR_PANEL
        # 見つからない場合はグレー
        return c.CHR_PANELX - c.CHR_PANEL

    def __clear_line(self, pos_x):
        """1列削除"""
        for i in range(c.FIELD_H):
            self.fieldmap[i][pos_x] = None

    def __check_line(self, x, shot_y):
        """1列そろったか"""
        for y in range(c.FIELD_H):
            if self.fieldmap[y][x] is None:
                return

        for y in range(c.FIELD_H):
            self.fieldmap[y][x].flash = True
            if self.fieldmap[y][x].chr_no < c.CHR_PANELX:
                self.fieldmap[y][x].chr_no = c.CHR_FLASH

        # ライン消去のイベント
        self.scene.event.post(
            [
                c.EV_DELETE_LINE,
                gl.EV_PRIORITY_MID,
                c.DELETE_DELAY,
                self,
                self.fieldmap[0][x],
            ]
        )
        # 一定時間停止
        self.scroll_wait += c.SCROLL_STOP_TIME

        # スコア可算 グレーパネルは無効
        if self.fieldmap[0][x].chr_no == c.CHR_FLASH:
            self.combo += 1
            if self.combo > 1:
                combo_x = x * c.PANEL_W + 22
                if combo_x > pl.LCD_W - c.COMBO_W:
                    compo_x = pl.LCD_W - c.COMBO_W

                # メッセージ表示
                BlinkMessage(
                    self.stage,
                    bmp_data[c.BMP_COMBO],
                    c.COMBO_DURATION,
                    0,
                    "combo",
                    combo_x,
                    shot_y,
                    c.MES_Z,
                    0,
                    0,
                ).enter()

            game_status["score"] += (c.FIELD_W - x) * self.combo * 10
            # ライン可算
            game_status["lines"] += 1
            # デッドラインタイム　少し回復
            self.scene.update_deadtime_bar(self.combo * c.DEADTIME_RECOVERY)

            # レベルアップ
            if (
                game_status["lines"]
            ) % c.LEVEL_UP_INTERVAL == 0 and self.scroll_wait_def > 1:
                self.scroll_wait_def -= 1

    def __scroll_map(self):
        """フィールドマップとスプライトの更新"""
        for y in range(c.FIELD_H):
            for x in range(c.FIELD_W - 1):
                self.fieldmap[y][x] = self.fieldmap[y][x + 1]  # 1キャラクタ分スクロール
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].base_x -= c.PANEL_W  # ベース座標の更新

    def __check_over(self):
        """ゲームオーバーか

        Returns:
            (bool): True ゲームオーバー
        """
        for y in range(c.FIELD_H):
            if self.fieldmap[y][self.deadline] is not None:
                # イベント発行
                self.scene.event.post(
                    [
                        c.EV_GAMEOVER,
                        gl.EV_PRIORITY_HI,
                        30,  # タイムラグ
                        self,
                        None,
                    ]
                )
                # ゲームオーバー処理以外のリスナーをオフにする
                self.scene.event.disable_listners(None, [c.EV_GAMEOVER])
                return True

        return False

    def __check_deadline(self):
        """デッドライン更新時のゲームオーバー判定

        Returns:
            (bool): True ゲームオーバー
        """
        for x in range(self.deadline, -1, -1):
            for y in range(c.FIELD_H):
                if self.fieldmap[y][x] is not None:
                    # イベント発行
                    self.scene.event.post(
                        [
                            c.EV_GAMEOVER,
                            gl.EV_PRIORITY_HI,
                            30,  # タイムラグ
                            self,
                            None,
                        ]
                    )
                    # ゲームオーバー処理以外のリスナーをオフにする
                    self.scene.event.disable_listners(None, [c.EV_GAMEOVER])
                    return True
        return False

    # イベントリスナー
    def event_enter_frame(self, type, sender, option):
        """毎フレーム"""
        # スクロール
        self.scroll_wait -= 1
        if self.scroll_wait == 0:
            self.scroll_wait = self.scroll_wait_def

            # オフセット更新
            self.scroll_offset -= 1
            if self.scroll_offset == 0:
                self.scroll_offset = c.PANEL_OFFSET
                # ゲームオーバー
                if self.__check_over():
                    return

                # マップを更新（スクロール）
                self.__scroll_map()
                # 新しいパネルをセット
                self.set_new_line()

        # パネルスプライトを更新
        for y in range(c.FIELD_H):
            for x in range(c.FIELD_W):
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].x = (
                        self.fieldmap[y][x].base_x + self.scroll_offset
                    )

    def event_delete_line(self, type, sender, option):
        """ライン消去"""
        for pos in range(c.FIELD_W):
            if self.fieldmap[0][pos] is option:  # X座標を取得
                chr_no = self.fieldmap[0][pos].chr_no
                break

        # 1列削除
        for y in range(c.FIELD_H):
            self.fieldmap[y][pos].leave()
            self.fieldmap[y][pos] = None

        # 詰める
        for y in range(c.FIELD_H):
            for x in range(pos, 0, -1):
                self.fieldmap[y][x] = self.fieldmap[y][x - 1]
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].base_x += c.PANEL_W

        # 先頭は空
        for y in range(c.FIELD_H):
            if self.fieldmap[y][0] is not None:
                self.fieldmap[y][0] = None

        # コンボひとつ終了
        if chr_no == c.CHR_FLASH:
            self.combo -= 1

    def event_update_deadline(self, type, sender, option):
        """デッドライン更新"""
        if self.deadline < c.MAX_DEADLINE:
            self.deadline += 1
            # ゲームオーバー判定
            self.__check_deadline()


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
            if self.flash_time % c.FLASH_INTERVAL == 0:
                self.visible = not self.visible


class ShotPanel(gl.Sprite):
    """自機の打ち出すパネル"""

    def __init__(self):
        super().__init__()

    def enter(self):
        self.scene.event.add_listner([gl.EV_ENTER_FRAME, self, True])
        return super().enter()

    def leave(self):
        self.scene.event.remove_all_listner(self)
        super().leave()

    def action(self):
        super().action()

    # イベントリスナー
    def event_enter_frame(self, type, sender, option):
        # 移動
        if self.x % c.PANEL_W == 0:
            # イベントを出さずにここで当たり判定
            self.scene.fieldmap.check_hit_panel(self)

        self.x += c.SHOT_SPEED


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

    def init_params(self, parent, chr_no, name, x, y, z, w, h):
        super().init_params(parent, chr_no, name, x, y, z, w, h)
        self.def_chr = chr_no
        return self

    def enter(self):
        self.scene.event.add_listner([gl.EV_ENTER_FRAME, self, True])
        return super().enter()

    def leave(self):
        self.scene.event.remove_all_listner(self)
        super().leave()

    def action(self):
        super().action()

    # イベントリスナー
    def event_enter_frame(self, type, sender, option):
        self.x -= c.ITEM_SPEED

        # 点滅
        self.flash_time += 1
        if self.flash_time % c.FLASH_INTERVAL == 0:
            self.chr_flg ^= 1
            self.chr_no = self.def_chr + self.chr_flg

        # 当たり判定
        if (
            self.x < 0
            and self.scene.ship.y == self.y
            and self.scene.ship.stop_time == 0
        ):
            self.scene.ship.flash = False
            self.scene.ship.visible = True
            if self.chr_no == c.CHR_METEO:  # メテオ
                self.scene.ship.stop_time = c.STOP_TIME
            else:  # バースト
                self.scene.ship.burst_time = c.STOP_TIME

            self.scene.item_num -= 1
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
            sp = gl.Sprite()
            sp.init_params(
                self,
                c.CHR_DEADLINE,
                "deadline",
                0,
                i * c.DEAD_H,
                c.DEAD_Z,
                c.DEAD_W,
                c.DEAD_H,
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
                bmp_data[c.BMP_NUM],
                "num",
                i * (c.NUM_W),
                2,
                100,
                c.NUM_W,
                c.NUM_H,
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
            self.scores[i].set_bitmap(bmp_data[c.BMP_NUM + (s % 10)])


# インデックスカラースプライト
chr_data = [
    (data.ship_0, 20, 20),  # 自機
    (data.ship_red, 20, 20),  # 自機 状態
    (data.ship_blue, 20, 20),  # 自機 状態
    (data.p_0, 20, 20),  # パネル
    (data.p_1, 20, 20),
    (data.p_2, 20, 20),
    (data.p_3, 20, 20),
    (data.p_4, 20, 20),
    (data.p_5, 20, 20),
    (data.p_x, 20, 20),  # グレーパネル
    (data.p_flash, 20, 20),  # フラッシュ
    (data.s_0, 20, 20),  # 弾
    (data.deadline, 4, 22),  # dead line
    (data.e_0, 20, 20),  # バッテリー（エネルギー）
    (data.e_1, 20, 20),
    (data.meteo_0, 20, 20),  # メテオ
    (data.meteo_1, 20, 20),
    (data.w_0, 20, 20),  # 連射
    (data.w_1, 20, 20),
]
# イメージバッファ生成
gl.create_image_buffers(data.palette565, chr_data)

# ビットマップスプライト
bmp_data = [
    (data.title, 240, 70),
    (data.gameover, 152, 24),
    (data.hi, 24, 20),
    (data.score, 80, 20),
    (data.lines, 72, 20),
    (data.info_bright, 48, 24),
    (data.ready, 96, 24),
    (data.credit, 168, 14),
    (data.combo, 88, 20),
    (data.num_0, 16, 16),  # 数字
    (data.num_1, 16, 16),
    (data.num_2, 16, 16),
    (data.num_3, 16, 16),
    (data.num_4, 16, 16),
    (data.num_5, 16, 16),
    (data.num_6, 16, 16),
    (data.num_7, 16, 16),
    (data.num_8, 16, 16),
    (data.num_9, 16, 16),
]

# ステータスをロード
game_status = gl.load_status()

if game_status is None:
    # デフォルト
    game_status = {"lv": 1, "score": 0, "hi": 0, "lines": 0, "brightness": 2}
    gl.save_status(game_status)

# LCDの明るさ
gl.lcd.brightness(game_status["brightness"])

# キー入力 シーン共通
key_global = pl.InputKey()

# 各シーンの作成
title = TitleScene("title", key_global)
main = MainScene("main", key_global)  # ゲーム本編
pause = PauseScene("pause", key_global)
over = OverScene("over", key_global)
scenes = [main, pause, over, title]

# ディレクターの作成
director = gl.Director(scenes)
# シーン実行
director.push("title")
director.play()

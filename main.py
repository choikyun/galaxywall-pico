"""GALAXY WALL Rainbow"""
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
        stage = MainStage(self, 0, "", 0, 0, 0, pl.LCD_WIDTH, pl.LCD_HEIGHT)
        # イベントマネージャ
        event = gl.EventManager()
        # 登録
        self.register(stage, event, key)

        # イベントリスナー
        event.add_listner([c.EV_GAMEOVER, self, True])
        # スプライト作成
        self.ship = Ship(
            stage, c.CHR_SHIP, "ship", 0, 0, 100, c.SHIP_WIDTH, c.SHIP_HEIGHT
        )
        # フィールド作成
        self.fieldmap = FieldMap(stage, c.FIELD_WIDTH, c.FIELD_HEIGHT)

    def enter(self):
        """ゲームの初期化処理"""
        # イベントのクリア
        self.event.clear_queue()
        # 全てのリスナーを有効
        self.event.enable_listners()
        # ステータス初期化
        game_status["lines"] = 0
        game_status["score"] = 0
        game_status["lv"] = 1
        # フィールドマップ初期化
        self.fieldmap.init_map()
        # 自機
        self.ship.x = 0
        self.ship.y = c.SHIP_MOVE_STEP * 2
        super().enter()

    def action(self):
        """フレーム毎のアクション 30FPS"""
        super().action()
        # ポーズ
        if self.active and self.key.push & pl.KEY_A:
            self.director.push("pause")

    def leave(self):
        """終了処理"""
        super().leave()

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
        stage = MainStage(self, 0, "", 0, 0, 0, pl.LCD_WIDTH, pl.LCD_HEIGHT)
        # イベントマネージャ
        event = gl.EventManager()
        # 登録
        self.register(stage, event, key)

        # スプライト作成
        gl.Sprite(stage, c.CHR_LINES, "lines", 22, 22, 1, c.LINES_W, c.LINES_H)
        gl.Sprite(
            stage,
            c.CHR_SCORE,
            "score",
            16,
            44,
            1,
            c.SCORE_W,
            c.SCORE_H,
        )
        gl.Sprite(stage, c.CHR_HI, "hi", 70, 66, 1, c.HI_W, c.HI_H)
        gl.Sprite(
            stage,
            c.CHR_INFO_BRIGHT,
            "info-bright",
            196,
            98,
            1,
            c.INFO_BRIGHT_W,
            c.INFO_BRIGHT_H,
        )
        # スコア
        self.lines = ScoreNum(self.stage, c.LINE_DIGIT, "score_num", 108, 22, 2)
        self.score = ScoreNum(self.stage, c.SCORE_DIGIT, "score_num", 108, 44, 2)
        self.hi = ScoreNum(self.stage, c.SCORE_DIGIT, "hi_num", 108, 66, 2)

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
            elif self.key.push & pl.KEY_DOWN and game_status["brightness"] > 0:
                game_status["brightness"] -= 1
                gl.lcd.brightness(game_status["brightness"])

            # ポーズ解除
            if self.key.push & pl.KEY_A:
                self.director.pop()

            # リセット
            if self.key.push == (pl.KEY_B | pl.KEY_CENTER):
                machine.reset()

    def leave(self):
        super().leave()


class MainStage(gl.Stage):
    """ステージ"""

    def __init__(self, scene, chr_no, name, x, y, z, w, h):
        super().__init__(scene, chr_no, name, x, y, z, w, h)

    def action(self):
        # スプライトアクション
        super().action()

    # イベントリスナー


class OverScene(gl.Scene):
    """ゲームオーバー
    ・スコア表示
    """

    def __init__(self, name, key):
        super().__init__(name)
        # ステージ
        stage = MainStage(self, 0, "", 0, 0, 0, pl.LCD_WIDTH, pl.LCD_HEIGHT)
        # イベントマネージャ
        event = gl.EventManager()
        # 登録
        self.register(stage, event, key)

        # スプライト作成
        gl.Sprite(
            stage,
            c.CHR_OVER,
            "over",
            42,
            7,
            1,
            c.OVER_W,
            c.OVER_H,
        )
        gl.Sprite(
            stage,
            c.CHR_LINES,
            "lines",
            22,
            44,
            1,
            c.LINES_W,
            c.LINES_H,
        )
        gl.Sprite(
            stage,
            c.CHR_SCORE,
            "score",
            16,
            66,
            1,
            c.SCORE_W,
            c.SCORE_H,
        )
        self.hi = gl.Sprite(stage, c.CHR_HI, "hi", 70, 88, 1, c.HI_W, c.HI_H)
        self.lines_num = ScoreNum(self.stage, c.LINE_DIGIT, "lines_num", 108, 44, 1)
        self.score_num = ScoreNum(self.stage, c.SCORE_DIGIT, "score_num", 108, 66, 1)
        self.hi_num = ScoreNum(self.stage, c.SCORE_DIGIT, "hi_num", 108, 88, 1)

    def enter(self):
        self.lines_num.set_value(game_status["lines"])
        self.score_num.set_value(game_status["score"])
        self.hi_num.set_value(game_status["hi"])
        super().enter()

    def action(self):
        super().action()

        if self.active:
            # リプレイ
            if self.key.push & pl.KEY_A:
                self.director.pop()
                self.director.pop()  # メイン画面もpop
                self.director.push("main")

    def leave(self):
        super().leave()


class MainStage(gl.Stage):
    """ステージ"""

    def __init__(self, scene, chr_no, name, x, y, z, w, h):
        super().__init__(scene, chr_no, name, x, y, z, w, h)

    def action(self):
        # スプライトアクション
        super().action()

    # イベントリスナー


class Ship(gl.Sprite):
    """自機クラス"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__(parent, chr_no, name, x, y, z, w, h)
        self.move_anime = gl.Anime(self.scene.event, ease.out_quart)  # 移動アニメ
        self.move_anime.attach()  # アニメ有効化
        # イベントリスナー登録
        self.scene.event.add_listner([gl.EV_ENTER_FRAME, self, True])

    def enter(self):
        self.fire_panel_num = 0  # 現在の発射数
        super().enter()

    def leave(self):
        # イベントリスナー削除
        self.scene.event.remove_all_listner(self)
        self.move_anime.detach()  # アニメ無効化
        super().leave()

    def action(self):
        super().action()

    def __fire_panel(self):
        """弾発射"""
        if self.fire_panel_num >= c.SHOT_PANEL_MAX:
            return
        self.fire_panel_num += 1
        # 新しい弾を生成
        shot = ShotPanel(
            self.stage,
            c.CHR_SHOT,
            "shot",
            self.x,
            self.y,
            10,
            c.SHOT_WIDTH,
            c.SHOT_HEIGHT,
        )
        shot.enter()

    # イベントリスナー
    def event_enter_frame(self, type, sender, option):
        """フレーム毎"""
        # 上下移動
        if option.repeat & pl.KEY_UP and self.y > 0 and not self.move_anime.is_playing:
            # アニメセット
            self.move_anime.start = self.y
            self.move_anime.delta = -c.SHIP_MOVE_STEP
            self.move_anime.total_frame = c.SHIP_MOVE_FRAME_MAX
            self.move_anime.play()
        if (
            option.repeat & pl.KEY_DOWN
            and self.y < c.SHIP_MOVE_LIMIT
            and not self.move_anime.is_playing
        ):
            # アニメセット
            self.move_anime.start = self.y
            self.move_anime.delta = c.SHIP_MOVE_STEP
            self.move_anime.total_frame = c.SHIP_MOVE_FRAME_MAX
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
        # イベントリスナー登録
        self.scene.event.add_listner([gl.EV_ENTER_FRAME, self, True])
        self.scene.event.add_listner([c.EV_DELETE_LINE, self, True])  # ライン消去

        # フィールドマップ パネルの配置 2次元マップ
        self.fieldmap = [
            [None for i in range(c.FIELD_WIDTH)] for j in range(c.FIELD_HEIGHT)
        ]

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
        self.deadline = 0

        # フィールド初期化
        self.clear()
        for i in range(c.DEF_LINES):
            self.set_new_line(c.FIELD_WIDTH - c.DEF_LINES + i)

    def clear(self):
        """マップをクリア
        スプライトも破棄
        """
        for y in range(c.FIELD_HEIGHT):
            for x in range(c.FIELD_WIDTH):
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].leave()
                    self.fieldmap[y][x] = None

    def set_new_line(self, x=c.FIELD_WIDTH - 1):
        """新しいラインを作成"""
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
        if self.line_count % c.COLOR_STEP == 0:
            self.current_color = (self.current_color + 1) % c.COLOR_MAX

    def set_new_panel(self, x, y, color):
        """新しいパネルをセット"""
        sp_x = x * c.PANEL_WIDTH
        sp_y = y * (c.PANEL_HEIGHT + c.PANEL_BLANK_Y)
        self.fieldmap[y][x] = Panel(
            self.stage,
            color + c.CHR_PANEL,
            "panel",
            sp_x,
            sp_y,
            50,
            c.PANEL_WIDTH,
            c.PANEL_HEIGHT,
        )
        self.fieldmap[y][x].enter()

    def __shuffle(self, x):
        """1列まぜる"""
        for i in range(c.FIELD_HEIGHT):
            y = random.randint(0, c.FIELD_HEIGHT - 1)
            tmp = self.fieldmap[i][x]
            self.fieldmap[i][x] = self.fieldmap[y][x]
            self.fieldmap[y][x] = tmp

        # Y座標決定
        for y in range(c.FIELD_HEIGHT):
            if self.fieldmap[y][x] is not None:
                self.fieldmap[y][x].y = y * (c.PANEL_HEIGHT + c.PANEL_BLANK_Y)

    def check_hit_panel(self, shot_panel):
        """弾とパネルの当たり判定"""
        x = shot_panel.x // c.PANEL_WIDTH
        y = shot_panel.y // (c.PANEL_HEIGHT + c.PANEL_BLANK_Y)
        hit = False
        new_panel_x = x

        # フィールドがスクロールしなかった場合
        if x == (c.FIELD_WIDTH - 1) or self.fieldmap[y][x + 1] is not None:
            hit = True

        # スクロールしている場合もある
        if self.fieldmap[y][x] is not None:
            hit = True
            new_panel_x -= 1

        if hit:
            self.set_new_panel(
                new_panel_x, y, self.__get_panel_color(new_panel_x)
            )  # パネル生成
            shot_panel.leave()  # 弾削除
            self.scene.ship.fire_panel_num -= 1
            self.__check_line(new_panel_x)  # ライン消去判定

    def __get_panel_color(self, x):
        """パネルの色を取得
            無効な弾はグレー
        """
        for y in range(c.FIELD_HEIGHT):
            if self.fieldmap[y][x] is not None:
                return self.fieldmap[y][x].chr_no - c.CHR_PANEL
        # 見つからない場合はグレー
        return c.GRAY_PANEL

    def __clear_line(self, pos_x):
        """1列削除"""
        for i in range(c.FIELD_HEIGHT):
            self.fieldmap[i][pos_x] = None

    def __check_line(self, x):
        """1列そろったか"""
        for y in range(c.FIELD_HEIGHT):
            if self.fieldmap[y][x] is None:
                return
        
        # コンボ発生 
        if self.combo >= 1:
            pass

        for y in range(c.FIELD_HEIGHT):
            self.fieldmap[y][x].flash = True

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
        if self.fieldmap[0][x].chr_no != (c.CHR_PANEL + c.GRAY_PANEL):
            self.combo += 1
            game_status["score"] += (c.FIELD_WIDTH - x) * self.combo
            # ライン可算
            game_status["lines"] += 1

    def __scroll_map(self):
        """フィールドマップとスプライトの更新"""
        for y in range(c.FIELD_HEIGHT):
            for x in range(c.FIELD_WIDTH - 1):
                self.fieldmap[y][x] = self.fieldmap[y][x + 1]  # 1キャラクタ分スクロール
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].base_x -= c.PANEL_WIDTH  # ベース座標の更新

    def __check_over(self):
        """ゲームオーバーか
        Returns:
            (bool): True ゲームオーバー
        """
        for y in range(c.FIELD_HEIGHT):
            if self.fieldmap[y][self.deadline] is not None:
                # イベント発行
                self.scene.event.post(
                    [
                        c.EV_GAMEOVER,
                        gl.EV_PRIORITY_HI,
                        30, # タイムラグ 1秒後
                        self,
                        None,
                    ]
                )
                # ゲームオーバー以外のリスナーをオフにする
                self.scene.event.disable_listers(None,[c.EV_GAMEOVER])
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
        for y in range(c.FIELD_HEIGHT):
            for x in range(c.FIELD_WIDTH):
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].x = (
                        self.fieldmap[y][x].base_x + self.scroll_offset
                    )

    def event_delete_line(self, type, sender, option):
        """ライン消去"""
        for pos in range(c.FIELD_WIDTH):
            if self.fieldmap[0][pos] is option:  # X座標を取得
                break

        for y in range(c.FIELD_HEIGHT):
            self.fieldmap[y][pos].leave()
            self.fieldmap[y][pos] = None

        # 詰める
        for y in range(c.FIELD_HEIGHT):
            for x in range(pos, 0, -1):
                self.fieldmap[y][x] = self.fieldmap[y][x - 1]
                if self.fieldmap[y][x] is not None:
                    self.fieldmap[y][x].base_x += c.PANEL_WIDTH

        # 先頭は空
        for y in range(c.FIELD_HEIGHT):
            if self.fieldmap[y][0] is not None:
                self.fieldmap[y][0] = None

        # コンボひとつ終了
        self.combo -= 1


class Panel(gl.Sprite):
    """迫りくるパネル"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__(parent, chr_no, name, x, y, z, w, h)
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
            if self.flash_time % c.FLASH_INTERVAL == 0:
                self.visible = not self.visible

    # イベントリスナー


class ShotPanel(gl.Sprite):
    """自機の打ち出すパネル"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__(parent, chr_no, name, x, y, z, w, h)
        self.scene.event.add_listner([gl.EV_ENTER_FRAME, self, True])

    def enter(self):
        super().enter()

    def leave(self):
        self.scene.event.remove_all_listner(self)
        super().leave()

    def action(self):
        super().action()

    # イベントリスナー
    def event_enter_frame(self, type, sender, option):
        # 移動
        if self.x % c.PANEL_WIDTH == 0:
            # イベントを出さずにここで当たり判定
            self.scene.fieldmap.check_hit_panel(self)

        self.x += c.SHOT_SPEED


class ScoreNum(gl.SpriteContainer):
    """スコア表示
    子スプライトが数字を表示

    Params;
        score (int): スコア
    """

    def __init__(self, parent, digit, name, x, y, z):
        super().__init__(parent, name, x, y, z)
        self.digit = digit

        # 子スプライト
        self.score = []
        for i in range(digit):
            # 桁数分の数字スプライト
            self.score.append(
                gl.Sprite(
                    self,
                    c.CHR_NUM,
                    "",
                    i * (c.NUM_W),
                    0,
                    100,
                    c.NUM_W,
                    c.NUM_H,
                )
            )

    def enter(self):
        super().enter()

    def set_value(self, val):
        """数値をセット"""
        for i in range(self.digit):
            s = val
            for d in range(self.digit - i - 1):
                s //= 10
            self.score[i].chr_no = c.CHR_NUM + (s % 10)


# スプライト用イメージバッファ生成
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
    (data.p_x, 20, 20), # グレーパネル
    (data.s_0, 20, 20),  # 弾
    (data.hi, 28, 20),
    (data.score, 84, 20),
    (data.lines, 76, 20),
    (data.info_bright, 44, 24),
    (data.gameover, 152, 24),  # ゲームオーバー
    (data.num_0, 20, 20),  # 数字
    (data.num_1, 20, 20),
    (data.num_2, 20, 20),
    (data.num_3, 20, 20),
    (data.num_4, 20, 20),
    (data.num_5, 20, 20),
    (data.num_6, 20, 20),
    (data.num_7, 20, 20),
    (data.num_8, 20, 20),
    (data.num_9, 20, 20),
]

# イメージバッファ生成
gl.create_image_buffers(data.palet565, chr_data)

# ステータスをロード
game_status = gl.load_status()
if game_status is None:
    # デフォルト
    game_status = {"lv": 1, "score": 0, "hi": 0, "lines": 0, "brightness": 2}
    gl.save_status(game_status)

# キー入力 シーン共通
key_global = pl.InputKey()

# 各シーンの作成
main = MainScene("main", key_global)  # ゲーム本編
pause = PauseScene("pause", key_global)
over = OverScene("over", key_global)
scenes = [main, pause, over]

# ディレクターの作成
director = gl.Director(scenes)
# シーン実行
director.push("main")
director.play()

from micropython import const

# 自機
SHIP_W = const(20)
SHIP_H = const(20)
SHIP_MOVE_STEP = const(SHIP_H + 2)
SHIP_MOVE_LIMIT = const(SHIP_MOVE_STEP * 5)
SHIP_MOVE_FRAME_MAX = const(8)  # 移動にかかるフレーム数

# 弾
SHOT_W = const(20)
SHOT_H = const(20)
SHOT_PANEL_MAX = const(1)
SHOT_SPEED = const(10)

# フィールド
FIELD_W = const(12)
FIELD_H = const(6)

# レベル
LEVEL_MAX = const(5)
# 3ラインで色が変わる
COLOR_STEP = const(3)

# スコア
SCORE_DIGIT = const(6)

LINE_DIGIT = const(4)
DEF_LINES = const(6)

# パネル
PANEL_W = const(20)
PANEL_H = const(20)
PANEL_BLANK_Y = const(2)
PANEL_OFFSET = const(20)
PANEL_OFFSET_INIT = const(20)
PANEL_MAX = const(5)
COLOR_MAX = const(6)

DEF_DEAD_X = const(24)
DEAD_W = const(4)
DEAD_H = const(132)

# スクロール
SCROLL_WAIT = const(6)  # ウェイト
SCROLL_STOP_TIME = const(30)  # 一定時間停止

# 点滅
FLASH_INTERVAL = const(4)

# 1列消去の遅延時間
DELETE_DELAY = const(30)

# キャラクタ
CHR_SHIP = const(0)
CHR_PANEL = const(3)
CHR_PANELX = const(9)
CHR_FLASH = const(10)
CHR_SHOT = const(11)

CHR_HI = const(12)
CHR_SCORE = const(13)
CHR_LINES = const(14)
CHR_INFO_BRIGHT = const(15)
CHR_OVER = const(16)
CHR_NUM = const(17)
CHR_DEADLINE = const(27)

# ポーズ画面
SCORE_W = const(84)
SCORE_H = const(20)
HI_W = const(28)
HI_H = const(20)
LINES_W = const(76)
LINES_H = const(20)
INFO_BRIGHT_W = const(44)
INFO_BRIGHT_H = const(24)

NUM_W = const(16)
NUM_H = const(20)

# ゲームオーバー
OVER_W = const(152)
OVER_H = const(24)

# デッドライン
DEAD_INTERVAL = const(120)

# イベント
EV_CHECK_HIT = const("event_check_hit_panel")
"""弾とパネルの当たり判定"""
EV_DELETE_LINE = const("event_delete_line")
"""ライン消去"""
EV_GAMEOVER = const("event_gameover")
"""ゲームオーバー"""

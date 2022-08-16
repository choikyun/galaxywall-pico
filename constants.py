# 自機
SHIP_WIDTH = 20
SHIP_HEIGHT = 20
SHIP_MOVE_STEP = SHIP_HEIGHT + 2
SHIP_MOVE_LIMIT = SHIP_MOVE_STEP * 5
SHIP_MOVE_FRAME_MAX = 8  # 移動にかかるフレーム数

# 弾
SHOT_WIDTH = 20
SHOT_HEIGHT = 20
SHOT_PANEL_MAX = 1
SHOT_SPEED = 10

# フィールド
FIELD_WIDTH = 12
FIELD_HEIGHT = 6

# レベル
LEVEL_MAX = 5
# 3ラインで色が変わる
COLOR_STEP = 3

# スコア
SCORE_DIGIT = 6
SCORE_WIDTH = 20
SCORE_HEIGHT = 20

LINE_DIGIT = 4
DEF_LINES = 6

# パネル
PANEL_WIDTH = 20
PANEL_HEIGHT = 20
PANEL_BLANK_Y = 2
PANEL_OFFSET = 20
PANEL_OFFSET_INIT = 20
PANEL_MAX = 5
COLOR_MAX = 6

# スクロール
SCROLL_WAIT = 6  # ウェイト
SCROLL_STOP_TIME = 30  # 一定時間停止

# 点滅
FLASH_INTERVAL = 4

# 1列消去の遅延時間
DELETE_DELAY = 30

# キャラクタ
CHR_SHIP = 0
CHR_PANEL = 3
CHR_SHOT = 10

CHR_HI = 11
CHR_SCORE = 12
CHR_LINES = 13
CHR_INFO_BRIGHT = 14
CHR_OVER = 15
CHR_NUM = 16

# 無効なパネル
GRAY_PANEL = 6

# ポーズ画面
SCORE_W = 84
SCORE_H = 20
HI_W = 28
HI_H = 20
LINES_W = 76
LINES_H = 20
INFO_BRIGHT_W = 44
INFO_BRIGHT_H = 24

NUM_W = 16
NUM_H = 20

# ゲームオーバー
OVER_W = 152
OVER_H = 24

# イベント
EV_CHECK_HIT = "event_check_hit_panel"
"""弾とパネルの当たり判定"""
EV_DELETE_LINE = "event_delete_line"
"""ライン消去"""
EV_GAMEOVER = "event_gameover"
"""ゲームオーバー"""

PLAY = 1
"""ゲームステータス: プレイ中"""
OVER = 2
"""ゲームステータス: ゲームオーバー"""
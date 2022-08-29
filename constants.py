"""GALAXY WALL PICO"""
__version__ = "1.0.0"
__author__ = "Choi Gyun 2022"

from micropython import const

# 自機
SHIP_W = const(20)
SHIP_H = const(20)
SHIP_MOVE_STEP = const(SHIP_H + 2)
SHIP_MOVE_LIMIT = const(SHIP_MOVE_STEP * 5)
SHIP_MOVE_FRAME_MAX = const(8)  # 移動にかかるフレーム数
SHIP_FLASH_INTERVAL = const(2)

# 弾
SHOT_W = const(20)
SHOT_H = const(20)
SHOT_PANEL_MAX = const(2)
SHOT_SPEED = const(10)

# フィールド
FIELD_W = const(12)
FIELD_H = const(6)

READY_W = const(108)
READY_H = const(24)

# レベル
LEVEL_MAX = const(5)
# レベルアップの間隔
LEVEL_UP_INTERVAL = const(10)
# 3ラインで色が変わる
COLOR_STEP = const(3)

# スコア
SCORE_DIGIT = const(6)
LINE_DIGIT = const(4)

DEF_LINES = const(7)

# パネル
PANEL_W = const(20)
PANEL_H = const(20)
PANEL_BLANK_Y = const(2)
PANEL_OFFSET = const(20)
PANEL_OFFSET_INIT = const(20)
PANEL_MAX = const(5)
COLOR_MAX = const(6)

DEAD_X = const(24)
DEAD_W = const(4)
DEAD_H = const(22)
DEAD_BLANK = const(2)

# スクロール
SCROLL_WAIT = const(6)  # ウェイト
SCROLL_STOP_TIME = const(30)  # 一定時間停止

# 点滅
FLASH_INTERVAL = const(4)

# メッセージ
READY_DURATION = const(30 * 2)
READY_INTERVAL = const(6)
# combo メッセージ
COMBO_DURATION = const(15)
COMBO_INTERVAL = const(4)

# 1列消去の遅延時間
DELETE_DELAY = const(30)

# キャラクタ
# メイン
CHR_SHIP = const(0)
CHR_PANEL = const(3)
CHR_PANELX = const(9)
CHR_FLASH = const(10)
CHR_SHOT = const(11)
CHR_DEADLINE = const(12)
CHR_EPANEL = const(13)
CHR_METEO = const(15)
CHR_BURST = const(17)

BMP_TITLE = const(0)
BMP_OVER = const(1)
BMP_HI = const(2)
BMP_SCORE = const(3)
BMP_LINES = const(4)
BMP_INFO_BRIGHT = const(5)
BMP_READY = const(6)
BMP_CREDIT = const(7)
BMP_COMBO = const(8)
BMP_NUM = const(9)

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
NUM_H = const(16)

# ゲームオーバー
OVER_W = const(152)
OVER_H = const(24)

# デッドライン
DEAD_INTERVAL = const(15)

# タイトル
TITLE_W = const(240)
TITLE_H = const(70)

CREDIT_W = const(168)
CREDIT_H = const(14)

COMBO_W = (88)
COMBO_H = (20)

# デッドライン移動までの時間
MAX_DEADTIME = const(60)
DEADTIME_STEP = const(4)
DEADTIME_COL_FULL = const(0b00000_111111_00000)
DEADTIME_COL_MID = const(0b11111_111111_00000)
DEADTIME_COL_EMPTY = const(0b11111_000000_00000)
# 回復
DEADTIME_RECOVERY = const(6)

# デッドラインの最大値（X座標）
MAX_DEADLINE = const(6)

# 停止
ITEM_SPEED = const(1)
STOP_TIME = const(30 * 8)
# アイテム最大数
MAX_ITEM = (5)
# アイテム出現間隔
ITEM_INTERVAL = const(30)

# 強制スクロールスコア
FORCE_SCORE = const(1)

SHIP_Z = 100
SHOT_Z = 50
DEAD_Z = 10
PANEL_Z = 500
ITEM_Z = 1000
MES_Z = 10000

# イベント
EV_CHECK_HIT = const("event_check_hit_panel")
"""弾とパネルの当たり判定"""
EV_DELETE_LINE = const("event_delete_line")
"""ライン消去"""
EV_GAMEOVER = const("event_gameover")
"""ゲームオーバー"""
EV_UPDATE_DEADLINE = const("event_update_deadline")
"""デッドライン更新"""
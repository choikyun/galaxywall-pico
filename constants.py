"""GALAXY WALL PICO"""
__version__ = "1.0.0"
__author__ = "Choi Gyun 2022"

from micropython import const

### オブジェクトのサイズ
OBJ_W = const(20)
OBJ_H = const(20)

### 自機
SHIP_MOVE_STEP = const(OBJ_H + 2)
SHIP_MOVE_MAX = const(SHIP_MOVE_STEP * 5)
SHIP_MOVE_FRAME_MAX = const(5)  # 移動にかかるフレーム数
SHIP_FLASH_INTERVAL = const(2)

KEY_WAIT = const(5)

### 弾
SHOT_PANEL_MAX = const(2)
SHOT_SPEED = const(10)

### フィールド
FIELD_W = const(12)
FIELD_H = const(6)

READY_W = const(108)
READY_H = const(24)

COLOR_STEP = const(3)  # 色が変わる

### スコア
SCORE_DIGIT = const(6)
LINE_DIGIT = const(4)

DEF_LINES = const(6)

### パネル
PANEL_BLANK_Y = const(2)
PANEL_OFFSET = const(20)
PANEL_OFFSET_INIT = const(20)
PANEL_MAX = const(5)
COLOR_MAX = const(6)

DEAD_X = const(24)
DEAD_W = const(4)
DEAD_H = const(22)
DEAD_BLANK = const(2)

### スクロール
SCROLL_WAIT_NORMAL = const(4)  # ウェイト
SCROLL_WAIT_EX = const(2)
SCROLL_STOP_TIME = const(30)  # 一定時間停止

FLASH_INTERVAL = const(4)  # 点滅

### メッセージ
READY_DURATION = const(30 * 2)
READY_INTERVAL = const(6)

# combo メッセージ
COMBO_DURATION = const(20)
COMBO_INTERVAL = const(4)

DELETE_DELAY = const(30)  # 1列消去の遅延時間

### キャラクタ
CHR_SHIP = const(0)
CHR_PANEL = const(3)
CHR_PANELX = const(9)
CHR_FLASH = const(10)
CHR_SHOT = const(11)
CHR_DEADLINE = const(12)
CHR_ITEM = const(13)
CHR_AIM = const(15)

BMP_TITLE = const(0)
BMP_OVER = const(1)
BMP_HI = const(2)
BMP_SCORE = const(3)
BMP_LINES = const(4)
BMP_INFO_BRIGHT = const(5)
BMP_READY = const(6)
BMP_COMBO = const(7)
BMP_NUM = const(8)
BMP_CREDIT = const(18)
BMP_EX = const(19)

### ポーズ画面
SCORE_W = const(84)
SCORE_H = const(20)
HI_W = const(28)
HI_H = const(20)
LINES_W = const(76)
LINES_H = const(20)
INFO_BRIGHT_W = const(44)
INFO_BRIGHT_H = const(24)

### 数字
NUM_W = const(16)
NUM_H = const(16)

### ゲームオーバー
OVER_W = const(152)
OVER_H = const(24)

DEAD_INTERVAL = const(12)  # デッドラインバー減る間隔

### タイトル
TITLE_W = const(240)
TITLE_H = const(70)

CREDIT_W = const(144)
CREDIT_H = const(10)

COMBO_W = const(88)
COMBO_H = const(20)

MAX_DEADTIME = const(60)  # デッドライン移動までの時間
DEADTIME_STEP = const(4)
DEADTIME_COL_FULL = const(0b00000_111111_00000)
DEADTIME_COL_MID = const(0b11111_111111_00000)
DEADTIME_COL_EMPTY = const(0b11111_000000_00000)
DEADTIME_RECOVERY = const(8)  # 回復
MAX_DEADLINE = const(6)  # デッドラインの最大値（X座標）

### アイテム
ITEM_FREEZE = const(0)
ITEM_BURST = const(1)
ITEM_SPEED = const(5)
MAX_ITEM = const(5)  # アイテム最大数
ITEM_INTERVAL = const(15)  # アイテム出現間隔
FREEZE_DURATION = const(30 * 3)  # アイテム効果持続時間
BURST_DURATION = const(30 * 6)

### 画面ゆれ
SHAKE_FRAME_MAX = const(2)
SHAKE_DELTA = const(4)

### 各オブジェクト　重なり順
PANEL_Z = const(10)
DEAD_Z = const(20)
SHOT_Z = const(30)
SHIP_Z = const(40)
AIM_Z = const(50)
ITEM_Z = const(60)
MES_Z = const(70)

# イベント
EV_CHECK_HIT = const("event_check_hit_panel")
"""弾とパネルの当たり判定"""
EV_DELETE_LINE = const("event_delete_line")
"""ライン消去"""
EV_GAMEOVER = const("event_gameover")
"""ゲームオーバー"""
EV_UPDATE_DEADLINE = const("event_update_deadline")
"""デッドライン更新"""

""" 1.14inch LCD Display Module for Raspberry Pi Pico の制御

https://www.waveshare.com/pico-lcd-1.14.htm
"""
from machine import Pin, SPI, PWM
import framebuf
import time

BL = 13
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

# 画面サイズ
LCD_WIDTH = 240
LCD_HEIGHT = 135

# デフォルトのカラー
COL_RED = 0xF800
COL_GREEN = 0x07E0
COL_BLUE = 0x001F
COL_WHITE = 0xFFFF
COL_BLACK = 0x0000

# キー入力
KEY_UP = 0b0000_1000
KEY_DOWN = 0b0000_0100
KEY_LEFT = 0b0000_0010
KEY_RIGHT = 0b0000_0001
KEY_A = 0b0010_0000
KEY_B = 0b0001_0000
KEY_CENTER = 0b1000_0000


class LCD:
    """Pico LCD 1.14inch の画面表示制御"""

    def __init__(self):
        self.cs = Pin(CS, Pin.OUT)
        self.rst = Pin(RST, Pin.OUT)

        self.cs(1)
        # ボーレートは適当
        self.spi = SPI(
            1, 100_000_000, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI), miso=None
        )
        self.dc = Pin(DC, Pin.OUT)
        self.dc(1)

        # 液晶の明るさ
        self.pwm = PWM(Pin(BL))
        self.pwm.freq(1000)
        self.brightness(32768 // 2)

        self.init_display()

    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        """画面初期化"""
        self.rst(1)  # reset
        self.rst(0)
        self.rst(1)

        self.write_cmd(0x36)  # Memory Data Access Control
        self.write_data(0x70)  # 0111_0000

        self.write_cmd(0x3A)  # Interface pixel format
        self.write_data(0x05)  # 0000_0101

        self.write_cmd(0xB0)  # RAM Control
        self.write_data(0x00)  # 0000_0000
        self.write_data(0xF8)  # 1111_1000

        self.write_cmd(0xBB)  # VCOM Setting
        self.write_data(0x19)

        self.write_cmd(0xC0)  # LCM Control
        self.write_data(0x0C)  # 0010_1100

        self.write_cmd(0xC3)  # VRH Set
        self.write_data(0x12)

        self.write_cmd(0xE0)  # Positive Voltage Gamma Control
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0D)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2B)
        self.write_data(0x3F)
        self.write_data(0x54)
        self.write_data(0x4C)
        self.write_data(0x18)
        self.write_data(0x0D)
        self.write_data(0x0B)
        self.write_data(0x1F)
        self.write_data(0x23)

        self.write_cmd(0xE1)  # Negative Voltage Gamma Control
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0C)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2C)
        self.write_data(0x3F)
        self.write_data(0x44)
        self.write_data(0x51)
        self.write_data(0x2F)
        self.write_data(0x1F)
        self.write_data(0x1F)
        self.write_data(0x20)
        self.write_data(0x23)

        self.write_cmd(0x21)  # Display Inversion On
        self.write_cmd(0x11)  # Sleep out
        self.write_cmd(0x29)  # Display On

    def show(self, buf):
        """バッファ転送"""
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x28)
        self.write_data(0x01)
        self.write_data(0x17)

        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x35)
        self.write_data(0x00)
        self.write_data(0xBB)

        self.write_cmd(0x2C)

        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)

    def brightness(self, v=32767):
        """画面の明るさ"""
        self.pwm.duty_u16(v)  # max 65535


class InputKey:
    """キー入力"""

    def __init__(self):
        self.repeat = 0
        self.push = 0

    def scan(self):
        """キースキャン
        repeat は押しっぱなし, push は押したまま.
        """
        self.push = ~self.repeat
        self.repeat = 0

        if Pin(15, Pin.IN, Pin.PULL_UP).value() == 0:
            self.repeat |= KEY_A
        elif Pin(17, Pin.IN, Pin.PULL_UP).value() == 0:
            self.repeat |= KEY_B

        if Pin(2, Pin.IN, Pin.PULL_UP).value() == 0:
            self.repeat |= KEY_UP
        elif Pin(3, Pin.IN, Pin.PULL_UP).value() == 0:
            self.repeat |= KEY_CENTER
        elif Pin(16, Pin.IN, Pin.PULL_UP).value() == 0:
            self.repeat |= KEY_LEFT
        elif Pin(18, Pin.IN, Pin.PULL_UP).value() == 0:
            self.repeat |= KEY_DOWN
        elif Pin(20, Pin.IN, Pin.PULL_UP).value() == 0:
            self.repeat |= KEY_RIGHT

        self.push &= self.repeat

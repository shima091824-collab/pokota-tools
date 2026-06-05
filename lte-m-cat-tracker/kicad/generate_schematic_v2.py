#!/usr/bin/env python3
"""
LTE-M 猫GPSトラッカー KiCad 回路図生成スクリプト v2.1
- 全ICを 2.54mm(100mil)グリッドに配置
- ピンエンドポイントを数式で正確計算
- ラベル・GND・PWRをピン端点に直置き（ワイヤー不要）
- endpoint_off_grid をゼロにする
"""

import uuid, math

SYMDIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

def gen_uuid(): return str(uuid.uuid4())

def rot(px, py, a):
    """KiCad Y下向き座標系での反時計回り回転"""
    a %= 360
    if a == 0:   return  px,  py
    if a == 90:  return -py,  px
    if a == 180: return -px, -py
    if a == 270: return  py, -px
    r = math.radians(a)
    return px*math.cos(r)-py*math.sin(r), px*math.sin(r)+py*math.cos(r)

def pabs(sx, sy, sa, px, py):
    # KiCadシンボル定義はY-UP座標系 → Y-DOWNレイアウトに変換してから回転
    rx, ry = rot(px, -py, sa)
    return round(sx+rx, 4), round(sy+ry, 4)

G = 2.54  # 基本グリッド

# ── ピン座標（標準ライブラリ実測値）─────────────
P_TP4056 = dict(
    TEMP=(10.16,0), PROG=(10.16,-2.54), GND=(0,-12.70), VCC=(0,12.70),
    BAT=(10.16,5.08), STDBY=(-10.16,-2.54), CHRG=(-10.16,0), CE=(-10.16,5.08),
    EPAD=(-2.54,-12.70),
)
P_XC6220 = dict(VIN=(-12.70,2.54), GND=(0,-10.16), CE=(-12.70,-2.54), NC=(7.62,-2.54), VOUT=(12.70,2.54))
P_R  = {'1':(0,3.81),  '2':(0,-3.81)}
P_C  = {'1':(0,3.81),  '2':(0,-3.81)}
P_LED= {'K':(-3.81,0), 'A':(3.81,0)}
P_E32= dict(
    LNA_IN=(22.86,20.32), CHIP_EN=(22.86,15.24),
    MTMS=(22.86,10.16),MTDI=(22.86,7.62),MTCK=(22.86,5.08),MTDO=(22.86,2.54),
    VDD_SPI=(5.08,25.40),SPIHD=(22.86,-2.54),SPIWP=(22.86,-5.08),
    SPICS0=(22.86,-7.62),SPICLK=(22.86,-10.16),SPID=(22.86,-12.70),SPIQ=(22.86,-15.24),
    VDD3P3=(-10.16,25.40),VDD3P3_RTC=(-5.08,25.40),VDD3P3_CPU=(0,25.40),
    VDDA=(10.16,25.40),GND=(0,-25.40),
    GPIO2=(-22.86,20.32),GPIO3=(-22.86,17.78),GPIO8=(-22.86,15.24),
    GPIO9=(-22.86,12.70),GPIO10=(-22.86,10.16),GPIO18=(-22.86,7.62),
    GPIO19=(-22.86,5.08),U0RXD=(-22.86,-2.54),U0TXD=(-22.86,0),
    XTAL_32K_P=(-22.86,-7.62),XTAL_32K_N=(-22.86,-10.16),
    XTAL_N=(-22.86,-12.70),XTAL_P=(-22.86,-15.24),
)
P_SIM = {
    'VBAT1':(-20.32,17.78),'VBAT2':(-20.32,15.24),'VBAT3':(-20.32,12.70),'VBAT4':(-20.32,10.16),
    'GND5':(-20.32,7.62),'GND6':(-20.32,5.08),'GND7':(-20.32,2.54),
    'PWRKEY':(-20.32,0),'STATUS':(-20.32,-2.54),'RESETN':(-20.32,-5.08),
    'NETLIGHT':(-20.32,-7.62),'TXD':(-20.32,-10.16),'RXD':(-20.32,-12.70),
    'RTS':(-20.32,-15.24),'CTS':(-20.32,-17.78),
    'SIM_VDD':(20.32,17.78),'SIM_DATA':(20.32,15.24),'SIM_CLK':(20.32,12.70),
    'SIM_RST':(20.32,10.16),'SIM_DET':(20.32,7.62),'SIM_GND':(20.32,5.08),
    'LTE_ANT':(20.32,2.54),'GNSS_ANT':(20.32,0),'GND77':(20.32,-2.54),
}
P_LIS= {
    'SDO':(-15.24,5.08),'VDD':(-15.24,2.54),'SCL':(-15.24,0),'CS':(-15.24,-2.54),
    'INT2':(-15.24,-5.08),'GND6':(-15.24,-7.62),
    'RES1':(15.24,5.08),'RES2':(15.24,2.54),'INT1':(15.24,0),
    'GND10':(15.24,-2.54),'SDA':(15.24,-5.08),'VDD_IO':(15.24,-7.62),
}
P_SIM1= dict(VCC=(-12.70,5.08),DATA=(-12.70,2.54),CLK=(-12.70,0),RST=(-12.70,-2.54),GND=(-12.70,-5.08),CD=(12.70,0))
P_UFL = dict(SIG=(0,7.62),GND=(0,-5.08))
P_ANT = dict(RF=(-5.08,0),GND=(5.08,0))
P_USB = dict(VBUS=(-12.70,-10.16),DM=(-12.70,-7.62),DP=(-12.70,-5.08),
             CC1=(-12.70,-2.54),CC2=(-12.70,0),GND_A=(-12.70,2.54),GND_B=(-12.70,5.08),SH=(-12.70,7.62))
P_JST = {'+':(-10.16,1.27),'-':(-10.16,-1.27)}
P_SW  = {'A':(-6.35,0),'B':(6.35,0)}

# ── lib_symbols ─────────────────────────────────
def ext(lib, sym):
    nn = f"{lib}:{sym}"
    with open(f"{SYMDIR}/{lib}.kicad_sym") as f: c = f.read()
    i = c.find(f'\t(symbol "{sym}"')
    if i<0: return ""
    d=0
    for j in range(i,len(c)):
        if c[j]=='(': d+=1
        elif c[j]==')':
            d-=1
            if d==0: return c[i:j+1].replace(f'(symbol "{sym}"',f'(symbol "{nn}"',1)
    return ""

SIM_SYM='''    (symbol "Custom:SIM7080G-M"
      (exclude_from_sim no)(in_bom yes)(on_board yes)(duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "U" (at 0 32 0)(effects(font(size 1.27 1.27))))
      (property "Value" "SIM7080G-M" (at 0 30 0)(effects(font(size 1.27 1.27))))
      (property "Footprint" "lte-m-custom:SIM7080GM_LCC77" (at 0 28 0)(effects(font(size 1.27 1.27))hide))
      (property "LCSC" "C18548266" (at 0 26 0)(effects(font(size 1.27 1.27))hide))
      (symbol "SIM7080G-M_0_1"
        (rectangle(start -15.24 -20.32)(end 15.24 20.32)(stroke(width 0.254)(type default))(fill(type background))))
      (symbol "SIM7080G-M_1_1"
        (pin power_in  line(at -20.32 17.78 0)(length 5.08)(name "VBAT"(effects(font(size 1.016 1.016))))(number "1"(effects(font(size 1.016 1.016)))))
        (pin power_in  line(at -20.32 15.24 0)(length 5.08)(name "VBAT"(effects(font(size 1.016 1.016))))(number "2"(effects(font(size 1.016 1.016)))))
        (pin power_in  line(at -20.32 12.70 0)(length 5.08)(name "VBAT"(effects(font(size 1.016 1.016))))(number "3"(effects(font(size 1.016 1.016)))))
        (pin power_in  line(at -20.32 10.16 0)(length 5.08)(name "VBAT"(effects(font(size 1.016 1.016))))(number "4"(effects(font(size 1.016 1.016)))))
        (pin power_in  line(at -20.32  7.62 0)(length 5.08)(name "GND" (effects(font(size 1.016 1.016))))(number "5"(effects(font(size 1.016 1.016)))))
        (pin power_in  line(at -20.32  5.08 0)(length 5.08)(name "GND" (effects(font(size 1.016 1.016))))(number "6"(effects(font(size 1.016 1.016)))))
        (pin power_in  line(at -20.32  2.54 0)(length 5.08)(name "GND" (effects(font(size 1.016 1.016))))(number "7"(effects(font(size 1.016 1.016)))))
        (pin input     line(at -20.32  0.00 0)(length 5.08)(name "PWRKEY"(effects(font(size 1.016 1.016))))(number "17"(effects(font(size 1.016 1.016)))))
        (pin output    line(at -20.32 -2.54 0)(length 5.08)(name "STATUS"(effects(font(size 1.016 1.016))))(number "18"(effects(font(size 1.016 1.016)))))
        (pin input     line(at -20.32 -5.08 0)(length 5.08)(name "~{RESETN}"(effects(font(size 1.016 1.016))))(number "19"(effects(font(size 1.016 1.016)))))
        (pin output    line(at -20.32 -7.62 0)(length 5.08)(name "NETLIGHT"(effects(font(size 1.016 1.016))))(number "20"(effects(font(size 1.016 1.016)))))
        (pin output    line(at -20.32 -10.16 0)(length 5.08)(name "TXD"(effects(font(size 1.016 1.016))))(number "22"(effects(font(size 1.016 1.016)))))
        (pin input     line(at -20.32 -12.70 0)(length 5.08)(name "RXD"(effects(font(size 1.016 1.016))))(number "23"(effects(font(size 1.016 1.016)))))
        (pin output    line(at -20.32 -15.24 0)(length 5.08)(name "RTS"(effects(font(size 1.016 1.016))))(number "24"(effects(font(size 1.016 1.016)))))
        (pin input     line(at -20.32 -17.78 0)(length 5.08)(name "CTS"(effects(font(size 1.016 1.016))))(number "25"(effects(font(size 1.016 1.016)))))
        (pin power_out line(at  20.32 17.78 180)(length 5.08)(name "SIM_VDD"(effects(font(size 1.016 1.016))))(number "38"(effects(font(size 1.016 1.016)))))
        (pin bidirectional line(at 20.32 15.24 180)(length 5.08)(name "SIM_DATA"(effects(font(size 1.016 1.016))))(number "39"(effects(font(size 1.016 1.016)))))
        (pin output    line(at  20.32 12.70 180)(length 5.08)(name "SIM_CLK"(effects(font(size 1.016 1.016))))(number "40"(effects(font(size 1.016 1.016)))))
        (pin output    line(at  20.32 10.16 180)(length 5.08)(name "SIM_RST"(effects(font(size 1.016 1.016))))(number "41"(effects(font(size 1.016 1.016)))))
        (pin input     line(at  20.32  7.62 180)(length 5.08)(name "SIM_DET"(effects(font(size 1.016 1.016))))(number "42"(effects(font(size 1.016 1.016)))))
        (pin power_in  line(at  20.32  5.08 180)(length 5.08)(name "SIM_GND"(effects(font(size 1.016 1.016))))(number "43"(effects(font(size 1.016 1.016)))))
        (pin unspecified line(at 20.32  2.54 180)(length 5.08)(name "LTE_ANT"(effects(font(size 1.016 1.016))))(number "75"(effects(font(size 1.016 1.016)))))
        (pin unspecified line(at 20.32  0.00 180)(length 5.08)(name "GNSS_ANT"(effects(font(size 1.016 1.016))))(number "76"(effects(font(size 1.016 1.016)))))
        (pin power_in  line(at  20.32 -2.54 180)(length 5.08)(name "GND"(effects(font(size 1.016 1.016))))(number "77"(effects(font(size 1.016 1.016)))))
      )
    )'''

LIS_SYM='''    (symbol "Custom:LIS2DW12TR"
      (exclude_from_sim no)(in_bom yes)(on_board yes)(duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "U" (at 0 10 0)(effects(font(size 1.27 1.27))))
      (property "Value" "LIS2DW12TR" (at 0 8.5 0)(effects(font(size 1.27 1.27))))
      (property "Footprint" "Package_LGA:LGA-12_2x2mm_P0.5mm" (at 0 7 0)(effects(font(size 1.27 1.27))hide))
      (property "LCSC" "C189624" (at 0 5.5 0)(effects(font(size 1.27 1.27))hide))
      (symbol "LIS2DW12TR_0_1"
        (rectangle(start -10.16 -10.16)(end 10.16 7.62)(stroke(width 0.254)(type default))(fill(type background))))
      (symbol "LIS2DW12TR_1_1"
        (pin input      line(at -15.24  5.08 0)(length 5.08)(name "SDO/SA0"(effects(font(size 1.016 1.016))))(number "1" (effects(font(size 1.016 1.016)))))
        (pin power_in   line(at -15.24  2.54 0)(length 5.08)(name "VDD"    (effects(font(size 1.016 1.016))))(number "2" (effects(font(size 1.016 1.016)))))
        (pin input      line(at -15.24  0.00 0)(length 5.08)(name "SCL/SPC"(effects(font(size 1.016 1.016))))(number "3" (effects(font(size 1.016 1.016)))))
        (pin input      line(at -15.24 -2.54 0)(length 5.08)(name "~{CS}"  (effects(font(size 1.016 1.016))))(number "4" (effects(font(size 1.016 1.016)))))
        (pin output     line(at -15.24 -5.08 0)(length 5.08)(name "INT2"   (effects(font(size 1.016 1.016))))(number "5" (effects(font(size 1.016 1.016)))))
        (pin power_in   line(at -15.24 -7.62 0)(length 5.08)(name "GND"    (effects(font(size 1.016 1.016))))(number "6" (effects(font(size 1.016 1.016)))))
        (pin no_connect line(at  15.24  5.08 180)(length 5.08)(name "RES1" (effects(font(size 1.016 1.016))))(number "7" (effects(font(size 1.016 1.016)))))
        (pin no_connect line(at  15.24  2.54 180)(length 5.08)(name "RES2" (effects(font(size 1.016 1.016))))(number "8" (effects(font(size 1.016 1.016)))))
        (pin output     line(at  15.24  0.00 180)(length 5.08)(name "INT1"  (effects(font(size 1.016 1.016))))(number "9" (effects(font(size 1.016 1.016)))))
        (pin power_in   line(at  15.24 -2.54 180)(length 5.08)(name "GND"   (effects(font(size 1.016 1.016))))(number "10"(effects(font(size 1.016 1.016)))))
        (pin bidirectional line(at 15.24 -5.08 180)(length 5.08)(name "SDA/SDI"(effects(font(size 1.016 1.016))))(number "11"(effects(font(size 1.016 1.016)))))
        (pin power_in   line(at  15.24 -7.62 180)(length 5.08)(name "VDD_IO"(effects(font(size 1.016 1.016))))(number "12"(effects(font(size 1.016 1.016)))))
      )
    )'''

S1_SYM='''    (symbol "Custom:SMN-305"
      (exclude_from_sim no)(in_bom yes)(on_board yes)(duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "SIM" (at 0 10 0)(effects(font(size 1.27 1.27))))
      (property "Value" "SMN-305" (at 0 8.5 0)(effects(font(size 1.27 1.27))))
      (property "Footprint" "lte-m-custom:SIM_SMN-305" (at 0 7 0)(effects(font(size 1.27 1.27))hide))
      (property "LCSC" "C266890" (at 0 5.5 0)(effects(font(size 1.27 1.27))hide))
      (symbol "SMN-305_0_1"
        (rectangle(start -7.62 -7.62)(end 7.62 7.62)(stroke(width 0.254)(type default))(fill(type background))))
      (symbol "SMN-305_1_1"
        (pin power_in    line(at -12.70  5.08 0)(length 5.08)(name "VCC" (effects(font(size 1.016 1.016))))(number "1"(effects(font(size 1.016 1.016)))))
        (pin bidirectional line(at -12.70 2.54 0)(length 5.08)(name "DATA"(effects(font(size 1.016 1.016))))(number "2"(effects(font(size 1.016 1.016)))))
        (pin input       line(at -12.70  0.00 0)(length 5.08)(name "CLK" (effects(font(size 1.016 1.016))))(number "3"(effects(font(size 1.016 1.016)))))
        (pin input       line(at -12.70 -2.54 0)(length 5.08)(name "RST" (effects(font(size 1.016 1.016))))(number "4"(effects(font(size 1.016 1.016)))))
        (pin power_in    line(at -12.70 -5.08 0)(length 5.08)(name "GND" (effects(font(size 1.016 1.016))))(number "5"(effects(font(size 1.016 1.016)))))
        (pin input       line(at  12.70  0.00 180)(length 5.08)(name "~{CD}"(effects(font(size 1.016 1.016))))(number "6"(effects(font(size 1.016 1.016)))))
      )
    )'''

UFL_SYM='''    (symbol "Custom:U.FL-R-SMT"
      (exclude_from_sim no)(in_bom yes)(on_board yes)(duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "ANT" (at 0 5 0)(effects(font(size 1.27 1.27))))
      (property "Value" "U.FL-R-SMT" (at 0 3.5 0)(effects(font(size 1.27 1.27))))
      (property "Footprint" "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical" (at 0 2 0)(effects(font(size 1.27 1.27))hide))
      (property "LCSC" "C317592" (at 0 0.5 0)(effects(font(size 1.27 1.27))hide))
      (symbol "U.FL-R-SMT_0_1"
        (circle(center 0 0)(radius 2.54)(stroke(width 0.254)(type default))(fill(type background)))
        (polyline(pts(xy 0 -2.54)(xy 0 -5.08))(stroke(width 0.254)(type default))))
      (symbol "U.FL-R-SMT_1_1"
        (pin unspecified line(at 0  7.62 270)(length 2.54)(name "SIG"(effects(font(size 1.016 1.016))))(number "1"(effects(font(size 1.016 1.016)))))
        (pin power_in    line(at 0 -5.08  90)(length 2.54)(name "GND"(effects(font(size 1.016 1.016))))(number "2"(effects(font(size 1.016 1.016)))))
      )
    )'''

ANT_SYM='''    (symbol "Custom:ChipAntenna-2450"
      (exclude_from_sim no)(in_bom yes)(on_board yes)(duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "ANT" (at 0 5 0)(effects(font(size 1.27 1.27))))
      (property "Value" "2450AT18A100" (at 0 3.5 0)(effects(font(size 1.27 1.27))))
      (property "Footprint" "lte-m-custom:ChipAntenna_2x1.25mm" (at 0 2 0)(effects(font(size 1.27 1.27))hide))
      (symbol "ChipAntenna-2450_0_1"
        (polyline(pts(xy -2.54 0)(xy 2.54 0))(stroke(width 0.254)(type default)))
        (polyline(pts(xy -1.27 0)(xy -1.27 2.54)(xy 0 2.54)(xy 0 -2.54)(xy 1.27 -2.54)(xy 1.27 0))(stroke(width 0.254)(type default))))
      (symbol "ChipAntenna-2450_1_1"
        (pin unspecified line(at -5.08 0   0)(length 2.54)(name "RF" (effects(font(size 1.016 1.016))))(number "1"(effects(font(size 1.016 1.016)))))
        (pin power_in    line(at  5.08 0 180)(length 2.54)(name "GND"(effects(font(size 1.016 1.016))))(number "2"(effects(font(size 1.016 1.016)))))
      )
    )'''

USB_SYM='''    (symbol "Custom:USB-C-16P"
      (exclude_from_sim no)(in_bom yes)(on_board yes)(duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "J" (at 0 14 0)(effects(font(size 1.27 1.27))))
      (property "Value" "USB-C-16P" (at 0 12.5 0)(effects(font(size 1.27 1.27))))
      (property "Footprint" "lte-m-custom:USB_C_16P_SMD" (at 0 11 0)(effects(font(size 1.27 1.27))hide))
      (property "LCSC" "C2765186" (at 0 9.5 0)(effects(font(size 1.27 1.27))hide))
      (symbol "USB-C-16P_0_1"
        (rectangle(start -7.62 -12.7)(end 7.62 12.7)(stroke(width 0.254)(type default))(fill(type background)))
        (text "USB-C"(at 0 0 0)(effects(font(size 1.27 1.27)))))
      (symbol "USB-C-16P_1_1"
        (pin power_out   line(at -12.70 -10.16 0)(length 5.08)(name "VBUS"  (effects(font(size 1.016 1.016))))(number "A4"(effects(font(size 1.016 1.016)))))
        (pin bidirectional line(at -12.70 -7.62 0)(length 5.08)(name "D-"   (effects(font(size 1.016 1.016))))(number "A7"(effects(font(size 1.016 1.016)))))
        (pin bidirectional line(at -12.70 -5.08 0)(length 5.08)(name "D+"   (effects(font(size 1.016 1.016))))(number "A6"(effects(font(size 1.016 1.016)))))
        (pin passive     line(at -12.70 -2.54 0)(length 5.08)(name "CC1"   (effects(font(size 1.016 1.016))))(number "A5"(effects(font(size 1.016 1.016)))))
        (pin passive     line(at -12.70  0.00 0)(length 5.08)(name "CC2"   (effects(font(size 1.016 1.016))))(number "B5"(effects(font(size 1.016 1.016)))))
        (pin power_in    line(at -12.70  2.54 0)(length 5.08)(name "GND"   (effects(font(size 1.016 1.016))))(number "A1"(effects(font(size 1.016 1.016)))))
        (pin power_in    line(at -12.70  5.08 0)(length 5.08)(name "GND"   (effects(font(size 1.016 1.016))))(number "B1"(effects(font(size 1.016 1.016)))))
        (pin power_in    line(at -12.70  7.62 0)(length 5.08)(name "SHIELD"(effects(font(size 1.016 1.016))))(number "S1"(effects(font(size 1.016 1.016)))))
      )
    )'''

JST_SYM='''    (symbol "Custom:JST-GH-2P"
      (exclude_from_sim no)(in_bom yes)(on_board yes)(duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "J" (at 0 6 0)(effects(font(size 1.27 1.27))))
      (property "Value" "JST-GH-2P" (at 0 4.5 0)(effects(font(size 1.27 1.27))))
      (property "Footprint" "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal" (at 0 3 0)(effects(font(size 1.27 1.27))hide))
      (property "LCSC" "C160404" (at 0 1.5 0)(effects(font(size 1.27 1.27))hide))
      (symbol "JST-GH-2P_0_1"
        (rectangle(start -5.08 -3.81)(end 5.08 3.81)(stroke(width 0.254)(type default))(fill(type background)))
        (text "LiPo"(at 0 0 0)(effects(font(size 1.016 1.016)))))
      (symbol "JST-GH-2P_1_1"
        (pin passive line(at -10.16  1.27 0)(length 5.08)(name "+"(effects(font(size 1.016 1.016))))(number "1"(effects(font(size 1.016 1.016)))))
        (pin passive line(at -10.16 -1.27 0)(length 5.08)(name "-"(effects(font(size 1.016 1.016))))(number "2"(effects(font(size 1.016 1.016)))))
      )
    )'''

SW_SYM='''    (symbol "Custom:MSK12C02"
      (exclude_from_sim no)(in_bom yes)(on_board yes)(duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "SW" (at 0 5 0)(effects(font(size 1.27 1.27))))
      (property "Value" "MSK12C02" (at 0 3.5 0)(effects(font(size 1.27 1.27))))
      (property "Footprint" "lte-m-custom:SW_MSK12C02" (at 0 2 0)(effects(font(size 1.27 1.27))hide))
      (property "LCSC" "C431541" (at 0 0.5 0)(effects(font(size 1.27 1.27))hide))
      (symbol "MSK12C02_0_1"
        (polyline(pts(xy -3.81 -1.27)(xy -3.81 1.27))(stroke(width 0.254)(type default)))
        (polyline(pts(xy -3.81 0)(xy -1.27 1.27))(stroke(width 0.254)(type default)))
        (polyline(pts(xy 1.27 0)(xy 3.81 0))(stroke(width 0.254)(type default))))
      (symbol "MSK12C02_1_1"
        (pin passive line(at -6.35 0   0)(length 2.54)(name "A"(effects(font(size 1.016 1.016))))(number "1"(effects(font(size 1.016 1.016)))))
        (pin passive line(at  6.35 0 180)(length 2.54)(name "B"(effects(font(size 1.016 1.016))))(number "2"(effects(font(size 1.016 1.016)))))
      )
    )'''

# ── 要素ビルダー ─────────────────────────────────
class S:
    def __init__(self): self.items=[]

    def inst(self,lib_id,sx,sy,sr,ref,val,fp="",lcsc=""):
        self.items.append(f'''  (symbol (lib_id "{lib_id}") (at {sx} {sy} {sr}) (unit 1)
    (exclude_from_sim no)(in_bom yes)(on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "{ref}" (at {sx} {sy-3.5} 0)(effects(font(size 1.27 1.27))))
    (property "Value" "{val}" (at {sx} {sy-2} 0)(effects(font(size 1.27 1.27))))
    (property "Footprint" "{fp}" (at {sx} {sy} 0)(effects(font(size 1.27 1.27))hide))
    (property "LCSC" "{lcsc}" (at {sx} {sy} 0)(effects(font(size 1.27 1.27))hide))
  )''')

    def lbl(self,net,x,y,a=0):
        j="left" if a in(0,270) else "right"
        self.items.append(f'  (label "{net}" (at {x} {y} {a})\n    (effects(font(size 1.27 1.27))(justify {j}))\n    (uuid "{gen_uuid()}"))')

    def gnd(self,x,y):
        self.items.append(f'''  (symbol (lib_id "power:GND") (at {x} {y} 0)(unit 1)
    (exclude_from_sim no)(in_bom no)(on_board no)(uuid "{gen_uuid()}")
    (property "Reference" "#PWR"(at {x} {y+2.54} 0)(effects(font(size 1.27 1.27))hide))
    (property "Value" "GND"(at {x} {y+1.27} 0)(effects(font(size 1.27 1.27))))
    (property "Footprint" ""(at {x} {y} 0)(effects(font(size 1.27 1.27))hide)))''')

    def pwr(self,x,y):
        self.items.append(f'''  (symbol (lib_id "power:+3.3V") (at {x} {y} 0)(unit 1)
    (exclude_from_sim no)(in_bom no)(on_board no)(uuid "{gen_uuid()}")
    (property "Reference" "#PWR"(at {x} {y-2.54} 0)(effects(font(size 1.27 1.27))hide))
    (property "Value" "+3.3V"(at {x} {y-1.27} 0)(effects(font(size 1.27 1.27))))
    (property "Footprint" ""(at {x} {y} 0)(effects(font(size 1.27 1.27))hide)))''')

    def nc(self,x,y):
        self.items.append(f'  (no_connect (at {x} {y})(uuid "{gen_uuid()}"))')

    def wire(self,x1,y1,x2,y2):
        self.items.append(f'  (wire(pts(xy {x1} {y1})(xy {x2} {y2}))(stroke(width 0)(type default))(uuid "{gen_uuid()}"))')

    def pp(self,sx,sy,sa,pins,key): return pabs(sx,sy,sa,*pins[key])


def build():
    s = S()

    # ======================================================
    # J2: USB-C (16G, 20G) = (40.64, 50.80)
    # ======================================================
    J2x,J2y,J2a = 16*G,20*G,0
    s.inst("Custom:USB-C-16P",J2x,J2y,J2a,"J2","USB-C-16P",
           "lte-m-custom:USB_C_16P_SMD","C2765186")
    vbus = s.pp(J2x,J2y,J2a,P_USB,'VBUS'); s.lbl("VUSB",*vbus,180)
    s.nc(*s.pp(J2x,J2y,J2a,P_USB,'DM'))
    s.nc(*s.pp(J2x,J2y,J2a,P_USB,'DP'))
    for k in ('GND_A','GND_B','SH'): s.gnd(*s.pp(J2x,J2y,J2a,P_USB,k))

    # R1 (CC1 pull-down 5.1k): pin2直結→CC1, pin1→GND
    cc1 = s.pp(J2x,J2y,J2a,P_USB,'CC1')
    R1x = cc1[0]-3.81; R1y = cc1[1]  # rot=90: pin2=(+3.81,0)
    s.inst("Device:R",R1x,R1y,90,"R1","5.1k","Resistor_SMD:R_0402_1005Metric","C23186")
    s.gnd(*pabs(R1x,R1y,90,*P_R['2']))  # pin2 left (Y-flip後) → GND

    # R2 (CC2 pull-down 5.1k)
    cc2 = s.pp(J2x,J2y,J2a,P_USB,'CC2')
    R2x = cc2[0]-3.81; R2y = cc2[1]
    s.inst("Device:R",R2x,R2y,90,"R2","5.1k","Resistor_SMD:R_0402_1005Metric","C23186")
    s.gnd(*pabs(R2x,R2y,90,*P_R['2']))

    # ======================================================
    # U4: TP4056 (34G, 22G) = (86.36, 55.88)
    # ======================================================
    U4x,U4y,U4a = 34*G,22*G,0
    s.inst("Battery_Management:TP4056-42-ESOP8",U4x,U4y,U4a,"U4","TP4056",
           "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm","C16581")
    vcc4 = s.pp(U4x,U4y,U4a,P_TP4056,'VCC'); s.lbl("VUSB",*vcc4,270)
    bat4 = s.pp(U4x,U4y,U4a,P_TP4056,'BAT'); s.lbl("VBAT",*bat4,0)
    s.gnd(*s.pp(U4x,U4y,U4a,P_TP4056,'GND'))
    s.gnd(*s.pp(U4x,U4y,U4a,P_TP4056,'EPAD'))
    s.pwr(*s.pp(U4x,U4y,U4a,P_TP4056,'CE'))  # CE=HIGH常時ON
    s.nc(*s.pp(U4x,U4y,U4a,P_TP4056,'STDBY'))
    s.nc(*s.pp(U4x,U4y,U4a,P_TP4056,'TEMP'))
    chrg4 = s.pp(U4x,U4y,U4a,P_TP4056,'CHRG'); s.lbl("CHRG",*chrg4,180)

    # R3 (PROG 3.3k): pin2→PROG, pin1→GND
    prog4 = s.pp(U4x,U4y,U4a,P_TP4056,'PROG')
    R3x=prog4[0]; R3y=prog4[1]+3.81  # rot=0: pin2=(0,-3.81)→上
    s.inst("Device:R",R3x,R3y,0,"R3","3.3k","Resistor_SMD:R_0402_1005Metric","C25804")
    s.gnd(*pabs(R3x,R3y,0,*P_R['2']))  # pin2 下(Y-flip後)→GND

    # LED1 + R4 (充電インジケータ): CHRG→R4→LED→GND
    # R4 rot=90: pin2右=CHRG, pin1左=LED.A
    R4x = chrg4[0]-3.81; R4y = chrg4[1]
    s.inst("Device:R",R4x,R4y,90,"R4","1k","Resistor_SMD:R_0402_1005Metric","C11702")
    led1a = pabs(R4x,R4y,90,*P_R['2'])  # R4.pin2 左(Y-flip後) → LED.A
    # LED1 rot=0: A右=R4.pin1, K左=GND
    LED1x = led1a[0]-3.81; LED1y = led1a[1]
    s.inst("Device:LED",LED1x,LED1y,0,"LED1","RED","LED_SMD:LED_0402_1005Metric","C2286")
    s.gnd(*pabs(LED1x,LED1y,0,*P_LED['K']))  # K→GND

    # ======================================================
    # SW1: 電源スイッチ (45G, 20G) = (114.30, 50.80)
    # ======================================================
    SW1x,SW1y,SW1a = 45*G,20*G,0
    s.inst("Custom:MSK12C02",SW1x,SW1y,SW1a,"SW1","MSK12C02","lte-m-custom:SW_MSK12C02","C431541")
    s.lbl("VBAT",   *s.pp(SW1x,SW1y,SW1a,P_SW,'A'),180)
    s.lbl("VBAT_SW",*s.pp(SW1x,SW1y,SW1a,P_SW,'B'),0)

    # ======================================================
    # J1: JST LiPo (45G, 28G) = (114.30, 71.12)
    # ======================================================
    J1x,J1y,J1a = 45*G,28*G,0
    s.inst("Custom:JST-GH-2P",J1x,J1y,J1a,"J1","JST-GH-1.25mm-2P",
           "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal","C160404")
    s.lbl("VBAT",*s.pp(J1x,J1y,J1a,P_JST,'+'),180)
    s.gnd(*s.pp(J1x,J1y,J1a,P_JST,'-'))

    # ======================================================
    # U5: XC6220 LDO 3.3V (47G, 38G) = (119.38, 96.52)
    # ======================================================
    U5x,U5y,U5a = 47*G,38*G,0
    s.inst("Regulator_Linear:XC6220B331MR",U5x,U5y,U5a,"U5","XC6220B331MR-G",
           "Package_TO_SOT_SMD:SOT-23-5","C86534")
    s.lbl("VBAT_SW",*s.pp(U5x,U5y,U5a,P_XC6220,'VIN'),180)
    s.lbl("VBAT_SW",*s.pp(U5x,U5y,U5a,P_XC6220,'CE'),180)  # CE=VINで常時ON
    s.gnd(*s.pp(U5x,U5y,U5a,P_XC6220,'GND'))
    s.nc(*s.pp(U5x,U5y,U5a,P_XC6220,'NC'))
    s.pwr(*s.pp(U5x,U5y,U5a,P_XC6220,'VOUT'))

    # C9 (VIN 10μF), C10 (VOUT 10μF)
    vin5 = s.pp(U5x,U5y,U5a,P_XC6220,'VIN')
    vout5 = s.pp(U5x,U5y,U5a,P_XC6220,'VOUT')
    C9x=vin5[0]-5*G; C9y=vin5[1]
    s.inst("Device:C",C9x,C9y,0,"C9","10uF","Capacitor_SMD:C_0805_2012Metric","C15850")
    s.lbl("VBAT_SW",*pabs(C9x,C9y,0,*P_C['1']),270); s.gnd(*pabs(C9x,C9y,0,*P_C['2']))
    C10x=vout5[0]+5*G; C10y=vout5[1]
    s.inst("Device:C",C10x,C10y,0,"C10","10uF","Capacitor_SMD:C_0805_2012Metric","C15850")
    s.pwr(*pabs(C10x,C10y,0,*P_C['1'])); s.gnd(*pabs(C10x,C10y,0,*P_C['2']))

    # ======================================================
    # U1: SIM7080G-M (94G, 34G) = (238.76, 86.36)
    # ======================================================
    U1x,U1y,U1a = 94*G,34*G,0
    s.inst("Custom:SIM7080G-M",U1x,U1y,U1a,"U1","SIM7080G-M","lte-m-custom:SIM7080GM_LCC77","C18548266")
    for k in ('VBAT1','VBAT2','VBAT3','VBAT4'):
        s.lbl("VBAT_SW",*s.pp(U1x,U1y,U1a,P_SIM,k),180)
    for k in ('GND5','GND6','GND7','GND77'):
        s.gnd(*s.pp(U1x,U1y,U1a,P_SIM,k))
    s.lbl("SIM_PWRKEY",*s.pp(U1x,U1y,U1a,P_SIM,'PWRKEY'),180)
    s.lbl("SIM_STATUS", *s.pp(U1x,U1y,U1a,P_SIM,'STATUS'),180)
    s.lbl("SIM_RESETN", *s.pp(U1x,U1y,U1a,P_SIM,'RESETN'),180)
    s.nc(*s.pp(U1x,U1y,U1a,P_SIM,'NETLIGHT'))
    s.lbl("SIM_TXD",*s.pp(U1x,U1y,U1a,P_SIM,'TXD'),180)
    s.lbl("SIM_RXD",*s.pp(U1x,U1y,U1a,P_SIM,'RXD'),180)
    s.nc(*s.pp(U1x,U1y,U1a,P_SIM,'RTS')); s.nc(*s.pp(U1x,U1y,U1a,P_SIM,'CTS'))
    s.lbl("SIM_VDD", *s.pp(U1x,U1y,U1a,P_SIM,'SIM_VDD'),0)
    s.lbl("SIM_DATA",*s.pp(U1x,U1y,U1a,P_SIM,'SIM_DATA'),0)
    s.lbl("SIM_CLK", *s.pp(U1x,U1y,U1a,P_SIM,'SIM_CLK'),0)
    s.lbl("SIM_RST", *s.pp(U1x,U1y,U1a,P_SIM,'SIM_RST'),0)
    s.nc(*s.pp(U1x,U1y,U1a,P_SIM,'SIM_DET'))
    s.gnd(*s.pp(U1x,U1y,U1a,P_SIM,'SIM_GND'))
    s.lbl("LTE_ANT", *s.pp(U1x,U1y,U1a,P_SIM,'LTE_ANT'),0)
    s.lbl("GNSS_ANT",*s.pp(U1x,U1y,U1a,P_SIM,'GNSS_ANT'),0)
    # C11, C12 (VBAT 10μF)
    for cx,cy,ref in [(U1x-4*G,U1y-13*G,"C11"),(U1x+4*G,U1y-13*G,"C12")]:
        s.inst("Device:C",cx,cy,0,ref,"10uF","Capacitor_SMD:C_0805_2012Metric","C15850")
        s.lbl("VBAT_SW",*pabs(cx,cy,0,*P_C['1']),270); s.gnd(*pabs(cx,cy,0,*P_C['2']))

    # ======================================================
    # SIM1: nano SIM (122G, 22G) = (309.88, 55.88)
    # ======================================================
    S1x,S1y,S1a = 122*G,22*G,0
    s.inst("Custom:SMN-305",S1x,S1y,S1a,"SIM1","SMN-305","lte-m-custom:SIM_SMN-305","C266890")
    s.lbl("SIM_VDD", *s.pp(S1x,S1y,S1a,P_SIM1,'VCC'),180)
    s.lbl("SIM_DATA",*s.pp(S1x,S1y,S1a,P_SIM1,'DATA'),180)
    s.lbl("SIM_CLK", *s.pp(S1x,S1y,S1a,P_SIM1,'CLK'),180)
    s.lbl("SIM_RST", *s.pp(S1x,S1y,S1a,P_SIM1,'RST'),180)
    s.gnd(*s.pp(S1x,S1y,S1a,P_SIM1,'GND'))
    s.nc(*s.pp(S1x,S1y,S1a,P_SIM1,'CD'))

    # ======================================================
    # ANT1: U.FL LTE (122G, 32G) = (309.88, 81.28)
    # ======================================================
    A1x,A1y,A1a = 122*G,32*G,0
    s.inst("Custom:U.FL-R-SMT",A1x,A1y,A1a,"ANT1","U.FL-LTE",
           "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical","C317592")
    s.lbl("LTE_ANT",*s.pp(A1x,A1y,A1a,P_UFL,'SIG'),90)
    s.gnd(*s.pp(A1x,A1y,A1a,P_UFL,'GND'))

    # ======================================================
    # ANT2: U.FL GNSS (122G, 41G) = (309.88, 104.14)
    # ======================================================
    A2x,A2y,A2a = 122*G,41*G,0
    s.inst("Custom:U.FL-R-SMT",A2x,A2y,A2a,"ANT2","U.FL-GNSS",
           "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical","C317592")
    s.lbl("GNSS_ANT",*s.pp(A2x,A2y,A2a,P_UFL,'SIG'),90)
    s.gnd(*s.pp(A2x,A2y,A2a,P_UFL,'GND'))

    # ======================================================
    # U2: ESP32-C3 (35G, 79G) = (88.90, 200.66)
    # ======================================================
    U2x,U2y,U2a = 35*G,79*G,0
    s.inst("MCU_Espressif:ESP32-C3",U2x,U2y,U2a,"U2","ESP32-C3",
           "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.7x3.7mm","C2838500")
    for k in ('VDD3P3','VDD3P3_RTC','VDD3P3_CPU','VDDA','VDD_SPI'):
        s.pwr(*s.pp(U2x,U2y,U2a,P_E32,k))
    s.gnd(*s.pp(U2x,U2y,U2a,P_E32,'GND'))
    # CHIP_EN → R5(10k) → +3.3V
    en2 = s.pp(U2x,U2y,U2a,P_E32,'CHIP_EN')
    R5x=en2[0]+3.81; R5y=en2[1]  # rot=90: pin2左→EN, pin1右→+3.3V
    s.inst("Device:R",R5x,R5y,90,"R5","10k","Resistor_SMD:R_0402_1005Metric","C25744")
    s.pwr(*pabs(R5x,R5y,90,*P_R['1']))  # pin1 右→+3.3V
    # LNA_IN → WIFI_ANT
    s.lbl("WIFI_ANT",*s.pp(U2x,U2y,U2a,P_E32,'LNA_IN'),0)
    # UART → SIM7080G-M
    s.lbl("SIM_TXD",*s.pp(U2x,U2y,U2a,P_E32,'U0RXD'),180)
    s.lbl("SIM_RXD",*s.pp(U2x,U2y,U2a,P_E32,'U0TXD'),180)
    # I2C
    s.lbl("I2C_SDA",*s.pp(U2x,U2y,U2a,P_E32,'GPIO8'),180)
    s.lbl("I2C_SCL",*s.pp(U2x,U2y,U2a,P_E32,'GPIO9'),180)
    # Control
    s.lbl("ACCEL_INT1",*s.pp(U2x,U2y,U2a,P_E32,'GPIO10'),180)
    s.lbl("SIM_PWRKEY",*s.pp(U2x,U2y,U2a,P_E32,'GPIO3'),180)
    s.lbl("SIM_RESETN",*s.pp(U2x,U2y,U2a,P_E32,'GPIO2'),180)
    s.lbl("SIM_STATUS",*s.pp(U2x,U2y,U2a,P_E32,'XTAL_32K_P'),180)
    # GPIO18/19 = USB D-/D+: USB-C充電専用のため未使用
    s.nc(*s.pp(U2x,U2y,U2a,P_E32,'GPIO18'))
    s.nc(*s.pp(U2x,U2y,U2a,P_E32,'GPIO19'))
    for k in ('MTMS','MTDI','MTCK','MTDO','SPIHD','SPIWP','SPICS0',
              'SPICLK','SPID','SPIQ','XTAL_32K_N','XTAL_N','XTAL_P'):
        s.nc(*s.pp(U2x,U2y,U2a,P_E32,k))
    # バイパスコン C1-C6
    vb = s.pp(U2x,U2y,U2a,P_E32,'VDD3P3')
    for i,(cx,cy) in enumerate([(vb[0]-6*G,vb[1]-4*G),(vb[0]-4*G,vb[1]-4*G),
                                  (vb[0]-2*G,vb[1]-4*G),(vb[0],vb[1]-4*G),
                                  (vb[0]+2*G,vb[1]-4*G),(vb[0]+4*G,vb[1]-4*G)]):
        s.inst("Device:C",cx,cy,0,f"C{i+1}","100nF","Capacitor_SMD:C_0402_1005Metric","C14663")
        s.pwr(*pabs(cx,cy,0,*P_C['1'])); s.gnd(*pabs(cx,cy,0,*P_C['2']))

    # ======================================================
    # ANT3: チップアンテナ (18G, 79G) = (45.72, 200.66)
    # ======================================================
    A3x,A3y,A3a = 18*G,79*G,0
    s.inst("Custom:ChipAntenna-2450",A3x,A3y,A3a,"ANT3","2450AT18A100","lte-m-custom:ChipAntenna_2x1.25mm","")
    s.lbl("WIFI_ANT",*s.pp(A3x,A3y,A3a,P_ANT,'RF'),180)
    s.gnd(*s.pp(A3x,A3y,A3a,P_ANT,'GND'))

    # I2C プルアップ R6, R7
    for rx,ry,ref,net in [(64*G,75*G,"R6","I2C_SDA"),(64*G,79*G,"R7","I2C_SCL")]:
        s.inst("Device:R",rx,ry,0,ref,"4.7k","Resistor_SMD:R_0402_1005Metric","C25900")
        s.pwr(*pabs(rx,ry,0,*P_R['1']))
        s.lbl(net,*pabs(rx,ry,0,*P_R['2']),90)

    # ======================================================
    # U3: LIS2DW12TR (96G, 79G) = (243.84, 200.66)
    # ======================================================
    U3x,U3y,U3a = 96*G,79*G,0
    s.inst("Custom:LIS2DW12TR",U3x,U3y,U3a,"U3","LIS2DW12TR",
           "Package_LGA:LGA-12_2x2mm_P0.5mm","C189624")
    s.pwr(*s.pp(U3x,U3y,U3a,P_LIS,'VDD'))
    s.pwr(*s.pp(U3x,U3y,U3a,P_LIS,'VDD_IO'))
    s.gnd(*s.pp(U3x,U3y,U3a,P_LIS,'GND6'))
    s.gnd(*s.pp(U3x,U3y,U3a,P_LIS,'GND10'))
    s.lbl("I2C_SCL",   *s.pp(U3x,U3y,U3a,P_LIS,'SCL'),180)
    s.lbl("I2C_SDA",   *s.pp(U3x,U3y,U3a,P_LIS,'SDA'),0)
    s.lbl("ACCEL_INT1",*s.pp(U3x,U3y,U3a,P_LIS,'INT1'),0)
    s.pwr(*s.pp(U3x,U3y,U3a,P_LIS,'CS'))      # CS=HIGH→I2Cモード
    s.gnd(*s.pp(U3x,U3y,U3a,P_LIS,'SDO'))     # SA0=GND→addr 0x18
    for k in ('INT2','RES1','RES2'): s.nc(*s.pp(U3x,U3y,U3a,P_LIS,k))
    # C7, C8 バイパス
    for cx,cy,ref in [(U3x-3*G,U3y-7*G,"C7"),(U3x+3*G,U3y-7*G,"C8")]:
        s.inst("Device:C",cx,cy,0,ref,"100nF","Capacitor_SMD:C_0402_1005Metric","C14663")
        s.pwr(*pabs(cx,cy,0,*P_C['1'])); s.gnd(*pabs(cx,cy,0,*P_C['2']))

    # ── PWR_FLAG: 外部駆動ネットに追加 ─────────────────
    # VBAT_SW / VBAT / GND は外部から駆動されるため PWR_FLAG が必要
    for net, x, y in [
        ("VBAT_SW",  50*G, 22*G),  # (127.00, 55.88)
        ("VBAT",     44*G, 22*G),  # (111.76, 55.88)
        ("VUSB",     34*G, 16*G),  # (86.36, 40.64)
    ]:
        s.items.append(f'''  (symbol (lib_id "power:PWR_FLAG") (at {x} {y} 0) (unit 1)
    (exclude_from_sim no)(in_bom no)(on_board no)(uuid "{gen_uuid()}")
    (property "Reference" "#PWR"(at {x} {y-2.54} 0)(effects(font(size 1.27 1.27))hide))
    (property "Value" "PWR_FLAG"(at {x} {y-1.27} 0)(effects(font(size 1.27 1.27))))
    (property "Footprint" ""(at {x} {y} 0)(effects(font(size 1.27 1.27))hide)))''')
        s.lbl(net, x, y, 270)

    # ── lib_symbols ─────────────────────────────────
    std = "".join(ext(l,n)+"\n" for l,n in [
        ("MCU_Espressif","ESP32-C3"),
        ("Battery_Management","TP4056-42-ESOP8"),
        ("Regulator_Linear","XC6220B331MR"),
        ("Device","R"),("Device","C"),("Device","LED"),
        ("power","GND"),("power","+3.3V"),("power","PWR_FLAG"),
    ])

    lib = f"""  (lib_symbols
{SIM_SYM}
{LIS_SYM}
{S1_SYM}
{UFL_SYM}
{ANT_SYM}
{USB_SYM}
{JST_SYM}
{SW_SYM}
{std}  )"""

    body = "\n".join(s.items)
    return f"""(kicad_sch
  (version 20250114)(generator "eeschema")(generator_version "10.0.3")
  (uuid "{gen_uuid()}")
  (paper "A3")
  (title_block
    (title "LTE-M 猫GPSトラッカー")(date "2026-06-05")(rev "v1.1")(company "Personal")
    (comment 1 "30x35mm  SIM7080G-M + ESP32-C3 + LIS2DW12 + TP4056 + XC6220")
    (comment 2 "USB-C→TP4056→LiPo350mAh→SW1→VBAT_SW→SIM7080G-M / XC6220 3.3V")
    (comment 3 "JLCPCB PCBA全量  手はんだゼロ  SIM7080G-Mピン番号はHW Design v1.02確認要")
  )

{lib}

{body}

  (sheet_instances(path "/"(page "1")))
)
"""

if __name__=="__main__":
    out="/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_sch"
    c=build()
    with open(out,"w") as f: f.write(c)
    print(f"Written: {out}  ({len(c):,} bytes)")

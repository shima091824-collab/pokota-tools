#!/usr/bin/env python3
"""
LTE-M 猫GPSトラッカー KiCad 回路図生成スクリプト
KiCad 10.0 (.kicad_sch S-expression format)

コンポーネント:
  U1: SIM7080G-M  (LTE-M + GPS, カスタムシンボル)
  U2: ESP32-C3    (MCU + WiFi, MCU_Espressif標準)
  U3: LIS2DW12TR  (加速度センサー, カスタムシンボル)
  U4: TP4056-42-ESOP8 (充電IC, Battery_Management標準)
  U5: XC6220B331MR    (LDO 3.3V, Regulator_Linear標準)
  J1: JST-GH 1.25mm 2P (LiPoコネクタ)
  J2: USB-C 16P       (充電コネクタ)
  SIM1: SMN-305       (nano SIMホルダー)
  ANT1: U.FL          (LTE)
  ANT2: U.FL          (GNSS)
  ANT3: チップアンテナ (WiFi 2.4GHz)
  SW1: MSK12C02       (電源スイッチ)
  LED1: 赤LED 0402    (充電インジケータ)
  R1,R2: 5.1kΩ       (USB-C CC pull-down)
  R3: 3.3kΩ          (TP4056 PROG → 364mA)
  R4: 1kΩ            (LED電流制限)
  C1-C8: 100nF 0402  (バイパスコン)
  C9,C10: 10μF 0805  (バルクコン)
  C11,C12: 10μF 0805 (SIM7080G-M電源デカップリング)
"""

import uuid
import sys

def gen_uuid():
    return str(uuid.uuid4())

# ─────────────────────────────────────────────
# カスタムシンボル定義（lib_symbols内に埋め込む）
# ─────────────────────────────────────────────

SIM7080G_SYMBOL = '''    (symbol "Custom:SIM7080G-M"
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "U"
        (at 0 32 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "SIM7080G-M"
        (at 0 30 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "Custom:SIM7080GM_LCC77"
        (at 0 28 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "https://simcom.ee/documents/SIM7080G/SIM7080G_Hardware%20Design_V1.02.pdf"
        (at 0 26 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "LCSC" "C18548266"
        (at 0 24 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Description" "LTE-M Cat-M1/NB2 + GNSS module, LCC+LGA-77"
        (at 0 22 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "SIM7080G-M_0_1"
        (rectangle (start -15.24 -27.94) (end 15.24 20.32)
          (stroke (width 0.254) (type default))
          (fill (type background))
        )
      )
      (symbol "SIM7080G-M_1_1"
        (pin power_in line (at -20.32 17.78 0) (length 5.08)
          (name "VBAT" (effects (font (size 1.016 1.016))))
          (number "1" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -20.32 15.24 0) (length 5.08)
          (name "VBAT" (effects (font (size 1.016 1.016))))
          (number "2" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -20.32 12.7 0) (length 5.08)
          (name "VBAT" (effects (font (size 1.016 1.016))))
          (number "3" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -20.32 10.16 0) (length 5.08)
          (name "VBAT" (effects (font (size 1.016 1.016))))
          (number "4" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -20.32 7.62 0) (length 5.08)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "5" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -20.32 5.08 0) (length 5.08)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "6" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -20.32 2.54 0) (length 5.08)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "7" (effects (font (size 1.016 1.016))))
        )
        (pin input line (at -20.32 0 0) (length 5.08)
          (name "PWRKEY" (effects (font (size 1.016 1.016))))
          (number "17" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at -20.32 -2.54 0) (length 5.08)
          (name "STATUS" (effects (font (size 1.016 1.016))))
          (number "18" (effects (font (size 1.016 1.016))))
        )
        (pin input line (at -20.32 -5.08 0) (length 5.08)
          (name "~{RESETN}" (effects (font (size 1.016 1.016))))
          (number "19" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at -20.32 -7.62 0) (length 5.08)
          (name "NETLIGHT" (effects (font (size 1.016 1.016))))
          (number "20" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at -20.32 -10.16 0) (length 5.08)
          (name "TXD" (effects (font (size 1.016 1.016))))
          (number "22" (effects (font (size 1.016 1.016))))
        )
        (pin input line (at -20.32 -12.7 0) (length 5.08)
          (name "RXD" (effects (font (size 1.016 1.016))))
          (number "23" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at -20.32 -15.24 0) (length 5.08)
          (name "RTS" (effects (font (size 1.016 1.016))))
          (number "24" (effects (font (size 1.016 1.016))))
        )
        (pin input line (at -20.32 -17.78 0) (length 5.08)
          (name "CTS" (effects (font (size 1.016 1.016))))
          (number "25" (effects (font (size 1.016 1.016))))
        )
        (pin power_out line (at 20.32 17.78 180) (length 5.08)
          (name "SIM_VDD" (effects (font (size 1.016 1.016))))
          (number "38" (effects (font (size 1.016 1.016))))
        )
        (pin bidirectional line (at 20.32 15.24 180) (length 5.08)
          (name "SIM_DATA" (effects (font (size 1.016 1.016))))
          (number "39" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at 20.32 12.7 180) (length 5.08)
          (name "SIM_CLK" (effects (font (size 1.016 1.016))))
          (number "40" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at 20.32 10.16 180) (length 5.08)
          (name "SIM_RST" (effects (font (size 1.016 1.016))))
          (number "41" (effects (font (size 1.016 1.016))))
        )
        (pin input line (at 20.32 7.62 180) (length 5.08)
          (name "SIM_DET" (effects (font (size 1.016 1.016))))
          (number "42" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at 20.32 5.08 180) (length 5.08)
          (name "SIM_GND" (effects (font (size 1.016 1.016))))
          (number "43" (effects (font (size 1.016 1.016))))
        )
        (pin unspecified line (at 20.32 2.54 180) (length 5.08)
          (name "LTE_ANT" (effects (font (size 1.016 1.016))))
          (number "75" (effects (font (size 1.016 1.016))))
        )
        (pin unspecified line (at 20.32 0 180) (length 5.08)
          (name "GNSS_ANT" (effects (font (size 1.016 1.016))))
          (number "76" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at 20.32 -2.54 180) (length 5.08)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "77" (effects (font (size 1.016 1.016))))
        )
      )
    )'''

LIS2DW12_SYMBOL = '''    (symbol "Custom:LIS2DW12TR"
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "U"
        (at 0 10 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "LIS2DW12TR"
        (at 0 8.5 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "Package_LGA:LGA-12_2x2mm_P0.5mm"
        (at 0 7 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "https://www.st.com/resource/en/datasheet/lis2dw12.pdf"
        (at 0 5.5 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "LCSC" "C189624"
        (at 0 4 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Description" "3-axis MEMS accelerometer, ultra-low-power, LGA-12 2x2mm"
        (at 0 2.5 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "LIS2DW12TR_0_1"
        (rectangle (start -10.16 -10.16) (end 10.16 7.62)
          (stroke (width 0.254) (type default))
          (fill (type background))
        )
      )
      (symbol "LIS2DW12TR_1_1"
        (pin input line (at -15.24 5.08 0) (length 5.08)
          (name "SDO/SA0" (effects (font (size 1.016 1.016))))
          (number "1" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -15.24 2.54 0) (length 5.08)
          (name "VDD" (effects (font (size 1.016 1.016))))
          (number "2" (effects (font (size 1.016 1.016))))
        )
        (pin input line (at -15.24 0 0) (length 5.08)
          (name "SCL/SPC" (effects (font (size 1.016 1.016))))
          (number "3" (effects (font (size 1.016 1.016))))
        )
        (pin input line (at -15.24 -2.54 0) (length 5.08)
          (name "~{CS}" (effects (font (size 1.016 1.016))))
          (number "4" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at -15.24 -5.08 0) (length 5.08)
          (name "INT2" (effects (font (size 1.016 1.016))))
          (number "5" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -15.24 -7.62 0) (length 5.08)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "6" (effects (font (size 1.016 1.016))))
        )
        (pin no_connect line (at 15.24 5.08 180) (length 5.08)
          (name "RES1" (effects (font (size 1.016 1.016))))
          (number "7" (effects (font (size 1.016 1.016))))
        )
        (pin no_connect line (at 15.24 2.54 180) (length 5.08)
          (name "RES2" (effects (font (size 1.016 1.016))))
          (number "8" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at 15.24 0 180) (length 5.08)
          (name "INT1" (effects (font (size 1.016 1.016))))
          (number "9" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at 15.24 -2.54 180) (length 5.08)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "10" (effects (font (size 1.016 1.016))))
        )
        (pin bidirectional line (at 15.24 -5.08 180) (length 5.08)
          (name "SDA/SDI" (effects (font (size 1.016 1.016))))
          (number "11" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at 15.24 -7.62 180) (length 5.08)
          (name "VDD_IO" (effects (font (size 1.016 1.016))))
          (number "12" (effects (font (size 1.016 1.016))))
        )
      )
    )'''

# nano SIM ホルダー
SMN305_SYMBOL = '''    (symbol "Custom:SMN-305"
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "SIM"
        (at 0 10 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "SMN-305"
        (at 0 8.5 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "Custom:SIM_SMN-305"
        (at 0 7 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "LCSC" "C266890"
        (at 0 5.5 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Description" "Nano SIM card holder, SMD flip type"
        (at 0 4 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "SMN-305_0_1"
        (rectangle (start -7.62 -7.62) (end 7.62 7.62)
          (stroke (width 0.254) (type default))
          (fill (type background))
        )
      )
      (symbol "SMN-305_1_1"
        (pin power_in line (at -12.7 5.08 0) (length 5.08)
          (name "VCC" (effects (font (size 1.016 1.016))))
          (number "1" (effects (font (size 1.016 1.016))))
        )
        (pin bidirectional line (at -12.7 2.54 0) (length 5.08)
          (name "DATA" (effects (font (size 1.016 1.016))))
          (number "2" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at -12.7 0 0) (length 5.08)
          (name "CLK" (effects (font (size 1.016 1.016))))
          (number "3" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at -12.7 -2.54 0) (length 5.08)
          (name "RST" (effects (font (size 1.016 1.016))))
          (number "4" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -12.7 -5.08 0) (length 5.08)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "5" (effects (font (size 1.016 1.016))))
        )
        (pin output line (at 12.7 0 180) (length 5.08)
          (name "~{CD}" (effects (font (size 1.016 1.016))))
          (number "6" (effects (font (size 1.016 1.016))))
        )
      )
    )'''

# U.FL コネクタ
UFL_SYMBOL = '''    (symbol "Custom:U.FL-R-SMT"
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "ANT"
        (at 0 5 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "U.FL-R-SMT"
        (at 0 3.5 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical"
        (at 0 2 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "LCSC" "C317592"
        (at 0 0.5 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "U.FL-R-SMT_0_1"
        (circle (center 0 0) (radius 2.54)
          (stroke (width 0.254) (type default))
          (fill (type background))
        )
        (polyline
          (pts (xy 0 -2.54) (xy 0 -5.08))
          (stroke (width 0.254) (type default))
        )
      )
      (symbol "U.FL-R-SMT_1_1"
        (pin unspecified line (at 0 -7.62 90) (length 2.54)
          (name "SIG" (effects (font (size 1.016 1.016))))
          (number "1" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at 0 5.08 270) (length 2.54)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "2" (effects (font (size 1.016 1.016))))
        )
      )
    )'''

# チップアンテナ (2.4GHz WiFi用)
CHIP_ANT_SYMBOL = '''    (symbol "Custom:ChipAntenna-2450"
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "ANT"
        (at 0 5 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "2450AT18A100"
        (at 0 3.5 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "Custom:ChipAntenna_2x1.25mm"
        (at 0 2 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Description" "2.4GHz chip antenna 2x1.25mm"
        (at 0 0.5 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "ChipAntenna-2450_0_1"
        (polyline
          (pts (xy -2.54 0) (xy 2.54 0))
          (stroke (width 0.254) (type default))
        )
        (polyline
          (pts (xy -1.27 0) (xy -1.27 2.54) (xy 0 2.54) (xy 0 -2.54) (xy 1.27 -2.54) (xy 1.27 0))
          (stroke (width 0.254) (type default))
        )
      )
      (symbol "ChipAntenna-2450_1_1"
        (pin unspecified line (at -5.08 0 0) (length 2.54)
          (name "RF" (effects (font (size 1.016 1.016))))
          (number "1" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at 5.08 0 180) (length 2.54)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "2" (effects (font (size 1.016 1.016))))
        )
      )
    )'''

# USB-C コネクタ (簡易版 - 充電専用)
USBC_SYMBOL = '''    (symbol "Custom:USB-C-16P"
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "J"
        (at 0 14 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "USB-C-16P"
        (at 0 12.5 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "Connector_USB:USB_C_Receptacle_GCT_USB4135-GF-A_Vertical"
        (at 0 11 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "LCSC" "C2765186"
        (at 0 9.5 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "USB-C-16P_0_1"
        (rectangle (start -7.62 -12.7) (end 7.62 12.7)
          (stroke (width 0.254) (type default))
          (fill (type background))
        )
        (text "USB-C" (at 0 0 0)
          (effects (font (size 1.27 1.27)))
        )
      )
      (symbol "USB-C-16P_1_1"
        (pin power_out line (at -12.7 10.16 0) (length 5.08)
          (name "VBUS" (effects (font (size 1.016 1.016))))
          (number "A4" (effects (font (size 1.016 1.016))))
        )
        (pin bidirectional line (at -12.7 7.62 0) (length 5.08)
          (name "D-" (effects (font (size 1.016 1.016))))
          (number "A7" (effects (font (size 1.016 1.016))))
        )
        (pin bidirectional line (at -12.7 5.08 0) (length 5.08)
          (name "D+" (effects (font (size 1.016 1.016))))
          (number "A6" (effects (font (size 1.016 1.016))))
        )
        (pin passive line (at -12.7 2.54 0) (length 5.08)
          (name "CC1" (effects (font (size 1.016 1.016))))
          (number "A5" (effects (font (size 1.016 1.016))))
        )
        (pin passive line (at -12.7 0 0) (length 5.08)
          (name "CC2" (effects (font (size 1.016 1.016))))
          (number "B5" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -12.7 -2.54 0) (length 5.08)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "A1" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -12.7 -5.08 0) (length 5.08)
          (name "GND" (effects (font (size 1.016 1.016))))
          (number "B1" (effects (font (size 1.016 1.016))))
        )
        (pin power_in line (at -12.7 -7.62 0) (length 5.08)
          (name "SHIELD" (effects (font (size 1.016 1.016))))
          (number "S1" (effects (font (size 1.016 1.016))))
        )
      )
    )'''

# JST-GH 1.25mm 2P コネクタ
JST_SYMBOL = '''    (symbol "Custom:JST-GH-2P"
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "J"
        (at 0 6 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "JST-GH-2P"
        (at 0 4.5 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal"
        (at 0 3 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "LCSC" "C160404"
        (at 0 1.5 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "JST-GH-2P_0_1"
        (rectangle (start -5.08 -3.81) (end 5.08 3.81)
          (stroke (width 0.254) (type default))
          (fill (type background))
        )
        (text "LiPo" (at 0 0 0)
          (effects (font (size 1.016 1.016)))
        )
      )
      (symbol "JST-GH-2P_1_1"
        (pin passive line (at -10.16 1.27 0) (length 5.08)
          (name "+" (effects (font (size 1.016 1.016))))
          (number "1" (effects (font (size 1.016 1.016))))
        )
        (pin passive line (at -10.16 -1.27 0) (length 5.08)
          (name "-" (effects (font (size 1.016 1.016))))
          (number "2" (effects (font (size 1.016 1.016))))
        )
      )
    )'''

# MSK12C02 電源スイッチ
SW_SYMBOL = '''    (symbol "Custom:MSK12C02"
      (exclude_from_sim no)
      (in_bom yes)
      (on_board yes)
      (in_pos_files yes)
      (duplicate_pin_numbers_are_jumpers no)
      (property "Reference" "SW"
        (at 0 5 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "MSK12C02"
        (at 0 3.5 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "Custom:SW_MSK12C02"
        (at 0 2 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "LCSC" "C431541"
        (at 0 0.5 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "MSK12C02_0_1"
        (polyline
          (pts (xy -3.81 -1.27) (xy -3.81 1.27))
          (stroke (width 0.254) (type default))
        )
        (polyline
          (pts (xy -3.81 0) (xy -1.27 1.27))
          (stroke (width 0.254) (type default))
        )
        (polyline
          (pts (xy 1.27 0) (xy 3.81 0))
          (stroke (width 0.254) (type default))
        )
      )
      (symbol "MSK12C02_1_1"
        (pin passive line (at -6.35 0 0) (length 2.54)
          (name "A" (effects (font (size 1.016 1.016))))
          (number "1" (effects (font (size 1.016 1.016))))
        )
        (pin passive line (at 6.35 0 180) (length 2.54)
          (name "B" (effects (font (size 1.016 1.016))))
          (number "2" (effects (font (size 1.016 1.016))))
        )
      )
    )'''


def extract_std_symbol(lib_file, sym_name):
    """KiCad標準ライブラリからシンボル定義を抽出し、LibName:SymName形式にリネームする"""
    SYMDIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
    new_name = f"{lib_file}:{sym_name}"
    with open(f"{SYMDIR}/{lib_file}.kicad_sym") as f:
        content = f.read()

    pattern = f'\t(symbol "{sym_name}"'
    idx = content.find(pattern)
    if idx == -1:
        return None

    depth = 0
    i = idx
    while i < len(content):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                sym = content[idx:i+1]
                # 親シンボルのみLibrary:Symbol形式にリネーム（サブシンボルはそのまま）
                sym = sym.replace(f'(symbol "{sym_name}"', f'(symbol "{new_name}"', 1)
                return sym
        i += 1
    return None


def build_schematic():
    """回路図全体を構築する"""

    # 標準シンボルを抽出
    esp32c3_sym = extract_std_symbol("MCU_Espressif", "ESP32-C3")
    tp4056_sym = extract_std_symbol("Battery_Management", "TP4056-42-ESOP8")
    xc6220_sym = extract_std_symbol("Regulator_Linear", "XC6220B331MR")

    # Device symbols
    r_sym = extract_std_symbol("Device", "R")
    c_sym = extract_std_symbol("Device", "C")
    led_sym = extract_std_symbol("Device", "LED")

    # Power symbols
    gnd_sym = extract_std_symbol("power", "GND")
    pwr3v3_sym = extract_std_symbol("power", "+3.3V")

    lib_sym_section = f"""  (lib_symbols
{SIM7080G_SYMBOL}
{LIS2DW12_SYMBOL}
{SMN305_SYMBOL}
{UFL_SYMBOL}
{CHIP_ANT_SYMBOL}
{USBC_SYMBOL}
{JST_SYMBOL}
{SW_SYMBOL}
{esp32c3_sym}
{tp4056_sym}
{xc6220_sym}
{r_sym}
{c_sym}
{led_sym}
{gnd_sym}
{pwr3v3_sym}
  )"""

    # ─────────────────────────────────────────
    # シンボルインスタンスと配線の定義
    # 座標はmm単位 (KiCad内部)
    # ─────────────────────────────────────────

    # レイアウト概要:
    # ┌────────────────────────────────────────────┐ A3 420×297mm
    # │ [USB-C][TP4056][SW][JST]  | [SIM7080G-M]   │
    # │ Power section (x:20-130)  | (x:160-310)    │
    # │ [XC6220]                  |   [U.FL×2]     │
    # ├────────────────────────────────────────────┤
    # │ [ESP32-C3]   [ChipAnt]    | [LIS2DW12]    │
    # │ (x:20-130, y:150-250)     | (x:200-280)   │
    # └────────────────────────────────────────────┘

    components = []
    wires = []
    labels = []
    no_connects = []
    power_symbols = []

    # ─── J2: USB-C コネクタ ───
    j2_x, j2_y = 40, 50
    components.append(f'''  (symbol (lib_id "Custom:USB-C-16P") (at {j2_x} {j2_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "J2" (at {j2_x} {j2_y-16} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "USB-C-16P" (at {j2_x} {j2_y-14.5} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Connector_USB:USB_C_Receptacle_GCT_USB4135-GF-A_Vertical" (at {j2_x} {j2_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C2765186" (at {j2_x} {j2_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # USB-C VBUS → net label VUSB
    vbus_pin_x = j2_x - 12.7
    vbus_pin_y = j2_y - 10.16
    labels.append(f'''  (label "VUSB" (at {vbus_pin_x-2.54} {vbus_pin_y} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    wires.append(f'''  (wire (pts (xy {vbus_pin_x} {vbus_pin_y}) (xy {vbus_pin_x-2.54} {vbus_pin_y}))
    (stroke (width 0) (type default))
    (uuid "{gen_uuid()}")
  )''')

    # CC1, CC2 → R1, R2 (5.1kΩ to GND)
    cc1_x, cc1_y = vbus_pin_x, j2_y - 2.54
    cc2_x, cc2_y = vbus_pin_x, j2_y

    # R1 (CC1 pull-down)
    r1_x, r1_y = cc1_x - 10.16, cc1_y
    components.append(f'''  (symbol (lib_id "Device:R") (at {r1_x} {r1_y} 90) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "R1" (at {r1_x} {r1_y-2} 90)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "5.1k" (at {r1_x} {r1_y+2} 90)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0402_1005Metric" (at {r1_x} {r1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C23186" (at {r1_x} {r1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    wires.append(f'''  (wire (pts (xy {cc1_x} {cc1_y}) (xy {r1_x+1.27} {cc1_y}))
    (stroke (width 0) (type default))
    (uuid "{gen_uuid()}")
  )''')
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {r1_x-1.27} {cc1_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {r1_x-1.27} {cc1_y+2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {r1_x-1.27} {cc1_y+1.27} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {r1_x-1.27} {cc1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # R2 (CC2 pull-down)
    r2_x, r2_y = cc2_x - 10.16, cc2_y
    components.append(f'''  (symbol (lib_id "Device:R") (at {r2_x} {r2_y} 90) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "R2" (at {r2_x} {r2_y-2} 90)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "5.1k" (at {r2_x} {r2_y+2} 90)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0402_1005Metric" (at {r2_x} {r2_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C23186" (at {r2_x} {r2_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    wires.append(f'''  (wire (pts (xy {cc2_x} {cc2_y}) (xy {r2_x+1.27} {cc2_y}))
    (stroke (width 0) (type default))
    (uuid "{gen_uuid()}")
  )''')
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {r2_x-1.27} {cc2_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {r2_x-1.27} {cc2_y+2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {r2_x-1.27} {cc2_y+1.27} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {r2_x-1.27} {cc2_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # USB-C GND → GND power symbols
    gnd1_x, gnd1_y = vbus_pin_x, j2_y + 2.54  # A1 GND
    gnd2_x, gnd2_y = vbus_pin_x, j2_y + 5.08  # B1 GND
    gnd3_x, gnd3_y = vbus_pin_x, j2_y + 7.62  # S1 SHIELD
    for gx, gy in [(gnd1_x, gnd1_y), (gnd2_x, gnd2_y), (gnd3_x, gnd3_y)]:
        power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {gx-2.54} {gy} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {gx-2.54} {gy+2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {gx-2.54} {gy+1.27} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {gx-2.54} {gy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
        wires.append(f'''  (wire (pts (xy {gx} {gy}) (xy {gx-2.54} {gy}))
    (stroke (width 0) (type default))
    (uuid "{gen_uuid()}")
  )''')

    # D+, D- → no connect (充電専用)
    no_connects.append(f'  (no_connect (at {vbus_pin_x} {j2_y-7.62}) (uuid "{gen_uuid()}"))')  # D-
    no_connects.append(f'  (no_connect (at {vbus_pin_x} {j2_y-5.08}) (uuid "{gen_uuid()}"))')  # D+

    # ─── U4: TP4056 ───
    u4_x, u4_y = 85, 55
    components.append(f'''  (symbol (lib_id "Battery_Management:TP4056-42-ESOP8") (at {u4_x} {u4_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "U4" (at {u4_x} {u4_y-12} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "TP4056" (at {u4_x} {u4_y-10.5} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" (at {u4_x} {u4_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C16581" (at {u4_x} {u4_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # TP4056 VIN ← VUSB
    labels.append(f'''  (label "VUSB" (at {u4_x-12.7} {u4_y-5.08} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')
    # TP4056 VBAT/OUT → VBAT net
    labels.append(f'''  (label "VBAT" (at {u4_x+12.7} {u4_y-2.54} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')
    # TP4056 GND
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {u4_x} {u4_y+10.16} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u4_x} {u4_y+12.7} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {u4_x} {u4_y+11.43} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u4_x} {u4_y+10.16} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # R3: PROG抵抗 3.3kΩ (364mA充電電流設定)
    r3_x, r3_y = u4_x - 7.62, u4_y + 5.08
    components.append(f'''  (symbol (lib_id "Device:R") (at {r3_x} {r3_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "R3" (at {r3_x+2} {r3_y} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "3.3k" (at {r3_x-2} {r3_y} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0402_1005Metric" (at {r3_x} {r3_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C25804" (at {r3_x} {r3_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    # PROG pin to R3 top, R3 bottom to GND
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {r3_x} {r3_y+2.54} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {r3_x} {r3_y+5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {r3_x} {r3_y+3.81} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {r3_x} {r3_y+2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # TP4056 CHRG → LED1 (charge indicator)
    # LED1
    led1_x, led1_y = u4_x - 10.16, u4_y - 2.54
    components.append(f'''  (symbol (lib_id "Device:LED") (at {led1_x} {led1_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "LED1" (at {led1_x} {led1_y-3} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "RED_LED" (at {led1_x} {led1_y+3} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "LED_SMD:LED_0402_1005Metric" (at {led1_x} {led1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C2286" (at {led1_x} {led1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    # R4: LED電流制限 1kΩ
    r4_x, r4_y = led1_x - 5.08, led1_y
    components.append(f'''  (symbol (lib_id "Device:R") (at {r4_x} {r4_y} 90) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "R4" (at {r4_x} {r4_y-2} 90)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "1k" (at {r4_x} {r4_y+2} 90)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0402_1005Metric" (at {r4_x} {r4_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C11702" (at {r4_x} {r4_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    # CHRG → R4 → LED1 → GND
    labels.append(f'''  (label "CHRG" (at {r4_x-2.54} {r4_y} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {led1_x+5.08} {led1_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {led1_x+5.08} {led1_y+2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {led1_x+5.08} {led1_y+1.27} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {led1_x+5.08} {led1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ─── SW1: 電源スイッチ ───
    sw1_x, sw1_y = 115, 50
    components.append(f'''  (symbol (lib_id "Custom:MSK12C02") (at {sw1_x} {sw1_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "SW1" (at {sw1_x} {sw1_y-7} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "MSK12C02" (at {sw1_x} {sw1_y+7} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Custom:SW_MSK12C02" (at {sw1_x} {sw1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C431541" (at {sw1_x} {sw1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    # VBAT → SW1 → VBAT_SW
    labels.append(f'''  (label "VBAT" (at {sw1_x-8.89} {sw1_y} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    labels.append(f'''  (label "VBAT_SW" (at {sw1_x+8.89} {sw1_y} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')

    # ─── J1: JST LiPoコネクタ ───
    j1_x, j1_y = 115, 70
    components.append(f'''  (symbol (lib_id "Custom:JST-GH-2P") (at {j1_x} {j1_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "J1" (at {j1_x} {j1_y-7} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "JST-GH-1.25mm-2P" (at {j1_x} {j1_y+7} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal" (at {j1_x} {j1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C160404" (at {j1_x} {j1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    # J1 + → VBAT
    labels.append(f'''  (label "VBAT" (at {j1_x-12.7} {j1_y-1.27} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    # J1 - → GND
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {j1_x-12.7} {j1_y+1.27} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {j1_x-12.7} {j1_y+3.81} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {j1_x-12.7} {j1_y+2.54} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {j1_x-12.7} {j1_y+1.27} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ─── U5: XC6220 LDO 3.3V ───
    u5_x, u5_y = 115, 95
    components.append(f'''  (symbol (lib_id "Regulator_Linear:XC6220B331MR") (at {u5_x} {u5_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "U5" (at {u5_x} {u5_y-8} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "XC6220B331MR-G" (at {u5_x} {u5_y+8} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Package_TO_SOT_SMD:SOT-25" (at {u5_x} {u5_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C86534" (at {u5_x} {u5_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    # XC6220 VIN ← VBAT_SW
    labels.append(f'''  (label "VBAT_SW" (at {u5_x-10.16} {u5_y-2.54} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    # XC6220 VOUT → +3.3V
    power_symbols.append(f'''  (symbol (lib_id "power:+3.3V") (at {u5_x+10.16} {u5_y-2.54} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u5_x+10.16} {u5_y-5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "+3.3V" (at {u5_x+10.16} {u5_y-3.81} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u5_x+10.16} {u5_y-2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    # XC6220 GND
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {u5_x} {u5_y+7.62} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u5_x} {u5_y+10.16} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {u5_x} {u5_y+8.89} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u5_x} {u5_y+7.62} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # LDO デカップリングコンデンサ (C9: 10μF input, C10: 10μF output)
    c9_x, c9_y = u5_x - 7.62, u5_y + 2.54
    c10_x, c10_y = u5_x + 7.62, u5_y + 2.54
    for ci, (cx, cy, ref, val, lcsc) in enumerate([(c9_x, c9_y, "C9", "10μF", "C15850"), (c10_x, c10_y, "C10", "10μF", "C15850")]):
        components.append(f'''  (symbol (lib_id "Device:C") (at {cx} {cy} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "{ref}" (at {cx+2} {cy} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "{val}" (at {cx+2} {cy+1.5} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {cx} {cy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "{lcsc}" (at {cx} {cy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
        power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {cx} {cy+3.81} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {cx} {cy+6.35} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {cx} {cy+5.08} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {cx} {cy+3.81} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ─── U1: SIM7080G-M ───
    u1_x, u1_y = 235, 80
    components.append(f'''  (symbol (lib_id "Custom:SIM7080G-M") (at {u1_x} {u1_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "U1" (at {u1_x} {u1_y-34} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "SIM7080G-M" (at {u1_x} {u1_y-32} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Custom:SIM7080GM_LCC77" (at {u1_x} {u1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C18548266" (at {u1_x} {u1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # SIM7080G-M VBAT (4ピン) ← VBAT_SW
    for i, vy_offset in enumerate([17.78, 15.24, 12.7, 10.16]):
        labels.append(f'''  (label "VBAT_SW" (at {u1_x-20.32} {u1_y-vy_offset} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')

    # SIM7080G-M GND (ピン5,6,7,77)
    for vy_offset in [7.62, 5.08, 2.54, -(-2.54)]:  # pin5,6,7
        power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {u1_x-20.32} {u1_y-vy_offset} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u1_x-20.32} {u1_y-vy_offset+2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {u1_x-20.32} {u1_y-vy_offset+1.27} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u1_x-20.32} {u1_y-vy_offset} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    # pin77 GND (right side)
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {u1_x+20.32} {u1_y+2.54} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u1_x+20.32} {u1_y+5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {u1_x+20.32} {u1_y+3.81} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u1_x+20.32} {u1_y+2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # SIM7080G-M UART → ESP32-C3 (net labels)
    labels.append(f'''  (label "SIM_TXD" (at {u1_x-20.32} {u1_y+10.16} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')  # TXD (pin22)
    labels.append(f'''  (label "SIM_RXD" (at {u1_x-20.32} {u1_y+12.7} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')  # RXD (pin23)
    no_connects.append(f'  (no_connect (at {u1_x-20.32} {u1_y+15.24}) (uuid "{gen_uuid()}"))')  # RTS
    no_connects.append(f'  (no_connect (at {u1_x-20.32} {u1_y+17.78}) (uuid "{gen_uuid()}"))')  # CTS

    # Control signals
    labels.append(f'''  (label "SIM_PWRKEY" (at {u1_x-20.32} {u1_y} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    labels.append(f'''  (label "SIM_STATUS" (at {u1_x-20.32} {u1_y+2.54} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    labels.append(f'''  (label "SIM_RESETN" (at {u1_x-20.32} {u1_y+5.08} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    no_connects.append(f'  (no_connect (at {u1_x-20.32} {u1_y+7.62}) (uuid "{gen_uuid()}"))')  # NETLIGHT

    # SIM interface → SIM1 holder (right side)
    labels.append(f'''  (label "SIM_VDD" (at {u1_x+20.32} {u1_y-17.78} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')
    labels.append(f'''  (label "SIM_DATA" (at {u1_x+20.32} {u1_y-15.24} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')
    labels.append(f'''  (label "SIM_CLK" (at {u1_x+20.32} {u1_y-12.7} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')
    labels.append(f'''  (label "SIM_RST" (at {u1_x+20.32} {u1_y-10.16} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')
    no_connects.append(f'  (no_connect (at {u1_x+20.32} {u1_y-7.62}) (uuid "{gen_uuid()}"))')  # SIM_DET
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {u1_x+20.32} {u1_y-5.08} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u1_x+20.32} {u1_y-2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {u1_x+20.32} {u1_y-3.81} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u1_x+20.32} {u1_y-5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # LTE_ANT → ANT1 U.FL (net label)
    labels.append(f'''  (label "LTE_ANT" (at {u1_x+20.32} {u1_y-2.54} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')
    # GNSS_ANT → ANT2 U.FL (net label)
    labels.append(f'''  (label "GNSS_ANT" (at {u1_x+20.32} {u1_y} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')

    # SIM7080G-M デカップリング C11, C12 (VBAT)
    c11_x, c11_y = u1_x - 7.62, u1_y - 25.4
    c12_x, c12_y = u1_x + 7.62, u1_y - 25.4
    for cx, cy, ref in [(c11_x, c11_y, "C11"), (c12_x, c12_y, "C12")]:
        components.append(f'''  (symbol (lib_id "Device:C") (at {cx} {cy} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "{ref}" (at {cx+2} {cy} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "10μF" (at {cx+2} {cy+1.5} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at {cx} {cy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C15850" (at {cx} {cy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
        labels.append(f'''  (label "VBAT_SW" (at {cx} {cy-3.81} 90)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
        power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {cx} {cy+3.81} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {cx} {cy+6.35} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {cx} {cy+5.08} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {cx} {cy+3.81} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ─── ANT1: U.FL (LTE) ───
    ant1_x, ant1_y = 300, 78
    components.append(f'''  (symbol (lib_id "Custom:U.FL-R-SMT") (at {ant1_x} {ant1_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "ANT1" (at {ant1_x+5} {ant1_y} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "U.FL-LTE" (at {ant1_x+5} {ant1_y+2} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical" (at {ant1_x} {ant1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C317592" (at {ant1_x} {ant1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    labels.append(f'''  (label "LTE_ANT" (at {ant1_x} {ant1_y+7.62} 270)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {ant1_x} {ant1_y-5.08} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {ant1_x} {ant1_y-7.62} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {ant1_x} {ant1_y-6.35} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {ant1_x} {ant1_y-5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ─── ANT2: U.FL (GNSS) ───
    ant2_x, ant2_y = 300, 100
    components.append(f'''  (symbol (lib_id "Custom:U.FL-R-SMT") (at {ant2_x} {ant2_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "ANT2" (at {ant2_x+5} {ant2_y} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "U.FL-GNSS" (at {ant2_x+5} {ant2_y+2} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical" (at {ant2_x} {ant2_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C317592" (at {ant2_x} {ant2_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    labels.append(f'''  (label "GNSS_ANT" (at {ant2_x} {ant2_y+7.62} 270)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {ant2_x} {ant2_y-5.08} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {ant2_x} {ant2_y-7.62} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {ant2_x} {ant2_y-6.35} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {ant2_x} {ant2_y-5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ─── SIM1: nano SIMホルダー ───
    sim1_x, sim1_y = 300, 55
    components.append(f'''  (symbol (lib_id "Custom:SMN-305") (at {sim1_x} {sim1_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "SIM1" (at {sim1_x} {sim1_y-12} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "SMN-305" (at {sim1_x} {sim1_y+12} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Custom:SIM_SMN-305" (at {sim1_x} {sim1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C266890" (at {sim1_x} {sim1_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    # SIM1 connections via net labels
    labels.append(f'''  (label "SIM_VDD" (at {sim1_x-15.24} {sim1_y-5.08} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    labels.append(f'''  (label "SIM_DATA" (at {sim1_x-15.24} {sim1_y-2.54} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    labels.append(f'''  (label "SIM_CLK" (at {sim1_x-15.24} {sim1_y} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    labels.append(f'''  (label "SIM_RST" (at {sim1_x-15.24} {sim1_y+2.54} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {sim1_x-15.24} {sim1_y+5.08} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {sim1_x-15.24} {sim1_y+7.62} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {sim1_x-15.24} {sim1_y+6.35} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {sim1_x-15.24} {sim1_y+5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    no_connects.append(f'  (no_connect (at {sim1_x+12.7} {sim1_y}) (uuid "{gen_uuid()}"))')  # ~CD

    # ─── U2: ESP32-C3 ───
    u2_x, u2_y = 80, 195
    components.append(f'''  (symbol (lib_id "MCU_Espressif:ESP32-C3") (at {u2_x} {u2_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "U2" (at {u2_x} {u2_y-27} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "ESP32-C3" (at {u2_x} {u2_y-25} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.7x3.7mm" (at {u2_x} {u2_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C2838500" (at {u2_x} {u2_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ESP32-C3 VDD3P3_RTC, VDD3P3_CPU → +3.3V
    for i, (px, py) in enumerate([(-22.86, u2_y-22.86), (-22.86, u2_y-20.32)]):
        power_symbols.append(f'''  (symbol (lib_id "power:+3.3V") (at {u2_x+px-2.54} {py} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u2_x+px-2.54} {py-2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "+3.3V" (at {u2_x+px-2.54} {py-1.27} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u2_x+px-2.54} {py} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ESP32-C3 GND
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {u2_x} {u2_y+25.4} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u2_x} {u2_y+27.94} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {u2_x} {u2_y+26.67} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u2_x} {u2_y+25.4} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ESP32-C3 UART to SIM7080G-M (GPIO20=RX, GPIO21=TX)
    # Right side: GPIO0-21 pins
    labels.append(f'''  (label "SIM_TXD" (at {u2_x+22.86} {u2_y+7.62} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # GPIO20 = UART RX ← SIM_TXD
    labels.append(f'''  (label "SIM_RXD" (at {u2_x+22.86} {u2_y+10.16} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # GPIO21 = UART TX → SIM_RXD

    # SIM control signals (GPIO3, GPIO4, GPIO5)
    labels.append(f'''  (label "SIM_PWRKEY" (at {u2_x+22.86} {u2_y+2.54} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # GPIO3
    labels.append(f'''  (label "SIM_STATUS" (at {u2_x+22.86} {u2_y+5.08} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # GPIO4
    labels.append(f'''  (label "SIM_RESETN" (at {u2_x+22.86} {u2_y+0} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # GPIO5

    # I2C to LIS2DW12 (GPIO8=SDA, GPIO9=SCL)
    labels.append(f'''  (label "I2C_SDA" (at {u2_x+22.86} {u2_y-5.08} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # GPIO8
    labels.append(f'''  (label "I2C_SCL" (at {u2_x+22.86} {u2_y-2.54} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # GPIO9

    # ACCEL INT1 (GPIO6)
    labels.append(f'''  (label "ACCEL_INT1" (at {u2_x+22.86} {u2_y-7.62} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # GPIO6

    # USB D+/D- for programming (GPIO18, GPIO19)
    labels.append(f'''  (label "USB_DP" (at {u2_x+22.86} {u2_y+15.24} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # GPIO19 = USB D+
    labels.append(f'''  (label "USB_DM" (at {u2_x+22.86} {u2_y+12.7} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # GPIO18 = USB D-

    # Chip antenna connection (CHIP_ANT pin, ESP32-C3 pin12)
    labels.append(f'''  (label "WIFI_ANT" (at {u2_x-22.86} {u2_y-10.16} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')

    # EN pin → +3.3V via 10kΩ (left side)
    # BOOT/GPIO9 → +3.3V via 10kΩ (boot mode: high=normal)
    # Unused GPIOs → no_connect
    # (省略: KiCad GUI で設定)

    # ESP32-C3 EN pin プルアップ
    ren_x, ren_y = u2_x - 30.48, u2_y - 25.4
    components.append(f'''  (symbol (lib_id "Device:R") (at {ren_x} {ren_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "R5" (at {ren_x+2} {ren_y} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "10k" (at {ren_x-2} {ren_y} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0402_1005Metric" (at {ren_x} {ren_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C25744" (at {ren_x} {ren_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    power_symbols.append(f'''  (symbol (lib_id "power:+3.3V") (at {ren_x} {ren_y-2.54} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {ren_x} {ren_y-5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "+3.3V" (at {ren_x} {ren_y-3.81} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {ren_x} {ren_y-2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    labels.append(f'''  (label "ESP_EN" (at {ren_x} {ren_y+2.54} 270)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')
    labels.append(f'''  (label "ESP_EN" (at {u2_x-22.86} {u2_y-17.78} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')

    # ─── ANT3: チップアンテナ (WiFi 2.4GHz) ───
    ant3_x, ant3_y = 40, 195
    components.append(f'''  (symbol (lib_id "Custom:ChipAntenna-2450") (at {ant3_x} {ant3_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "ANT3" (at {ant3_x} {ant3_y-7} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "2450AT18A100" (at {ant3_x} {ant3_y+7} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Custom:ChipAntenna_2x1.25mm" (at {ant3_x} {ant3_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
    labels.append(f'''  (label "WIFI_ANT" (at {ant3_x+7.62} {ant3_y} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {ant3_x-7.62} {ant3_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {ant3_x-7.62} {ant3_y+2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {ant3_x-7.62} {ant3_y+1.27} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {ant3_x-7.62} {ant3_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ─── U3: LIS2DW12TR ───
    u3_x, u3_y = 250, 195
    components.append(f'''  (symbol (lib_id "Custom:LIS2DW12TR") (at {u3_x} {u3_y} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "U3" (at {u3_x} {u3_y-12} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "LIS2DW12TR" (at {u3_x} {u3_y+12} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Package_LGA:LGA-12_2x2mm_P0.5mm" (at {u3_x} {u3_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C189624" (at {u3_x} {u3_y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # LIS2DW12 VDD, VDD_IO ← +3.3V
    for py_off in [-(-5.08+u3_y)+u3_y, -(-7.62+u3_y)+u3_y]:
        pass
    power_symbols.append(f'''  (symbol (lib_id "power:+3.3V") (at {u3_x-15.24} {u3_y-2.54} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u3_x-15.24} {u3_y-5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "+3.3V" (at {u3_x-15.24} {u3_y-3.81} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u3_x-15.24} {u3_y-2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')  # VDD (pin2)
    power_symbols.append(f'''  (symbol (lib_id "power:+3.3V") (at {u3_x+15.24} {u3_y+7.62} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u3_x+15.24} {u3_y+5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "+3.3V" (at {u3_x+15.24} {u3_y+6.35} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u3_x+15.24} {u3_y+7.62} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')  # VDD_IO (pin12)

    # LIS2DW12 GND (pin6, pin10)
    for py_off in [7.62, 2.54]:
        power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {u3_x-15.24} {u3_y-py_off} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u3_x-15.24} {u3_y-py_off+2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {u3_x-15.24} {u3_y-py_off+1.27} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u3_x-15.24} {u3_y-py_off} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # LIS2DW12 I2C connections
    labels.append(f'''  (label "I2C_SCL" (at {u3_x-15.24} {u3_y} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')  # SCL pin3
    labels.append(f'''  (label "I2C_SDA" (at {u3_x+15.24} {u3_y+5.08} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # SDA pin11

    # LIS2DW12 INT1 → ESP32-C3
    labels.append(f'''  (label "ACCEL_INT1" (at {u3_x+15.24} {u3_y} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')  # INT1 pin9

    # CS → VDD_IO (I2C mode: CS high)
    labels.append(f'''  (label "I2C_CS_TIE" (at {u3_x-15.24} {u3_y+2.54} 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "{gen_uuid()}")
  )''')  # CS pin4 → +3.3V

    # SDO/SA0 → GND (I2C address = 0x18)
    power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {u3_x-15.24} {u3_y-5.08} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {u3_x-15.24} {u3_y-2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {u3_x-15.24} {u3_y-3.81} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {u3_x-15.24} {u3_y-5.08} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')  # SDO/SA0 → GND (addr=0x18)

    # INT2, RES1, RES2 → no_connect
    no_connects.append(f'  (no_connect (at {u3_x-15.24} {u3_y+5.08}) (uuid "{gen_uuid()}"))')   # INT2
    no_connects.append(f'  (no_connect (at {u3_x+15.24} {u3_y-5.08}) (uuid "{gen_uuid()}"))')  # RES1
    no_connects.append(f'  (no_connect (at {u3_x+15.24} {u3_y-2.54}) (uuid "{gen_uuid()}"))')  # RES2

    # LIS2DW12 バイパスコン C7, C8 (100nF)
    c7_x, c7_y = u3_x + 7.62, u3_y - 15.24
    c8_x, c8_y = u3_x - 7.62, u3_y - 15.24
    for cx, cy, ref in [(c7_x, c7_y, "C7"), (c8_x, c8_y, "C8")]:
        components.append(f'''  (symbol (lib_id "Device:C") (at {cx} {cy} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "{ref}" (at {cx+2} {cy} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "100nF" (at {cx+2} {cy+1.5} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Capacitor_SMD:C_0402_1005Metric" (at {cx} {cy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C14663" (at {cx} {cy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
        power_symbols.append(f'''  (symbol (lib_id "power:+3.3V") (at {cx} {cy-3.81} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {cx} {cy-6.35} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "+3.3V" (at {cx} {cy-5.08} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {cx} {cy-3.81} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
        power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {cx} {cy+3.81} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {cx} {cy+6.35} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {cx} {cy+5.08} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {cx} {cy+3.81} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # ESP32-C3 バイパスコン C1-C6 (100nF)
    for ci, (cx, cy, ref) in enumerate([
        (u2_x-15.24, u2_y-35, "C1"),
        (u2_x-7.62, u2_y-35, "C2"),
        (u2_x, u2_y-35, "C3"),
        (u2_x+7.62, u2_y-35, "C4"),
        (u2_x+15.24, u2_y-35, "C5"),
        (u2_x+22.86, u2_y-35, "C6"),
    ]):
        components.append(f'''  (symbol (lib_id "Device:C") (at {cx} {cy} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "{ref}" (at {cx+2} {cy} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "100nF" (at {cx+2} {cy+1.5} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Capacitor_SMD:C_0402_1005Metric" (at {cx} {cy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C14663" (at {cx} {cy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
        power_symbols.append(f'''  (symbol (lib_id "power:+3.3V") (at {cx} {cy-3.81} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {cx} {cy-6.35} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "+3.3V" (at {cx} {cy-5.08} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {cx} {cy-3.81} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
        power_symbols.append(f'''  (symbol (lib_id "power:GND") (at {cx} {cy+3.81} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {cx} {cy+6.35} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "GND" (at {cx} {cy+5.08} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {cx} {cy+3.81} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')

    # I2C プルアップ抵抗 R6 (SDA), R7 (SCL) → +3.3V
    r6_x, r6_y = 190, 185
    r7_x, r7_y = 190, 190
    for rx, ry, ref, lbl in [(r6_x, r6_y, "R6", "I2C_SDA"), (r7_x, r7_y, "R7", "I2C_SCL")]:
        components.append(f'''  (symbol (lib_id "Device:R") (at {rx} {ry} 90) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{gen_uuid()}")
    (property "Reference" "{ref}" (at {rx} {ry-2} 90)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "4.7k" (at {rx} {ry+2} 90)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0402_1005Metric" (at {rx} {ry} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "LCSC" "C25900" (at {rx} {ry} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
        power_symbols.append(f'''  (symbol (lib_id "power:+3.3V") (at {rx-1.27} {ry} 0) (unit 1)
    (exclude_from_sim no) (in_bom no) (on_board no)
    (uuid "{gen_uuid()}")
    (property "Reference" "#PWR" (at {rx-1.27} {ry-2.54} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "+3.3V" (at {rx-1.27} {ry-1.27} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {rx-1.27} {ry} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
  )''')
        labels.append(f'''  (label "{lbl}" (at {rx+1.27} {ry} 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "{gen_uuid()}")
  )''')

    # ─────────────────────────────────────────
    # 回路図全体を組み立て
    # ─────────────────────────────────────────

    all_items = (
        components +
        power_symbols +
        labels +
        wires +
        no_connects
    )

    items_str = "\n".join(all_items)

    schematic = f"""(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "10.0.3")
  (uuid "{gen_uuid()}")

  (paper "A3")

  (title_block
    (title "LTE-M 猫GPSトラッカー")
    (date "2026-06-05")
    (rev "v1.0")
    (company "Personal")
    (comment 1 "PCB: 30x35mm  SIM7080G-M + ESP32-C3 + LIS2DW12 + TP4056 + XC6220")
    (comment 2 "電源: USB-C 5V → TP4056 → 350mAh LiPo → SIM7080G-M(VBAT) / XC6220 3.3V")
    (comment 3 "JLCPCB PCBA全量委託  手はんだゼロ  アンテナ・LiPoのみプラグイン")
    (comment 4 "⚠️ SIM7080G-Mピン番号はLCC77データシートで要確認")
  )

{lib_sym_section}

{items_str}

  (sheet_instances
    (path "/" (page "1"))
  )
)
"""
    return schematic


if __name__ == "__main__":
    output_path = "/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_sch"
    sch = build_schematic()
    with open(output_path, "w") as f:
        f.write(sch)
    print(f"Schematic written: {output_path}")
    print(f"File size: {len(sch)} bytes")

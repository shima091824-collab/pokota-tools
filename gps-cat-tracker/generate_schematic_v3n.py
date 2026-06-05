#!/usr/bin/env python3
"""
GPS Cat Tracker v3n — KiCad 10 Schematic Generator
Design: lora-30x35-v3n (ATtiny3226 + E220-900T22S LoRa + ATGM336H GPS + TP4056)

Connections (from DESIGN.md / PCB):
  USB-C → TP4056 → LiPo → SW1 → E220(VCC)
  E220.VDD3V3(out) → ATtiny3226(VCC) + ATGM336H(VCC)
  GPS TXD → ATtiny PC1/pad7, GPS RXD ← ATtiny PC2/pad8
  E220.pad6(M1) ↔ ATtiny.pad6, E220.pad7 ↔ ATtiny.pad12, E220.pad8 ↔ ATtiny.pad11
  ATtiny.pad16(UPDI) → TP1

Run:  cd ~/gps-cat-tracker && python3 generate_schematic_v3n.py
Output: lora-30x35-v3n.kicad_sch
"""

import uuid as _uuid, os

ROOT_UUID = "c2d3e4f5-a6b7-8901-bcde-f23456789012"
KICAD_SYM = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

def uid(): return str(_uuid.uuid4())

def snap(v):
    """Snap to 1.27mm grid."""
    return round(round(v / 1.27) * 1.27, 3)

def G2(x, y):
    """Convert 2.54mm-grid units to mm (ensures 1.27mm grid alignment)."""
    return round(x * 2.54, 3), round(y * 2.54, 3)

def pa(cx, cy, sx, sy):
    """Absolute pin position. cx/cy must be 2.54mm multiples, sx/sy must be 1.27mm multiples."""
    return (round(cx + sx, 3), round(cy - sy, 3))

# ── ELEMENT BUILDERS ──────────────────────────────────────────────────────────

def label(net, x, y, angle=0):
    justify = "left" if angle in (0, 270) else "right"
    return (f'  (label "{net}" (at {x:.3f} {y:.3f} {angle})\n'
            f'    (effects (font (size 1.27 1.27)) (justify {justify}))\n'
            f'    (uuid "{uid()}")\n'
            f'  )')

def no_connect(x, y):
    return f'  (no_connect (at {x:.3f} {y:.3f}) (uuid "{uid()}"))'

def gnd_inst(x, y):
    u = uid()
    return (f'  (symbol (lib_id "power:GND") (at {x:.3f} {y:.3f} 0) (unit 1)\n'
            f'    (exclude_from_sim no) (in_bom no) (on_board no)\n'
            f'    (uuid "{u}")\n'
            f'    (property "Reference" "#PWR" (at {x:.3f} {y+2.54:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n    )\n'
            f'    (property "Value" "GND" (at {x:.3f} {y+1.27:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n    )\n'
            f'    (property "Footprint" "" (at {x:.3f} {y:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n    )\n'
            f'  )')

def pwr_flag_inst(x, y, net_label):
    u = uid()
    flag = (f'  (symbol (lib_id "power:PWR_FLAG") (at {x:.3f} {y:.3f} 0) (unit 1)\n'
            f'    (exclude_from_sim no) (in_bom yes) (on_board no)\n'
            f'    (uuid "{u}")\n'
            f'    (property "Reference" "#FLG0" (at {x:.3f} {y-2.54:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n    )\n'
            f'    (property "Value" "PWR_FLAG" (at {x:.3f} {y-1.27:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n    )\n'
            f'    (property "Footprint" "" (at {x:.3f} {y:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n    )\n'
            f'  )')
    lbl = label(net_label, x, y)
    return flag + "\n" + lbl

def inst(lib_id, ref, value, cx, cy, fp="", ds="", lcsc=""):
    cx, cy = snap(cx), snap(cy)
    u = uid()
    lcsc_prop = ""
    if lcsc:
        lcsc_prop = (f'\n    (property "LCSC" "{lcsc}" (at {cx:.3f} {cy:.3f} 0)\n'
                     f'      (effects (font (size 1.27 1.27)) hide)\n    )')
    return (f'  (symbol (lib_id "{lib_id}") (at {cx:.3f} {cy:.3f} 0) (unit 1)\n'
            f'    (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            f'    (uuid "{u}")\n'
            f'    (property "Reference" "{ref}" (at {cx:.3f} {cy-4:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n    )\n'
            f'    (property "Value" "{value}" (at {cx:.3f} {cy+4:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n    )\n'
            f'    (property "Footprint" "{fp}" (at {cx:.3f} {cy:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n    )\n'
            f'    (property "Datasheet" "{ds}" (at {cx:.3f} {cy:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n    ){lcsc_prop}\n'
            f'  )')

def text(txt, x, y, size=1.27):
    return (f'  (text "{txt}" (at {x:.3f} {y:.3f} 0)\n'
            f'    (effects (font (size {size} {size})) (justify left))\n'
            f'    (uuid "{uid()}")\n'
            f'  )')

def wire(x1, y1, x2, y2):
    return (f'  (wire (pts (xy {x1:.3f} {y1:.3f}) (xy {x2:.3f} {y2:.3f}))\n'
            f'    (stroke (width 0) (type default))\n'
            f'    (uuid "{uid()}")\n'
            f'  )')

def get_symbol(lib_file, sym_name):
    lib_prefix = lib_file.replace(".kicad_sym", "")
    lib = open(f"{KICAD_SYM}/{lib_file}", encoding="utf-8").read()
    marker = f'(symbol "{sym_name}"'
    s = lib.find(marker)
    if s < 0: raise ValueError(f"{sym_name} not found in {lib_file}")
    d = 0
    for i, c in enumerate(lib[s:]):
        if c == "(": d += 1
        elif c == ")": d -= 1
        if d == 0:
            sym = lib[s:s+i+1]
            sym = sym.replace(f'(symbol "{sym_name}"',
                              f'(symbol "{lib_prefix}:{sym_name}"', 1)
            return sym
    raise ValueError("unbalanced parens")

def indent4(sym):
    return "\n".join("    " + ln for ln in sym.splitlines())

# ── CUSTOM SYMBOLS ────────────────────────────────────────────────────────────

def sym_e220():
    """E220-900T22S(JP) LoRa 920MHz module (hand solder, 22-pin)
    Right-side key pins (top→bottom): GND,TXD,RXD,AUX,M0,M1,pad7,pad8,GND,VCC,GND
    Left-side: GND/shield
    VDD3V3 = 3.3V output from internal LDO (powers MCU and GPS)
    """
    return """    (symbol "Custom:E220_900T22S"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 -16 0) (effects (font (size 1.27 1.27))))
      (property "Value" "E220-900T22S(JP)" (at 0 -18.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "E220_900T22S_0_1"
        (rectangle (start -10.16 -13.97) (end 10.16 13.97)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "E220-900T22S(JP)" (at 0 1.27 0) (effects (font (size 1.27 1.27) bold)))
        (text "LoRa 920MHz  LCSC:手はんだ" (at 0 -1.27 0) (effects (font (size 0.889 0.889))))
      )
      (symbol "E220_900T22S_1_1"
        (pin power_in line (at -13.97 11.43 0) (length 3.81)
          (name "VCC" (effects (font (size 1.27 1.27))))
          (number "10" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -13.97 8.89 0) (length 3.81)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "GND1" (effects (font (size 1.27 1.27)))))
        (pin input line (at -13.97 6.35 0) (length 3.81)
          (name "RXD" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27)))))
        (pin output line (at -13.97 3.81 0) (length 3.81)
          (name "TXD" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin output line (at -13.97 1.27 0) (length 3.81)
          (name "AUX" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27)))))
        (pin input line (at -13.97 -1.27 0) (length 3.81)
          (name "M0" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27)))))
        (pin input line (at -13.97 -3.81 0) (length 3.81)
          (name "M1" (effects (font (size 1.27 1.27))))
          (number "6" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -13.97 -6.35 0) (length 3.81)
          (name "SIG7" (effects (font (size 1.27 1.27))))
          (number "7" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -13.97 -8.89 0) (length 3.81)
          (name "SIG8" (effects (font (size 1.27 1.27))))
          (number "8" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 13.97 11.43 180) (length 3.81)
          (name "VDD3V3" (effects (font (size 1.27 1.27))))
          (number "VDD" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 13.97 6.35 180) (length 3.81)
          (name "ANT" (effects (font (size 1.27 1.27))))
          (number "ANT" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 13.97 -11.43 180) (length 3.81)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "GND2" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_tp4056():
    """TP4056 LiPo charger IC, ESOP-8
    Pin1=PROG, Pin2=GND, Pin3=GND, Pin4=VIN(VBUS)
    Pin5=CE(charge enable→VIN), Pin6=CHRG(OD,active-low), Pin7=STDBY(OD,active-low), Pin8=BAT
    Charge current = 1000/RPROG mA → R2=5kΩ → 200mA
    """
    return """    (symbol "Custom:TP4056"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 -9 0) (effects (font (size 1.27 1.27))))
      (property "Value" "TP4056" (at 0 -11.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C16581" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "TP4056_0_1"
        (rectangle (start -7.62 -6.35) (end 7.62 6.35)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "TP4056" (at 0 0.5 0) (effects (font (size 1.27 1.27) bold)))
        (text "LiPo Charger" (at 0 -1.5 0) (effects (font (size 0.889 0.889))))
      )
      (symbol "TP4056_1_1"
        (pin passive line (at -10.16 5.08 0) (length 2.54)
          (name "PROG" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -10.16 2.54 0) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -10.16 0 0) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -10.16 -2.54 0) (length 2.54)
          (name "VIN" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27)))))
        (pin input line (at 10.16 -2.54 180) (length 2.54)
          (name "CE" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27)))))
        (pin open_collector line (at 10.16 0 180) (length 2.54)
          (name "CHRG" (effects (font (size 1.27 1.27))))
          (number "6" (effects (font (size 1.27 1.27)))))
        (pin open_collector line (at 10.16 2.54 180) (length 2.54)
          (name "STDBY" (effects (font (size 1.27 1.27))))
          (number "7" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 10.16 5.08 180) (length 2.54)
          (name "BAT" (effects (font (size 1.27 1.27))))
          (number "8" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_atgm336h():
    """ATGM336H-5N31 GPS module, LCC-18
    Right side p1-p9, Left side p10-p18 (per datasheet)
    p1=GND, p2=TXD, p3=RXD, p4=1PPS, p5=ON/OFF(H=on→VCC), p6=VBAT, p7=NC, p8=VCC, p9=nRESET(H=run→VCC)
    p10=GND, p11=RF_IN, p12=GND, p13=NC, p14=VCC_RF(3.3V out), p15=Reserved, p16=SDA, p17=SCL, p18=Reserved
    """
    return """    (symbol "Custom:ATGM336H"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 -14 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ATGM336H-5N31" (at 0 -16.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C90770" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "ATGM336H_0_1"
        (rectangle (start -10.16 -11.43) (end 10.16 11.43)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "ATGM336H" (at 0 1.27 0) (effects (font (size 1.27 1.27) bold)))
        (text "GPS LCC-18" (at 0 -1.27 0) (effects (font (size 0.889 0.889))))
      )
      (symbol "ATGM336H_1_1"
        (pin power_in line (at -13.97 8.89 0) (length 3.81)
          (name "VCC" (effects (font (size 1.27 1.27))))
          (number "8" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -13.97 6.35 0) (length 3.81)
          (name "VBAT" (effects (font (size 1.27 1.27))))
          (number "6" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -13.97 3.81 0) (length 3.81)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin output line (at -13.97 1.27 0) (length 3.81)
          (name "TXD" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin input line (at -13.97 -1.27 0) (length 3.81)
          (name "RXD" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27)))))
        (pin output line (at -13.97 -3.81 0) (length 3.81)
          (name "1PPS" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27)))))
        (pin input line (at -13.97 -6.35 0) (length 3.81)
          (name "ON/OFF" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27)))))
        (pin input line (at -13.97 -8.89 0) (length 3.81)
          (name "nRESET" (effects (font (size 1.27 1.27))))
          (number "9" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 13.97 8.89 180) (length 3.81)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "10" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 13.97 6.35 180) (length 3.81)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "12" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 13.97 3.81 180) (length 3.81)
          (name "RF_IN" (effects (font (size 1.27 1.27))))
          (number "11" (effects (font (size 1.27 1.27)))))
        (pin no_connect line (at 13.97 1.27 180) (length 3.81)
          (name "NC" (effects (font (size 1.27 1.27))))
          (number "7" (effects (font (size 1.27 1.27)))))
        (pin no_connect line (at 13.97 -1.27 180) (length 3.81)
          (name "NC" (effects (font (size 1.27 1.27))))
          (number "13" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_attiny3226():
    """ATtiny3226 MCU, VQFN-20 (4x4mm, 0.5mm pitch)
    Physical pad layout (CCW from upper-left):
      Left  (pad1-5,  top→bot): pad1=VCC, pad2-5=PA4-PA7
      Bottom(pad6-10, L→R):    pad6-10
      Right (pad11-15,bot→top): pad11-15
      Top   (pad16-20,R→L):    pad16=UPDI/PA0, pad17=PA1, pad18-20
      EP = GND (center)
    Known from DESIGN.md:
      pad7=PC1/RxD1 (GPS TXD→here), pad8=PC2/TxD1 (here→GPS RXD)
      pad11↔E220.pad8, pad12↔E220.pad7, pad6↔E220.pad6(M1)
      pad16=UPDI→TP1, pad17=PA0
    """
    return """    (symbol "Custom:ATtiny3226"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 -16 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ATtiny3226-MFR" (at 0 -18.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_DFN_QFN:DFN-20-1EP_4x4mm_P0.5mm_EP2.5x2.5mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C3014522" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "ATtiny3226_0_1"
        (rectangle (start -10.16 -13.97) (end 10.16 13.97)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "ATtiny3226" (at 0 1.27 0) (effects (font (size 1.27 1.27) bold)))
        (text "VQFN-20" (at 0 -1.27 0) (effects (font (size 0.889 0.889))))
      )
      (symbol "ATtiny3226_1_1"
        (pin power_in line (at -13.97 12.70 0) (length 3.81)
          (name "VCC" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -13.97 10.16 0) (length 3.81)
          (name "PA4/SCK" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -13.97 7.62 0) (length 3.81)
          (name "PA5/MISO" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -13.97 5.08 0) (length 3.81)
          (name "PA6/MOSI" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -13.97 2.54 0) (length 3.81)
          (name "PA7" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -13.97 0 0) (length 3.81)
          (name "LORA_M1/pad6" (effects (font (size 1.27 1.27))))
          (number "6" (effects (font (size 1.27 1.27)))))
        (pin input line (at -13.97 -2.54 0) (length 3.81)
          (name "PC1/RxD1(GPS_TXD)" (effects (font (size 1.27 1.27))))
          (number "7" (effects (font (size 1.27 1.27)))))
        (pin output line (at -13.97 -5.08 0) (length 3.81)
          (name "PC2/TxD1(GPS_RXD)" (effects (font (size 1.27 1.27))))
          (number "8" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -13.97 -7.62 0) (length 3.81)
          (name "pad9" (effects (font (size 1.27 1.27))))
          (number "9" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -13.97 -10.16 0) (length 3.81)
          (name "pad10" (effects (font (size 1.27 1.27))))
          (number "10" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -13.97 -12.70 0) (length 3.81)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "11" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 13.97 -12.70 180) (length 3.81)
          (name "LORA_SIG/pad12" (effects (font (size 1.27 1.27))))
          (number "12" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 13.97 -10.16 180) (length 3.81)
          (name "LORA_SIG/pad13" (effects (font (size 1.27 1.27))))
          (number "13" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 13.97 -7.62 180) (length 3.81)
          (name "pad14" (effects (font (size 1.27 1.27))))
          (number "14" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 13.97 -5.08 180) (length 3.81)
          (name "pad15" (effects (font (size 1.27 1.27))))
          (number "15" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 13.97 -2.54 180) (length 3.81)
          (name "UPDI/PA0" (effects (font (size 1.27 1.27))))
          (number "16" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 13.97 0 180) (length 3.81)
          (name "PA1" (effects (font (size 1.27 1.27))))
          (number "17" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 13.97 2.54 180) (length 3.81)
          (name "PA2" (effects (font (size 1.27 1.27))))
          (number "18" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 13.97 5.08 180) (length 3.81)
          (name "PA3" (effects (font (size 1.27 1.27))))
          (number "19" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 13.97 7.62 180) (length 3.81)
          (name "pad20" (effects (font (size 1.27 1.27))))
          (number "20" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 13.97 12.70 180) (length 3.81)
          (name "GND(EP)" (effects (font (size 1.27 1.27))))
          (number "EP" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_usbc():
    """USB-C 16P SMD connector (J2, C2765186)
    Key pins: VBUS(A4/B4/A9/B9), GND(A1/B1/A12/B12), CC1(A5), CC2(B5)
    """
    return """    (symbol "Custom:USBC_16P"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 -10 0) (effects (font (size 1.27 1.27))))
      (property "Value" "USB-C 16P SMD" (at 0 -12.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C2765186" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "USBC_16P_0_1"
        (rectangle (start -6.35 -7.62) (end 6.35 7.62)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "USB-C" (at 0 0 0) (effects (font (size 1.27 1.27) bold)))
      )
      (symbol "USBC_16P_1_1"
        (pin passive line (at -10.16 5.08 0) (length 3.81)
          (name "VBUS" (effects (font (size 1.27 1.27))))
          (number "AB4/AB9" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -10.16 2.54 0) (length 3.81)
          (name "CC1" (effects (font (size 1.27 1.27))))
          (number "A5" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -10.16 0 0) (length 3.81)
          (name "CC2" (effects (font (size 1.27 1.27))))
          (number "B5" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 10.16 5.08 180) (length 3.81)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "AB1/AB12" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 10.16 2.54 180) (length 3.81)
          (name "SHIELD" (effects (font (size 1.27 1.27))))
          (number "SH" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_jst_gh():
    """JST-GH 1.25mm 2P battery connector (J1, C160404)"""
    return """    (symbol "Custom:JST_GH_2P"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 -6 0) (effects (font (size 1.27 1.27))))
      (property "Value" "JST-GH 1.25mm 2P" (at 0 -8.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C160404" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "JST_GH_2P_0_1"
        (rectangle (start -3.81 -3.81) (end 3.81 3.81)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "LiPo 500mAh" (at 0 0 0) (effects (font (size 1.016 1.016))))
      )
      (symbol "JST_GH_2P_1_1"
        (pin passive line (at -6.35 1.27 0) (length 2.54)
          (name "+BAT" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -6.35 -1.27 0) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_sw1():
    """MSK12C02 power slide switch (SW1, C431541)"""
    return """    (symbol "Custom:MSK12C02"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "SW" (at 0 -6 0) (effects (font (size 1.27 1.27))))
      (property "Value" "MSK12C02" (at 0 -8.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C431541" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "MSK12C02_0_1"
        (rectangle (start -5.08 -2.54) (end 5.08 2.54)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "SW_PWR" (at 0 0 0) (effects (font (size 1.016 1.016) bold)))
      )
      (symbol "MSK12C02_1_1"
        (pin passive line (at -7.62 0 0) (length 2.54)
          (name "IN" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 7.62 0 180) (length 2.54)
          (name "OUT" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_ufl():
    """U.FL-R-SMT antenna connector (ANT1, C317592)"""
    return """    (symbol "Custom:UFL"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "ANT" (at 0 -5 0) (effects (font (size 1.27 1.27))))
      (property "Value" "U.FL-R-SMT" (at 0 -7.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C317592" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "UFL_0_1"
        (circle (center 0 0) (radius 2.54)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "U.FL" (at 0 0 0) (effects (font (size 1.016 1.016))))
      )
      (symbol "UFL_1_1"
        (pin passive line (at -5.08 0 0) (length 2.54)
          (name "RF" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 5.08 0 180) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_tp():
    """Test point TP1 (UPDI)"""
    return """    (symbol "Custom:TestPoint"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "TP" (at 0 -4 0) (effects (font (size 1.27 1.27))))
      (property "Value" "UPDI_TP" (at 0 -6 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "TestPoint_0_1"
        (circle (center 0 0) (radius 1.27)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "TP" (at 0 0 0) (effects (font (size 1.016 1.016))))
      )
      (symbol "TestPoint_1_1"
        (pin passive line (at 0 -3.81 90) (length 2.54)
          (name "P" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
      )
    )"""

# ── MAIN BUILD ────────────────────────────────────────────────────────────────

def build():
    elems = []

    header = f"""(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "10.0.3")
  (uuid "{ROOT_UUID}")

  (paper "A3")

  (title_block
    (title "GPS Cat Tracker v3n — LoRa 920MHz")
    (date "2026-05-30")
    (rev "v3n")
    (company "Personal")
    (comment 1 "PCB: 30x35mm  ATtiny3226 + E220-900T22S(JP) + ATGM336H-5N31 + TP4056")
    (comment 2 "技適番号: 001-P01730  Power: USB-C 5V → TP4056 → 500mAh LiPo → E220 LDO 3.3V")
    (comment 3 "JLCPCB SMT: U2/U3/U4 + passives  手はんだ: U1(E220)")
  )"""

    # ── LIB SYMBOLS ──────────────────────────────────────────────────────────
    r_sym       = get_symbol("Device.kicad_sym",  "R")
    c_sym       = get_symbol("Device.kicad_sym",  "C")
    led_sym     = get_symbol("Device.kicad_sym",  "LED")
    gnd_sym     = get_symbol("power.kicad_sym",   "GND")
    pwrflag_sym = get_symbol("power.kicad_sym",   "PWR_FLAG")

    lib_block = ("  (lib_symbols\n" +
                 indent4(r_sym)       + "\n" +
                 indent4(c_sym)       + "\n" +
                 indent4(led_sym)     + "\n" +
                 indent4(gnd_sym)     + "\n" +
                 indent4(pwrflag_sym) + "\n" +
                 sym_e220()           + "\n" +
                 sym_tp4056()         + "\n" +
                 sym_atgm336h()       + "\n" +
                 sym_attiny3226()     + "\n" +
                 sym_usbc()           + "\n" +
                 sym_jst_gh()         + "\n" +
                 sym_sw1()            + "\n" +
                 sym_ufl()            + "\n" +
                 sym_tp()             + "\n" +
                 "  )")

    # ── COMPONENT POSITIONS (A3: 420×297mm, all in mm) ────────────────────────
    # 全座標はG2()で2.54mmグリッド整数倍に固定 → 1.27mmグリッド整合 → ERC pass
    # Zone A: Power (left, x≈20-150)
    J2x,  J2y  = G2(14, 22)   # 35.56,  55.88  USB-C
    U4x,  U4y  = G2(36, 22)   # 91.44,  55.88  TP4056
    J1x,  J1y  = G2(14, 44)   # 35.56, 111.76  JST-GH battery
    SW1x, SW1y = G2(32, 44)   # 81.28, 111.76  Power switch
    R2x,  R2y  = G2(36, 12)   # 91.44,  30.48  PROG resistor (5kΩ)
    R5x,  R5y  = G2( 8, 31)   # 20.32,  78.74  CC1 5.1kΩ
    R6x,  R6y  = G2( 8, 36)   # 20.32,  91.44  CC2 5.1kΩ
    R3x,  R3y  = G2(48, 18)   # 121.92, 45.72  LED1 current (330Ω)
    R4x,  R4y  = G2(48, 25)   # 121.92, 63.50  LED2 current (330Ω)
    D1x,  D1y  = G2(58, 18)   # 147.32, 45.72  LED1 Red
    D2x,  D2y  = G2(58, 25)   # 147.32, 63.50  LED2 Blue
    R1x,  R1y  = G2(36, 55)   # 91.44, 139.70  R1 DNP (10kΩ)

    # Zone B: LoRa module (center, x≈170-240)
    U1x,  U1y  = G2(80, 40)   # 203.20, 101.60  E220
    ANT1x,ANT1y= G2(69, 40)   # 175.26, 101.60  U.FL antenna

    # Zone C: MCU (upper-right, x≈270-380)
    U2x,  U2y  = G2(122, 32)  # 309.88,  81.28  ATtiny3226
    TP1x, TP1y = G2(146, 24)  # 370.84,  60.96  UPDI test point

    # Zone D: GPS (lower-right, x≈270-380)
    U3x,  U3y  = G2(122, 80)  # 309.88, 203.20  ATGM336H

    # Bypass caps
    C1x,  C1y  = G2( 76, 24)  # 193.04,  60.96  E220 VCC bypass
    C2x,  C2y  = G2( 82, 24)  # 208.28,  60.96
    C3x,  C3y  = G2(122, 16)  # 309.88,  40.64  ATtiny VCC bypass
    C4x,  C4y  = G2(128, 16)  # 325.12,  40.64
    C5x,  C5y  = G2(122, 61)  # 309.88, 154.94  GPS VCC bypass
    C6x,  C6y  = G2(128, 61)  # 325.12, 154.94  GPS VCC bypass (1uF)

    # ── COMPONENT INSTANCES ───────────────────────────────────────────────────
    elems.append(inst("Custom:USBC_16P",   "J2",  "USB-C 16P SMD", J2x, J2y,
        lcsc="C2765186"))
    elems.append(inst("Custom:TP4056",     "U4",  "TP4056",         U4x, U4y,
        fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", lcsc="C16581"))
    elems.append(inst("Custom:JST_GH_2P",  "J1",  "JST-GH 1.25mm 2P 500mAh", J1x, J1y,
        lcsc="C160404"))
    elems.append(inst("Custom:MSK12C02",   "SW1", "MSK12C02",       SW1x, SW1y,
        lcsc="C431541"))
    elems.append(inst("Device:R",          "R2",  "5.0kΩ 0402",     R2x,  R2y,
        fp="Resistor_SMD:R_0402_1005Metric", lcsc="C25905"))
    elems.append(inst("Device:R",          "R5",  "5.1kΩ 0402 CC1", R5x,  R5y,
        fp="Resistor_SMD:R_0402_1005Metric", lcsc="C23186"))
    elems.append(inst("Device:R",          "R6",  "5.1kΩ 0402 CC2", R6x,  R6y,
        fp="Resistor_SMD:R_0402_1005Metric", lcsc="C23186"))
    elems.append(inst("Device:R",          "R3",  "330Ω 0402",      R3x,  R3y,
        fp="Resistor_SMD:R_0402_1005Metric", lcsc="C22978"))
    elems.append(inst("Device:R",          "R4",  "330Ω 0402",      R4x,  R4y,
        fp="Resistor_SMD:R_0402_1005Metric", lcsc="C22978"))
    elems.append(inst("Device:LED",        "LED1","RED 0402",        D1x,  D1y,
        fp="LED_SMD:LED_0402_1005Metric",   lcsc="C2286"))
    elems.append(inst("Device:LED",        "LED2","BLUE 0402",       D2x,  D2y,
        fp="LED_SMD:LED_0402_1005Metric",   lcsc="C72041"))
    # R1 DNP
    elems.append(inst("Device:R",          "R1",  "10kΩ 0402 DNP",  R1x,  R1y,
        fp="Resistor_SMD:R_0402_1005Metric"))
    elems.append(inst("Custom:E220_900T22S","U1", "E220-900T22S(JP)",U1x,  U1y))
    elems.append(inst("Custom:UFL",        "ANT1","U.FL-R-SMT",     ANT1x,ANT1y,
        lcsc="C317592"))
    elems.append(inst("Custom:ATtiny3226", "U2",  "ATtiny3226-MFR", U2x,  U2y,
        fp="Package_DFN_QFN:QFN-20-1EP_4x4mm_P0.5mm_EP2.5x2.5mm", lcsc="C3014522"))
    elems.append(inst("Custom:TestPoint",  "TP1", "UPDI",           TP1x, TP1y))
    elems.append(inst("Custom:ATGM336H",   "U3",  "ATGM336H-5N31",  U3x,  U3y,
        lcsc="C90770"))
    # Bypass caps
    for (ref, val, lcsc, cx, cy) in [
        ("C1","100nF 10V 0402","C14663",C1x,C1y),
        ("C2","100nF 10V 0402","C14663",C2x,C2y),
        ("C3","100nF 10V 0402","C14663",C3x,C3y),
        ("C4","100nF 10V 0402","C14663",C4x,C4y),
        ("C5","100nF 10V 0402","C14663",C5x,C5y),
        ("C6","1uF 10V 0402",  "C52923",C6x,C6y),
    ]:
        elems.append(inst("Device:C", ref, val, cx, cy,
            fp="Capacitor_SMD:C_0402_1005Metric", lcsc=lcsc))

    # ── NET LABELS & GND ──────────────────────────────────────────────────────
    nets = []

    def L(net, cx, cy, sx, sy, angle=0):
        x, y = pa(cx, cy, sx, sy)
        nets.append(label(net, x, y, angle))

    def G(cx, cy, sx, sy):
        x, y = pa(cx, cy, sx, sy)
        nets.append(gnd_inst(x, y))

    def NC(cx, cy, sx, sy):
        x, y = pa(cx, cy, sx, sy)
        nets.append(no_connect(x, y))

    # ── J2 USB-C ─────────────────────────────────────────────────────────────
    L("VBUS",   J2x, J2y, -10.16,  5.08)
    L("CC1",    J2x, J2y, -10.16,  2.54)
    L("CC2",    J2x, J2y, -10.16,  0)
    G(J2x, J2y,  10.16,  5.08)
    G(J2x, J2y,  10.16,  2.54)    # SHIELD→GND

    # ── R5 CC1 pulldown (5.1kΩ) ──────────────────────────────────────────────
    L("CC1",    R5x, R5y,  0,  3.81)
    G(R5x, R5y,  0, -3.81)

    # ── R6 CC2 pulldown (5.1kΩ) ──────────────────────────────────────────────
    L("CC2",    R6x, R6y,  0,  3.81)
    G(R6x, R6y,  0, -3.81)

    # ── U4 TP4056 ────────────────────────────────────────────────────────────
    L("PROG_NET",U4x, U4y, -10.16,  5.08)   # PROG→R2
    G(U4x, U4y, -10.16,  2.54)              # GND(2)
    G(U4x, U4y, -10.16,  0)                 # GND(3)
    L("VBUS",   U4x, U4y, -10.16, -2.54)    # VIN
    L("VBUS",   U4x, U4y,  10.16, -2.54)    # CE→VIN (always enabled)
    L("CHRG_N", U4x, U4y,  10.16,  0)       # CHRG→R3→LED1
    L("STDBY_N",U4x, U4y,  10.16,  2.54)    # STDBY→R4→LED2
    L("VBAT",   U4x, U4y,  10.16,  5.08)    # BAT

    # ── R2 PROG (5kΩ → 200mA charge current) ─────────────────────────────────
    L("PROG_NET",R2x, R2y,  0,  3.81)
    G(R2x, R2y,  0, -3.81)

    # ── J1 Battery ───────────────────────────────────────────────────────────
    L("VBAT",   J1x, J1y, -6.35,  1.27)
    G(J1x, J1y, -6.35, -1.27)

    # ── SW1 Power switch ─────────────────────────────────────────────────────
    L("VBAT",   SW1x, SW1y, -7.62, 0)
    L("VCC_E220",SW1x,SW1y,  7.62, 0)

    # ── R3 + LED1 (CHRG, Red) ────────────────────────────────────────────────
    L("CHRG_N", R3x, R3y,  0,  3.81)
    L("LED1_A", R3x, R3y,  0, -3.81)
    L("LED1_A", D1x, D1y,  3.81, 0)
    G(D1x, D1y, -3.81, 0)

    # ── R4 + LED2 (STDBY, Blue) ──────────────────────────────────────────────
    L("STDBY_N",R4x, R4y,  0,  3.81)
    L("LED2_A", R4x, R4y,  0, -3.81)
    L("LED2_A", D2x, D2y,  3.81, 0)
    G(D2x, D2y, -3.81, 0)

    # ── R1 DNP ───────────────────────────────────────────────────────────────
    NC(R1x, R1y,  0,  3.81)
    NC(R1x, R1y,  0, -3.81)

    # ── U1 E220 ──────────────────────────────────────────────────────────────
    L("VCC_E220",U1x, U1y, -13.97,  11.43)   # VCC(pad10)
    G(U1x, U1y, -13.97,  8.89)               # GND
    L("LORA_RXD",U1x, U1y, -13.97,  6.35)   # RXD←MCU TXD
    L("LORA_TXD",U1x, U1y, -13.97,  3.81)   # TXD→MCU RXD
    NC(U1x, U1y, -13.97,  1.27)              # AUX (not connected in this design)
    NC(U1x, U1y, -13.97, -1.27)              # M0
    L("LORA_M1", U1x, U1y, -13.97, -3.81)   # M1(pad6)↔MCU pad6
    L("LORA_S7", U1x, U1y, -13.97, -6.35)   # SIG7(pad7)↔MCU pad12
    L("LORA_S8", U1x, U1y, -13.97, -8.89)   # SIG8(pad8)↔MCU pad11
    L("VCC_3V3", U1x, U1y,  13.97,  11.43)  # VDD3V3 output
    L("LORA_ANT",U1x, U1y,  13.97,   6.35)  # ANT→U.FL
    G(U1x, U1y,  13.97, -11.43)              # GND

    # ── ANT1 U.FL ────────────────────────────────────────────────────────────
    L("LORA_ANT",ANT1x, ANT1y, -5.08, 0)
    G(ANT1x, ANT1y,  5.08, 0)

    # ── Bypass caps C1/C2 (E220 VCC) ─────────────────────────────────────────
    L("VCC_E220",C1x, C1y, 0,  3.81)
    G(C1x, C1y, 0, -3.81)
    L("VCC_E220",C2x, C2y, 0,  3.81)
    G(C2x, C2y, 0, -3.81)

    # ── U2 ATtiny3226 ────────────────────────────────────────────────────────
    L("VCC_3V3", U2x, U2y, -13.97,  12.70)  # VCC(pad1)
    NC(U2x, U2y, -13.97,  10.16)             # PA4
    NC(U2x, U2y, -13.97,   7.62)             # PA5
    NC(U2x, U2y, -13.97,   5.08)             # PA6
    NC(U2x, U2y, -13.97,   2.54)             # PA7
    L("LORA_M1", U2x, U2y, -13.97,   0)     # pad6↔E220 M1
    L("GPS_TXD", U2x, U2y, -13.97,  -2.54)  # PC1/RxD1←GPS TXD
    L("GPS_RXD", U2x, U2y, -13.97,  -5.08)  # PC2/TxD1→GPS RXD
    NC(U2x, U2y, -13.97,  -7.62)             # pad9
    NC(U2x, U2y, -13.97, -10.16)             # pad10
    G(U2x, U2y,  -13.97, -12.70)             # GND(pad11)
    L("LORA_S7", U2x, U2y,  13.97, -12.70)  # pad12↔E220 SIG7
    L("LORA_S8", U2x, U2y,  13.97, -10.16)  # pad11↔E220 SIG8  (note: pad11=right-bottom)
    NC(U2x, U2y,  13.97,  -7.62)             # pad13 (NOTE: pad12 in symbol = physical pad12)
    NC(U2x, U2y,  13.97,  -5.08)             # pad14
    L("UPDI",    U2x, U2y,  13.97,  -2.54)  # pad16=UPDI/PA0→TP1  (sy=-2.54が正しい)
    L("LORA_RXD",U2x, U2y,  13.97,   0)    # PA1(pad17)/TxD0→E220.RXD
    L("LORA_TXD",U2x, U2y,  13.97,   2.54) # PA2(pad18)/RxD0←E220.TXD
    NC(U2x, U2y,  13.97,   5.08)            # PA3(pad19)
    NC(U2x, U2y,  13.97,   7.62)            # pad20
    # sy=10.16には対応するピンなし → NC削除(dangling防止)
    G(U2x, U2y,   13.97,  12.70)            # GND(EP)

    # ── Bypass caps C3/C4 (ATtiny VCC) ───────────────────────────────────────
    L("VCC_3V3", C3x, C3y, 0,  3.81)
    G(C3x, C3y, 0, -3.81)
    L("VCC_3V3", C4x, C4y, 0,  3.81)
    G(C4x, C4y, 0, -3.81)

    # ── TP1 UPDI ─────────────────────────────────────────────────────────────
    L("UPDI",    TP1x, TP1y, 0, -3.81)

    # ── U3 ATGM336H GPS ──────────────────────────────────────────────────────
    L("VCC_3V3", U3x, U3y, -13.97,   8.89)  # VCC(p8)
    L("VCC_3V3", U3x, U3y, -13.97,   6.35)  # VBAT(p6)→VCC(hot start)
    G(U3x, U3y, -13.97,  3.81)               # GND(p1)
    L("GPS_TXD", U3x, U3y, -13.97,   1.27)  # TXD(p2)→MCU RxD
    L("GPS_RXD", U3x, U3y, -13.97,  -1.27)  # RXD(p3)←MCU TxD
    NC(U3x, U3y, -13.97, -3.81)              # 1PPS(p4) not used
    L("VCC_3V3", U3x, U3y, -13.97,  -6.35)  # ON/OFF(p5)→VCC (always on)
    L("VCC_3V3", U3x, U3y, -13.97,  -8.89)  # nRESET(p9)→VCC (always active)
    G(U3x, U3y,  13.97,   8.89)              # GND(p10)
    G(U3x, U3y,  13.97,   6.35)              # GND(p12)
    NC(U3x, U3y,  13.97,   3.81)             # RF_IN(p11) internal GPS antenna
    NC(U3x, U3y,  13.97,   1.27)             # NC(p7)
    NC(U3x, U3y,  13.97,  -1.27)             # NC(p13)

    # ── Bypass caps C5/C6 (GPS VCC) ──────────────────────────────────────────
    L("VCC_3V3", C5x, C5y, 0,  3.81)
    G(C5x, C5y, 0, -3.81)
    L("VCC_3V3", C6x, C6y, 0,  3.81)
    G(C6x, C6y, 0, -3.81)

    # ── PWR_FLAG (ERC: power_pin_not_driven) ─────────────────────────────────
    nets.append(pwr_flag_inst(snap(J2x - 5), snap(J2y + 12.7), "VBUS"))
    nets.append(pwr_flag_inst(*G2(34, 48), "VCC_E220"))   # SW1出力
    nets.append(pwr_flag_inst(*G2( 4, 68), "GND"))        # GNDネット明示的に駆動

    elems.extend(nets)

    # ── ANNOTATION NOTES ─────────────────────────────────────────────────────
    notes = [
        text("GPS Cat Tracker v3n  |  30×35mm  |  LoRa 920MHz 技適 001-P01730", 15, 15),
        text("充電: USB-C 5V → TP4056(200mA) → LiPo 500mAh → SW1 → E220(VCC)", 15, 20),
        text("E220内蔵LDO → VCC_3V3(3.3V) → ATtiny3226 + ATGM336H GPS", 15, 25),
        text("=== POWER PATH ===", 15, 45),
        text("VBUS: R2=5kΩ → PROG → 充電電流=1000/5k=200mA", 15, 50),
        text("R5/R6=5.1kΩ: USB-C CC1/CC2プルダウン(5V/900mA認識)", 15, 55),
        text("R1=DNP(用途不明・安全のため未実装)", 15, 130),
        text("=== LoRa E220 ===", 165, 50),
        text("E220 M1(pad6)↔ATtiny pad6  |  SIG7(pad7)↔ATtiny pad12  |  SIG8(pad8)↔ATtiny pad11", 165, 55),
        text("E220 TXD→LORA_TXD→MCU  |  E220 RXD←LORA_RXD←MCU", 165, 60),
        text("=== GPS UART ===", 265, 150),
        text("GPS TXD(p2)→GPS_TXD→ATtiny PC1/RxD1(pad7)", 265, 155),
        text("GPS RXD(p3)←GPS_RXD←ATtiny PC2/TxD1(pad8)", 265, 160),
        text("ON/OFF(p5)・VBAT(p6)・nRESET(p9) → VCC_3V3で常時動作", 265, 165),
    ]
    elems.extend(notes)

    footer = """  (sheet_instances
    (path "/" (page "1"))
  )
)"""

    body = header + "\n\n" + lib_block + "\n\n" + "\n".join(elems) + "\n\n" + footer
    return body


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lora-30x35-v3n.kicad_sch")
    sch = build()
    with open(out, "w", encoding="utf-8") as f:
        f.write(sch)
    nc_count  = sch.count("(no_connect")
    lbl_count = sch.count('\n  (label')
    gnd_count = sch.count('(lib_id "power:GND")')
    print(f"✓ {out}")
    print(f"  {len(sch):,} bytes  |  labels: {lbl_count}  no_connect: {nc_count}  gnd_syms: {gnd_count}")
    print("  KiCadで開く: File → Open → lora-30x35-v3n.kicad_sch")
    print("  ERC実行して確認してください")

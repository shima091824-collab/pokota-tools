#!/usr/bin/env python3
"""
GPS Cat Tracker — KiCad 10 Schematic Generator v3
All component pins connected via net labels placed at exact pin endpoints.
abs_x = snap(comp_x + sym_pin_x)
abs_y = snap(comp_y - sym_pin_y)   ← Y-axis flip between symbol and schematic coords

Fixes vs v2:
  - All coordinates snapped to 1.27mm grid (endpoint_off_grid resolved)
  - Standard symbols (Device:R/C/LED, power:GND/PWR_FLAG) pulled from library (lib_symbol_mismatch resolved)
  - lib_symbols names prefixed with "LibName:" to match instance lib_id (lib_symbol_mismatch resolved)
  - PWR_FLAG added to VBUS and GND nets (power_pin_not_driven resolved)
  - SWDCLK pin type changed to bidirectional (pin_not_driven resolved)

Run:  cd ~/gps-cat-tracker && python3 generate_schematic.py
Output: gps-cat-tracker.kicad_sch
"""

import uuid as _uuid, re

ROOT_UUID = "b47f98a5-3c1a-4d2e-8f6b-9e2c4a1d5f7e"
KICAD_SYM = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

def uid(): return str(_uuid.uuid4())

def snap(v):
    """Snap to 1.27mm grid (50-mil standard KiCad grid)."""
    return round(round(v / 1.27) * 1.27, 3)

def pa(cx, cy, sx, sy):
    """Absolute schematic coordinate of a pin at symbol-local (sx, sy), snapped to grid."""
    return (snap(cx + sx), snap(cy - sy))

# ── EXTRACT SYMBOL FROM LIBRARY ──────────────────────────────────────────────

def get_symbol(lib_file, sym_name):
    """Extract symbol from KiCad library, rename parent to 'LibName:SymName'."""
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
            # Prefix parent symbol name only (replace first occurrence)
            sym = sym.replace(f'(symbol "{sym_name}"',
                              f'(symbol "{lib_prefix}:{sym_name}"', 1)
            return sym
    raise ValueError("unbalanced parens")

# ── SCHEMATIC ELEMENT BUILDERS ───────────────────────────────────────────────

def label(net, x, y, angle=0):
    return (f'  (label "{net}" (at {x:.3f} {y:.3f} {angle})\n'
            f'    (effects (font (size 1.27 1.27)) (justify left))\n'
            f'    (uuid "{uid()}")\n'
            f'  )')

def no_connect(x, y):
    return f'  (no_connect (at {x:.3f} {y:.3f}) (uuid "{uid()}"))'

def gnd_inst(x, y):
    """power:GND symbol instance."""
    u = uid()
    return (f'  (symbol (lib_id "power:GND") (at {x:.3f} {y:.3f} 0) (unit 1)\n'
            f'    (exclude_from_sim no) (in_bom no) (on_board no)\n'
            f'    (uuid "{u}")\n'
            f'    (property "Reference" "#PWR" (at {x:.3f} {y+2.54:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n'
            f'    )\n'
            f'    (property "Value" "GND" (at {x:.3f} {y+1.27:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n'
            f'    )\n'
            f'    (property "Footprint" "" (at {x:.3f} {y:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n'
            f'    )\n'
            f'  )')

def pwr_flag_inst(x, y, net_label):
    """power:PWR_FLAG instance + net label at same pin location (x,y).
    Adds a PWR_FLAG (power_out) to drive the given net, resolving power_pin_not_driven."""
    u = uid()
    flag = (f'  (symbol (lib_id "power:PWR_FLAG") (at {x:.3f} {y:.3f} 0) (unit 1)\n'
            f'    (exclude_from_sim no) (in_bom yes) (on_board no)\n'
            f'    (uuid "{u}")\n'
            f'    (property "Reference" "#FLG0" (at {x:.3f} {y-2.54:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n'
            f'    )\n'
            f'    (property "Value" "PWR_FLAG" (at {x:.3f} {y-1.27:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n'
            f'    )\n'
            f'    (property "Footprint" "" (at {x:.3f} {y:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n'
            f'    )\n'
            f'  )')
    # Connect the PWR_FLAG pin to the net via a label
    lbl = label(net_label, x, y)
    return flag + "\n" + lbl

def inst(lib_id, ref, value, cx, cy, fp="", ds="", extra=None):
    cx, cy = snap(cx), snap(cy)
    u = uid()
    props = ""
    if extra:
        for k, v in extra.items():
            props += (f'\n    (property "{k}" "{v}" (at {cx:.3f} {cy:.3f} 0)\n'
                      f'      (effects (font (size 1.27 1.27)) hide)\n'
                      f'    )')
    return (f'  (symbol (lib_id "{lib_id}") (at {cx:.3f} {cy:.3f} 0) (unit 1)\n'
            f'    (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            f'    (uuid "{u}")\n'
            f'    (property "Reference" "{ref}" (at {cx:.3f} {cy-3.5:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n'
            f'    )\n'
            f'    (property "Value" "{value}" (at {cx:.3f} {cy+3.5:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n'
            f'    )\n'
            f'    (property "Footprint" "{fp}" (at {cx:.3f} {cy:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n'
            f'    )\n'
            f'    (property "Datasheet" "{ds}" (at {cx:.3f} {cy:.3f} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n'
            f'    ){props}\n'
            f'  )')

def text(txt, x, y):
    return (f'  (text "{txt}" (at {x:.3f} {y:.3f} 0)\n'
            f'    (effects (font (size 1.27 1.27)) (justify left))\n'
            f'    (uuid "{uid()}")\n'
            f'  )')

def wire(x1, y1, x2, y2):
    return (f'  (wire (pts (xy {x1:.3f} {y1:.3f}) (xy {x2:.3f} {y2:.3f}))\n'
            f'    (stroke (width 0) (type default))\n'
            f'    (uuid "{uid()}")\n'
            f'  )')

# ── CUSTOM SYMBOL DEFINITIONS ────────────────────────────────────────────────

def sym_mcp73831():
    return """    (symbol "Custom:MCP73831T"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 -8 0) (effects (font (size 1.27 1.27))))
      (property "Value" "MCP73831T-2ACI/OT" (at 0 -10.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-23-5" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C14879" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "MCP73831T_0_1"
        (rectangle (start -7.62 -5.08) (end 7.62 5.08)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "MCP73831T" (at 0 0 0) (effects (font (size 1.27 1.27) bold)))
      )
      (symbol "MCP73831T_1_1"
        (pin open_collector line (at -10.16 2.54 0) (length 2.54)
          (name "STAT" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -10.16 -2.54 0) (length 2.54)
          (name "VSS" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 10.16 2.54 180) (length 2.54)
          (name "PROG" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 10.16 -2.54 180) (length 2.54)
          (name "VDD" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 0 -7.62 90) (length 2.54)
          (name "VBAT" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27)))))
      )
    )"""
# MCP73831 pin abs coords at (cx,cy):
# STAT: pa(cx,cy, -10.16, 2.54)
# VSS:  pa(cx,cy, -10.16, -2.54)
# PROG: pa(cx,cy,  10.16, 2.54)
# VDD:  pa(cx,cy,  10.16, -2.54)
# VBAT: pa(cx,cy,  0,     -7.62)

def sym_usbc():
    return """    (symbol "Custom:USBC_PWR"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 -10 0) (effects (font (size 1.27 1.27))))
      (property "Value" "TYPE-C-31-M-12" (at 0 -12.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C165948" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "USBC_PWR_0_1"
        (rectangle (start -6.35 -7.62) (end 6.35 7.62)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "USB-C" (at 0 0 0) (effects (font (size 1.27 1.27) bold)))
      )
      (symbol "USBC_PWR_1_1"
        (pin passive line (at -8.89 5.08 0) (length 2.54)
          (name "VBUS1" (effects (font (size 1.27 1.27))))
          (number "A9" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -8.89 2.54 0) (length 2.54)
          (name "VBUS2" (effects (font (size 1.27 1.27))))
          (number "B9" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -8.89 -2.54 0) (length 2.54)
          (name "CC1" (effects (font (size 1.27 1.27))))
          (number "A5" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -8.89 -5.08 0) (length 2.54)
          (name "CC2" (effects (font (size 1.27 1.27))))
          (number "B5" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 8.89 5.08 180) (length 2.54)
          (name "GND1" (effects (font (size 1.27 1.27))))
          (number "A1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 8.89 2.54 180) (length 2.54)
          (name "GND2" (effects (font (size 1.27 1.27))))
          (number "B1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 8.89 0 180) (length 2.54)
          (name "SHIELD" (effects (font (size 1.27 1.27))))
          (number "S1" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_sim():
    return """    (symbol "Custom:SIM_Nano"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 -9 0) (effects (font (size 1.27 1.27))))
      (property "Value" "SIM_Nano" (at 0 -11.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Custom:SIM_Nano_SMD" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C5882851" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "SIM_Nano_0_1"
        (rectangle (start -7.62 -6.35) (end 7.62 6.35)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "Nano SIM" (at 0 0 0) (effects (font (size 1.27 1.27) bold)))
      )
      (symbol "SIM_Nano_1_1"
        (pin passive line (at -10.16 5.08 0) (length 2.54)
          (name "VCC" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -10.16 2.54 0) (length 2.54)
          (name "RST" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -10.16 0 0) (length 2.54)
          (name "CLK" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -10.16 -2.54 0) (length 2.54)
          (name "IO" (effects (font (size 1.27 1.27))))
          (number "7" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 10.16 2.54 180) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 10.16 -2.54 180) (length 2.54)
          (name "CD" (effects (font (size 1.27 1.27))))
          (number "8" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_ufl():
    return """    (symbol "Custom:UFL"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 -5 0) (effects (font (size 1.27 1.27))))
      (property "Value" "U.FL" (at 0 -7.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C88374" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "UFL_0_1"
        (circle (center 0 0) (radius 2.54)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "U.FL" (at 0 0 0) (effects (font (size 1.016 1.016))))
      )
      (symbol "UFL_1_1"
        (pin passive line (at -5.08 0 0) (length 2.54)
          (name "RF" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 5.08 0 180) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_swd():
    # SWDCLK changed from input→bidirectional to fix pin_not_driven ERC error
    return """    (symbol "Custom:SWD_Header"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 -8 0) (effects (font (size 1.27 1.27))))
      (property "Value" "SWD_4P" (at 0 -10.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical_SMD" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C429954" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "SWD_Header_0_1"
        (rectangle (start -3.81 -6.35) (end 3.81 6.35)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "SWD" (at 0 0 0) (effects (font (size 1.27 1.27) bold)))
      )
      (symbol "SWD_Header_1_1"
        (pin power_in line (at -6.35 3.81 0) (length 2.54)
          (name "VCC" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -6.35 1.27 0) (length 2.54)
          (name "SWDIO" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -6.35 -1.27 0) (length 2.54)
          (name "SWDCLK" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -6.35 -3.81 0) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27)))))
      )
    )"""

def sym_bat():
    return """    (symbol "Custom:JST_PH_BAT"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 -5 0) (effects (font (size 1.27 1.27))))
      (property "Value" "JST-PH-2P" (at 0 -7.5 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "LCSC" "C131337" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "JST_PH_BAT_0_1"
        (rectangle (start -3.81 -3.81) (end 3.81 3.81)
          (stroke (width 0.254) (type default)) (fill (type background)))
        (text "BAT" (at 0 0 0) (effects (font (size 1.27 1.27) bold)))
      )
      (symbol "JST_PH_BAT_1_1"
        (pin passive line (at -6.35 1.27 0) (length 2.54)
          (name "+BATT" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -6.35 -1.27 0) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
      )
    )"""


# ── MAIN BUILD ───────────────────────────────────────────────────────────────

def build():
    elems = []

    # ── HEADER ──────────────────────────────────────────────────────────────
    header = f"""(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "10.0.3")
  (uuid "{ROOT_UUID}")

  (paper "A3")

  (title_block
    (title "GPS Cat Tracker — nRF9161 SiP")
    (date "2026-05-24")
    (rev "1.0")
    (company "Personal")
    (comment 1 "PCB: 20x35mm  Weight: <16g  LTE-M + GPS")
    (comment 2 "MIC certification: 77859B (nRF9161 Japan)")
    (comment 3 "SIM: 1NCE LTE-M SoftBank  JLCPCB SMT")
  )"""

    # ── LIB_SYMBOLS ─────────────────────────────────────────────────────────
    # Standard symbols pulled from installed KiCad libraries (exact match → no lib_symbol_mismatch)
    nrf_sym     = get_symbol("MCU_Nordic.kicad_sym", "nRF9160-SIxA")
    r_sym       = get_symbol("Device.kicad_sym",     "R")
    c_sym       = get_symbol("Device.kicad_sym",     "C")
    led_sym     = get_symbol("Device.kicad_sym",     "LED")
    gnd_sym     = get_symbol("power.kicad_sym",      "GND")
    pwrflag_sym = get_symbol("power.kicad_sym",      "PWR_FLAG")

    def indent4(sym):
        return "\n".join("    " + ln for ln in sym.splitlines())

    lib_block = ("  (lib_symbols\n" +
                 indent4(nrf_sym)     + "\n" +
                 indent4(r_sym)       + "\n" +
                 indent4(c_sym)       + "\n" +
                 indent4(led_sym)     + "\n" +
                 indent4(gnd_sym)     + "\n" +
                 indent4(pwrflag_sym) + "\n" +
                 sym_mcp73831()       + "\n" +
                 sym_usbc()           + "\n" +
                 sym_sim()            + "\n" +
                 sym_ufl()            + "\n" +
                 sym_swd()            + "\n" +
                 sym_bat()            + "\n" +
                 "  )")

    # ── COMPONENT INSTANCES ──────────────────────────────────────────────────
    # All positions are multiples of 2.54mm (100-mil grid) → pins land on 1.27mm grid
    # Layout (A3: 420×297mm)
    # J1 USB-C:       18×2.54=45.72,  30×2.54=76.2
    # U2 MCP73831:   40×2.54=101.6,  30×2.54=76.2
    # J2 JST BAT:     18×2.54=45.72,  45×2.54=114.3
    # C7 VBUS cap:    27×2.54=68.58,  28×2.54=71.12
    # C8 VBAT bulk:   28×2.54=71.12,  43×2.54=109.22
    # C9 VBAT bulk:   33×2.54=83.82,  43×2.54=109.22
    # R1 PROG:        45×2.54=114.3,  37×2.54=93.98
    # R2 CC1:         15×2.54=38.1,   37×2.54=93.98
    # R3 CC2:         15×2.54=38.1,   42×2.54=106.68
    # R4 LED:         47×2.54=119.38, 43×2.54=109.22
    # D1 LED:         55×2.54=139.7,  43×2.54=109.22
    # U1 nRF9161:     79×2.54=200.66, 70×2.54=177.8
    # C1-C4 decap:    76/79/83/74 × 2.54, 43×2.54=109.22
    # C10 SIM VCC:   110×2.54=279.4,  80×2.54=203.2
    # J3 SIM:        119×2.54=302.26, 83×2.54=210.82
    # J4 LTE UFL:     57×2.54=144.78, 70×2.54=177.8
    # J5 GPS UFL:     57×2.54=144.78, 76×2.54=193.04
    # J6 SWD:         24×2.54=60.96,  57×2.54=144.78

    J1x,  J1y  = 45.72,  76.20
    U2x,  U2y  = 101.6,  76.20
    J2x,  J2y  = 45.72,  114.3
    C7x,  C7y  = 68.58,  71.12
    C8x,  C8y  = 71.12,  109.22
    C9x,  C9y  = 83.82,  109.22
    R1x,  R1y  = 114.3,  93.98
    R2x,  R2y  = 38.10,  93.98
    R3x,  R3y  = 38.10,  106.68
    R4x,  R4y  = 119.38, 109.22
    D1x,  D1y  = 139.70, 109.22
    U1x,  U1y  = 200.66, 177.80
    C1x,  C1y  = 193.04, 109.22
    C2x,  C2y  = 200.66, 109.22
    C3x,  C3y  = 210.82, 109.22
    C4x,  C4y  = 187.96, 109.22
    C10x, C10y = 279.40, 203.20
    J3x,  J3y  = 302.26, 210.82
    J4x,  J4y  = 144.78, 177.80
    J5x,  J5y  = 144.78, 193.04
    J6x,  J6y  = 60.96,  144.78

    comps = []
    comps.append(inst("Custom:USBC_PWR",    "J1", "TYPE-C-31-M-12",          J1x, J1y,
        fp="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"))
    comps.append(inst("Custom:MCP73831T",   "U2", "MCP73831T-2ACI/OT",       U2x, U2y,
        fp="Package_TO_SOT_SMD:SOT-23-5"))
    comps.append(inst("Custom:JST_PH_BAT",  "J2", "JST-PH-2P 250mAh LiPo",  J2x, J2y,
        fp="Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"))
    comps.append(inst("Device:C", "C7",  "100nF 0402 10V",  C7x,  C7y,
        fp="Capacitor_SMD:C_0402_1005Metric"))
    comps.append(inst("Device:C", "C8",  "10uF 0805 10V",   C8x,  C8y,
        fp="Capacitor_SMD:C_0805_2012Metric"))
    comps.append(inst("Device:C", "C9",  "10uF 0805 10V",   C9x,  C9y,
        fp="Capacitor_SMD:C_0805_2012Metric"))
    comps.append(inst("Device:R", "R1",  "2k 0402",         R1x,  R1y,
        fp="Resistor_SMD:R_0402_1005Metric"))
    comps.append(inst("Device:R", "R2",  "5.1k 0402",       R2x,  R2y,
        fp="Resistor_SMD:R_0402_1005Metric"))
    comps.append(inst("Device:R", "R3",  "5.1k 0402",       R3x,  R3y,
        fp="Resistor_SMD:R_0402_1005Metric"))
    comps.append(inst("Device:R", "R4",  "330 0402",        R4x,  R4y,
        fp="Resistor_SMD:R_0402_1005Metric"))
    comps.append(inst("Device:LED","D1", "LED_Green 0402",  D1x,  D1y,
        fp="LED_SMD:LED_0402_1005Metric"))
    comps.append(inst("MCU_Nordic:nRF9160-SIxA", "U1", "nRF9161-LACA-R7", U1x, U1y,
        fp="Package_LGA:Nordic_nRF9160-SIxx_LGA-102-59EP_16.0x10.5mm_P0.5mm",
        ds="https://infocenter.nordicsemi.com/pdf/nRF9161_PS.pdf",
        extra={"LCSC": "C5765359"}))
    comps.append(inst("Device:C", "C1",  "100nF 0402 10V",  C1x,  C1y,
        fp="Capacitor_SMD:C_0402_1005Metric"))
    comps.append(inst("Device:C", "C2",  "100nF 0402 10V",  C2x,  C2y,
        fp="Capacitor_SMD:C_0402_1005Metric"))
    comps.append(inst("Device:C", "C3",  "100nF 0402 10V",  C3x,  C3y,
        fp="Capacitor_SMD:C_0402_1005Metric"))
    comps.append(inst("Device:C", "C4",  "100nF 0402 10V",  C4x,  C4y,
        fp="Capacitor_SMD:C_0402_1005Metric"))
    comps.append(inst("Device:C", "C10", "100nF 0402 10V",  C10x, C10y,
        fp="Capacitor_SMD:C_0402_1005Metric"))
    comps.append(inst("Custom:SIM_Nano", "J3", "Nano SIM HYC10-TF08A", J3x, J3y,
        fp="Custom:SIM_Nano_SMD",
        extra={"LCSC": "C5882851"}))
    comps.append(inst("Custom:UFL", "J4", "U.FL LTE",  J4x, J4y,
        fp="Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
        extra={"LCSC": "C88374"}))
    comps.append(inst("Custom:UFL", "J5", "U.FL GPS",  J5x, J5y,
        fp="Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
        extra={"LCSC": "C88374"}))
    comps.append(inst("Custom:SWD_Header", "J6", "SWD 1.27mm 4P", J6x, J6y,
        fp="Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical_SMD",
        extra={"LCSC": "C429954"}))

    elems.extend(comps)

    # ── NET LABELS & GND SYMBOLS ─────────────────────────────────────────────
    nets = []

    def L(net, cx, cy, sx, sy):
        x, y = pa(cx, cy, sx, sy)
        nets.append(label(net, x, y))

    def G(cx, cy, sx, sy):
        x, y = pa(cx, cy, sx, sy)
        nets.append(gnd_inst(x, y))

    def NC(cx, cy, sx, sy):
        x, y = pa(cx, cy, sx, sy)
        nets.append(no_connect(x, y))

    # ── J1 USB-C ─────────────────────────────────────────────────────────────
    L("VBUS", J1x, J1y, -8.89,  5.08)
    L("VBUS", J1x, J1y, -8.89,  2.54)
    L("CC1",  J1x, J1y, -8.89, -2.54)
    L("CC2",  J1x, J1y, -8.89, -5.08)
    G(J1x, J1y,  8.89,  5.08)
    G(J1x, J1y,  8.89,  2.54)
    G(J1x, J1y,  8.89,  0)

    # ── U2 MCP73831 ──────────────────────────────────────────────────────────
    L("STAT",   U2x, U2y, -10.16,  2.54)
    G(U2x, U2y, -10.16, -2.54)
    L("PROG_R", U2x, U2y,  10.16,  2.54)
    L("VBUS",   U2x, U2y,  10.16, -2.54)
    L("VBAT",   U2x, U2y,  0,     -7.62)

    # ── J2 JST Battery ───────────────────────────────────────────────────────
    L("VBAT", J2x, J2y, -6.35,  1.27)
    G(J2x, J2y, -6.35, -1.27)

    # ── C7 VBUS bypass ───────────────────────────────────────────────────────
    L("VBUS", C7x, C7y,  0,  3.81)
    G(C7x, C7y,  0, -3.81)

    # ── C8 VBAT bulk ─────────────────────────────────────────────────────────
    L("VBAT", C8x, C8y,  0,  3.81)
    G(C8x, C8y,  0, -3.81)

    # ── C9 VBAT bulk ─────────────────────────────────────────────────────────
    L("VBAT", C9x, C9y,  0,  3.81)
    G(C9x, C9y,  0, -3.81)

    # ── R1 PROG (2kΩ) ────────────────────────────────────────────────────────
    L("PROG_R", R1x, R1y,  0,  3.81)
    G(R1x, R1y,  0, -3.81)

    # ── R2 CC1 (5.1kΩ) ───────────────────────────────────────────────────────
    L("CC1", R2x, R2y,  0,  3.81)
    G(R2x, R2y,  0, -3.81)

    # ── R3 CC2 (5.1kΩ) ───────────────────────────────────────────────────────
    L("CC2", R3x, R3y,  0,  3.81)
    G(R3x, R3y,  0, -3.81)

    # ── R4 LED (330Ω) ─────────────────────────────────────────────────────────
    L("STAT",  R4x, R4y,  0,  3.81)
    L("LED_A", R4x, R4y,  0, -3.81)

    # ── D1 LED ────────────────────────────────────────────────────────────────
    G(D1x, D1y, -3.81,  0)
    L("LED_A", D1x, D1y,  3.81,  0)

    # ── U1 nRF9161 ────────────────────────────────────────────────────────────
    L("VBAT",    U1x, U1y, -25.40,  45.72)   # ENABLE → tie to VBAT
    L("SWDCLK",  U1x, U1y, -25.40,  38.10)
    L("SWDIO",   U1x, U1y, -25.40,  35.56)
    L("LTE_ANT", U1x, U1y, -25.40,   5.08)
    L("GPS_ANT", U1x, U1y, -25.40, -10.16)
    L("SIM_VCC", U1x, U1y, -25.40, -25.40)   # SIM_1V8
    L("SIM_CLK", U1x, U1y, -25.40, -27.94)
    L("SIM_RST", U1x, U1y, -25.40, -30.48)
    L("SIM_IO",  U1x, U1y, -25.40, -33.02)
    L("VBAT",    U1x, U1y,   0.00,  53.34)   # VDD1
    L("VBAT",    U1x, U1y,   2.54,  53.34)   # VDD2
    L("VBAT",    U1x, U1y,   7.62,  53.34)   # VDD_GPIO
    L("DEC0",    U1x, U1y,  -5.08,  53.34)   # DEC0
    G(U1x, U1y,   0.00, -53.34)              # VSS (GND Shield)

    # No-connect: left side unused pins
    NC(U1x, U1y, -25.40,  40.64)  # ~{RESET}
    NC(U1x, U1y, -25.40,  25.40)  # COEX0
    NC(U1x, U1y, -25.40,  22.86)  # COEX1
    NC(U1x, U1y, -25.40,  20.32)  # COEX2
    NC(U1x, U1y, -25.40,   0.00)  # AUX
    NC(U1x, U1y, -25.40, -40.64)  # VIO
    NC(U1x, U1y, -25.40, -43.18)  # SCLK
    NC(U1x, U1y, -25.40, -45.72)  # SDATA

    # No-connect: right side GPIO (P0.00 – P0.31, MAGPIO, NC pads)
    for sy in [45.72, 43.18, 40.64, 38.10, 35.56, 33.02, 30.48, 27.94,
               25.40, 22.86, 20.32, 17.78, 15.24, 12.70, 10.16,  7.62,
                5.08,  2.54,  0.00, -2.54, -5.08, -7.62,-10.16,-12.70,
              -15.24,-17.78,-20.32,-22.86,-25.40,-27.94,-30.48,-33.02,
              -40.64,-43.18,-45.72]:
        NC(U1x, U1y, 25.40, sy)

    # ── C1-C4 decoupling ──────────────────────────────────────────────────────
    L("VBAT", C1x, C1y,  0,  3.81)
    G(C1x, C1y,  0, -3.81)
    L("VBAT", C2x, C2y,  0,  3.81)
    G(C2x, C2y,  0, -3.81)
    L("VBAT", C3x, C3y,  0,  3.81)
    G(C3x, C3y,  0, -3.81)
    L("DEC0", C4x, C4y,  0,  3.81)
    G(C4x, C4y,  0, -3.81)

    # ── J3 SIM ────────────────────────────────────────────────────────────────
    L("SIM_VCC", J3x, J3y, -10.16,  5.08)
    L("SIM_RST", J3x, J3y, -10.16,  2.54)
    L("SIM_CLK", J3x, J3y, -10.16,  0)
    L("SIM_IO",  J3x, J3y, -10.16, -2.54)
    G(J3x, J3y,  10.16,  2.54)
    NC(J3x, J3y, 10.16, -2.54)              # CD not used

    # ── C10 SIM VCC bypass ────────────────────────────────────────────────────
    L("SIM_VCC", C10x, C10y,  0,  3.81)
    G(C10x, C10y,  0, -3.81)

    # ── J4 LTE U.FL ───────────────────────────────────────────────────────────
    L("LTE_ANT", J4x, J4y, -5.08, 0)
    G(J4x, J4y,  5.08, 0)

    # ── J5 GPS U.FL ───────────────────────────────────────────────────────────
    L("GPS_ANT", J5x, J5y, -5.08, 0)
    G(J5x, J5y,  5.08, 0)

    # ── J6 SWD ────────────────────────────────────────────────────────────────
    L("VBAT",   J6x, J6y, -6.35,  3.81)
    L("SWDIO",  J6x, J6y, -6.35,  1.27)
    L("SWDCLK", J6x, J6y, -6.35, -1.27)
    G(J6x, J6y, -6.35, -3.81)

    # ── PWR_FLAG (resolves power_pin_not_driven) ──────────────────────────────
    # GND net: place near J1 GND1 pin
    gnd_flag_x, gnd_flag_y = pa(J1x, J1y, 8.89, 5.08)
    nets.append(pwr_flag_inst(gnd_flag_x, gnd_flag_y + 5.08, "GND"))
    nets.append(gnd_inst(gnd_flag_x, gnd_flag_y + 5.08))

    # VBUS net: place near J1 VBUS1 pin
    vbus_flag_x, vbus_flag_y = pa(J1x, J1y, -8.89, 5.08)
    nets.append(pwr_flag_inst(vbus_flag_x, vbus_flag_y - 5.08, "VBUS"))

    elems.extend(nets)

    # ── ANNOTATION TEXT ───────────────────────────────────────────────────────
    notes = [
        text("GPS Cat Tracker — nRF9161 SiP  |  20x35mm PCB  |  <16g", 20, 20),
        text("MIC 77859B | 1NCE LTE-M (SoftBank) | Charge: 1000/R1[kΩ] mA", 20, 25),
        text("=== POWER ===", 20, 52),
        text("J1=USB-C 5V in  →  U2=MCP73831 charger  →  VBAT=LiPo 3.7V", 20, 57),
        text("R1=2kΩ sets 500mA charge (use 4kΩ for 250mA safe)", 20, 62),
        text("R2,R3=5.1kΩ CC pull-down (tells host: 5V/900mA)", 20, 67),
        text("=== nRF9161 ===", 150, 88),
        text("VDD1,VDD2,VDD_GPIO,ENABLE → VBAT (3.3-5.5V)", 150, 93),
        text("DEC0 → C4 100nF to GND", 150, 98),
        text("SIM interface: SIM_VCC(1.8V out), CLK, RST, IO", 150, 248),
        text("SWD debug: SWDCLK, SWDIO  (J-Link EDU Mini)", 20, 160),
    ]
    elems.extend(notes)

    # ── FOOTER ───────────────────────────────────────────────────────────────
    footer = """  (sheet_instances
    (path "/" (page "1"))
  )
)"""

    body = header + "\n\n" + lib_block + "\n\n" + "\n".join(elems) + "\n\n" + footer
    return body


if __name__ == "__main__":
    import os
    out = os.path.join(os.path.dirname(__file__), "gps-cat-tracker.kicad_sch")
    sch = build()
    with open(out, "w", encoding="utf-8") as f:
        f.write(sch)
    nc_count  = sch.count("(no_connect")
    lbl_count = sch.count("\n  (label")
    gnd_count = sch.count('(lib_id "power:GND")')
    flag_count= sch.count('(lib_id "power:PWR_FLAG")')
    print(f"✓ {out}")
    print(f"  {len(sch):,} bytes  |  labels: {lbl_count}  no_connect: {nc_count}  gnd_syms: {gnd_count}  pwr_flags: {flag_count}")
    print("  Open KiCad → Open Project → gps-cat-tracker.kicad_pro")
    print("  Run ERC to verify (目標: 0 errors)")

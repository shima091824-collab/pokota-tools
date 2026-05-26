#!/usr/bin/env python3
"""
GPS Cat Tracker LoRa Edition — KiCad PCB Generator
Board: 50×30mm
Components:
  U1: E220-900T22S(JP)  LoRa module (16×26mm, 24 castellated pads)
  U2: XIAO nRF52840     MCU+BLE (17.5×21mm, 14 castellated pads)
  U3: MAX-M10S          GPS (4.1×3.1mm, LCC-16)
  J1: JST-GH 1.25mm 2P Battery connector
  C1-C4: 100nF 0402     Decoupling caps
  R1: 10kΩ 0402         Pull-up
"""

LAYERS = """  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user "B.Fabrication")
    (49 "F.Fab" user "F.Fabrication")
  )"""

SETUP = """  (setup
    (pad_to_mask_clearance 0)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros false)
      (usegerberextensions false)
      (usegerberattributes true)
      (usegerberadvancedattributes true)
      (creategerberjobfile true)
      (dashed_line_dash_ratio 12.000000)
      (dashed_line_gap_ratio 3.000000)
      (svgprecision 4)
      (plotframeref false)
      (viasonmask false)
      (mode 1)
      (useauxorigin false)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (dxfpolygonmode true)
      (dxfimperialunits true)
      (dxfusepcbnewfont true)
      (psnegative false)
      (psa4output false)
      (plotreference true)
      (plotvalue true)
      (plotinvisibletext false)
      (sketchpadsonfab false)
      (subtractmaskfromsilk false)
      (outputformat 1)
      (mirror false)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "gerber/")
    )
  )"""


def fmt(v):
    """Format float to 4 decimal places."""
    return f"{v:.4f}"


def smd_pad(num, x, y, w, h, layer="F"):
    """Generate an SMD pad."""
    layers = f'"{layer}.Cu" "{layer}.Paste" "{layer}.Mask"'
    return f'    (pad "{num}" smd rect (at {fmt(x)} {fmt(y)}) (size {fmt(w)} {fmt(h)}) (layers {layers}))'


def fp_rect(x1, y1, x2, y2, layer, width=0.1):
    """Generate a footprint rectangle."""
    return (f'    (fp_rect (start {fmt(x1)} {fmt(y1)}) (end {fmt(x2)} {fmt(y2)}) '
            f'(layer "{layer}") (stroke (width {fmt(width)}) (type solid)))')


def fp_text(text, ref_or_val, x, y, layer, size=1.0, thickness=0.15):
    """Generate a footprint text."""
    kind = "reference" if ref_or_val == "ref" else "value"
    return (f'    (fp_text {kind} "{text}" (at {fmt(x)} {fmt(y)}) (layer "{layer}")\n'
            f'      (effects (font (size {fmt(size)} {fmt(size)}) (thickness {fmt(thickness)}))))')


def make_e220(cx, cy, rot=0):
    """
    E220-900T22S(JP) footprint
    Size: 16mm (W) × 26mm (H)
    24 castellated pads: 12 per long side
    Pad pitch: 2mm, pad size: 1.7×0.8mm
    Pins (left side, top to bottom):
      1=GND, 2=VCC, 3=M0, 4=M1, 5=RXD, 6=TXD,
      7=AUX, 8=NC, 9=NC, 10=NC, 11=NC, 12=GND
    Pins (right side, top to bottom):
      13=GND, 14=NC, 15=NC, 16=NC, 17=NC, 18=NC,
      19=NC, 20=NC, 21=NC, 22=NC, 23=NC, 24=GND
    NOTE: Verify against actual datasheet before manufacturing!
    """
    # Module half-dimensions
    hw = 8.0   # 16/2
    hh = 13.0  # 26/2

    pads = []
    pad_w = 1.7  # pad width (extends beyond edge for castle)
    pad_h = 0.8  # pad height

    # Left side (12 pads): x = -hw, y from -(11) to +(11) at 2mm pitch
    left_pins = ["GND", "VCC", "M0", "M1", "RXD", "TXD", "AUX", "NC", "NC", "NC", "NC", "GND"]
    for i, name in enumerate(left_pins):
        py = -11.0 + i * 2.0
        pads.append(smd_pad(i + 1, -hw, py, pad_w, pad_h))

    # Right side (12 pads): x = +hw, same y values
    right_pins = ["GND", "NC", "NC", "NC", "NC", "NC", "NC", "NC", "NC", "NC", "NC", "GND"]
    for i, name in enumerate(right_pins):
        py = -11.0 + i * 2.0
        pads.append(smd_pad(i + 13, hw, py, pad_w, pad_h))

    lines = [
        f'  (footprint "Custom:E220-900T22S_JP"',
        f'    (layer "F.Cu")',
        f'    (at {fmt(cx)} {fmt(cy)} {rot})',
        fp_text("U1", "ref", 0, -hh - 1.5, "F.SilkS"),
        fp_text("E220-900T22S(JP)", "val", 0, hh + 1.5, "F.Fab"),
        # Courtyard (add 0.5mm margin)
        fp_rect(-hw - 0.5, -hh - 0.5, hw + 0.5, hh + 0.5, "F.CrtYd", 0.05),
        # Fabrication outline
        fp_rect(-hw, -hh, hw, hh, "F.Fab", 0.1),
        # Silkscreen outline
        fp_rect(-hw - 0.2, -hh - 0.2, hw + 0.2, hh + 0.2, "F.SilkS", 0.12),
        # Antenna keep-out note line
        f'    (fp_text user "ANT" (at 0 0) (layer "F.Fab")'
        f'\n      (effects (font (size 1.5 1.5) (thickness 0.2))))',
    ]
    lines += pads
    lines.append('  )')
    return '\n'.join(lines)


def make_xiao_nrf52840(cx, cy, rot=0):
    """
    Seeed XIAO nRF52840 module footprint
    Size: 17.5mm (W) × 21mm (H)
    14 castellated pads: 7 per long side
    Pad pitch: 2.54mm
    Left side (top to bottom): D0/TX, D1/RX, D2, D3, D4/SDA, D5/SCL, D6/TX_nRF
    Right side (top to bottom): VIN, GND, 3V3, NC, RST, A0, A1
    NOTE: Verify against actual Seeed datasheet!
    """
    hw = 8.75   # 17.5/2
    hh = 10.5   # 21/2

    pads = []
    pad_w = 1.8
    pad_h = 0.9

    # Left side (7 pads at 2.54mm pitch)
    left_pins = ["TX", "RX", "D2", "D3", "SDA", "SCL", "TX0"]
    # Span = 6*2.54 = 15.24mm, start at -7.62, end at +7.62
    for i, name in enumerate(left_pins):
        py = -7.62 + i * 2.54
        pads.append(smd_pad(i + 1, -hw, py, pad_w, pad_h))

    # Right side (7 pads at 2.54mm pitch)
    right_pins = ["VIN", "GND", "3V3", "NC", "RST", "A0", "A1"]
    for i, name in enumerate(right_pins):
        py = -7.62 + i * 2.54
        pads.append(smd_pad(i + 8, hw, py, pad_w, pad_h))

    lines = [
        f'  (footprint "Custom:XIAO_nRF52840"',
        f'    (layer "F.Cu")',
        f'    (at {fmt(cx)} {fmt(cy)} {rot})',
        fp_text("U2", "ref", 0, -hh - 1.5, "F.SilkS"),
        fp_text("XIAO_nRF52840", "val", 0, hh + 1.5, "F.Fab"),
        fp_rect(-hw - 0.5, -hh - 0.5, hw + 0.5, hh + 0.5, "F.CrtYd", 0.05),
        fp_rect(-hw, -hh, hw, hh, "F.Fab", 0.1),
        fp_rect(-hw - 0.2, -hh - 0.2, hw + 0.2, hh + 0.2, "F.SilkS", 0.12),
        f'    (fp_text user "USB-C" (at 0 -9) (layer "F.Fab")'
        f'\n      (effects (font (size 0.8 0.8) (thickness 0.15))))',
    ]
    lines += pads
    lines.append('  )')
    return '\n'.join(lines)


def make_max_m10s(cx, cy, rot=0):
    """
    u-blox MAX-M10S GPS module footprint
    Size: 4.1×3.1mm, LCC-16
    16 pads on 4 sides
    """
    hw = 2.05   # 4.1/2
    hh = 1.55   # 3.1/2

    pads = []
    pad_w = 0.7
    pad_h = 0.4

    # Bottom side (5 pads along 4.1mm): VCC, IO1, IO2, GND, TIMEPULSE
    # Left side (3 pads): GND, ANT, GND
    # Top side (5 pads): GND, TX, RX, RSVD, GND
    # Right side (3 pads): GND, GND, GND

    # Simplified: 4 pads per side at 0.8mm pitch (approximate)
    # Bottom row (y=+hh): pads 1-4
    btm_x = [-0.6, -0.2, 0.2, 0.6]  # simplified layout
    for i, bx in enumerate(btm_x):
        pads.append(smd_pad(i + 1, bx, hh, pad_h, pad_w))

    # Left side (x=-hw): pads 5-8
    lft_y = [-0.4, 0, 0.4]
    for i, ly in enumerate(lft_y):
        pads.append(smd_pad(i + 5, -hw, ly, pad_w, pad_h))

    # Top row (y=-hh): pads 8-12
    top_x = [-0.6, -0.2, 0.2, 0.6]
    for i, tx in enumerate(top_x):
        pads.append(smd_pad(i + 8, tx, -hh, pad_h, pad_w))

    # Right side (x=+hw): pads 13-16
    rgt_y = [-0.4, 0, 0.4]
    for i, ry in enumerate(rgt_y):
        pads.append(smd_pad(i + 13, hw, ry, pad_w, pad_h))

    # Center GND pad (exposed)
    pads.append(smd_pad("GND", 0, 0, 2.5, 1.2))

    lines = [
        f'  (footprint "Custom:MAX-M10S"',
        f'    (layer "F.Cu")',
        f'    (at {fmt(cx)} {fmt(cy)} {rot})',
        fp_text("U3", "ref", 0, -hh - 1.2, "F.SilkS", size=0.7),
        fp_text("MAX-M10S", "val", 0, hh + 1.2, "F.Fab", size=0.7),
        fp_rect(-hw - 0.5, -hh - 0.5, hw + 0.5, hh + 0.5, "F.CrtYd", 0.05),
        fp_rect(-hw, -hh, hw, hh, "F.Fab", 0.1),
        fp_rect(-hw - 0.15, -hh - 0.15, hw + 0.15, hh + 0.15, "F.SilkS", 0.12),
    ]
    lines += pads
    lines.append('  )')
    return '\n'.join(lines)


def make_jst_gh_1v25_2p(cx, cy, rot=0):
    """
    JST GH 1.25mm pitch 2-pin SMD connector (horizontal)
    Battery connector: +BATT, GND
    """
    hw = 1.25   # half-width
    hh = 2.0    # half-height

    pads = [
        smd_pad(1, -hw / 2, 0, 1.5, 2.5),  # +BATT
        smd_pad(2, hw / 2, 0, 1.5, 2.5),   # GND
    ]

    lines = [
        f'  (footprint "Custom:JST_GH_1v25_2P"',
        f'    (layer "F.Cu")',
        f'    (at {fmt(cx)} {fmt(cy)} {rot})',
        fp_text("J1", "ref", 0, -hh - 1.0, "F.SilkS", size=0.8),
        fp_text("BAT+/GND", "val", 0, hh + 1.0, "F.Fab", size=0.8),
        fp_rect(-hw - 0.5, -hh - 0.5, hw + 0.5, hh + 0.5, "F.CrtYd", 0.05),
        fp_rect(-hw, -hh, hw, hh, "F.Fab", 0.1),
        fp_rect(-hw - 0.2, -hh - 0.2, hw + 0.2, hh + 0.2, "F.SilkS", 0.12),
    ]
    lines += pads
    lines.append('  )')
    return '\n'.join(lines)


def make_0402(ref, value, cx, cy, rot=0):
    """0402 SMD passive (resistor/capacitor)."""
    pads = [
        smd_pad(1, -0.9, 0, 0.9, 0.5),
        smd_pad(2,  0.9, 0, 0.9, 0.5),
    ]
    lines = [
        f'  (footprint "Resistor_SMD:R_0402_1005Metric"',
        f'    (layer "F.Cu")',
        f'    (at {fmt(cx)} {fmt(cy)} {rot})',
        fp_text(ref, "ref", 0, -0.9, "F.SilkS", size=0.5, thickness=0.08),
        fp_text(value, "val", 0, 0.9, "F.Fab", size=0.5, thickness=0.08),
        fp_rect(-1.1, -0.65, 1.1, 0.65, "F.CrtYd", 0.05),
        fp_rect(-0.5, -0.25, 0.5, 0.25, "F.Fab", 0.1),
        fp_rect(-1.1, -0.65, 1.1, 0.65, "F.SilkS", 0.12),
    ]
    lines += pads
    lines.append('  )')
    return '\n'.join(lines)


def make_board_title(board_w, board_h):
    """Add title/version text to board."""
    lines = []
    # Board info text
    lines.append(
        f'  (gr_text "GPS Cat Tracker LoRa v1.0  50x30mm" '
        f'(at {fmt(board_w/2)} {fmt(-3)} 0) (layer "F.SilkS")\n'
        f'    (effects (font (size 1.0 1.0) (thickness 0.15))))'
    )
    lines.append(
        f'  (gr_text "E220-900T22S(JP) + XIAO nRF52840 + MAX-M10S" '
        f'(at {fmt(board_w/2)} {fmt(-1.5)} 0) (layer "F.SilkS")\n'
        f'    (effects (font (size 0.8 0.8) (thickness 0.12))))'
    )
    return '\n'.join(lines)


def generate_pcb():
    board_w = 50.0
    board_h = 30.0

    # ── Component placements ──────────────────────────────────────
    # E220-900T22S(JP): 16×26mm → center at (14, 15)
    #   Occupies: X=1..27, Y=2..28 with courtyard
    e220_cx, e220_cy = 14.0, 15.0

    # XIAO nRF52840: 17.5×21mm → center at (40, 12)
    #   Occupies: X=31.25..48.75, Y=1.5..22.5 with courtyard
    xiao_cx, xiao_cy = 40.0, 12.0

    # MAX-M10S: 4.1×3.1mm → top-right corner, center at (45, 26)
    #   Near edge for GPS antenna sky visibility
    gps_cx, gps_cy = 45.0, 26.0

    # JST connector: center at (36, 26)
    jst_cx, jst_cy = 36.0, 26.0

    # Decoupling caps (4 × 100nF 0402)
    passives = [
        ("C1", "100nF", 28.0, 20.0),
        ("C2", "100nF", 28.0, 22.0),
        ("C3", "100nF", 28.0, 24.0),
        ("C4", "100nF", 28.0, 26.0),
        ("R1", "10k",   28.0, 28.0),
    ]

    # ── Net labels (for reference in silkscreen) ──────────────────
    net_labels = [
        # E220 pins
        (f"  (gr_text \"GND\" (at {fmt(e220_cx-9)} {fmt(e220_cy-11)} 0) "
         f"(layer \"F.SilkS\")\n    (effects (font (size 0.5 0.5) (thickness 0.08))))"),
        (f"  (gr_text \"VCC\" (at {fmt(e220_cx-9)} {fmt(e220_cy-9)} 0) "
         f"(layer \"F.SilkS\")\n    (effects (font (size 0.5 0.5) (thickness 0.08))))"),
        (f"  (gr_text \"M0\" (at {fmt(e220_cx-9)} {fmt(e220_cy-7)} 0) "
         f"(layer \"F.SilkS\")\n    (effects (font (size 0.5 0.5) (thickness 0.08))))"),
        (f"  (gr_text \"M1\" (at {fmt(e220_cx-9)} {fmt(e220_cy-5)} 0) "
         f"(layer \"F.SilkS\")\n    (effects (font (size 0.5 0.5) (thickness 0.08))))"),
        (f"  (gr_text \"RXD\" (at {fmt(e220_cx-9)} {fmt(e220_cy-3)} 0) "
         f"(layer \"F.SilkS\")\n    (effects (font (size 0.5 0.5) (thickness 0.08))))"),
        (f"  (gr_text \"TXD\" (at {fmt(e220_cx-9)} {fmt(e220_cy-1)} 0) "
         f"(layer \"F.SilkS\")\n    (effects (font (size 0.5 0.5) (thickness 0.08))))"),
        (f"  (gr_text \"AUX\" (at {fmt(e220_cx-9)} {fmt(e220_cy+1)} 0) "
         f"(layer \"F.SilkS\")\n    (effects (font (size 0.5 0.5) (thickness 0.08))))"),
    ]

    parts = [
        make_e220(e220_cx, e220_cy),
        make_xiao_nrf52840(xiao_cx, xiao_cy),
        make_max_m10s(gps_cx, gps_cy),
        make_jst_gh_1v25_2p(jst_cx, jst_cy),
    ] + [make_0402(ref, val, cx, cy) for ref, val, cx, cy in passives]

    # Board outline
    board_outline = f"""  (gr_rect
    (start 0 0)
    (end {fmt(board_w)} {fmt(board_h)})
    (stroke
      (width 0.05)
      (type solid)
    )
    (layer "Edge.Cuts")
  )"""

    # Mounting holes (optional, 2mm drill at corners)
    mounting = []
    for mx, my in [(2.5, 2.5), (board_w - 2.5, 2.5), (2.5, board_h - 2.5), (board_w - 2.5, board_h - 2.5)]:
        mounting.append(
            f'  (footprint "MountingHole:MountingHole_2mm_Pad_Via"\n'
            f'    (layer "F.Cu")\n'
            f'    (at {fmt(mx)} {fmt(my)})\n'
            f'    (pad "1" thru_hole circle (at 0 0) (size 3.2 3.2) (drill 2) (layers "*.Cu" "*.Mask"))\n'
            f'  )'
        )

    pcb = f"""(kicad_pcb
  (version 20221018)
  (generator pcbnew)
  (general
    (thickness 1.6)
  )
  (paper "A4")
{LAYERS}
{SETUP}

  ; ── Board outline ─────────────────────────────────────────────
{board_outline}

  ; ── Mounting holes ────────────────────────────────────────────
{''.join(mounting)}

  ; ── Components ────────────────────────────────────────────────
{''.join(p + chr(10) for p in parts)}
  ; ── Net labels / silkscreen notes ────────────────────────────
{''.join(nl + chr(10) for nl in net_labels)}
  ; ── Design notes ──────────────────────────────────────────────
  (gr_text "UART: XIAO TX→E220 RXD  XIAO RX→E220 TXD" (at 25 0.8 0) (layer "Dwgs.User")
    (effects (font (size 0.8 0.8) (thickness 0.12))))
  (gr_text "GPS: XIAO D4(SDA)→MAX TX  D5(SCL)→MAX RX" (at 25 2.0 0) (layer "Dwgs.User")
    (effects (font (size 0.8 0.8) (thickness 0.12))))
  (gr_text "PWR: XIAO 3V3→E220 VCC  XIAO 3V3→MAX VCC" (at 25 3.2 0) (layer "Dwgs.User")
    (effects (font (size 0.8 0.8) (thickness 0.12))))
  (gr_text "NOTE: Verify all footprints vs datasheets before ordering!" (at 25 4.4 0) (layer "Cmts.User")
    (effects (font (size 0.8 0.8) (thickness 0.12))))
)
"""
    return pcb


if __name__ == "__main__":
    output = generate_pcb()
    path = "/Users/m2mac/gps-cat-tracker/gps-cat-tracker-lora.kicad_pcb"
    with open(path, "w") as f:
        f.write(output)
    print(f"Written: {path}")
    print(f"Board: 50×30mm")
    print(f"Components:")
    print(f"  U1 E220-900T22S(JP): center (14, 15)")
    print(f"  U2 XIAO nRF52840:    center (40, 12)")
    print(f"  U3 MAX-M10S GPS:     center (45, 26)")
    print(f"  J1 JST 1.25mm:       center (36, 26)")
    print(f"  C1-C4, R1:           (28, 20-28)")

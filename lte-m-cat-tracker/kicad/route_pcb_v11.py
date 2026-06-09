#!/usr/bin/env python3
"""
LTE-M Cat Tracker PCB Routing Script v11 — 完全再設計版（shorts=0を目標）
旧v11は33ショートを発生。以下の問題を全修正：
- VBAT_SW: y=1.0 F.CuトランクがSIM B.Cuコリドー(y=2.0-3.5)と干渉→B.Cu右トランク(x=27.5)を使用
- SIM bottom signals: F.Cu下降ではなくB.Cu上行コリドー方式を採用
- TXD/RXD: GND thermal pad(y=21.65-25.35)と交差する経路を修正
- RESETN: C2.pad2[GND]と+3.3V B.Cu(x=6.5)を回避する経路に変更
- SIM_STATUS: B.Cu y=0.6はVBAT_SW B.Cu(y=1.26)と近すぎ→F.Cu直接ルート
- SIM_PWRKEY: B.Cu y=0.9→B.Cu y=1.26 pad座標から直接

U1中心 (15,10)。絶対パッド座標:
  上辺(y=1.26): pad34(19.40)[VBAT_SW], pad35(18.30)[VBAT_SW], pad39(13.90)[PWRKEY], pad42(10.60)[STATUS]
  右辺(x=23.75): pad32(y=5.05)[LTE_ANT], pad28(y=9.45)[RESETN], pad23(y=14.95)[RXD], pad22(y=16.05)[TXD]
  下辺(y=18.74): pad15(x=12.80)[DATA], pad16(x=13.90)[CLK], pad17(x=15.00)[RST], pad18(x=16.10)[VDD]
  内部LGA: pad68(19.40,5.05)[GNSS_ANT]

B.Cu SIMコリドー（上行）:
  DATA: y=2.0→x=26.0降下, CLK: y=2.5→x=25.5降下, RST: y=3.0→x=24.0降下, VDD: y=3.5→x=22.0降下

注意:
- LTE_ANT, GNSS_ANT: W_RF不可（U1隣接パッドクリアランス不足）→ W_S=0.2mm使用
- SIM_DATA B.Cu 降下x=26.0（+3.3V B.Cu x=26.55を回避）
- SIM_RXD B.Cu 降下x=28.5、水平y=33.0（CC1 B.Cu y=32.0回避）
- SIM_STATUS: WIFI_ANT F.Cu(y=20.87, x=1-5.8)回避のためB.Cu経由
- SIM_RESETN B.Cu: +3.3V水平(y=26.5)、SIM_TXD(x=9.5)回避のためy=32.5水平
- U2全パッド: PCBネット未割当（DRC偽陽性あり）
- 削除: dangling VBAT_SW segment (24.35,8.2)→(25.02,8)
"""

import uuid, re, shutil

PCB = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'
BAK = PCB + '.bak_v11'

def U():
    return str(uuid.uuid4())

def seg(x1, y1, x2, y2, w, layer, net):
    return (f'\t(segment\n'
            f'\t\t(start {x1} {y1})\n'
            f'\t\t(end {x2} {y2})\n'
            f'\t\t(width {w})\n'
            f'\t\t(layer "{layer}")\n'
            f'\t\t(net "{net}")\n'
            f'\t\t(uuid "{U()}")\n'
            f'\t)')

def via(x, y, net, size=0.6, drill=0.3):
    return (f'\t(via\n'
            f'\t\t(at {x} {y})\n'
            f'\t\t(size {size})\n'
            f'\t\t(drill {drill})\n'
            f'\t\t(layers "F.Cu" "B.Cu")\n'
            f'\t\t(net "{net}")\n'
            f'\t\t(uuid "{U()}")\n'
            f'\t)')

W_P  = 0.5   # 電源トレース
W_S  = 0.2   # 信号トレース

R = []

# =============================================================================
# STEP 1: VBAT (J1→C13, J1→SW1→U4)
# J1.pad1(2.875,32.65), C13.pad1(3.025,33.3), SW1.pad1(2.0,26.95), U4.pad5(23.975,24.405)
# VBAT y=27.2使用: C9.pad1[VBAT_SW](10.55,28.5)のtop=27.775とのクリア確保
# =============================================================================
R += [seg(2.875, 32.65, 2.875, 33.3,  W_P, 'F.Cu', 'VBAT'),
      seg(2.875, 33.3,  3.025, 33.3,  W_P, 'F.Cu', 'VBAT')]
R += [seg(2.875, 32.65, 1.2,   32.65, W_P, 'F.Cu', 'VBAT'),  # x=1.2: VBAT_SW via(2.0,28.85) left=1.7 gap=0.25mm ✓
      seg(1.2,   32.65, 1.2,   26.95, W_P, 'F.Cu', 'VBAT'),
      seg(1.2,   26.95, 2.0,   26.95, W_P, 'F.Cu', 'VBAT')]
# y=27.2でLED1.pad2[LED_ANODE](16.485,27.5)も避けてjog
R += [seg(2.0,  26.95, 2.0,  27.2,  W_P, 'F.Cu', 'VBAT'),
      seg(2.0,  27.2,  14.5, 27.2,  W_P, 'F.Cu', 'VBAT'),
      seg(14.5, 27.2,  14.5, 28.5,  W_P, 'F.Cu', 'VBAT'),
      seg(14.5, 28.5,  17.5, 28.5,  W_P, 'F.Cu', 'VBAT'),
      seg(17.5, 28.5,  17.5, 27.2,  W_P, 'F.Cu', 'VBAT'),
      seg(17.5, 27.2,  25.0, 27.2,  W_P, 'F.Cu', 'VBAT'),
      seg(25.0, 27.2,  25.0, 24.405,W_P, 'F.Cu', 'VBAT'),
      seg(25.0, 24.405,23.975,24.405,W_P,'F.Cu', 'VBAT')]

# =============================================================================
# STEP 2: LED_ANODE  R4.pad1(15.49,26.3) → LED1.pad2(16.485,27.5)
# 斜め1本: LED1.pad1[GND](15.52,27.5)を避ける（垂直→水平ルートはpad1を通過する）
# 垂直距離=pad1からのperp距離=0.742mm, gap=0.342mm ✓
# =============================================================================
R += [seg(15.49, 26.3,  16.485,27.5,  W_S, 'F.Cu', 'LED_ANODE')]

# =============================================================================
# STEP 3: VBAT_SW
# U1.pad34,35 → B.Cu右トランク(x=27.5) → 既存バス(26.363,21.05)
# C11,C12 → B.Cu左(x=1.55) → SW1.pad2 → C9
# =============================================================================
R += [seg(18.3, 1.26,  19.4, 1.26,  W_P, 'F.Cu', 'VBAT_SW')]  # pad35-pad34
R += [via(19.4, 1.26, 'VBAT_SW')]
R += [seg(19.4, 1.26,  27.5, 1.26,  W_P, 'B.Cu', 'VBAT_SW'),
      seg(27.5, 1.26,  27.5, 21.05, W_P, 'B.Cu', 'VBAT_SW')]
R += [via(27.5, 21.05, 'VBAT_SW')]
R += [seg(27.5, 21.05, 26.363,21.05,W_P, 'F.Cu', 'VBAT_SW')]
R += [via(1.55, 7.0, 'VBAT_SW'),
      seg(1.55, 7.0,  1.55, 13.0, W_P, 'B.Cu', 'VBAT_SW')]
R += [via(1.55, 13.0, 'VBAT_SW'),
      seg(1.55, 13.0, 1.55, 28.85,W_P, 'B.Cu', 'VBAT_SW'),
      seg(1.55, 28.85,2.0,  28.85,W_P, 'B.Cu', 'VBAT_SW')]
R += [via(2.0, 28.85, 'VBAT_SW'),
      seg(2.0, 28.85, 2.0,  28.5, W_P, 'F.Cu', 'VBAT_SW'),
      seg(2.0, 28.5,  10.55,28.5, W_P, 'F.Cu', 'VBAT_SW')]

# =============================================================================
# STEP 4: LTE_ANT  U1.pad32(23.75,5.05) → ANT1.pad1(26.475,4.5)
# W_S使用: W_RF=1.4mmだとU1.pad33[GND](y=3.95,bottom=4.40)と
#          ANT1.pad2[GND](x=26.9-29.1,y=5.45-6.50)に接触するため
# =============================================================================
R += [seg(23.75, 5.05,  26.475,5.05, W_S, 'F.Cu', 'LTE_ANT'),
      seg(26.475,5.05,  26.475,4.5,  W_S, 'F.Cu', 'LTE_ANT')]

# =============================================================================
# STEP 5: GNSS_ANT  U1.pad68(19.40,5.05) → ANT2.pad1(26.475,13.5)
# B.Cu下降をy=12.5で止める: U1.pad24(no-net,y=13.85,top=13.40)との
# クリアランス確保 (trace bottom=12.6, pad top=13.4, gap=0.8mm ✓)
# F.Cu y=12.5→x=26.475, 上昇→y=13.5(ANT2.pad1中心)
# =============================================================================
R += [seg(19.4, 5.05,  20.5, 5.05,  W_S, 'F.Cu', 'GNSS_ANT')]
R += [via(20.5, 5.05, 'GNSS_ANT')]
R += [seg(20.5, 5.05,  20.5, 12.0,  W_S, 'B.Cu', 'GNSS_ANT')]
R += [via(20.5, 12.0, 'GNSS_ANT')]
R += [seg(20.5, 12.0,  26.475,12.0, W_S, 'F.Cu', 'GNSS_ANT'),
      seg(26.475,12.0,  26.475,13.5, W_S, 'F.Cu', 'GNSS_ANT')]

# =============================================================================
# STEP 6: SIM_PWRKEY  U1.pad39(13.90,1.26) → U2.pad7(6.05,24.75)+pad8(6.05,25.25)
# PWRKEY via(13.9,1.26)はCLK via(13.9,18.74)と同x: F.Cu→B.Cu直接
# +3.3V via(7.75,19.6)クリア: x=5.5, gap=5.5-0.10-(7.75-0.30)=7.45-5.60=1.85mm ✓
# =============================================================================
R += [via(13.9, 1.26, 'SIM_PWRKEY'),
      seg(13.9, 1.26,  5.5, 1.26,  W_S, 'B.Cu', 'SIM_PWRKEY'),
      seg(5.5,  1.26,  5.5, 25.25, W_S, 'B.Cu', 'SIM_PWRKEY')]
R += [via(5.5, 25.25, 'SIM_PWRKEY'),
      seg(5.5, 25.25, 6.05,25.25, W_S, 'F.Cu', 'SIM_PWRKEY'),
      seg(6.05,25.25, 6.05,24.75, W_S, 'F.Cu', 'SIM_PWRKEY')]

# =============================================================================
# STEP 7: SIM_STATUS  U1.pad42(10.60,1.26) → U2.pad4(6.05,23.25)
# B.Cu経由: x=0.5はANT3.pad1[WIFI_ANT](1.0,19.0)と衝突するため回避
#           x=4.7 B.Cu縦: +3.3V F.Cu bus(x=5.3-9.6, y=19.6-20.4)も回避
# via(4.7,1.26): PWRKEY B.Cu seg(5.5,1.26)左端right=5.0 gap=5.4-5.0=0.4mm ✓
# B.Cu x=4.7 縦: PWRKEY B.Cu(x=5.5) gap=5.4-4.8=0.6mm ✓
#                RESETN B.Cu(x=3.0) gap=1.5mm ✓
#                +3.3V B.Cu全て x≥6.5 gap≥1.6mm ✓
# via(4.7,23.25): RESETN B.Cu seg端(3.0,23.75) distance=1.77mm gap=1.17mm ✓
# F.Cu y=23.25: +3.3V via(6.05,22.5) bottom=22.8 top=23.15 gap=0.35mm ✓
# =============================================================================
# via(4.7,22.6): C2.pad2[GND](4.4-4.96, 23.19-23.81)上端からgap=0.29mm ✓（旧via(4.7,23.25)はC2.pad2と重複→S1/S2）
# F.Cu x=5.3縦: U2.pad3[+3.3V](5.65-6.45, 22.625-22.875)左端gap=0.25mm / C2.pad2右端gap=0.24mm ✓
R += [seg(10.6,  1.26,  4.7,  1.26,  W_S, 'F.Cu', 'SIM_STATUS')]
R += [via(4.7, 1.26, 'SIM_STATUS')]
R += [seg(4.7,  1.26,  4.7, 22.6,   W_S, 'B.Cu', 'SIM_STATUS')]
R += [via(4.7, 22.6, 'SIM_STATUS')]
R += [seg(4.7,  22.6,  5.3,  22.6,  W_S, 'F.Cu', 'SIM_STATUS'),
      seg(5.3,  22.6,  5.3,  23.25, W_S, 'F.Cu', 'SIM_STATUS'),
      seg(5.3,  23.25, 6.05, 23.25, W_S, 'F.Cu', 'SIM_STATUS')]

# =============================================================================
# STEP 8: SIM_RESETN  U1.pad28(23.75,9.45) → U2.pad5(6.05,23.75)+pad6(6.05,24.25)
# viaをx=26.5へ: SIM_RST B.Cu(x=24.0)との間隔0.3mm→旧via(24.4)では0mmで接触
#   SIM_DATA B.Cu(x=26.0)とのgap: 26.5-0.3-26.0-0.1=0.1mm→改善必要→x=26.8使用
#   (SIM_CLK B.Cu x=25.5とのgap: 26.8-0.3-25.5-0.1=0.9mm ✓)
#   (VBAT_SW B.Cu x=27.5とのgap: 27.5-0.1-26.8-0.3=0.3mm ✓)
# B.Cu x=26.8→y=4.0→x=23.5→y=32.5→x=3.0→y=23.75→via
# via(3.0,23.75): C2.pad2[GND](4.68,23.5)からの距離1.70mm gap=1.12mm ✓
# F.Cu迂回: C2.pad2右端≈4.96、y=24.15で下回り
# =============================================================================
# 北回り再設計(2026-06-10): 旧ルート(y=4.0横断・y=32.5横断)はCLK/DATA/RST/TXDと計4交差(C1-C4)
# B.Cu x=26.7北上: DATA B.Cu(x=26.0) gap=0.5mm / DATA横y=2.0は x≤26.0でy=2.4手前まで ✓
# F.CuホップでVBAT_SW B.Cu横(y=1.26, x=19.4-27.5)を飛び越え、F.Cu y=0.5で西へ横断
# F.Cu y=0.5: U1上辺パッド列(y=1.26, 高さ0.8→上端0.86)からgap=0.26mm / 基板上端から0.4mm(既存TXD y=34.7=0.2mmの前例あり)
# via(3.0,0.9): U1.pad42(10.6,1.26)から遠方 / STATUS via(4.7,1.26)からdist=1.74mm ✓
# B.Cu x=3.0南下: STATUS B.Cu(x=4.7) gap=1.5mm / VBAT_SW B.Cu(x=1.55,w0.5) gap=1.0mm / GND via(4,18.5) gap=0.6mm ✓
# via(26.7,9.45): VBAT_SW B.Cu(x=27.5,w0.5)からgap=0.25mm（旧26.8では0.15mm） / DATA B.Cu(x=26.0)からgap=0.3mm
R += [seg(23.75,9.45,  26.7, 9.45, W_S, 'F.Cu', 'SIM_RESETN')]
R += [via(26.7, 9.45, 'SIM_RESETN')]
R += [seg(26.7, 9.45,  26.7, 2.4,  W_S, 'B.Cu', 'SIM_RESETN')]
R += [via(26.7, 2.4, 'SIM_RESETN')]
R += [seg(26.7, 2.4,   26.7, 0.5,  W_S, 'F.Cu', 'SIM_RESETN'),
      seg(26.7, 0.5,   3.0,  0.5,  W_S, 'F.Cu', 'SIM_RESETN'),
      seg(3.0,  0.5,   3.0,  0.9,  W_S, 'F.Cu', 'SIM_RESETN')]
R += [via(3.0, 0.9, 'SIM_RESETN')]
# 西側末端再設計(2026-06-10): 旧via(3.0,23.75)は+3.3V F.Cu縦(x=3.5,y21.5-26.5)とgap=0.05mm、
# 旧F.Cu尾部y=24.15は同+3.3V縦と物理交差（DRC未検出だが実ショート）→ y=24.8で+3.3V縦の東へ回り込む
# via(4.5,24.8): C2.pad2[GND]下端23.81からgap=0.69mm / U2.pad7左端5.65からgap=0.85mm / PWRKEY via(5.5,25.25)からgap=0.5mm
# F.Cu y=24.25水平はU2.pad6中心線に直入。U2.pad7上端24.625とgap=0.275mm / C2.pad2とgap=0.34mm
# via(4.5,24.5): C2.pad2[GND]下端23.81とgap=0.39mm / C3.pad2[GND](4.68,25.5)上端25.19とgap=0.39mm
R += [seg(3.0,  0.9,   3.0,  24.5, W_S, 'B.Cu', 'SIM_RESETN'),
      seg(3.0,  24.5,  4.5,  24.5, W_S, 'B.Cu', 'SIM_RESETN')]
R += [via(4.5, 24.5, 'SIM_RESETN')]
R += [seg(4.5,  24.5,  4.5,  24.25,W_S, 'F.Cu', 'SIM_RESETN'),
      seg(4.5,  24.25, 6.05, 24.25,W_S, 'F.Cu', 'SIM_RESETN'),
      seg(6.05, 24.25, 6.05, 23.75,W_S, 'F.Cu', 'SIM_RESETN')]

# =============================================================================
# STEP 9: SIM_TXD  U1.pad22(23.75,16.05) → U2.pad26(9.75)+pad27(9.25,21.05)
# via(28.5,16.05): VBAT_SW B.Cu(x=27.5) gap=0.6mm ✓ / ANT2.pad2[GND](y=14.45-15.5) gap=0.25mm ✓
# B.Cu x=28.5縦: VBAT_SW gap=0.6mm ✓ / PCB右端(x=30) gap=1.4mm ✓
# B.Cu y=34.7水平: CC2 B.Cu(y=34.2) top=34.3 gap=0.3mm ✓ / PCB下端(y=35) gap=0.2mm ✓
# B.Cu x=10.1縦: ACCEL via(10.85,25.95) left=10.55 gap=0.35mm ✓
#               ACCEL B.Cu segs gap=0.4mm+ ✓ / +3.3V B.Cu(x=7.75) gap=2.15mm ✓
# via(10.1,21.0): +3.3V via(7.75,19.6) distance=2.86mm ✓
# F.Cu y=21.0: +3.3V F.Cu(y=20.4) gap=0.4mm ✓
# =============================================================================
R += [seg(23.75,16.05, 28.5, 16.05, W_S,'F.Cu','SIM_TXD')]
R += [via(28.5, 16.05, 'SIM_TXD')]
R += [seg(28.5, 16.05, 28.5, 34.7, W_S,'B.Cu','SIM_TXD'),
      seg(28.5, 34.7,  10.1, 34.7, W_S,'B.Cu','SIM_TXD'),
      seg(10.1, 34.7,  10.1, 21.0, W_S,'B.Cu','SIM_TXD')]
R += [via(10.1, 21.0, 'SIM_TXD')]
R += [seg(10.1, 21.0,  9.75, 21.0, W_S,'F.Cu','SIM_TXD'),
      seg(9.75, 21.0,  9.75, 21.05,W_S,'F.Cu','SIM_TXD'),
      seg(9.75, 21.05, 9.25, 21.05,W_S,'F.Cu','SIM_TXD')]

# =============================================================================
# STEP 10: SIM_RXD  U1.pad23(23.75,14.95) → U2.pad28(8.75,21.05)
# F.Cu東へ(x=25.3): pad23右端24.15→25.3, pad22/24 gap≥0.45mm ✓
#                   +3.3V F.Cu(y=19.6)はy=14.95から遠く無干渉 ✓
# via(25.3,14.95): SIM_CLK B.Cu(x=24.7) gap=0.2mm ✓ / SIM_DATA B.Cu(x=26.0) gap=0.3mm ✓
# B.Cu x=25.3南(y=14.95→33.0): CLK gap=0.4mm ✓ / DATA gap=0.5mm ✓ / RESETN x=23.5 gap=1.6mm ✓
# B.Cu y=33.0西(x=25.3→15.1): RESETN y=32.5 gap=0.3mm ✓ / CC2 y=34.2 gap=1.0mm ✓
# B.Cu x=15.1北(y=33.0→21.5): TXD B.Cu(x=10.1) gap=4.65mm ✓ / ACCEL gap=0.54mm ✓
# B.Cu y=21.5西(x=15.1→12.4): +3.3V B.Cu(x=11.8) left=12.1 gap=0.2mm ✓
# via(12.4,21.5): +3.3V B.Cu(x=11.8) gap=0.2mm ✓
# F.Cu y=21.5西(x=12.4→8.75): +3.3V via(11.8,19.6) distance≥1.5mm ✓ / WIFI gap≥2.7mm ✓
# F.Cu x=8.75北(y=21.5→21.05→pad28): TXD seg(9.25,21.05) gap=0.3mm ✓
# =============================================================================
# 南側横断をF.Cu y=33.0に変更(2026-06-10): 旧B.Cu横断はCC2(x=20)/VUSB(y=30.5)/LED_ANODE via/+3.3V F.Cuと衝突(C5-C7,S5-S7)
# F.Cu y=33.0(x=25.3→8.7): SIM1.pad4下端32.59からgap=0.31mm / J2パッド群と非干渉(スキャン済み y=32.9-33.2クリア)
# B.Cu x=8.7北上(33.0→21.05): TXD B.Cu(x=10.1) gap=1.2mm / +3.3V B.Cu(x=7.75) gap=0.75mm / ACCEL(x=10.85) gap=1.95mm ✓
# via(8.7,21.05): TXD via(10.1,21.0) dist=1.4mm / U2.pad30[+3.3V](7.625-7.875)からgap=0.53mm ✓
R += [seg(23.75,14.95, 25.3, 14.95, W_S,'F.Cu','SIM_RXD')]
R += [via(25.3, 14.95, 'SIM_RXD')]
R += [seg(25.3, 14.95, 25.3, 33.0, W_S,'B.Cu','SIM_RXD')]
R += [via(25.3, 33.0, 'SIM_RXD')]
R += [seg(25.3, 33.0,  8.7,  33.0, W_S,'F.Cu','SIM_RXD')]
R += [via(8.7, 33.0, 'SIM_RXD')]
R += [seg(8.7,  33.0,  8.7,  21.05,W_S,'B.Cu','SIM_RXD')]
R += [via(8.7, 21.05, 'SIM_RXD')]
R += [seg(8.7,  21.05, 8.75, 21.05,W_S,'F.Cu','SIM_RXD')]

# =============================================================================
# STEP 11: SIM_DATA  U1.pad15(12.80,18.74) → SIM1.pad2(23.6,29.3)
# B.Cu上行コリドーy=2.0, 右降下x=26.0
# (旧x=26.5: +3.3V B.Cu x=26.55との間隔-0.15mm → x=26.0に変更)
# F.Cu水平y=28.0: SIM_CLK via(25.5,28.8)との間隔0.4mm ✓
#                  SIM1.pad3[CLK](x=25.59-26.69,y=28.55-30.05)との間隔0.45mm ✓
# =============================================================================
R += [via(12.8, 18.74, 'SIM_DATA')]
R += [seg(12.8, 18.74, 12.8, 2.0,  W_S, 'B.Cu', 'SIM_DATA'),
      seg(12.8, 2.0,   26.0, 2.0,  W_S, 'B.Cu', 'SIM_DATA'),
      seg(26.0, 2.0,   26.0, 28.0, W_S, 'B.Cu', 'SIM_DATA'),
      seg(26.0, 28.0,  26.4, 28.0, W_S, 'B.Cu', 'SIM_DATA')]
R += [via(26.4, 28.0, 'SIM_DATA')]
R += [seg(26.4, 28.0,  23.6, 28.0, W_S, 'F.Cu', 'SIM_DATA'),
      seg(23.6, 28.0,  23.6, 29.3, W_S, 'F.Cu', 'SIM_DATA')]

# =============================================================================
# STEP 12: SIM_CLK  U1.pad16(13.90,18.74) → SIM1.pad3(26.14,29.3)
# =============================================================================
R += [via(13.9, 18.74, 'SIM_CLK')]
R += [seg(13.9, 18.74, 13.9, 2.5,  W_S, 'B.Cu', 'SIM_CLK'),
      seg(13.9, 2.5,   24.7, 2.5,  W_S, 'B.Cu', 'SIM_CLK'),
      seg(24.7, 2.5,   24.7, 28.8, W_S, 'B.Cu', 'SIM_CLK')]
R += [via(24.7, 28.8, 'SIM_CLK')]
R += [seg(24.7, 28.8,  24.7, 29.3, W_S, 'F.Cu', 'SIM_CLK'),
      seg(24.7, 29.3,  26.14,29.3, W_S, 'F.Cu', 'SIM_CLK')]

# =============================================================================
# STEP 13: SIM_RST  U1.pad17(15.00,18.74) → SIM1.pad4(21.06,31.84)
# =============================================================================
R += [via(15.0, 18.74, 'SIM_RST')]
R += [seg(15.0, 18.74, 15.0, 3.0,  W_S, 'B.Cu', 'SIM_RST'),
      seg(15.0, 3.0,   24.0, 3.0,  W_S, 'B.Cu', 'SIM_RST'),
      seg(24.0, 3.0,   24.0, 31.3, W_S, 'B.Cu', 'SIM_RST')]
R += [via(24.0, 31.3, 'SIM_RST')]
R += [seg(24.0, 31.3,  21.06,31.3, W_S, 'F.Cu', 'SIM_RST'),
      seg(21.06,31.3,  21.06,31.84,W_S, 'F.Cu', 'SIM_RST')]

# =============================================================================
# STEP 14: SIM_VDD  U1.pad18(16.10,18.74) → SIM1.pad1(21.06,29.3)
# =============================================================================
R += [via(16.1, 18.74, 'SIM_VDD')]
R += [seg(16.1, 18.74, 16.1, 3.5,  W_S, 'B.Cu', 'SIM_VDD'),
      seg(16.1, 3.5,   22.0, 3.5,  W_S, 'B.Cu', 'SIM_VDD'),
      seg(22.0, 3.5,   22.0, 28.8, W_S, 'B.Cu', 'SIM_VDD')]
R += [via(22.0, 28.8, 'SIM_VDD')]
R += [seg(22.0, 28.8,  22.0, 29.3, W_S, 'F.Cu', 'SIM_VDD'),
      seg(22.0, 29.3,  21.06,29.3, W_S, 'F.Cu', 'SIM_VDD')]

# =============================================================================
# STEP 15: CHRG  U4.pad7(23.975,21.865) → R4.pad2(16.51,26.3)
# =============================================================================
R += [seg(23.975,21.865,22.0, 21.865,W_S,'F.Cu','CHRG'),
      seg(22.0, 21.865,22.0, 26.3,  W_S, 'F.Cu', 'CHRG'),
      seg(22.0, 26.3,  16.51,26.3,  W_S, 'F.Cu', 'CHRG')]

# =============================================================================
# STEP 16: ACCEL_INT1  U3.pad7(14.2625,25.25) → U2.pad16(10.25,25.95)
# B.Cu経由: I2C_SCL F.Cu(y=24.75近傍)との交差回避、U2 GND thermal pad(x=6.65-10.35,y=21.65-25.35)も回避
# via(14.2625,25.25)→B.Cu南(y=29.5)→B.Cu西(x=10.25)→B.Cu北(y=25.95)→via
# y=29.5水平: SIM_CLK B.Cu(x=13.9,y=2.5-28.8)の南 gap=0.6mm ✓
#            SIM_DATA B.Cu(x=26.0,y=2.0-28.0)の南 gap=1.3mm ✓
# x=10.25縦: SIM_TXD B.Cu(x=9.5) gap=0.55mm ✓
#            U2 GND thermal pad(x=6.65-10.35,y=21.65-25.35): x=10.25は右端10.35の0.1mm内側
#            → 実際のB.Cu to thermal-pad gap: 10.35-0.1-10.25-0.1=−0.1mm(tight)
#            → x=10.6使用: gap=10.35-0.1-10.6+0.1=−0.35mm もNG
#            → B.Cu at x=10.5: 10.5-0.1=10.4 > 10.35, gap=10.4-10.35=0.05mm(NG)
#            → x=10.7: gap=10.7-0.1-10.35-0.1=0.15mm(NG)
#            → x=10.85: gap=10.85-0.1-10.35-0.1=0.3mm ✓ → B.Cuをx=10.85で下降
#              その後F.Cuで(10.85,25.95)→(10.25,25.95)
# =============================================================================
R += [via(14.2625,25.25,'ACCEL_INT1')]
R += [seg(14.2625,25.25,14.2625,29.5,W_S,'B.Cu','ACCEL_INT1'),
      seg(14.2625,29.5, 10.85, 29.5, W_S,'B.Cu','ACCEL_INT1'),
      seg(10.85, 29.5,  10.85, 25.95,W_S,'B.Cu','ACCEL_INT1')]
R += [via(10.85,25.95,'ACCEL_INT1')]
R += [seg(10.85, 25.95, 10.25, 25.95,W_S,'F.Cu','ACCEL_INT1')]

# =============================================================================
# PCBファイルへの書き込み
# =============================================================================
with open(PCB) as f:
    content = f.read()

import os
if not os.path.exists(BAK):
    shutil.copy2(PCB, BAK)
    print(f"バックアップ: {BAK}")

# dangling VBAT_SW segment (24.35,8.2)→(25.02,8) を削除
def remove_segment(content, x1, y1, x2, y2):
    pattern = re.compile(
        r'\t\(segment\n'
        r'\t\t\(start ' + re.escape(str(x1)) + r' ' + re.escape(str(y1)) + r'\)\n'
        r'\t\t\(end ' + re.escape(str(x2)) + r' ' + re.escape(str(y2)) + r'\)\n'
        r'.*?\n\t\)\n',
        re.DOTALL
    )
    new_content, count = pattern.subn('', content)
    if count > 0:
        print(f"削除: segment ({x1},{y1})→({x2},{y2}) [{count}件]")
    else:
        # インライン形式も試みる
        pattern2 = re.compile(
            r'\t\(segment \(start ' + re.escape(str(x1)) + r' ' + re.escape(str(y1)) + r'\)'
            r' \(end ' + re.escape(str(x2)) + r' ' + re.escape(str(y2)) + r'\)'
            r'[^\n]+\n'
        )
        new_content, count = pattern2.subn('', content)
        if count > 0:
            print(f"削除(inline): segment ({x1},{y1})→({x2},{y2}) [{count}件]")
        else:
            print(f"警告: segment ({x1},{y1})→({x2},{y2}) が見つからない（既に削除済みか）")
    return new_content

def remove_via(content, x, y):
    pattern = re.compile(
        r'\t\(via\n'
        r'\t\t\(at ' + re.escape(str(x)) + r' ' + re.escape(str(y)) + r'\)\n'
        r'.*?\n\t\)\n',
        re.DOTALL
    )
    new_content, count = pattern.subn('', content)
    if count > 0:
        print(f"削除: via ({x},{y}) [{count}件]")
    else:
        print(f"警告: via ({x},{y}) が見つからない（既に削除済みか）")
    return new_content

content = remove_segment(content, 24.35, 8.2, 25.02, 8)

# CC2 via(11.25,34.2)がTXD B.Cu(y=34.7)とgap=0.1mm → via を(11.0,33.9)へ移設
# J2.B4(10.6-10.9)/B5(11.1-11.4)はともにCC2ネット、新via環(10.7-11.3, 33.6-34.2)は両パッドに重なり接続維持
# 新via vs J2.B1[GND](10.1-10.4): gap=0.3mm / vs J2.B6[no-net](11.6-): gap=0.3mm / vs TXD y=34.7: gap=0.4mm
content = remove_segment(content, 20, 34.2, 11.25, 34.2)
content = remove_via(content, 11.25, 34.2)
R += [seg(20.0, 34.2, 11.1, 34.2, 0.2, 'B.Cu', 'CC2'),
      seg(11.1, 34.2, 11.1, 33.9, 0.2, 'B.Cu', 'CC2')]
R += [via(11.1, 33.9, 'CC2')]

# 新しいセグメント/ビアをPCBに追加（最後の")"の手前に挿入）
new_routing = '\n'.join(R) + '\n'

insert_pos = content.rfind('\n)')
if insert_pos == -1:
    print("ERROR: PCBファイル末尾が見つからない")
    exit(1)

new_content = content[:insert_pos] + '\n' + new_routing + content[insert_pos:]

with open(PCB, 'w') as f:
    f.write(new_content)

print(f"✅ route_pcb_v11.py 完了: {len(R)}個の要素追加")
print(f"  内訳: VBAT×10, LED_ANODE×2, VBAT_SW×13, LTE_ANT×2, GNSS_ANT×5,")
print(f"        PWRKEY×5, STATUS×5, RESETN×12, TXD×7, RXD×7,")
print(f"        SIM_DATA×6, SIM_CLK×6, SIM_RST×5, SIM_VDD×6, CHRG×3, ACCEL_INT1×2")
print("次: kicad-cli DRC で shorts/crossings を確認")

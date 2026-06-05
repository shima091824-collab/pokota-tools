#!/usr/bin/env python3
"""
LTE-M Cat Tracker PCB: 自動配線スクリプト
RF経路 (LTE_ANT/GNSS_ANT/WIFI_ANT) を除く信号・電源を配線する。
"""
import sys
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages')
import pcbnew, shutil

PCB_FILE = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'
shutil.copy2(PCB_FILE, PCB_FILE + '.bak_preroute')

board = pcbnew.LoadBoard(PCB_FILE)

# ── ネット取得ヘルパー ────────────────────────────────────────────────────
def get_net(name):
    ni = board.FindNet(name)
    if ni is None:
        raise ValueError(f'Net not found: {name}')
    return ni

# ── パッド位置取得ヘルパー ────────────────────────────────────────────────
def get_pad(ref, pad_num):
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            for pad in fp.Pads():
                if pad.GetNumber() == str(pad_num):
                    pos = pad.GetPosition()
                    return pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
    raise ValueError(f'Pad not found: {ref}.{pad_num}')

# ── トレース追加ヘルパー ──────────────────────────────────────────────────
def add_track(x1, y1, x2, y2, net, layer=pcbnew.F_Cu, width_mm=0.25):
    if abs(x1 - x2) < 0.001 and abs(y1 - y2) < 0.001:
        return  # 同点はスキップ
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(width_mm))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)

def route_L(x1, y1, x2, y2, net, via_x=None, via_y=None,
            layer=pcbnew.F_Cu, width_mm=0.25):
    """L字ルーティング。via_x/via_yで折れ点を指定。省略時は x2,y1 経由。"""
    mx = via_x if via_x is not None else x2
    my = via_y if via_y is not None else y1
    add_track(x1, y1, mx, my, net, layer, width_mm)
    add_track(mx, my, x2, y2, net, layer, width_mm)

def add_via(x, y, net):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(0.6))    # via外径
    v.SetDrill(pcbnew.FromMM(0.3))    # 穴径
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net)
    board.Add(v)

# ===================================================================
print('■ ネット設定')
gnd   = get_net('GND')
v33   = get_net('+3.3V')
vbat  = get_net('VBAT')
vbsw  = get_net('VBAT_SW')
vusb  = get_net('VUSB')
chrg  = get_net('CHRG')
acc   = get_net('ACCEL_INT1')
pwrk  = get_net('SIM_PWRKEY')
rst_n = get_net('SIM_RESETN')
stat  = get_net('SIM_STATUS')
txd   = get_net('SIM_TXD')
rxd   = get_net('SIM_RXD')
sclk  = get_net('SIM_CLK')
sdat  = get_net('SIM_DATA')
srst  = get_net('SIM_RST')
svdd  = get_net('SIM_VDD')
scl   = get_net('I2C_SCL')
sda   = get_net('I2C_SDA')
print('  OK')

# ===================================================================
print('\n■ GND ビア (F.Cu ↔ B.Cu 接続)')
# 基板全体に均等に6本配置
gnd_via_positions = [
    (3.0, 5.0), (3.0, 17.0), (3.0, 30.0),
    (25.0, 5.0), (25.0, 20.0), (25.0, 30.0),
]
for vx, vy in gnd_via_positions:
    add_via(vx, vy, gnd)
    print(f'  via @ ({vx},{vy})')

# ===================================================================
print('\n■ VBAT (電源・0.5mm)')
# J1.1 (2.88,32.65) → SW1.1 (2.0,26.95)
route_L(2.88, 32.65, 2.00, 26.95, vbat, via_x=2.00, width_mm=0.5)
# SW1.1 (2.0,26.95) → U4.5 (23.98,24.41) — B.Cu で横断
route_L(2.00, 26.95, 23.98, 24.41, vbat, via_y=24.41,
        layer=pcbnew.B_Cu, width_mm=0.5)
print('  J1→SW1→U4 OK')

# ===================================================================
print('\n■ VUSB (電源・0.5mm)')
# J2.A4 (10.75,31.30) → U4.4 (19.02,24.41)
route_L(10.75, 31.30, 19.02, 24.41, vusb, via_y=24.41,
        layer=pcbnew.B_Cu, width_mm=0.5)
print('  J2→U4 OK')

# ===================================================================
print('\n■ VBAT_SW 配線 (電源・0.4mm)')
# SW1.2 (2.0,28.85) → C9.1 (10.55,28.50) — B.Cu
route_L(2.00, 28.85, 10.55, 28.50, vbsw,
        layer=pcbnew.B_Cu, width_mm=0.4)
# C9.1 (10.55,28.50) は B.Cu ゾーンに繋げる
# U5.1 (26.36,21.05) → U5.3 (26.36,22.95) : 同一コンポーネント・別パッド → 配線不要
# U1 VBAT_SW pads (上部右側) → C11.1 (1.55,7.0) / C12.1 (1.55,13.0)
# U1.1 (24.35,2.80) / U1.2 (24.35,4.60) / U1.3 (24.35,6.40) / U1.4 (24.35,8.20)
# C11 at (1.55,7.0), C12 at (1.55,13.0) — B.Cu 横断
route_L(24.35, 2.80, 1.55, 7.00, vbsw, via_y=7.00,
        layer=pcbnew.B_Cu, width_mm=0.4)
add_track(24.35, 2.80, 24.35, 8.20, vbsw, pcbnew.F_Cu, 0.4)  # U1 側縦配線
# C11 ↔ C12 (縦)
add_track(1.55, 7.00, 1.55, 13.00, vbsw, pcbnew.B_Cu, 0.4)
# U5 (VBAT_SW出力) → C10 (27.5,25.0) : U5 pad1→C10
route_L(26.36, 21.05, 27.55, 25.00, vbsw, via_x=27.55,
        layer=pcbnew.F_Cu, width_mm=0.4)
print('  主要VBAT_SW配線 OK')

# ===================================================================
print('\n■ +3.3V 配線 (0.3mm)')
# XC6220 (U5) pad5 (28.64,21.05) → 各消費部品へ
# U5 → U4.8 (23.98,20.59)  : TP4056 VCC
add_track(28.64, 21.05, 23.98, 21.05, v33, pcbnew.F_Cu, 0.3)
add_track(23.98, 21.05, 23.98, 20.59, v33, pcbnew.F_Cu, 0.3)
# U5 → R5.2 (13.51,19.80) — B.Cu
route_L(28.64, 21.05, 13.51, 19.80, v33, via_y=19.80,
        layer=pcbnew.B_Cu, width_mm=0.3)
# R5.2 → C5.1 (8.02,19.80)
add_track(13.51, 19.80, 8.02, 19.80, v33, pcbnew.B_Cu, 0.3)
# C5.1 → C6.1 (10.02,19.80) 逆向き接続は同ネット配線
add_track(8.02, 19.80, 10.02, 19.80, v33, pcbnew.B_Cu, 0.3)
# C5.1 → C4.1 (6.02,19.00) 縦→横
route_L(8.02, 19.80, 6.02, 19.00, v33, via_x=6.02,
        layer=pcbnew.B_Cu, width_mm=0.3)
# U5 → U2.31 (7.25,21.05) + U2.32 (6.75,21.05)
route_L(28.64, 21.05, 7.25, 21.05, v33, layer=pcbnew.B_Cu, width_mm=0.3)
add_track(7.25, 21.05, 6.75, 21.05, v33, pcbnew.B_Cu, 0.3)
# U2.2 (6.05,22.25) U2.3 (6.05,22.75) — F.Cu 縦
add_track(7.25, 21.05, 7.25, 22.25, v33, pcbnew.F_Cu, 0.3)
add_track(7.25, 22.25, 6.05, 22.25, v33, pcbnew.F_Cu, 0.3)
add_track(6.05, 22.25, 6.05, 22.75, v33, pcbnew.F_Cu, 0.3)
# U2.17 (10.95,25.25) + U2.18 (10.95,24.75) — F.Cu 縦
route_L(28.64, 21.05, 10.95, 24.75, v33, via_x=10.95,
        layer=pcbnew.B_Cu, width_mm=0.3)
add_track(10.95, 24.75, 10.95, 25.25, v33, pcbnew.F_Cu, 0.3)
# C7.1 (12.12,22.0) C8.1 (14.02,22.0)
route_L(28.64, 21.05, 12.12, 22.00, v33, via_y=22.00,
        layer=pcbnew.B_Cu, width_mm=0.3)
add_track(12.12, 22.00, 14.02, 22.00, v33, pcbnew.B_Cu, 0.3)
# R6.1 (12.49,21.0) R7.1 (15.99,21.5)
add_track(12.12, 22.00, 12.49, 21.00, v33, pcbnew.F_Cu, 0.3)
route_L(28.64, 21.05, 15.99, 21.50, v33, via_x=15.99,
        layer=pcbnew.B_Cu, width_mm=0.3)
# C1.1 (3.72,21.5) C2.1 (3.72,23.5) C3.1 (3.72,25.5)
route_L(7.25, 21.05, 3.72, 21.50, v33, layer=pcbnew.B_Cu, width_mm=0.3)
add_track(3.72, 21.50, 3.72, 23.50, v33, pcbnew.B_Cu, 0.3)
add_track(3.72, 23.50, 3.72, 25.50, v33, pcbnew.B_Cu, 0.3)
# U2.11 (7.75,25.95)
route_L(7.25, 21.05, 7.75, 25.95, v33, via_x=7.75,
        layer=pcbnew.B_Cu, width_mm=0.3)
# U3.12 (13.25,23.74) U3.2 (12.74,24.25) U3.4 (12.74,25.25) C10.1 (26.55,25.0)
route_L(15.99, 21.50, 13.25, 23.74, v33, via_x=13.25,
        layer=pcbnew.B_Cu, width_mm=0.3)
add_track(13.25, 23.74, 12.74, 24.25, v33, pcbnew.B_Cu, 0.3)
add_track(12.74, 24.25, 12.74, 25.25, v33, pcbnew.B_Cu, 0.3)
add_track(26.55, 25.00, 28.64, 25.00, v33, pcbnew.B_Cu, 0.3)
add_track(28.64, 25.00, 28.64, 21.05, v33, pcbnew.B_Cu, 0.3)
print('  +3.3V 主要配線 OK')

# ===================================================================
print('\n■ CHRG 配線 (0.2mm)')
# U4.7 (23.98,21.86) → R4.2 (16.51,26.30)
route_L(23.98, 21.86, 16.51, 26.30, chrg, via_y=26.30,
        layer=pcbnew.F_Cu, width_mm=0.2)
print('  U4→R4 OK')

# ===================================================================
print('\n■ ACCEL_INT1 (0.2mm)')
# U3.9 (14.26,24.25) → U2.16 (10.25,25.95)
route_L(14.26, 24.25, 10.25, 25.95, acc, via_y=25.95,
        layer=pcbnew.F_Cu, width_mm=0.2)
print('  U3→U2 OK')

# ===================================================================
print('\n■ SIM制御信号 U1→U2 (左側縦ルート, 0.2mm)')
# ルーティングチャンネル: x=4.8 (U1左パッド外側)
CH = 4.8   # 縦配線チャンネルX

# SIM_PWRKEY: U1.17 (5.65,17.20) → U2.8 (6.05,25.25)
add_track(5.65, 17.20, CH, 17.20, pwrk, pcbnew.F_Cu, 0.2)
add_track(CH, 17.20, CH, 25.25, pwrk, pcbnew.F_Cu, 0.2)
add_track(CH, 25.25, 6.05, 25.25, pwrk, pcbnew.F_Cu, 0.2)
print('  SIM_PWRKEY OK')

# SIM_STATUS: U1.18 (5.65,15.40) → U2.4 (6.05,23.25)
add_track(5.65, 15.40, CH-0.3, 15.40, stat, pcbnew.F_Cu, 0.2)
add_track(CH-0.3, 15.40, CH-0.3, 23.25, stat, pcbnew.F_Cu, 0.2)
add_track(CH-0.3, 23.25, 6.05, 23.25, stat, pcbnew.F_Cu, 0.2)
print('  SIM_STATUS OK')

# SIM_RESETN: U1.19 (5.65,13.60) → U2.6 (6.05,24.25)
add_track(5.65, 13.60, CH-0.6, 13.60, rst_n, pcbnew.F_Cu, 0.2)
add_track(CH-0.6, 13.60, CH-0.6, 24.25, rst_n, pcbnew.F_Cu, 0.2)
add_track(CH-0.6, 24.25, 6.05, 24.25, rst_n, pcbnew.F_Cu, 0.2)
print('  SIM_RESETN OK')

# ===================================================================
print('\n■ SIM UART U1→U2 (0.2mm)')
# SIM_TXD: U1.22 (5.65,8.20) → U2.27 (9.25,21.05)
# 縦降りしてからU2トップ部へ水平
add_track(5.65, 8.20, CH-0.9, 8.20, txd, pcbnew.F_Cu, 0.2)
add_track(CH-0.9, 8.20, CH-0.9, 20.55, txd, pcbnew.F_Cu, 0.2)
add_track(CH-0.9, 20.55, 9.25, 20.55, txd, pcbnew.F_Cu, 0.2)
add_track(9.25, 20.55, 9.25, 21.05, txd, pcbnew.F_Cu, 0.2)
print('  SIM_TXD OK')

# SIM_RXD: U1.23 (5.65,6.40) → U2.28 (8.75,21.05)
add_track(5.65, 6.40, CH-1.2, 6.40, rxd, pcbnew.F_Cu, 0.2)
add_track(CH-1.2, 6.40, CH-1.2, 20.55, rxd, pcbnew.F_Cu, 0.2)
add_track(CH-1.2, 20.55, 8.75, 20.55, rxd, pcbnew.F_Cu, 0.2)
add_track(8.75, 20.55, 8.75, 21.05, rxd, pcbnew.F_Cu, 0.2)
print('  SIM_RXD OK')

# ===================================================================
print('\n■ SIMカード信号 U1→SIM1 (右側ルート, 0.2mm)')
# SIM1は (23.6,31.3) 付近, U1上端パッドから右側を通って下へ
# SIM_CLK: U1.40 (15.0,4.60) → SIM1.3 (26.14,29.30)
route_L(15.00, 4.60, 26.14, 29.30, sclk,
        via_x=26.14, layer=pcbnew.B_Cu, width_mm=0.2)
print('  SIM_CLK OK')

# SIM_DATA: U1.39 (12.60,4.60) → SIM1.2 (23.60,29.30)
route_L(12.60, 4.60, 23.60, 29.30, sdat,
        via_x=23.60, layer=pcbnew.B_Cu, width_mm=0.2)
print('  SIM_DATA OK')

# SIM_RST: U1.41 (17.40,4.60) → SIM1.4 (21.06,31.84)
route_L(17.40, 4.60, 21.06, 31.84, srst,
        via_x=21.06, layer=pcbnew.B_Cu, width_mm=0.2)
print('  SIM_RST OK')

# SIM_VDD: U1.38 (10.20,4.60) → SIM1.1 (21.06,29.30)
route_L(10.20, 4.60, 21.06, 29.30, svdd,
        via_x=21.06, layer=pcbnew.B_Cu, width_mm=0.2)
print('  SIM_VDD OK')

# ===================================================================
print('\n■ I2C (0.2mm)')
# I2C_SCL: U2.15 (9.75,25.95) → U3.3 (12.74,24.75) → R7.2 (17.01,21.50)
add_track(9.75, 25.95, 9.75, 24.75, scl, pcbnew.F_Cu, 0.2)
add_track(9.75, 24.75, 12.74, 24.75, scl, pcbnew.F_Cu, 0.2)
add_track(12.74, 24.75, 12.74, 21.50, scl, pcbnew.F_Cu, 0.2)
add_track(12.74, 21.50, 17.01, 21.50, scl, pcbnew.F_Cu, 0.2)
print('  I2C_SCL OK')

# I2C_SDA: U2.14 (9.25,25.95) → U3.11 (13.75,23.74) → R6.2 (13.51,21.00)
add_track(9.25, 25.95, 9.25, 23.74, sda, pcbnew.F_Cu, 0.2)
add_track(9.25, 23.74, 13.75, 23.74, sda, pcbnew.F_Cu, 0.2)
add_track(13.75, 23.74, 13.51, 21.00, sda, pcbnew.F_Cu, 0.2)
print('  I2C_SDA OK')

# ===================================================================
print('\n■ ゾーン充填')
pcbnew.ZONE_FILLER(board).Fill(board.Zones())

print('\n■ 保存')
board.Save(PCB_FILE)
print(f'  保存完了: {PCB_FILE}')
print('\n⚠️  RF経路 (LTE_ANT/GNSS_ANT/WIFI_ANT) は KiCad GUI で手動配線してください')

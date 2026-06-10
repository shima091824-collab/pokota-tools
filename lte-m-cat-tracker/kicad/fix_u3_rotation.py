#!/usr/bin/env python3
"""U3 LIS2DW12 ネット割当バグ修正: 180°回転＋データシート準拠ネット再割当＋配線引き直し。
KiCad同梱Pythonで実行。verify_u3rot.py で全ルートcheck_route検証済み（2026-06-10）。
"""
import pcbnew

PCB = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'
board = pcbnew.LoadBoard(PCB)

def mm(p):
    return (round(p.x/1e6, 4), round(p.y/1e6, 4))

# --- U3 180°回転 + ネット再割当（SWIG破壊回避のため削除より先に実行） ---
u3 = next(fp for fp in board.Footprints() if fp.GetReference() == 'U3')
u3.SetOrientationDegrees(180)
print('U3を180°回転')

nets = board.GetNetsByName()
NEWNET = {'1':'I2C_SCL','2':'+3.3V','3':'GND','4':'I2C_SDA','5':None,'6':'GND',
          '7':'GND','8':'GND','9':'+3.3V','10':'+3.3V','11':None,'12':'ACCEL_INT1'}
for pad in u3.Pads():
    n = NEWNET[pad.GetNumber()]
    if n is None:
        pad.SetNetCode(0)
    else:
        pad.SetNet(nets[n])
    print(f'  pad{pad.GetNumber()}: {mm(pad.GetPosition())} → {n or "no-net"}')

RIP_SEGS = [
    ((11.8,23.0),(13.25,23.0)),((13.25,23.0),(13.25,23.738)),((13.25,23.738),(13.3,23.738)),
    ((13.3,23.738),(13.3,24.25)),((13.3,24.25),(12.7375,24.25)),
    ((13.2,26.5),(13.2,24.75)),((13.2,24.75),(12.738,24.75)),
    ((9.15,25.95),(9.15,29.55)),((9.15,29.55),(13.3,29.55)),((13.3,29.55),(13.3,29.15)),
    ((13.3,29.15),(16.8,29.15)),((16.8,29.15),(16.8,29.225)),((16.8,29.225),(14.875,29.225)),
    ((14.875,29.225),(14.875,23.4)),((14.875,23.4),(15.5,23.4)),((15.5,23.4),(13.65,23.4)),
    ((13.65,23.4),(13.75,23.4)),((13.75,23.4),(13.75,23.7375)),
    ((13.35,21.0),(13.35,21.6)),((13.35,21.6),(15.5,21.6)),((15.5,21.6),(15.5,23.4)),
    ((14.2625,24.25),(14.2625,25.25)),((14.2625,25.25),(14.2625,29.85)),
    ((14.2625,29.85),(10.85,29.85)),((10.85,29.85),(10.85,25.95)),
    ((14.2625,23.75),(14.95,23.75)),((13.75,25.2625),(13.75,25.9)),
]
RIP_VIAS = [(11.8,23.0),(9.15,29.55),(16.8,29.225),(15.5,23.4),(14.2625,25.25)]

removed = 0
for t in list(board.GetTracks()):
    cls = t.GetClass()
    if cls == 'PCB_TRACK':
        s, e = mm(t.GetStart()), mm(t.GetEnd())
        for a, b in RIP_SEGS:
            if (s == a and e == b) or (s == b and e == a):
                board.Remove(t); removed += 1
                break
    elif cls == 'PCB_VIA':
        p = mm(t.GetPosition())
        if p in [(round(x,4),round(y,4)) for x,y in RIP_VIAS]:
            board.Remove(t); removed += 1
print(f'削除: {removed}要素（期待: segs {len(RIP_SEGS)} + vias {len(RIP_VIAS)} = {len(RIP_SEGS)+len(RIP_VIAS)}）')

# --- 新規配線 ---
def seg(x1, y1, x2, y2, w, layer, net):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(int(x1*1e6), int(y1*1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(x2*1e6), int(y2*1e6)))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(pcbnew.F_Cu if layer == 'F.Cu' else pcbnew.B_Cu)
    t.SetNet(nets[net])
    board.Add(t)

def via(x, y, net):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(int(x*1e6), int(y*1e6)))
    v.SetWidth(pcbnew.FromMM(0.6))
    v.SetDrill(pcbnew.FromMM(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(nets[net])
    board.Add(v)

# SDAメイン（U2.14 via(9.15,25.95)既存→B北上→y=18.45横断→蛇行→via(15.2,20.5)→F東回り→pin4）
seg(9.15,25.95, 9.15,22.0, 0.15,'B.Cu','I2C_SDA')
seg(9.15,22.0, 9.3,22.0, 0.15,'B.Cu','I2C_SDA')
seg(9.3,22.0, 9.3,18.45, 0.15,'B.Cu','I2C_SDA')
seg(9.3,18.45, 12.28,18.45, 0.15,'B.Cu','I2C_SDA')
seg(12.28,18.45, 12.28,19.45, 0.15,'B.Cu','I2C_SDA')
seg(12.28,19.45, 15.35,19.45, 0.15,'B.Cu','I2C_SDA')
seg(13.35,19.45, 13.35,21.0, 0.15,'B.Cu','I2C_SDA')  # R6.2プルアップへのT分岐（既存via(13.35,21.0)へ）
seg(15.35,19.45, 15.35,20.1, 0.15,'B.Cu','I2C_SDA')
seg(15.35,20.1, 15.2,20.1, 0.15,'B.Cu','I2C_SDA')
seg(15.2,20.1, 15.2,20.5, 0.15,'B.Cu','I2C_SDA')
via(15.2,20.5,'I2C_SDA')
seg(15.2,20.5, 15.2,21.3, 0.15,'F.Cu','I2C_SDA')
seg(15.2,21.3, 15.5,21.3, 0.15,'F.Cu','I2C_SDA')
seg(15.5,21.3, 15.5,23.3, 0.15,'F.Cu','I2C_SDA')
seg(15.5,23.3, 14.2625,23.3, 0.15,'F.Cu','I2C_SDA')
seg(14.2625,23.3, 14.2625,23.75, 0.15,'F.Cu','I2C_SDA')
# SCL（既存東枝からpin1へ）
seg(15.0,25.2, 14.2625,25.2, 0.2,'F.Cu','I2C_SCL')
seg(14.2625,25.2, 14.2625,25.25, 0.2,'F.Cu','I2C_SCL')
# +3.3V（pin10は既存(12.738,25.5→25.25)が給電。pin10→pin9列＋pin9→pin2橋）
seg(12.7375,25.25, 12.7375,24.75, 0.2,'F.Cu','+3.3V')
seg(12.7375,24.75, 14.2625,24.75, 0.2,'F.Cu','+3.3V')
# GND（pin7は既存西スタブが接続。pin7→pin8列＋pin8→pin3橋＋pin7→pin6）
seg(12.7375,23.75, 12.7375,24.25, 0.2,'F.Cu','GND')
seg(12.7375,24.25, 14.2625,24.25, 0.2,'F.Cu','GND')
seg(12.7375,23.75, 13.25,23.7375, 0.15,'F.Cu','GND')
# ACCEL_INT1（既存via(10.85,25.95)→B南回り→via(13.75,25.95)→pin12）
seg(10.85,25.95, 10.85,27.0, 0.2,'B.Cu','ACCEL_INT1')
seg(10.85,27.0, 13.75,27.0, 0.2,'B.Cu','ACCEL_INT1')
seg(13.75,27.0, 13.75,25.95, 0.2,'B.Cu','ACCEL_INT1')
via(13.75,25.95,'ACCEL_INT1')
seg(13.75,25.95, 13.75,25.2625, 0.2,'F.Cu','ACCEL_INT1')
print('新規: seg×27, via×2 追加')

print('充填:', pcbnew.ZONE_FILLER(board).Fill(board.Zones()))
pcbnew.SaveBoard(PCB, board)
print('保存完了')

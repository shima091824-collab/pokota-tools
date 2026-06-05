import sys
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

PCB_PATH = "/Users/m2mac/gps-cat-tracker/lora-30x35-v3n.kicad_pcb"
board = pcbnew.LoadBoard(PCB_PATH)

def mm(x): return pcbnew.FromMM(x)

# 1. J1 信号パッド幅 1.2mm → 1.0mm
for fp in board.GetFootprints():
    if fp.GetReference() == "J1":
        for pad in fp.Pads():
            sx = pcbnew.ToMM(pad.GetSize().x)
            sy = pcbnew.ToMM(pad.GetSize().y)
            if abs(sx - 1.2) < 0.05:
                pad.SetSize(pcbnew.VECTOR2I(mm(1.0), pad.GetSize().y))
                print(f"J1 pad{pad.GetNumber()} 幅: {sx:.2f}→1.0mm")

# 2. 重複via(18.6,17.0)を1つ削除
vias_at_pos = []
for t in board.GetTracks():
    if t.GetClass() == "PCB_VIA":
        vx, vy = pcbnew.ToMM(t.GetX()), pcbnew.ToMM(t.GetY())
        if abs(vx-18.6)<0.05 and abs(vy-17.0)<0.05:
            vias_at_pos.append(t)
            print(f"via(18.6,17.0) 発見: net={t.GetNetname()}")

if len(vias_at_pos) > 1:
    board.Remove(vias_at_pos[-1])  # 後から追加した方を削除
    print(f"重複via削除: {len(vias_at_pos)}個→1個")

board.Save(PCB_PATH)
print("保存完了")

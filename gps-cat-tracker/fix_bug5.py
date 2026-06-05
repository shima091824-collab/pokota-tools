import sys
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

PCB_PATH = "/Users/m2mac/gps-cat-tracker/lora-30x35-v3n.kicad_pcb"
board = pcbnew.LoadBoard(PCB_PATH)

def mm(x): return pcbnew.FromMM(x)
def pt(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

F_Cu = board.GetLayerID("F.Cu")
B_Cu = board.GetLayerID("B.Cu")

removed = 0
# 削除対象を収集
to_remove = []
for t in board.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        sx, sy = pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)
        ex, ey = pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)
        layer = t.GetLayer()
        # 1. F.Cu (12.0,23.0)→(13.25,23.0)
        if layer == F_Cu:
            if (abs(sx-12.0)<0.05 and abs(sy-23.0)<0.05 and abs(ex-13.25)<0.05 and abs(ey-23.0)<0.05):
                to_remove.append(t); print(f"  削除予定: F.Cu ({sx:.2f},{sy:.2f})→({ex:.2f},{ey:.2f})")
            elif (abs(ex-12.0)<0.05 and abs(ey-23.0)<0.05 and abs(sx-13.25)<0.05 and abs(sy-23.0)<0.05):
                to_remove.append(t); print(f"  削除予定: F.Cu ({sx:.2f},{sy:.2f})→({ex:.2f},{ey:.2f}) [逆向き]")
        # 2. B.Cu (12.0,20.0)→(12.0,23.0)
        if layer == B_Cu:
            if (abs(sx-12.0)<0.05 and abs(sy-20.0)<0.05 and abs(ex-12.0)<0.05 and abs(ey-23.0)<0.05):
                to_remove.append(t); print(f"  削除予定: B.Cu ({sx:.2f},{sy:.2f})→({ex:.2f},{ey:.2f})")
            elif (abs(ex-12.0)<0.05 and abs(ey-20.0)<0.05 and abs(sx-12.0)<0.05 and abs(sy-23.0)<0.05):
                to_remove.append(t); print(f"  削除予定: B.Cu ({sx:.2f},{sy:.2f})→({ex:.2f},{ey:.2f}) [逆向き]")

    elif t.GetClass() == "PCB_VIA":
        vx, vy = pcbnew.ToMM(t.GetX()), pcbnew.ToMM(t.GetY())
        # 3. via at (12.0,23.0)
        if abs(vx-12.0)<0.05 and abs(vy-23.0)<0.05:
            to_remove.append(t); print(f"  削除予定: via ({vx:.2f},{vy:.2f})")

for item in to_remove:
    board.Remove(item)
    removed += 1
print(f"削除完了: {removed}件")

# 追加
# 4. B.Cu トレース (13.5,15.5)→(13.5,21.1) w=0.4mm
t = pcbnew.PCB_TRACK(board)
t.SetStart(pt(13.5, 15.5))
t.SetEnd(pt(13.5, 21.1))
t.SetWidth(mm(0.4))
t.SetLayer(B_Cu)
t.SetNet(board.FindNet("VCC"))
board.Add(t)
print("追加: B.Cu トレース (13.5,15.5)→(13.5,21.1) w=0.4mm VCC")

# 5. via at (13.5,21.1) size=0.8 drill=0.4
v = pcbnew.PCB_VIA(board)
v.SetPosition(pt(13.5, 21.1))
v.SetWidth(mm(0.8))
v.SetDrill(mm(0.4))
v.SetNet(board.FindNet("VCC"))
board.Add(v)
print("追加: via (13.5,21.1) size=0.8 drill=0.4 VCC")

board.Save(PCB_PATH)
print("保存完了: lora-30x35-v3n.kicad_pcb")

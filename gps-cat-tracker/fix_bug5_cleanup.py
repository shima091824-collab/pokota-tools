import sys
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

PCB_PATH = "/Users/m2mac/gps-cat-tracker/lora-30x35-v3n.kicad_pcb"
board = pcbnew.LoadBoard(PCB_PATH)

B_Cu = board.GetLayerID("B.Cu")

to_remove = []
for t in board.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        sx, sy = pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)
        ex, ey = pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)
        # B.Cu (12,15.5)→(12,23) net=""の孤立トレース削除
        if t.GetLayer() == B_Cu:
            if (abs(sx-12.0)<0.05 and abs(sy-15.5)<0.05 and abs(ex-12.0)<0.05 and abs(ey-23.0)<0.05):
                to_remove.append(t)
                print(f"削除: B.Cu ({sx:.1f},{sy:.1f})→({ex:.1f},{ey:.1f}) net='{t.GetNetname()}'")
            elif (abs(ex-12.0)<0.05 and abs(ey-15.5)<0.05 and abs(sx-12.0)<0.05 and abs(sy-23.0)<0.05):
                to_remove.append(t)
                print(f"削除: B.Cu ({sx:.1f},{sy:.1f})→({ex:.1f},{ey:.1f}) net='{t.GetNetname()}' [逆]")

for item in to_remove:
    board.Remove(item)

print(f"削除完了: {len(to_remove)}件")

# Fill All Zones
board.BuildConnectivity()
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
print("Fill All Zones 完了")

board.Save(PCB_PATH)
print("保存完了")

"""Move SIM_TXD via from (9.25,21.05) to (9.5,21.05) to clear SIM_RXD via (8.75,21.05).

New layout:
- B.Cu route: ... → (8.3,21.45)→(9.5,21.45)→(9.5,21.05) [via]
- F.Cu stub: (9.25,21.05)[U2.pad27] → (9.5,21.05)[via]
"""
import sys, uuid
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

PCB_PATH = "kicad/lte-m-cat-tracker.kicad_pcb"
board = pcbnew.LoadBoard(PCB_PATH)

OLD_VIA_X = pcbnew.FromMM(9.25)
OLD_VIA_Y = pcbnew.FromMM(21.05)
NEW_VIA_X = pcbnew.FromMM(9.5)
NEW_VIA_Y = pcbnew.FromMM(21.05)
NET_SIMTXD = board.FindNet("SIM_TXD").GetNetCode()

# 1. Move the via
via_moved = False
for track in board.GetTracks():
    if track.GetClass() == 'PCB_VIA':
        pos = track.GetPosition()
        if (abs(pos.x - OLD_VIA_X) < pcbnew.FromMM(0.01) and
            abs(pos.y - OLD_VIA_Y) < pcbnew.FromMM(0.01) and
            track.GetNetCode() == NET_SIMTXD):
            track.SetPosition(pcbnew.VECTOR2I(NEW_VIA_X, NEW_VIA_Y))
            via_moved = True
            print(f"Moved SIM_TXD via to (9.5, 21.05)")
            break

# 2. Update B.Cu segment (8.3,21.45)→(9.25,21.45) to (8.3,21.45)→(9.5,21.45)
# and (9.25,21.45)→(9.25,21.05) to (9.5,21.45)→(9.5,21.05)
F_CU = board.GetLayerID("F.Cu")
B_CU = board.GetLayerID("B.Cu")

segs_to_update = []
for track in board.GetTracks():
    if track.GetClass() != 'PCB_TRACK':
        continue
    s = track.GetStart()
    e = track.GetEnd()
    if track.GetNetCode() != NET_SIMTXD or track.GetLayer() != B_CU:
        continue
    sx, sy = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
    ex, ey = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
    # Segment going right to old via x position
    if abs(ex - 9.25) < 0.01 and abs(ey - 21.45) < 0.01:
        segs_to_update.append(('end_x', track, NEW_VIA_X))
        print(f"Updated B.Cu seg end from (9.25,21.45) to (9.5,21.45)")
    elif abs(sx - 9.25) < 0.01 and abs(sy - 21.45) < 0.01:
        segs_to_update.append(('start_x', track, NEW_VIA_X))
        print(f"Updated B.Cu seg start from (9.25,21.45) to (9.5,21.45)")
    # Segment going down from 21.45 to old via
    elif abs(sx - 9.25) < 0.01 and abs(sy - 21.45) < 0.01 and abs(ex - 9.25) < 0.01 and abs(ey - 21.05) < 0.01:
        segs_to_update.append(('both_x', track, NEW_VIA_X))
        print(f"Updated B.Cu vertical seg")

for op, track, new_x in segs_to_update:
    s = track.GetStart()
    e = track.GetEnd()
    if op == 'end_x':
        track.SetEnd(pcbnew.VECTOR2I(new_x, e.y))
    elif op == 'start_x':
        track.SetStart(pcbnew.VECTOR2I(new_x, s.y))
    elif op == 'both_x':
        track.SetStart(pcbnew.VECTOR2I(new_x, s.y))
        track.SetEnd(pcbnew.VECTOR2I(new_x, e.y))

# Fix the vertical B.Cu segment separately
for track in board.GetTracks():
    if track.GetClass() != 'PCB_TRACK':
        continue
    if track.GetNetCode() != NET_SIMTXD or track.GetLayer() != B_CU:
        continue
    s = track.GetStart()
    e = track.GetEnd()
    sx, sy = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
    ex, ey = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
    # The vertical going down to via
    if abs(sx - 9.25) < 0.01 and abs(sy - 21.45) < 0.01 and abs(ex - 9.25) < 0.01 and abs(ey - 21.05) < 0.01:
        track.SetStart(pcbnew.VECTOR2I(NEW_VIA_X, s.y))
        track.SetEnd(pcbnew.VECTOR2I(NEW_VIA_X, e.y))
        print("Fixed B.Cu vertical segment")

# 3. Add F.Cu stub: (9.25,21.05)→(9.5,21.05)
stub = pcbnew.PCB_TRACK(board)
stub.SetLayer(F_CU)
stub.SetStart(pcbnew.VECTOR2I(OLD_VIA_X, OLD_VIA_Y))
stub.SetEnd(pcbnew.VECTOR2I(NEW_VIA_X, NEW_VIA_Y))
stub.SetWidth(pcbnew.FromMM(0.2))
stub.SetNet(board.FindNet("SIM_TXD"))
board.Add(stub)
print("Added F.Cu stub (9.25,21.05)→(9.5,21.05)")

board.Save(PCB_PATH)
print("Saved")

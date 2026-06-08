"""Fix undersized vias using pcbnew API, then save."""
import sys
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')

import pcbnew

PCB_PATH = "kicad/lte-m-cat-tracker.kicad_pcb"
MIN_DRILL = pcbnew.FromMM(0.3)
MIN_PAD   = pcbnew.FromMM(0.6)  # drill + 2×0.15mm annular

board = pcbnew.LoadBoard(PCB_PATH)

fixed = 0
for track in board.GetTracks():
    if track.GetClass() == 'PCB_VIA':
        via = track
        drill = via.GetDrillValue()
        size  = via.GetWidth()
        if drill < MIN_DRILL:
            via.SetDrill(MIN_DRILL)
            if size < MIN_PAD:
                via.SetWidth(MIN_PAD)
            fixed += 1

print(f"Fixed {fixed} vias")

# Verify
drills = {}
for track in board.GetTracks():
    if track.GetClass() == 'PCB_VIA':
        d = round(pcbnew.ToMM(track.GetDrillValue()), 2)
        drills[d] = drills.get(d, 0) + 1
print("Drill sizes after fix:", drills)

board.Save(PCB_PATH)
print(f"Saved: {PCB_PATH}")

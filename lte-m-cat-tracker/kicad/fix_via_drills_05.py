"""Fix undersized via drills to 0.3mm drill / 0.5mm pad (JLCPCB minimum)."""
import sys
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

PCB_PATH = "kicad/lte-m-cat-tracker.kicad_pcb"
MIN_DRILL = pcbnew.FromMM(0.3)
MIN_PAD   = pcbnew.FromMM(0.5)

board = pcbnew.LoadBoard(PCB_PATH)

fixed = 0
for track in board.GetTracks():
    if track.GetClass() == 'PCB_VIA':
        via = track
        drill = via.GetDrillValue()
        if drill < MIN_DRILL:
            via.SetDrill(MIN_DRILL)
            # Set to exactly 0.5mm pad - only if it was undersized
            via.SetWidth(MIN_PAD)
            fixed += 1

print(f"Fixed {fixed} vias")

# Verify
drills = {}
sizes = {}
for track in board.GetTracks():
    if track.GetClass() == 'PCB_VIA':
        d = round(pcbnew.ToMM(track.GetDrillValue()), 2)
        s = round(pcbnew.ToMM(track.GetWidth()), 2)
        drills[d] = drills.get(d, 0) + 1
        sizes[s] = sizes.get(s, 0) + 1

print("Drill sizes:", drills)
print("Pad sizes:", sizes)

board.Save(PCB_PATH)
print(f"Saved: {PCB_PATH}")

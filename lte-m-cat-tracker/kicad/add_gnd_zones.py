#!/usr/bin/env python3
"""F.Cu/B.Cu両面にGNDベタゾーンを追加してZONE_FILLERで充填・保存する。
KiCad同梱Pythonで実行:
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 add_gnd_zones.py
"""
import pcbnew

PCB = '/Users/m2mac/lte-m-cat-tracker/kicad/lte-m-cat-tracker.kicad_pcb'

board = pcbnew.LoadBoard(PCB)
gnd = board.GetNetsByName()['GND']
print(f"GND net code: {gnd.GetNetCode()}")

bbox = board.GetBoardEdgesBoundingBox()
print(f"外形: ({bbox.GetLeft()/1e6},{bbox.GetTop()/1e6}) - ({bbox.GetRight()/1e6},{bbox.GetBottom()/1e6}) mm")

existing = board.Zones()
print(f"既存ゾーン数: {len(existing)}")

for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(gnd)
    pts = [
        pcbnew.VECTOR2I(bbox.GetLeft(), bbox.GetTop()),
        pcbnew.VECTOR2I(bbox.GetRight(), bbox.GetTop()),
        pcbnew.VECTOR2I(bbox.GetRight(), bbox.GetBottom()),
        pcbnew.VECTOR2I(bbox.GetLeft(), bbox.GetBottom()),
    ]
    chain = pcbnew.SHAPE_LINE_CHAIN()
    for p in pts:
        chain.Append(p)
    chain.SetClosed(True)
    zone.Outline().AddOutline(chain)
    zone.SetLocalClearance(pcbnew.FromMM(0.2))
    zone.SetMinThickness(pcbnew.FromMM(0.2))
    zone.SetThermalReliefGap(pcbnew.FromMM(0.3))
    zone.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.3))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetIsFilled(False)
    zone.SetZoneName(f"GND_{pcbnew.LayerName(layer)}")
    board.Add(zone)
    print(f"追加: GNDゾーン {pcbnew.LayerName(layer)}")

filler = pcbnew.ZONE_FILLER(board)
ok = filler.Fill(board.Zones())
print(f"充填: {'OK' if ok else 'FAILED'}")

pcbnew.SaveBoard(PCB, board)
print(f"保存完了: {PCB}")

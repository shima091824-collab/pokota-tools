"""
HEAD以降の全変更を適用:
1. C1移動 (27.5,2.5) → (27.5,0.8) + VCCトレース + GND via
2. J1パッド幅 1.27→1.0mm
3. TP1(UPDI)/TP2(VCC)/TP3(GND) テストパッド追加
4. R1 DNP設定
5. Bug5修正 (F.Cu/via/B.Cu削除 + B.Cu+via追加)
6. Fill All Zones
"""
import sys
sys.path.insert(0, '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.9/site-packages')
import pcbnew

PCB_PATH = "/Users/m2mac/gps-cat-tracker/lora-30x35-v3n.kicad_pcb"
board = pcbnew.LoadBoard(PCB_PATH)

def mm(x): return pcbnew.FromMM(x)
def pt(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

F_Cu = board.GetLayerID("F.Cu")
B_Cu = board.GetLayerID("B.Cu")

# ── 1. C1を(27.5,0.8)に移動 ──────────────────────────────────
for fp in board.GetFootprints():
    if fp.GetReference() == "C1":
        fp.SetX(mm(27.5))
        fp.SetY(mm(0.8))
        print("C1移動: (27.5, 0.8)")

# C1用 VCCトレース (26.6,0.8)→(26.6,2.92) F.Cu
t = pcbnew.PCB_TRACK(board)
t.SetStart(pt(26.6, 0.8)); t.SetEnd(pt(26.6, 2.92))
t.SetWidth(mm(0.4)); t.SetLayer(F_Cu)
t.SetNet(board.FindNet("VCC"))
board.Add(t)
print("追加: F.Cu VCCトレース (26.6,0.8)→(26.6,2.92)")

# C1用 GND via (28.4,1.5)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pt(28.4, 1.5)); v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4))
v.SetNet(board.FindNet("GND"))
board.Add(v)
print("追加: GND via (28.4,1.5)")

# ── 2. J1パッド幅 1.27→1.0mm ─────────────────────────────────
for fp in board.GetFootprints():
    if fp.GetReference() == "J1":
        for pad in fp.Pads():
            sx, sy = pcbnew.ToMM(pad.GetSize().x), pcbnew.ToMM(pad.GetSize().y)
            if abs(sx - 1.27) < 0.05:
                pad.SetSize(pcbnew.VECTOR2I(mm(1.0), mm(1.27)))
                print(f"J1 pad{pad.GetNumber()} 幅: 1.27→1.0mm")

# ── 3. テストパッド追加 (TP1/TP2/TP3) ────────────────────────
def add_test_pad(board, ref, x, y, net_name):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetX(mm(x)); fp.SetY(mm(y))
    pad = pcbnew.PAD(fp)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetSize(pcbnew.VECTOR2I(mm(1.5), mm(1.5)))
    pad.SetLayerSet(pad.SMDMask())
    pad.SetNumber("1")
    net = board.FindNet(net_name)
    if net:
        pad.SetNet(net)
    fp.Add(pad)
    board.Add(fp)
    print(f"追加: {ref} テストパッド ({x},{y}) net={net_name}")
    return fp

add_test_pad(board, "TP1", 16.0, 18.5, "UPDI")
add_test_pad(board, "TP2", 18.5, 18.5, "VCC")
add_test_pad(board, "TP3", 20.5, 18.5, "GND")

# TP1用トレース: U2.pad16(PC5/UPDI)→TP1 (16.0,20.75)→(16.0,18.5) F.Cu
t = pcbnew.PCB_TRACK(board)
t.SetStart(pt(16.0, 20.75)); t.SetEnd(pt(16.0, 18.5))
t.SetWidth(mm(0.2)); t.SetLayer(F_Cu)
net = board.FindNet("UPDI")
if net:
    t.SetNet(net)
board.Add(t)
print(f"追加: TP1トレース (16.0,20.75)→(16.0,18.5) net={'あり' if net else 'なし'}")

# TP2用トレース→via(18.6,17.0) F.Cu
t = pcbnew.PCB_TRACK(board)
t.SetStart(pt(18.5, 18.5)); t.SetEnd(pt(18.6, 17.0))
t.SetWidth(mm(0.2)); t.SetLayer(F_Cu)
t.SetNet(board.FindNet("VCC"))
board.Add(t)
print("追加: TP2トレース (18.5,18.5)→(18.6,17.0)")

# TP2用 via(18.6,17.0) B.Cu VCCトレースへ
v = pcbnew.PCB_VIA(board)
v.SetPosition(pt(18.6, 17.0)); v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4))
v.SetNet(board.FindNet("VCC"))
board.Add(v)
print("追加: TP2 via (18.6,17.0)")

# TP3用 via(20.5,17.0) → GND zone
v = pcbnew.PCB_VIA(board)
v.SetPosition(pt(20.5, 17.0)); v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4))
v.SetNet(board.FindNet("GND"))
board.Add(v)
print("追加: TP3 via (20.5,17.0)")

# TP3用トレース (20.5,18.5)→(20.5,17.0) F.Cu
t = pcbnew.PCB_TRACK(board)
t.SetStart(pt(20.5, 18.5)); t.SetEnd(pt(20.5, 17.0))
t.SetWidth(mm(0.2)); t.SetLayer(F_Cu)
t.SetNet(board.FindNet("GND"))
board.Add(t)
print("追加: TP3トレース (20.5,18.5)→(20.5,17.0)")

# ── 4. R1 DNP設定 ─────────────────────────────────────────────
for fp in board.GetFootprints():
    if fp.GetReference() == "R1":
        fp.SetDNP(True)
        print("R1 DNP設定完了")

# ── 5. Bug5修正 ───────────────────────────────────────────────
removed = 0
to_remove = []
for t in board.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        sx, sy = pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)
        ex, ey = pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)
        layer = t.GetLayer()
        # F.Cu (12.0,23.0)→(13.25,23.0)
        if layer == F_Cu:
            if ((abs(sx-12.0)<0.05 and abs(sy-23.0)<0.05 and abs(ex-13.25)<0.05 and abs(ey-23.0)<0.05) or
                (abs(ex-12.0)<0.05 and abs(ey-23.0)<0.05 and abs(sx-13.25)<0.05 and abs(sy-23.0)<0.05)):
                to_remove.append(t); print(f"Bug5削除: F.Cu (12,23)→(13.25,23)")
        # B.Cu (12.0,20.0)→(12.0,23.0) or (12.0,15.5)→(12.0,23.0)
        if layer == B_Cu:
            if abs(ex-12.0)<0.05 and abs(ey-23.0)<0.05 and abs(sx-12.0)<0.05:
                to_remove.append(t); print(f"Bug5削除: B.Cu ({sx:.1f},{sy:.1f})→(12,23)")
            elif abs(sx-12.0)<0.05 and abs(sy-23.0)<0.05 and abs(ex-12.0)<0.05:
                to_remove.append(t); print(f"Bug5削除: B.Cu ({sx:.1f},{sy:.1f})→(12,23) [逆]")
    elif t.GetClass() == "PCB_VIA":
        vx, vy = pcbnew.ToMM(t.GetX()), pcbnew.ToMM(t.GetY())
        if abs(vx-12.0)<0.05 and abs(vy-23.0)<0.05:
            to_remove.append(t); print(f"Bug5削除: via (12,23)")

for item in to_remove:
    board.Remove(item)
    removed += 1
print(f"Bug5削除完了: {removed}件")

# Bug5追加: B.Cu (13.5,15.5)→(13.5,21.1) w=0.4mm VCC
t = pcbnew.PCB_TRACK(board)
t.SetStart(pt(13.5, 15.5)); t.SetEnd(pt(13.5, 21.1))
t.SetWidth(mm(0.4)); t.SetLayer(B_Cu)
t.SetNet(board.FindNet("VCC"))
board.Add(t)
print("Bug5追加: B.Cu VCC (13.5,15.5)→(13.5,21.1)")

# Bug5追加: via(13.5,21.1) VCC → ATtiny pad1
v = pcbnew.PCB_VIA(board)
v.SetPosition(pt(13.5, 21.1)); v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4))
v.SetNet(board.FindNet("VCC"))
board.Add(v)
print("Bug5追加: via (13.5,21.1) VCC")

# ── 6. Fill All Zones ─────────────────────────────────────────
board.BuildConnectivity()
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
print("Fill All Zones 完了")

board.Save(PCB_PATH)
print(f"\n保存完了: {PCB_PATH}")
print("次: kicad-cli DRC → Gerber生成")

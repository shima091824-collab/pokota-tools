#!/usr/bin/env python3
"""
Fill All Zones + R1 DNP設定スクリプト
KiCad付属Python (3.9) で実行すること
"""
import sys
import os

PCB_PATH = "/Users/m2mac/gps-cat-tracker/lora-30x35-v3n.kicad_pcb"

print("=== Fill All Zones + R1 DNP ===")
print(f"PCBファイル: {PCB_PATH}")

import pcbnew

# PCB読み込み
board = pcbnew.LoadBoard(PCB_PATH)
print(f"KiCad バージョン: {pcbnew.Version()}")

# --- Step 1: R1 を DNP に設定 ---
r1_found = False
for fp in board.GetFootprints():
    if fp.GetReference() == "R1":
        fp.SetDNP(True)
        r1_found = True
        print(f"[OK] R1 DNP設定完了 (座標: {fp.GetX()/1e6:.1f}, {fp.GetY()/1e6:.1f} mm)")
        break

if not r1_found:
    print("[ERROR] R1が見つかりません")
    sys.exit(1)

# --- Step 2: Fill All Zones ---
print("Fill All Zones を実行中...")
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
print(f"[OK] {len(board.Zones())} ゾーンを塗り込み完了")

# TP3 GND viaの接続確認
for z in board.Zones():
    net = z.GetNetname()
    layer = z.GetLayerName()
    print(f"  ゾーン: {net} ({layer})")

# --- Step 3: 保存 ---
board.Save(PCB_PATH)
print(f"[OK] PCBファイル保存完了: {PCB_PATH}")

print("\n=== 完了 ===")
print("次のステップ: DRC実行 → Gerber出力")

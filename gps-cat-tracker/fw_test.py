#!/usr/bin/env python3
"""
猫GPSトラッカー ファームウェア動作確認テスト
基板到着前にPC上でロジックを検証する

テスト項目:
  1. NMEAパース ($GNRMC → 緯度・経度)
  2. 12バイトパケット エンコード/デコード
  3. Google Maps URL 生成
  4. GPS補足失敗時（lat=0）の判定
  5. $PCAS04 チェックサム確認
  6. ゲートウェイ コマンド応答シミュレーション

実行: python3 fw_test.py
"""

import struct

# ─────────────────────────────────────────────────────────
# 1. NMEA チェックサム計算
# ─────────────────────────────────────────────────────────
def nmea_checksum(payload: str) -> str:
    """$と*の間の文字列のXORを返す（例: "PCAS04,1" → "1A"）"""
    cs = 0
    for c in payload:
        cs ^= ord(c)
    return f"{cs:02X}"

# ─────────────────────────────────────────────────────────
# 2. NMEA パース ($GNRMC / $GPRMC)
# ─────────────────────────────────────────────────────────
def ddmm_to_deg(ddmm: float) -> float:
    """DDMM.MMMM形式 → 十進度"""
    deg = int(ddmm / 100)
    minutes = ddmm - deg * 100
    return deg + minutes / 60.0

def parse_gnrmc(sentence: str):
    """
    $GNRMC文を解析して (lat, lon) を返す。
    無効またはパース失敗時は (0.0, 0.0) を返す。
    """
    sentence = sentence.strip()
    # チェックサム検証
    if '*' in sentence:
        body, cs_recv = sentence[1:].rsplit('*', 1)
        tag, payload = body.split(',', 1)
        cs_calc = nmea_checksum(f"{tag},{payload}")
        if cs_calc != cs_recv[:2].upper():
            return 0.0, 0.0  # チェックサム不一致

    fields = sentence.split(',')
    if len(fields) < 7:
        return 0.0, 0.0
    if fields[2] != 'A':          # A=有効、V=無効
        return 0.0, 0.0

    try:
        lat = ddmm_to_deg(float(fields[3]))
        if fields[4] == 'S':
            lat = -lat
        lon = ddmm_to_deg(float(fields[5]))
        if fields[6] == 'W':
            lon = -lon
        return lat, lon
    except (ValueError, IndexError):
        return 0.0, 0.0

# ─────────────────────────────────────────────────────────
# 3. LoRaパケット エンコード / デコード（12バイト）
# ─────────────────────────────────────────────────────────
def encode_packet(lat: float, lon: float, seq: int) -> bytes:
    """
    緯度・経度・シーケンス番号を12バイトのバイナリに変換。
    GPS失敗時は lat=0.0, lon=0.0 を渡す。
    フォーマット: int32 lat × 1e6 | int32 lon × 1e6 | uint32 seq
    (リトルエンディアン)
    """
    lat_i = int(lat * 1_000_000)
    lon_i = int(lon * 1_000_000)
    return struct.pack('<iiI', lat_i, lon_i, seq)

def decode_packet(data: bytes) -> dict:
    """12バイトを辞書に変換。Google Maps URLも生成。"""
    if len(data) < 12:
        return {"error": "パケット長が短い"}
    lat_i, lon_i, seq = struct.unpack('<iiI', data[:12])
    if lat_i == 0 and lon_i == 0:
        return {"status": "GPS補足失敗", "seq": seq, "url": None}
    lat = lat_i / 1_000_000
    lon = lon_i / 1_000_000
    url = f"https://maps.google.com/?q={lat},{lon}"
    return {"status": "OK", "lat": lat, "lon": lon, "seq": seq, "url": url}

# ─────────────────────────────────────────────────────────
# 4. ゲートウェイ コマンド応答シミュレーション
# ─────────────────────────────────────────────────────────
def handle_command(cmd_byte: int, lat: float, lon: float, seq: int) -> bytes | None:
    """
    ゲートウェイからの1バイトコマンドを処理。
    0x01: 即時位置送信要求 → パケットを返す
    その他: None（無視）
    """
    if cmd_byte == 0x01:
        return encode_packet(lat, lon, seq)
    return None

# ─────────────────────────────────────────────────────────
# テスト実行
# ─────────────────────────────────────────────────────────
def run_tests():
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    results = []

    print("=" * 60)
    print("  猫GPSトラッカー ファームウェア動作確認テスト")
    print("=" * 60)

    # ── テスト1: $PCAS04 チェックサム ──────────────────────
    print("\n【1】$PCAS04 チェックサム確認")
    cs0 = nmea_checksum("PCAS04,0")
    cs1 = nmea_checksum("PCAS04,1")
    ok0 = cs0 == "19"
    ok1 = cs1 == "18"
    print(f"  GPS停止コマンド: $PCAS04,0*{cs0}\\r\\n  → {PASS if ok0 else FAIL} (期待値: 19)")
    print(f"  GPS起動コマンド: $PCAS04,1*{cs1}\\r\\n  → {PASS if ok1 else FAIL} (期待値: 18)")
    results.append(ok0 and ok1)

    # ── テスト2: 正常なNMEAパース ──────────────────────────
    print("\n【2】NMEAパース（正常・有効Fix）")
    nmea_valid = "$GNRMC,143000.00,A,3541.3700,N,13941.5020,E,0.0,0.0,300526,,,A*4A"
    lat, lon = parse_gnrmc(nmea_valid)
    # 3541.3700 → 35 + 41.37/60 = 35.6895°
    # 13941.5020 → 139 + 41.502/60 = 139.6917°
    lat_ok = abs(lat - 35.6895) < 0.0001
    lon_ok = abs(lon - 139.6917) < 0.0001
    print(f"  入力: {nmea_valid}")
    print(f"  緯度: {lat:.6f}° → {PASS if lat_ok else FAIL} (期待値: 35.689500°)")
    print(f"  経度: {lon:.6f}° → {PASS if lon_ok else FAIL} (期待値: 139.691700°)")
    results.append(lat_ok and lon_ok)

    # ── テスト3: 無効Fix (V) ────────────────────────────────
    print("\n【3】NMEAパース（無効Fix: V）")
    nmea_invalid = "$GNRMC,143000.00,V,0000.0000,N,00000.0000,E,0.0,0.0,300526,,,N*5C"
    lat2, lon2 = parse_gnrmc(nmea_invalid)
    ok3 = (lat2 == 0.0 and lon2 == 0.0)
    print(f"  入力: ステータス=V（無効）")
    print(f"  結果: lat={lat2}, lon={lon2} → {PASS if ok3 else FAIL} (期待値: 0.0, 0.0)")
    results.append(ok3)

    # ── テスト4: パケット エンコード ────────────────────────
    print("\n【4】12バイトパケット エンコード")
    pkt = encode_packet(35.6895, 139.6917, 42)
    print(f"  lat=35.6895°, lon=139.6917°, seq=42")
    print(f"  バイナリ: {pkt.hex()} ({len(pkt)}バイト)")
    ok4 = len(pkt) == 12
    print(f"  サイズ: {len(pkt)}バイト → {PASS if ok4 else FAIL} (期待値: 12バイト)")
    results.append(ok4)

    # ── テスト5: パケット デコード ─────────────────────────
    print("\n【5】12バイトパケット デコード")
    result = decode_packet(pkt)
    lat_ok2 = abs(result['lat'] - 35.6895) < 0.000002
    lon_ok2 = abs(result['lon'] - 139.6917) < 0.000002
    seq_ok  = result['seq'] == 42
    ok5 = lat_ok2 and lon_ok2 and seq_ok
    print(f"  status: {result['status']}")
    print(f"  lat: {result['lat']:.6f}° → {PASS if lat_ok2 else FAIL}")
    print(f"  lon: {result['lon']:.6f}° → {PASS if lon_ok2 else FAIL}")
    print(f"  seq: {result['seq']} → {PASS if seq_ok else FAIL}")
    print(f"  URL: {result['url']}")
    results.append(ok5)

    # ── テスト6: GPS補足失敗パケット ────────────────────────
    print("\n【6】GPS補足失敗パケット（lat=0, lon=0）")
    pkt_nf = encode_packet(0.0, 0.0, 99)
    result_nf = decode_packet(pkt_nf)
    ok6 = result_nf['status'] == 'GPS補足失敗'
    print(f"  バイナリ: {pkt_nf.hex()}")
    print(f"  status: {result_nf['status']} → {PASS if ok6 else FAIL}")
    results.append(ok6)

    # ── テスト7: ゲートウェイ コマンド応答 ─────────────────
    print("\n【7】ゲートウェイ コマンド応答シミュレーション")
    resp_01 = handle_command(0x01, 35.6895, 139.6917, 7)
    resp_ff = handle_command(0xFF, 35.6895, 139.6917, 7)
    ok7a = resp_01 is not None and len(resp_01) == 12
    ok7b = resp_ff is None
    print(f"  cmd=0x01（位置要求）: {resp_01.hex() if resp_01 else None} → {PASS if ok7a else FAIL}")
    print(f"  cmd=0xFF（不明）: {resp_ff} → {PASS if ok7b else FAIL} (期待値: 無視=None)")
    results.append(ok7a and ok7b)

    # ── テスト8: エンド・ツー・エンド シミュレーション ───────
    print("\n【8】エンド・ツー・エンド シミュレーション")
    print("  [GPS] NMEA受信 → パース → エンコード → LoRa送信 → デコード → Google Maps")
    nmea_e2e = "$GNRMC,083000.00,A,3536.1200,N,13945.6780,E,0.0,0.0,300526,,,A*4A"
    lat_e2e, lon_e2e = parse_gnrmc(nmea_e2e)
    pkt_e2e = encode_packet(lat_e2e, lon_e2e, 1)
    res_e2e = decode_packet(pkt_e2e)
    ok8 = res_e2e['status'] == 'OK' and res_e2e['url'] is not None
    print(f"  緯度: {lat_e2e:.6f}°  経度: {lon_e2e:.6f}°")
    print(f"  パケット: {pkt_e2e.hex()}")
    print(f"  Google Maps: {res_e2e['url']}")
    print(f"  → {PASS if ok8 else FAIL}")
    results.append(ok8)

    # ── 結果サマリー ────────────────────────────────────────
    print("\n" + "=" * 60)
    passed = sum(results)
    total  = len(results)
    print(f"  結果: {passed}/{total} PASS", "🎉 全テスト通過！" if passed == total else "⚠️ 一部失敗")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()

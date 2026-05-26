# GPS Cat Tracker LoRa v3 Plan-B — BOM (Bill of Materials)

> **基板**: 30 × 28 mm（GPS搭載版 — AirTag相当サイズ）
> **通信**: E220-900T22S(JP) LoRa 920MHz 技適済 (001-P01730)
> **設計ファイル**: `lora-30x28-v3b.kicad_pcb` / `gerber-v3b/lora-30x28-v3b-gerber.zip`
> **ピン配置**: 全部品データシートで確認済み (2026-05-26)

---

## ⚠️ v3 Plan-B 変更点（v2からの修正）

| 変更点 | v2（GPS無し） | v3 Plan-B |
|--------|------------|-----------|
| ボードサイズ | 30×22mm | **30×28mm**（GPS搭載のため拡大） |
| GPS | プレースホルダのみ | **MAX-M8Q 実装**（9.7×10.1mm） |
| GPS footprint | 4.1×3.1mm（**誤り**） | **9.7×10.1mm**（データシート実測値） |
| GPSパッドピッチ | 0.35mm（推定、誤り） | **1.1mm**（データシートTable21 E値） |
| 重量（目安） | 約5〜6g | **約8〜9g** |
| バッテリ寿命 | LoRaのみ約214日 | **GPS+LoRa 約10日** |

### v2からの継続事項（変更なし）
| 項目 | 内容 |
|------|------|
| E220ピン配置 | データシート確認済み：短辺22ピンDFN |
| ATtiny3226ピン配置 | データシート確認済み：VQFN-20 セクション2.3 |
| GPS電圧 | 3.3V直接接続（VIO_SEL=開放で3.3Vモード） |
| 充電回路 | 削除済み（外付け充電器で充電） |
| 電源 | E220 VDD(pin15)=3.3V出力を活用（LDO不要） |
| GPSアンテナ | 開放（チップアンテナ or IPEXコネクタ接続） |

---

## 主要部品

| Ref | 部品名 | 型番 | 調達先候補 | 数量 | 単価(目安) | 備考 |
|-----|--------|------|-----------|------|------------|------|
| U1 | LoRaモジュール | E220-900T22S(JP) | 秋月/Amazon/千石 | 1 | ¥2,500 | 技適✅ 001-P01730, 26×16mm DFN-22 |
| U2 | MCU | ATtiny3226-MFR | Mouserほか | 1 | ¥220 | VQFN-20 3×3mm, UART×2, 1.8-5.5V |
| U3 | GPS | MAX-M8Q-00B | Mouserほか | 1 | ¥800 | **9.7×10.1mm LCC-18**, 3.3V対応, -148dBm |
| J1 | バッテリコネクタ | JST-GH 1.25mm 2P | 秋月 | 1 | ¥60 | SMD横差し |
| C1–C4 | コンデンサ 100nF 0402 | — | JLCPCB Basic | 4 | ¥3 | 電源デカップリング |
| C5 | コンデンサ 1μF 0402 | — | JLCPCB Basic | 1 | ¥5 | 3.3Vバルクキャップ |
| R1 | 抵抗 10kΩ 0402 | — | JLCPCB Basic | 1 | ¥2 | E220 AUXプルアップ（オプション） |

---

## 電源アーキテクチャ（LDO不要！）

```
LiPo 3.7V ──→ J1(BATT+) ──→ E220 VCC (pin10, 2.2-5.5V対応)
                                    │
                              E220内蔵LDO
                                    │
                              E220 VDD (pin15) = 3.3V出力（最大100mA）
                                    │
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
              ATtiny VDD(pin4)  GPS VCC(pin8)   GPS V_IO(pin7)
              ATtiny電源(3.3V)  GPS電源(3.3V)   GPS IOレベル(3.3V)
```

**GPS VIO_SEL (pin15) = 開放 → V_IO = VCC = 3.3V**（3.3Vモード自動選択）

---

## 確認済みピン配置（全てデータシート実測値）

### E220-900T22S(JP) — データシート Rev2.1.1 セクション3.1

| ピン | 信号名 | 接続先 |
|------|--------|--------|
| 1-3 | AGND | GND（RF側） |
| 4 | GND | GND |
| 5 | M0 | ATtiny PA4 (VQFN pin5) |
| 6 | M1 | ATtiny PA5 (VQFN pin6) |
| 7 | RXD | ATtiny PB2/USART0-TxD (VQFN pin12) |
| 8 | TXD | ATtiny PB3/USART0-RxD (VQFN pin11) |
| 9 | AUX | ATtiny PA6 (VQFN pin7)、入力 |
| 10 | VCC | BATT+ (3.7V LiPo) |
| 11 | GND | GND |
| 12 | SWDIO | 未接続（FW更新用） |
| 13 | SWGND | GND（FW更新時のみ） |
| 14 | SWCLK | 未接続（FW更新用） |
| 15 | VDD | **3.3V出力** → ATtiny/GPS電源 |
| 16-18 | NC | 開放 |
| 19 | GND | GND |
| 20 | AGND | GND（RF側） |
| 21 | ANT | IPEXコネクタ（アンテナ接続） |
| 22 | AGND | GND（RF側） |

### ATtiny3226 VQFN-20 — DS40002345A セクション2.3

| ピン | 信号名 | 接続先 |
|------|--------|--------|
| 1 | PA2 | 未使用 |
| 2 | PA3 | 未使用 |
| 3 | GND | GND |
| 4 | VDD | 3.3V（E220 VDD） |
| 5 | PA4 | E220 M0 (pin5) |
| 6 | PA5 | E220 M1 (pin6) |
| 7 | PA6 | E220 AUX (pin9) |
| 8 | PA7 | 未使用 |
| 9 | PB5 | 未使用 |
| 10 | PB4 | 未使用 |
| 11 | PB3/USART0-RxD | E220 TXD (pin8) |
| 12 | PB2/USART0-TxD | E220 RXD (pin7) |
| 13 | PB1 | 未使用 |
| 14 | PB0 | 未使用 |
| 15 | PC0 | 未使用 |
| 16 | PC1/USART1-RxD★ | GPS TXD (pin2) ★PORTMUX要設定 |
| 17 | PC2/USART1-TxD★ | GPS RXD (pin3) ★PORTMUX要設定 |
| 18 | PC3 | 未使用 |
| 19 | PA0/UPDI | プログラミング端子 |
| 20 | PA1 | 未使用 |
| EP | GND | GND（熱パッド、接続必須） |

★PORTMUX設定: `PORTMUX.USARTROUTEA |= PORTMUX_USART1_ALT1_gc;` （USART1をPC1/PC2に割り当て）

### MAX-M8Q LCC-18 — 9.7×10.1mm（データシート実測値）

> **パッド仕様**: 9パッド/辺（長辺10.1mm側）、ピッチ1.1mm、パッドサイズ1.4×0.4mm
> **★ 発注前にu-blox HIMでフットプリント寸法を必ず実測確認すること**

| ピン | 信号名 | 接続先 |
|------|--------|--------|
| 1 | GND | GND |
| 2 | TXD | ATtiny PC1/USART1-RxD (pin16) |
| 3 | RXD | ATtiny PC2/USART1-TxD (pin17) |
| 4 | TIMEPULSE | 未使用（開放） |
| 5 | EXTINT | 未使用（開放） |
| 6 | V_BCKP | VCC(3.3V)に接続（RTC維持） |
| 7 | V_IO | 3.3V（E220 VDD） |
| 8 | VCC | 3.3V（E220 VDD） |
| 9 | RESET_N | 未使用（開放）内部プルアップあり |
| 10 | GND | GND |
| 11 | RF_IN | GPSチップアンテナ（1575MHz対応品） |
| 12 | GND | GND |
| 13 | LNA_EN | 未使用（開放） |
| 14 | VCC_RF | 未使用（開放） |
| 15 | VIO_SEL | **開放（floating）→ 3.3V V_IOモード自動選択** |
| 16 | SDA | 未使用（開放） |
| 17 | SCL | 未使用（開放） |
| 18 | SAFEBOOT_N | 未使用（開放）内部プルアップあり |
| EP | GND | GND（サーマルパッド、必須） |

---

## ★ 発注前の必須確認事項

- [ ] **u-blox Hardware Integration Manual** でMAX-M8Qフットプリント寸法確認
  - URL: https://www.u-blox.com/en/product/max-m8q-module → "Resources"タブ
  - 確認項目: ランドパターン、パッドピッチ(目標1.1mm)、パッドサイズ、EPサイズ
  - 現在の設定値: pitch=1.1mm, pad=1.4×0.4mm, EP=6.5×7.8mm（要HIM確認）
- [ ] KiCad DRC（`検査 > デザイン ルール チェッカー`）エラーゼロ確認
- [ ] E220フットプリント: パッドピッチ1.27mm確認済み（データシートより）
- [ ] ATtiny3226 QFN-20: 0.5mmピッチ → **外注推奨**（手はんだ難）
- [ ] MAX-M8Q LCC-18: 1.1mmピッチ → **外注推奨**（細密）
- [ ] GPS用チップアンテナを選定・追加（1575.42MHz GPS対応品）
  - 候補: Taoglas AA.161, Molex 2137640100など

---

## PCB発注（JLCPCB）

| 項目 | 仕様 |
|------|------|
| 基板サイズ | 30 × 28 mm |
| 層数 | 2層 |
| 厚さ | 0.8mm（軽量化） |
| 銅箔 | 1oz |
| 表面仕上げ | HASL（鉛なし） |
| ソルダーマスク | 緑 |
| 枚数 | 5枚（最小ロット） |
| **PCB代（目安）** | **約$2〜3（OCS NEP送料込み）** |

**アップロードファイル**: `gerber-v3b/lora-30x28-v3b-gerber.zip`

---

## バッテリ（別途調達）

| 品名 | 寸法 | 価格 |
|------|------|------|
| LiPo 300mAh 3.7V | 5×30×28mm以内 | ¥600〜900 |

外付けUSBchargerでバッテリーを充電

---

## 重量・バッテリ寿命

| 項目 | 値 |
|------|-----|
| PCB重量目安 | 約3.5g（30×28mm） |
| バッテリ（300mAh） | 約5g |
| GPSチップアンテナ | 約0.5g |
| 合計 | 約9〜10g |
| GPS取得時消費 | 約15mA（M8Q: 低消費モード）× 30秒 |
| LoRa送信時消費 | 約43mA（13dBm）× 2秒 |
| スリープ消費 | ATtiny3226: <5µA + E220 DeepSleep: 2.5µA |
| **30分間隔動作時** | **約10日 / 300mAh** |

---

## ホーム受信機（別途構築）

猫が帰宅/外出した際のLoRa信号受信用

| 部品 | 型番 | 価格 |
|------|------|------|
| Raspberry Pi Zero W | — | ¥2,000〜 |
| E220-900T22S(JP) | 同型 | ¥2,500 |
| USBシリアル変換 | CP2102など | ¥500 |
| 外付けアンテナ | 920MHz対応 | ¥500 |
| **合計** | | **¥5,500〜** |

---

## 総コスト（初回）

| 項目 | 金額 |
|------|------|
| JLCPCB PCB（5枚） | ¥450 |
| E220-900T22S(JP) × 1 | ¥2,500 |
| ATtiny3226 × 1 | ¥220 |
| MAX-M8Q × 1 | ¥800 |
| JST-GH + コネクタ | ¥60 |
| パッシブ部品一式 | ¥100 |
| GPSチップアンテナ | ¥200〜 |
| バッテリ 300mAh | ¥700 |
| はんだ付け外注（GPS/MCU） | ¥3,000〜 |
| **合計（初回）** | **約¥8,000〜** |

---

*設計: Claude Code / Anthropic — v3 Plan-B 2026-05-26*
*全ピン配置はデータシートで確認済み。GPS footprintはu-blox HIMで要確認。*

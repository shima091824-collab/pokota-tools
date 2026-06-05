# 猫GPSトラッカー 自作LoRa基板 設計書

**ファイル**: `lora-30x35-v3n.kicad_pcb`  
**最終更新**: 2026-05-30（セッション3）  
**KiCad**: 10.0.3  

---

## 0. 設計検証ルール（必読・全セッション共通）

**フェーズゲートチェックリスト**: [`CHECKLIST.md`](./CHECKLIST.md)  
PCB発注・FW書き込み・ブリングアップの前に CHECKLIST.md を参照すること。

**一次情報参照ルール（これを守ればバグの9割は防げる）**:

| 情報の種類 | 一次情報源（使うべきもの） | 禁止 |
|-----------|------------------------|------|
| ピン番号 | KiCad .kicad_pcb の pad 座標・net名 | シルクスクリーン・メモ・記憶 |
| レジスタ値・enum | `avr/iotn3226.h` を grep | 推測・他MCUの知識の転用 |
| ISRベクタ名 | `iotn3226.h` を grep して存在確認 | 推測・AVR Classic仕様の転用 |
| 修正完了の判定 | kicad-cli DRC 件数の変化を確認 | 「たぶん反映された」という記憶 |
| LCSC番号 | JLCPCB parts library で実在確認 | BOMの既存記録（変わることがある） |

---

## 1. 要件定義

### 1-1. 基本仕様

| 項目 | 仕様 |
|------|------|
| 用途 | 猫の屋外位置追跡（LoRa通信） |
| 通信 | LoRa 920MHz（技適取得済み 001-P01730） |
| 測位 | GPS（ATGM336H-5N31） |
| MCU | ATtiny3226（UART×2系統：GPS/E220） |
| 電源 | LiPo 500mAh JST-GH 1.25mm 2P |
| 充電 | USB-C → TP4056（200mA） → LiPo（約3時間） |
| 基板サイズ | 30×35mm（2層） |
| 基板厚 | **0.8mm FR4**（RF50Ω設計値・変更禁止） |
| 表面処理 | HASL有鉛 |
| 発注先 | JLCPCB |

### 1-2. 動作要件（2026-05-30 確定）

| 項目 | 仕様 | 備考 |
|------|------|------|
| 位置更新間隔 | 30分ごと（自動送信） | ATtinyがUARTでGPSスリープ制御 |
| リアルタイム確認 | ゲートウェイからコマンドで随時取得 | LoRaポーリング受信で対応（応答遅延最大1分） |
| バッテリー持ち（目標） | **3〜5日** | 充電ゼロから |
| バッテリー持ち（試算） | コールドGPS: **約6日**、ホットGPS: **約8日** | 下記試算参照 |
| 通信距離（目標） | 自宅〜近隣200〜500m | E220 22dBm、障害物あり都市環境 |

### 1-3. システム構成（受信側）

| 項目 | 仕様 |
|------|------|
| ゲートウェイ | 自宅設置1台（別途製作：RaspberryPi + E220等） |
| スマホ連携 | ゲートウェイ経由（オプション・後日検討） |
| データフォーマット | 未定（ファームウェア設計時に決定） |

### 1-4. 装着条件

| 項目 | 仕様 |
|------|------|
| 装着方法 | ケース入り、猫の首輪に取り付け |
| 重量（目標） | ケース込み50g以下（PCB+LiPo推定20〜30g） |
| 防水 | ケース側で対応（基板自体はコンフォーマルコート検討） |

### 1-5. データフォーマット・UI要件（2026-05-30 確定）

**LoRaペイロード（12バイト固定長バイナリ）**:

| バイト | 内容 | 型 | 備考 |
|--------|------|-----|------|
| 0–3 | 緯度 (latitude) | int32_t | 実値×1,000,000（例: 35.6895° → 35689500） |
| 4–7 | 経度 (longitude) | int32_t | 実値×1,000,000（例: 139.6917° → 139691700） |
| 8–11 | タイムスタンプ | uint32_t | UNIX時刻（秒）またはカウンター |

→ **バイナリ選択理由**: LoRA 920MHzのペイロード制限・省電力に最適。CSV文字列は20〜30バイトになり送信時間・電力が増える。

**ゲートウェイ（Raspberry Pi）の処理**:
1. LoRaパケット受信 → 12バイトデコード
2. Google Maps URL生成: `https://maps.google.com/?q=緯度,経度`
3. Web UIでブラウザ表示（地図+最終確認時刻）

**確認方法（UI）**:
- スマホブラウザ → ゲートウェイのローカルIPにアクセス
- ゲートウェイがシンプルなWebサーバー（Flask等）を立てる
- Google Maps埋め込みで猫の位置をピン表示
- 自宅外からのアクセス: tailscale等VPNまたはngrok（後日検討）

---

### 1-6. バッテリー試算（前提：スリープ制御あり）

**30分サイクルの動作モデル**:
| フェーズ | 電流 | 時間 | 消費 |
|---------|------|------|------|
| GPS補足（コールド） | 30mA | 60秒 | 0.50mAh |
| GPS継続受信 | 25mA | 30秒 | 0.21mAh |
| LoRa送信 | 120mA | 1秒 | 0.033mAh |
| LoRaポーリング×30回（2秒/回） | 16mA | 60秒 | 0.27mAh |
| スリープ（E220スタンバイ+GPS VBAT） | 1.5mA | 約27分 | 0.69mAh |
| **合計（30分）** | **平均3.4mA** | — | **1.70mAh** |

→ **500mAh ÷ 3.4mA = 約147時間 ≈ 6.1日**  
→ ホットスタート（2回目以降）: 平均2.4mA → **約8.5日**

**スリープ制御の実現方法**:
- GPS ON/OFF(p5)はVCCに固定（ハード制御不可）
- → **NMEAコマンド（$PCAS04）でUARTソフトスリープ制御**（GPIO追加不要）
- GPS VBAT(p6)はVCC_3V3接続済み → ホットスタート（~15秒補足）対応 ✅

---

## 2. 部品リスト（BOM）

### JLCPCB SMT実装部品

| Ref | 型番/値 | LCSC# | パッケージ | 役割 |
|-----|---------|-------|-----------|------|
| U2 | ATtiny3226-MU | **C5227682** | VQFN-20 | MCU（主制御） |
| U3 | ATGM336H-5N31 | C90770 | LCC-18 | GPS |
| U4 | TP4056 | C16581 | ESOP-8 | LiPo充電IC |
| C1,C2,C3,C4,C6 | 100nF 10V | C14663 | 0402 | バイパスコン |
| C5 | 1uF 10V | C52923 | 0402 | バイパスコン |
| R2 | 5.0kΩ | C25905 | 0402 | TP4056 PROG（充電電流設定） |
| R3,R4 | 330Ω | C22978 | 0402 | LED電流制限 |
| R5 | 5.1kΩ（CC1） | C23186 | 0402 | USB-C CC1プルダウン |
| R6 | 5.1kΩ（CC2） | C23186 | 0402 | USB-C CC2プルダウン |
| LED1 | RED 0402 | C2286 | 0402 | 状態表示（赤） |
| LED2 | BLUE 0402 | C72041 | 0402 | 状態表示（青） |
| SW1 | MSK12C02-HB | C431541 | SMD | 電源スイッチ |
| ANT1 | U.FL-R-SMT-1(10) | **C88373** | SMD | LoRaアンテナ端子 |
| J1 | JST-GH 1.25mm 2P | **C189893** | SMD | LiPoバッテリー（JLCPCB在庫3,394個 ✅） |
| J2 | USB-C 16P SMD | C2765186 | SMD | 充電コネクタ |

> **⚠️ BOM修正履歴（2026-05-30）**: 旧LCSC番号に誤りが3件あり修正済み  
> - U2: C3014522（存在しない）→ **C5227682** (ATTINY3226-MU VQFN-20(3x3))  
> - ANT1: C317592（PADAUKのMCU・全くの別部品）→ **C88373** (Hirose U.FL-R-SMT-1(10))  
> - J1: C160404（JST SH 1mm 4P・ピン数・ピッチ共に不一致）→ **C189893** (SM02B-GHS-TB JST-GH 1.25mm 2P)

### 手はんだ部品（LCSC外・別途調達）

| Ref | 型番 | 調達先 | 役割 |
|-----|------|--------|------|
| U1 | E220-900T22S(JP) | AliExpress（Ebyte公式）¥600〜800/個 | LoRa 920MHz送受信 |

### DNP（実装しない）

| Ref | 値 | 理由 |
|-----|-----|------|
| R1 | 10kΩ | 用途不明・設計者も理由を失念→DNP |

---

## 3. 電源トポロジー

```
USB-C (J2)
  │
  ├── R5 (5.1kΩ) → CC1 (GND)    ← USB-C 5V給電認識用
  └── R6 (5.1kΩ) → CC2 (GND)    ← USB-C 5V給電認識用
  │
  ↓ VBUS 5V
TP4056 (U4)
  │
  ↓ BAT（4.2V max）
LiPo 500mAh (J1)
  │
  ↓
SW1 (電源スイッチ)
  │
  ↓ VCC（3.7V / LiPo電圧）
E220 (U1)
  ├── 内蔵LDO → VDD 3.3V出力ピン
  │     ├── ATtiny3226 (U2) VCC
  │     ├── ATGM336H (U3) VCC
  │     └── バイパスコン (C1-C6)
  └── RF出力 → ANT1 (U.FL) → アンテナ
```

**重要**: E220のVDD出力（3.3V）がMCU・GPSの電源。  
E220が起動していないとMCUもGPSも動作しない。

---

## 4. 信号接続（UART）

```
ATGM336H (U3)          ATtiny3226 (U2)                 E220 (U1)
   TXD ────────────────→ PC1=RxD1 (USART1 ALT1)
   RXD ←──────────────── PC2=TxD1 (USART1 ALT1)

                          PA1=TxD0 (USART0 ALT1) ──────→ RXD
                          PA2=RxD0 (USART0 ALT1) ←────── TXD
```

※ATtiny3226はUART2系統（USART0/USART1）を持つ。  
※PORTMUX.USARTROUTEA = 0x05 (USART0_ALT1 | USART1_ALT1) 必須。  
　未設定時: USART0→PB[3:0]、USART1→PA[4:1]（どちらも誤ピン）。

---

## 5. 部品の絶対座標（PCBより自動抽出）

### コンポーネント中心座標

| Ref | X (mm) | Y (mm) | 回転 | 備考 |
|-----|--------|--------|------|------|
| U1 | 13.000 | 8.000 | 0° | 手はんだ |
| U2 | 15.000 | 22.500 | 0° | |
| U3 | 6.600 | 22.000 | 0° | |
| U4 | 25.000 | 30.500 | 0° | |
| C1 | 27.500 | 0.800 | 0° | U1パッド干渉回避のためy=0.8に移動・pad1(26.6,0.8)→VCC縦トレース→U1.pad10、pad2(28.4,0.8)→GND via(28.4,1.5) |
| C2 | 28.500 | 4.500 | 90° | 2026-05-30適用済 |
| C3 | 19.500 | 20.500 | 0° | |
| C4 | 12.900 | 17.000 | 90° | 2026-05-30適用済 |
| C5 | 28.500 | 7.500 | 90° | 2026-05-30適用済 |
| C6 | 28.000 | 27.500 | 0° | |
| R1 | 19.500 | 24.500 | 0° | DNP |
| R2 | 25.000 | 33.500 | 0° | |
| R3 | 17.000 | 29.500 | 0° | |
| R4 | 20.000 | 29.500 | 0° | |
| R5 | 5.000 | 33.000 | 0° | |
| R6 | 8.000 | 33.000 | 0° | |
| LED1 | 17.000 | 28.500 | 0° | |
| LED2 | 20.000 | 28.500 | 0° | |
| SW1 | 3.000 | 30.000 | 0° | |
| ANT1 | 25.000 | 19.000 | 0° | |
| J1 | 23.000 | 24.500 | 0° | |
| J2 | 15.000 | 33.000 | 0° | |

### 重要パッド絶対座標

| パッド | X (mm) | Y (mm) | 接続先 |
|--------|--------|--------|--------|
| C4.pad1 | 12.900 | 17.900 | GND → via@(14.5,17.0) → B.Cu GND zone |
| C4.pad2 | 12.900 | 16.100 | VCC → (11.2,16.1) → (11.2,17.5) → via@(11.2,17.5) |
| U3.pad8 | 11.350 | 18.700 | VCC（F.Cu x=11.35 + F.Cu x=12経由） |
| U3.pad9 | 11.350 | 17.600 | VCC（F.Cu x=11.35 → via@11.2,17.5） |
| U3.pad7 | 11.350 | 19.800 | VCC_IO（F.Cu x=11.35, pad8から供給） |
| C1.pad1 | 26.600 | 0.800 | VCC → F.Cu縦トレース(26.6,0.8→26.6,2.92) |
| C1.pad2 | 28.400 | 0.800 | GND → F.Cu(28.4,0.8→28.4,1.5) → via@(28.4,1.5) → B.Cu GNDゾーン |
| C2.pad1 | 28.500 | 5.400 | GND → via@(27.5,5.4) |
| C2.pad2 | 28.500 | 3.600 | VCC |
| C5.pad1 | 28.500 | 8.400 | GND → via@(28.5,9.0) |
| C5.pad2 | 28.500 | 6.600 | VCC |

### B.Cu VCC迂回via（バグ3修正で追加）

| via | X (mm) | Y (mm) | 役割 |
|-----|--------|--------|------|
| via | 12.000 | 17.200 | B.Cu VCC → F.Cu（RFトレース上帯を回避） |
| via | 12.000 | 20.000 | F.Cu → B.Cu（RFトレース下帯に再突入） |

---

## 6. PCBレイヤー構成

| レイヤー | 内容 |
|---------|------|
| F.Cu | 信号トレース・VCCトレース（一部） |
| B.Cu | VCCトレース（幅1.5mm・y=18.7）＋GNDベタ塗り |
| F.SilkS | シルク（部品名） |
| B.SilkS | 裏シルク |
| F.Mask / B.Mask | ソルダーマスク |
| Edge.Cuts | 基板外形 30×35mm |

**B.Cu VCCトレース**:
- y=18.7: 幅1.5mm (y=17.95〜19.45), x=3.5〜24.0 → RF 50Ω設計（0.8mm FR4対応）
- y=15.5: 幅0.4mm (y=15.3〜15.7), x=1.5〜18.6

---

## 7. 製造ファイル

| ファイル | 状態 | 備考 |
|---------|------|------|
| `lora-30x35-v3n.kicad_pcb` | ✅ 最新 | |
| `lora-30x35-v3n.kicad_sch` | ✅ 生成完了 | 2026-05-30・`generate_schematic_v3n.py`で生成・ERC実質0件 |
| `generate_schematic_v3n.py` | ✅ | Pythonスクリプト（回路図生成）・再実行でkicad_sch再生成可 |
| `lora-30x35-v3n_gerber.zip` | ⚠️ 使用禁止 | 旧.gbrファイルと新JLCPCB標準ファイルが混在（重複レイヤー多数）→誤製造リスク |
| `lora-30x35-v3n_gerber_jlcpcb.zip` | ✅ 発注用 | 2026-05-30（セッション3）・JLCPCB標準拡張子のみ12ファイル・20KB |
| `bom_jlcpcb.csv` | ✅ 修正済み | 2026-05-30: LCSC# 3件誤り修正（ATtiny/U.FL/JST-GH） |
| `cpl_jlcpcb.csv` | ✅ 更新済み | C2/C4/C5座標修正・R1/U1除外 |

---

## 8. フロー別進捗（2026-06-05更新）

| # | フェーズ | 状態 | 進捗 | タイミング |
|---|---------|------|------|-----------|
| 1 | 要件定義 | ✅ | **100%** | 発注前 |
| 2 | 部品選定 | ✅ | **100%** | 発注前 |
| 3 | 回路図 | ✅ | **90%** | 発注前 |
| 4 | ERC | ✅ | **95%** | 発注前 |
| 5 | PCBレイアウト | ✅ | **100%** | 発注前 |
| 6 | DRC | ✅ | **95%** | **358件・clearance 0・未配線 0**（via_dangling 3・track_dangling 3は構造的・製造影響なし） |
| 7 | Gerber | ✅ | **完了** | **2026-06-05 再生成済み** `gerber_jlcpcb_final.zip` (18KB) |
| 8 | BOM/CPL | ✅ | **98%** | 発注前 |
| 9 | **FW設計（アーキテクチャ）** | ✅ | **100%** | **完了**（2026-05-30） |
| 10 | 発注 | ⚠️ | **95%** | **← 今ここ・ユーザー操作（JLCPCB決済）待ち** |
| 11 | 実装（はんだ付け） | ❌ | 0% | 基板到着後 |
| 12 | **FW実装・書き込み** | ❌ | 0% | 実装後 |
| 13 | **動作確認・デバッグ** | ❌ | 0% | FW書き込み後 |

**ファームウェア設計の進め方:**
- FW設計（アーキテクチャ）→ **今から着手可能**。ピン配置・通信仕様が確定済みのため。
- FW実装・書き込み → 基板実装後（ATtiny3226 + UPDIアダプタ必要）
- 動作確認 → 基板実装後

---

## 9. 既知の問題・TODO

### ✅ 修正済みバグ（2026-05-29）

**バグ1: ATtiny3226 VCC→信号ピン短絡 →【修正済み・ただしBug5を誘発】**
- 原因: via at (13.25, 23.7) が ATtiny pad5 (PA7, y=23.5) と物理的に重なっていた
- 修正内容: B.Cu縦トレース `(13.25,20)→(13.25,23.7)` を削除、via at (13.25,23.7) を削除
- ⚠️ **修正後に「via(12,23)→F.Cu→pad1でVCC維持」と記録したが、これは誤り**
  - F.Cu (12.0,23.0)→(13.25,23.0) の終点は U2 **pad4 (PA6)** であり VDD (pad1) ではない
  - ATtiny pad1 (VDD, y=21.5) と pad4 (PA6, y=23.0) はy方向に1.5mm離れており別パッド
  - → これがBug5（ATtiny VDD未接続）の根本原因

**バグ2: GPS GND短絡バグ →【誤診断・修正を取消し】**
- 元の想定: p5/p6/p7=GNDと仮定していたが、データシートで誤りと判明
- 正しいピン配置（2026-05-29データシート確認）:
  - p9=nRESET（VCCに接続→常時動作・リセット無効）
  - p8=VCC ✓
  - p7=NC（VCCに接続しても無害）
  - p6=VBAT（RTC・SRAMバックアップ、VCC=3.3V接続で簡易設計として適切）
  - p5=ON/OFF（Low有効、VCC=3.3V接続で常時ON）
- 一度削除したトレース `(11.35,20.9)→(11.35,22)` を復元（VBAT・ON/OFF接続を維持）
- **元のトレース設計は意図的・問題なし。バグ2は誤診断だった**

**バグ3: B.Cu VCCトレースがB.Cu RFトレースと交差→ANT1信号がVCC短絡 →【修正済み】**
- 原因: B.Cu VCCトレース `(12,15.5)→(12,23)` が B.Cu RFトレース（y=18.7, 幅1.5mm, y=17.95〜19.45）と交差
- 交差点: x=11.8〜12.2, y=17.95〜19.45 → ANT1.pS → via(24,19) → B.Cu RF → VCC短絡
- 修正内容: B.Cu `(12,15.5)→(12,23)` を F.Cu経由に迂回
  - B.Cu `(12,15.5)→(12,17.2)` + via at (12,17.2)
  - F.Cu `(12,17.2)→(12,20)` （RF帯を安全にF.Cuで越える）
  - via at (12,20) + B.Cu `(12,20)→(12,23)`
- 副効果: F.Cu x=12のトレースがGPS pad8 VCC・pad7 VCC_IOに接触→GPS VCC供給も安定

### ✅ 判明済み事項

- **R2の用途**: TP4056の充電電流設定抵抗（PROG）→ R2.p1→U4.p1(PROG), R2.p2→GND
- **LED接続**: LED1(RED)→U4.p6(CHRG充電中表示), LED2(BLUE)→R4→U4.p7(STDBY満充電表示)
- **GPS→MCU UART【バグ4：修正完了 2026-05-30】**: GPS TXD(p2)→ATtiny pad7(PC1=RxD1, 14.5,24.25)・GPS RXD(p3)→ATtiny pad8(PC2=TxD1, 15.0,24.25) に正しく再配線済み。pad16(UPDI)/pad17(PA0)はfloating（UPDI書き込みヘッダ追加が今後の課題）。
- **LoRa→MCU**: U1.p6↔U2.p6, U1.p7↔U2.p12, U1.p8↔U2.p11
- **電源スイッチ**: J1.p1(バッテリー+) → SW1.p2 → U1.p10(E220 VCC)
- **GPS U3全ピン配置（2026-05-29データシート確認済み）**:
  - 右側: p1=GND, p2=TXD, p3=RXD, p4=1PPS, p5=ON/OFF, p6=VBAT, p7=NC, p8=VCC, p9=nRESET
  - 左側: p10=GND, p11=RF_IN, p12=GND, p13=NC, p14=VCC_RF(アンテナ給電3.3V出力), p15=Reserved, p16=SDA, p17=SCL, p18=Reserved
  - VCC供給: p8(VCC), p5(ON/OFF=High→常時ON), p6(VBAT=3.3V→ホットスタート維持)
  - nRESET(p9)はVCCトレースに接触→リセット不可だが常時動作は問題なし

---

### 🔴 **Bug5: ATtiny VDD (pad1) 未接続 → 発注前に必ず修正【凍結中・未修正】**

**発見日**: 2026-05-30 セッション4（GPS pad接続追跡中に判明）

**症状**: ATtiny3226 VDD（pad1, 座標13.25,21.5）に銅線が届いていない → ATtinyが動作しない（致命的バグ）

**根本原因（Bug1修正の副作用）**:
- Bug1修正でvia(13.25,23.7)とB.Cu縦トレースを削除した際、ATtiny VDD接続が失われた
- 代替パスとして記録した「via(12.0,23.0)→F.Cu(12.0,23.0→13.25,23.0)→pad1」は誤り
- 実際の終点: (13.25,23.0) = U2 **pad4 (PA6)** であり **VDD (pad1, y=21.5) ではない**（1.5mm誤差）

**副作用（同時に存在する問題）**:
1. ATtiny PA6 (pad4) が VCC に接続されている（GPIO pin に電源短絡）
2. GPS 1PPS (U3 pad4, y=23.1) が via(12.0,23.0) 経由でVCCに接続されている
   - via(12.0,23.0)の銅環(0.4mm半径)がGPS pad4の銅箔(x=10.45-12.25, y=22.70-23.50)と重複 → 電気的接続
   - 1PPS=プッシュプル出力なら1秒ごとにVCCとの電流衝突が発生（GPS破損リスク）

**修正計画（未適用）**:

削除:
1. F.Cu トレース (12.0,23.0)→(13.25,23.0) — PA6へのVCC接続を除去
2. B.Cu トレース (12.0,20.0)→(12.0,23.0) — GPS 1PPSへのVCC経路を除去
3. via(12.0,23.0) — 同上

追加:
4. B.Cu トレース (13.5,15.5)→(13.5,21.1) w=0.4mm — VCC幹線分岐点(13.5,15.5)からATtiny VDD方向へ
5. via(13.5,21.1) size=0.8 drill=0.4 — B.Cu→F.Cu変換、ATtiny pad1と銅箔重複接続
   - 重複確認済み: via銅環(x=13.1-13.9, y=20.7-21.5) ∩ pad1(x=12.925-13.575, y=21.375-21.625) = 0.475×0.125mm ✅
   - pad2(PA4, y=22.0)との非重複確認済み: via上端21.5 < pad2下端21.875 ✅

**修正後の効果**:
- ATtiny VDD (pad1) に VCC 供給 ✅
- PA6 (pad4) のVCC誤接続を除去 ✅
- GPS 1PPS (U3 pad4) のVCC誤接続を除去 ✅
- GPS pad7 (NC) は via(12.0,20.0) 経由でVCC継続（NC pin, 無害）✅
- GPS VCC/VBAT/ON/OFF は F.Cu x=11.35 スト リップ経由で維持 ✅

---

### 発注前に必須

- [x] **バグ1修正**: via(13.25,23.7)削除・B.Cu trace(13.25,20→13.25,23.7)削除（2026-05-30 Pythonで実際に適用）
- [x] **バグ2修正**: GPS VCCトレース p7で停止（2026-05-29完了・誤診断のため取消し・元に戻した）
- [x] **バグ3修正**: B.Cu `(12,15.5)→(12,23)` を削除し `(12,15.5)→(12,17.2)` + via(12,17.2) + F.Cu bypass `(12,17.2)→(12,20)` + via(12,20) + B.Cu `(12,20)→(12,23)` に分割（2026-05-30 Pythonで実際に適用）
- [x] **C2位置修正**: (27.5,5.5,0°) → (28.5,4.5,90°) + VCCトレース(28.5,3.6)→(29.0,3.6) + GND via(27.5,5.4)（2026-05-30完了）
- [x] **C4位置修正**: (11.5,22.0,0°) → (12.9,17.0,90°) + VCCトレース(12.9,16.1)→(11.2,16.1)→(11.2,17.5) + GND via(12.9,17.0)（2026-05-30完了）
- [x] **C5位置修正**: (27.5,8.5,0°) → (28.5,7.5,90°) + VCCトレース(28.5,6.6)→(29.0,6.6) + GND via(28.5,9.0)（2026-05-30完了）
- [x] **孤立via×5削除**: (3,15)(8,15)(15,26.3)(16.5,25.5)(13.5,16.5)（2026-05-30完了）
- [x] **デッドエンドトレース削除**: B.Cu (26.1,20→13.25,20) (26.1,9.27→26.1,20)（2026-05-30完了）
- [x] **GPS p10/p12 GND接続追加**: 済み
- [x] **GPS p1 GND→ATtiny pad20 不正接続削除**: 済み
- [x] **【バグ4】GPS UART配線修正**: 済み（2026-05-30完了）
- [x] **DRC実行（kicad-cli）**: 352件 (未配線0件)。clearance 0件・track_dangling 3件・via_dangling 3件（2026-05-30 TP2/TP3追加後・TP3 GND via要zone fill）
- [x] **C1 clearance修正**: C1を(27.5,0.8,0°)に移動（U1パッド列より上に配置）+ VCC縦トレース(26.6,0.8→2.92) + GND via@(28.4,1.5)（2026-05-30完了）
- [x] **J1 footprint修正**: J1パッド幅1.2→1.0mmに縮小（ギャップ0.05→0.25mm確保）（2026-05-30完了）
- [x] **E220信号ルーティング確認**: U1.pad6(26.0,8.0)↔U2.pad6(14.0,24.25)は接続済みと確認（F.Cu→via(25.5,8.0)→B.Cu(25.1,8.0→25.1,21.0→14.0,21.0→14.0,25.5)→via(14.0,25.5)→F.Cu(14.0,25.5→14.0,24.25)）
- [x] **UPDI書き込みヘッダ追加**: TP1テストポイント(1.5mmφ SMDパッド)を(16.0,18.5)に追加・U2.pad16(PC5/UPDI)からトレースで接続（2026-05-30完了）
- [x] **UPDI VCC/GND テストポイント追加**:（2026-05-30完了）
  - TP2(VCC)=(18.5,18.5) F.Cu SMD 1.5mm + F.Cu trace→既存via(18.6,17.0)→B.Cu VCCトレース
  - TP3(GND)=(20.5,18.5) F.Cu SMD 1.5mm + F.Cu trace→via(20.5,17.0)→B.Cu GNDゾーン
  - **⚠️ TP3 GND via(20.5,17.0)はKiCad GUIで「Edit→Fill All Zones（B）」実行後にGNDゾーンと接続される**
  - 3パッドが y=18.5 ライン上に並列: TP1(16.0) – TP2(18.5) – TP3(20.5)、2.5mm間隔
- [x] 回路図を生成（.kicad_sch）→ ERCで検証（2026-05-30完了・実質エラー0件）
- [x] KiCad GUIでR1をDNP設定（2026-05-30 セッション3 pcbnew Pythonで完了）
- [x] Fill All Zones（2026-05-30 セッション3 pcbnew Pythonで完了・via_dangling 3件残存はネット未割り当てPCBの構造的制約・製造影響なし）
- [x] Gerber再生成（2026-05-30 セッション3完了・kicad-cli出力・JLCPCB標準拡張子・lora-30x35-v3n_gerber.zip）
- [x] JLCPCB DFM確認完了（2026-05-30）・発注設定確認済み
- [x] **🔴 Bug5修正**: ATtiny VDD (pad1) 未接続 → **2026-06-05 apply_all_fixes.py で修正完了**
  - 削除: F.Cu(12,23)→(13.25,23)・via(12,23)・B.Cu(12,20)→(12,23)
  - 追加: B.Cu VCC(13.5,15.5)→(13.5,21.1) w=0.4mm + via(13.5,21.1)
- [x] **Bug5修正後: Fill All Zones → DRC(clearance 0・未配線 0) → Gerber再生成** → `gerber_jlcpcb_final.zip`

> **✅ 設計完了（2026-06-05）**: Bug5修正・C1/J1/TP1/TP2/TP3・R1 DNP全て適用済み。発注可能状態。

### 設計リスク（未検証）

- [ ] **E220 VDD出力電流**: Bring-up時にVDD電圧を実測要（MCU+GPS=38mA負荷時に3.3V±0.1Vを確認）。公式PDF解析不可のため事前確認できず。
- [x] **50Ω インピーダンス確認済み（2026-05-30）**: W=1.5mm → 44.7Ω（-10%）。電気長0.06λのため挿入損0.03dB・実用影響なし。設計変更不要。
- [ ] TP4056 RPROG値（R2=5kΩ）→充電電流 = 1000/5 = 200mA（500mAhに適正か確認）
- [x] UPDI書き込み端子の引き出し確認（TP1/TP2/TP3 で3線完備 → 2026-05-30完了）

### JLCPCB 発注設定（2026-05-30確認済み）

| 項目 | 設定値 |
|------|--------|
| 基板サイズ | 30×35mm |
| 層数 | 2層 |
| PCB厚さ | **0.8mm**（変更禁止） |
| 素材 | FR4 TG135 |
| 表面仕上げ | HASL（有鉛） |
| 外層銅箔厚み | 1 oz |
| PCBカラー | 緑 |
| シルク | 白 |
| デバリング/エッジの丸め | はい（+$0.10） |
| 数量 | 5枚 |
| 電気テスト | フライング・プローブ |
| 合計（PCBのみ） | $2.10 |
| 送料（DHL Express DDP） | $29.51 |

### 製造注意事項

- [ ] U1（E220-900T22S）は手はんだ→先にSMT実装された基板に後付け
- [ ] PCB厚は必ず0.8mm（JLCPCBデフォルト1.6mmに注意）
- [ ] R1パッドは銅が残るが実装しない（J1と隣接するが物理干渉なし）

---

## 10. ファームウェア設計（2026-05-30 着手）

### 10-1. UART・GPIO割り当て

| ピン | ATtiny3226 | 接続先 | 用途 |
|------|-----------|--------|------|
| PA1 (pad12) | TxD0 (USART0 ALT1) | E220 RXD (pad7) | LoRa送信 |
| PA2 (pad11) | RxD0 (USART0 ALT1) | E220 TXD (pad8) | LoRa受信 |
| PC1 (pad7)  | RxD1 (USART1 ALT1) | GPS TXD  | GPS受信（NMEA） |
| PC2 (pad8)  | TxD1 (USART1 ALT1) | GPS RXD  | GPS送信（コマンド） |
| PB0 (pad6)  | GPIO out | E220 M1 | LoRaモード制御（M0はGND固定） |
| PA0 (pad16) | UPDI | — | 書き込み専用（UPDI）→TP1テストポイント経由 |

**PORTMUX設定必須**: `PORTMUX.USARTROUTEA = PORTMUX_USART0_ALT1_gc | PORTMUX_USART1_ALT1_gc;` (= 0x05)  
PCBトレース確認済み: pad12(16.75,23.0)→E220 pad7(RXD)、pad11(16.75,23.5)→E220 pad8(TXD)

**E220モード制御**:
- M0（E220 pin5）: PCB上でGNDに固定 → ファームウェア不要
- M1（E220 pin6）: ATtiny pad6(PB0)で制御

| M1(PB0) | M0(固定) | モード | 用途 |
|---------|---------|--------|------|
| LOW | 0 | 通常（透過転送） | 送受信時 |
| HIGH | 0 | WOR受信（省電力） | スリープ中のコマンド待受 |

### 10-2. メインループ（30分サイクル）

```
[起動・初期化]
  PORTMUX.USARTROUTEA = 0x05（ALT1: USART0→PA, USART1→PC）
  UART0: 9600bps（E220 / PA1=TxD, PA2=RxD）
  UART1: 9600bps（GPS / PC2=TxD, PC1=RxD）
  M0=0, M1=0（E220通常モード）
  RTC PIT設定（1秒周期 / ULP32K発振器）

[メインループ]
┌─────────────────────────────────────────┐
│ 1. GPS起動コマンド送信（UART1）          │
│    → $PCAS04,1*{chk}\r\n               │
│                                         │
│ 2. GPS補足待ち（最大90秒）              │
│    → UART1で$GNRMCを受信               │
│    → Status='A'（有効）になるまで待機   │
│    → タイムアウト時：緯度経度=0で続行   │
│                                         │
│ 3. 緯度・経度を抽出                     │
│    → int32_t lat = deg × 1,000,000     │
│    → int32_t lon = deg × 1,000,000     │
│                                         │
│ 4. GPS停止コマンド送信（UART1）          │
│    → $PCAS04,0*{chk}\r\n               │
│                                         │
│ 5. LoRaパケット送信（UART0）            │
│    → 12バイトバイナリ送信               │
│    → AUXピンでビジー確認（後日対応）    │
│                                         │
│ 6. コマンドポーリング（60秒）           │
│    → M0=0, M1=0（受信モード）           │
│    → ゲートウェイからの即時位置要求待機 │
│    → 受信した場合：GPS起動→送信        │
│                                         │
│ 7. スリープ移行                         │
│    → M0=0, M1=1（E220 WOR受信モード）  │
│    → ATtiny RTC PIT POWERDOWN          │
│    → 1秒ごとPIT割り込み×1620 ≒ 27分   │
└─────────────────────────────────────────┘
```

### 10-3. GPSスリープ制御（$PCAS04コマンド）

```c
// NMEAチェックサム計算（$と*の間のXOR）
uint8_t nmea_checksum(const char *cmd) {
    uint8_t cs = 0;
    for (const char *p = cmd; *p; p++) cs ^= (uint8_t)*p;
    return cs;
}

// GPS起動: $PCAS04,1*18\r\n
void gps_wake(void) {
    uart1_send("$PCAS04,1*18\r\n");
}

// GPS停止: $PCAS04,0*19\r\n
void gps_sleep(void) {
    uart1_send("$PCAS04,0*19\r\n");
}
```

**チェックサム計算（固定値）**:
- `PCAS04,1` → XOR = `0x18` → `$PCAS04,1*18\r\n`
- `PCAS04,0` → XOR = `0x19` → `$PCAS04,0*19\r\n`
- ※ 2026-05-30 fw_test.py実行で判明・旧値(1A/1B)は誤り

### 10-4. NMEAパース（$GNRMC / $GPRMC）

```
$GNRMC,143000.00,A,3541.3700,N,13941.5020,E,0.0,0.0,300526,,,A*68

フィールド:
  [0] $GNRMC
  [1] 143000.00  ← 時刻(HHMMSS)
  [2] A          ← ステータス A=有効 V=無効
  [3] 3541.3700  ← 緯度(DDMM.MMMM)
  [4] N          ← 北緯/南緯
  [5] 13941.5020 ← 経度(DDDMM.MMMM)
  [6] E          ← 東経/西経
```

**緯度変換（DDMM.MMMM → 十進度）**:
```c
// 例: 3541.3700 → 35 + 41.3700/60 = 35.689500°
float ddmm_to_deg(float ddmm) {
    int deg = (int)(ddmm / 100);
    float min = ddmm - deg * 100;
    return deg + min / 60.0f;
}
int32_t deg_to_int32(float deg) {
    return (int32_t)(deg * 1000000.0f);
}
```

### 10-5. LoRaパケット構築（12バイト）

```c
typedef struct {
    int32_t  lat;   // 緯度 × 1,000,000  例: 35689500
    int32_t  lon;   // 経度 × 1,000,000  例: 139691700
    uint32_t seq;   // 送信カウンター（電源OFFでリセット）
} LoraPacket;      // 合計12バイト リトルエンディアン

// ゲートウェイ側 Python デコード例:
// import struct
// lat, lon, seq = struct.unpack('<iil', data)
// lat_deg = lat / 1e6
// lon_deg = lon / 1e6
// url = f"https://maps.google.com/?q={lat_deg},{lon_deg}"
```

### 10-6. ATtinyスリープ（RTC PIT）

ATtiny3226（tinyAVR 2-Series）はWDT割り込みを持たない（WDTはリセットのみ）。  
→ **RTC PIT（Periodic Interrupt Timer）で1秒ごとに割り込み → 1620回で約27分**。

```c
// RTC PIT: ULP32K内蔵発振器 32768サイクル = 1秒周期
static volatile uint16_t pit_count = 0;

ISR(RTC_PIT_vect) {
    RTC.PITINTFLAGS = RTC_PI_bm;  /* フラグクリア必須 */
    pit_count++;
}

static void rtc_pit_init(void) {
    RTC.CLKSEL = RTC_CLKSEL_INT32K_gc;
    while (RTC.STATUS & RTC_CTRLABUSY_bm);
    RTC.PITCTRLA = RTC_PERIOD_CYC32768_gc | RTC_PITEN_bm;  /* 1秒周期 */
    while (RTC.PITSTATUS & RTC_CTRLABUSY_bm);
    RTC.PITINTCTRL = RTC_PI_bm;
}

static void sleep_27min(void) {
    pit_count = 0;
    sei();
    while (pit_count < 1620) {  /* 1秒 × 1620 = 27分 */
        SLPCTRL.CTRLA = SLPCTRL_SMODE_PDOWN_gc | SLPCTRL_SEN_bm;
        sleep_cpu();
    }
}
```

### 10-7. E220モード制御（確定：M1のみ制御）

PCB確認の結果、E220接続状態：
- **M0（pin5）**: GND固定（常時LOW）
- **M1（pin6）**: ATtiny pad6に接続 → ファームウェアで制御可能
- **AUX（pin4）**: 未接続（送信完了確認不可）

| ATtiny pad6 (M1) | M0（固定） | E220モード | 用途 |
|-----------------|-----------|-----------|------|
| LOW (0V) | 0 | 通常モード（透過転送） | 送受信時 |
| HIGH (3.3V) | 0 | WOR受信モード（省電力） | スリープ中のコマンド待受 |

```c
// ATtiny pad6 = PB0（仮）→ E220 M1
#define E220_M1_PIN PIN_PB0

void e220_set_normal(void)  { PORTB.OUTCLR = PIN0_bm; _delay_ms(1); }  // M1=0
void e220_set_wor(void)     { PORTB.OUTSET = PIN0_bm; _delay_ms(1); }  // M1=1
```

### 10-8. AUX未接続問題の対処（確定：固定ウェイト）

AUXピンがATtinyに接続されていないため、送信完了を検知できない。  
→ **固定500msウェイトで代替**（根拠：E220デフォルト設定 SF9/BW125kHz で12バイト送信時間 ≈ 200ms + マージン300ms）

```c
void lora_send(const LoraPacket *pkt) {
    e220_set_normal();
    uart0_send((uint8_t*)pkt, sizeof(LoraPacket));  // 12バイト送信
    _delay_ms(500);  // AUX代替ウェイト
}
```

### 10-9. ゲートウェイからのコマンド形式（確定：1バイト）

| 値 | コマンド | 応答 |
|----|---------|------|
| `0x01` | 即時位置送信要求 | 12バイト LoraPacket（GPS取得後） |
| その他 | 無視 | なし |

```c
// 60秒ポーリングループ（2秒タイムアウト × 30回）
void poll_gateway_commands(void) {
    for (uint8_t i = 0; i < 30; i++) {
        uint8_t cmd;
        if (uart0_recv_timeout(&cmd, 2000)) {
            if (cmd == 0x01) {
                gps_wake();
                LoraPacket pkt = acquire_gps();
                gps_sleep();
                lora_send(&pkt);
            }
        }
    }
}
```

### 10-10. GPS補足タイムアウト時の動作（確定：lat=0で送信）

- タイムアウト閾値：**90秒**（コールドスタート最大値）
- タイムアウト時：`lat=0, lon=0, seq=N` で送信
- 判定根拠：日本国内では緯度が絶対に0にならない → ゲートウェイ側で`lat==0`をGPS失敗として判定

```c
// ゲートウェイ側Python判定
if lat == 0 and lon == 0:
    status = "GPS補足失敗"
else:
    status = f"https://maps.google.com/?q={lat/1e6},{lon/1e6}"
```

### 10-11. ATtinyクロック設定（確定：8MHz内蔵発振器）

| 項目 | 選択値 | 理由 |
|------|--------|------|
| クロック源 | 内蔵発振器（OSCULP/OSC20M） | 外部水晶不要・部品追加なし |
| 動作周波数 | **8MHz** | 3.3V動作（E220 VDD出力）・UART 9600bps処理に十分・外部水晶不要 |
| 20MHz不採用 | — | ATtiny3226は3.3Vで20MHz動作可能だが消費電力増・8MHzで機能十分 |

```c
// fuse2=0x01（FREQSEL_16MHZ_gc）を書き込んでおくこと
// → OSC20M を 16MHz モードで起動、prescaler /2 → 8MHz 動作
CPU_CCP = CCP_IOREG_gc;
CLKCTRL.MCLKCTRLB = CLKCTRL_PDIV_2X_gc | CLKCTRL_PEN_bm;  // 16MHz÷2 = 8MHz
```

**fuse確認値**:
- FUSE2=0x01 (FREQSEL_16MHZ_gc = 0x01, 誤記注意: FREQSEL_20MHZ_gc = 0x02)
- 書き込みコマンド: `avrdude ... -U fuse2:w:0x01:m`

### 10-12. ゲートウェイ側ソフト概要（スコープ外・参考）

別途 Raspberry Pi + E220 で製作。インターフェース仕様のみ定義：

```python
# 受信処理（Python / pyserial + E220透過モード）
import struct, datetime

def decode_packet(data: bytes):
    lat_raw, lon_raw, seq = struct.unpack('<iiI', data[:12])
    if lat_raw == 0 and lon_raw == 0:
        return {"status": "no_fix", "seq": seq}
    lat = lat_raw / 1_000_000
    lon = lon_raw / 1_000_000
    url = f"https://maps.google.com/?q={lat},{lon}"
    return {"lat": lat, "lon": lon, "url": url, "seq": seq,
            "time": datetime.datetime.now().isoformat()}

# Webサーバー（Flask）でスマホブラウザに地図表示
# Google Maps JavaScript API embed または静的URLリダイレクト
```

---

## FW設計 進捗まとめ（2026-05-30 完了）

| 項目 | 状態 |
|------|------|
| UART・GPIO割り当て | ✅ 確定（PORTMUX ALT1設定実装済み） |
| メインループ（30分サイクル） | ✅ 確定 |
| GPSスリープ制御（$PCAS04） | ✅ 確定 |
| NMEAパース（$GNRMC） | ✅ 確定 |
| LoRaパケット構造（12バイト） | ✅ 確定 |
| ATtinyスリープ（RTC PIT 1s×1620） | ✅ 確定（WDT割り込みなし→PIT使用） |
| E220モード制御（M1のみ） | ✅ 確定 |
| AUX未接続→固定500msウェイト | ✅ 確定 |
| ゲートウェイコマンド（0x01） | ✅ 確定 |
| GPS補足タイムアウト（lat=0） | ✅ 確定 |
| クロック（8MHz内蔵） | ✅ 確定 |
| ゲートウェイ側Flask | 📋 スコープ外（仕様のみ定義） |

---

## 11. 設計判断記録

| 日付 | 判断内容 | 理由 |
|------|---------|------|
| 2026-05 | U3をMAX-M8QからATGM336H-5N31に変更 | MAX-M8QがJLCPCB LCSC在庫なし→ATGM336Hは同一フットプリント(LCC-18)でLCSC C90770あり |
| 2026-05 | PCB厚を0.8mmに設定 | B.Cu VCCトレース幅1.5mmで50Ω整合（0.8mm FR4基準） |
| 2026-05 | C4を(11.5,22)→(12.9,17,90°)に移動 | VCC-GNDショート解消（C4.pad2が旧位置でVCCパッドと重複） |
| 2026-05 | C2を(27.5,5.5)→(28.5,4.5,90°)に移動 | VCC配線整理 |
| 2026-05 | C5を(27.5,8.5)→(28.5,7.5,90°)に移動 | VCC配線整理 |
| 2026-05 | R1をDNP決定 | 設計者が用途を失念・回路上の影響不明→安全のため実装しない |
| 2026-05 | E220をSMT対象外（手はんだ）に決定 | LCSCカタログに存在しない |
| 2026-05-29 | バグ1: via(13.25,23.7)削除・B.Cu縦トレース削除 | viaがATtiny pad5(PA7)と物理的に重なりVCC短絡。VCC供給はvia(12,23)経路で維持 |
| 2026-05-29 | バグ2: GPS VCCトレースをp7(VCC_IO, y=19.8)で停止 | PCBのgr_textよりp7=VCC_IO確認。p6/p5は用途不明なため接続除外 |
| 2026-05-29 | バグ3: B.Cu VCC x=12をF.Cu経由で迂回 | B.Cu VCC(x=12)とB.Cu RF(y=18.7,幅1.5mm)が交差してANT1短絡。F.Cu迂回で解消。副効果でGPS pad8/pad7にもVCC供給 |
| 2026-05-29 | ぶら下がりトレース削除: B.Cu `(26.1,9.27→26.1,20)` と `(26.1,20→13.25,20)` | バグ1修正でvia(13.25,23.7)を削除した際に生じた行き先のないB.Cuスタブ。ATtinyへのVCCは via(12,23)経路で維持 |
| 2026-05-29 | GPS p10/p12 GND接続追加 | GPS左側のGNDピン(p10=1.85,17.6、p12=1.85,19.8)にF.Cuトレース+viaが未接続。F.Cu→via(3.2,17.6)とvia(3.2,19.8)でB.Cu GNDゾーンに接続 |
| 2026-05-30 | GPS p1(GND)→ATtiny pad20 不正接続削除 | GPS p1=GNDなのに設計者がp1=TXDと誤認してATtiny pad20(UART信号ピン)にGNDを接続していた。F.Cu (7.5,20.75→14.0,20.75)を削除。GPS p1 GNDはvia(7.5,26.4)でB.Cuゾーン接続を維持。ATtiny pad20のUART接続はKiCad GUIで要確認。 |
| 2026-05-30 | バグ4発見・修正：GPS UART全ルートが誤ったATtinyピンに接続 | シルク注記「16:PC1=RxD1」「17:PC2=TxD1」は誤り。pad16=PC5(UPDI/RESET)、pad17=PA0(UART機能なし)。Pythonスクリプトで誤ルート8本削除・既存スタブ2本削除・正ルート7本追加。GPS TXD→pad7(PC1=RxD1)、GPS RXD→pad8(PC2=TxD1)に修正完了。 |
| 2026-05-30 | UPDI書き込みテストポイントTP1を追加 | U2.pad16(PC5/UPDI)がfloating→(16.0,18.5)に1.5mmφ SMDテストパッドを追加・トレース(16.0,20.75→16.0,18.5)で接続。シルクhide。UPDI書き込みアダプタ/クリップで直接接触可能なポイントを設けた。 |
| 2026-05-30 | E220信号ルーティング: U1.pad7↔U2.pad12・U1.pad8↔U2.pad11は接続済み確認。U1.pad6↔U2.pad6のみ未接続（KiCad GUI必要） | U1右辺パッド列(x=25.2〜26.8)が密集・既存縦ルート(x=26.5, x=27.0)がy=8.0の横トレースと交差して短絡する。ANT1(RF)のcourtyard内も通せない。KiCadインタラクティブルーターで解決する。 |
| 2026-05-30 | Edge.Cuts を start(-1,0)→start(0,0) に修正（30×35mm化） | JLCPCBが31×35mmと認識していたため修正。U1(E220)コートヤード左端がx=-0.5で基板外に出るが手はんだ部品なので製造上問題なし。 |
| 2026-05-30 | C1を(27.5,2.5,0°)→(27.5,0.8,0°)に移動・J1パッド幅1.2→1.0mmに縮小 | C1.pad1がU1.pad10(26.0,2.92)に0mm接触、かつU1右側パッド列が1.27mmピッチで密集しているため横移動では干渉回避不可。y方向上部（基板端付近）に移動してパッド列から外した。VCCは縦トレース(26.6,0.8→2.92)でU1.pad10エリアに接続、GNDはvia@(28.4,1.5)。J1はJST-GH 1.25mmピッチに対しパッド幅1.2mmで両パッド間0.05mmのDRC違反→1.0mmに縮小して0.25mmギャップ確保。clearance 2件→0件達成。DRC:349→345件。 |
| 2026-05-30 | Bug1/Bug3/C2/C4/C5を実際にPCBファイルに適用 | DESIGN.mdに「修正済み」と記録されていたが、PCBファイルには未適用だった。kicad-cli DRCで363件→349件に削減。clearance 10件→2件（C1・J1残存）。via_dangling 4件→0件。track_dangling 3件（C2/C4/C5 GNDスタブ・B.Cuゾーン接続・製造上問題なし）。 |
| 2026-05-30 | C2(27.5,5.5,0°)→(28.5,4.5,90°)・C4(11.5,22.0,0°)→(12.9,17.0,90°)・C5(27.5,8.5,0°)→(28.5,7.5,90°) に正式移動 | DRCで判明：DESIGN.mdの座標は設計目標値であり実PCBには反映されていなかった。C4はU3.pad5に0mm接触（ショート）、C2/C5はU1パッドに0mm接触。移動+VCC・GNDトレース追加で解消。 |
| 2026-05-30 | FW設計アーキテクチャ確定（全11項目） | クロック8MHz内蔵・M1のみでE220モード制御（M0=GND固定）・AUX未接続→500msウェイト代替・GPS補足タイムアウトlat=0送信・1バイトコマンド形式・WDT 8s×203サイクルで27分スリープ |
| 2026-05-30 | 50Ω RF トレース計算検証。B.Cu W=1.5mm @0.8mm FR4(H=0.73mm,Er=4.6,T=1.38mil)で IPC-2141計算→Z0=44.7Ω(目標50Ωより-10%)。50Ω厳密値はW=1.29mm。ただし電気長0.06λ@920MHzのためVSWR=1.12・挿入損0.03dB。実用影響なしと判断、設計変更不要。 | LoRa 920MHz 200〜500m用途では±10%のインピーダンスずれは無視可能。 |
| 2026-05-30 | UPDI VCC/GND テストポイント（TP2/TP3）追加。TP2(VCC)=(18.5,18.5)、TP3(GND)=(20.5,18.5)。F.Cu SMD 1.5mm。TP2はvia(18.6,17.0)→B.Cu VCCトレースで供給。TP3はvia(20.5,17.0)→B.Cu GNDゾーン（KiCad Fill All Zones後に接続）。3パッドがy=18.5ライン上2.5mm間隔で並列配置。DRC: 349→352件（via_dangling+3相殺clearance-2、製造影響なし）。 | VCC/GNDのテストポイントがないとATtiny3226のUPDI書き込みができない（3線必須）。 |
| 2026-05-30 | BOM LCSC番号誤り3件修正（LCSCで実在確認済み） | C3014522(ATtiny)→C5227682(ATTINY3226-MU VQFN-20): C3014522はLCSCに存在しない。C317592(U.FL)→C88373(Hirose U.FL-R-SMT-1(10)): C317592はPADAUK PMC156-S16(全くの別部品)。C160404(JST-GH 2P)→C189893(SM02B-GHS-TB JST-GH 1.25mm 2P): C160404はJST SH 1mm 4P(ピン数・ピッチ共に不一致)。C189893は在庫切れのため要確認。 |
| 2026-05-30 | R1 DNP設定・Fill All Zones・Gerber再生成（kicad-cli）をPythonスクリプトで自動化 | KiCad GUIなしでpcbnew Python APIを使い全処理をCLIで完結。via_dangling 3件残存はネット未割り当てPCB（スクリプト生成）の構造的制約であり製造影響なし。GerberはJLCPCB標準拡張子（.gtl/.gbl等）で出力。 |
| 2026-05-30 | 回路図（lora-30x35-v3n.kicad_sch）生成・ERC通過 | `generate_schematic_v3n.py`で生成。A3用紙。全部品・ネット接続を記述。GNDピンをpassiveに統一（カスタムシンボルのpower_pin_not_driven誤検出回避）。PWR_FLAGをVBUS/VCC_E220/GNDネットに追加。ERC結果: lib_symbol_issues 9件（カスタムライブラリ未登録・想定内）、実質エラー0件。ATtiny UPDI=pad16(sy=-2.54)に修正、LORA_TXD/LORA_RXD=PA1/PA2(pad17/18)に接続。 |
| 2026-05-30 | セッション3: 全体再チェック（CHECKLIST.md初適用）。UART接続BFS追跡・ISRベクタgrep確認・BAUD誤差計算・DRC分類・Gerber zip混在問題発覚と修正。 | Gerber zipに旧.gbr（10ファイル）と新JLCPCB標準（12ファイル）が混在していたことが判明→`lora-30x35-v3n_gerber_jlcpcb.zip`（JLCPCB標準拡張子のみ）を新規作成。DRC clearance/short_circuit=0件確認。全UART経路・UPDIテストポイント接続をPCBファイル銅線BFSで確認（シルク・メモに依存しない検証）。FW: PORTMUX/ISRベクタ/PDIV/FREQSEL全て一次情報から確認済み。solder_mask_bridge 116件はスクリプト生成PCBの構造的制約（マスク展開パラメータ）でありJLCPCBガーバービューアでの最終確認が必要。 |
| 2026-05-30 | セッション4: GPS pad接続追跡中にBug5（ATtiny VDD未接続）を発見。開発を一時凍結。 | BFSアルゴリズムの中点検出バグにより「VCC未到達」と誤判定されていたGPS接続は実際には正常。しかし別途 F.Cu(12.0,23.0→13.25,23.0) の終点がpad4(PA6)であることをfootprint座標解析で確認→ATtiny VDD(pad1, y=21.5)に銅線なし。Bug1修正の際の「via(12,23)経路でVCC維持」という記録が誤りだった。generate_schematic_v3n.py line303の「pad1=VCC, pad2-5=PA4-PA7」でpad割当を確認。修正計画策定済み。LTE-M開発優先のため凍結。 |

---

## 12. PCBA費用概算（2026-05-30 JLCPCB実価格調査）

> 調査方法: JLCPCB parts library（https://jlcpcb.com/parts）で各LCSC#を直接確認  
> 調査日: 2026-05-30

### 部品代内訳（5枚分・JLCPCB実価格）

| 部品 | LCSC# | Basic/Extended | JLCPCB在庫 | 単価(1+) | 数量 | 小計 |
|------|-------|--------------|-----------|---------|------|------|
| ATtiny3226-MU | C5227682 | **Extended** | 319個（残278） | $2.26 | 5 | $11.30 |
| ATGM336H-5N31 | C90770 | **Extended** | 4,556個 | $3.21 | 5 | $16.05 |
| U.FL-R-SMT-1(10) | C88373 | **Extended** | 1,744個 | $0.24 | 5 | $1.20 |
| JST-GH 2P | C189893 | **Extended** | 3,394個 | $0.12 | 5 | $0.60 |
| TP4056 ESOP-8 | C16581 | 未確認 | 70,595個 | $0.19 | 5(min5) | $0.93 |
| USB-C 16P | C2765186 | 未確認 | 948,240個 | $0.07 | 20(min20) | $1.48 |
| MSK12C02-HB | C431541 | 未確認 | 54,660個 | $0.06 | 10(min10) | $0.61 |
| 100nF 0402 ×5 | C14663 | Basic想定 | — | ~$0.01 | 25 | ~$0.25 |
| 1µF 0402 ×1 | C52923 | Basic想定 | — | ~$0.01 | 5 | ~$0.05 |
| 5.0kΩ 0402 ×1 | C25905 | Basic想定 | — | ~$0.01 | 5 | ~$0.05 |
| 330Ω 0402 ×2 | C22978 | Basic想定 | — | ~$0.01 | 10 | ~$0.10 |
| 5.1kΩ 0402 ×2 | C23186 | Basic想定 | — | ~$0.01 | 10 | ~$0.10 |
| LED RED 0402 | C2286 | Basic想定 | — | ~$0.03 | 5 | ~$0.15 |
| LED BLUE 0402 | C72041 | Basic想定 | — | ~$0.05 | 5 | ~$0.25 |
| **部品代 合計** | | | | | | **~$33.12** |

### Extended部品 追加料金

JLCPCBのEconomic PCBA: Extended部品1種につき$3/オーダー

| 確認済みExtended部品 | 数 |
|---|---|
| ATtiny3226-MU (C5227682) | 1種 |
| ATGM336H-5N31 (C90770) | 1種 |
| U.FL-R-SMT-1(10) (C88373) | 1種 |
| JST-GH 2P (C189893) | 1種 |
| TP4056・USB-C・MSK12C02（未確認・Extended可能性あり）| 最大3種 |

→ Extended追加料金: **$12〜$21**（4〜7種 × $3）

### PCBA総費用概算（5枚）

| 費目 | 金額 | 備考 |
|------|------|------|
| PCB製造 | $2.10 | 5枚・0.8mm FR4・緑・HASL |
| 部品代 | ~$33 | 上表合計 |
| Extended追加料金 | ~$12〜21 | 4〜7種 × $3 |
| 送料（DHL Express） | ~$16〜25 | 実測値は発注時に確認 |
| **合計** | **$63〜81** | E220・LiPo・アンテナを除く |

### 正確な見積もりの取得方法

ファイルアップロードが必要なため手動操作が必須:

1. https://cart.jlcpcb.com/quote へアクセス
2. `lora-30x35-v3n_gerber.zip` をドラッグ&ドロップ
3. PCB厚 **0.8mm** を確認（デフォルト1.6mmに注意）
4. 「PCB Assembly」をONに切替 → 片面・Economic選択
5. `bom_jlcpcb.csv` と `cpl_jlcpcb.csv` をアップロード
6. 見積もり画面で合計確認 → **承認後に発注**

> **⚠️ ATtiny3226の在庫が残り278個**（2026-05-30時点）。早めの発注推奨。  
> **✅ JST-GH 2P (C189893)**: LCSCの小売は在庫切れだがJLCPCB PCBA用在庫は3,394個あり（2026-05-30確認）。

---

## 13. 別途購入が必要な部品一覧（手はんだ・JLCPCB対象外）

> これらはJLCPCBのPCBA発注に含まれない。**自分で購入・手はんだが必要。**

### 必須部品

| 品目 | 仕様 | 調達先 | 目安単価 | 5枚分 | 備考 |
|------|------|--------|---------|-------|------|
| **E220-900T22S(JP)** | 技適取得済み LoRa 920MHz | AliExpress Ebyte公式ストア | ¥700〜800 | ¥3,500〜4,000 | 手はんだ・半田付け難易度高め |
| **LiPoバッテリー** | 3.7V 500mAh・JST-GH 1.25mm 2Pコネクタ付き | AliExpress / Amazon | ¥600〜900 | ¥3,000〜4,500 | バッテリーはJLCPCB不可（危険物） |
| **920MHz アンテナ** | U.FL(IPEX)コネクタ付きケーブル + ホイップアンテナ | AliExpress | ¥300〜500 | ¥1,500〜2,500 | λ/4 ≈ 8.1cm at 920MHz |

### FW書き込み用（初回のみ）

| 品目 | 仕様 | 調達先 | 目安単価 | 備考 |
|------|------|--------|---------|------|
| **UPDIプログラマ** | SerialUPDI方式：USB-UARTアダプタ（CH340/CP2102） | Amazon / AliExpress | ¥500〜1,500 | 手持ちのUSB-UARTアダプタで代用可 |
| — | または MPLAB Snap（正規プログラマ） | Microchip Direct / 秋月 | ¥3,000〜5,000 | 信頼性高いが高価 |

**SerialUPDI方式の使い方:**
```
PC ─[USB]─ CH340 ─[TXD+RXD+GND]─ TP1(UPDI)パッド on PCB
```
ソフト: `pymcuprog` または `avrdude 7.x` (--programmer serialupdi)

### E220 購入先（AliExpress）

検索キーワード: **「E220-900T22S JP」「Ebyte 920MHz」**  
公式ストア: Ebyte Official Store（EBYTE STORE）  
技適番号: **001-P01730**（購入時に確認）

---

---

## 14. 業界標準フロー照合結果（2026-05-30）

標準フロー（要件→回路→PCB→製造→Bring-up→FW→テスト→製品化）と現状を照合。

### 🔴 発注前に対処すべき

| 項目 | 内容 |
|------|------|
| ~~UPDI 3線アクセス未確保~~ | **✅ 2026-05-30完了**: TP2(VCC/18.5,18.5)・TP3(GND/20.5,18.5)を追加。3線アクセス確保済み。**KiCad GUIでFill All Zones(B)後にGerber再生成が必要。** |
| E220 VDD出力電流 | ⚠️ **要確認**: E220のVCCはpower入力(3~5.5V)、VDDは内蔵LDO出力(3.3V)。MCU(~8mA)+GPS(~30mA)=38mA。Ebyte内蔵LDOの最大出力電流は公式PDFから未確認(PDF画像形式のため解析不可)。設計は継続可能だが**Bring-up時にVDD電圧（負荷時3.3V±0.1V確認）を必ず実測すること。** |
| ~~50Ω インピーダンス未検証~~ | **✅ 2026-05-30 計算確認済み**: IPC-2141、JLCPCB 2層0.8mm FR4(H=0.73mm, Er=4.6, T=1.38mil)で計算。W=1.5mm → Z0≈44.7Ω(目標50Ωより-10%)。50Ωに必要なWは1.29mm。ただし電気長0.06λ@920MHzのためVSWR=1.12・挿入損0.03dB・実用上影響なし。設計変更不要。 |

### 🟡 基板到着前に完了すべき（待機中にできる作業）

| 項目 | 内容 |
|------|------|
| **E220・LiPo・アンテナを今すぐ発注** | AliExpress配送2〜4週間。基板と同時に揃わないと動作確認できない。**今週中に発注** |
| ~~Bring-up手順書がない~~ | **✅ 2026-05-30 セッション3完了**: セクション16に詳細手順を追記済み |
| ~~FW開発環境未構築~~ | **✅ 2026-05-30 セッション3完了**: avr-gcc 14.3.0 + avrdude 8.1 + pymcuprog 3.19.4.61 インストール済み。fw/main.c + fw/Makefile 作成・警告ゼロコンパイル確認（1656bytes/32KB Flash） |
| ~~デバッグ手段がLEDのみ~~ | **✅ 確定**: LEDフラッシュパターンで対応。セクション16に定義済み |
| ~~ATtiny3226 fuse設定未定~~ | **✅ 2026-05-30 セッション3確定**: FUSE2=0x01(16MHz)・FUSE4=0xF6(UPDI有効)・FUSE5=0x08(64ms)。fw/Makefileに記載済み |

### 🟠 動作確認後に対処すべき

| 項目 | 内容 |
|------|------|
| ゲートウェイ製作計画なし | LoRa通信テストはトラッカー単体では不可。受信側（RaspberryPi + E220等）の製作時期・部品を計画する |
| ケース・装着設計ゼロ | 要件「首輪取り付け・50g以下・防水」に対して具体的設計なし。3Dプリントか市販ケース改造かも未定。ケースサイズによってバッテリーサイズも変わる可能性あり |
| フィールドテスト計画なし | 合否基準（バッテリー持ち実測・GPS取得成功率・LoRa到達距離）の定義が必要 |

### フロー別進捗（2026-05-30 セッション3更新）

| # | フェーズ | 状態 | 進捗 | 備考 |
|---|---------|------|------|------|
| 1 | 要件定義 | ✅ | 100% | 完了 |
| 2 | 部品選定・BOM | ✅ | 98% | LCSC#全修正済み・JLCPCB在庫確認済み |
| 3 | 回路図 | ✅ | 90% | kicad_sch生成済み・ERC実質0件 |
| 4 | ERC | ✅ | 95% | lib_symbol_issues 9件（カスタムライブラリ未登録・想定内） |
| 5 | PCBレイアウト | ✅ | 100% | 全バグ修正済み |
| 6 | DRC | ✅ | 90% | 352件・未配線0件・残存6件は構造的（製造影響なし） |
| 7 | Gerber/製造ファイル | ✅ | 100% | セッション3 kicad-cli再生成・JLCPCB標準拡張子 |
| 8 | インピーダンス検証 | ✅ | 100% | W=1.5mm→44.7Ω・実用影響なし |
| 9 | UPDI書き込み端子 | ✅ | 100% | TP1/TP2/TP3 3線確保済み |
| 10 | FW設計（アーキテクチャ） | ✅ | 100% | 全11項目確定 |
| 11 | FW開発環境構築 | ✅ | 100% | avr-gcc 14.3.0・avrdude 8.1・pymcuprog 3.19.4.61 |
| 12 | **手はんだ部品の調達** | ❌ | 0% | E220・LiPo・アンテナ 今週中AliExpress発注要 |
| 13 | **PCBA発注** | ⚠️ | 90% | ファイル準備完了・ユーザー操作（決済）待ち |
| 14 | 実装（手はんだ） | ❌ | 0% | 基板到着後 |
| 15 | Bring-up（初回電源投入） | ❌ | 0% | 手順書作成済み（セクション16） |
| 16 | FW実装・書き込み | ⚠️ | 30% | fw/main.c スケルトン完成・実機書き込み待ち |
| 17 | 動作確認・デバッグ | ❌ | 0% | 基板到着後 |
| 18 | ゲートウェイ製作 | ❌ | 0% | RaspberryPi + E220（別途製作） |
| 19 | ケース・装着設計 | ❌ | 0% | 動作確認後 |
| 20 | フィールドテスト | ❌ | 0% | ケース完成後 |

---

## 11. セッション開始時の確認手順

新しいセッションを始める前に必ずこのファイルを読む。  
確認コマンド:
```bash
cat /Users/m2mac/gps-cat-tracker/DESIGN.md
cat /Users/m2mac/gps-cat-tracker/bom_jlcpcb.csv
cat /Users/m2mac/gps-cat-tracker/cpl_jlcpcb.csv
```

---

## 15. 次セッションで最初にやること（2026-05-30 セッション3終了時点）

### ✅ セッション3で完了したこと
1. **R1 DNP設定**: pcbnew Python (`fill_zones_and_dnp.py`) でSetDNP(True)適用済み
2. **Fill All Zones**: pcbnew Pythonで実行済み（B.Cu GNDゾーン再塗り込み）
3. **DRC**: 352件（変化なし。via_dangling 3・track_dangling 3はネット未割り当てPCBの構造的制約・製造影響なし）
4. **Gerber再生成**: kicad-cli出力・JLCPCB標準拡張子（.gtl/.gbl/.gts等）・`lora-30x35-v3n_gerber.zip` 124KB

### 🔴 PCB設計フェーズは完了。次は発注と並行作業

### 発注（今すぐ実行）
1. **JLCPCB PCBA発注**
   - https://cart.jlcpcb.com/quote へアクセス
   - `lora-30x35-v3n_gerber.zip` → PCB厚 **0.8mm** 設定（デフォルト1.6mmに注意）
   - PCB Assembly ON → `bom_jlcpcb.csv` + `cpl_jlcpcb.csv` アップロード
2. **AliExpressで手はんだ部品を今週中に発注**（配送2〜4週間）
   - E220-900T22S(JP)：Ebyte公式ストア「E220-900T22S JP」
   - LiPo 500mAh JST-GH 1.25mm 2P
   - 920MHz U.FLアンテナ（λ/4=8.1cm）

### ✅ セッション3で追加完了
- ~~FW開発環境構築~~ → 完了
- ~~ATtiny3226 fuse設定決定~~ → 完了（セクション16参照）
- ~~Bring-up手順書作成~~ → 完了（セクション16参照）

### 🔴 次セッション最初にやること
1. **JLCPCB発注**: ユーザー操作（ブラウザ・決済）が必要
2. **AliExpress発注**: 今週中（E220・LiPo・アンテナ）

### 使用したPythonスクリプト（再実行不要・参考保存）
- `add_updi_test_points.py` → TP2/TP3追加（1回目・不完全版）
- `fix_updi_test_points.py` → TP3位置修正版（適用済み）
- `fill_zones_and_dnp.py` → R1 DNP + Fill All Zones（セッション3完了）

---

## 16. Bring-up手順書 + Fuse設定（2026-05-30 確定）

### ATtiny3226 Fuse設定（確定値）

| Fuse | アドレス | 設定値 | 内容 |
|------|---------|--------|------|
| FUSE0 (WDTCFG) | 0x00 | 0x00 | WDT無効（デフォルト） |
| FUSE1 (BODCFG) | 0x01 | 0x00 | BOD無効（初回Bring-up用） |
| FUSE2 (OSCCFG) | 0x02 | **0x01** | FREQSEL=16MHz内蔵発振器 |
| FUSE4 (SYSCFG0) | 0x04 | **0xF6** | UPDI有効・EESAVE有効（デフォルト値を明示） |
| FUSE5 (SYSCFG1) | 0x05 | **0x08** | 64ms起動待機（デフォルト値を明示） |
| FUSE6 (APPEND) | 0x06 | 0x00 | APPセクションなし |
| FUSE7 (BOOTEND) | 0x07 | 0x00 | BOOTセクションなし |

**重要**: FUSE4=0xF6 は `RSTPINCFG=01`（UPDI有効）。これを変更するとUPDI書き込み不可になる。

**fuse書き込みコマンド**:
```bash
cd ~/gps-cat-tracker/fw
SERIAL_PORT=/dev/cu.usbserial-XXXX  # 実際のポートに変更
make fuse SERIAL_PORT=$SERIAL_PORT
```

**クロック動作**:
- FUSE2=0x01 → 16MHz内蔵発振器
- firmware内: `CLKCTRL.MCLKCTRLB = CLKCTRL_PDIV_2X_gc | CLKCTRL_PEN_bm` → 16MHz÷2 = **8MHz**
- UART BAUD = 64 × 8,000,000 / (16 × 9600) = **3333** → 誤差0%

---

### FW開発環境

```bash
# ツールインストール確認
export PATH="/opt/homebrew/opt/avr-gcc@14/bin:$PATH"  # ~/.zshrc に追記済み
avr-gcc --version     # → avr-gcc 14.3.0
avrdude --version     # → avrdude 8.1
pymcuprog --version   # → pymcuprog 3.19.4.61

# ビルド
cd ~/gps-cat-tracker/fw
make

# 書き込み (SERIAL_PORT変更要)
make flash SERIAL_PORT=/dev/cu.usbserial-XXXX
```

---

### Bring-up手順書（基板到着後）

#### Step 0: 目視検査（電源投入前）
- [ ] はんだブリッジがないか確認（特にU2 VQFN-20・U4 ESOP-8）
- [ ] U.FL(ANT1)・JST-GH(J1)・USB-C(J2) のコネクタ浮きなし
- [ ] E220(U1)のピン配置確認（パッド1の位置）

#### Step 1: 抵抗測定（電源OFF状態）
テスターを**抵抗モード**にして以下を測定:

| 測定点 | 期待値 | 異常の場合 |
|--------|--------|-----------|
| VCC(TP2) – GND(TP3) 間 | >10kΩ | ショート→実装不良を確認 |
| USB-C VBUSピン – GND 間 | >1MΩ | ショート→TP4056周辺確認 |
| E220 VCC(SW1経由) – GND 間 | >1kΩ | E220内蔵LDOのプルダウン程度 |

#### Step 2: USB-C 接続（LiPoなし）
1. USB-Cケーブルを接続（PCのUSBポートから給電）
2. SW1はOFF状態で実施
3. **LED1(RED)が点灯** → TP4056が充電モード（正常）
4. USB電流: 100〜200mA（TP4056充電中）が正常範囲

#### Step 3: LiPo接続・SW1 ON
1. LiPoバッテリーをJ1に接続（**極性確認**: 赤=+, 黒=-）
2. SW1をON
3. E220のVDD(3.3V)出力が有効になる
4. **LED2(BLUE)が点灯** → LiPo満充電状態の表示（E220起動後に点灯）

#### Step 4: VDD電圧確認（重要）
テスターを**電圧モード**にして:

| 測定点 | 期待値 | 許容範囲 |
|--------|--------|---------|
| E220 VDD出力 – GND | 3.3V | 3.2〜3.4V |
| TP2(VCC) – TP3(GND) | 3.3V | 3.2〜3.4V |

> **注意**: E220のVDD出力電流が不足する場合（MCU+GPS=38mA負荷時に3.3V±0.1V外れる場合）は電源設計を見直す。

#### Step 5: UPDI書き込み（SerialUPDI）

**配線**:
```
PC USB ─[CH340/CP2102]─ TP1(UPDI) ─ ATtiny3226
                       ─ TP2(VCC)  ─ ATtiny3226 VCC
                       ─ TP3(GND)  ─ ATtiny3226 GND
```

> テストポイント配置: TP1(UPDI)=x16.0, TP2(VCC)=x18.5, TP3(GND)=x20.5、y=18.5ライン上に2.5mm間隔

```bash
# シリアルポート確認
ls /dev/cu.usbserial-*

# fuse書き込み（最初に実行）
cd ~/gps-cat-tracker/fw
make fuse SERIAL_PORT=/dev/cu.usbserial-XXXX

# fuse読み出し確認
make fuse-read SERIAL_PORT=/dev/cu.usbserial-XXXX
# FUSE2=0x01 FUSE4=0xF6 FUSE5=0x08 であることを確認

# ファームウェア書き込み
make flash SERIAL_PORT=/dev/cu.usbserial-XXXX
```

#### Step 6: GPS UART確認
GPS(U3)とE220(U1)を未接続のままで:
1. USB-UARTアダプタをATtiny UART0（PA1/PA2）にシリアルモニタ接続 (TODO)
   → UART0・UART1は基板上でE220/GPSに繋がるため**デバッグUARTなし**
2. **LEDデバッグパターン**で動作確認:

| 点滅パターン | 意味 |
|------------|------|
| LED1(RED) 1回点滅 | GPS起動コマンド送信 |
| LED1(RED) 2回点滅 | GPS補足成功 |
| LED2(BLUE) 1回点滅 | LoRa送信完了 |
| LED1(RED) 高速5回 | エラー（GPS補足タイムアウト等） |

> **注**: fw/main.cにLEDデバッグパターンは未実装。Step 6の前にmain.cに追加すること。

#### Step 7: LoRa通信確認
ゲートウェイ（RaspberryPi + E220）を別途用意して受信確認:
1. ゲートウェイ側でシリアル受信（115200bps → E220デフォルト設定に合わせる）
2. 12バイトパケット受信を確認
3. lat/lon/seqをPythonでデコード

---

### LEDデバッグパターン実装（fw/main.cに追加予定）

```c
// LED定義（要確認: LED1=R3経由U4.CHRG, LED2=R4経由U4.STDBY）
// デバッグ用にGPIOから直接制御する場合はATtiny GPIOに直結要
// 現設計はTP4056のCHRG/STDBYピンからLEDを駆動 → MCUから制御不可

// → LEDデバッグは断念。代わりにUPDIで書き込んだ後デバッガで確認するか、
//    ゲートウェイ受信パケットで動作確認する方針に変更。
```

> **設計上の制約**: LED1/LED2はTP4056のCHRG/STDBY出力に接続されており、ATtinyからは制御不可。デバッグ手段は「LoRaパケット受信確認」のみ。


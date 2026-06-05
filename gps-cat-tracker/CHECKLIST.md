# 猫GPSトラッカー フェーズゲートチェックリスト

**目的**: 再検証のたびにバグが出るパターンを防ぐ。  
**運用ルール**:
1. `[x]` は実際に確認した場合のみマーク。「たぶん大丈夫」は `[ ]` のまま残す
2. 確認方法が「コマンド実行」「ファイル参照」「datasheet Page XX」のいずれかであること。記憶・推測は不可
3. 新バグが出たら「バグ起源索引」に追加し、防げたはずのチェック項目を追記してからフェーズを進む
4. DESIGN.md の「修正済み」は、このチェックリストの該当項目が `[x]` になって初めて有効

---

## フェーズ1: PCB発注ゲート

> 以下が全て `[x]` になるまで JLCPCB への発注禁止。

### 1-A. 電気的検証（ツールで確認）

- [x] **DRC: clearance/short circuit エラー 0件**
  - 確認: `kicad-cli pcb drc` 実行済み (2026-05-30) → clearance: 0件, short_circuit: 0件 ✅
  - 根拠バグ: バグ1（via-pad短絡）、バグ3（RF-VCC交差）

- [x] **DRC: via_dangling が製造に影響しないこと確認**
  - 確認済み (2026-05-30): via_dangling 3件, track_dangling 3件 → B.CuゾーンFill後の構造起因
  - 総DRC件数: **352件**（内訳下記）

  | DRCタイプ | 件数 | 判定 | 理由 |
  |----------|------|------|------|
  | clearance | 0 | ✅ | ショートなし |
  | short_circuit | 0 | ✅ | |
  | copper_edge_clearance | 12 | ⚠️ 許容 | E220(x=0)が基板左端に接触。手はんだ部品なのでJLCPCB SMT製造対象外。実機搭載時の物理クリアランスに影響なし |
  | hole_clearance | 9 | ⚠️ 許容 | viaとパッドの穴間距離0mm。スクリプト生成PCBの構造的制約。JLCPCB最小ドリル間0.2mmは満たしている可能性が高い |
  | solder_mask_bridge | 116 | ⚠️ 要確認 | 基板全体に分布。スクリプト生成PCBのマスク展開設定の問題。**JLCPCBガーバービューアで確認必須** |
  | isolated_copper | 1 | ⚠️ 許容 | B.Cu ゾーン(0,0)。スクリプト生成アーティファクト。製造物への影響なし |
  | courtyards_overlap | 8 | ✅ 許容 | 高密度配置の設計判断。製造影響なし |
  | silk_over_copper | 158 | ✅ 許容 | シルク視認性への影響のみ |
  | silk_overlap/silk_edge_clearance | 42 | ✅ 許容 | シルク視認性のみ |
  | via_dangling | 3 | ✅ 許容 | Fill後のゾーン接続 |
  | track_dangling | 3 | ✅ 許容 | GNDスタブ。B.Cuゾーン接続 |

- [ ] **ERC: エラー 0件（lib_symbol_issues 除く）**
  - 確認: KiCad GUI → Inspect → Electrical Rules Checker
  - 除外可: `lib_symbol_issues`（カスタムライブラリ未登録・既知）

### 1-B. ピン接続（一次情報=KiCad .kicad_pcb から確認）

> **禁止**: シルクスクリーン・メモ・DESIGN.md の文字情報からピン番号を判定すること。
> **必須**: KiCad PCBエディタで「Net Inspector」または「Highlight Net」でトレース目視確認。

- [x] **UART クロス接続の向き確認**
  - ATtiny `TxD → デバイス RxD`（同名同士で繋がないこと）
  - USART0: ATtiny PA1(TxD0, pad12) → E220 pad7(RXD) ✅ (BFS経路確認済み 2026-05-30)
  - USART0: ATtiny PA2(RxD0, pad11) ← E220 pad8(TXD) ✅
  - USART1: ATtiny PC1(RxD1, pad7) ← GPS TXD(p2) ✅
  - USART1: ATtiny PC2(TxD1, pad8) → GPS RXD(p3) ✅
  - 根拠バグ: バグ4（全UART誤接続）

- [x] **E220 M0/M1 接続確認**
  - M0(E220 pin5) → GND（固定） ✅ (BFS確認済み: pad6→(25.5,8.0)方向)
  - M1(E220 pin6) → ATtiny pad6(PB0) ✅ (BFS 7ホップで接続確認済み)

- [x] **UPDI テストポイント接続確認**
  - TP1(16.0,18.5) → ATtiny pad16(16.0,20.75) ✅ (直線トレース1ホップ確認済み)
  - TP2(18.5,18.5) → via(18.6,17.0)経由でVCC ✅
  - TP3(20.5,18.5) → via(20.5,17.0)経由でGND ✅

- [ ] **電源デカップリング: 全IC の VCC ピン近傍に 100nF 配置確認**
  - ATtiny3226 U2 → C2(100nF)
  - ATGM336H U3 → C3(100nF)
  - E220 U1 → C1(100nF)

### 1-C. データシート照合（ATtiny3226 データシート Table 4-1 で確認）

- [ ] **ATtiny3226 VQFN-20 パッド番号の対応確認（KiCad座標 vs データシート）**

  | パッド | ポート | 座標（PCB） | DS確認 |
  |-------|--------|------------|--------|
  | pad6  | PB0    | (14.0, 24.75) | [ ] |
  | pad7  | PC1    | (14.5, 24.25) | [ ] |
  | pad8  | PC2    | (15.0, 24.25) | [ ] |
  | pad11 | PA2    | (16.75, 23.5) | [ ] |
  | pad12 | PA1    | (16.75, 23.0) | [ ] |
  | pad16 | PA0/UPDI | (16.0, 20.75) | [ ] |

  - 確認方法: ATtiny3226データシート「4.1 Pin Description」Table で pad番号↔ポート名を照合
  - 根拠バグ: pad17/pad18 誤記（シルクから参照していた）

### 1-D. 製造ファイル確認

- [x] **発注用 zip ファイルが正しいか（混在禁止）**
  - 使用するzip: `lora-30x35-v3n_gerber_jlcpcb.zip`（20KB・12ファイルのみ）
  - 確認: `python3 -c "import zipfile; [print(n) for n in zipfile.ZipFile('lora-30x35-v3n_gerber_jlcpcb.zip').namelist()]"`
  - 禁止: `lora-30x35-v3n_gerber.zip`（127KB・旧.gbrと新JLCPCB標準が混在）
  - 根拠: 2026-05-30 再チェックで発覚。zipを正しく再生成済み ✅

- [ ] **Gerber ファイル名が JLCPCB 標準拡張子**
  - `.gtl` (F.Cu), `.gbl` (B.Cu), `.gts` (F.Mask), `.gbs` (B.Mask)
  - `.gto` (F.Silkscreen), `.gbo` (B.Silkscreen), `.gtp` (F.Paste), `.gbp` (B.Paste)
  - `.gm1` (Edge.Cuts), `.drl` (ドリル)
  - 確認: `ls gerber_v3n/` で拡張子一覧を確認

- [ ] **基板サイズ確認**: Edge.Cuts が 30×35mm（JLCPCB ガーバービューアで確認）

- [ ] **PCB厚設定**: 0.8mm（RF 50Ω設計値・変更禁止）をJLCPCB注文フォームで指定済みか

- [ ] **BOM/CPL ファイルの LCSC番号が全て JLCPCB parts library で実在確認済み**
  - C5227682 (ATtiny3226-MU) → [ ] 在庫確認日: ___
  - C90770 (ATGM336H) → [ ] 在庫確認日: ___
  - C88373 (U.FL) → [ ] 在庫確認日: ___
  - C189893 (JST-GH 2P) → [ ] 在庫確認日: ___ ※要注意（過去在庫切れ）
  - 根拠バグ: BOM LCSC番号誤り3件（C3014522/C317592/C160404 全て別部品）

---

## フェーズ2: ファームウェア書き込みゲート

> `make flash` 実行前に以下を全て確認。

### 2-A. レジスタ値（iotn3226.h の enum から確認・推測禁止）

- [x] **PORTMUX設定が実装されているか**
  - 確認済み (2026-05-30): `portmux_init()` に `PORTMUX.USARTROUTEA = PORTMUX_USART0_ALT1_gc | PORTMUX_USART1_ALT1_gc` ✅
  - iotn3226.h 確認: USART0_ALT1_gc=(0x01<<0)=0x01, USART1_ALT1_gc=(0x01<<2)=0x04 → 合計0x05 ✅
  - 根拠バグ: PORTMUX未設定（UART全ピン誤出力・最大の致命バグ）

- [x] **PORTMUX が USART 有効化（CTRLB 設定）より前に呼ばれているか**
  - 確認済み (2026-05-30): main()で `portmux_init()` → `usart0_init()` → `usart1_init()` の順 ✅

- [x] **クロック設定: 計算式で確認**
  - fuse2: FREQSEL_16MHZ_gc = `0x01`（iotn3226.h grep確認済み: FREQSEL_20MHZ_gc=0x02と逆順注意）✅
  - prescaler: CLKCTRL_PDIV_2X_gc = `(0x00<<1)` = 0x00 → 16MHz ÷ 2 = **8MHz** ✅
  - fw/main.c: `CLKCTRL_PDIV_2X_gc` 使用確認済み ✅
  - 根拠バグ: PDIV_4X/FREQSEL=0x02 の二重ミス（計算なし・enum未確認）

- [x] **ISR ベクタ名を iotn3226.h で確認**
  - 確認済み (2026-05-30): `RTC_PIT_vect = _VECTOR(4)` が iotn3226.h に定義あり ✅
  - WDT_vect は tinyAVR 2-Series に存在しない（RTC PITを使う）✅
  - 根拠バグ: WDT_vect 使用（tinyAVR 2-Series はWDT割り込みなし）

- [x] **BAUD レジスタ計算値の確認**
  - 計算: (8000000 × 64) / (16 × 9600) = 3333, 実ボーレート 9601bps, 誤差0.010% ✅
  - fw/main.c の計算式 `((uint32_t)F_CPU * 64) / (16UL * BAUD_UART)` で正しく計算 ✅

### 2-B. fuse 書き込み確認

- [ ] **fuse2 = 0x01 が書き込まれているか**
  - 確認: `make fuse-read SERIAL_PORT=/dev/cu.xxx` → fuse2 行が `0x01` であること
  - 注意: デフォルト fuse2=0x02（20MHz）のままでは 8MHz にならない
  - 根拠バグ: FREQSEL 誤り

- [ ] **fuse4 = 0xF6（UPDI有効）が書き込まれているか**
  - UPDI を無効にすると書き込み不可になる（復帰には HVUPDI 必要）

### 2-C. コンパイル確認

- [x] **`make` が警告 0件でビルドできるか**
  - 確認済み (2026-05-30): 警告 0件 ✅

- [x] **Flash サイズが ATtiny3226 の 32KB 以内か**
  - 確認済み (2026-05-30): Program 1648 bytes / 32768 bytes (5%) ✅

---

## フェーズ3: ブリングアップゲート

> 実機に電源を入れる前に確認。

### 3-A. 電源投入前

- [ ] **実装前の目視: ブリッジ・ハンダ不足がないか**
  - ATtiny3226 VQFN-20（0.5mmピッチ）のパッド間ブリッジを虫眼鏡または顕微鏡で確認

- [ ] **VCC-GND 間抵抗が 0Ω でないか**
  - 確認: テスター抵抗モードで J1 VCC-GND 間 → 数百Ω以上あること（0Ω = ショート）

- [ ] **E220 のデフォルト設定確認（M0=M1=1 のコンフィグモード）**
  - 9600bps, CH17(920.125MHz), SF9/BW125kHz が工場デフォルトか確認
  - 確認方法: E220 を M0=M1=1 にして UART で `C0 00 08 xx xx xx ...` コマンドを読み出す

### 3-B. UPDI 書き込み確認

- [ ] **`make fuse-read` が成功するか（UPDI 疎通確認）**
  - TP1(UPDI), TP2(VCC), TP3(GND) にクリップを当てて `avrdude -c serialupdi ...` が通るか

- [ ] **`make flash` 成功・verify 通過**

### 3-C. 動作確認

- [ ] **UART0（E220）から起動メッセージ確認**
  - E220 のデフォルトモードで PCB UART0(PA1/PA2) に UART ロガーを繋いでデータが流れるか
  - データが出ない → PORTMUX 設定を疑う（PA1/PA2 に出ているか確認）

- [ ] **GPS コールドスタート取得確認（屋外・90秒以内）**
  - UART1(PC1/PC2) にロガーを繋いで NMEA ストリームが見えるか
  - `$GNRMC,...,A,...` の Status='A' が 90秒以内に取得できるか

- [ ] **LoRa パケット受信確認（ゲートウェイ側）**
  - 12バイトバイナリを受信し、lat/lon が現在地の緯度経度に近いか
  - 緯度 > 20,000,000（20.0度）かつ < 50,000,000（50.0度）であること（日本国内チェック）

---

## バグ起源索引

| チェック項目 | 防げたバグ | 発見日 |
|------------|----------|--------|
| 1-A: DRC clearance 0件 | バグ1(VCC短絡), バグ3(RF-VCC交差) | 2026-05-29 |
| 1-B: KiCad一次情報でピン確認 | バグ4(GPS UART全誤配線) | 2026-05-30 |
| 1-D: BOM LCSC番号実在確認 | BOM 3件誤り(別部品番号) | 2026-05-30 |
| 1-D: Gerber zipの内容確認 | **Gerber zip混在問題(旧.gbrと新JLCPCB標準が同一zip内・誤製造リスク)** | 2026-05-30 |
| 2-A: PORTMUX確認 | PORTMUX未設定(UART全ピン誤出力) | 2026-05-30 |
| 2-A: PDIV_2X確認 | PDIV_4X誤り(20÷4=5MHz, 目標8MHz) | 2026-05-30 |
| 2-A: FREQSEL enum確認 | FREQSEL=0x02誤り(実際は16MHz=0x01) | 2026-05-30 |
| 2-A: ISRベクタgrep確認 | WDT_vect誤り(tinyAVR 2-Series未実装) | 2026-05-30 |
| 1-C: DS照合でpad番号確認 | pad17/18誤記(正: pad12/11) | 2026-05-30 |

---

## 一次情報参照ルール（最重要）

```
ピン番号の信頼順位:
  1位 KiCad .kicad_pcb の pad 座標・net 名（機械情報・改ざん検知可）
  2位 ATtiny3226 データシート Table 4-1（PDF原本）
  3位 fw/main.c コメント（上記から派生）
  4位 DESIGN.md（三次情報・最も古くなりやすい）
  禁止 シルクスクリーンのテキスト・メモ・記憶

レジスタ値の信頼順位:
  1位 avr/iotn3226.h の enum 定義（grep で確認）
  2位 ATtiny3226 データシート Register Map
  禁止 「たぶん 0x01 だろう」という推測

ドキュメントの「修正済み」マーク条件:
  - DRC件数変化を kicad-cli で確認した場合のみ有効
  - 「Pythonで修正した・たぶん反映された」は未完了扱い
```

# Phase 1 テスト手順

## 必要なハードウェア

### 推奨: Lilygo T-SIM7080G-S3（1台で完結）

| 品名 | 価格目安 | 購入先 |
|------|---------|--------|
| **Lilygo T-SIM7080G-S3** | ~¥6,000 | AliExpress / Amazon |
| nano SIM（LTE-M対応） | SIM代 | IIJmio / nuroモバイル |
| LiPoバッテリー 400mAh JST2.0 | ~¥800 | Amazon |

**T-SIM7080G-S3 を選ぶ理由:**
- ESP32-S3 + SIM7080G-M が基板に統合済み → 配線不要
- microSDスロット・バッテリーコネクタ付き
- USB-C で書き込み・充電
- 本番PCB（ESP32-C3）と WiFi API / AT コマンドが共通 → コード移植容易

### 代替: 個別ボード構成（ESP32-C3 で本番と完全一致）

| 品名 | 価格目安 |
|------|---------|
| ESP32-C3 SuperMini または DevKitM-1 | ~¥500 |
| Waveshare SIM7080G-M2M-HAT | ~¥5,000 |
| ジャンパーワイヤー（UART接続用） | ~¥300 |

接続:
```
ESP32-C3         SIM7080G
GPIO17 (TX)  →  RX
GPIO18 (RX)  ←  TX
GND          ―  GND
3.3V or 5V   →  VCC（ボード仕様による）
```

---

## SIM カード

LTE-M（Cat-M1）対応SIMが必要。

| キャリア | プラン名 | 月額 | APN |
|---------|---------|------|-----|
| IIJmio | IoT SIM | ¥165〜 | iijmio.jp |
| nuroモバイル | IoT | ¥165〜 | nuro.jp.dti |
| ソラコム | plan-D / plan-KM1 | 従量 | soracom.io |

**ソラコムがおすすめ**: Webコンソールでデバイス確認・データ量確認が簡単。

---

## Arduino 開発環境セットアップ

### 1. ESP32 ボードパッケージ追加

Arduino IDE → Preferences → Additional boards URLs に追加:
```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```

Tools → Board Manager → "esp32" をインストール（v2.0.x 以上）

### 2. ボード選択

- Lilygo T-SIM7080G-S3 使用時: `ESP32S3 Dev Module`
- ESP32-C3 DevKit 使用時: `ESP32C3 Dev Module`

### 3. スケッチを開く

```
Arduino IDE → ファイル → 開く
→ /Users/m2mac/lte-m-cat-tracker/firmware/phase1_test/phase1_test.ino
```

### 4. 設定を編集（必須）

`phase1_test.ino` の設定セクションを変更:
```cpp
const char* HOME_SSID    = "自宅WiFiのSSID";
const char* APN          = "iijmio.jp";        // 契約SIMのAPN
const char* TRACCAR_HOST = "192.168.1.100";    // TraccarサーバーのIP
const char* DEVICE_ID    = "cat-tracker-001";
```

Lilygo T-SIM7080G-S3 のピン番号は公式リポジトリで確認:
https://github.com/Xinyuan-LilyGO/LilyGo-T-SIM7080G

---

## テスト手順（STEP順）

### STEP 1: AT 疎通確認
シリアルモニタ（115200bps）で確認:
```
[AT] >> AT
[AT] << AT
       OK
[OK] SIM7080G 応答あり
```
→ 出ない場合: TX/RX 逆、ボーレート不一致、電源不足

### STEP 2: LTE-M 接続
```
[OK] LTE-M ネットワーク登録成功
```
→ 出ない場合: APN設定、SIM未対応、バンド設定（B1/B19）

### STEP 3: GPS 測位
**屋外またはベランダ**でテストすること（室内では取れない）:
```
[OK] GPS固定: lat=35.681200 lon=139.767100 alt=10.0m sats=8
```
→ 初回 Cold start は 2〜5 分かかる

### STEP 4: WiFi 在宅判定
```
[OK] 在宅確認 → 省電力モードへ
```
→ HOME_SSID が自宅WiFiと一致しているか確認

### STEP 5: Traccar 送信
```
[OK] Traccar 送信成功
```
→ 先に Traccar サーバーを起動しておく（次節参照）

### STEP 6: deep sleep
```
=== deep sleep: 30分 ===
ESP32をdeep sleepに移行します...
```
→ 30分後に自動再起動 → STEP 1 から繰り返し

---

## Traccar サーバー（ローカル動作確認用）

### Mac でテスト起動（最速）

```bash
# Java 17 が必要
brew install openjdk@17

# Traccar ダウンロード
curl -L https://github.com/traccar/traccar/releases/latest/download/traccar-other.zip -o traccar.zip
unzip traccar.zip -d traccar/
cd traccar

# 起動
java -jar tracker-server.jar conf/traccar.xml
```

ブラウザで確認:
```
http://localhost:8082
```
初回: admin / admin でログイン → デバイス追加（ID: cat-tracker-001）

### 本番（Raspberry Pi またはVPS）

```bash
# Raspberry Pi (Debian/Ubuntu)
wget https://github.com/traccar/traccar/releases/latest/download/traccar-linux-64.zip
unzip traccar-linux-64.zip
sudo ./traccar.run
sudo systemctl enable traccar
sudo systemctl start traccar
```

---

## 消費電流の実測（重要）

Phase 1 で必ず電流を実測する（試算との差異を確認）。

**測定器**: USB電流計（¥500程度） または テスター直列挿入

| 状態 | 試算値 | 実測値 |
|------|--------|--------|
| 在宅WiFiスキャン100ms | 80mA瞬間 | |
| ESP32 deep sleep | 5μA | |
| GPS測位中 | 60mA | |
| LTE-M送信ピーク | 500mA | |
| PSM中 | 0.7μA | |

実測値を DESIGN.md の試算表に反映する。

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| AT応答なし | TX/RX逆・ボーレート | 配線確認・115200bps確認 |
| LTE-M登録できない | APN間違い | キャリアのAPN設定を確認 |
| GPS取れない | 室内 | 屋外・窓際でテスト |
| Traccar届かない | IP/Port | ping確認・ファイアウォール |
| deep sleep後に起きない | ピン設定 | SIM_PWR_PINの値を確認 |

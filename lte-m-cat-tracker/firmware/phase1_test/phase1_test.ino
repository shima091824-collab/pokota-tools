/**
 * LTE-M 猫GPSトラッカー Phase 1 テストファームウェア
 *
 * 開発ボード: Lilygo T-SIM7080G-S3
 *   - SIM7080G-M が ESP32-S3 に UART 接続済み
 *   - 本番PCBは ESP32-C3 + SIM7080G-M（同じATコマンド・同じWiFi API）
 *
 * テスト項目:
 *   STEP 1: SIM7080G AT通信確認
 *   STEP 2: LTE-M 接続
 *   STEP 3: GPS 測位
 *   STEP 4: WiFi スキャン（在宅判定）
 *   STEP 5: Traccar HTTP POST
 *   STEP 6: PSM 省電力 + ESP32 deep sleep
 *
 * 依存ライブラリ: なし（Arduino標準のみ）
 * ボード: "ESP32S3 Dev Module" または "Lilygo T-SIM7080G"
 */

#include <WiFi.h>
#include <HardwareSerial.h>

// ============================================================
// ★ 設定（自分の環境に合わせて変更する）
// ============================================================

// 在宅判定用 WiFi SSID（自宅ルーターのSSID）
const char* HOME_SSID = "Buffalo-2G-09C8";

// SIM カード APN（ソラコム plan-KM1）
const char* APN = "soracom.io";

// Traccar サーバー設定
const char* TRACCAR_HOST = "192.168.1.100";  // TraccarサーバーのIPまたはドメイン
const int   TRACCAR_PORT = 5055;
const char* DEVICE_ID   = "cat-tracker-001";

// GPS送信間隔（外出時）
const int GPS_INTERVAL_MIN = 30;  // 分

// Lilygo T-SIM7080G-S3 ピン定義
// ※ 本番 ESP32-C3 PCB では変更する
#define SIM_TX_PIN     17   // ESP32 TX → SIM7080G RX
#define SIM_RX_PIN     18   // ESP32 RX ← SIM7080G TX
#define SIM_PWR_PIN    41   // PWRKEY
#define SIM_POWER_ON   12   // MODEM POWER ENABLE（HIGH で電源供給）
#define SIM_RST_PIN    16   // RESET（active LOW）
#define SIM_DTR_PIN     1   // DTR（HIGH = awake）
#define LED_PIN        37   // 状態表示 LED

// ============================================================
// グローバル変数
// ============================================================

HardwareSerial simSerial(1);  // UART1

struct GpsData {
  bool    valid;
  float   lat;
  float   lon;
  float   speed;   // km/h
  float   alt;     // m
  int     satellites;
};

// ============================================================
// AT コマンドユーティリティ
// ============================================================

/**
 * ATコマンドを送信し、期待する応答が返るまで待つ
 * @param cmd     送信するATコマンド
 * @param expect  期待する応答文字列（"OK" / "ERROR" / 特定文字列）
 * @param timeout タイムアウト[ms]
 * @return 応答全体の文字列
 */
String sendAT(const char* cmd, const char* expect = "OK", unsigned long timeout = 5000) {
  while (simSerial.available()) simSerial.read();  // バッファクリア

  simSerial.println(cmd);
  Serial.print("[AT] >> "); Serial.println(cmd);

  String response = "";
  unsigned long start = millis();

  while (millis() - start < timeout) {
    while (simSerial.available()) {
      char c = simSerial.read();
      response += c;
    }
    if (response.indexOf(expect) >= 0) break;
    if (response.indexOf("ERROR") >= 0) break;
  }

  Serial.print("[AT] << "); Serial.println(response);
  return response;
}

bool waitForAT(const char* cmd, const char* expect, unsigned long timeout = 10000) {
  String r = sendAT(cmd, expect, timeout);
  return r.indexOf(expect) >= 0;
}

// ============================================================
// STEP 1: SIM7080G 起動・AT 疎通確認
// ============================================================

bool initSim7080g() {
  Serial.println("\n=== STEP 1: SIM7080G 初期化 ===");

  // 電源ON（T-SIM7080G-S3 公式手順）
  // 1. POWER ENABLE
  pinMode(SIM_POWER_ON, OUTPUT);
  digitalWrite(SIM_POWER_ON, HIGH);
  delay(500);
  Serial.println("[SIM] POWER_ON=HIGH");

  // 2. DTR = HIGH（モジュールを起こす）
  pinMode(SIM_DTR_PIN, OUTPUT);
  digitalWrite(SIM_DTR_PIN, HIGH);

  // 3. RESET パルス（active LOW: HIGH→LOW→HIGH）
  if (SIM_RST_PIN >= 0) {
    pinMode(SIM_RST_PIN, OUTPUT);
    digitalWrite(SIM_RST_PIN, HIGH);
    delay(100);
    digitalWrite(SIM_RST_PIN, LOW);
    delay(2600);
    digitalWrite(SIM_RST_PIN, HIGH);
    Serial.println("[SIM] RESET pulse done");
  }

  // 4. PWRKEY パルス（LOW→HIGH(1s)→LOW）
  pinMode(SIM_PWR_PIN, OUTPUT);
  digitalWrite(SIM_PWR_PIN, LOW);
  delay(100);
  digitalWrite(SIM_PWR_PIN, HIGH);
  delay(1000);
  digitalWrite(SIM_PWR_PIN, LOW);
  Serial.println("[SIM] PWRKEY done, waiting 5s...");
  delay(5000);

  // 起動時の unsolicited メッセージを生読み（デバッグ）
  Serial.print("[DBG] Raw bytes from modem (5s): ");
  unsigned long t0 = millis();
  int rawCount = 0;
  while (millis() - t0 < 5000) {
    if (simSerial.available()) {
      char c = simSerial.read();
      Serial.print(c);
      rawCount++;
    }
  }
  Serial.print("\n[DBG] Total raw bytes: "); Serial.println(rawCount);

  // AT 疎通確認（最大10秒待つ）
  for (int i = 0; i < 10; i++) {
    if (waitForAT("AT", "OK", 1000)) {
      Serial.println("[OK] SIM7080G 応答あり");
      break;
    }
    if (i == 9) {
      Serial.println("[NG] SIM7080G 応答なし → 配線・電源を確認してください");
      return false;
    }
    delay(1000);
  }

  // エコーバック無効（ログが読みやすくなる）
  waitForAT("ATE0", "OK");

  // モデム情報表示
  sendAT("ATI");                  // モデル名
  sendAT("AT+CIMI");              // IMSI（SIM確認）
  sendAT("AT+CGSN");              // IMEI

  // SIMカード確認
  String simStatus = sendAT("AT+CPIN?");
  if (simStatus.indexOf("READY") < 0) {
    Serial.println("[NG] SIMカード未挿入または PIN ロック");
    return false;
  }
  Serial.println("[OK] SIMカード認識");
  return true;
}

// ============================================================
// STEP 2: LTE-M 接続
// ============================================================

bool connectLTEM() {
  Serial.println("\n=== STEP 2: LTE-M 接続 ===");

  // NB-IoT無効・Cat-M1のみ
  waitForAT("AT+CMNB=1", "OK");  // 1=LTE-M, 2=NB-IoT, 3=両方

  // 日本バンド設定（B1=2100MHz, B19=800MHz）
  waitForAT("AT+CBANDCFG=\"CAT-M\",1,19", "OK");

  // APN 設定
  String apnCmd = String("AT+CGDCONT=1,\"IP\",\"") + APN + "\"";
  waitForAT(apnCmd.c_str(), "OK");

  // ネットワーク登録待ち（最大60秒）
  Serial.println("LTE-M 接続中...");
  for (int i = 0; i < 60; i++) {
    String reg = sendAT("AT+CEREG?", "+CEREG:", 2000);
    // +CEREG: 0,1 (home) または +CEREG: 0,5 (roaming) で登録成功
    if (reg.indexOf(",1") >= 0 || reg.indexOf(",5") >= 0) {
      Serial.println("[OK] LTE-M ネットワーク登録成功");
      break;
    }
    if (i == 59) {
      Serial.println("[NG] LTE-M 接続タイムアウト");
      Serial.println("     → APN設定・SIM契約・バンド設定を確認");
      return false;
    }
    delay(1000);
    Serial.print(".");
  }

  // IP アドレス取得確認
  sendAT("AT+CGPADDR=1");

  // 信号強度表示
  sendAT("AT+CSQ");    // RSSI
  sendAT("AT+CPSI?"); // 詳細ネットワーク情報（バンド・RSRP等）

  Serial.println("[OK] LTE-M 接続完了");
  return true;
}

// ============================================================
// STEP 3: GPS 測位
// ============================================================

bool enableGPS() {
  Serial.println("\n=== STEP 3: GPS 有効化 ===");

  // GPS電源ON
  if (!waitForAT("AT+CGNSPWR=1", "OK")) {
    Serial.println("[NG] GPS電源ONに失敗");
    return false;
  }
  Serial.println("[OK] GPS電源ON");
  return true;
}

/**
 * GPS測位を待ち、データを返す
 * @param timeout 最大待機時間[ms]（初回Cold startは2〜5分かかる場合あり）
 */
GpsData getGpsFix(unsigned long timeout = 120000) {
  GpsData data = {false, 0, 0, 0, 0, 0};

  Serial.println("GPS測位中（最大2分）...");
  unsigned long start = millis();

  while (millis() - start < timeout) {
    String info = sendAT("AT+CGNSINF", "+CGNSINF:", 2000);

    // 応答形式: +CGNSINF: 1,1,20240530123456.000,35.6812,139.7671,10.0,0.5,1.0,1,,1.2,1.4,0.8,,9,10,,,32,
    // フィールド: GPS_run,Fix,UTC,Lat,Lon,Alt,Speed,Course,...,Sats
    int idx = info.indexOf("+CGNSINF:");
    if (idx >= 0) {
      String csv = info.substring(idx + 9);
      csv.trim();

      // カンマ区切りでパース
      int fields[20];
      String parts[20];
      int count = 0;
      int prev = 0;
      for (int i = 0; i <= csv.length() && count < 20; i++) {
        if (i == csv.length() || csv[i] == ',') {
          parts[count++] = csv.substring(prev, i);
          prev = i + 1;
        }
      }

      // field[1] = Fix status (1=固定済み)
      if (count > 4 && parts[1] == "1") {
        data.valid      = true;
        data.lat        = parts[3].toFloat();
        data.lon        = parts[4].toFloat();
        data.alt        = (count > 5) ? parts[5].toFloat() : 0;
        data.speed      = (count > 6) ? parts[6].toFloat() : 0;
        data.satellites = (count > 14) ? parts[14].toInt() : 0;

        Serial.printf("[OK] GPS固定: lat=%.6f lon=%.6f alt=%.1fm sats=%d\n",
                      data.lat, data.lon, data.alt, data.satellites);
        return data;
      }
    }

    delay(5000);  // 5秒待って再試行
    Serial.print(".");
  }

  Serial.println("\n[NG] GPS測位タイムアウト（屋外でテストしてください）");
  return data;
}

// ============================================================
// STEP 4: WiFi スキャン（在宅判定）
// ============================================================

bool isAtHome() {
  Serial.println("\n=== STEP 4: WiFi 在宅判定 ===");

  int n = WiFi.scanNetworks();
  Serial.printf("検出SSID数: %d\n", n);

  for (int i = 0; i < n; i++) {
    String ssid = WiFi.SSID(i);
    Serial.printf("  [%d] %s (RSSI: %d)\n", i, ssid.c_str(), WiFi.RSSI(i));
    if (ssid == HOME_SSID) {
      Serial.println("[OK] 在宅確認 → 省電力モードへ");
      WiFi.scanDelete();
      return true;
    }
  }

  WiFi.scanDelete();
  Serial.println("[--] 自宅SSID未検出 → 外出モードへ");
  return false;
}

// ============================================================
// STEP 5: Traccar HTTP POST
// ============================================================

bool sendToTraccar(const GpsData& gps, int batteryPct) {
  Serial.println("\n=== STEP 5: Traccar 送信 ===");

  if (!gps.valid) {
    Serial.println("[SKIP] GPS未固定のためスキップ");
    return false;
  }

  // Traccar OsmAnd プロトコル（HTTPクエリパラメータ）
  // GET //?id=<id>&lat=<lat>&lon=<lon>&speed=<speed>&altitude=<alt>&batt=<batt>
  String url = String("http://") + TRACCAR_HOST + ":" + TRACCAR_PORT
             + "//?id=" + DEVICE_ID
             + "&lat="  + String(gps.lat, 6)
             + "&lon="  + String(gps.lon, 6)
             + "&speed=" + String(gps.speed, 1)
             + "&altitude=" + String(gps.alt, 1)
             + "&batt=" + batteryPct;

  Serial.println("送信URL: " + url);

  // SIM7080G で HTTP GET
  waitForAT("AT+HTTPINIT", "OK");

  String urlCmd = String("AT+HTTPPARA=\"URL\",\"") + url + "\"";
  waitForAT(urlCmd.c_str(), "OK");

  String response = sendAT("AT+HTTPACTION=0", "+HTTPACTION:", 15000);

  // +HTTPACTION: 0,200,<len> → 200 = 成功
  bool success = response.indexOf(",200,") >= 0;

  waitForAT("AT+HTTPTERM", "OK");

  if (success) {
    Serial.println("[OK] Traccar 送信成功");
  } else {
    Serial.println("[NG] Traccar 送信失敗 → サーバーIP・ポートを確認");
  }

  return success;
}

// ============================================================
// STEP 6: PSM 設定（省電力）
// ============================================================

void setupPSM() {
  Serial.println("\n=== STEP 6: PSM 設定 ===");

  // PSM有効化
  // AT+CPSMS=1,,,<T3412(periodic TAU)>,<T3324(active timer)>
  // T3412 = 01100001 = 1分×1 = 1分（ネットワーク側で上書きされる場合あり）
  // T3324 = 00000000 = 0秒（送信後すぐスリープ）
  // ※ 実際の値はキャリアポリシーによる（IIJmio等では数分〜数時間）
  waitForAT("AT+CPSMS=1,,,\"01100001\",\"00000000\"", "OK");

  Serial.println("[OK] PSM設定完了（次回接続から適用）");
  Serial.println("     → 送信後にSIM7080Gが自動でスリープ移行します");
}

// ============================================================
// ESP32 deep sleep（次のGPS送信まで待機）
// ============================================================

void goToDeepSleep(int minutes) {
  Serial.printf("\n=== deep sleep: %d分 ===\n", minutes);
  Serial.println("ESP32をdeep sleepに移行します...");
  Serial.flush();

  // deep sleep（タイマー起床）
  esp_sleep_enable_timer_wakeup((uint64_t)minutes * 60 * 1000000ULL);  // μs単位
  esp_deep_sleep_start();
  // ここには戻らない
}

// ============================================================
// メインフロー
// ============================================================

// ============================================================
// 診断モード: SIM7080G 単独テスト
//   - WiFiスキャンしない（突入電流を避ける）
//   - ブラウンアウト検出を無効化
//   - AT を繰り返し送り、生バイトを表示し続ける
// ============================================================
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

void setup() {
  // ブラウンアウト検出を無効化（モジュール突入電流でのリセット防止）
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  Serial.begin(115200);
  unsigned long t = millis();
  while (!Serial && millis() - t < 5000) { delay(10); }
  delay(500);
  Serial.println("\n========================================");
  Serial.println(" SIM7080G 診断モード");
  Serial.println("========================================");

  pinMode(LED_PIN, OUTPUT);

  // UART1 を SIM7080G に接続
  simSerial.begin(115200, SERIAL_8N1, SIM_RX_PIN, SIM_TX_PIN);
  delay(200);

  // 電源シーケンス
  pinMode(SIM_POWER_ON, OUTPUT);
  digitalWrite(SIM_POWER_ON, HIGH);
  Serial.println("[SIM] POWER_ON=HIGH");
  delay(500);

  pinMode(SIM_DTR_PIN, OUTPUT);
  digitalWrite(SIM_DTR_PIN, HIGH);

  // RESET パルス（active LOW）
  pinMode(SIM_RST_PIN, OUTPUT);
  digitalWrite(SIM_RST_PIN, HIGH);
  delay(100);
  digitalWrite(SIM_RST_PIN, LOW);
  delay(2600);
  digitalWrite(SIM_RST_PIN, HIGH);
  Serial.println("[SIM] RESET done");

  // PWRKEY パルス（LOW→HIGH(1.2s)→LOW）
  pinMode(SIM_PWR_PIN, OUTPUT);
  digitalWrite(SIM_PWR_PIN, LOW);
  delay(100);
  digitalWrite(SIM_PWR_PIN, HIGH);
  delay(1200);
  digitalWrite(SIM_PWR_PIN, LOW);
  Serial.println("[SIM] PWRKEY done");

  Serial.println("[DIAG] ループ開始: AT送信＋生バイト表示");
}

void loop() {
  // LED 点滅（生存確認）
  static bool led = false;
  led = !led;
  digitalWrite(LED_PIN, led);

  // 受信バイトをすべて表示
  while (simSerial.available()) {
    char c = simSerial.read();
    if (c == '\r') Serial.print("\\r");
    else if (c == '\n') Serial.println("\\n");
    else Serial.print(c);
  }

  // AT を送信
  Serial.println("\n[TX] AT");
  simSerial.print("AT\r\n");
  delay(1000);
}

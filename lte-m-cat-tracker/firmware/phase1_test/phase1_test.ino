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
// LTE網からMacのLAN IP(192.168.11.3:5055)には届かないため、cloudflared Quick Tunnel経由で送信する
// ※ トンネルURLは cloudflared 起動のたびに変わる。/tmp/cloudflared.log で確認して書き換える
const char* TRACCAR_HOST = "scholar-holland-disclosure-effects.trycloudflare.com";
const int   TRACCAR_PORT = 80;
const char* DEVICE_ID   = "cat-tracker-001";

// GPS送信間隔（外出時）
const int GPS_INTERVAL_MIN = 30;  // 分

// Lilygo T-SIM7080G-S3 ピン定義（公式リポジトリ examples/ATDebug/utilities.h で確認・2026-06-11）
// ※ 本番 ESP32-C3 PCB では変更する
// モデム電源はGPIOではなく AXP2101 PMU（I2C経由）で制御する
#define SIM_RX_PIN     4    // BOARD_MODEM_RXD_PIN
#define SIM_TX_PIN     5    // BOARD_MODEM_TXD_PIN
#define SIM_PWR_PIN    41   // PWRKEY（BOARD_MODEM_PWR_PIN）
#define SIM_DTR_PIN    42   // DTR（BOARD_MODEM_DTR_PIN）
#define PMU_I2C_SDA    15
#define PMU_I2C_SCL    7
// LED: GPIO35-37はOPI PSRAM占有のため使用不可。PMUの充電LEDを状態表示に使う

#define XPOWERS_CHIP_AXP2101
#include "XPowersLib.h"
XPowersPMU PMU;

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

  // DTR = HIGH（モジュールを起こす）
  pinMode(SIM_DTR_PIN, OUTPUT);
  digitalWrite(SIM_DTR_PIN, HIGH);

  // AT疎通確認 → 応答がなければPWRKEYパルスで起動（公式ATDebug準拠）
  pinMode(SIM_PWR_PIN, OUTPUT);
  bool alive = false;
  for (int attempt = 0; attempt < 3 && !alive; attempt++) {
    for (int i = 0; i < 10; i++) {
      if (waitForAT("AT", "OK", 1000)) { alive = true; break; }
    }
    if (!alive) {
      Serial.println("[SIM] 応答なし → PWRKEYパルス送出");
      digitalWrite(SIM_PWR_PIN, LOW);
      delay(100);
      digitalWrite(SIM_PWR_PIN, HIGH);
      delay(1000);
      digitalWrite(SIM_PWR_PIN, LOW);
      delay(5000);
    }
  }
  if (!alive) {
    Serial.println("[NG] SIM7080G 応答なし → PMU電源・配線を確認してください");
    return false;
  }
  Serial.println("[OK] SIM7080G 応答あり");

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

  // 日本バンド設定: B1/B19=docomo, B18/B26=KDDI(800MHz)
  // Soracom plan-KM1はKDDI網のためB18/B26が必須（B1,19のみだと登録不可・2026-06-11実測）
  waitForAT("AT+CBANDCFG=\"CAT-M\",1,18,19,26", "OK");

  // APN 設定
  String apnCmd = String("AT+CGDCONT=1,\"IP\",\"") + APN + "\"";
  waitForAT(apnCmd.c_str(), "OK");

  // PSM無効化は登録待ちの前に行う（前サイクルのSTEP6でPSM有効のままだと登録が進まないことがある）
  waitForAT("AT+CPSMS=0", "OK");

  // ネットワーク登録待ち（最大180秒。電源サイクル後のCat-M網探索は60秒超かかることがある）
  Serial.println("LTE-M 接続中...");
  for (int i = 0; i < 180; i++) {
    String reg = sendAT("AT+CEREG?", "+CEREG:", 2000);
    // +CEREG: 0,1 (home) または +CEREG: 0,5 (roaming) で登録成功
    if (reg.indexOf(",1") >= 0 || reg.indexOf(",5") >= 0) {
      Serial.println("[OK] LTE-M ネットワーク登録成功");
      break;
    }
    if (i == 179) {
      Serial.println("[NG] LTE-M 接続タイムアウト");
      Serial.println("     → APN設定・SIM契約・バンド設定を確認");
      return false;
    }
    delay(1000);
    Serial.print(".");
  }

  // 信号強度表示
  sendAT("AT+CSQ");    // RSSI
  sendAT("AT+CPSI?"); // 詳細ネットワーク情報（バンド・RSRP等）

  Serial.println("[OK] LTE-M 登録完了（PDPはSTEP5送信直前に有効化する）");
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

  // --- PDP有効化（STEP2実機実証済みの手順: CNCFG PAP認証 → CNACT）---
  String cnCfg = String("AT+CNCFG=0,1,\"") + APN + "\",\"sora\",\"sora\",1";
  waitForAT(cnCfg.c_str(), "OK");
  waitForAT("AT+CNACT=0,1", "OK", 10000);
  // 有効化は非同期（+CNACT: 0,2=処理中→0,1=完了）。最大60秒ポーリングする
  bool pdpUp = false;
  for (int i = 0; i < 12; i++) {
    String st = sendAT("AT+CNACT?", "OK", 3000);
    if (st.indexOf("+CNACT: 0,1") >= 0) { pdpUp = true; break; }
    delay(5000);
  }
  if (!pdpUp) {
    Serial.println("[NG] PDP有効化失敗（60秒待っても+CNACT: 0,1にならず）");
    return false;
  }

  // Traccar OsmAnd プロトコル（HTTP GET クエリパラメータ）
  // SIM7080GはSH系HTTPコマンドを使う（HTTPINIT系はSIM800系で本機では動かない）
  // ポート80のときは:80を付けない（AT+SHCONNが:80付きURLでERRORになった・2026-06-11実測）
  String base = String("http://") + TRACCAR_HOST;
  if (TRACCAR_PORT != 80) base += String(":") + TRACCAR_PORT;

  // DNS解決の診断
  String dnsCmd = String("AT+CDNSGIP=\"") + TRACCAR_HOST + "\"";
  sendAT(dnsCmd.c_str(), "+CDNSGIP:", 15000);
  String path = String("/?id=") + DEVICE_ID
              + "&lat="  + String(gps.lat, 6)
              + "&lon="  + String(gps.lon, 6)
              + "&speed=" + String(gps.speed, 1)
              + "&altitude=" + String(gps.alt, 1)
              + "&batt=" + batteryPct;

  Serial.println("送信先: " + base + path);

  String urlCmd = String("AT+SHCONF=\"URL\",\"") + base + "\"";
  waitForAT(urlCmd.c_str(), "OK");
  waitForAT("AT+SHCONF=\"BODYLEN\",1024", "OK");
  waitForAT("AT+SHCONF=\"HEADERLEN\",350", "OK");

  if (!waitForAT("AT+SHCONN", "OK", 30000)) {
    Serial.println("[NG] HTTP接続失敗（AT+SHCONN）");
    waitForAT("AT+CNACT=0,0", "OK");
    return false;
  }

  // GET リクエスト（type 1=GET）→ +SHREQ: "GET",200,<len>
  String reqCmd = String("AT+SHREQ=\"") + path + "\",1";
  String response = sendAT(reqCmd.c_str(), "+SHREQ:", 30000);
  bool success = response.indexOf(",200,") >= 0;

  waitForAT("AT+SHDISC", "OK");
  waitForAT("AT+CNACT=0,0", "OK");  // PDP切断（GNSSとRF共有のため）

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
// メインフロー（STEP1→2→4→3→5→6）
//   GPS(GNSS)はLTEとRFを共有するため、PDP未接続の状態で測位し、
//   測位完了後にSTEP5でPDP有効化→送信→切断の順に実行する
// ============================================================
// 注意: WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0) によるBOD無効化はESP32無印用。
// ESP32-S3ではこの書き込み自体がBOD誤発火→リセットループを引き起こした（2026-06-11実測）。絶対に入れない。

void setup() {
  Serial.begin(115200);
  unsigned long t = millis();
  while (!Serial && millis() - t < 5000) { delay(10); }
  delay(500);
  Serial.println("\n========================================");
  Serial.println(" Phase 1 テスト（STEP1-6）");
  Serial.println("========================================");

  // AXP2101 PMU 初期化（公式ATDebug準拠。モデム・GPSアンテナの電源はPMU制御）
  if (!PMU.begin(Wire, AXP2101_SLAVE_ADDRESS, PMU_I2C_SDA, PMU_I2C_SCL)) {
    Serial.println("[NG] PMU(AXP2101)初期化失敗");
    delay(60000);
    ESP.restart();
  }
  PMU.setChargingLedMode(XPOWERS_CHG_LED_ON);  // 通電表示

  // 未使用電源レールをOFF
  PMU.disableDC2(); PMU.disableDC4(); PMU.disableDC5();
  PMU.disableALDO1(); PMU.disableALDO2(); PMU.disableALDO3(); PMU.disableALDO4();
  PMU.disableBLDO2(); PMU.disableCPUSLDO(); PMU.disableDLDO1(); PMU.disableDLDO2();

  // 電源投入起動時はモデム電源を一度切ってから再投入
  if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_UNDEFINED) {
    PMU.disableDC3();
    delay(200);
  }

  // BLDO1=3.3V: モデムUARTレベル変換用（切ると通信不可）
  PMU.setBLDO1Voltage(3300);
  PMU.enableBLDO1();
  // DC3=3.0V: SIM7080G 主電源
  PMU.setDC3Voltage(3000);
  PMU.enableDC3();
  // BLDO2=3.3V: GPSアンテナ電源（STEP3に必須）
  PMU.setBLDO2Voltage(3300);
  PMU.enableBLDO2();
  Serial.printf("[PMU] OK 電池: %.2fV %d%%\n", PMU.getBattVoltage() / 1000.0, PMU.getBatteryPercent());

  // UART1 を SIM7080G に接続
  simSerial.begin(115200, SERIAL_8N1, SIM_RX_PIN, SIM_TX_PIN);
  delay(200);

  // STEP 1: SIM7080G 起動・AT疎通
  if (!initSim7080g()) {
    Serial.println("[ABORT] STEP1失敗。60秒後に再起動");
    delay(60000);
    ESP.restart();
  }

  // STEP 2: LTE-M 登録（PDPはまだ張らない）
  bool lteOk = connectLTEM();

  // STEP 4: WiFi 在宅判定（結果は表示のみ。テストでは全STEPを通す）
  bool home = isAtHome();
  Serial.printf("[INFO] 在宅判定: %s\n", home ? "在宅" : "外出");

  // STEP 3: GPS 測位（RF空き状態で実施。前回実測80秒でFIX）
  GpsData gps = {false, 0, 0, 0, 0, 0};
  if (enableGPS()) {
    gps = getGpsFix(180000);  // 最大3分
    waitForAT("AT+CGNSPWR=0", "OK");  // 測位後にGNSS電源OFF（RF解放）
  }

  // STEP 5: Traccar 送信（PDP有効化→HTTP GET→切断）
  if (lteOk) {
    sendToTraccar(gps, PMU.getBatteryPercent());
  } else {
    Serial.println("[SKIP] LTE未登録のためSTEP5スキップ");
  }

  // STEP 6: PSM 再有効化 → deep sleep
  setupPSM();
  goToDeepSleep(GPS_INTERVAL_MIN);  // 本番値30分（PSM電流実測の測定時間も兼ねる）
}

void loop() {
  // setup() 末尾の deep sleep で到達しない
}

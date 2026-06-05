/*
 * 猫GPSトラッカー ファームウェア
 * MCU: ATtiny3226 (tinyAVR 2-Series) @ 8MHz内蔵発振器
 *
 * ピン割り当て（VQFN-20 物理パッド番号）:
 *   PA1 (pad12) = TxD0 (USART0 ALT1) → E220 RXD    ← PORTMUX ALT1必須
 *   PA2 (pad11) = RxD0 (USART0 ALT1) ← E220 TXD    ← PORTMUX ALT1必須
 *   PC1 (pad7)  = RxD1 (USART1 ALT1) ← GPS TXD     ← PORTMUX ALT1必須
 *   PC2 (pad8)  = TxD1 (USART1 ALT1) → GPS RXD     ← PORTMUX ALT1必須
 *   PB0 (pad6)  = GPIO out            → E220 M1
 *
 * 重要: PORTMUX.USARTROUTEA = 0x05 (USART0_ALT1 | USART1_ALT1) を設定すること。
 *   未設定時: USART0→PB[3:0], USART1→PA[4:1] (どちらも間違ったピン)
 */

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <util/delay.h>
#include <stdint.h>
#include <string.h>

/* ====== 定数 ====== */
#define F_CPU         8000000UL
#define BAUD_UART     9600UL
#define BAUD_SETTING  ((F_CPU / (16UL * BAUD_UART)) - 1)  /* 51 at 8MHz/9600 */

/* E220 M1制御 (PB0) */
#define E220_M1_DIR   PORTB.DIR
#define E220_M1_OUT   PORTB.OUT
#define E220_M1_PIN   PIN0_bm

/* RTC PITスリープサイクル数 (1秒×N ≒ 27分) */
#define SLEEP_CYCLES  1620  /* 1s × 1620 = 27分 */

/* GPSコマンド (NMEAチェックサム計算済み) */
#define GPS_WAKE_CMD  "$PCAS04,1*18\r\n"
#define GPS_SLEEP_CMD "$PCAS04,0*19\r\n"

/* ゲートウェイコマンド */
#define GW_CMD_REQ_POS 0x01

/* GPS補足タイムアウト (ms) */
#define GPS_TIMEOUT_MS 90000UL

/* ====== パケット構造体 ====== */
typedef struct {
    int32_t  lat;  /* 緯度 × 1,000,000 */
    int32_t  lon;  /* 経度 × 1,000,000 */
    uint32_t seq;  /* 送信カウンター */
} __attribute__((packed)) LoraPacket;

/* ====== グローバル変数 ====== */
static volatile uint16_t pit_count = 0;   /* RTC PIT カウンター (1カウント=1秒) */
static          uint32_t pkt_seq   = 0;
static          char     gps_line[96];    /* GPS NMEAラインバッファ (スタック節約) */

/* ====== クロック設定 (20MHz→8MHz) ====== */
static void clock_init(void)
{
    /* fuse2=0x01 (FREQSEL_16MHZ) を前提。
     * prescaler /2 → 16MHz÷2 = 8MHz。
     * CLKCTRL_PDIV_2X_gc=0x00 なので MCLKCTRLB = 0x01 (PEN=1, PDIV=0→2X) */
    CPU_CCP = CCP_IOREG_gc;
    CLKCTRL.MCLKCTRLB = CLKCTRL_PDIV_2X_gc | CLKCTRL_PEN_bm;  /* 16MHz÷2 = 8MHz */
}

/* ====== PORTMUX 設定 ====== */
static void portmux_init(void)
{
    /* USART0 ALT1: PA1=TxD0, PA2=RxD0 (default PB[3:0] から変更)
     * USART1 ALT1: PC2=TxD1, PC1=RxD1 (default PA[4:1] から変更)
     * 0x01 | (0x01<<2) = 0x05 */
    PORTMUX.USARTROUTEA = PORTMUX_USART0_ALT1_gc | PORTMUX_USART1_ALT1_gc;
}

/* ====== USART0 (E220) ====== */
static void usart0_init(void)
{
    USART0.BAUD = (uint16_t)(((uint32_t)F_CPU * 64) / (16UL * BAUD_UART));
    USART0.CTRLB = USART_TXEN_bm | USART_RXEN_bm;
    PORTA.DIR |= PIN1_bm;   /* PA1=TxD0 出力 */
    PORTA.DIR &= ~PIN2_bm;  /* PA2=RxD0 入力 */
}

static void usart0_putchar(uint8_t c)
{
    while (!(USART0.STATUS & USART_DREIF_bm));
    USART0.TXDATAL = c;
}

static void usart0_send(const uint8_t *buf, uint8_t len)
{
    for (uint8_t i = 0; i < len; i++) usart0_putchar(buf[i]);
}

/* タイムアウト付き1バイト受信 (ms単位・概算) */
static uint8_t usart0_recv_timeout(uint8_t *c, uint16_t timeout_ms)
{
    uint32_t ticks = (uint32_t)timeout_ms * (F_CPU / 1000) / 16;
    while (ticks--) {
        if (USART0.STATUS & USART_RXCIF_bm) {
            *c = USART0.RXDATAL;
            return 1;
        }
    }
    return 0;
}

/* ====== USART1 (GPS) ====== */
static void usart1_init(void)
{
    USART1.BAUD = (uint16_t)(((uint32_t)F_CPU * 64) / (16UL * BAUD_UART));
    USART1.CTRLB = USART_TXEN_bm | USART_RXEN_bm;
    PORTC.DIR |= PIN2_bm;   /* PC2=TxD1 出力 */
    PORTC.DIR &= ~PIN1_bm;  /* PC1=RxD1 入力 */
}

static void usart1_putchar(uint8_t c)
{
    while (!(USART1.STATUS & USART_DREIF_bm));
    USART1.TXDATAL = c;
}

static void usart1_send_str(const char *s)
{
    while (*s) usart1_putchar((uint8_t)*s++);
}

/* タイムアウト付き1行受信（\nまで or バッファ満杯） */
static uint8_t usart1_recv_line(char *buf, uint8_t maxlen, uint32_t timeout_ms)
{
    uint8_t idx = 0;
    uint32_t ticks_per_ms = F_CPU / 1000 / 16;
    uint32_t total_ticks  = timeout_ms * ticks_per_ms;

    while (total_ticks) {
        if (USART1.STATUS & USART_RXCIF_bm) {
            char c = (char)USART1.RXDATAL;
            if (c == '\n') {
                buf[idx] = '\0';
                return idx;
            }
            if (idx < maxlen - 1) buf[idx++] = c;
        } else {
            total_ticks--;
        }
    }
    buf[idx] = '\0';
    return 0;
}

/* ====== E220 モード制御 ====== */
static void e220_init(void)
{
    E220_M1_DIR |= E220_M1_PIN;
    E220_M1_OUT &= ~E220_M1_PIN;  /* M1=0 通常モード */
}

static void e220_set_normal(void) { E220_M1_OUT &= ~E220_M1_PIN; _delay_ms(2); }
static void e220_set_wor(void)    { E220_M1_OUT |=  E220_M1_PIN; _delay_ms(2); }

/* ====== GPS 制御 ====== */
static void gps_wake(void)  { usart1_send_str(GPS_WAKE_CMD);  }
static void gps_sleep(void) { usart1_send_str(GPS_SLEEP_CMD); }

/* ====== NMEA パース ====== */
/* "DDMM.MMMM" → int32_t (度 × 1,000,000) */
static int32_t parse_ddmm(const char *s, char hemi)
{
    /* 整数部と小数部を分離 */
    uint32_t ipart = 0;
    uint32_t fpart = 0;
    uint8_t  fdigs = 0;
    const char *p = s;

    while (*p && *p != '.') { ipart = ipart * 10 + (*p - '0'); p++; }
    if (*p == '.') {
        p++;
        while (*p && fdigs < 4) { fpart = fpart * 10 + (*p - '0'); fdigs++; p++; }
        while (fdigs++ < 4) fpart *= 10;
    }

    /* DDを度に変換 (int部の上2桁=度、下2桁=分整数) */
    uint32_t deg = ipart / 100;
    uint32_t min_int = ipart % 100;
    /* 分を度に: (min_int + fpart/10000) / 60 × 1,000,000 */
    int32_t result = (int32_t)(deg * 1000000UL
                     + (min_int * 1000000UL + fpart * 100UL) / 60UL);

    return (hemi == 'S' || hemi == 'W') ? -result : result;
}

/* $GNRMCまたは$GPRMCを探してlat/lonを取得。有効データなら1を返す */
static uint8_t parse_gnrmc(const char *line, int32_t *lat, int32_t *lon)
{
    if (strncmp(line, "$GNRMC,", 7) != 0 && strncmp(line, "$GPRMC,", 7) != 0)
        return 0;

    /* フィールドを分解 */
    char fields[10][16];
    uint8_t fi = 0;
    uint8_t ci = 0;
    const char *p = line + 1; /* '$'の次から */

    while (*p && fi < 10) {
        if (*p == ',' || *p == '*') {
            fields[fi][ci] = '\0';
            fi++;
            ci = 0;
        } else if (ci < 15) {
            fields[fi][ci++] = *p;
        }
        p++;
    }

    /* field[2]='A'が有効 */
    if (fields[2][0] != 'A') return 0;

    *lat = parse_ddmm(fields[3], fields[4][0]);
    *lon = parse_ddmm(fields[5], fields[6][0]);
    return 1;
}

/* ====== GPS補足 ====== */
static LoraPacket acquire_gps(void)
{
    LoraPacket pkt = { .lat = 0, .lon = 0, .seq = pkt_seq++ };
    uint32_t elapsed = 0;

    while (elapsed < GPS_TIMEOUT_MS) {
        uint8_t len = usart1_recv_line(gps_line, sizeof(gps_line), 500);
        elapsed += 500;
        if (len && parse_gnrmc(gps_line, &pkt.lat, &pkt.lon)) break;
    }
    return pkt;
}

/* ====== LoRa送信 ====== */
static void lora_send(const LoraPacket *pkt)
{
    e220_set_normal();
    usart0_send((const uint8_t *)pkt, sizeof(LoraPacket));
    _delay_ms(500);  /* AUX未接続のため固定ウェイト */
}

/* ====== ゲートウェイコマンドポーリング (60秒) ====== */
static void poll_gateway(void)
{
    for (uint8_t i = 0; i < 30; i++) {
        uint8_t cmd;
        if (usart0_recv_timeout(&cmd, 2000) && cmd == GW_CMD_REQ_POS) {
            gps_wake();
            LoraPacket pkt = acquire_gps();
            gps_sleep();
            lora_send(&pkt);
        }
    }
}

/* ====== RTC PIT スリープ (~27分) ====== */
/* ATtiny3226はWDT割り込みなし(リセットのみ)。RTC PIT を使う。 */

/* PIT割り込みハンドラ: 1秒ごとに呼ばれる */
ISR(RTC_PIT_vect)
{
    RTC.PITINTFLAGS = RTC_PI_bm;  /* フラグクリア */
    pit_count++;
}

static void rtc_pit_init(void)
{
    /* 32.768kHz ULP内蔵発振器を選択 */
    RTC.CLKSEL = RTC_CLKSEL_INT32K_gc;
    while (RTC.STATUS & RTC_CTRLABUSY_bm);   /* 同期待ち */

    /* PIT周期: 32768サイクル = 1秒 */
    RTC.PITCTRLA = RTC_PERIOD_CYC32768_gc | RTC_PITEN_bm;
    while (RTC.PITSTATUS & RTC_CTRLABUSY_bm);

    RTC.PITINTCTRL = RTC_PI_bm;  /* PIT割り込み有効 */
}

static void sleep_27min(void)
{
    pit_count = 0;
    sei();

    while (pit_count < SLEEP_CYCLES) {  /* 1620秒 = 27分 */
        SLPCTRL.CTRLA = SLPCTRL_SMODE_PDOWN_gc | SLPCTRL_SEN_bm;
        sleep_cpu();
    }
}

/* ====== メインループ ====== */
int main(void)
{
    clock_init();
    portmux_init();  /* USARTピン割り当て: ALT1に変更 (必ずUSART有効化前) */
    usart0_init();
    usart1_init();
    e220_init();
    rtc_pit_init();

    _delay_ms(1000);  /* E220起動待ち (データシート推奨: 数百ms以上) */

    while (1) {
        /* 1. GPS起動 */
        gps_wake();

        /* 2. GPS補足（最大90秒）→ パケット生成 */
        LoraPacket pkt = acquire_gps();

        /* 3. GPS停止 */
        gps_sleep();

        /* 4. LoRa送信 */
        lora_send(&pkt);

        /* 5. ゲートウェイコマンド待機（60秒） */
        poll_gateway();

        /* 6. E220をWORモードにしてスリープ (~27分) */
        e220_set_wor();
        sleep_27min();
    }
}

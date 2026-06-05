MCU     = attiny3226
F_CPU   = 8000000
CC      = avr-gcc
OBJCOPY = avr-objcopy

CFLAGS  = -mmcu=$(MCU) -DF_CPU=$(F_CPU)UL -Os -Wall -Wextra \
          -std=c11 -ffunction-sections -fdata-sections
LDFLAGS = -mmcu=$(MCU) -Wl,--gc-sections

TARGET  = tracker
SRC     = main.c

# UPDI書き込み設定（SerialUPDI方式）
# SERIAL_PORT を実際のデバイスに変更すること
SERIAL_PORT = /dev/cu.usbserial-XXXX

all: $(TARGET).hex

$(TARGET).elf: $(SRC)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

$(TARGET).hex: $(TARGET).elf
	$(OBJCOPY) -O ihex -R .eeprom $< $@
	avr-size --format=avr --mcu=$(MCU) $<

# SerialUPDI書き込み (avrdude 8.x)
flash: $(TARGET).hex
	avrdude -c serialupdi -P $(SERIAL_PORT) -p $(MCU) -U flash:w:$(TARGET).hex:i

# fuse設定書き込み
# FUSE2=0x01(FREQSEL_16MHZ), FUSE4=0xF6(UPDI有効・EESAVE), FUSE5=0x08(64ms起動)
# firmware内でprescaler/2→8MHz動作
fuse:
	avrdude -c serialupdi -P $(SERIAL_PORT) -p $(MCU) \
	  -U fuse2:w:0x01:m \
	  -U fuse4:w:0xF6:m \
	  -U fuse5:w:0x08:m

# fuse現在値の読み出し
fuse-read:
	avrdude -c serialupdi -P $(SERIAL_PORT) -p $(MCU) \
	  -U fuse0:r:-:h \
	  -U fuse1:r:-:h \
	  -U fuse2:r:-:h \
	  -U fuse4:r:-:h \
	  -U fuse5:r:-:h

# pymcuprog での書き込み（avrdude代替）
flash-pymc: $(TARGET).hex
	pymcuprog write -t uart -u $(SERIAL_PORT) -d attiny3226 --verify -f $(TARGET).hex

clean:
	rm -f $(TARGET).elf $(TARGET).hex

.PHONY: all flash fuse fuse-read flash-pymc clean

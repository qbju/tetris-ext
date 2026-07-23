BUILD := ../build
LINKER := hello.ld
SOURCES := hello.c cat.c edit.c ls.c mkdir.c cd.c pwd.c echo.c clear.c help.c cp.c mv.c rm.c touch.c info.c date.c ps.c uname.c uptime.c extinfo.c kv.c sector.c fsck.c hexdump.c run.c kill.c reboot.c forth.c
TARGETS := $(SOURCES:%.c=$(BUILD)/%.elf)
CFLAGS := -m32 -ffreestanding -fno-pic -fno-pie -fno-stack-protector -nostdlib -static -no-pie
LDFLAGS := -Wl,--build-id=none -Wl,-T,$(LINKER)

.PHONY: all clean

all: $(TARGETS)

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.elf: %.c $(LINKER) | $(BUILD)
	gcc $(CFLAGS) $(LDFLAGS) -o $@ $<

clean:
	rm -f $(TARGETS)
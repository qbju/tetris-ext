BUILD := ../build
LINKER := hello.ld
SOURCES := hello.c cat.c edit.c ls.c mkdir.c cd.c pwd.c echo.c clear.c help.c cp.c mv.c rm.c touch.c info.c date.c ps.c uname.c uptime.c extinfo.c kv.c sector.c fsck.c hexdump.c run.c kill.c reboot.c forthc.c
TARGETS := $(SOURCES:%.c=$(BUILD)/%.elf)
CFLAGS := -m32 -ffreestanding -fno-pic -fno-pie -fno-stack-protector -nostdlib -static -no-pie
LDFLAGS := -Wl,--build-id=none -Wl,-T,$(LINKER)

.PHONY: all clean

all: $(TARGETS)

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.elf: %.c $(LINKER) | $(BUILD)
	gcc $(CFLAGS) $(LDFLAGS) -o $@ $<

forth_runtime_blob.h: forth_runtime.c hello.ld tools/embed_forth_runtime.py | $(BUILD)
	gcc $(CFLAGS) $(LDFLAGS) -o $(BUILD)/forth_runtime.elf forth_runtime.c
	python3 tools/embed_forth_runtime.py
$(BUILD)/forthc.elf: forth_runtime_blob.h

clean:
	rm -f $(TARGETS)
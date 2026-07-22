# LPython extension: the inverse of the built-in 01 palette.
ext_onezerotheme_frame: i32 = 0


def ext_onezerotheme_palette(index: i32, red: i32, green: i32, blue: i32) -> None:
    ui_set_palette_entry(index, red, green, blue)



def ext_onezerotheme_apply() -> None:
    index: i32 = 0
    while index < 16:
        # Built-in 01 is black for 0..6 and white for 7..15. Reverse it.
        value: i32 = 63 if index < 7 else 0
        ext_onezerotheme_palette(index, value, value, value)
        index = index + 1


def ext_onezerotheme_enter() -> None:
    global ext_onezerotheme_frame
    ext_onezerotheme_frame = 0
    ext_onezerotheme_apply()


def ext_onezerotheme_update() -> None:
    global ext_onezerotheme_frame
    ext_onezerotheme_frame = ext_onezerotheme_frame + 1


def ext_onezerotheme_exit() -> None:
    global ext_onezerotheme_frame
    ext_onezerotheme_frame = 0


def ext_onezerotheme_draw() -> None:
    clear_screen(0x0F)
    text(29, 2, 79, 0x0F); text(30, 2, 78, 0x0F); text(31, 2, 69, 0x0F)
    text(33, 2, 90, 0x0F); text(34, 2, 69, 0x0F); text(35, 2, 82, 0x0F); text(36, 2, 79, 0x0F)
    text(38, 2, 84, 0x0F); text(39, 2, 72, 0x0F); text(40, 2, 69, 0x0F); text(41, 2, 77, 0x0F); text(42, 2, 69, 0x0F)
    y: i32 = 5
    while y < 20:
        x: i32 = 8
        while x < 72:
            text(x, y, 48 + ((x + y) & 1), 0x0F)
            x = x + 1
        y = y + 2
    # White card uses palette 0; black ink uses palette 15 under this theme.
    ui_fill_rect(72, 64, 176, 64, 0)
    text(26, 9, 48, 0x0F); text(28, 9, 49, 0x0F); text(30, 9, 48, 0x0F); text(32, 9, 49, 0x0F)
    text(34, 9, 73, 0x0F); text(35, 9, 78, 0x0F); text(36, 9, 86, 0x0F); text(37, 9, 69, 0x0F); text(38, 9, 82, 0x0F); text(39, 9, 84, 0x0F); text(40, 9, 69, 0x0F); text(41, 9, 68, 0x0F)
    text(22, 22, 69, 0x0F); text(23, 22, 78, 0x0F); text(24, 22, 84, 0x0F); text(25, 22, 69, 0x0F); text(26, 22, 82, 0x0F)
    text(28, 22, 65, 0x0F); text(29, 22, 80, 0x0F); text(30, 22, 80, 0x0F); text(31, 22, 76, 0x0F); text(32, 22, 89, 0x0F)
    text(36, 22, 69, 0x0F); text(37, 22, 83, 0x0F); text(38, 22, 67, 0x0F)
    text(33, 22, 66, 0x0F); text(34, 22, 65, 0x0F); text(35, 22, 67, 0x0F); text(36, 22, 75, 0x0F)


def ext_onezerotheme_key(key: i32) -> i32:
    if key == 0x1C:
        ext_onezerotheme_apply()
        return 2
    return 0
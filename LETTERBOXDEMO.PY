# permissions: background
# Demonstrates drawing into the physical 40px top and bottom framebuffer bars.
ext_letterboxdemo_enabled: i32 = 1
ext_letterboxdemo_last: i32 = -100
ext_letterboxdemo_frame: i32 = 0


def ext_letterboxdemo_render_bars() -> None:
    extension_letterbox_fill(0, 0)
    extension_letterbox_fill(1, 0)
    extension_letterbox_draw_text(0, 0, 2, "TETRIS OS  /  PHYSICAL FRAMEBUFFER", 0x0B)
    extension_letterbox_draw_text(0, 1, 2, "TOP BAR: Y 0..39", 0x07)
    extension_letterbox_draw_text(1, 0, 2, "LETTERBOXDEMO.PY", 0x0E)
    extension_letterbox_draw_text(1, 1, 2, "RUNNING IN BACKGROUND  [B] TOGGLE", 0x0A)


def ext_letterboxdemo_enter() -> None:
    global ext_letterboxdemo_enabled, ext_letterboxdemo_last
    ext_letterboxdemo_enabled = 1
    ext_letterboxdemo_last = -100
    extension_background_set(1)
    ext_letterboxdemo_render_bars()


def ext_letterboxdemo_background() -> None:
    global ext_letterboxdemo_last, ext_letterboxdemo_frame
    if ext_letterboxdemo_enabled == 0: return
    if system_periods - ext_letterboxdemo_last < 25: return
    ext_letterboxdemo_last = system_periods
    ext_letterboxdemo_frame = (ext_letterboxdemo_frame + 1) % 4
    glyph: i32 = 124
    if ext_letterboxdemo_frame == 1: glyph = 47
    elif ext_letterboxdemo_frame == 2: glyph = 45
    elif ext_letterboxdemo_frame == 3: glyph = 92
    ui_letterbox_put_cell(616, 452, glyph, 0x0E)


def ext_letterboxdemo_update() -> None:
    global ext_letterboxdemo_frame
    ext_letterboxdemo_frame = ext_letterboxdemo_frame


def ext_letterboxdemo_draw() -> None:
    clear_screen(0x10)
    extension_draw_text_centered(4, "LETTERBOX FRAMEBUFFER DEMO", 0x0E)
    extension_draw_text_centered(9, "TOP AND BOTTOM ARE PHYSICAL 640PX", 0x0F)
    extension_draw_text_centered(12, "B TOGGLES BACKGROUND BAR OUTPUT", 0x0A)
    extension_draw_text_centered(20, "ESC RETURNS - BARS KEEP RUNNING", 0x07)


def ext_letterboxdemo_key(key: i32) -> i32:
    global ext_letterboxdemo_enabled
    if key == 0x30:
        ext_letterboxdemo_enabled = 0 if ext_letterboxdemo_enabled == 1 else 1
        extension_background_set(ext_letterboxdemo_enabled)
        if ext_letterboxdemo_enabled == 1: ext_letterboxdemo_render_bars()
        else: extension_letterbox_clear()
        return 3
    return 0


def ext_letterboxdemo_exit() -> None:
    global ext_letterboxdemo_last
    # Intentionally keep the registered background task alive as a demo.
    ext_letterboxdemo_last = ext_letterboxdemo_last
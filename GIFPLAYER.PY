# permissions: image.process framebuffer.native
# Built-in animated GIF viewer for smallplay.gif.
ext_gifplayer_length: i32 = 0
ext_gifplayer_frame: i32 = 0
ext_gifplayer_deadline: i32 = 0
ext_gifplayer_ready: i32 = 0
ext_gifplayer_status: i32 = 0


def ext_gifplayer_enter() -> None:
    global ext_gifplayer_length, ext_gifplayer_frame, ext_gifplayer_deadline, ext_gifplayer_ready, ext_gifplayer_status
    ext_gifplayer_length = extension_gif_load_builtin()
    ext_gifplayer_frame = 0
    if ext_gifplayer_length > 0:
        extension_image_clear(80 * 45, 0)
        ext_gifplayer_status = extension_gif_decode_frame(ext_gifplayer_length, 0)
        ext_gifplayer_ready = 1 if ext_gifplayer_status > 0 else 0
    else:
        ext_gifplayer_ready = 0
    ext_gifplayer_deadline = system_periods + 100


def ext_gifplayer_update() -> None:
    global ext_gifplayer_frame, ext_gifplayer_deadline, ext_gifplayer_ready, ext_gifplayer_status
    if ext_gifplayer_ready == 0 or system_periods < ext_gifplayer_deadline: return
    ext_gifplayer_frame = (ext_gifplayer_frame + 1) % 59
    if ext_gifplayer_frame == 0: extension_image_clear(80 * 45, 0)
    ext_gifplayer_status = extension_gif_decode_frame(ext_gifplayer_length, ext_gifplayer_frame)
    if ext_gifplayer_status < 0: ext_gifplayer_ready = 0
    ext_gifplayer_deadline = system_periods + 100
    extension_request_redraw()


def ext_gifplayer_draw() -> None:
    clear_screen(0x10)
    extension_native_fill_rect(0, 0, 640, 480, 0)
    if ext_gifplayer_ready == 1:
        extension_image_blit_scaled(80, 45, 0, 60, 640, 360, -1)
        extension_native_draw_text(12, 12, "SMALLPLAY.GIF  /  GIF89A ANIMATION", 0x0F)
        extension_native_draw_text(12, 444, "ESC: BACK   GIF LZW / 80X45 / 1 FPS", 0x0E)
    else:
        extension_native_draw_text(12, 12, "GIF DECODE FAILED", 0x0C)
        if ext_gifplayer_status == -8: extension_native_draw_text(12, 32, "LZW STREAM ERROR", 0x0F)
        elif ext_gifplayer_status == -7: extension_native_draw_text(12, 32, "INTERLACE UNSUPPORTED", 0x0F)
        elif ext_gifplayer_status == -6: extension_native_draw_text(12, 32, "FRAME NOT FOUND", 0x0F)
        elif ext_gifplayer_status == -5: extension_native_draw_text(12, 32, "TRUNCATED GIF DATA", 0x0F)
        else: extension_native_draw_text(12, 32, "HEADER OR BUFFER ERROR", 0x0F)


def ext_gifplayer_key(key: i32) -> i32:
    if key == 0x01: return 0
    return 0


def ext_gifplayer_exit() -> None:
    extension_gif_restore_palette()

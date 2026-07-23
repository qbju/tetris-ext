# permissions: settings.read settings.write settings.save autostart
# Shared integer easing functions plus an animated comparison extension.
ext_easingpack_start: i32 = 0
ext_easingpack_last: i32 = -1
ext_easingpack_os_enabled: i32 = 0
ext_easingpack_transition_start: i32 = 0


def ext_easingpack_linear(value: i32, scale: i32) -> i32:
    return value


def ext_easingpack_in_quad(value: i32, scale: i32) -> i32:
    return (value * value) // scale


def ext_easingpack_out_quad(value: i32, scale: i32) -> i32:
    remaining: i32 = scale - value
    return scale - (remaining * remaining) // scale


def ext_easingpack_out_cubic(value: i32, scale: i32) -> i32:
    remaining: i32 = scale - value
    return scale - (remaining * remaining * remaining) // (scale * scale)


def ext_easingpack_render() -> None:
    elapsed: i32 = (system_periods - ext_easingpack_start) % 200
    progress: i32 = elapsed if elapsed <= 100 else 200 - elapsed
    ui_fill_rect(96, 48, 192, 128, 1)
    linear_x: i32 = 104 + (168 * ext_easingpack_linear(progress, 100)) // 100
    in_x: i32 = 104 + (168 * ext_easingpack_in_quad(progress, 100)) // 100
    out_x: i32 = 104 + (168 * ext_easingpack_out_quad(progress, 100)) // 100
    cubic_x: i32 = 104 + (168 * ext_easingpack_out_cubic(progress, 100)) // 100
    ui_fill_rect(linear_x, 56, 8, 8, 14)
    ui_fill_rect(in_x, 88, 8, 8, 10)
    ui_fill_rect(out_x, 120, 8, 8, 11)
    ui_fill_rect(cubic_x, 152, 8, 8, 13)


def ext_easingpack_enter() -> None:
    global ext_easingpack_start, ext_easingpack_last
    ext_easingpack_start = system_periods
    ext_easingpack_last = -1


def ext_easingpack_update() -> None:
    global ext_easingpack_last
    now: i32 = system_periods
    if now == ext_easingpack_last: return
    ext_easingpack_last = now
    ext_easingpack_render()


def ext_easingpack_exit() -> None:
    global ext_easingpack_last
    ext_easingpack_last = -1


def ext_easingpack_draw() -> None:
    clear_screen(0x10)
    text(30, 2, 69, 0x0E); text(31, 2, 65, 0x0E); text(32, 2, 83, 0x0E); text(33, 2, 73, 0x0E); text(34, 2, 78, 0x0E); text(35, 2, 71, 0x0E)
    text(37, 2, 80, 0x0F); text(38, 2, 65, 0x0F); text(39, 2, 67, 0x0F); text(40, 2, 75, 0x0F)
    text(29, 4, 16, 0x0E); text(31, 4, 79, 0x0B); text(32, 4, 83, 0x0B); text(34, 4, 69, 0x0B); text(35, 4, 65, 0x0B); text(36, 4, 83, 0x0B); text(37, 4, 73, 0x0B); text(38, 4, 78, 0x0B); text(39, 4, 71, 0x0B)
    if ext_easingpack_os_enabled == 1:
        text(42, 4, 79, 0x0A); text(43, 4, 78, 0x0A)
    else:
        text(41, 4, 79, 0x08); text(42, 4, 70, 0x08); text(43, 4, 70, 0x08)
    text(3, 7, 76, 0x0F); text(4, 7, 73, 0x0F); text(5, 7, 78, 0x0F); text(6, 7, 69, 0x0F); text(7, 7, 65, 0x0F); text(8, 7, 82, 0x0F)
    text(3, 11, 73, 0x0A); text(4, 11, 78, 0x0A); text(6, 11, 81, 0x0A); text(7, 11, 85, 0x0A); text(8, 11, 65, 0x0A); text(9, 11, 68, 0x0A)
    text(3, 15, 79, 0x0B); text(4, 15, 85, 0x0B); text(5, 15, 84, 0x0B); text(7, 15, 81, 0x0B); text(8, 15, 85, 0x0B); text(9, 15, 65, 0x0B); text(10, 15, 68, 0x0B)
    text(3, 19, 79, 0x0D); text(4, 19, 85, 0x0D); text(5, 19, 84, 0x0D); text(7, 19, 67, 0x0D); text(8, 19, 85, 0x0D); text(9, 19, 66, 0x0D); text(10, 19, 73, 0x0D); text(11, 19, 67, 0x0D)
    text(31, 23, 69, 0x0C); text(32, 23, 83, 0x0C); text(33, 23, 67, 0x0C); text(35, 23, 66, 0x07); text(36, 23, 65, 0x07); text(37, 23, 67, 0x07); text(38, 23, 75, 0x07)
    ext_easingpack_render()


def ext_easingpack_transition_enabled() -> i32:
    return ext_easingpack_os_enabled


def ext_easingpack_transition_begin() -> None:
    global ext_easingpack_transition_start
    ext_easingpack_transition_start = system_periods


def ext_easingpack_transition_step() -> i32:
    elapsed: i32 = system_periods - ext_easingpack_transition_start
    if elapsed >= 30: return 320
    if elapsed < 0: elapsed = 0
    remaining: i32 = 30 - elapsed
    eased: i32 = 30 - (remaining * remaining * remaining) // 900
    return (320 * eased) // 30

def ext_easingpack_key(key: i32) -> i32:
    global ext_easingpack_start, ext_easingpack_os_enabled
    if key == 0x1C:
        ext_easingpack_os_enabled = 1 - ext_easingpack_os_enabled
        ext_easingpack_start = system_periods
    return 0
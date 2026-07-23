# permissions: framebuffer.native
# Multi-window desktop extension. Child extensions render into a dedicated
# offscreen surface and are composited into up to three logical windows.
ext_windowcursor_launcher_x: i32 = 8
ext_windowcursor_launcher_y: i32 = 24
ext_windowcursor_cursor_x: i32 = 160
ext_windowcursor_cursor_y: i32 = 100
ext_windowcursor_active: i32 = -1
ext_windowcursor_dragging: i32 = -1  # -2 launcher, -1 none, 0..2 child
ext_windowcursor_mouse_buttons: i32 = 0
ext_windowcursor_mouse_accum_x: i32 = 0
ext_windowcursor_mouse_accum_y: i32 = 0
ext_windowcursor_child_0: i32 = -1
ext_windowcursor_child_1: i32 = -1
ext_windowcursor_child_2: i32 = -1
ext_windowcursor_x_0: i32 = 160
ext_windowcursor_y_0: i32 = 24
ext_windowcursor_x_1: i32 = 132
ext_windowcursor_y_1: i32 = 48
ext_windowcursor_x_2: i32 = 104
ext_windowcursor_y_2: i32 = 72
ext_windowcursor_z_0: i32 = 0
ext_windowcursor_z_1: i32 = 1
ext_windowcursor_z_2: i32 = 2
ext_windowcursor_z_clock: i32 = 3


def ext_windowcursor_child_get(slot: i32) -> i32:
    if slot == 0: return ext_windowcursor_child_0
    if slot == 1: return ext_windowcursor_child_1
    if slot == 2: return ext_windowcursor_child_2
    return -1


def ext_windowcursor_child_set(slot: i32, value: i32) -> None:
    global ext_windowcursor_child_0, ext_windowcursor_child_1, ext_windowcursor_child_2
    if slot == 0: ext_windowcursor_child_0 = value
    elif slot == 1: ext_windowcursor_child_1 = value
    elif slot == 2: ext_windowcursor_child_2 = value


def ext_windowcursor_x_get(slot: i32) -> i32:
    if slot == 0: return ext_windowcursor_x_0
    if slot == 1: return ext_windowcursor_x_1
    return ext_windowcursor_x_2


def ext_windowcursor_y_get(slot: i32) -> i32:
    if slot == 0: return ext_windowcursor_y_0
    if slot == 1: return ext_windowcursor_y_1
    return ext_windowcursor_y_2


def ext_windowcursor_position_set(slot: i32, x: i32, y: i32) -> None:
    global ext_windowcursor_x_0, ext_windowcursor_x_1, ext_windowcursor_x_2, ext_windowcursor_y_0, ext_windowcursor_y_1, ext_windowcursor_y_2
    next_x: i32 = x
    next_y: i32 = y
    if next_x < 4: next_x = 4
    if next_x > 148: next_x = 148
    if next_y < 8: next_y = 8
    if next_y > 104: next_y = 104
    if slot == 0: ext_windowcursor_x_0 = next_x; ext_windowcursor_y_0 = next_y
    elif slot == 1: ext_windowcursor_x_1 = next_x; ext_windowcursor_y_1 = next_y
    elif slot == 2: ext_windowcursor_x_2 = next_x; ext_windowcursor_y_2 = next_y


def ext_windowcursor_z_get(slot: i32) -> i32:
    if slot == 0: return ext_windowcursor_z_0
    if slot == 1: return ext_windowcursor_z_1
    return ext_windowcursor_z_2


def ext_windowcursor_z_set(slot: i32, value: i32) -> None:
    global ext_windowcursor_z_0, ext_windowcursor_z_1, ext_windowcursor_z_2
    if slot == 0: ext_windowcursor_z_0 = value
    elif slot == 1: ext_windowcursor_z_1 = value
    else: ext_windowcursor_z_2 = value


def ext_windowcursor_bring_front(slot: i32) -> None:
    global ext_windowcursor_active, ext_windowcursor_z_clock
    ext_windowcursor_z_set(slot, ext_windowcursor_z_clock)
    ext_windowcursor_z_clock = ext_windowcursor_z_clock + 1
    ext_windowcursor_active = slot


def ext_windowcursor_z_slot(after: i32) -> i32:
    best_slot: i32 = -1
    best_z: i32 = 2147483647
    slot: i32 = 0
    while slot < 3:
        z: i32 = ext_windowcursor_z_get(slot)
        if ext_windowcursor_child_get(slot) >= 0 and z > after and z < best_z:
            best_z = z
            best_slot = slot
        slot = slot + 1
    return best_slot


def ext_windowcursor_top_at_cursor() -> i32:
    best_slot: i32 = -1
    best_z: i32 = -1
    slot: i32 = 0
    while slot < 3:
        wx: i32 = ext_windowcursor_x_get(slot)
        wy: i32 = ext_windowcursor_y_get(slot)
        z: i32 = ext_windowcursor_z_get(slot)
        if ext_windowcursor_child_get(slot) >= 0 and ext_windowcursor_cursor_x >= wx and ext_windowcursor_cursor_x < wx + 168 and ext_windowcursor_cursor_y >= wy and ext_windowcursor_cursor_y < wy + 116 and z > best_z:
            best_slot = slot
            best_z = z
        slot = slot + 1
    return best_slot


def ext_windowcursor_app_at(row: i32) -> i32:
    own: i32 = extension_window_host_id()
    identifier: i32 = 0
    visible: i32 = 0
    while identifier < extension_count():
        if identifier != own:
            if visible == row: return identifier
            visible = visible + 1
        identifier = identifier + 1
    return -1


def ext_windowcursor_open(identifier: i32) -> None:
    global ext_windowcursor_active
    slot: i32 = 0
    while slot < 3:
        if ext_windowcursor_child_get(slot) == identifier:
            ext_windowcursor_bring_front(slot)
            return
        slot = slot + 1
    slot = 0
    while slot < 3 and ext_windowcursor_child_get(slot) >= 0:
        slot = slot + 1
    if slot >= 3: return
    ext_windowcursor_child_set(slot, identifier)
    ext_windowcursor_position_set(slot, 160 - slot * 28, 24 + slot * 24)
    ext_windowcursor_bring_front(slot)
    extension_enter(identifier)


def ext_windowcursor_close(slot: i32) -> None:
    global ext_windowcursor_active, ext_windowcursor_dragging
    identifier: i32 = ext_windowcursor_child_get(slot)
    if identifier >= 0: extension_exit(identifier)
    ext_windowcursor_child_set(slot, -1)
    if ext_windowcursor_active == slot: ext_windowcursor_active = -1
    if ext_windowcursor_dragging == slot: ext_windowcursor_dragging = -1


def ext_windowcursor_enter() -> None:
    global ext_windowcursor_cursor_x, ext_windowcursor_cursor_y, ext_windowcursor_active, ext_windowcursor_dragging, ext_windowcursor_mouse_buttons, ext_windowcursor_mouse_accum_x, ext_windowcursor_mouse_accum_y
    ext_windowcursor_mouse_buttons = 0
    ext_windowcursor_mouse_accum_x = 0
    ext_windowcursor_mouse_accum_y = 0
    ext_windowcursor_cursor_x = 64
    ext_windowcursor_cursor_y = 40
    ext_windowcursor_active = -1
    ext_windowcursor_dragging = -1
    ps2_mouse_init()


def ext_windowcursor_update_children() -> None:
    slot: i32 = 0
    while slot < 3:
        identifier: i32 = ext_windowcursor_child_get(slot)
        if identifier >= 0: extension_update(identifier)
        slot = slot + 1


def ext_windowcursor_press_window(slot: i32) -> i32:
    global ext_windowcursor_active, ext_windowcursor_dragging
    identifier: i32 = ext_windowcursor_child_get(slot)
    if identifier < 0: return 0
    wx: i32 = ext_windowcursor_x_get(slot)
    wy: i32 = ext_windowcursor_y_get(slot)
    if ext_windowcursor_cursor_x < wx or ext_windowcursor_cursor_x >= wx + 168 or ext_windowcursor_cursor_y < wy or ext_windowcursor_cursor_y >= wy + 116: return 0
    ext_windowcursor_bring_front(slot)
    if ext_windowcursor_cursor_x >= wx + 152 and ext_windowcursor_cursor_y < wy + 16:
        ext_windowcursor_close(slot)
    elif ext_windowcursor_cursor_y < wy + 16:
        ext_windowcursor_dragging = slot
    return 1

def ext_windowcursor_update() -> None:
    global ext_windowcursor_cursor_x, ext_windowcursor_cursor_y, ext_windowcursor_launcher_x, ext_windowcursor_launcher_y, ext_windowcursor_dragging, ext_windowcursor_active, ext_windowcursor_mouse_buttons, ext_windowcursor_mouse_accum_x, ext_windowcursor_mouse_accum_y
    ext_windowcursor_update_children()
    packet: i32 = ps2_mouse_poll()
    if packet >= 0: return
    old_buttons: i32 = ext_windowcursor_mouse_buttons
    buttons: i32 = extension_mouse_buttons(packet)
    ext_windowcursor_mouse_accum_x = ext_windowcursor_mouse_accum_x + extension_mouse_dx(packet)
    ext_windowcursor_mouse_accum_y = ext_windowcursor_mouse_accum_y + extension_mouse_dy(packet)
    move_x: i32 = 0
    raw_y: i32 = 0
    if ext_windowcursor_mouse_accum_x >= 2: move_x = ext_windowcursor_mouse_accum_x // 2
    elif ext_windowcursor_mouse_accum_x <= -2: move_x = 0 - ((0 - ext_windowcursor_mouse_accum_x) // 2)
    if ext_windowcursor_mouse_accum_y >= 2: raw_y = ext_windowcursor_mouse_accum_y // 2
    elif ext_windowcursor_mouse_accum_y <= -2: raw_y = 0 - ((0 - ext_windowcursor_mouse_accum_y) // 2)
    ext_windowcursor_mouse_accum_x = ext_windowcursor_mouse_accum_x - move_x * 2
    ext_windowcursor_mouse_accum_y = ext_windowcursor_mouse_accum_y - raw_y * 2
    move_y: i32 = 0 - raw_y
    ext_windowcursor_cursor_x = ext_windowcursor_cursor_x + move_x
    ext_windowcursor_cursor_y = ext_windowcursor_cursor_y + move_y
    if ext_windowcursor_cursor_x < 0: ext_windowcursor_cursor_x = 0
    if ext_windowcursor_cursor_x > 310: ext_windowcursor_cursor_x = 310
    if ext_windowcursor_cursor_y < 0: ext_windowcursor_cursor_y = 0
    if ext_windowcursor_cursor_y > 171: ext_windowcursor_cursor_y = 171
    if ext_windowcursor_dragging >= 0 and (buttons & 1) != 0:
        ext_windowcursor_position_set(ext_windowcursor_dragging, ext_windowcursor_x_get(ext_windowcursor_dragging) + move_x, ext_windowcursor_y_get(ext_windowcursor_dragging) + move_y)
    elif ext_windowcursor_dragging == -2 and (buttons & 1) != 0:
        ext_windowcursor_launcher_x = ext_windowcursor_launcher_x + move_x
        ext_windowcursor_launcher_y = ext_windowcursor_launcher_y + move_y
        if ext_windowcursor_launcher_x < 4: ext_windowcursor_launcher_x = 4
        if ext_windowcursor_launcher_x > 184: ext_windowcursor_launcher_x = 184
        if ext_windowcursor_launcher_y < 8: ext_windowcursor_launcher_y = 8
        if ext_windowcursor_launcher_y > 48: ext_windowcursor_launcher_y = 48
    if (buttons & 1) != 0 and (old_buttons & 1) == 0:
        handled: i32 = 0
        hit_slot: i32 = ext_windowcursor_top_at_cursor()
        if hit_slot >= 0: handled = ext_windowcursor_press_window(hit_slot)
        if handled == 0:
            lx: i32 = ext_windowcursor_launcher_x
            ly: i32 = ext_windowcursor_launcher_y
            if ext_windowcursor_cursor_x >= lx and ext_windowcursor_cursor_x < lx + 124 and ext_windowcursor_cursor_y >= ly and ext_windowcursor_cursor_y < ly + 144:
                if ext_windowcursor_cursor_y < ly + 16: ext_windowcursor_dragging = -2
                else:
                    row: i32 = (ext_windowcursor_cursor_y - ly - 16) // 16
                    app: i32 = ext_windowcursor_app_at(row)
                    if app >= 0: ext_windowcursor_open(app)
    if (buttons & 1) == 0: ext_windowcursor_dragging = -1
    ext_windowcursor_mouse_buttons = buttons
    if move_x != 0 or move_y != 0 or buttons != old_buttons: extension_request_redraw()


def ext_windowcursor_draw_launcher() -> None:
    lx: i32 = ext_windowcursor_launcher_x
    ly: i32 = ext_windowcursor_launcher_y
    ui_fill_rect(lx + 4, ly + 5, 124, 144, 0)
    ui_fill_rect(lx, ly, 124, 144, 15)
    ui_fill_rect(lx + 2, ly + 2, 120, 140, 1)
    ui_fill_rect(lx + 2, ly + 2, 120, 14, 10)
    ui_put_cell(lx // 4 + 2, ly // 8 + 1, 65, 0x0F); ui_put_cell(lx // 4 + 3, ly // 8 + 1, 80, 0x0F); ui_put_cell(lx // 4 + 4, ly // 8 + 1, 80, 0x0F); ui_put_cell(lx // 4 + 5, ly // 8 + 1, 83, 0x0F)
    row: i32 = 0
    while row < 7:
        identifier: i32 = ext_windowcursor_app_at(row)
        if identifier >= 0:
            cell_y: i32 = ly // 8 + 2 + row * 2
            ui_put_cell(lx // 4 + 2, cell_y, 16, 0x1E)
            length: i32 = extension_name_length(identifier)
            index: i32 = 0
            while index < length and index < 24:
                ui_put_cell(lx // 4 + 4 + index, cell_y, extension_name_char(identifier, index), 0x1F)
                index = index + 1
        row = row + 1


def ext_windowcursor_draw() -> None:
    # The desktop and launcher remain in the normal logical compositor.
    ui_fill_rect(0, 0, 320, 200, 1)
    ui_fill_rect(0, 184, 320, 16, 8)
    ext_windowcursor_draw_launcher()
    extension_draw_text_centered(23, "SHIFT+ARROWS MOVE ACTIVE WINDOW", 0x0A)


def ext_windowcursor_native_child(slot: i32) -> None:
    identifier: i32 = ext_windowcursor_child_get(slot)
    if identifier < 0: return
    # Render the complete child at its native logical 320x200 resolution.
    ui_set_render_target(2)
    extension_draw(identifier)
    ui_set_render_target(1)
    wx: i32 = ext_windowcursor_x_get(slot) * 2
    wy: i32 = ext_windowcursor_y_get(slot) * 2 + 40
    ui_native_fill_rect(wx + 8, wy + 8, 336, 232, 0)
    ui_native_fill_rect(wx, wy, 336, 232, 15)
    ui_native_fill_rect(wx + 4, wy + 4, 328, 224, 7)
    title_colour: i32 = 14 if slot == ext_windowcursor_active else 9
    ui_native_fill_rect(wx + 4, wy + 4, 328, 28, title_colour)
    ui_native_blit_child(wx + 8, wy + 32)
    length: i32 = extension_name_length(identifier)
    index: i32 = 0
    while index < length and index < 34:
        ui_native_put_cell(wx + 8 + index * 8, wy + 8, extension_name_char(identifier, index), 0x0F)
        index = index + 1
    ui_native_fill_rect(wx + 304, wy + 6, 24, 22, 12)
    ui_native_put_cell(wx + 312, wy + 9, 88, 0x0F)


def ext_windowcursor_native_overlay() -> None:
    # Remove the previous native windows using the already-presented logical
    # desktop, then compose every child as a true physical 320x200 viewport.
    ui_native_begin()
    ui_native_restore_surface()
    last_z: i32 = -1
    drawn: i32 = 0
    while drawn < 3:
        slot: i32 = ext_windowcursor_z_slot(last_z)
        if slot < 0: drawn = 3
        else:
            ext_windowcursor_native_child(slot)
            last_z = ext_windowcursor_z_get(slot)
            drawn = drawn + 1
    cx: i32 = ext_windowcursor_cursor_x * 2
    cy: i32 = ext_windowcursor_cursor_y * 2 + 40
    ui_native_fill_rect(cx, cy, 4, 26, 0); ui_native_fill_rect(cx, cy, 18, 4, 0)
    ui_native_fill_rect(cx, cy, 4, 4, 15)
    ui_native_fill_rect(cx + 4, cy + 4, 4, 16, 15)
    ui_native_fill_rect(cx + 8, cy + 4, 8, 4, 15)
    ui_native_fill_rect(cx + 12, cy + 12, 4, 10, 0)
    ui_native_end()

def ext_windowcursor_key(key: i32) -> i32:
    global ext_windowcursor_cursor_x, ext_windowcursor_cursor_y, ext_windowcursor_launcher_x, ext_windowcursor_launcher_y, ext_windowcursor_active
    dx: i32 = 0
    dy: i32 = 0
    if key == 0x4B: dx = -4
    elif key == 0x4D: dx = 4
    elif key == 0x48: dy = -8
    elif key == 0x50: dy = 8
    if keyboard_shifted == 1 and (dx != 0 or dy != 0):
        if ext_windowcursor_active >= 0:
            ext_windowcursor_position_set(ext_windowcursor_active, ext_windowcursor_x_get(ext_windowcursor_active) + dx, ext_windowcursor_y_get(ext_windowcursor_active) + dy)
        else:
            ext_windowcursor_launcher_x = ext_windowcursor_launcher_x + dx
            ext_windowcursor_launcher_y = ext_windowcursor_launcher_y + dy
        extension_request_redraw()
        return 0
    if ext_windowcursor_active >= 0:
        identifier: i32 = ext_windowcursor_child_get(ext_windowcursor_active)
        if key == 0x01:
            ext_windowcursor_close(ext_windowcursor_active)
            return 3
        result: i32 = extension_key(identifier, key)
        if result != 0: ext_windowcursor_close(ext_windowcursor_active)
        return 0
    if dx != 0 or dy != 0:
        ext_windowcursor_cursor_x = ext_windowcursor_cursor_x + dx
        ext_windowcursor_cursor_y = ext_windowcursor_cursor_y + dy
        if ext_windowcursor_cursor_x < 0: ext_windowcursor_cursor_x = 0
        if ext_windowcursor_cursor_x > 310: ext_windowcursor_cursor_x = 310
        if ext_windowcursor_cursor_y < 0: ext_windowcursor_cursor_y = 0
        if ext_windowcursor_cursor_y > 171: ext_windowcursor_cursor_y = 171
    if key == 0x1C:
        row: i32 = (ext_windowcursor_cursor_y - ext_windowcursor_launcher_y - 16) // 16
        if ext_windowcursor_cursor_x >= ext_windowcursor_launcher_x and ext_windowcursor_cursor_x < ext_windowcursor_launcher_x + 124 and row >= 0:
            app: i32 = ext_windowcursor_app_at(row)
            if app >= 0: ext_windowcursor_open(app)
    return 0


def ext_windowcursor_exit() -> None:
    global ext_windowcursor_dragging
    slot: i32 = 0
    while slot < 3:
        ext_windowcursor_close(slot)
        slot = slot + 1
    ext_windowcursor_dragging = -1
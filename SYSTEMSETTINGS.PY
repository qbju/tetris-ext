# permissions: settings.read settings.write settings.save settings.admin
# Administrative viewer for hidden OS settings and extension capabilities.
ext_systemsettings_page: i32 = 0
ext_systemsettings_selection: i32 = 0
ext_systemsettings_scroll: i32 = 0
ext_systemsettings_status: i32 = 0


def ext_systemsettings_draw_name(identifier: i32, x: i32, y: i32, colour: i32) -> None:
    length: i32 = extension_name_length(identifier)
    index: i32 = 0
    while index < length and index < 28:
        ui_put_cell(x + index, y, extension_name_char(identifier, index), colour)
        index = index + 1


def ext_systemsettings_draw_toggle(y: i32, label: str, enabled: i32) -> None:
    extension_draw_text(25, y, label, 0x07)
    if enabled != 0: extension_draw_text(56, y, "ALLOW", 0x0A)
    else: extension_draw_text(56, y, "--", 0x08)


def ext_systemsettings_enter() -> None:
    global ext_systemsettings_page, ext_systemsettings_selection, ext_systemsettings_scroll, ext_systemsettings_status
    ext_systemsettings_page = 0
    ext_systemsettings_selection = 0
    ext_systemsettings_scroll = 0
    ext_systemsettings_status = 0


def ext_systemsettings_update() -> None:
    idle: i32 = ext_systemsettings_page


def ext_systemsettings_exit() -> None:
    idle: i32 = ext_systemsettings_page


def ext_systemsettings_update_scroll() -> None:
    global ext_systemsettings_scroll
    if ext_systemsettings_selection < ext_systemsettings_scroll: ext_systemsettings_scroll = ext_systemsettings_selection
    if ext_systemsettings_selection >= ext_systemsettings_scroll + 12: ext_systemsettings_scroll = ext_systemsettings_selection - 11


def ext_systemsettings_draw_header() -> None:
    extension_draw_text_centered(1, "SYSTEM SETTINGS", 0x0E)
    if ext_systemsettings_page == 0:
        extension_draw_text(23, 3, "< HIDDEN >", 0x0B)
        extension_draw_text(46, 3, "PERMISSIONS", 0x08)
    else:
        extension_draw_text(20, 3, "HIDDEN", 0x08)
        extension_draw_text(41, 3, "< PERMISSIONS >", 0x0B)
    extension_draw_text(3, 23, "ARROWS SELECT   ENTER APPLY   ESC BACK", 0x07)


def ext_systemsettings_draw_hidden() -> None:
    configured: i32 = extension_admin_autostart_get()
    extension_draw_text(8, 5, "BOOT EXTENSION", 0x0F)
    row: i32 = 0
    count: i32 = extension_count() + 1
    while row < 12 and ext_systemsettings_scroll + row < count:
        item: i32 = ext_systemsettings_scroll + row
        identifier: i32 = item - 1
        colour: i32 = 0x1F if item == ext_systemsettings_selection else 0x07
        ui_put_cell(8, 7 + row, 16 if item == ext_systemsettings_selection else 32, colour)
        if identifier < 0: extension_draw_text(11, 7 + row, "DISABLED", colour)
        else: ext_systemsettings_draw_name(identifier, 11, 7 + row, colour)
        if identifier == configured: extension_draw_text(48, 7 + row, "ACTIVE", 0x0A)
        elif identifier >= 0 and extension_background_capable(identifier) == 0: extension_draw_text(48, 7 + row, "NO BG", 0x08)
        row = row + 1
    if ext_systemsettings_status == 1: extension_draw_text(56, 21, "SAVED", 0x0A)
    elif ext_systemsettings_status < 0: extension_draw_text(55, 21, "DENIED", 0x0C)


def ext_systemsettings_draw_permissions() -> None:
    count: i32 = extension_count()
    if count <= 0: return
    identifier: i32 = ext_systemsettings_selection
    if identifier >= count: identifier = count - 1
    extension_draw_text(7, 5, "EXTENSION", 0x07)
    ext_systemsettings_draw_name(identifier, 25, 5, 0x0F)
    mask: i32 = extension_admin_permission_get(identifier)
    ext_systemsettings_draw_toggle(8, "SETTINGS READ", mask & 1)
    ext_systemsettings_draw_toggle(9, "SETTINGS WRITE", mask & 2)
    ext_systemsettings_draw_toggle(10, "SETTINGS SAVE", mask & 4)
    ext_systemsettings_draw_toggle(11, "AUTOSTART SELF", mask & 8)
    ext_systemsettings_draw_toggle(12, "BACKGROUND", mask & 16)
    ext_systemsettings_draw_toggle(13, "EVENTS", mask & 32)
    ext_systemsettings_draw_toggle(14, "NOTIFICATIONS", mask & 64)
    ext_systemsettings_draw_toggle(15, "MESSAGES", mask & 128)
    ext_systemsettings_draw_toggle(16, "STORAGE READ", mask & 256)
    ext_systemsettings_draw_toggle(17, "STORAGE WRITE", mask & 512)
    ext_systemsettings_draw_toggle(18, "NATIVE VIDEO", mask & 1024)
    ext_systemsettings_draw_toggle(19, "SYSTEM ADMIN", mask & 2048)
    extension_draw_text_centered(21, "DECLARED AT BUILD - READ ONLY", 0x08)


def ext_systemsettings_draw() -> None:
    clear_screen(0x10)
    ui_fill_rect(20, 8, 280, 176, 1)
    ui_fill_rect(20, 8, 280, 2, 14); ui_fill_rect(20, 182, 280, 2, 14)
    ui_fill_rect(20, 8, 2, 176, 14); ui_fill_rect(298, 8, 2, 176, 14)
    ext_systemsettings_draw_header()
    if ext_systemsettings_page == 0: ext_systemsettings_draw_hidden()
    else: ext_systemsettings_draw_permissions()


def ext_systemsettings_key(key: i32) -> i32:
    global ext_systemsettings_page, ext_systemsettings_selection, ext_systemsettings_scroll, ext_systemsettings_status
    count: i32 = extension_count() + 1 if ext_systemsettings_page == 0 else extension_count()
    if key == 0x01: return 1
    if key == 0x4B or key == 0x4D:
        ext_systemsettings_page = 1 - ext_systemsettings_page
        ext_systemsettings_selection = 0
        ext_systemsettings_scroll = 0
        ext_systemsettings_status = 0
    elif key == 0x48 and count > 0:
        ext_systemsettings_selection = (ext_systemsettings_selection + count - 1) % count
        ext_systemsettings_status = 0
    elif key == 0x50 and count > 0:
        ext_systemsettings_selection = (ext_systemsettings_selection + 1) % count
        ext_systemsettings_status = 0
    elif key == 0x1C and ext_systemsettings_page == 0:
        result: i32 = extension_admin_set_autostart(ext_systemsettings_selection - 1)
        ext_systemsettings_status = 1 if result == 0 else result
    ext_systemsettings_update_scroll()
    extension_request_redraw()
    return 0
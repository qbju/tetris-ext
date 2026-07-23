# permissions: storage.read storage.write
# Explorer-like TinyFS browser.
ext_fileexplorer_cwd: i32 = 0
ext_fileexplorer_selection: i32 = 0
ext_fileexplorer_scroll: i32 = 0
ext_fileexplorer_modal: i32 = 0  # 0 none, 1 info, 2 delete confirmation
ext_fileexplorer_picked_kind: i32 = -1
ext_fileexplorer_picked_index: i32 = -1
ext_fileexplorer_picked_lba: i32 = -1


def ext_fileexplorer_pick(ordinal: i32) -> i32:
    global ext_fileexplorer_picked_kind, ext_fileexplorer_picked_index, ext_fileexplorer_picked_lba
    ext_fileexplorer_picked_kind = -1; ext_fileexplorer_picked_index = -1; ext_fileexplorer_picked_lba = -1
    if ata_read_sector(18):
        count: i32 = fs_get_u32(4)
        if count > 12: count = 12
        entry: i32 = 0
        visible: i32 = 0
        while entry < count:
            offset: i32 = 8 + entry * 32
            kind_value: i32 = fs_buffer_get(offset + 24)
            if kind_value != 2 and fs_buffer_get(offset + 25) == ext_fileexplorer_cwd:
                if visible == ordinal:
                    ext_fileexplorer_picked_kind = kind_value
                    ext_fileexplorer_picked_index = entry
                    ext_fileexplorer_picked_lba = 18
                    return 1
                visible = visible + 1
            entry = entry + 1
    if ata_read_sector(16):
        elf_count: i32 = fs_get_u32(4)
        if elf_count > 30: elf_count = 30
        elf_entry: i32 = 0
        while elf_entry < elf_count:
            page: i32 = elf_entry // 15
            if elf_entry % 15 == 0 and not ata_read_sector(16 + page): return 0
            elf_offset: i32 = 8 + (elf_entry % 15) * 32
            if fs_buffer_get(elf_offset + 24) == 0xF0 and fs_buffer_get(elf_offset + 25) == ext_fileexplorer_cwd:
                if visible == ordinal:
                    ext_fileexplorer_picked_kind = 0xF0
                    ext_fileexplorer_picked_index = elf_entry % 15
                    ext_fileexplorer_picked_lba = 16 + page
                    return 1
                visible = visible + 1
            elf_entry = elf_entry + 1
    return 0


def ext_fileexplorer_count() -> i32:
    ordinal: i32 = 0
    while ordinal < 42 and ext_fileexplorer_pick(ordinal) == 1: ordinal = ordinal + 1
    return ordinal


def ext_fileexplorer_name_char(position: i32) -> i32:
    if ext_fileexplorer_picked_lba < 0 or not ata_read_sector(ext_fileexplorer_picked_lba): return 0
    offset: i32 = 8 + ext_fileexplorer_picked_index * 32
    if position < 0 or position >= 16: return 0
    return fs_buffer_get(offset + position)


def ext_fileexplorer_draw_name(x: i32, y: i32, ordinal: i32, selected: i32) -> None:
    if ext_fileexplorer_pick(ordinal) == 0: return
    colour: i32 = 0x1F if selected == 1 else 0x17
    label0: i32 = 68 if ext_fileexplorer_picked_kind == 1 else (69 if ext_fileexplorer_picked_kind == 0xF0 else 84)
    ui_put_cell(x, y, 91, colour); ui_put_cell(x + 1, y, label0, colour)
    ui_put_cell(x + 2, y, 73 if ext_fileexplorer_picked_kind == 1 else (76 if ext_fileexplorer_picked_kind == 0xF0 else 88), colour)
    ui_put_cell(x + 3, y, 82 if ext_fileexplorer_picked_kind == 1 else (70 if ext_fileexplorer_picked_kind == 0xF0 else 84), colour)
    ui_put_cell(x + 4, y, 93, colour)
    position: i32 = 0
    while position < 16:
        character: i32 = ext_fileexplorer_name_char(position)
        if character != 0: ui_put_cell(x + 6 + position, y, character, colour)
        position = position + 1


def ext_fileexplorer_draw() -> None:
    clear_screen(0x10)
    row: i32 = 1
    while row < 24:
        column: i32 = 1
        while column < 79:
            ui_put_cell(column, row, 32, 0x17)
            column = column + 1
        row = row + 1
    extension_draw_text(3, 2, "TETRIS OS EXPLORER", 0x1F)
    extension_draw_text(3, 4, "QUICK ACCESS", 0x1E)
    extension_draw_text(3, 6, "> C:/", 0x1F)
    extension_draw_text(3, 8, "TINYFS", 0x1B)
    extension_draw_text(3, 10, "ELF PROGRAMS", 0x1B)
    row = 1
    while row < 24:
        ui_put_cell(22, row, 179, 0x18)
        row = row + 1
    extension_draw_text(25, 2, "C:/", 0x1E)
    total: i32 = ext_fileexplorer_count()
    if ext_fileexplorer_selection >= total and total > 0: ext_fileexplorer_selection = total - 1
    shown: i32 = 0
    while shown < 15 and ext_fileexplorer_scroll + shown < total:
        ordinal: i32 = ext_fileexplorer_scroll + shown
        ext_fileexplorer_draw_name(25, 5 + shown, ordinal, 1 if ordinal == ext_fileexplorer_selection else 0)
        shown = shown + 1
    if total == 0: extension_draw_text(25, 7, "THIS FOLDER IS EMPTY", 0x18)
    extension_draw_text(25, 22, "ENTER OPEN  BACKSPACE UP  DEL DELETE  ESC BACK", 0x18)
    if ext_fileexplorer_modal != 0:
        y: i32 = 7
        while y < 17:
            x: i32 = 29
            while x < 69:
                ui_put_cell(x, y, 32, 0x70)
                x = x + 1
            y = y + 1
        extension_draw_text(32, 9, "FILE PROPERTIES" if ext_fileexplorer_modal == 1 else "DELETE ITEM?", 0x70)
        if ext_fileexplorer_pick(ext_fileexplorer_selection) == 1:
            extension_draw_text(32, 11, "TYPE: DIRECTORY" if ext_fileexplorer_picked_kind == 1 else ("TYPE: ELF PROGRAM" if ext_fileexplorer_picked_kind == 0xF0 else "TYPE: FILE"), 0x70)
        extension_draw_text(32, 14, "ENTER CONFIRM   ESC CANCEL", 0x70)


def ext_fileexplorer_enter() -> None:
    global ext_fileexplorer_selection, ext_fileexplorer_scroll, ext_fileexplorer_modal
    ext_fileexplorer_selection = 0; ext_fileexplorer_scroll = 0; ext_fileexplorer_modal = 0


def ext_fileexplorer_update() -> None:
    return


def ext_fileexplorer_delete_selected() -> i32:
    if ext_fileexplorer_pick(ext_fileexplorer_selection) == 0: return -1
    if ext_fileexplorer_picked_kind == 1:
        child: i32 = 0
        while child < 42:
            if ext_fileexplorer_pick(child) == 1 and ext_fileexplorer_picked_kind >= 0: child = child + 1
            else: child = 42
        # Directory removal is kept conservative; only ordinary files/ELFs are deleted in v1.
        return -2
    if not ata_read_sector(ext_fileexplorer_picked_lba): return -1
    offset: i32 = 8 + ext_fileexplorer_picked_index * 32
    fs_buffer_set(offset + 24, 2)
    if ata_write_sector(ext_fileexplorer_picked_lba): return 0
    return -1


def ext_fileexplorer_key(key: i32) -> i32:
    global ext_fileexplorer_selection, ext_fileexplorer_scroll, ext_fileexplorer_modal, ext_fileexplorer_cwd
    if ext_fileexplorer_modal != 0:
        if key == 0x01: ext_fileexplorer_modal = 0; return 3
        if key == 0x1C:
            if ext_fileexplorer_modal == 2: ext_fileexplorer_delete_selected()
            ext_fileexplorer_modal = 0; return 3
        return 0
    total: i32 = ext_fileexplorer_count()
    if key == 0x48 and ext_fileexplorer_selection > 0: ext_fileexplorer_selection = ext_fileexplorer_selection - 1
    elif key == 0x50 and ext_fileexplorer_selection + 1 < total: ext_fileexplorer_selection = ext_fileexplorer_selection + 1
    elif key == 0x0E:
        if ext_fileexplorer_cwd != 0 and ata_read_sector(18):
            ext_fileexplorer_cwd = fs_buffer_get(8 + (ext_fileexplorer_cwd - 1) * 32 + 25)
            ext_fileexplorer_selection = 0; ext_fileexplorer_scroll = 0
    elif key == 0x1C and ext_fileexplorer_pick(ext_fileexplorer_selection) == 1:
        if ext_fileexplorer_picked_kind == 1:
            ext_fileexplorer_cwd = ext_fileexplorer_picked_index + 1
            ext_fileexplorer_selection = 0; ext_fileexplorer_scroll = 0
        else: ext_fileexplorer_modal = 1
    elif key == 0x53 and ext_fileexplorer_pick(ext_fileexplorer_selection) == 1: ext_fileexplorer_modal = 2
    elif key == 0x01: return 0
    if ext_fileexplorer_selection < ext_fileexplorer_scroll: ext_fileexplorer_scroll = ext_fileexplorer_selection
    if ext_fileexplorer_selection >= ext_fileexplorer_scroll + 15: ext_fileexplorer_scroll = ext_fileexplorer_selection - 14
    return 3


def ext_fileexplorer_exit() -> None:
    return
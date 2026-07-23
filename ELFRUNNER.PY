# LPython ELF32 loader extension. CPython+llvmlite only exposes raw boundaries.
ext_elfrunner_status: i32 = 0
ext_elfrunner_entry: i32 = 0
ext_elfrunner_input_length: i32 = 0
ext_elfrunner_cursor: i32 = 0
ext_elfrunner_source_mode: i32 = 0
ext_elfrunner_file_lba: i32 = 0
ext_elfrunner_file_size: i32 = 0
ext_elfrunner_cache_lba: i32 = -1
ext_elfrunner_last_error: i32 = 0
ext_elfrunner_event_sequence: i32 = 0
ext_elfrunner_stdin_length: i32 = 0
ext_elfrunner_text_length: i32 = 0
ext_elfrunner_text_cursor: i32 = 0
ext_elfrunner_text_lba: i32 = 0
ext_elfrunner_text_entry: i32 = -1
ext_elfrunner_text_name_length: i32 = 0
ext_elfrunner_waiting_editor: i32 = 0
ext_elfrunner_argument_start: i32 = 0
ext_elfrunner_argument_length: i32 = 0
ext_elfrunner_cwd: i32 = 0


def ext_elfrunner_source_size() -> i32:
    if ext_elfrunner_source_mode == 0: return elf_image_size()
    return ext_elfrunner_file_size


def ext_elfrunner_source_get(offset: i32) -> i32:
    global ext_elfrunner_cache_lba
    if ext_elfrunner_source_mode == 0: return elf_image_get(offset)
    wanted_lba: i32 = ext_elfrunner_file_lba + offset // 512
    if wanted_lba != ext_elfrunner_cache_lba:
        if not ata_read_sector(wanted_lba): return 0
        ext_elfrunner_cache_lba = wanted_lba
    return fs_buffer_get(offset % 512)


def ext_elfrunner_find_file() -> bool:
    global ext_elfrunner_source_mode, ext_elfrunner_file_lba, ext_elfrunner_file_size, ext_elfrunner_cache_lba, ext_elfrunner_argument_start, ext_elfrunner_argument_length
    if not ata_read_sector(16): return False
    if fs_buffer_get(0) != 69 or fs_buffer_get(1) != 76 or fs_buffer_get(2) != 70 or fs_buffer_get(3) != 68: return False
    command_name_length: i32 = 0
    while command_name_length < ext_elfrunner_input_length and extension_memory_get(700 + command_name_length) != 32:
        command_name_length = command_name_length + 1
    ext_elfrunner_argument_start = command_name_length + 1
    ext_elfrunner_argument_length = ext_elfrunner_input_length - ext_elfrunner_argument_start
    if ext_elfrunner_argument_length < 0: ext_elfrunner_argument_length = 0
    file_count: i32 = fs_get_u32(4)
    if file_count > 30: file_count = 30
    file_index: i32 = 0
    while file_index < file_count:
        if file_index % 15 == 0:
            if not ata_read_sector(16 + file_index // 15): return False
        entry_offset: i32 = 8 + (file_index % 15) * 32
        name_length: i32 = 0
        while name_length < 16 and fs_buffer_get(entry_offset + name_length) != 0:
            name_length = name_length + 1
        same: bool = name_length == command_name_length or name_length == command_name_length + 4
        if fs_buffer_get(entry_offset + 24) == 0xF0 and fs_buffer_get(entry_offset + 25) != ext_elfrunner_cwd: same = False
        name_index: i32 = 0
        while same and name_index < name_length:
            typed: i32 = extension_memory_get(700 + name_index)
            if typed >= 97 and typed <= 122: typed = typed - 32
            if name_index < command_name_length:
                if typed != fs_buffer_get(entry_offset + name_index): same = False
            else:
                suffix_position: i32 = name_index - command_name_length
                suffix_value: i32 = 46 if suffix_position == 0 else (69 if suffix_position == 1 else (76 if suffix_position == 2 else 70))
                if fs_buffer_get(entry_offset + name_index) != suffix_value: same = False
            name_index = name_index + 1
        if same:
            ext_elfrunner_file_lba = fs_get_u32(entry_offset + 16)
            ext_elfrunner_file_size = fs_get_u32(entry_offset + 20)
            ext_elfrunner_source_mode = 1
            ext_elfrunner_cache_lba = -1
            return ext_elfrunner_file_lba >= 32 and ext_elfrunner_file_size >= 52
        file_index = file_index + 1
    return False

def ext_elfrunner_u16(offset: i32) -> i32:
    return ext_elfrunner_source_get(offset) | (ext_elfrunner_source_get(offset + 1) << 8)


def ext_elfrunner_u32(offset: i32) -> i32:
    return ext_elfrunner_source_get(offset) | (ext_elfrunner_source_get(offset + 1) << 8) | (ext_elfrunner_source_get(offset + 2) << 16) | (ext_elfrunner_source_get(offset + 3) << 24)


def ext_elfrunner_prepare_stdin() -> None:
    physical_write8(0x00500100, ext_elfrunner_input_length)
    physical_write8(0x00500101, 0)
    index: i32 = 0
    while index < ext_elfrunner_input_length:
        physical_write8(0x00500102 + index, extension_memory_get(700 + index))
        index = index + 1

def ext_elfrunner_load() -> i32:
    global ext_elfrunner_entry, ext_elfrunner_stdin_length
    if ext_elfrunner_source_size() < 52: return -1
    if ext_elfrunner_source_get(0) != 0x7F or ext_elfrunner_source_get(1) != 69 or ext_elfrunner_source_get(2) != 76 or ext_elfrunner_source_get(3) != 70: return -2
    if ext_elfrunner_source_get(4) != 1 or ext_elfrunner_source_get(5) != 1: return -3
    if ext_elfrunner_u16(18) != 3: return -4
    ext_elfrunner_entry = ext_elfrunner_u32(24)
    program_offset: i32 = ext_elfrunner_u32(28)
    program_size: i32 = ext_elfrunner_u16(42)
    program_count: i32 = ext_elfrunner_u16(44)
    if program_size < 32 or program_count <= 0: return -5
    index: i32 = 0
    loaded: i32 = 0
    while index < program_count:
        header: i32 = program_offset + index * program_size
        if header < 0 or header + 32 > ext_elfrunner_source_size(): return -6
        if ext_elfrunner_u32(header) == 1:
            file_offset: i32 = ext_elfrunner_u32(header + 4)
            address: i32 = ext_elfrunner_u32(header + 8)
            file_size: i32 = ext_elfrunner_u32(header + 16)
            memory_size: i32 = ext_elfrunner_u32(header + 20)
            if address < 0x00300000 or address + memory_size >= 0x00500000: return -7
            if file_offset < 0 or file_offset + file_size > ext_elfrunner_source_size() or file_size > memory_size: return -8
            byte_index: i32 = 0
            while byte_index < file_size:
                physical_write8(address + byte_index, ext_elfrunner_source_get(file_offset + byte_index))
                byte_index = byte_index + 1
            while byte_index < memory_size:
                physical_write8(address + byte_index, 0)
                byte_index = byte_index + 1
            loaded = loaded + 1
        index = index + 1
    if loaded == 0 or ext_elfrunner_entry < 0x00300000 or ext_elfrunner_entry >= 0x00500000: return -9
    physical_write8(0x00500000, 0)
    ext_elfrunner_stdin_length = 0
    argument_index: i32 = 0
    while argument_index < ext_elfrunner_argument_length and argument_index < 249:
        physical_write8(0x00500102 + argument_index, extension_memory_get(700 + ext_elfrunner_argument_start + argument_index))
        argument_index = argument_index + 1
    if ext_elfrunner_argument_length > 0 and argument_index < 250:
        physical_write8(0x00500102 + argument_index, 10)
        argument_index = argument_index + 1
    ext_elfrunner_stdin_length = argument_index
    physical_write8(0x00500100, argument_index)
    physical_write8(0x00500101, 0)
    return elf_call_entry(ext_elfrunner_entry)


def ext_elfrunner_enter() -> None:
    global ext_elfrunner_status, ext_elfrunner_input_length, ext_elfrunner_cursor, ext_elfrunner_last_error
    ext_elfrunner_input_length = 0
    ext_elfrunner_cursor = 0
    ext_elfrunner_last_error = 0
    physical_write8(0x00500000, 0)
    ext_elfrunner_status = 2

def ext_elfrunner_update() -> None:
    return


def ext_elfrunner_exit() -> None:
    global ext_elfrunner_status
    ext_elfrunner_status = 0


def ext_elfrunner_command_prefix(a: i32, b: i32, c: i32, d: i32) -> bool:
    if ext_elfrunner_input_length < 5: return False
    p0: i32 = extension_memory_get(700); p1: i32 = extension_memory_get(701)
    p2: i32 = extension_memory_get(702); p3: i32 = extension_memory_get(703)
    if p0 >= 97 and p0 <= 122: p0 = p0 - 32
    if p1 >= 97 and p1 <= 122: p1 = p1 - 32
    if p2 >= 97 and p2 <= 122: p2 = p2 - 32
    if p3 >= 97 and p3 <= 122: p3 = p3 - 32
    return p0 == a and p1 == b and p2 == c and p3 == d and extension_memory_get(704) == 32


def ext_elfrunner_is_cat_command() -> bool:
    if ext_elfrunner_input_length < 5 or extension_memory_get(703) != 32: return False
    a: i32 = extension_memory_get(700); b: i32 = extension_memory_get(701); c: i32 = extension_memory_get(702)
    if a >= 97 and a <= 122: a = a - 32
    if b >= 97 and b <= 122: b = b - 32
    if c >= 97 and c <= 122: c = c - 32
    return a == 67 and b == 65 and c == 84


def ext_elfrunner_is_edit_command() -> bool:
    return ext_elfrunner_command_prefix(69, 68, 73, 84)

def ext_elfrunner_text_directory() -> bool:
    if not ata_read_sector(18): return False
    if fs_buffer_get(0) == 84 and fs_buffer_get(1) == 88 and fs_buffer_get(2) == 84 and fs_buffer_get(3) == 68: return True
    fs_buffer_clear()
    fs_buffer_set(0, 84); fs_buffer_set(1, 88); fs_buffer_set(2, 84); fs_buffer_set(3, 68)
    fs_put_u32(4, 0)
    return ata_write_sector(18)


def ext_elfrunner_text_find(command_start: i32) -> bool:
    global ext_elfrunner_text_lba, ext_elfrunner_text_entry, ext_elfrunner_text_name_length, ext_elfrunner_text_length
    if not ext_elfrunner_text_directory(): return False
    wanted_length: i32 = ext_elfrunner_input_length - command_start
    if wanted_length <= 0 or wanted_length > 15: return False
    count: i32 = fs_get_u32(4)
    if count > 12: count = 12
    entry: i32 = 0
    while entry < count:
        offset: i32 = 8 + entry * 32
        stored_length: i32 = 0
        while stored_length < 16 and fs_buffer_get(offset + stored_length) != 0:
            stored_length = stored_length + 1
        same: bool = stored_length == wanted_length
        if fs_buffer_get(offset + 24) != 0 or fs_buffer_get(offset + 25) != ext_elfrunner_cwd: same = False
        index: i32 = 0
        while same and index < wanted_length:
            typed: i32 = extension_memory_get(700 + command_start + index)
            if typed >= 97 and typed <= 122: typed = typed - 32
            if typed != fs_buffer_get(offset + index): same = False
            index = index + 1
        if same:
            ext_elfrunner_text_lba = fs_get_u32(offset + 16)
            ext_elfrunner_text_length = fs_get_u32(offset + 20)
            ext_elfrunner_text_entry = entry
            ext_elfrunner_text_name_length = wanted_length
            index = 0
            while index < wanted_length:
                extension_memory_set(600 + index, fs_buffer_get(offset + index))
                index = index + 1
            return True
        entry = entry + 1
    return False


def ext_elfrunner_text_prepare_new(command_start: i32) -> bool:
    global ext_elfrunner_text_lba, ext_elfrunner_text_entry, ext_elfrunner_text_name_length, ext_elfrunner_text_length
    if not ext_elfrunner_text_directory(): return False
    wanted_length: i32 = ext_elfrunner_input_length - command_start
    count: i32 = fs_get_u32(4)
    if wanted_length <= 0 or wanted_length > 15: return False
    reusable: i32 = -1
    scan: i32 = 0
    while scan < count and reusable < 0:
        if fs_buffer_get(8 + scan * 32 + 24) == 2: reusable = scan
        scan = scan + 1
    if reusable < 0 and count >= 12: return False
    ext_elfrunner_text_entry = reusable if reusable >= 0 else count
    ext_elfrunner_text_lba = 20 + ext_elfrunner_text_entry
    ext_elfrunner_text_name_length = wanted_length
    ext_elfrunner_text_length = 0
    offset: i32 = 8 + ext_elfrunner_text_entry * 32
    index: i32 = 0
    while index < 32:
        fs_buffer_set(offset + index, 0)
        index = index + 1
    index = 0
    while index < wanted_length:
        value: i32 = extension_memory_get(700 + command_start + index)
        if value >= 97 and value <= 122: value = value - 32
        fs_buffer_set(offset + index, value)
        extension_memory_set(600 + index, value)
        index = index + 1
    fs_put_u32(offset + 16, ext_elfrunner_text_lba)
    fs_put_u32(offset + 20, 0)
    fs_buffer_set(offset + 24, 0)
    fs_buffer_set(offset + 25, ext_elfrunner_cwd)
    if reusable < 0: fs_put_u32(4, count + 1)
    return ata_write_sector(18)

def ext_elfrunner_text_open() -> bool:
    global ext_elfrunner_text_length, ext_elfrunner_text_cursor, ext_elfrunner_status
    found: bool = ext_elfrunner_text_find(5)
    if not found:
        if not ext_elfrunner_text_prepare_new(5): return False
    elif not ata_read_sector(ext_elfrunner_text_lba): return False
    if found:
        if ext_elfrunner_text_length > 480: ext_elfrunner_text_length = 480
        index: i32 = 0
        while index < ext_elfrunner_text_length:
            extension_memory_set(index, fs_buffer_get(index))
            index = index + 1
    ext_elfrunner_text_cursor = ext_elfrunner_text_length
    ext_elfrunner_status = 3
    return True


def ext_elfrunner_text_save() -> bool:
    fs_buffer_clear()
    index: i32 = 0
    while index < ext_elfrunner_text_length:
        fs_buffer_set(index, extension_memory_get(index))
        index = index + 1
    if not ata_write_sector(ext_elfrunner_text_lba): return False
    if not ata_read_sector(18): return False
    fs_put_u32(8 + ext_elfrunner_text_entry * 32 + 20, ext_elfrunner_text_length)
    return ata_write_sector(18)


def ext_elfrunner_text_cat() -> bool:
    if not ext_elfrunner_text_find(4): return False
    if not ata_read_sector(ext_elfrunner_text_lba): return False
    output_length: i32 = ext_elfrunner_text_length
    if output_length > 250: output_length = 250
    physical_write8(0x00500000, output_length)
    index: i32 = 0
    while index < output_length:
        physical_write8(0x00500001 + index, fs_buffer_get(index))
        index = index + 1
    return True


def ext_elfrunner_text_move_vertical(direction: i32) -> None:
    global ext_elfrunner_text_cursor
    line_start: i32 = ext_elfrunner_text_cursor
    while line_start > 0 and extension_memory_get(line_start - 1) != 10:
        line_start = line_start - 1
    column: i32 = ext_elfrunner_text_cursor - line_start
    if direction < 0:
        if line_start == 0: return
        previous_end: i32 = line_start - 1
        previous_start: i32 = previous_end
        while previous_start > 0 and extension_memory_get(previous_start - 1) != 10:
            previous_start = previous_start - 1
        ext_elfrunner_text_cursor = previous_start + column
        if ext_elfrunner_text_cursor > previous_end: ext_elfrunner_text_cursor = previous_end
    else:
        line_end: i32 = ext_elfrunner_text_cursor
        while line_end < ext_elfrunner_text_length and extension_memory_get(line_end) != 10:
            line_end = line_end + 1
        if line_end >= ext_elfrunner_text_length: return
        next_start: i32 = line_end + 1
        next_end: i32 = next_start
        while next_end < ext_elfrunner_text_length and extension_memory_get(next_end) != 10:
            next_end = next_end + 1
        ext_elfrunner_text_cursor = next_start + column
        if ext_elfrunner_text_cursor > next_end: ext_elfrunner_text_cursor = next_end

def ext_elfrunner_draw_editor() -> None:
    clear_screen(0x00)
    ui_put_cell(2, 1, 69, 0x0A); ui_put_cell(3, 1, 68, 0x0A); ui_put_cell(4, 1, 73, 0x0A); ui_put_cell(5, 1, 84, 0x0A)
    name_index: i32 = 0
    while name_index < ext_elfrunner_text_name_length:
        ui_put_cell(8 + name_index, 1, extension_memory_get(600 + name_index), 0x0F)
        name_index = name_index + 1
    position: i32 = 0
    draw_x: i32 = 3
    draw_y: i32 = 4
    cursor_x: i32 = 3
    cursor_y: i32 = 4
    while position <= ext_elfrunner_text_length and draw_y < 21:
        if position == ext_elfrunner_text_cursor:
            cursor_x = draw_x; cursor_y = draw_y
        if position < ext_elfrunner_text_length:
            value: i32 = extension_memory_get(position)
            if value == 10:
                draw_x = 3; draw_y = draw_y + 1
            else:
                ui_put_cell(draw_x, draw_y, value, 0x0F)
                draw_x = draw_x + 1
                if draw_x >= 77:
                    draw_x = 3; draw_y = draw_y + 1
        position = position + 1
    ui_put_cell(cursor_x, cursor_y + 1, 94, 0x0E)
    ui_put_cell(3, 23, 83, 0x0A); ui_put_cell(4, 23, 72, 0x0A); ui_put_cell(5, 23, 73, 0x0A); ui_put_cell(6, 23, 70, 0x0A); ui_put_cell(7, 23, 84, 0x0A)
    ui_put_cell(9, 23, 69, 0x0A); ui_put_cell(10, 23, 78, 0x0A); ui_put_cell(11, 23, 84, 0x0A); ui_put_cell(12, 23, 69, 0x0A); ui_put_cell(13, 23, 82, 0x0A)
    ui_put_cell(15, 23, 83, 0x07); ui_put_cell(16, 23, 65, 0x07); ui_put_cell(17, 23, 86, 0x07); ui_put_cell(18, 23, 69, 0x07)
    ui_put_cell(22, 23, 69, 0x0C); ui_put_cell(23, 23, 83, 0x0C); ui_put_cell(24, 23, 67, 0x0C)
    ui_put_cell(26, 23, 66, 0x07); ui_put_cell(27, 23, 65, 0x07); ui_put_cell(28, 23, 67, 0x07); ui_put_cell(29, 23, 75, 0x07)

def ext_elfrunner_syscall_result_byte(index: i32, value: i32) -> None:
    physical_write8(0x00500420 + index, value)


def ext_elfrunner_fs_list() -> i32:
    if not ext_elfrunner_text_directory(): return -1
    count: i32 = fs_get_u32(4)
    if count > 12: count = 12
    output: i32 = 0
    entry: i32 = 0
    while entry < count and output < 470:
        offset: i32 = 8 + entry * 32
        if fs_buffer_get(offset + 25) == ext_elfrunner_cwd:
            name_index: i32 = 0
            while name_index < 16 and fs_buffer_get(offset + name_index) != 0 and output < 470:
                ext_elfrunner_syscall_result_byte(output, fs_buffer_get(offset + name_index))
                output = output + 1
                name_index = name_index + 1
            if fs_buffer_get(offset + 24) == 1 and output < 470:
                ext_elfrunner_syscall_result_byte(output, 47); output = output + 1
            ext_elfrunner_syscall_result_byte(output, 10); output = output + 1
        entry = entry + 1
    if ata_read_sector(16):
        elf_count: i32 = fs_get_u32(4)
        if elf_count > 30: elf_count = 30
        entry = 0
        while entry < elf_count and output < 470:
            if entry % 15 == 0 and not ata_read_sector(16 + entry // 15): return -1
            offset = 8 + (entry % 15) * 32
            if fs_buffer_get(offset + 24) == 0xF0 and fs_buffer_get(offset + 25) == ext_elfrunner_cwd:
                name_index = 0
                while name_index < 16 and fs_buffer_get(offset + name_index) != 0 and output < 470:
                    ext_elfrunner_syscall_result_byte(output, fs_buffer_get(offset + name_index))
                    output = output + 1; name_index = name_index + 1
                ext_elfrunner_syscall_result_byte(output, 10); output = output + 1
            entry = entry + 1
    physical_write8(0x00500404, output & 255); physical_write8(0x00500405, (output >> 8) & 255)
    return 0


def ext_elfrunner_fs_mkdir() -> i32:
    if not ext_elfrunner_text_directory(): return -1
    count: i32 = fs_get_u32(4)
    wanted: i32 = ext_elfrunner_input_length
    if wanted <= 0 or wanted > 15: return -1
    reusable: i32 = -1
    entry: i32 = 0
    while entry < count:
        offset: i32 = 8 + entry * 32
        if fs_buffer_get(offset + 24) == 2: reusable = entry
        same: bool = fs_buffer_get(offset + 24) != 2 and fs_buffer_get(offset + 25) == ext_elfrunner_cwd
        name_index: i32 = 0
        while same and name_index < wanted:
            stored: i32 = fs_buffer_get(offset + name_index)
            typed: i32 = extension_memory_get(700 + name_index)
            if typed >= 97 and typed <= 122: typed = typed - 32
            if stored != typed: same = False
            name_index = name_index + 1
        if same and fs_buffer_get(offset + wanted) == 0: return -2
        entry = entry + 1
    if reusable < 0 and count >= 12: return -1
    entry = reusable if reusable >= 0 else count
    offset = 8 + entry * 32
    name_index = 0
    while name_index < 32:
        fs_buffer_set(offset + name_index, 0)
        name_index = name_index + 1
    name_index = 0
    while name_index < wanted:
        typed = extension_memory_get(700 + name_index)
        if typed >= 97 and typed <= 122: typed = typed - 32
        fs_buffer_set(offset + name_index, typed)
        name_index = name_index + 1
    fs_buffer_set(offset + 24, 1); fs_buffer_set(offset + 25, ext_elfrunner_cwd)
    if reusable < 0: fs_put_u32(4, count + 1)
    if ata_write_sector(18): return 0
    return -1

def ext_elfrunner_fs_cd() -> i32:
    global ext_elfrunner_cwd
    if not ext_elfrunner_text_directory(): return -1
    if ext_elfrunner_input_length == 2 and extension_memory_get(700) == 46 and extension_memory_get(701) == 46:
        if ext_elfrunner_cwd == 0: return 0
        target_entry: i32 = ext_elfrunner_cwd - 1
        ext_elfrunner_cwd = fs_buffer_get(8 + target_entry * 32 + 25)
        return 0
    count: i32 = fs_get_u32(4)
    entry: i32 = 0
    while entry < count:
        offset: i32 = 8 + entry * 32
        same: bool = fs_buffer_get(offset + 24) == 1 and fs_buffer_get(offset + 25) == ext_elfrunner_cwd
        name_index: i32 = 0
        while same and name_index < ext_elfrunner_input_length:
            typed: i32 = extension_memory_get(700 + name_index)
            if typed >= 97 and typed <= 122: typed = typed - 32
            if typed != fs_buffer_get(offset + name_index): same = False
            name_index = name_index + 1
        if same and fs_buffer_get(offset + ext_elfrunner_input_length) == 0:
            ext_elfrunner_cwd = entry + 1
            return 0
        entry = entry + 1
    return -1


def ext_elfrunner_fs_pwd() -> i32:
    output: i32 = 0
    ext_elfrunner_syscall_result_byte(output, 47); output = output + 1
    if ext_elfrunner_cwd != 0 and ext_elfrunner_text_directory():
        offset: i32 = 8 + (ext_elfrunner_cwd - 1) * 32
        name_index: i32 = 0
        while name_index < 16 and fs_buffer_get(offset + name_index) != 0:
            ext_elfrunner_syscall_result_byte(output, fs_buffer_get(offset + name_index))
            output = output + 1; name_index = name_index + 1
    ext_elfrunner_syscall_result_byte(output, 10); output = output + 1
    physical_write8(0x00500404, output); physical_write8(0x00500405, 0)
    return 0

def ext_elfrunner_result_char(position: i32, value: i32) -> None:
    physical_write8(0x00500420 + position, value)


def ext_elfrunner_result_text(message: str) -> None:
    length: i32 = len(message)
    if length > 470: length = 470
    index: i32 = 0
    while index < length:
        ext_elfrunner_result_char(index, ord(message[index]))
        index = index + 1
    physical_write8(0x00500404, length & 255); physical_write8(0x00500405, (length >> 8) & 255)


def ext_elfrunner_split_names() -> i32:
    split: i32 = 0
    while split < ext_elfrunner_input_length and extension_memory_get(700 + split) != 32:
        split = split + 1
    if split <= 0 or split >= ext_elfrunner_input_length - 1 or split > 15 or ext_elfrunner_input_length - split - 1 > 15: return -1
    return split


def ext_elfrunner_shift_second_name(split: i32) -> i32:
    second_length: i32 = ext_elfrunner_input_length - split - 1
    index: i32 = 0
    while index < second_length:
        extension_memory_set(700 + index, extension_memory_get(701 + split + index))
        index = index + 1
    return second_length


def ext_elfrunner_fs_copy() -> i32:
    global ext_elfrunner_input_length, ext_elfrunner_text_length
    original_length: i32 = ext_elfrunner_input_length
    split: i32 = ext_elfrunner_split_names()
    if split < 0: return -1
    ext_elfrunner_input_length = split
    if not ext_elfrunner_text_find(0): ext_elfrunner_input_length = original_length; return -1
    if fs_buffer_get(8 + ext_elfrunner_text_entry * 32 + 24) != 0: ext_elfrunner_input_length = original_length; return -1
    source_length: i32 = ext_elfrunner_text_length
    if not ata_read_sector(ext_elfrunner_text_lba): ext_elfrunner_input_length = original_length; return -1
    index: i32 = 0
    while index < source_length:
        extension_memory_set(index, fs_buffer_get(index))
        index = index + 1
    ext_elfrunner_input_length = original_length
    second_length: i32 = ext_elfrunner_shift_second_name(split)
    ext_elfrunner_input_length = second_length
    found: bool = ext_elfrunner_text_find(0)
    if not found:
        if not ext_elfrunner_text_prepare_new(0): return -1
    elif fs_buffer_get(8 + ext_elfrunner_text_entry * 32 + 24) != 0: return -1
    fs_buffer_clear()
    index = 0
    while index < source_length:
        fs_buffer_set(index, extension_memory_get(index))
        index = index + 1
    if not ata_write_sector(ext_elfrunner_text_lba): return -1
    if not ata_read_sector(18): return -1
    fs_put_u32(8 + ext_elfrunner_text_entry * 32 + 20, source_length)
    ext_elfrunner_text_length = source_length
    return 0 if ata_write_sector(18) else -1


def ext_elfrunner_fs_move() -> i32:
    global ext_elfrunner_input_length
    original_length: i32 = ext_elfrunner_input_length
    split: i32 = ext_elfrunner_split_names()
    if split < 0: return -1
    ext_elfrunner_input_length = split
    if not ext_elfrunner_text_find(0): ext_elfrunner_input_length = original_length; return -1
    source_entry: i32 = ext_elfrunner_text_entry
    ext_elfrunner_input_length = original_length
    second_length: i32 = ext_elfrunner_shift_second_name(split)
    ext_elfrunner_input_length = second_length
    if ext_elfrunner_text_find(0): return -1
    if not ata_read_sector(18): return -1
    offset: i32 = 8 + source_entry * 32
    index: i32 = 0
    while index < 16:
        fs_buffer_set(offset + index, extension_memory_get(700 + index) if index < second_length else 0)
        index = index + 1
    return 0 if ata_write_sector(18) else -1


def ext_elfrunner_elf_remove() -> i32:
    if not ata_read_sector(16): return -1
    count: i32 = fs_get_u32(4)
    if count > 30: count = 30
    entry: i32 = 0
    while entry < count:
        if entry % 15 == 0 and not ata_read_sector(16 + entry // 15): return -1
        offset: i32 = 8 + (entry % 15) * 32
        if fs_buffer_get(offset + 24) == 0xF0 and fs_buffer_get(offset + 25) == ext_elfrunner_cwd:
            stored_length: i32 = 0
            while stored_length < 16 and fs_buffer_get(offset + stored_length) != 0: stored_length = stored_length + 1
            same: bool = stored_length == ext_elfrunner_input_length
            index: i32 = 0
            while same and index < stored_length:
                wanted: i32 = extension_memory_get(700 + index)
                if wanted >= 97 and wanted <= 122: wanted = wanted - 32
                if wanted != fs_buffer_get(offset + index): same = False
                index = index + 1
            if same:
                index = 0
                while index < 32: fs_buffer_set(offset + index, 0); index = index + 1
                return 0 if ata_write_sector(16 + entry // 15) else -1
        entry = entry + 1
    return -1

def ext_elfrunner_fs_remove() -> i32:
    if not ext_elfrunner_text_find(0): return ext_elfrunner_elf_remove()
    removed_entry: i32 = ext_elfrunner_text_entry
    if not ata_read_sector(18): return -1
    offset: i32 = 8 + removed_entry * 32
    if fs_buffer_get(offset + 24) == 1:
        count: i32 = fs_get_u32(4)
        child: i32 = 0
        while child < count:
            if fs_buffer_get(8 + child * 32 + 25) == removed_entry + 1: return -1
            child = child + 1
    index: i32 = 0
    while index < 32:
        fs_buffer_set(offset + index, 0)
        index = index + 1
    fs_buffer_set(offset + 24, 2)
    return 0 if ata_write_sector(18) else -1


def ext_elfrunner_fs_touch() -> i32:
    global ext_elfrunner_text_length
    if ext_elfrunner_text_find(0): return 0
    if not ext_elfrunner_text_prepare_new(0): return -1
    fs_buffer_clear()
    if not ata_write_sector(ext_elfrunner_text_lba): return -1
    if not ata_read_sector(18): return -1
    fs_put_u32(8 + ext_elfrunner_text_entry * 32 + 20, 0)
    ext_elfrunner_text_length = 0
    return 0 if ata_write_sector(18) else -1


def ext_elfrunner_fs_info() -> i32:
    if not ext_elfrunner_text_directory(): return -1
    count: i32 = fs_get_u32(4)
    files: i32 = 0
    directories: i32 = 0
    index: i32 = 0
    while index < count:
        kind: i32 = fs_buffer_get(8 + index * 32 + 24)
        if kind == 0: files = files + 1
        elif kind == 1: directories = directories + 1
        index = index + 1
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    ext_elfrunner_append_text("TETRIS OS\nARCH I386\nFRAMEBUFFER 640X480X32\nDISK 16 MIB\nTINYFS FILES ")
    ext_elfrunner_append_decimal(files)
    ext_elfrunner_append_text(" DIRS ")
    ext_elfrunner_append_decimal(directories)
    ext_elfrunner_append_char(10)
    return 0

def ext_elfrunner_two_digits(position: i32, value: i32) -> None:
    ext_elfrunner_result_char(position, 48 + (value // 10) % 10)
    ext_elfrunner_result_char(position + 1, 48 + value % 10)


def ext_elfrunner_uptime() -> i32:
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    ext_elfrunner_append_text("UP "); ext_elfrunner_append_decimal(system_periods // 100); ext_elfrunner_append_text("s\n")
    return 0


def ext_elfrunner_fs_date() -> i32:
    second: i32 = rtc_read(0); minute: i32 = rtc_read(2); hour: i32 = rtc_read(4)
    day: i32 = rtc_read(7); month: i32 = rtc_read(8); year: i32 = rtc_read(9)
    status_b: i32 = rtc_read(0x0B)
    if (status_b & 4) == 0:
        second = bcd_value(second); minute = bcd_value(minute); hour = bcd_value(hour & 0x7F)
        day = bcd_value(day); month = bcd_value(month); year = bcd_value(year)
    ext_elfrunner_two_digits(0, 20); ext_elfrunner_two_digits(2, year)
    ext_elfrunner_result_char(4, 45); ext_elfrunner_two_digits(5, month); ext_elfrunner_result_char(7, 45); ext_elfrunner_two_digits(8, day)
    ext_elfrunner_result_char(10, 32); ext_elfrunner_two_digits(11, hour); ext_elfrunner_result_char(13, 58); ext_elfrunner_two_digits(14, minute); ext_elfrunner_result_char(16, 58); ext_elfrunner_two_digits(17, second); ext_elfrunner_result_char(19, 10)
    physical_write8(0x00500404, 20); physical_write8(0x00500405, 0)
    return 0


def ext_elfrunner_append_char(value: i32) -> None:
    length: i32 = physical_read8(0x00500404) | (physical_read8(0x00500405) << 8)
    if length >= 470: return
    ext_elfrunner_result_char(length, value)
    length = length + 1
    physical_write8(0x00500404, length & 255); physical_write8(0x00500405, (length >> 8) & 255)


def ext_elfrunner_append_text(message: str) -> None:
    index: i32 = 0
    while index < len(message):
        ext_elfrunner_append_char(ord(message[index]))
        index = index + 1


def ext_elfrunner_append_decimal(value: i32) -> None:
    divisor: i32 = 1000000000
    started_digits: bool = False
    while divisor > 0:
        digit: i32 = (value // divisor) % 10
        if digit != 0 or started_digits or divisor == 1:
            ext_elfrunner_append_char(48 + digit)
            started_digits = True
        divisor = divisor // 10


def ext_elfrunner_append_hex(value: i32) -> None:
    high: i32 = (value >> 4) & 15
    low: i32 = value & 15
    ext_elfrunner_append_char(48 + high if high < 10 else 55 + high)
    ext_elfrunner_append_char(48 + low if low < 10 else 55 + low)


def ext_elfrunner_extension_processes() -> i32:
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    identifier: i32 = 0
    while identifier < extension_count():
        ext_elfrunner_append_char(42 if (extension_background_mask & (1 << identifier)) != 0 else 32)
        ext_elfrunner_append_char(32)
        index: i32 = 0
        while index < extension_name_length(identifier):
            ext_elfrunner_append_char(extension_name_char(identifier, index))
            index = index + 1
        ext_elfrunner_append_char(10)
        identifier = identifier + 1
    return 0


def ext_elfrunner_extension_info() -> i32:
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    if ext_elfrunner_input_length <= 0:
        ext_elfrunner_append_text("EXTENSIONS "); ext_elfrunner_append_decimal(extension_count()); ext_elfrunner_append_char(10)
        ext_elfrunner_append_text("USE EXTINFO NAME\n")
        return 0
    identifier: i32 = extension_find_memory(ext_elfrunner_input_length, 700)
    if identifier < 0: return -1
    ext_elfrunner_append_text("ID "); ext_elfrunner_append_decimal(identifier); ext_elfrunner_append_char(10)
    ext_elfrunner_append_text("NAME ")
    index: i32 = 0
    while index < extension_name_length(identifier):
        ext_elfrunner_append_char(extension_name_char(identifier, index))
        index = index + 1
    ext_elfrunner_append_char(10)
    ext_elfrunner_append_text("PERMISSIONS "); ext_elfrunner_append_decimal(extension_permission_mask(identifier)); ext_elfrunner_append_char(10)
    ext_elfrunner_append_text("BACKGROUND ")
    ext_elfrunner_append_text("RUNNING\n" if (extension_background_mask & (1 << identifier)) != 0 else "STOPPED\n")
    return 0


def ext_elfrunner_extension_run() -> i32:
    identifier: i32 = extension_find_memory(ext_elfrunner_input_length, 700)
    if identifier < 0 or extension_background_capable(identifier) == 0: return -1
    extension_enter(identifier)
    return extension_background_start(identifier)


def ext_elfrunner_extension_kill() -> i32:
    global extension_background_mask
    identifier: i32 = extension_find_memory(ext_elfrunner_input_length, 700)
    if identifier < 0 or (extension_background_mask & (1 << identifier)) == 0: return -1
    extension_background_mask = extension_background_mask & (0 - (1 << identifier) - 1)
    extension_exit(identifier)
    return 0


def ext_elfrunner_kv_list() -> i32:
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    ext_elfrunner_append_text("ELFRUNNER.KV\n")
    base_lba: i32 = extension_kvfile_prepare(0)
    if base_lba < 0: return base_lba
    if base_lba == 0: ext_elfrunner_append_text("EMPTY\n"); return 0
    total: i32 = 0
    page: i32 = 0
    while page < 7:
        if not ata_read_sector(base_lba + 1 + page): return -1
        record: i32 = 0
        while record < 16:
            offset: i32 = record * 32
            length: i32 = fs_buffer_get(offset + 23)
            if length > 0 and length <= 23:
                index: i32 = 0
                while index < length:
                    ext_elfrunner_append_char(fs_buffer_get(offset + index))
                    index = index + 1
                ext_elfrunner_append_text(" = ")
                ext_elfrunner_append_decimal(fs_get_u32(offset + 24))
                ext_elfrunner_append_char(10)
                total = total + 1
            record = record + 1
        page = page + 1
    if total == 0: ext_elfrunner_append_text("EMPTY\n")
    return 0


def ext_elfrunner_parse_decimal() -> i32:
    if ext_elfrunner_input_length <= 0: return -1
    value: i32 = 0
    index: i32 = 0
    while index < ext_elfrunner_input_length:
        character: i32 = extension_memory_get(700 + index)
        if character < 48 or character > 57: return -1
        value = value * 10 + character - 48
        index = index + 1
    return value


def ext_elfrunner_sector_view() -> i32:
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    ext_elfrunner_append_text("ELFRUNNER.KV\nFORMAT KVF1\nSECTORS 8\nCAPACITY 112 KEYS\nKEY MAX 23\n")
    base_lba: i32 = extension_kvfile_prepare(0)
    if base_lba < 0: ext_elfrunner_append_text("STATE ERROR\n"); return -1
    if base_lba == 0: ext_elfrunner_append_text("STATE NOT CREATED\n"); return 0
    ext_elfrunner_append_text("STATE READY\n")
    return 0


def ext_elfrunner_fsck() -> i32:
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    ext_elfrunner_append_text("FSCK ELFRUNNER.KV\n")
    base_lba: i32 = extension_kvfile_prepare(0)
    if base_lba < 0: ext_elfrunner_append_text("HEADER ERROR\n"); return -1
    if base_lba == 0: ext_elfrunner_append_text("NOT CREATED - OK\n"); return 0
    errors: i32 = 0
    records: i32 = 0
    page: i32 = 0
    while page < 7:
        if not ata_read_sector(base_lba + 1 + page): ext_elfrunner_append_text("READ ERROR\n"); return -1
        record: i32 = 0
        while record < 16:
            offset: i32 = record * 32
            length: i32 = fs_buffer_get(offset + 23)
            if length > 23: errors = errors + 1
            elif length > 0:
                records = records + 1
                value: i32 = fs_get_u32(offset + 24)
                if fs_get_u32(offset + 28) != (value ^ extension_storage_key(extension_current_id)): errors = errors + 1
                index: i32 = 0
                while index < length:
                    character: i32 = fs_buffer_get(offset + index)
                    if character < 32 or character > 126: errors = errors + 1
                    index = index + 1
            record = record + 1
        page = page + 1
    ext_elfrunner_append_text("RECORDS "); ext_elfrunner_append_decimal(records)
    ext_elfrunner_append_text("\nERRORS "); ext_elfrunner_append_decimal(errors); ext_elfrunner_append_char(10)
    return 0 if errors == 0 else -1

def ext_elfrunner_name_contains(entry_offset: i32) -> bool:
    if ext_elfrunner_input_length <= 0: return True
    start: i32 = 0
    while start < 16 and fs_buffer_get(entry_offset + start) != 0:
        same: bool = True
        index: i32 = 0
        while same and index < ext_elfrunner_input_length and start + index < 16:
            stored: i32 = fs_buffer_get(entry_offset + start + index)
            typed: i32 = extension_memory_get(700 + index)
            if stored >= 97 and stored <= 122: stored = stored - 32
            if typed >= 97 and typed <= 122: typed = typed - 32
            if stored != typed: same = False
            index = index + 1
        if same and index == ext_elfrunner_input_length: return True
        start = start + 1
    return False


def ext_elfrunner_fs_find() -> i32:
    if not ext_elfrunner_text_directory(): return -1
    count: i32 = fs_get_u32(4)
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    entry: i32 = 0
    while entry < count:
        offset: i32 = 8 + entry * 32
        if fs_buffer_get(offset + 24) != 2 and ext_elfrunner_name_contains(offset):
            index: i32 = 0
            while index < 16 and fs_buffer_get(offset + index) != 0:
                ext_elfrunner_append_char(fs_buffer_get(offset + index)); index = index + 1
            if fs_buffer_get(offset + 24) == 1: ext_elfrunner_append_char(47)
            ext_elfrunner_append_char(10)
        entry = entry + 1
    return 0


def ext_elfrunner_fs_wc() -> i32:
    if not ext_elfrunner_text_find(0) or not ata_read_sector(ext_elfrunner_text_lba): return -1
    lines: i32 = 0; words: i32 = 0; inside: bool = False; index: i32 = 0
    while index < ext_elfrunner_text_length:
        character: i32 = fs_buffer_get(index)
        if character == 10: lines = lines + 1
        separator: bool = character == 10 or character == 13 or character == 32 or character == 9
        if separator: inside = False
        elif not inside: words = words + 1; inside = True
        index = index + 1
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    ext_elfrunner_append_decimal(lines); ext_elfrunner_append_char(32); ext_elfrunner_append_decimal(words); ext_elfrunner_append_char(32); ext_elfrunner_append_decimal(ext_elfrunner_text_length); ext_elfrunner_append_char(10)
    return 0


def ext_elfrunner_fs_hexdump() -> i32:
    if not ext_elfrunner_text_find(0) or not ata_read_sector(ext_elfrunner_text_lba): return -1
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    limit: i32 = ext_elfrunner_text_length
    if limit > 96: limit = 96
    index: i32 = 0
    while index < limit:
        ext_elfrunner_append_hex(fs_buffer_get(index)); ext_elfrunner_append_char(32)
        if index % 16 == 15: ext_elfrunner_append_char(10)
        index = index + 1
    if index % 16 != 0: ext_elfrunner_append_char(10)
    return 0


def ext_elfrunner_forth_word(start: i32, length: i32, word: str) -> bool:
    if length != len(word): return False
    index: i32 = 0
    while index < length:
        value: i32 = extension_memory_get(start + index)
        if value >= 97 and value <= 122: value = value - 32
        if value != ord(word[index]): return False
        index = index + 1
    return True


def ext_elfrunner_forth_output_char(value: i32) -> bool:
    length: i32 = extension_memory_get(590)
    if length >= 60: return False
    extension_memory_set(600 + length, value & 255)
    extension_memory_set(590, length + 1)
    return True


def ext_elfrunner_forth_output_number(value: i32) -> bool:
    number: i32 = value
    if number == 0: return ext_elfrunner_forth_output_char(48) and ext_elfrunner_forth_output_char(32)
    if number < 0:
        if not ext_elfrunner_forth_output_char(45): return False
        number = 0 - number
    digits: i32 = 0
    while number > 0 and digits < 11:
        extension_memory_set(570 + digits, number % 10)
        number = number // 10
        digits = digits + 1
    while digits > 0:
        digits = digits - 1
        if not ext_elfrunner_forth_output_char(48 + extension_memory_get(570 + digits)): return False
    return ext_elfrunner_forth_output_char(32)


def ext_elfrunner_forth_parse(source_length: i32) -> i32:
    extension_memory_set(589, 0)
    extension_memory_set(590, 0)
    position: i32 = 0
    while position < source_length:
        while position < source_length and (extension_memory_get(position) == 32 or extension_memory_get(position) == 9 or extension_memory_get(position) == 10 or extension_memory_get(position) == 13): position = position + 1
        if position >= source_length: break
        start: i32 = position
        while position < source_length and extension_memory_get(position) != 32 and extension_memory_get(position) != 9 and extension_memory_get(position) != 10 and extension_memory_get(position) != 13: position = position + 1
        length: i32 = position - start
        negative: bool = length > 1 and extension_memory_get(start) == 45
        digit_start: i32 = start + 1 if negative else start
        numeric: bool = digit_start < position
        scan: i32 = digit_start
        value: i32 = 0
        while scan < position:
            character: i32 = extension_memory_get(scan)
            if character < 48 or character > 57: numeric = False
            if numeric: value = value * 10 + character - 48
            scan = scan + 1
        depth: i32 = extension_memory_get(589)
        if numeric:
            if depth >= 32: return 2
            extension_memory_set(500 + depth, 0 - value if negative else value)
            extension_memory_set(589, depth + 1)
        elif ext_elfrunner_forth_word(start, length, "DUP"):
            if depth < 1 or depth >= 32: return 2
            extension_memory_set(500 + depth, extension_memory_get(499 + depth)); extension_memory_set(589, depth + 1)
        elif ext_elfrunner_forth_word(start, length, "DROP"):
            if depth < 1: return 2
            extension_memory_set(589, depth - 1)
        elif ext_elfrunner_forth_word(start, length, "SWAP"):
            if depth < 2: return 2
            value = extension_memory_get(498 + depth); scan = extension_memory_get(499 + depth)
            extension_memory_set(498 + depth, scan); extension_memory_set(499 + depth, value)
        elif ext_elfrunner_forth_word(start, length, "OVER"):
            if depth < 2 or depth >= 32: return 2
            extension_memory_set(500 + depth, extension_memory_get(498 + depth)); extension_memory_set(589, depth + 1)
        elif ext_elfrunner_forth_word(start, length, "."):
            if depth < 1: return 2
            value = extension_memory_get(499 + depth); extension_memory_set(589, depth - 1)
            if not ext_elfrunner_forth_output_number(value): return 3
        elif ext_elfrunner_forth_word(start, length, "EMIT"):
            if depth < 1: return 2
            value = extension_memory_get(499 + depth); extension_memory_set(589, depth - 1)
            if not ext_elfrunner_forth_output_char(value): return 3
        elif ext_elfrunner_forth_word(start, length, "CR"):
            if not ext_elfrunner_forth_output_char(10): return 3
        else:
            if depth < 2: return 1
            value = extension_memory_get(499 + depth)
            scan = extension_memory_get(498 + depth)
            if ext_elfrunner_forth_word(start, length, "+"): scan = scan + value
            elif ext_elfrunner_forth_word(start, length, "-"): scan = scan - value
            elif ext_elfrunner_forth_word(start, length, "*"): scan = scan * value
            elif ext_elfrunner_forth_word(start, length, "/"):
                if value == 0: return 4
                scan = scan // value
            elif ext_elfrunner_forth_word(start, length, "MOD"):
                if value == 0: return 4
                scan = scan % value
            else: return 1
            extension_memory_set(498 + depth, scan); extension_memory_set(589, depth - 1)
    return 0


def ext_elfrunner_forth_build_sector(total_size: i32) -> None:
    fs_buffer_clear()
    fs_buffer_set(0, 0x7F); fs_buffer_set(1, 69); fs_buffer_set(2, 76); fs_buffer_set(3, 70)
    fs_buffer_set(4, 1); fs_buffer_set(5, 1); fs_buffer_set(6, 1)
    fs_buffer_set(16, 2); fs_buffer_set(18, 3); fs_buffer_set(20, 1)
    fs_put_u32(24, 0x00400054); fs_put_u32(28, 52)
    fs_buffer_set(40, 52); fs_buffer_set(42, 32); fs_buffer_set(44, 1)
    fs_put_u32(52, 1); fs_put_u32(56, 0); fs_put_u32(60, 0x00400000); fs_put_u32(64, 0x00400000)
    fs_put_u32(68, total_size); fs_put_u32(72, total_size); fs_put_u32(76, 7); fs_put_u32(80, 0x1000)
    output_length: i32 = extension_memory_get(590)
    code: i32 = 84
    index: i32 = 0
    while index <= output_length:
        fs_buffer_set(code, 0xC6); fs_buffer_set(code + 1, 0x05)
        fs_put_u32(code + 2, 0x00500000 + index)
        fs_buffer_set(code + 6, output_length if index == 0 else extension_memory_get(599 + index))
        code = code + 7; index = index + 1
    fs_buffer_set(code, 0x31); fs_buffer_set(code + 1, 0xC0); fs_buffer_set(code + 2, 0xC3)


def ext_elfrunner_forth_compile() -> i32:
    global ext_elfrunner_input_length
    source_name_length: i32 = ext_elfrunner_input_length
    if source_name_length < 5 or source_name_length > 15: ext_elfrunner_result_text("USAGE FORTHC FILE.FTH\n"); return -1
    suffix: i32 = source_name_length - 4
    if extension_memory_get(700 + suffix) != 46: ext_elfrunner_result_text("SOURCE MUST END .FTH\n"); return -1
    if not ((extension_memory_get(701 + suffix) == 70 or extension_memory_get(701 + suffix) == 102) and (extension_memory_get(702 + suffix) == 84 or extension_memory_get(702 + suffix) == 116) and (extension_memory_get(703 + suffix) == 72 or extension_memory_get(703 + suffix) == 104)): ext_elfrunner_result_text("SOURCE MUST END .FTH\n"); return -1
    if suffix > 11: ext_elfrunner_result_text("OUTPUT NAME TOO LONG\n"); return -1
    if not ext_elfrunner_text_find(0): ext_elfrunner_result_text("SOURCE NOT FOUND\n"); return -1
    source_length: i32 = ext_elfrunner_text_length
    if source_length > 480 or not ata_read_sector(ext_elfrunner_text_lba): ext_elfrunner_result_text("SOURCE READ ERROR\n"); return -1
    index: i32 = 0
    while index < source_length:
        extension_memory_set(index, fs_buffer_get(index)); index = index + 1
    parse_status: i32 = ext_elfrunner_forth_parse(source_length)
    if parse_status == 1: ext_elfrunner_result_text("UNKNOWN FORTH WORD\n"); return -1
    if parse_status == 2: ext_elfrunner_result_text("FORTH STACK ERROR\n"); return -1
    if parse_status == 3: ext_elfrunner_result_text("OUTPUT TOO LONG\n"); return -1
    if parse_status == 4: ext_elfrunner_result_text("DIVISION BY ZERO\n"); return -1
    if not ata_read_sector(16): return -1
    count: i32 = fs_get_u32(4)
    if count > 30: count = 30
    target: i32 = -1
    target_lba: i32 = 0
    reusable: i32 = -1
    next_lba: i32 = 32
    entry: i32 = 0
    while entry < count:
        if entry % 15 == 0 and not ata_read_sector(16 + entry // 15): return -1
        offset: i32 = 8 + (entry % 15) * 32
        lba: i32 = fs_get_u32(offset + 16); size: i32 = fs_get_u32(offset + 20)
        end_lba: i32 = lba + (size + 511) // 512
        if end_lba > next_lba: next_lba = end_lba
        stored_length: i32 = 0
        while stored_length < 16 and fs_buffer_get(offset + stored_length) != 0: stored_length = stored_length + 1
        if stored_length == 0 and reusable < 0: reusable = entry
        same: bool = stored_length == suffix + 4 and fs_buffer_get(offset + 24) == 0xF0 and fs_buffer_get(offset + 25) == ext_elfrunner_cwd
        name_index: i32 = 0
        while same and name_index < suffix:
            wanted: i32 = extension_memory_get(700 + name_index)
            if wanted >= 97 and wanted <= 122: wanted = wanted - 32
            if fs_buffer_get(offset + name_index) != wanted: same = False
            name_index = name_index + 1
        if same and (fs_buffer_get(offset + suffix) != 46 or fs_buffer_get(offset + suffix + 1) != 69 or fs_buffer_get(offset + suffix + 2) != 76 or fs_buffer_get(offset + suffix + 3) != 70): same = False
        if same: target = entry; target_lba = lba
        entry = entry + 1
    if target < 0:
        if reusable >= 0: target = reusable; target_lba = next_lba
        else:
            if count >= 30: ext_elfrunner_result_text("ELF DIRECTORY FULL\n"); return -1
            target = count; count = count + 1; target_lba = next_lba
    output_length: i32 = extension_memory_get(590)
    total_size: i32 = 84 + (output_length + 1) * 7 + 3
    ext_elfrunner_forth_build_sector(total_size)
    if not ata_write_sector(target_lba): return -1
    directory_sector: i32 = 16 + target // 15
    if not ata_read_sector(directory_sector): return -1
    offset = 8 + (target % 15) * 32
    index = 0
    while index < 32: fs_buffer_set(offset + index, 0); index = index + 1
    index = 0
    while index < suffix:
        wanted = extension_memory_get(700 + index)
        if wanted >= 97 and wanted <= 122: wanted = wanted - 32
        fs_buffer_set(offset + index, wanted); index = index + 1
    fs_buffer_set(offset + suffix, 46); fs_buffer_set(offset + suffix + 1, 69); fs_buffer_set(offset + suffix + 2, 76); fs_buffer_set(offset + suffix + 3, 70)
    fs_put_u32(offset + 16, target_lba); fs_put_u32(offset + 20, total_size)
    fs_buffer_set(offset + 24, 0xF0); fs_buffer_set(offset + 25, ext_elfrunner_cwd)
    if directory_sector == 16: fs_put_u32(4, count)
    if not ata_write_sector(directory_sector): return -1
    if directory_sector != 16:
        if not ata_read_sector(16): return -1
        fs_put_u32(4, count)
        if not ata_write_sector(16): return -1
    physical_write8(0x00500404, 0); physical_write8(0x00500405, 0)
    ext_elfrunner_append_text("COMPILED ")
    index = 0
    while index < suffix:
        wanted = extension_memory_get(700 + index)
        if wanted >= 97 and wanted <= 122: wanted = wanted - 32
        ext_elfrunner_append_char(wanted); index = index + 1
    ext_elfrunner_append_text(".ELF\nTYPE: ")
    index = 0
    while index < suffix:
        wanted = extension_memory_get(700 + index)
        if wanted >= 97 and wanted <= 122: wanted = wanted - 32
        ext_elfrunner_append_char(wanted); index = index + 1
    ext_elfrunner_append_char(10)
    return 0

def ext_elfrunner_service_syscall() -> i32:
    global ext_elfrunner_input_length, ext_elfrunner_text_length, ext_elfrunner_text_cursor, ext_elfrunner_status, ext_elfrunner_waiting_editor
    operation: i32 = physical_read8(0x00500400)
    name_length: i32 = physical_read8(0x00500402)
    maximum_name_length: i32 = 31 if operation == 7 or operation == 8 or operation == 15 or operation == 16 or operation == 17 or operation == 26 else 15
    if name_length > maximum_name_length or ((operation == 1 or operation == 2 or operation == 4 or operation == 5 or operation == 7 or operation == 8 or operation == 9 or operation == 10) and name_length <= 0):
        physical_write8(0x00500401, 1)
        return 1
    ext_elfrunner_input_length = name_length
    name_index: i32 = 0
    while name_index < name_length:
        extension_memory_set(700 + name_index, physical_read8(0x00500410 + name_index))
        name_index = name_index + 1
    if operation == 1:
        if not ext_elfrunner_text_find(0) or not ata_read_sector(ext_elfrunner_text_lba):
            physical_write8(0x00500401, 1)
            return 1
        result_length: i32 = ext_elfrunner_text_length
        if result_length > 480: result_length = 480
        physical_write8(0x00500401, 0)
        physical_write8(0x00500404, result_length & 255)
        physical_write8(0x00500405, (result_length >> 8) & 255)
        result_index: i32 = 0
        while result_index < result_length:
            physical_write8(0x00500420 + result_index, fs_buffer_get(result_index))
            result_index = result_index + 1
        return 1
    if operation == 2:
        found: bool = ext_elfrunner_text_find(0)
        if not found:
            if not ext_elfrunner_text_prepare_new(0):
                physical_write8(0x00500401, 1)
                return 1
        elif not ata_read_sector(ext_elfrunner_text_lba):
            physical_write8(0x00500401, 1)
            return 1
        if found:
            if ext_elfrunner_text_length > 480: ext_elfrunner_text_length = 480
            result_index = 0
            while result_index < ext_elfrunner_text_length:
                extension_memory_set(result_index, fs_buffer_get(result_index))
                result_index = result_index + 1
        ext_elfrunner_text_cursor = ext_elfrunner_text_length
        ext_elfrunner_waiting_editor = 1
        ext_elfrunner_status = 3
        return 0
    syscall_status: i32 = -1
    if operation == 3: syscall_status = ext_elfrunner_fs_list()
    elif operation == 4: syscall_status = ext_elfrunner_fs_mkdir()
    elif operation == 5: syscall_status = ext_elfrunner_fs_cd()
    elif operation == 6: syscall_status = ext_elfrunner_fs_pwd()
    elif operation == 7: syscall_status = ext_elfrunner_fs_copy()
    elif operation == 8: syscall_status = ext_elfrunner_fs_move()
    elif operation == 9: syscall_status = ext_elfrunner_fs_remove()
    elif operation == 10: syscall_status = ext_elfrunner_fs_touch()
    elif operation == 11: syscall_status = ext_elfrunner_fs_info()
    elif operation == 12: syscall_status = ext_elfrunner_fs_date()
    elif operation == 13: syscall_status = ext_elfrunner_extension_processes()
    elif operation == 14: ext_elfrunner_result_text("TETRIS OS PYTHONOS I386 LPYTHON LLVM\n"); syscall_status = 0
    elif operation == 15: syscall_status = ext_elfrunner_extension_info()
    elif operation == 16: syscall_status = ext_elfrunner_extension_run()
    elif operation == 17: syscall_status = ext_elfrunner_extension_kill()
    elif operation == 18: syscall_status = ext_elfrunner_kv_list()
    elif operation == 19: syscall_status = ext_elfrunner_sector_view()
    elif operation == 20: syscall_status = ext_elfrunner_fsck()
    elif operation == 21:
        physical_write8(0x00500401, 0)
        io_out8(0x64, 0xFE)
        return 1
    elif operation == 22: syscall_status = ext_elfrunner_fs_find()
    elif operation == 23: syscall_status = ext_elfrunner_fs_wc()
    elif operation == 24: syscall_status = ext_elfrunner_fs_hexdump()
    elif operation == 25: syscall_status = ext_elfrunner_uptime()
    elif operation == 26: syscall_status = ext_elfrunner_forth_compile()
    else:
        physical_write8(0x00500401, 2)
        return 1
    physical_write8(0x00500401, 0 if syscall_status == 0 else 1)
    return 1


def ext_elfrunner_resume_editor(saved: i32) -> None:
    global ext_elfrunner_status, ext_elfrunner_waiting_editor
    physical_write8(0x00500401, 0 if saved == 1 else 2)
    ext_elfrunner_waiting_editor = 0
    resume_result: i32 = elf_call_entry(ext_elfrunner_entry)
    if resume_result == 1: ext_elfrunner_status = 1
    else:
        ext_elfrunner_status = 2
        ext_elfrunner_save_log()

def ext_elfrunner_save_log() -> None:
    fs_buffer_clear()
    fs_buffer_set(0, 69); fs_buffer_set(1, 76); fs_buffer_set(2, 79); fs_buffer_set(3, 71)
    log_length: i32 = physical_read8(0x00500000)
    if log_length > 250: log_length = 250
    fs_put_u32(4, log_length)
    fs_put_u32(8, ext_elfrunner_event_sequence)
    log_index: i32 = 0
    while log_index < log_length:
        fs_buffer_set(16 + log_index, physical_read8(0x00500001 + log_index))
        log_index = log_index + 1
    ata_write_sector(19)

def ext_elfrunner_load_cwd_name() -> i32:
    if ext_elfrunner_cwd == 0: return 0
    if not ext_elfrunner_text_directory(): return 0
    entry_offset: i32 = 8 + (ext_elfrunner_cwd - 1) * 32
    length: i32 = 0
    while length < 15 and fs_buffer_get(entry_offset + length) != 0:
        extension_memory_set(620 + length, fs_buffer_get(entry_offset + length))
        length = length + 1
    return length

def ext_elfrunner_draw() -> None:
    if ext_elfrunner_status == 3:
        ext_elfrunner_draw_editor()
        return
    clear_screen(0x00)
    # TETRIS OS ELF TERMINAL
    ui_put_cell(3, 1, 84, 0x0A); ui_put_cell(4, 1, 69, 0x0A); ui_put_cell(5, 1, 84, 0x0A); ui_put_cell(6, 1, 82, 0x0A); ui_put_cell(7, 1, 73, 0x0A); ui_put_cell(8, 1, 83, 0x0A)
    ui_put_cell(10, 1, 79, 0x0A); ui_put_cell(11, 1, 83, 0x0A)
    ui_put_cell(13, 1, 69, 0x0A); ui_put_cell(14, 1, 76, 0x0A); ui_put_cell(15, 1, 70, 0x0A)
    ui_put_cell(17, 1, 84, 0x0A); ui_put_cell(18, 1, 69, 0x0A); ui_put_cell(19, 1, 82, 0x0A); ui_put_cell(20, 1, 77, 0x0A); ui_put_cell(21, 1, 73, 0x0A); ui_put_cell(22, 1, 78, 0x0A); ui_put_cell(23, 1, 65, 0x0A); ui_put_cell(24, 1, 76, 0x0A)
    length: i32 = physical_read8(0x00500000)
    position: i32 = 0
    output_x: i32 = 3
    output_y: i32 = 6
    while position < length and output_y < 18:
        output_character: i32 = physical_read8(0x00500001 + position)
        if output_character == 10:
            output_x = 3
            output_y = output_y + 1
        else:
            ui_put_cell(output_x, output_y, output_character, 0x0A)
            output_x = output_x + 1
            if output_x >= 77:
                output_x = 3
                output_y = output_y + 1
        position = position + 1
    if ext_elfrunner_last_error != 0:
        ui_put_cell(3, 18, 78, 0x0C); ui_put_cell(4, 18, 79, 0x0C); ui_put_cell(5, 18, 84, 0x0C)
        ui_put_cell(7, 18, 70, 0x0C); ui_put_cell(8, 18, 79, 0x0C); ui_put_cell(9, 18, 85, 0x0C); ui_put_cell(10, 18, 78, 0x0C); ui_put_cell(11, 18, 68, 0x0C)
    input_y: i32 = 20
    input_x: i32 = 10
    if ext_elfrunner_status == 1:
        ui_put_cell(3, input_y, 83, 0x0B); ui_put_cell(4, input_y, 84, 0x0B); ui_put_cell(5, input_y, 68, 0x0B); ui_put_cell(6, input_y, 73, 0x0B); ui_put_cell(7, input_y, 78, 0x0B); ui_put_cell(8, input_y, 62, 0x0A)
    else:
        ui_put_cell(3, input_y, 67, 0x07); ui_put_cell(4, input_y, 58, 0x07); ui_put_cell(5, input_y, 47, 0x07); ui_put_cell(6, input_y, 69, 0x07); ui_put_cell(7, input_y, 88, 0x07); ui_put_cell(8, input_y, 84, 0x07)
        cwd_length: i32 = ext_elfrunner_load_cwd_name()
        if cwd_length == 0:
            ui_put_cell(9, input_y, 62, 0x0A)
            input_x = 10
        else:
            ui_put_cell(9, input_y, 47, 0x07)
            cwd_index: i32 = 0
            while cwd_index < cwd_length:
                ui_put_cell(10 + cwd_index, input_y, extension_memory_get(620 + cwd_index), 0x07)
                cwd_index = cwd_index + 1
            ui_put_cell(10 + cwd_length, input_y, 62, 0x0A)
            input_x = 11 + cwd_length
    input_index: i32 = 0
    while input_index < ext_elfrunner_input_length:
        ui_put_cell(input_x + input_index, input_y, extension_memory_get(700 + input_index), 0x0F)
        input_index = input_index + 1
    ui_put_cell(input_x + ext_elfrunner_cursor, input_y + 1, 94, 0x0E)
    ui_put_cell(3, 23, 69, 0x0A); ui_put_cell(4, 23, 78, 0x0A); ui_put_cell(5, 23, 84, 0x0A); ui_put_cell(6, 23, 69, 0x0A); ui_put_cell(7, 23, 82, 0x0A)
    ui_put_cell(9, 23, 82, 0x07); ui_put_cell(10, 23, 85, 0x07); ui_put_cell(11, 23, 78, 0x07)
    ui_put_cell(15, 23, 69, 0x0C); ui_put_cell(16, 23, 83, 0x0C); ui_put_cell(17, 23, 67, 0x0C); ui_put_cell(19, 23, 66, 0x07); ui_put_cell(20, 23, 65, 0x07); ui_put_cell(21, 23, 67, 0x07); ui_put_cell(22, 23, 75, 0x07)


def ext_elfrunner_key(key: i32) -> i32:
    global ext_elfrunner_status, ext_elfrunner_input_length, ext_elfrunner_cursor, ext_elfrunner_last_error, ext_elfrunner_event_sequence, ext_elfrunner_stdin_length, ext_elfrunner_text_length, ext_elfrunner_text_cursor
    run_result: i32 = 0
    character: i32 = 0
    if keyboard_control == 1 and key == 0x2E and (ext_elfrunner_status == 1 or ext_elfrunner_status == 3):
        output_length: i32 = physical_read8(0x00500000)
        if output_length < 248:
            physical_write8(0x00500001 + output_length, 94)
            physical_write8(0x00500002 + output_length, 67)
            physical_write8(0x00500000, output_length + 2)
        ext_elfrunner_status = 2
        ext_elfrunner_waiting_editor = 0
        ext_elfrunner_input_length = 0
        ext_elfrunner_cursor = 0
        ext_elfrunner_save_log()
        return 0
    if ext_elfrunner_status == 3:
        if key == 0x01:
            ext_elfrunner_resume_editor(0)
            return 3
        if key == 0x1C and keyboard_shifted == 1:
            if ext_elfrunner_text_save():
                ext_elfrunner_resume_editor(1)
            else:
                ext_elfrunner_last_error = 12
            return 0
        if key == 0x4B:
            if ext_elfrunner_text_cursor > 0: ext_elfrunner_text_cursor = ext_elfrunner_text_cursor - 1
            return 0
        if key == 0x4D:
            if ext_elfrunner_text_cursor < ext_elfrunner_text_length: ext_elfrunner_text_cursor = ext_elfrunner_text_cursor + 1
            return 0
        if key == 0x48:
            ext_elfrunner_text_move_vertical(-1)
            return 0
        if key == 0x50:
            ext_elfrunner_text_move_vertical(1)
            return 0
        if key == 0x0E and ext_elfrunner_text_cursor > 0:
            editor_delete: i32 = ext_elfrunner_text_cursor - 1
            while editor_delete + 1 < ext_elfrunner_text_length:
                extension_memory_set(editor_delete, extension_memory_get(editor_delete + 1))
                editor_delete = editor_delete + 1
            ext_elfrunner_text_length = ext_elfrunner_text_length - 1
            ext_elfrunner_text_cursor = ext_elfrunner_text_cursor - 1
            return 0
        if key == 0x53 and ext_elfrunner_text_cursor < ext_elfrunner_text_length:
            editor_forward_delete: i32 = ext_elfrunner_text_cursor
            while editor_forward_delete + 1 < ext_elfrunner_text_length:
                extension_memory_set(editor_forward_delete, extension_memory_get(editor_forward_delete + 1))
                editor_forward_delete = editor_forward_delete + 1
            ext_elfrunner_text_length = ext_elfrunner_text_length - 1
            return 0
        character = scancode_ascii(key)
        if key == 0x1C: character = 10
        if character != 0 and ext_elfrunner_text_length < 480:
            editor_insert: i32 = ext_elfrunner_text_length
            while editor_insert > ext_elfrunner_text_cursor:
                extension_memory_set(editor_insert, extension_memory_get(editor_insert - 1))
                editor_insert = editor_insert - 1
            extension_memory_set(ext_elfrunner_text_cursor, character)
            ext_elfrunner_text_length = ext_elfrunner_text_length + 1
            ext_elfrunner_text_cursor = ext_elfrunner_text_cursor + 1
        return 0
    if ext_elfrunner_status == 1:
        character = scancode_ascii(key)
        if key == 0x1C: character = 10
        elif key == 0x0E: character = 8
        elif key == 0x53: character = 127
        ext_elfrunner_event_sequence = ext_elfrunner_event_sequence + 1
        physical_write8(0x00500200, ext_elfrunner_event_sequence & 255)
        physical_write8(0x00500201, key)
        physical_write8(0x00500202, character)
        physical_write8(0x00500203, keyboard_shifted)
        physical_write8(0x00500204, 1)
        if character != 0 and ext_elfrunner_stdin_length < 250:
            physical_write8(0x00500102 + ext_elfrunner_stdin_length, character)
            ext_elfrunner_stdin_length = ext_elfrunner_stdin_length + 1
            physical_write8(0x00500100, ext_elfrunner_stdin_length)
        run_result = elf_call_entry(ext_elfrunner_entry)
        if run_result == 2:
            if ext_elfrunner_service_syscall() == 0: return 0
            run_result = elf_call_entry(ext_elfrunner_entry)
        if run_result == 1:
            ext_elfrunner_status = 1
        else:
            ext_elfrunner_status = 2
            ext_elfrunner_save_log()
        return 0
    if key == 0x1C and ext_elfrunner_status == 2 and ext_elfrunner_input_length > 0:
        if ext_elfrunner_find_file():
            ext_elfrunner_last_error = 0
            ext_elfrunner_stdin_length = 0
            run_result = ext_elfrunner_load()
            if run_result == 2:
                if ext_elfrunner_service_syscall() != 0: run_result = elf_call_entry(ext_elfrunner_entry)
            if run_result == 1: ext_elfrunner_status = 1
            elif run_result == 2: ext_elfrunner_status = 3
            else: ext_elfrunner_status = 2
            if run_result < 0: ext_elfrunner_last_error = 0 - run_result
            if run_result == 0: ext_elfrunner_save_log()
        else:
            ext_elfrunner_last_error = 11
        ext_elfrunner_input_length = 0
        ext_elfrunner_cursor = 0
    elif ext_elfrunner_status == 2 and key == 0x4B:
        if ext_elfrunner_cursor > 0: ext_elfrunner_cursor = ext_elfrunner_cursor - 1
    elif ext_elfrunner_status == 2 and key == 0x4D:
        if ext_elfrunner_cursor < ext_elfrunner_input_length: ext_elfrunner_cursor = ext_elfrunner_cursor + 1
    elif ext_elfrunner_status == 2 and key == 0x0E and ext_elfrunner_cursor > 0:
        delete_index: i32 = ext_elfrunner_cursor - 1
        while delete_index + 1 < ext_elfrunner_input_length:
            extension_memory_set(700 + delete_index, extension_memory_get(701 + delete_index))
            delete_index = delete_index + 1
        ext_elfrunner_input_length = ext_elfrunner_input_length - 1
        ext_elfrunner_cursor = ext_elfrunner_cursor - 1
        extension_memory_set(700 + ext_elfrunner_input_length, 0)
    elif ext_elfrunner_status == 2 and key == 0x53 and ext_elfrunner_cursor < ext_elfrunner_input_length:
        forward_delete_index: i32 = ext_elfrunner_cursor
        while forward_delete_index + 1 < ext_elfrunner_input_length:
            extension_memory_set(700 + forward_delete_index, extension_memory_get(701 + forward_delete_index))
            forward_delete_index = forward_delete_index + 1
        ext_elfrunner_input_length = ext_elfrunner_input_length - 1
        extension_memory_set(700 + ext_elfrunner_input_length, 0)
    elif ext_elfrunner_status == 2:
        character = scancode_ascii(key)
        if character != 0 and ext_elfrunner_input_length < 59:
            insert_index: i32 = ext_elfrunner_input_length
            while insert_index > ext_elfrunner_cursor:
                extension_memory_set(700 + insert_index, extension_memory_get(699 + insert_index))
                insert_index = insert_index - 1
            extension_memory_set(700 + ext_elfrunner_cursor, character)
            ext_elfrunner_input_length = ext_elfrunner_input_length + 1
            ext_elfrunner_cursor = ext_elfrunner_cursor + 1
    return 0
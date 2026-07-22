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
    if file_count > 15: file_count = 15
    file_index: i32 = 0
    while file_index < file_count:
        entry_offset: i32 = 8 + file_index * 32
        name_length: i32 = 0
        while name_length < 16 and fs_buffer_get(entry_offset + name_length) != 0:
            name_length = name_length + 1
        same: bool = name_length == command_name_length or name_length == command_name_length + 4
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
    if wanted_length <= 0 or wanted_length > 15 or count >= 12: return False
    ext_elfrunner_text_entry = count
    ext_elfrunner_text_lba = 20 + count
    ext_elfrunner_text_name_length = wanted_length
    ext_elfrunner_text_length = 0
    offset: i32 = 8 + count * 32
    index: i32 = 0
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
    fs_put_u32(4, count + 1)
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
    physical_write8(0x00500404, output & 255); physical_write8(0x00500405, (output >> 8) & 255)
    return 0


def ext_elfrunner_fs_mkdir() -> i32:
    if not ext_elfrunner_text_directory(): return -1
    count: i32 = fs_get_u32(4)
    if count >= 12: return -1
    wanted: i32 = ext_elfrunner_input_length
    entry: i32 = 0
    while entry < count:
        offset: i32 = 8 + entry * 32
        same: bool = fs_buffer_get(offset + 25) == ext_elfrunner_cwd
        name_index: i32 = 0
        while same and name_index < wanted:
            stored: i32 = fs_buffer_get(offset + name_index)
            typed: i32 = extension_memory_get(700 + name_index)
            if typed >= 97 and typed <= 122: typed = typed - 32
            if stored != typed: same = False
            name_index = name_index + 1
        if same and fs_buffer_get(offset + wanted) == 0: return -2
        entry = entry + 1
    offset = 8 + count * 32
    name_index = 0
    while name_index < wanted:
        typed = extension_memory_get(700 + name_index)
        if typed >= 97 and typed <= 122: typed = typed - 32
        fs_buffer_set(offset + name_index, typed)
        name_index = name_index + 1
    fs_buffer_set(offset + 24, 1); fs_buffer_set(offset + 25, ext_elfrunner_cwd)
    fs_put_u32(4, count + 1)
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

def ext_elfrunner_service_syscall() -> i32:
    global ext_elfrunner_input_length, ext_elfrunner_text_length, ext_elfrunner_text_cursor, ext_elfrunner_status, ext_elfrunner_waiting_editor
    operation: i32 = physical_read8(0x00500400)
    name_length: i32 = physical_read8(0x00500402)
    if name_length > 15 or ((operation == 1 or operation == 2 or operation == 4 or operation == 5) and name_length <= 0):
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
    ata_write_sector(17)

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
# Sample LPython extension: editable Version 1-L QR generator (byte mode).
# The build registry derives ext_qr_generator_* from this filename.
ext_qr_generator_length: i32 = 0
ext_qr_generator_ready: i32 = 0
ext_qr_generator_bit_length: i32 = 0
ext_qr_generator_editing: i32 = 1
ext_qr_generator_ease_start: i32 = 0
ext_qr_generator_ease_last: i32 = -1


def ext_qr_generator_cell(x: i32, y: i32) -> i32:
    return extension_memory_get(y * 21 + x)


def ext_qr_generator_set_cell(x: i32, y: i32, value: i32) -> None:
    if x >= 0 and x < 21 and y >= 0 and y < 21:
        extension_memory_set(y * 21 + x, value)


def ext_qr_generator_reserve(x: i32, y: i32, dark: i32) -> None:
    ext_qr_generator_set_cell(x, y, 3 if dark != 0 else 2)


def ext_qr_generator_finder(origin_x: i32, origin_y: i32) -> None:
    dy: i32 = -1
    while dy <= 7:
        dx: i32 = -1
        while dx <= 7:
            x: i32 = origin_x + dx
            y: i32 = origin_y + dy
            dark: i32 = 0
            if dx >= 0 and dx <= 6 and dy >= 0 and dy <= 6:
                if dx == 0 or dx == 6 or dy == 0 or dy == 6 or (dx >= 2 and dx <= 4 and dy >= 2 and dy <= 4): dark = 1
            ext_qr_generator_reserve(x, y, dark)
            dx = dx + 1
        dy = dy + 1


def ext_qr_generator_append(value: i32, count: i32) -> None:
    global ext_qr_generator_bit_length
    bit: i32 = count - 1
    while bit >= 0:
        byte_index: i32 = ext_qr_generator_bit_length // 8
        shift: i32 = 7 - ext_qr_generator_bit_length % 8
        old_value: i32 = extension_memory_get(520 + byte_index)
        extension_memory_set(520 + byte_index, old_value | (((value >> bit) & 1) << shift))
        ext_qr_generator_bit_length = ext_qr_generator_bit_length + 1
        bit = bit - 1


def ext_qr_generator_gf_multiply(left: i32, right: i32) -> i32:
    result: i32 = 0
    value: i32 = left
    multiplier: i32 = right
    while multiplier > 0:
        if (multiplier & 1) != 0: result = result ^ value
        value = value << 1
        if (value & 0x100) != 0: value = value ^ 0x11D
        multiplier = multiplier >> 1
    return result


def ext_qr_generator_coefficient(index: i32) -> i32:
    if index == 0: return 127
    if index == 1: return 122
    if index == 2: return 154
    if index == 3: return 164
    if index == 4: return 11
    if index == 5: return 68
    return 117


def ext_qr_generator_build_codewords() -> None:
    global ext_qr_generator_bit_length
    index: i32 = 0
    while index < 26:
        extension_memory_set(520 + index, 0)
        index = index + 1
    ext_qr_generator_bit_length = 0
    ext_qr_generator_append(4, 4)
    ext_qr_generator_append(ext_qr_generator_length, 8)
    index = 0
    while index < ext_qr_generator_length:
        ext_qr_generator_append(extension_memory_get(500 + index), 8)
        index = index + 1
    remaining: i32 = 152 - ext_qr_generator_bit_length
    terminator: i32 = 4 if remaining >= 4 else remaining
    ext_qr_generator_append(0, terminator)
    while ext_qr_generator_bit_length % 8 != 0:
        ext_qr_generator_append(0, 1)
    pad: i32 = 0
    while ext_qr_generator_bit_length < 152:
        ext_qr_generator_append(0xEC if pad % 2 == 0 else 0x11, 8)
        pad = pad + 1
    index = 0
    while index < 7:
        extension_memory_set(550 + index, 0)
        index = index + 1
    data_index: i32 = 0
    while data_index < 19:
        factor: i32 = extension_memory_get(520 + data_index) ^ extension_memory_get(550)
        index = 0
        while index < 6:
            next_ecc: i32 = extension_memory_get(551 + index)
            extension_memory_set(550 + index, next_ecc ^ ext_qr_generator_gf_multiply(factor, ext_qr_generator_coefficient(index)))
            index = index + 1
        extension_memory_set(556, ext_qr_generator_gf_multiply(factor, ext_qr_generator_coefficient(6)))
        data_index = data_index + 1
    index = 0
    while index < 7:
        extension_memory_set(539 + index, extension_memory_get(550 + index))
        index = index + 1


def ext_qr_generator_build_matrix() -> None:
    index: i32 = 0
    while index < 441:
        extension_memory_set(index, -1)
        index = index + 1
    ext_qr_generator_finder(0, 0)
    ext_qr_generator_finder(14, 0)
    ext_qr_generator_finder(0, 14)
    timing: i32 = 8
    while timing < 13:
        ext_qr_generator_reserve(timing, 6, 1 if timing % 2 == 0 else 0)
        ext_qr_generator_reserve(6, timing, 1 if timing % 2 == 0 else 0)
        timing = timing + 1
    # Reserve and write the two format-information tracks (L, mask 0).
    format_value: i32 = 0x77C4
    format_index: i32 = 0
    while format_index < 15:
        format_bit: i32 = (format_value >> format_index) & 1
        if format_index < 6: ext_qr_generator_reserve(8, format_index, format_bit)
        elif format_index < 8: ext_qr_generator_reserve(8, format_index + 1, format_bit)
        else: ext_qr_generator_reserve(8, 21 - 15 + format_index, format_bit)
        if format_index < 8: ext_qr_generator_reserve(20 - format_index, 8, format_bit)
        elif format_index == 8: ext_qr_generator_reserve(7, 8, format_bit)
        else: ext_qr_generator_reserve(15 - format_index - 1, 8, format_bit)
        format_index = format_index + 1
    ext_qr_generator_reserve(8, 13, 1)
    bit_index: i32 = 0
    column: i32 = 20
    upward: i32 = 1
    while column > 0:
        if column == 6: column = column - 1
        row_step: i32 = 0
        while row_step < 21:
            row: i32 = 20 - row_step if upward == 1 else row_step
            pair: i32 = 0
            while pair < 2:
                x: i32 = column - pair
                if ext_qr_generator_cell(x, row) == -1:
                    data_bit: i32 = 0
                    if bit_index < 208:
                        bit_shift: i32 = 7 - bit_index % 8
                        data_bit = (extension_memory_get(520 + bit_index // 8) >> bit_shift) & 1
                    if (x + row) % 2 == 0: data_bit = 1 - data_bit
                    ext_qr_generator_set_cell(x, row, data_bit)
                    bit_index = bit_index + 1
                pair = pair + 1
            row_step = row_step + 1
        upward = 1 - upward
        column = column - 2


def ext_qr_generator_generate() -> None:
    ext_qr_generator_build_codewords()
    ext_qr_generator_build_matrix()


def ext_qr_generator_initialize() -> None:
    global ext_qr_generator_length, ext_qr_generator_ready, ext_qr_generator_editing
    if ext_qr_generator_ready != 0: return
    ext_qr_generator_length = 0
    ext_qr_generator_editing = 1
    ext_qr_generator_ready = 1
    ext_qr_generator_generate()

def ext_qr_generator_palette(index: i32, red: i32, green: i32, blue: i32) -> None:
    ui_set_palette_entry(index, red, green, blue)



def ext_qr_generator_enter() -> None:
    global ext_qr_generator_ease_start, ext_qr_generator_ease_last, ext_qr_generator_editing
    ext_qr_generator_editing = 1
    ext_qr_generator_ease_start = system_periods
    ext_qr_generator_ease_last = -1
    ext_qr_generator_palette(32, 0, 0, 0)
    ext_qr_generator_palette(33, 0, 0, 0)


def ext_qr_generator_update() -> None:
    global ext_qr_generator_ease_last
    elapsed: i32 = system_periods - ext_qr_generator_ease_start
    if elapsed < 0: elapsed = 0
    if elapsed > 60: elapsed = 60
    if elapsed == ext_qr_generator_ease_last: return
    ext_qr_generator_ease_last = elapsed
    # ease-out cubic, scaled to 0..60 using integer-only LPython arithmetic.
    remaining: i32 = 60 - elapsed
    eased: i32 = 60 - (remaining * remaining * remaining) // 3600
    ext_qr_generator_palette(32, (2 * eased) // 60, (6 * eased) // 60, (12 * eased) // 60)
    ext_qr_generator_palette(33, (48 * eased) // 60, (63 * eased) // 60, (54 * eased) // 60)


def ext_qr_generator_exit() -> None:
    global ext_qr_generator_ease_last
    ext_qr_generator_ease_last = -1

def ext_qr_generator_draw() -> None:
    ext_qr_generator_initialize()
    clear_screen(0x10)
    text(3, 2, 81, 0x0E); text(4, 2, 82, 0x0E)
    text(6, 2, 71, 0x0F); text(7, 2, 69, 0x0F); text(8, 2, 78, 0x0F); text(9, 2, 69, 0x0F); text(10, 2, 82, 0x0F); text(11, 2, 65, 0x0F); text(12, 2, 84, 0x0F); text(13, 2, 79, 0x0F); text(14, 2, 82, 0x0F)
    # QR quiet zone is four modules on every side; each module is 5x5 pixels.
    ui_fill_rect(4, 27, 145, 145, 33)
    y: i32 = 0
    while y < 21:
        x: i32 = 0
        while x < 21:
            dark: i32 = ext_qr_generator_cell(x, y) & 1
            ui_fill_rect(24 + x * 5, 47 + y * 5, 5, 5, 32 if dark == 1 else 33)
            x = x + 1
        y = y + 1
    text(50, 6, 84, 0x0B); text(51, 6, 69, 0x0B); text(52, 6, 88, 0x0B); text(53, 6, 84, 0x0B)
    index: i32 = 0
    while index < ext_qr_generator_length:
        text(50 + index, 8, extension_memory_get(500 + index), 0x0E)
        index = index + 1
    if ext_qr_generator_editing == 1: text(50 + ext_qr_generator_length, 8, 95, 0x0E)
    text(50, 12, 84, 0x07); text(51, 12, 89, 0x07); text(52, 12, 80, 0x07); text(53, 12, 69, 0x07)
    text(50, 14, 66, 0x07); text(51, 14, 65, 0x07); text(52, 14, 67, 0x07); text(53, 14, 75, 0x07); text(54, 14, 83, 0x07); text(55, 14, 80, 0x07); text(56, 14, 65, 0x07); text(57, 14, 67, 0x07); text(58, 14, 69, 0x07)
    text(50, 16, 69, 0x0A); text(51, 16, 78, 0x0A); text(52, 16, 84, 0x0A); text(53, 16, 69, 0x0A); text(54, 16, 82, 0x0A)
    text(56, 16, 82, 0x07); text(57, 16, 69, 0x07); text(58, 16, 71, 0x07); text(59, 16, 69, 0x07); text(60, 16, 78, 0x07)
    text(50, 18, 78, 0x0E); text(52, 18, 69, 0x07); text(53, 18, 68, 0x07); text(54, 18, 73, 0x07); text(55, 18, 84, 0x07)
    text(50, 20, 69, 0x0C); text(51, 20, 83, 0x0C); text(52, 20, 67, 0x0C); text(54, 20, 66, 0x07); text(55, 20, 65, 0x07); text(56, 20, 67, 0x07); text(57, 20, 75, 0x07)


def ext_qr_generator_key(key: i32) -> i32:
    global ext_qr_generator_length, ext_qr_generator_editing
    changed: i32 = 0
    if ext_qr_generator_editing == 1:
        if key == 0x1C:
            ext_qr_generator_editing = 0
            changed = 1
        elif key == 0x0E and ext_qr_generator_length > 0:
            ext_qr_generator_length = ext_qr_generator_length - 1
            extension_memory_set(500 + ext_qr_generator_length, 0)
            changed = 1
        else:
            character: i32 = scancode_ascii(key)
            if character != 0 and ext_qr_generator_length < 17:
                extension_memory_set(500 + ext_qr_generator_length, character)
                ext_qr_generator_length = ext_qr_generator_length + 1
                changed = 1
    elif key == 0x31 or key == 0x1C:
        ext_qr_generator_editing = 1
    if changed == 1: ext_qr_generator_generate()
    return 0
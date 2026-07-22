typedef unsigned int size_t;
static volatile unsigned char *const stdout_buffer = (volatile unsigned char *)0x00500000;
static volatile unsigned char *const stdin_buffer = (volatile unsigned char *)0x00500100;
static unsigned int program_state = 0;
static unsigned int echo_started = 0;
static volatile unsigned char *const key_event = (volatile unsigned char *)0x00500200;

enum { ELF_EXIT = 0, ELF_WAIT_INPUT = 1 };

int printf(const char *format, ...) {
    unsigned int length = stdout_buffer[0];
    unsigned int source = 0;
    while (format[source] != '\0' && length < 250) {
        stdout_buffer[1 + length] = (unsigned char)format[source];
        source++;
        length++;
    }
    stdout_buffer[0] = (unsigned char)length;
    return (int)source;
}

int getchar(void) {
    unsigned int length = stdin_buffer[0];
    unsigned int cursor = stdin_buffer[1];
    if (cursor >= length) return -1;
    stdin_buffer[1] = (unsigned char)(cursor + 1);
    return stdin_buffer[2 + cursor];
}
int getkey_scancode(void) { return key_event[1]; }
int getkey_ascii(void) { return key_event[2]; }
int getkey_shift(void) { return key_event[3]; }

int _start(void) {
    if (program_state == 0) {
        stdout_buffer[0] = 0;
        printf("HelloWorld\nINPUT> ");
        program_state = 1;
        return ELF_WAIT_INPUT;
    }
    if (program_state == 1) {
        int character = getchar();
        if (character < 0) return ELF_WAIT_INPUT;
        if (character == '\n') {
            printf("\nEXIT 0");
            program_state = 2;
            return ELF_EXIT;
        }
        if (!echo_started) {
            printf("\nECHO: ");
            echo_started = 1;
        }
        if (character == 8 || character == 127) {
            printf("<DEL>");
        } else {
            char text[2];
            text[0] = (char)character;
            text[1] = '\0';
            printf(text);
        }
        return ELF_WAIT_INPUT;
    }
    return ELF_EXIT;
}
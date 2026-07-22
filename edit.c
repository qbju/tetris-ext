typedef unsigned char u8;
static volatile u8 *const out = (volatile u8 *)0x00500000;
static volatile u8 *const in = (volatile u8 *)0x00500100;
static volatile u8 *const call = (volatile u8 *)0x00500400;
static int state = 0;
static int name_len = 0;
static char name[16];
enum { EXIT = 0, WAIT = 1, SYSCALL = 2 };

static void puts(const char *s) {
    unsigned int n = out[0];
    while (*s && n < 250) out[1 + n++] = (u8)*s++;
    out[0] = (u8)n;
}
static int getchar(void) {
    unsigned int length = in[0], cursor = in[1];
    if (cursor >= length) return -1;
    in[1] = (u8)(cursor + 1);
    return in[2 + cursor];
}
static void request(unsigned int operation) {
    int i;
    call[0] = (u8)operation; call[1] = 0xFF; call[2] = (u8)name_len;
    for (i = 0; i < name_len; i++) call[16 + i] = (u8)name[i];
}
int _start(void) {
    int c;
    if (state == 0) { out[0] = 0; puts("EDIT FILE> "); state = 1; }
    if (state == 1) {
        while ((c = getchar()) >= 0) {
            if (c == 8 || c == 127) { if (name_len > 0) name_len--; }
            else if (c == '\n') { request(2); state = 2; return SYSCALL; }
            else if (name_len < 15) name[name_len++] = (char)c;
        }
        return WAIT;
    }
    if (state == 2) {
        if (call[1] == 0) puts("\nSAVED"); else puts("\nCANCELLED");
        return EXIT;
    }
    return EXIT;
}
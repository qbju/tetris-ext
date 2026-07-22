typedef unsigned char u8;
static volatile u8 *const out=(volatile u8*)0x00500000;
static volatile u8 *const in=(volatile u8*)0x00500100;
static volatile u8 *const call=(volatile u8*)0x00500400;
static int state=0, name_len=0; static char name[16];
enum { EXIT=0, WAIT=1, SYSCALL=2 };
static void puts(const char*s){unsigned n=out[0];while(*s&&n<250)out[1+n++]=(u8)*s++;out[0]=(u8)n;}
static int getchar(void){unsigned n=in[0],c=in[1];if(c>=n)return -1;in[1]=(u8)(c+1);return in[2+c];}
static void request(int op){int i;call[0]=(u8)op;call[1]=255;call[2]=(u8)name_len;for(i=0;i<name_len;i++)call[16+i]=(u8)name[i];}
static void result(void){int i,n=call[4]|(call[5]<<8);if(call[1]){puts("ERROR\n");return;}for(i=0;i<n&&out[0]<250;i++){unsigned p=out[0];out[1+p]=call[32+i];out[0]=(u8)(p+1);}}int _start(void){int c;out[0]=0;while((c=getchar())>=0&&c!=10){char t[2];t[0]=(char)c;t[1]=0;puts(t);}puts("\n");return EXIT;}
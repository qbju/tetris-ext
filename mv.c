typedef unsigned char u8;
static volatile u8 *const out=(volatile u8*)0x00500000;
static volatile u8 *const in=(volatile u8*)0x00500100;
static volatile u8 *const call=(volatile u8*)0x00500400;
static int done=0;
static int get(void){unsigned n=in[0],p=in[1];if(p>=n)return -1;in[1]=(u8)(p+1);return in[2+p];}
static void put(const char*s){unsigned n=out[0];while(*s&&n<250)out[1+n++]=(u8)*s++;out[0]=(u8)n;}
static void finish(void){int i,n=call[4]|(call[5]<<8);if(call[1])put("ERROR\n");for(i=0;i<n&&out[0]<250;i++){unsigned p=out[0];out[1+p]=call[32+i];out[0]=(u8)(p+1);}}
int _start(void){int c,n=0;if(done){finish();return 0;}done=1;out[0]=0;call[4]=0;call[5]=0;while((c=get())>=0&&c!=10&&n<31)call[16+n++]=(u8)c;call[0]=8;call[1]=255;call[2]=(u8)n;return 2;}
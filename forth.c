typedef unsigned char u8;
typedef int i32;
static volatile u8 *const out=(volatile u8*)0x00500000;
static volatile u8 *const in=(volatile u8*)0x00500100;
static i32 stack[32]; static int sp=0, started=0, token_len=0, exiting=0;
static char token[24];
static int getch(void){unsigned n=in[0],p=in[1];if(p>=n)return -1;in[1]=(u8)(p+1);return in[2+p];}
static void compact(void){int i,n=out[0];if(n<220)return;for(i=0;i<120;i++)out[1+i]=out[1+n-120+i];out[0]=120;}
static void putc1(int c){unsigned n;compact();n=out[0];if(n<250){out[1+n]=(u8)c;out[0]=(u8)(n+1);}}
static void puts1(const char*s){while(*s)putc1(*s++);}
static int eq(const char*s){int i=0;while(s[i]&&i<token_len){char a=token[i],b=s[i];if(a>='a'&&a<='z')a-=32;if(a!=b)return 0;i++;}return i==token_len&&s[i]==0;}
static void number(i32 v){char b[12];int n=0;if(v==0){putc1('0');return;}if(v<0){putc1('-');v=-v;}while(v&&n<11){b[n++]=(char)('0'+v%10);v/=10;}while(n)putc1(b[--n]);}
static int pop(i32*v){if(sp<=0){puts1(" STACK? ");return 0;}*v=stack[--sp];return 1;}
static void push(i32 v){if(sp>=32){puts1(" FULL ");return;}stack[sp++]=v;}
static int parse(i32*v){int i=0,neg=0; i32 n=0;if(token_len==0)return 0;if(token[0]=='-'){neg=1;i=1;if(token_len==1)return 0;}while(i<token_len){if(token[i]<'0'||token[i]>'9')return 0;n=n*10+token[i]-'0';i++;}*v=neg?-n:n;return 1;}
static void eval(void){i32 a,b,v;int i;if(token_len==0)return;if(parse(&v)){push(v);token_len=0;return;}
 if(eq("+")){if(pop(&b)&&pop(&a))push(a+b);}else if(eq("-")){if(pop(&b)&&pop(&a))push(a-b);}else if(eq("*")){if(pop(&b)&&pop(&a))push(a*b);}else if(eq("/")){if(pop(&b)&&pop(&a)){if(b==0){puts1(" DIV0 ");push(a);push(b);}else push(a/b);}}
 else if(eq("MOD")){if(pop(&b)&&pop(&a)){if(b==0)puts1(" DIV0 ");else push(a%b);}}else if(eq(".")){if(pop(&a)){number(a);putc1(' ');}}else if(eq("DUP")){if(sp>0)push(stack[sp-1]);else puts1(" STACK? ");}
 else if(eq("DROP")){pop(&a);}else if(eq("SWAP")){if(pop(&b)&&pop(&a)){push(b);push(a);}}else if(eq("OVER")){if(sp>=2)push(stack[sp-2]);else puts1(" STACK? ");}
 else if(eq("=")){if(pop(&b)&&pop(&a))push(a==b?-1:0);}else if(eq("<")){if(pop(&b)&&pop(&a))push(a<b?-1:0);}else if(eq(">")){if(pop(&b)&&pop(&a))push(a>b?-1:0);}
 else if(eq("EMIT")){if(pop(&a))putc1(a&255);}else if(eq("CR")){putc1('\n');}else if(eq("DEPTH")){push(sp);}else if(eq(".S")){puts1("<");number(sp);puts1("> ");for(i=0;i<sp;i++){number(stack[i]);putc1(' ');}}
 else if(eq("WORDS")){puts1("+ - * / MOD . DUP DROP SWAP OVER = < > EMIT CR DEPTH .S WORDS BYE ");}else if(eq("BYE")){exiting=1;}else{puts1(" ?");for(i=0;i<token_len;i++)putc1(token[i]);putc1(' ');}token_len=0;}
int _start(void){int c;if(!started){out[0]=0;puts1("TETRIS FORTH 0.1\nTYPE WORDS FOR HELP\nok> ");started=1;}while((c=getch())>=0){if(c==8||c==127){if(token_len>0)token_len--;}else if(c==10||c==13){eval();putc1('\n');if(exiting)return 0;puts1("ok> ");}else if(c==' '||c=='\t'){eval();putc1(' ');}else if(token_len<23){token[token_len++]=(char)c;putc1(c);}}return exiting?0:1;}
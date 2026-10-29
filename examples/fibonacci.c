int a = 0;
int b = 1;
int i = 0;
while (i < 10) {
    print(a);
    int t = a + b;
    a = b;
    b = t;
    i = i + 1;
}
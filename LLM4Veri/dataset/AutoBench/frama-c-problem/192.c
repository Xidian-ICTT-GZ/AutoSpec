#include<limits.h>

int simple(int p,int n,int r)
{
    int si;
    si = p*n*r/100;
    return si;
}
 
int main()
{
    int s = simple(10000, 3,10);
    //@ assert s == 3000;
    return 0;
}
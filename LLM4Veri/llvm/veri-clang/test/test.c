#include<stdio.h>

int test();

int main() {
    test();
    return 0;
}

int test()
{
    int w, e, s;
    for (w=0; w<=2; ++w)
    {
        for (e=0; e<=5; ++e)
        {
            for (s=0; s<=10; ++s)
            {
                if (100 == 50*w+20*e+10*s)
                {
                    printf("%d  %d  %d\n", w, e, s);
                }
            }

                        for (s=0; s<=10; ++s)
            {
                if (100 == 50*w+20*e+10*s)
                {
                    printf("%d  %d  %d\n", w, e, s);
                }
            }
        }
    }
    return 0;
}

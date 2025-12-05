## 项目介绍

### Background

Static program verification tools allow establishing formal guarantees for important program properties such as correctness and memory safety. Such tools usually compromise between the level of automation and the significance of the results. A common middle ground is to automate the proof but requires developers to manually provide specifications. Providing these specifications can be expensive and difficult, limiting the popularity and the practicality of such verification tools. Therefore, it is a key research challenge to ease the burden of manually constructing specifications.

Automated program synthesis has recently seen major advancements through the use of machine learning techniques. Large language models (LLMs) such as ChatGPT are capable of generating functional code from natural language prompts. However, LLMs are probabilistic and lack formal guarantees on the correctness and the safety of generated code.

An LLM augmented with the understanding of verification could help to improve both aspects mentioned above. Such a model can be used to automatically infer specifications for existing code to reduce the overhead of manually providing specifications. Moreover, it can also be used to directly generate verifying code with specifications, potentially from natural language prompts. As a result, the trust in code synthesized by LLMs can be greatly improved.

### Goals

This project aims to leverage existing open-source LLMs such as ChatGPT and the Frama-C verification suite to obtain a new LLM capable of generating specifications or verified programs.

----------

## 安装和部署

### Requirements

- Memory Requirements: docker image's size is about 15GB, make sure you have sufficient memory. 
- Docker: The only requirement is to install Docker (version higher than 18.09.7). You can use the command sudo apt-get install docker.io to install the docker on your Linux machine. (If you have any questions on docker, you can see Docker's Documentation).

# docker image downloads
```sh
docker pull xxx:v2
```
notice: the docker image is compiled with amd64, and if you are using arm64(macos device), you should add '--platform linux/amd64' this parameter in this command.

# clone this repo
```sh
git clone ssh@
cd 
```

# run docker image and mount local files
```sh
docker run -d -p 2222:22 -v $(pwd):/app xxx
```

# get into the container through iteractive way or ssh connection
```sh
docker exec -it container_ID /bin/bash
```
or
```sh
ssh -p 2222 root@127.0.0.1 #ssh password is 123456
cd /app
```

# set the ENV
```sh
vim ~/.bashrc

export PATH="/opt/clang/bin:$PATH"
export PATH="/app/LLM4Veri/llvm/bin:$PATH"
export VERI_LIB_PATH=/app/LLM4Veri/llvm/

source ~/.bashrc
```

# install veri-clang
```sh
cd LLM4Veri
bash ./scripts/install/install_veri-clang.sh
```

# test clang and veri-clang
```sh
clang --version
veri-clang --version
```
----------

## Usage

### Set up API_KEY and BASE_URL

there is a models_config.yaml at config/ filefolder, and there are some examples help u to set the env.
further, you need to set your API_KEY to the ~/.bashrc
```sh
vim ~/.bashrc
aliyun_API_KEY="..." # (set your API_KEY)
volcano_API_KEY="..."
source ~/.bashrc
```

### Annotate C/C++ source file

Usage:

```
fuzz.py -f <file> -m <model> -o <output_file_folder> # process single file
autofuzz.py <input_file_folder>  <model> <output_file_folder> <timeout_for_single_file(seconds)> <concurrent_count>
```

For example: `test/fib_46_benchmark_mutation/45_mutation_1.c` （约5分钟）

```C
#include <assert.h>

int unknown1();
int unknown2();
int unknown3();
int unknown4();

void foo(int p) {
  int a = 0;
  int b = 0;
  int j = 0;
  int i = 0;

  // invariant (a == b && j >= i)
  while (unknown1()) {
    a++;
    b++;
    i += a;
    j += b;
    if (p) {
      j += 1;
    }
  }
  if (j >= i)
    a = b;
  else
    a = b + 1;

  int w = 1;
  int z = 0;
  // invariant (w%2 == 1 && z%2 == 0 && a == b)
  while (unknown2()) {
    // invariant (w%2 == 1 && z%2 == 0 && a == b)
    while (unknown3()) {
      if (w % 2 == 1)
        a++;
      if (z % 2 == 0)
        b++;
    }
    z = a + b;
    w = z + 1;
  }
  static_assert(a == b);
}

```

run `./fuzz.py -f test/fib_46_benchmark_mutation/45_mutation_1.c`

Then you can get the annotated file on `test/fib_46_benchmark_mutation/45_mutation_1.c`, looks like:

```C
#include <assert.h>

int unknown1();
int unknown2();
int unknown3();
int unknown4();

/* 4. FUNC CONTRACT */
void foo(int p) {
  int a = 0;
  int b = 0;
  int j = 0;
  int i = 0;

  /* 1. LOOP INVARIANT */
  while (unknown1()) {
    a++;
    b++;
    i += a;
    j += b;
    if (p) {
      j += 1;
    }
  }
  if (j >= i)
    a = b;
  else
    a = b + 1;

  int w = 1;
  int z = 0;
  /* 3. LOOP INVARIANT */
  while (unknown2()) {
    /* 2. LOOP INVARIANT */
    while (unknown3()) {
      if (w % 2 == 1)
        a++;
      if (z % 2 == 0)
        b++;
    }
    z = a + b;
    w = z + 1;
  }
  //@ assert a == b;
}

```



After executing the above given command, the duration of fuzzing may last for 5 minutes.

You can view intermediate files in the `out/45_mutation_1_000?`

Once it find out the necessnery sepcifination, it will print "INFO:root: Congratulations, you have successfully passed the verification."

The following file could be generated in `out/45_mutation_1_0003/45_mutation_1_merged.c`. 

You can run `frama-c-gui -wp out/45_mutation_1_0003/45_mutation_1_merged.c` to see the whether the asertion can sucessfully verified.

```C
#include <assert.h>

int unknown1();
int unknown2();
int unknown3();
int unknown4();

void foo(int p) {
  int a = 0;
  int b = 0;
  int j = 0;
  int i = 0;

  /*@
  loop invariant j >= i ==> a == b;
  loop invariant j < i ==> a == b + 1;
  loop invariant i == a*(a+1)/2;
  loop invariant i == a * (a + 1) / 2;
  loop invariant b <= j;
  loop invariant a == b;
  loop invariant a <= i;
  loop invariant 0 <= j;
  loop invariant 0 <= i;
  loop invariant 0 <= b;
  loop invariant 0 <= a;
  loop assigns p;
  loop assigns j;
  loop assigns i;
  loop assigns b;
  loop assigns a;
  */
  while (unknown1()) {
    a++;
    b++;
    i += a;
    j += b;
    if (p) {
      j += 1;
    }
  }
  if (j >= i)
    a = b;
  else
    a = b + 1;

  int w = 1;
  int z = 0;
  /*@
  loop invariant w == z + 1;
  loop invariant j >= i ==> a == b;
  loop invariant j < i ==> a == b + 1;
  loop invariant a > b ==> i > j;
  loop invariant a == b;
  loop invariant a == b + 1 || a == b;
  loop invariant a == b + 1 ==> i == a * (a + 1) / 2;
  loop invariant a < b ==> i < j;
  loop invariant 0 <= z;
  loop invariant 0 <= w;
  loop invariant 0 <= j;
  loop invariant 0 <= i;
  loop invariant 0 <= b;
  loop invariant 0 <= a;
  loop assigns z;
  loop assigns w;
  loop assigns p;
  loop assigns j;
  loop assigns i;
  loop assigns b;
  loop assigns a;
  */
  while (unknown2()) {
    /*@
    loop invariant w == z + 1;
    loop invariant j >= i ==> a == b;
    loop invariant j < i ==> a == b + 1;
    loop invariant a > b ==> i > j;
    loop invariant a == b;
    loop invariant a == b + 1 || a == b;
    loop invariant a == b + 1 ==> i == a * (a + 1) / 2;
    loop invariant a < b ==> i < j;
    loop invariant 0 <= z;
    loop invariant 0 <= w;
    loop invariant 0 <= j;
    loop invariant 0 <= i;
    loop invariant 0 <= b;
    loop invariant 0 <= a;
    loop assigns z;
    loop assigns w;
    loop assigns p;
    loop assigns j;
    loop assigns i;
    loop assigns b;
    loop assigns a;
    */
    while (unknown3()) {
      if (w % 2 == 1)
        a++;
      if (z % 2 == 0)
        b++;
    }
    z = a + b;
    w = z + 1;
  }
  //@ assert a == b;
}
```
### ID-File mapping for the OOPLSA-13 benchmark (Table 3)
The mapping relationship between the ID number and actual file name in the artifact of OOPSLA-13 benchmark suite in Table 3 is as follows:

| ID | File|
| -- | -- |
| 1	 | 01.c |
| 2	 | 02.c |
| 3	 | 04.c |
| 4	 | 05.c |
| 5	 | 07.c |
| 6	 | 08.c |
| 7	 | 10.c |
| 8	 | 11.c |
| 9	 | 13.c |
| 10 | 	14.c |
| 11 | 	15.c |
| 12 | 	16.c |
| 13 | 	18.c |
| 14 | 	19.c |
| 15 | 	20.c |
| 16 | 	21.c |
| 17 | 	22.c |
| 18 | 	23.c |
| 19 | 	30.c |
| 20 | 	32.c |
| 21 | 	34.c |
| 22 | 	35.c |
| 23 | 	37.c |
| 24 | 	38.c |
| 25 | 	39.c |
| 26 | 	41.c |
| 27 | 	42.c |
| 28 | 	43.c |
| 29 | 	44.c |
| 30 | 	46.c |
| 31 | 	09.c |
| 32 | 	12.c |
| 33 | 	28.c |
| 34 | 	40.c |
| 35 | 	03.c |
| 36 | 	06.c |
| 37 | 	17.c |
| 38 | 	24.c |
| 39 | 	25.c |
| 40 | 	26.c |
| 41 | 	29.c |
| 42 | 	31.c |
| 43 | 	33.c |
| 44 | 	36.c |
| 45 | 	45.c |
| 46 | 	27.c |

----------


#include "types.h"
#include "alloc-inl.h"
#include "debug.h"
#include "config.h"
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <stdbool.h>

static u32  llvm_marjor_version = 0;  /* LLVM version						*/
static u8*  obj_path;                 /* Path to runtime libraries		*/
static u8** cc_params;                /* Parameters passed to the real CC	*/
static u32  cc_par_cnt = 1;           /* Param count, including argv0		*/
static bool isCXX = true;
static bool islink = true;
char* targetP = "";
char* targetPO = "";

/* Try to find the runtime libraries. If that fails, abort. */

static void find_obj(u8* argv0) {

  u8 *veri_lib_path = getenv("VERI_LIB_PATH");
  u8 *slash, *tmp;

  if (veri_lib_path) {
    tmp = alloc_printf("%s/lib/veri-llvm-pass.so", veri_lib_path);
    if (!access(tmp, R_OK)) {
      obj_path = veri_lib_path;
      ck_free(tmp);
      return;
    }

    ck_free(tmp);

  }

  slash = strrchr(argv0, '/');

  if (slash) {

    u8 *dir;

    *slash = 0;
    dir = ck_strdup(argv0);
    *slash = '/';
    tmp = alloc_printf("%s/lib/veri-llvm-pass.so", dir);
    if (!access(tmp, R_OK)) {
      obj_path = dir;
      ck_free(tmp);
      return;
    }

    ck_free(tmp);
    ck_free(dir);

  }
  if (!access(VERI_LIB_PATH "/lib/veri-llvm-pass.so", R_OK)) {
    obj_path = VERI_LIB_PATH;
    return;
  }

  FATAL("Unable to find 'veri-llvm-pass.so'. Please set VERI_LIB_PATH");
}


/* Detect LLVM marjor verson */

static u32 detect_llvm_verson(char* cc_compiler) {
	
	u32 marjor_version = 12;
	char result_buf[50];
	char* cc_vcommand = " -dumpversion";
	unsigned int len_vcommand = strlen(cc_compiler)+strlen(cc_vcommand);
	char* cc_version = (char*)malloc(sizeof(char*)*len_vcommand);
	memset(cc_version, 0, sizeof(len_vcommand));
	strcat(cc_version, cc_compiler);
	strcat(cc_version, cc_vcommand);
 	
	FILE *fp;
	int rc = 0; // 用于接收命令返回值
	fp = popen(cc_version, "r");
	if(NULL == fp) {
		printf("fail to execute popen.");
		exit(1);
	}
	while(fgets(result_buf, sizeof(result_buf), fp) != NULL) {
		//为了下面输出好看些，把命令返回的换行符去掉
		if('\n' == result_buf[strlen(result_buf)-1]) {
			result_buf[strlen(result_buf)-1] = '\0';
		}
	}
	//printf("command:[%s]; output: [%s]\r\n", cc_version, result_buf);
	
	if (strchr(result_buf, '.')) {
		*(strchr(result_buf, '.')) = '\0';
	}
	
	if (atoi(result_buf) != 0) {
		marjor_version = atoi(result_buf); // 版本号转整型
	}
		
	rc = pclose(fp); // 等待命令执行完毕并关闭管道及文件指针
	if(-1 == rc) {
		perror("fail to execute pclose.");
		exit(1);
	}

	return marjor_version;
}


/* Copy argv to cc_params, making the necessary edits. */

static void edit_params(u32 argc, char** argv) {

  u8 fortify_set = 0, asan_set = 0, x_set = 0, bit_mode = 0;
  u8 *name;
  char** argv_backup = argv;
  u32 argc_backup = argc;

  cc_params = ck_alloc((argc + 128) * sizeof(u8*));

  name = strrchr(argv[0], '/');
  if (!name) name = argv[0]; else name++;

  if (!strcmp(name, "veri-clang++")) {
    u8* alt_cxx = getenv("VERI_CXX");
    cc_params[0] = alt_cxx ? alt_cxx : (u8*)"clang++";
    isCXX = true;
  } else {
    u8* alt_cc = getenv("VERI_CC");
    cc_params[0] = alt_cc ? alt_cc : (u8*)"clang";
    isCXX = false;
  }
  
  llvm_marjor_version = detect_llvm_verson(cc_params[0]); // Detect LLVM marjor verson

  /* There are two ways to compile veri-clang. In the traditional mode, we
     use veri-llvm-pass.so to inject instrumentation. In the experimental
     'trace-pc-guard' mode, we use native LLVM instrumentation callbacks
     instead. The latter is a very recent addition - see:

     http://clang.llvm.org/docs/SanitizerCoverage.html#tracing-pcs-with-guards */

#ifdef USE_TRACE_PC
  cc_params[cc_par_cnt++] = "-fsanitize-coverage=trace-pc-guard";
#ifndef __ANDROID__
  cc_params[cc_par_cnt++] = "-mllvm";
  cc_params[cc_par_cnt++] = "-sanitizer-coverage-block-threshold=0";
#endif
#else
  if (llvm_marjor_version <= 12) {
	if (llvm_marjor_version >= 11 && llvm_marjor_version <= 12) {
      cc_params[cc_par_cnt++] = "-flegacy-pass-manager";
	}
    cc_params[cc_par_cnt++] = "-Xclang";
    cc_params[cc_par_cnt++] = "-load";
    cc_params[cc_par_cnt++] = "-Xclang";
    cc_params[cc_par_cnt++] = alloc_printf("%s/lib/veri-llvm-pass.so", obj_path);
  } else {
    cc_params[cc_par_cnt++] = "-fexperimental-new-pass-manager";
    cc_params[cc_par_cnt++] = alloc_printf("-fpass-plugin=%s/lib/veri-llvm-pass.so", obj_path);
  }
#endif /* ^USE_TRACE_PC */

  cc_params[cc_par_cnt++] = "-Qunused-arguments";

  //int targetP_index = 0;
  while (--argc) {
    u8* cur = *(++argv);
    
    if (!strcmp(cur, "-m32")) bit_mode = 32;
    if (!strcmp(cur, "armv7a-linux-androideabi")) bit_mode = 32;
    if (!strcmp(cur, "-m64")) bit_mode = 64;

    if (!strcmp(cur, "-x")) x_set = 1;
    if (!strcmp(cur, "-c")) {
      ; // 无需操作
    }
    
    if (!strcmp(cur, "-fsanitize=address") ||
        !strcmp(cur, "-fsanitize=memory")) asan_set = 1;

    if (strstr(cur, "FORTIFY_SOURCE")) fortify_set = 1;

    if (!strcmp(cur, "-Wl,-z,defs") ||
        !strcmp(cur, "-Wl,--no-undefined")) continue;

    cc_params[cc_par_cnt++] = cur;
  }
  argv = argv_backup;
  argc = argc_backup;

  if (getenv("VERI_HARDEN")) {

    cc_params[cc_par_cnt++] = "-fstack-protector-all";

    if (!fortify_set)
      cc_params[cc_par_cnt++] = "-D_FORTIFY_SOURCE=2";

  }

  if (!asan_set) {

    if (getenv("VERI_USE_ASAN")) {

      if (getenv("VERI_USE_MSAN"))
        FATAL("ASAN and MSAN are mutually exclusive");

      if (getenv("VERI_HARDEN"))
        FATAL("ASAN and VERI_HARDEN are mutually exclusive");

      cc_params[cc_par_cnt++] = "-U_FORTIFY_SOURCE";
      cc_params[cc_par_cnt++] = "-fsanitize=address";

    } else if (getenv("VERI_USE_MSAN")) {

      if (getenv("VERI_USE_ASAN"))
        FATAL("ASAN and MSAN are mutually exclusive");

      if (getenv("VERI_HARDEN"))
        FATAL("MSAN and VERI_HARDEN are mutually exclusive");

      cc_params[cc_par_cnt++] = "-U_FORTIFY_SOURCE";
      cc_params[cc_par_cnt++] = "-fsanitize=memory";

    }

  }

#ifdef USE_TRACE_PC

  if (getenv("VERI_INST_RATIO"))
    FATAL("VERI_INST_RATIO not available at compile time with 'trace-pc'.");

#endif /* USE_TRACE_PC */

  if (!getenv("VERI_DONT_OPTIMIZE")) {

    cc_params[cc_par_cnt++] = "-g";
    //cc_params[cc_par_cnt++] = "-O3";
    cc_params[cc_par_cnt++] = "-funroll-loops";
    #ifndef __APPLE__
    cc_params[cc_par_cnt++] = "-ldl";
    cc_params[cc_par_cnt++] = "-lpthread";
    #endif
    cc_params[cc_par_cnt++] = "-rdynamic";
  }

  if (getenv("VERI_NO_BUILTIN")) {

    cc_params[cc_par_cnt++] = "-fno-builtin-strcmp";
    cc_params[cc_par_cnt++] = "-fno-builtin-strncmp";
    cc_params[cc_par_cnt++] = "-fno-builtin-strcasecmp";
    cc_params[cc_par_cnt++] = "-fno-builtin-strncasecmp";
    cc_params[cc_par_cnt++] = "-fno-builtin-memcmp";

  }

  if (x_set) {
    cc_params[cc_par_cnt++] = "-x";
    cc_params[cc_par_cnt++] = "none";
  }

  cc_params[cc_par_cnt++] = "-Wno-deprecated";
#ifdef __APPLE__
  FILE *xcrun;
  char result_buf[250];
  xcrun = popen("/usr/bin/xcrun --show-sdk-path -sdk macosx", "r");
	if(NULL == xcrun) {
		printf("fail to execute popen.");
		exit(1);
	}
  cc_params[cc_par_cnt++] = "-L";
	while(fgets(result_buf, sizeof(result_buf), xcrun) != NULL) {
		//为了下面输出好看些，把命令返回的换行符去掉
		if('\n' == result_buf[strlen(result_buf)-1]) {
			result_buf[strlen(result_buf)-1] = '\0';
		}
    cc_params[cc_par_cnt++] = alloc_printf("%s/usr/lib", result_buf);
	}
#endif
  cc_params[cc_par_cnt] = NULL;

}


/* Main entry point */

int main(int argc, char** argv) {
  
  char** argv_backup = argv;
  int argc_backup = argc;
  
  if (isatty(2) && !getenv("VERI_QUIET")) {

#ifdef USE_TRACE_PC
    SAYF(cCYA "veri-clang [tpcg] " cBRI VERSION  cRST " by <wcventure@outlook.com>\n");
#else
    SAYF(cCYA "veri-clang " cBRI VERSION  cRST " by <wcventure@outlook.com>\n");
#endif /* ^USE_TRACE_PC */

  }

  if (argc < 2) {

    SAYF("\n"
         "This is a helper application for veri-fuzz. It serves as a drop-in replacement\n"
         "for clang, letting you recompile third-party code with the required runtime\n"
         "instrumentation. A common use pattern would be one of the following:\n\n"

         "  CC=%s/veri-clang ./configure\n"
         "  CXX=%s/veri-clang++ ./configure\n\n"

         "In contrast to the traditional veri-clang tool, this version is implemented as\n"
         "an LLVM pass and tends to offer improved performance with slow programs.\n\n"

         "You can specify custom next-stage toolchain via VERI_CC and VERI_CXX. Setting\n"
         "VERI_HARDEN enables hardening optimizations in the compiled code.\n\n",
         BIN_PATH, BIN_PATH);

    exit(1);

  }


#ifndef __ANDROID__
  find_obj(argv[0]);
#endif

  edit_params(argc, argv);
  if (llvm_marjor_version == 0 || llvm_marjor_version < 3) {
	  printf("Cannot find llvm version.\n");
	  exit(1);
  }
  
  printf("=====================================================================>\n");
  for (int i = 0; i < cc_par_cnt + 10; i++) {
    if (cc_params[i] == NULL)
      break;
    printf("%s ", cc_params[i]);
  }
  printf("\n=====================================================================>\n");
  execvp(cc_params[0], (char**)cc_params);

  //FATAL("Oops, failed to execute '%s' - check your PATH", cc_params[0]);

  return 0;

}

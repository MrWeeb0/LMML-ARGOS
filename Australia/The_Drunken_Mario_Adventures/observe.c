#define _GNU_SOURCE
#include <dlfcn.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static void *watch(void *unused){
 const char *path=getenv("MARATHON_OBSERVER");
 int (*initialized)(void)=dlsym(RTLD_DEFAULT,"Py_IsInitialized");
 int (*ensure)(void)=dlsym(RTLD_DEFAULT,"PyGILState_Ensure");
 void (*release)(int)=dlsym(RTLD_DEFAULT,"PyGILState_Release");
 void *(*modules)(void)=dlsym(RTLD_DEFAULT,"PyImport_GetModuleDict");
 void *(*item)(void*,const char*)=dlsym(RTLD_DEFAULT,"PyDict_GetItemString");
 void *(*dict)(void*)=dlsym(RTLD_DEFAULT,"PyModule_GetDict");
 int (*run)(const char*)=dlsym(RTLD_DEFAULT,"PyRun_SimpleString");
 if(!path||!initialized||!ensure||!release||!modules||!item||!dict||!run)return NULL;
 for(int i=0;i<1200;i++){
  if(initialized()){
   int gil=ensure();
   void *module=item(modules(),"lab.evolution");
   if(module&&item(dict(module),"Lab")){
    char code[8192];
    snprintf(code,sizeof(code),"exec(compile(open('%s').read(),'%s','exec'))",path,path);
    run(code);release(gil);return NULL;
   }
   release(gil);
  }
  usleep(100000);
 }
 return NULL;
}

__attribute__((constructor)) static void start(void){
 pthread_t thread;
 if(!pthread_create(&thread,NULL,watch,NULL))pthread_detach(thread);
}

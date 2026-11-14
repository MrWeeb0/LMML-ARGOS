#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

static int installed;
static __thread int busy;

static void probe(void){
 if(installed||busy)return;
 busy=1;
 void *(*modules)(void)=dlsym(RTLD_NEXT,"PyImport_GetModuleDict");
 void *(*item)(void*,const char*)=dlsym(RTLD_NEXT,"PyDict_GetItemString");
 void *(*dict)(void*)=dlsym(RTLD_NEXT,"PyModule_GetDict");
 int (*run)(const char*)=dlsym(RTLD_NEXT,"PyRun_SimpleString");
 if(modules&&item&&dict&&run){
  void *module=item(modules(),"lab.evolution");
  const char *path=getenv("MARATHON_OBSERVER");
  if(module&&item(dict(module),"Lab")&&path){
   char code[8192];installed=1;
   snprintf(code,sizeof(code),"exec(compile(open('%s').read(),'%s','exec'))",path,path);
   run(code);
  }
 }
 busy=0;
}

void *PyObject_Call(void *a,void *b,void *c){
 static void *(*real)(void*,void*,void*);
 if(!real)real=dlsym(RTLD_NEXT,"PyObject_Call");
 void *result=real(a,b,c);
 if(result)probe();
 return result;
}

void *PyImport_ImportModuleLevelObject(void *a,void *b,void *c,void *d,int e){
 static void *(*real)(void*,void*,void*,void*,int);
 if(!real)real=dlsym(RTLD_NEXT,"PyImport_ImportModuleLevelObject");
 void *result=real(a,b,c,d,e);
 if(result)probe();
 return result;
}

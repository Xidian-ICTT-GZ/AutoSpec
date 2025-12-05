/*
   VERI
   ----------------------------------------------

   Written and maintained by Cheng Wen (<wcventure@outlook.com>), Xidian University (Guangzhou)
*/
#define VERI_LLVM_PASS
#include "config.h"
#include "debug.h"

// system header
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <iostream>
#include <fstream>
#include <string>
#include <map>
#include <set>
#include <vector>
#include <cstdlib>
#include <ctime>
#include <chrono>
#include <algorithm>
#include <cassert>
#include <sys/resource.h>  // increase stack size

// LLVM header

#include <llvm/Pass.h>
#include "llvm/ADT/PostOrderIterator.h"
#include "llvm/ADT/SCCIterator.h"
#include <llvm/ADT/Statistic.h>
#include <llvm/ADT/STLExtras.h>
#include <llvm/ADT/SmallVector.h>
#include <llvm/IR/CFG.h>
#include <llvm/IR/Type.h>
#include <llvm/IR/User.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/IRBuilder.h>
#include <llvm/IR/Module.h>          // for Module
#include <llvm/IR/Function.h>        // for Function
#include <llvm/IR/BasicBlock.h>      // for BasicBlock
#include <llvm/IR/Instructions.h>    // for Instructions
#include <llvm/IR/GlobalVariable.h>  // for GlobalVariable
#include <llvm/IR/InstrTypes.h>      // for TerminatorInst
#include <llvm/IR/IntrinsicInst.h>   // for intrinsic instruction
#include <llvm/IR/InstIterator.h>    // for inst iteration
#include <llvm/IR/Constant.h>
#include <llvm/IR/Dominators.h>
#include <llvm/Support/CommandLine.h>
#include <llvm/Support/Debug.h>
#include <llvm/Support/Compiler.h>
#include <llvm/Support/MemoryBuffer.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/Transforms/IPO/PassManagerBuilder.h>
#include <llvm/Transforms/Utils/Local.h>  // for FindDbgAddrUses
#include <llvm/Transforms/Utils/ValueMapper.h>
#include <llvm/Transforms/Utils/Cloning.h>
#include <llvm/Analysis/PostDominators.h>
#include <llvm/Analysis/CallGraph.h>
#include <llvm/Analysis/CFG.h>            // for CFG
#include <llvm/Analysis/LoopInfo.h>
#if LLVM_VERSION_MAJOR >= 4
#include <llvm/Demangle/Demangle.h>
#endif

// 3rd
#include "PointerAnalysis.h"
#include <boost/algorithm/string.hpp>

#if LLVM_VERSION_MAJOR >= 13  // 11			/* use new pass manager */
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/IR/PassManager.h"
#else
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#endif

#if LLVM_VERSION_MAJOR >= 14 /* how about stable interfaces? */
#include "llvm/Passes/OptimizationLevel.h"
#endif

#if LLVM_VERSION_MAJOR >= 4 || (LLVM_VERSION_MAJOR == 3 && LLVM_VERSION_MINOR > 4)
#include "llvm/IR/DebugInfo.h"
#include "llvm/IR/CFG.h"
#else
#include "llvm/DebugInfo.h"
#include "llvm/Support/CFG.h"
#endif

using namespace llvm;
using namespace std::chrono;
using namespace std;
using std::cout;
using std::endl;
using std::vector;

namespace {
#if LLVM_VERSION_MAJOR >= 13  // 11			/* use new pass manager */
class CallGraphPass : public PassInfoMixin<CallGraphPass> {
public:
    CallGraphPass()
    {}
#else
struct CallGraphPass : public ModulePass {
public:
    static char ID; // Pass ID, replacement for typeid

    Graph *callgraph = new Graph();
    PointerAnalysis *pointerAnalysis = new PointerAnalysis();

    CallGraphPass() : ModulePass(ID) {}

    virtual void getAnalysisUsage(AnalysisUsage &AU) const override {
        AU.addRequiredTransitive<CallGraphWrapperPass>();
        AU.setPreservesAll();
    }
#endif

#if LLVM_VERSION_MAJOR >= 13  // 11			/* use new pass manager */
    PreservedAnalyses run(llvm::Module &M, ModuleAnalysisManager &MAM);
#else
    virtual bool runOnModule(llvm::Module &M) override;
#endif

#if LLVM_VERSION_MAJOR <= 3
    const char *getPassName() const override
    {
        return "CallGraphPass Instrumentation";
    }
#elif LLVM_VERSION_MAJOR >= 4 && LLVM_VERSION_MAJOR <= 12
    StringRef getPassName() const override
    {
        return "CallGraphPass Instrumentation";
    }
#endif 

    virtual bool doFinalization(llvm::Module &M) override {
        //pointerAnalysis->printPointToSet();
        //pointerAnalysis->processWorkList(callgraph); // resolve Pointers and modify the callgraph
        //callgraph->printGraph();

        //Clean up 
        delete callgraph;
        delete pointerAnalysis;
        return true;
    }

};
} // namespace


#if LLVM_VERSION_MAJOR >= 13  // 11			/* use new pass manager */
extern "C" ::llvm::PassPluginLibraryInfo LLVM_ATTRIBUTE_WEAK llvmGetPassPluginInfo()
{

    return {LLVM_PLUGIN_API_VERSION,
        "CallGraphPass",
        "v0.1",
        /* lambda to insert our pass into the pass pipeline. */
        [](PassBuilder &PB) {

#if 1
#if LLVM_VERSION_MAJOR <= 13
            using OptimizationLevel = typename PassBuilder::OptimizationLevel;
#endif
            PB.registerOptimizerLastEPCallback(
                [](ModulePassManager &MPM, OptimizationLevel OL) { MPM.addPass(CallGraphPass()); });
/* TODO LTO registration */
#else
            using PipelineElement = typename PassBuilder::PipelineElement;
            PB.registerPipelineParsingCallback([](StringRef Name, ModulePassManager &MPM, ArrayRef<PipelineElement>) {
                if (Name == "CallGraphPass") {
                    MPM.addPass(CallGraphPass());
                    return true;
                } else {
                    return false;
                }
            });
#endif
        }};
}
#else
char CallGraphPass::ID = 0;
#endif


/*!
 * Get source code line number of a function according to debug info
 */
std::string getSourceLocOfFunction(const llvm::Function *F)
{
    std::string str;
    raw_string_ostream rawstr(str);
    NamedMDNode* CU_Nodes = F->getParent()->getNamedMetadata("llvm.dbg.cu");
    if(CU_Nodes) {
      /*
       * Looks like the DICompileUnt->getSubprogram was moved into Function::
       */
        for (unsigned i = 0, e = CU_Nodes->getNumOperands(); i != e; ++i) {
		#if LLVM_VERSION_MAJOR < 4 /* LLVM 3.6.2 */
            DICompileUnit CUNode(CU_Nodes->getOperand(i));
            DIArray SPs = CUNode.getSubprograms();
            for (unsigned i = 0, e = SPs.getNumElements(); i != e; ++i) {
                DISubprogram SP(SPs.getElement(i));
                if (F == SP.getFunction()) {
                    //rawstr << "in line: " << SP.getLineNumber() << " file: " << SP.getFilename();
                    rawstr << SP.getFilename() << ":" << SP.getLineNumber();
                }
            }
        #else
            /*
            * https://reviews.llvm.org/D18074?id=50385 
            * looks like the relevant
            */
            if (DISubprogram *SP =  F->getSubprogram()) {
                if (SP->describes(F)) {
                    //rawstr << "in line: " << SP->getLine() << " file: " << SP->getFilename();
                    rawstr << SP->getFilename() << ":" << SP->getLine();
                }
            }    
        #endif
        }
    }
    return rawstr.str();
}


/*!
 * Get the meta data (line number and file name) info of a LLVM value
 */
std::string getSourceLoc(const Value *val)
{
    if (val == NULL)
        return "empty val";

    std::string str;
    raw_string_ostream rawstr(str);
    if (const Instruction *inst = dyn_cast<Instruction>(val)) {
        if (isa<AllocaInst>(inst)) {
#if LLVM_VERSION_MAJOR <= 5 /* LLVM 4.0, 5.0*/
            DbgDeclareInst *DDI = llvm::FindAllocaDbgDeclare(const_cast<Instruction *>(inst));
            if (DDI) {
                DIVariable *DIVar = cast<DIVariable>(DDI->getVariable());
#if LLVM_VERSION_MAJOR <= 3
                rawstr << DIVar->getLineNumber();
#else
                rawstr << DIVar->getLine();
#endif
            }
#else /* LLVM 6.0+ , LLVM 12.0 */
            for (DbgInfoIntrinsic *DII : FindDbgAddrUses(const_cast<Instruction *>(inst))) {
                if (DbgDeclareInst *DDI = dyn_cast<DbgDeclareInst>(DII)) {
                    DIVariable *DIVar = cast<DIVariable>(DDI->getVariable());
                    rawstr << DIVar->getLine();
                    break;
                }
            }
#endif
        } else if (MDNode *N = inst->getMetadata("dbg")) {  // Here I is an LLVM instruction
#if LLVM_VERSION_MAJOR <= 3
            DILocation Loc(N);
            unsigned Line = Loc.getLineNumber();
            StringRef File = Loc.getFilename();
#else
            DILocation *Loc = cast<DILocation>(N);  // DILocation is in DebugInfo.h
            unsigned Line = Loc->getLine();
            StringRef File = Loc->getFilename();
#endif
            rawstr << File << ":" << Line;
        }
    } else if (const Argument* argument = dyn_cast<Argument>(val)) {
        if (argument->getArgNo()%10 == 1)
            rawstr << argument->getArgNo() << "st";
        else if (argument->getArgNo()%10 == 2)
            rawstr << argument->getArgNo() << "nd";
        else if (argument->getArgNo()%10 == 3)
            rawstr << argument->getArgNo() << "rd";
        else
            rawstr << argument->getArgNo() << "th";
        rawstr << " arg " << argument->getParent()->getName() << " "
               << getSourceLocOfFunction(argument->getParent());
    }
    else if (const GlobalVariable* gvar = dyn_cast<GlobalVariable>(val)) {
        rawstr << "Glob ";
        NamedMDNode* CU_Nodes = gvar->getParent()->getNamedMetadata("llvm.dbg.cu");
        if(CU_Nodes) {
            for (unsigned i = 0, e = CU_Nodes->getNumOperands(); i != e; ++i) {
			#if LLVM_VERSION_MAJOR < 4 /* LLVM 3.6.2 */
                DICompileUnit CUNode(CU_Nodes->getOperand(i));
                DIArray GVs = CUNode.getGlobalVariables();
                for (unsigned i = 0, e = GVs.getNumElements(); i != e; ++i) {
                    DIGlobalVariable GV(GVs.getElement(i));
                }
            #else
                DICompileUnit *CUNode = cast<DICompileUnit>(CU_Nodes->getOperand(i));
                for (DIGlobalVariableExpression *GV : CUNode->getGlobalVariables()) {
                    DIGlobalVariable * DGV = GV->getVariable();
                }
            #endif
            }
        }
    }
    else if (const Function* func = dyn_cast<Function>(val)) {
        rawstr << getSourceLocOfFunction(func);
    }
    else {
        rawstr << "Can only get source location for instruction, argument, global var or function.";
    }
    return rawstr.str();
}


llvm::Instruction *getPrevLLVMInstruction(llvm::Instruction *inst)
{
#if LLVM_VERSION_MAJOR <= 7 && LLVM_VERSION_MAJOR >= 4
    return inst->getPrevNode();
#elif LLVM_VERSION_MAJOR > 7
    return inst->getPrevNonDebugInstruction();
#else
    return NULL;  // TODO: ERR in LLVM 3.6.2
#endif
}


llvm::Instruction *getNextLLVMInstruction(llvm::Instruction *inst)
{
#if LLVM_VERSION_MAJOR <= 7
    return inst->getNextNode();
#else
    return inst->getNextNonDebugInstruction();
#endif
}


std::string getAllSubLoop_inner(Loop *L, int* loopcounter)
{
    ++(*loopcounter);

    std::string str;
    raw_string_ostream rawstr(str);
    
    for (Loop *SL : L->getSubLoops()) {
        rawstr << getAllSubLoop_inner(SL, loopcounter) << ",";
    }
    
    rawstr << L->getStartLoc()->getLine();
    return rawstr.str();
}


std::string getAllSubLoop(Loop *L, int* loopcounter)
{
    ++(*loopcounter);

    std::string str;
    raw_string_ostream rawstr(str);
    
    for (Loop *SL : L->getSubLoops()) {
        rawstr << getAllSubLoop_inner(SL, loopcounter) << ",";
    }
    
    rawstr << "@" << L->getStartLoc()->getLine();
    return rawstr.str();
}


std::string getLoopLoc(llvm::FunctionAnalysisManager *FAM, llvm::Function *Fptr) 
{
    std::string str;
    raw_string_ostream rawstr(str);

    llvm::LoopInfo &LI = (*FAM).getResult<llvm::LoopAnalysis>(*Fptr);
    int loopcounter = 0;
    int tmp = 0;
    // reverse order
    for (LoopInfo::iterator LIT = LI.begin(), LEND = LI.end(); LIT != LEND; ) {
        if (tmp != 0) {
            rawstr << ",";
        }
        rawstr << getAllSubLoop(*(--LEND), &loopcounter);
        tmp++;
    }
    
    if (loopcounter == 0)
        return "0";
    else
        return rawstr.str();
}


void SeekingCallee2(Function* func, std::map<Function*, bool> *functionDumpMapPtr){ //Seeking Callee
    bool canSeekCallee = false;
    bool AllCalleeMark = true;
    for (Function::iterator iter = func->begin(); iter != func->end(); ++iter){
        // 遍历基本块中的每条指令
        for (BasicBlock::iterator Biter = iter->begin(); Biter != iter->end(); ++Biter){
            Instruction *I = &*Biter;            
            //使用dyn_cast函数来判断指令是callInst还是invokeInst,当是这两个指令的时候，解析这两个指令，通过getCalledFunction()函数来获得所调用的函数，
            if (CallInst *inst = dyn_cast<CallInst>(I)){
                Function* called = inst->getCalledFunction();
                if ((*functionDumpMapPtr).count(called)) {
                    canSeekCallee = true;
                    if ((*functionDumpMapPtr)[called] == false) {
                        AllCalleeMark = false;
                    }
                    outs() << called->getName() << "__" << (*functionDumpMapPtr)[called] << "##\n";
                }
            }		
        }	
    }
    if (canSeekCallee == false) {
        (*functionDumpMapPtr)[func] = true;
        return;
    } else if (AllCalleeMark == true) {
        (*functionDumpMapPtr)[func] = true;
        return;
    }

}


void SeekingCallee(Function* func, std::map<Function*, bool> *functionDumpMapPtr, Graph *callgraph){ //Seeking Callee
    bool canSeekCallee = false;
    bool AllCalleeMark = true;
    
    // Build Call Graph
    vector<Value *> tmpVec = callgraph->getCallee(func);

    // Empty Callee || All Callee are already marked
    for (auto const calleeNodeId : tmpVec) {
        if (functionDumpMapPtr->count(callgraph->getFunctionByNodeValue(calleeNodeId))) {
            canSeekCallee = true;
            if ((*functionDumpMapPtr)[callgraph->getFunctionByNodeValue(calleeNodeId)] == false && callgraph->getFunctionByNodeValue(calleeNodeId) != func) {
                AllCalleeMark = false;
            }
            //outs() << "@@@ ^^^^^^^^^^^ " << callgraph->getFunctionByNodeValue(calleeNodeId)->getName() << " ^^^^^^^^^^^ @@@\n";
        }
    }

    if (canSeekCallee == false) {
        (*functionDumpMapPtr)[func] = true;
        return;
    } else if (AllCalleeMark == true) {
        (*functionDumpMapPtr)[func] = true;
        return;
    }

}


// wcventure: the start of veri-llvm-pass
// -------------------------------------------------------------------------------------- Main Functions
#if LLVM_VERSION_MAJOR >= 13  // 11			/* use new pass manager */
PreservedAnalyses CallGraphPass::run(llvm::Module &M, ModuleAnalysisManager &MAM)
{
#else
bool CallGraphPass::runOnModule(llvm::Module &M)
{
#endif
#if LLVM_VERSION_MAJOR >= 13  // 11		/* use new pass manager */
    auto PA = PreservedAnalyses::all();
#endif

    // Build Call Graph
    for (Function &Func : M) {

        callgraph->addNode(&Func);

        for (BasicBlock &BB : Func) {
            for (Instruction &Ins : BB) {

                if (isa<StoreInst>(Ins)) {
                    StoreInst *storeInst = dyn_cast<StoreInst>(&Ins);

                    Value *to = storeInst->getValueOperand()->stripPointerCasts();

                    Value *from = storeInst->getPointerOperand()->stripPointerCasts();
                    // Add Points-To
                    pointerAnalysis->pointsTo(from, to);
                    // Add to Worklist
                    pointerAnalysis->addToWorkList(&Ins);
                    continue;
                }
                if (isa<LoadInst>(Ins)) {
                    LoadInst *loadInst = dyn_cast<LoadInst>(&Ins);

                    Value *to = loadInst->getPointerOperand()->stripPointerCasts();
                    Value *from = dyn_cast<Value>(loadInst);

                    // Add Points-To
                    pointerAnalysis->pointsTo(from, to);
                    // Add to Worklist
                    pointerAnalysis->addToWorkList(&Ins);
                    continue;
                }

                else if (isa<CallBase>(Ins)) {
                    CallBase *callBase = dyn_cast<CallBase>(&Ins);

                    if (!callBase) {
                      // Maybe Indirect Call
                      pointerAnalysis->addToWorkList(&Ins);
                      continue;
                    }

                    // errs()<<*callInst;
                    if (callBase->isIndirectCall()) {

                      pointerAnalysis->addToWorkList(&Ins);
                      continue;
                    }

                    // Direct Call
                    Function *calleeFunc = callBase->getCalledFunction();
                    if(calleeFunc->isIntrinsic()) continue; // Ignored Function calls inserted by LLVM
                    callgraph->addNode(calleeFunc);
                    callgraph->addEdge(&Func, calleeFunc);
                }
            }
        }
    }


    // resolve Pointers and modify the callgraph
    pointerAnalysis->processWorkList(callgraph); 


    // 写文件
    ofstream ofs;                       //定义流对象
    ofs.open("SpecLoC.txt", ios::out);  //以写的方式打开文件
    if(!ofs.is_open())					        //判断是否打开成功
    {
        cout << "open SpecLoC.txt failed" << endl;
    #if LLVM_VERSION_MAJOR >= 13        // 11 /* use new pass manager */
        return PA;
    #else
        return true;
    #endif
    }
    
    llvm::PassBuilder pb;
    llvm::FunctionAnalysisManager FAM;
    pb.registerFunctionAnalyses(FAM);

    //CallGraph &CG = Pass::getAnalysis<CallGraphWrapperPass>().getCallGraph();   //获取Call graph
    std::map<Function*, bool> functionDumpMap; // Function导出的标记
    
    // -------------------------------------------------------------------------

    for (llvm::Module::iterator function = M.begin(), FEnd = M.end(); function != FEnd; function++) {  // 遍历每一个Function
        if (function->isDeclaration() || function->size() == 0) {
            continue;
        }

        Function* Fptr = &*function;
        if (functionDumpMap.find(Fptr) == functionDumpMap.end()) {
                functionDumpMap[Fptr] = false;
        }
    }

    //不动点
    while(1) {
        unsigned int count_in_this_round = 0;
        //遍历Map，并输出Map
        std::map<Function*, bool>::iterator Fiter;
        for(Fiter = functionDumpMap.begin(); Fiter != functionDumpMap.end(); Fiter++)
        {
            if (Fiter->second == false) {
                SeekingCallee(Fiter->first, &functionDumpMap, callgraph); // SeekingCallee2(Fiter->first, &functionDumpMap);
                //outs() << Fiter->first->getName() << " " << Fiter->second << "\n";
                
                if (Fiter->second) {
                    Function *Fptr = Fiter->first;
                    // 写入SpecLoC.txt
                    ofs << Fptr->getName().str() 
                        << "===" << getSourceLoc(Fptr) 
                        << "===" << getLoopLoc(&FAM, Fptr) << "\n";
                    // 屏幕输出
                    outs() << Fptr->getName().str() 
                        << "===" << getSourceLoc(Fptr) 
                        << "===" << getLoopLoc(&FAM, Fptr) << "\n";
                }

                count_in_this_round++;
            }
        }
        if (count_in_this_round == 0) {
            break;
        }
    }
    
    // -------------------------------------------------------------------------\

    ofs.close();

#if LLVM_VERSION_MAJOR >= 13  // 11			/* use new pass manager */
    return PA;
#else
    return true;
#endif
}


//char CallGraphPass::ID = 0;

static RegisterPass<CallGraphPass> X("callgraph", "CallGraph Generation");

static void registerPass(const PassManagerBuilder &,
                         legacy::PassManagerBase &PM) {
  PM.add(new CallGraphPass());
}
static RegisterStandardPasses
    RegisterMyPass(PassManagerBuilder::EP_OptimizerLast, registerPass);

static RegisterStandardPasses
    RegisterMyPass0(PassManagerBuilder::EP_EnabledOnOptLevel0, registerPass);

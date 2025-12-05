/*
@Author: Bernard Nongpoh
@Email: bernard.nongpoh@gmail.com
*/

#include "Graph.h"

void Graph::addEdge(Value *src, Value *dest) {
    if (!isEdgeExist(src, dest))
        adjMap[src].push_back(dest);
}


bool Graph::isEdgeExist(Value *src, Value *desc) {
    for (auto e : adjMap[src]) {
        if (e == desc)
            return true;
    }
    return false;
}


void Graph::addNode(llvm::Function *func) {
    idToFuncMap[func] = func;
}


llvm::Function *Graph::getFunctionByNodeValue(Value *value) {
    return idToFuncMap[value];
}


map<Value *, llvm::Function *> Graph::getValueToFuncMap(){
    return idToFuncMap;
}


vector<Value *> Graph::getCallee(llvm::Function *funcPtr) {
    vector<Value *> tmpVec;
    for (auto const calleeNodeId : adjMap[funcPtr]) {
        tmpVec.push_back(getFunctionByNodeValue(calleeNodeId));  
    }
    return tmpVec;
}


void Graph::printGraph() {

    std::string graphFileName = "graph.text";
    std::string graphFileNameDot = "graph.dot";
    std::ofstream graphFile, graphDot;
    graphFile.open(graphFileName);
    graphDot.open(graphFileNameDot);
    graphDot << "digraph G {"
            << "\n";

    for (auto const &node : adjMap) {
        graphFile << "[" << getFunctionByNodeValue(node.first)->getName().str()
                  << "]:";

        unsigned int count = 0;
        for (auto const calleeNodeId : node.second) {

            graphDot << getFunctionByNodeValue(node.first)->getName().str() << "->"
                    << getFunctionByNodeValue(calleeNodeId)->getName().str()
                    << ";\n";
            // Formatting Comma only
            if (count != node.second.size() - 1) {
                graphFile << "["
                          << getFunctionByNodeValue(calleeNodeId)->getName().str()
                          << "],";

            } else {
                graphFile << "["
                          << getFunctionByNodeValue(calleeNodeId)->getName().str()
                          << "]";
            }
            count++;
        }
        graphFile << "\n";
    }

    graphDot << "}";

    graphFile.close();
    graphDot.close();
    displayBanner();
}


void Graph::displayBanner(){
    errs()<<"Graphical Graph: xdot graph.dot\nText Format: gedit graph.txt\n";

}

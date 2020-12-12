import os
import sys
import re

e_arrays = re.compile(r"new\s+(const)?\s*([a-zA-Z_][_a-zA-Z0-9]+)\s*(\[.+\])+\s*=\s*([\s\S]*?)\s*;")
e_arg = re.compile(r"(?P<isConst>const)?\s*(?P<name>[_a-zA-Z0-9]+)(?P<isArray>\[\])?")
e_func = re.compile(r"^([_a-zA-Z][_a-zA-Z0-9]+)\((.*)\)\s*{",flags=re.MULTILINE)
e_case = re.compile(r"case\s*(\d.*)*\:")
e_switches = re.compile(r"case")

def scanBasicReplacement(lines):
    linesRes = re.sub(r'#.*$', '', lines,flags=re.MULTILINE)
    linesRes = re.sub(r'forward\s+|native\s+|public\s+', '', linesRes,flags=re.MULTILINE)
    linesRes = re.sub(r"bool\:", "bool ", linesRes, flags=re.MULTILINE)
    linesRes = re.sub(r"]\s*=\s*0\s*;", "]={0};", linesRes, flags=re.MULTILINE)
    return linesRes

def scanCase(lines):
    do = True
    prevSymbol = 0
    endSymbol = len(lines)
    resultLines = ""
    while(do):        
        #pdb.set_trace()
        match = e_case.search(lines,prevSymbol)
        if ((match is None) == True):
            break
        resultLines += lines[prevSymbol:match.span()[0]] #add previous block of code
        prevSymbol = match.span()[1]        
        #if (prevSymbol == len(lines)):
        #    break
        numberStr = match.groups()[0]
        numbers = numberStr.split(",")
        for number in numbers:
            resultLines += "case "
            resultLines += number.strip()
            resultLines += ":" 
    if (len(lines) - 1 != endSymbol):
        resultLines += lines[prevSymbol:len(lines)]
    return resultLines

def newArray(isPorted,parsed):
    resultLines = ""
    def doSize(sizeStr):
        unparsed = list(sizeStr)
        parsed = [x for x in unparsed if x != " "]
        return "".join(parsed)
    def doInit(initStr):
        unparsed = list(initStr)      
        parsed = []
        for symbol in unparsed:
            if (symbol == "["):
                parsed.append("{")
            elif (symbol == "]"):
                parsed.append("}")
            else:
                parsed.append(symbol)
        return "".join(parsed)
    if isPorted == False:
        resultLines += "new" + " "
        resultLines += (parsed["const"] + " ") if not (parsed["const"] is None) else ""
        resultLines += parsed["name"] + doSize(parsed["size"]) + " = " + parsed["initializer"] + ";\n"
    else:
        resultLines += "cell" + " " + parsed["name"] + doSize(parsed["size"]) + " = " + doInit(parsed["initializer"]) + ";"        
    return resultLines
    
def scanArray(lines):
    do = True
    prevSymbol = 0
    endSymbol = len(lines)
    resultLines = ""
    while(do):
        match = e_arrays.search(lines,prevSymbol)
        if ((match is None) == True):
            break
        resultLines += lines[prevSymbol:match.span()[0]] #add previous block of code
        prevSymbol = match.span()[1]        
        if (prevSymbol == len(lines)):
            break
        parsed = {}
        parsed["const"], parsed["name"], parsed["size"],parsed["initializer"] = match.groups()   
        resultLines += newArray(isPorted=True,parsed=parsed)
    if (len(lines) - 1 != endSymbol):
        resultLines += lines[prevSymbol:len(lines) - 1]
    return resultLines

def newFunction(isPorted,parsed):
    splitted = []
    if not (parsed["parameters"] is None):
        splitted = parsed["parameters"].split(",")
    else:
        splitted = []
    resultLines = ""
    def doArg(isPorted, argStr):
        if not argStr is None:
            argStr = argStr.strip()
        match = e_arg.search(argStr)
        if match is None:
            return ""
        isConst = match.group("isConst")
        if isConst is None:
            isConst = False
        else:
            isConst = True
        name = match.group("name")
        isArray = match.group("isArray")
        if isArray is None:
            isArray = False
        else:
            isArray = True
        resultLine = ""
        if (isPorted == False):
            if isConst:
                resultLine += "const" + " "
            if (isArray == False):
                resultLine += name
            else:
                resultLine += name + "[]"
        else:
            if (isArray == False):
                resultLine += "cell" + " "
            else:
                resultLine += "cell*" + " "
            resultLine += name
        return resultLine    
    funcProto = ""
    first = True
    if isPorted == True:
        funcProto += "cell" + " "
    funcProto += parsed["name"] + "("
    for arg in splitted:
        if not (arg is None):
            if first == False:
                funcProto += "," + " "
            else:
                first = False
            funcProto += doArg(isPorted = isPorted,argStr = arg)            
    resultLines += funcProto + ")" + "\n" + "{"
    funcProto += ")" + ";" + "\n"
    return funcProto,resultLines

def scanFunctions(lines, isPorted = False):
    do = True
    prevSymbol = 0
    endSymbol = len(lines)
    resultLines = ""
    resultProto = ""
    while(do):
        match = e_func.search(lines,prevSymbol)
        if ((match is None) == True):
            break
        resultLines += lines[prevSymbol:match.span()[0]] #add previous block of code
        prevSymbol = match.span()[1]        
        if (prevSymbol == len(lines)):
            break
        parsed = {}
        parsed["name"], parsed["parameters"] = match.groups()
        proto, func = newFunction(isPorted=isPorted,parsed=parsed)
        resultLines += func
        resultProto += proto
      
    #pdb.set_trace()
    if (len(lines) - 1 != endSymbol):
        resultLines += lines[prevSymbol:len(lines)]
    return resultProto, resultLines

def ScanSwitches(lines):
    do = True
    prevSymbol = 0
    endSymbol = len(lines)
    resultLines = ""
    while(do):
        match = e_switches.search(lines,prevSymbol)
        if ((match is None) == True):
            break
        resultLines += lines[prevSymbol:match.span()[0]] #add previous block of code
        prevSymbol = match.span()[1]        
        if (prevSymbol == len(lines)):
            break
        resultLines += "break;case"
    if (len(lines) - 1 != endSymbol):
        resultLines += lines[prevSymbol:len(lines)]
    return resultLines

def MakeSource(lines,isPorted):
    #pdb.set_trace()
    resSource = scanBasicReplacement(lines)
    resSource = scanArray(resSource)
      
    #pdb.set_trace()
    resSource = ScanSwitches(resSource)
    resSource = scanCase(resSource)
    resHeader = ""
    resHeader += "typedef int cell;\n"
    resHeader += "#define new signed\n"
    resHeader += "#define bool int\n"
    resHeader += "#define false 0\n"
    resHeader += "#define true 1\n"
    resHeader += "typedef int stock;\n"  
    resHeaderTmp, resTmp = scanFunctions(resSource,True)
    resSource = resTmp    
    resHeader += resHeaderTmp
    return resHeader, resSource

def CreateFile(fileName):
    if os.name == 'nt':
        os.system("pawncc.exe " + fileName + " -l")
    else:
        os.system("./pawncc " + fileName + " -l")

    basicFileName = re.sub(r"\.pwn|\.lst", "",fileName)
    lines = open(basicFileName + ".lst").read()
    basicFileName = basicFileName + "_ported"
    header, ported = MakeSource(lines,True)
    headerFile = open(basicFileName + ".h", "w")
    headerFile.write(header)
    headerFile.close()
    portedFile = open(basicFileName + ".c", "w")
    portedFile.write("#include \"" + basicFileName + ".h" + "\"\n")
    portedFile.write(ported)
    portedFile.close()

if __name__ == "__main__":
    CreateFile(sys.argv[1])
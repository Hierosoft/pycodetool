# 
# * Created by SharpDevelop.
# * User: jgustafson
# * Date: 3/25/2015
# * Time: 9:02 AM
# * see python version in ../../d.pygame/ via www.developerfusion.com/tools/convert/csharp-to-python
# * To change this template use Tools | Options | Coding | Edit Standard Headers.
# 

# as converted from C# by SharpDevelop 3.0, SharpDevelop 5.1, or http://codeconverter.sharpdevelop.net/SnippetConverter.aspx

from System import *
from System.Collections import *
from System.IO import *
from System.Linq import * #Enumerable etc
#   public class YAMLLineInfo {
#       public const int TYPE_NOLINE=0;
#       public const int TYPE_OBJECTNAME=1;
#       public const int TYPE_ARRAYNAME=2;
#       public const int TYPE_ARRAYVALUE=3;
#       public const int TYPE_VARIABLE=4;
#       public int lineType=0;
#       public int lineIndex=-1;//for debugging only--line of file
#   }
class YAMLObject(object):
    """ <summary>
     YAMLObject. The first YAMLObject object is the root (one where you call load).
     Other YAMLObject can be either:
     * Root is the yaml object from which you called load--normally, use this object to get values: such as myrootyamlobject.getArrayValues("groups.Owner.inheritance") or myrootyamlobject.getValue("groups.SuperAdmin.default").
     * Object is stored in file like: name, colon, newline, additional indent, object/array/variable
     * Array is stored in file like: name, colon, newline, no additional indent, hyphen, space, value
     * Variable is stored in file like: name, colon, value (next line should have less or equal indent)
     </summary>
    """
    # <summary>
    # line from source file--for debugging only
    # </summary>
    def __init__(self, name, val, Parent):
        self._Name = None
        self._Value = None
        self._arrayValues = None
        self._namedSubObjects = None
        self._depthCount = 0
        self._indentCount = 0
        self._whitespaceCount = 0
        self._whitespaceString = ""
        self._lineIndex = -1
        self._parent = None
        self._thisYAMLSyntaxErrors = None
        self._IsVerbose = False
        self._indentDefaultString = "  "
        #       public YAMLObject(string val)
        #       {
        #           Value=val;
        #       }
        self._Name = name
        self._Value = val
        self._parent = Parent

    def __init__(self, name, val, Parent):
        self._Name = None
        self._Value = None
        self._arrayValues = None
        self._namedSubObjects = None
        self._depthCount = 0
        self._indentCount = 0
        self._whitespaceCount = 0
        self._whitespaceString = ""
        self._lineIndex = -1
        self._parent = None
        self._thisYAMLSyntaxErrors = None
        self._IsVerbose = False
        self._indentDefaultString = "  "
        self._Name = name
        self._Value = val
        self._parent = Parent

    def __init__(self, name, val, Parent):
        self._Name = None
        self._Value = None
        self._arrayValues = None
        self._namedSubObjects = None
        self._depthCount = 0
        self._indentCount = 0
        self._whitespaceCount = 0
        self._whitespaceString = ""
        self._lineIndex = -1
        self._parent = None
        self._thisYAMLSyntaxErrors = None
        self._IsVerbose = False
        self._indentDefaultString = "  "
        self._Name = name
        self._Value = val
        self._parent = Parent

    def getFullName(self):
        return self.getFullNameRecursive_DontCallMeDirectly(self._Name)

    def getFullNameRecursive_DontCallMeDirectly(self, child):
        if self.isRoot():
            return child
        else:
            return self._parent.getFullNameRecursive_DontCallMeDirectly(self._Name + "." + child)

    def setValue(self, name, new_value):
        """ <summary>
         This should always be called using the root YAMLObject (the one from which you loaded a YAML file).
         Sub-objects should be accessed using dot notation.
         </summary>
         <param name="Name">object name (must be in dot notation if indented more, such as groups.Administrator.default)</param>
         <returns></returns>
        """
        if name != None:
            if name.Length > 0:
                foundObject = self.getObject(name)
                if foundObject == None:
                    self.createObject(name)
                    foundObject = self.getObject(name)
                if foundObject != None:
                    foundObject.Value = new_value
                else:
                    Console.Error.WriteLine("setValue error: setValue could neither find nor create an object (this should never happen) {name:\"" + name.Replace("\"", "\\\"") + "\"}.")
            else:
                Console.Error.WriteLine("Programmer error: setValue cannot do anything since name is empty (0-length).")
        else:
            Console.Error.WriteLine("Programmer error: setValue cannot do anything since name is null")

    def getObject(self, name):
        foundObject = None
        if name != None:
            if name.Length > 0:
                dotIndex = -1
                nameSub = None
                if dotIndex >= 0:
                    nameSub = name.Substring(dotIndex + 1).Trim()
                    name = name.Substring(0, dotIndex).Trim()
                enumerator = namedSubObjects.GetEnumerator()
                while enumerator.MoveNext():
                    thisObject = enumerator.Current
                    if thisObject.Name == name:
                        if nameSub != None:
                            foundObject = thisObject.getObject(nameSub)
                        else:
                            foundObject = thisObject
                        break
            else:
                Console.Error.WriteLine("Programmer error: getObject cannot do anything since name is empty (0-length).")
        else:
            Console.Error.WriteLine("Programmer error: getObject cannot do anything since name is null.")
        return foundObject
 #end getObject
    def createObject(self, name):
        dotIndex = -1
        nameSub = None
        if name != None:
            name = name.Trim()
            dotIndex = name.IndexOf(".")
            if dotIndex >= 0:
                nameSub = name.Substring(dotIndex + 1).Trim()
                name = name.Substring(0, dotIndex).Trim()
            if name.Length > 0:
                newObject = None
                newObject = self.getObject(name)
                if newObject == None:
                    newObject = YAMLObject(name, None, self)
                    self._namedSubObjects.Add(newObject)
                if nameSub != None:
                    newObject.createObject(nameSub)
            else:
                Console.Error.WriteLine("Programmer error: createObject cannot do anything since name is empty (0-length) string.")
        else:
            Console.Error.WriteLine("Programmer error: createObject cannot do anything since name is null.")

    def addArrayValue(self, val):
        if self._arrayValues == None:
            self._arrayValues = ArrayList()
        if val != None:
            self._arrayValues.Add(YAMLObject(None, val))
        else:
            Console.Error.WriteLine("WARNING: addArrayValue skipped null value.")

    def isArray(self):
        return self._arrayValues != None

    def getSubValue(self, name):
        """ <summary>
         
         </summary>
         <param name="name">full variable name (with dot notation if necessary)</param>
         <returns></returns>
        """
        foundValue = None
        if name != None:
            if name.Length > 0:
                foundObject = self.getObject(name)
                if foundObject != None:
                    foundValue = foundObject.Value
                else:
                    Console.Error.WriteLine("Programmer error: createObject cannot get value since object does not exist {name:\"" + name.Replace("\"", "\\\"") + "\"}.")
            else:
                Console.Error.WriteLine("Programmer error: createObject cannot do anything since name is empty (0-length) string.")
        else:
            Console.Error.WriteLine("Programmer error: createObject cannot do anything since name is null.")
        return foundValue

    def getValue(self):
        val = None
        if self._arrayValues == None:
            val = self._Value
        return val

    def getSubTrees(self):
        thisAL = None
        if self._namedSubObjects != None:
            thisAL = ArrayList()
            enumerator = namedSubObjects.GetEnumerator()
            while enumerator.MoveNext():
                thisYT = enumerator.Current
                thisAL.Add(thisYT)
        return thisAL

    def getArrayValues(self):
        thisAL = None
        if self._arrayValues != None:
            thisAL = ArrayList()
            enumerator = arrayValues.GetEnumerator()
            while enumerator.MoveNext():
                thisValue = enumerator.Current
                thisAL.Add(thisValue)
        return thisAL

    def addSub(self, addObject):
        if self._namedSubObjects == None:
            self._namedSubObjects = ArrayList()
        self._namedSubObjects.Add(addObject)

    def isLeaf(self):
        return not self.isRoot() and self._namedSubObjects == None

    def isRoot(self):
        return self._parent == None

    #       public void loadLine(string original_line, ref int currentFileLineIndex) {
    #           
    #       }
    def getLines(fileName):
        thisAL = None
        inStream = None
        original_line = None
        try:
            inStream = StreamReader(fileName)
            thisAL = ArrayList()
            while (original_line = inStream.ReadLine()) != None:
                thisAL.Add(original_line)
            inStream.Close()
            inStream = None
        except Exception, e:
            Console.Error.WriteLine("Could not finish YAMLObject static getLines: " + e.ToString())
            if inStream != None:
                try:
                    inStream.Close()
                    inStream = None
                except , :
                finally:
        finally: #don't care
        return thisAL

    getLines = staticmethod(getLines)

    def deqErrorsInYAMLSyntax(self):
        thisAL = self._thisYAMLSyntaxErrors
        self._thisYAMLSyntaxErrors = ArrayList()
        return thisAL

    def getAncestorWithIndent(self, theoreticalWhitespaceCount, lineOfSibling_ForSyntaxCheckingMessage):
        ancestor = None
        if self._whitespaceCount == theoreticalWhitespaceCount:
            ancestor = self
            self.addVerboseSyntaxMessage("...this (" + self.getDebugNounString() + ") is ancestor since has whitespace count " + self._whitespaceCount.ToString())
        else:
            if self._parent != None:
                IsCircularReference = False
                if self._parent.parent != None:
                    if self._parent.parent == self:
                        IsCircularReference = True
                        msg = "YAML syntax error on line " + (lineOfSibling_ForSyntaxCheckingMessage + 1).ToString() + ": circular reference (parent of object on line " + (self._lineIndex + 1).ToString() + "'s parent is said object)."
                        self._thisYAMLSyntaxErrors.Add(msg)
                        Console.Error.WriteLine(msg)
                if not IsCircularReference:
                    ancestor = self._parent.getAncestorWithIndent(theoreticalWhitespaceCount, lineOfSibling_ForSyntaxCheckingMessage)
            else:
                msg = "YAML syntax error on line " + (lineOfSibling_ForSyntaxCheckingMessage + 1).ToString() + ": unexpected indent (there is no previous line with this indentation level, yet it is further back than a previous line indicating it should have a sibling)."
                self._thisYAMLSyntaxErrors.Add(msg)
                Console.Error.WriteLine(msg)
        return ancestor
 #end getAncestorWithIndent
    def addVerboseSyntaxMessage(msg):
        if self._IsVerbose:
            if msg != None:
                msg = "#Verbose message: " + msg
                if self._thisYAMLSyntaxErrors != None:
                    self._thisYAMLSyntaxErrors.Add(msg)
                Console.WriteLine(msg)

    addVerboseSyntaxMessage = staticmethod(addVerboseSyntaxMessage)

    def getArrayValueCount(self):
        count = 0
        if self._arrayValues != None:
            count = self._arrayValues.Count
        return count

    def getYAMLObject(lines, currentFileLineIndex, rootObject, prevLineYAMLObject):
        """ <summary>
         Parses a line and gets the yaml object, setting the parent properly.
         </summary>
         <param name="lines"></param>
         <param name="currentFileLineIndex"></param>
         <param name="prevWhitespaceCount"></param>
         <param name="rootObject"></param>
         <param name="prevLineYAMLObject"></param>
         <returns>A new YAML Object EXCEPT when an array element, then returns prevLineYAMLObject</returns>
        """
        #YAMLObject nextLineParentYAMLObject=null;
        newObject = None
        try:
            if lines != None:
                prevWhitespaceCount = 0
                if prevLineYAMLObject != None:
                    prevWhitespaceCount = prevLineYAMLObject.whitespaceCount
                original_line = lines[currentFileLineIndex]
                line_TrimStart = original_line.TrimStart()
                line_Trim = original_line.Trim()
                if line_Trim.Length > 0:
                    line_whitespaceCount = original_line.Length - line_TrimStart.Length
                    #thisWhitespace=original_line.Substring(0,
                    #if (whitespaceCount==prevWhitespaceCount) {
                    if line_Trim.StartsWith("- "): #this line is part of an array
                        IsSyntaxErrorShown = False
                        if prevLineYAMLObject != None:
                            newObject = prevLineYAMLObject
                            prevLineYAMLObject.addArrayValue(line_Trim.Substring(2).Trim()) #do it regardless for fault tolerance
                            YAMLObject.addVerboseSyntaxMessage("line " + (currentFileLineIndex + 1).ToString() + "...array value at index [" + (prevLineYAMLObject.getArrayValueCount() - 1).ToString() + "]...")
                        else:
                            newObject = rootObject
                            rootObject.addArrayValue(line_Trim.Substring(2).Trim())
                            #string msg="YAML syntax error on line "+(currentFileLineIndex+1).ToString()+": array element was found without a name at same indent level on a previous line, so the value was added to the variable on line "+(newObject.lineIndex+1).ToString()+".";
                            msg = "YAML syntax error on line " + (currentFileLineIndex + 1).ToString() + ": array element was found without a name at same indent level on a previous line, so the value was added to the root object to prevent data loss."
                            IsSyntaxErrorShown = True
                            self._thisYAMLSyntaxErrors.Add(msg)
                            Console.Error.WriteLine(msg)
                        if line_whitespaceCount != prevWhitespaceCount:
                            if not IsSyntaxErrorShown:
                                msg = "YAML syntax error on line " + (currentFileLineIndex + 1).ToString() + ": array element should not be indented by " + line_whitespaceCount.ToString() + " characters but was added to the variable above it {line:" + (newObject.lineIndex + 1).ToString() + "} to prevent data loss."
                                self._thisYAMLSyntaxErrors.Add(msg)
                                Console.Error.WriteLine(msg)
                    else: #end if line is an array element #this line is an object, single-value variable, or array name)
                        newObject = YAMLObject()
                        newObject.whitespaceCount = line_whitespaceCount
                        newObject.whitespaceString = original_line.Substring(0, line_whitespaceCount)
                        newObject.lineIndex = currentFileLineIndex
                        if newObject.whitespaceCount == prevWhitespaceCount:
                            newObject.parent = prevLineYAMLObject.parent if (prevLineYAMLObject != None) else rootObject #nextLineParentYAMLObject=prevLineYAMLObject;
                            if newObject.parent != None:
                                newObject.parent.addSub(newObject)
                            YAMLObject.addVerboseSyntaxMessage("line " + (currentFileLineIndex + 1).ToString() + "...same parent as previous line...")
                        elif newObject.whitespaceCount > prevWhitespaceCount:
                            newObject.parent = prevLineYAMLObject
                            if newObject.parent != None:
                                newObject.parent.addSub(newObject)
                            YAMLObject.addVerboseSyntaxMessage("line " + (currentFileLineIndex + 1).ToString() + "...child of previous line...")
                        else: #indented less than previous line
                            if prevLineYAMLObject != None:
                                newObject.parent = prevLineYAMLObject.getAncestorWithIndent(newObject.whitespaceCount - 2, currentFileLineIndex)
                                ancestorLineIndex = -1
                                if newObject.parent != None:
                                    newObject.parent.addSub(newObject)
                                    ancestorLineIndex = newObject.parent.lineIndex
                                    YAMLObject.addVerboseSyntaxMessage("line " + (currentFileLineIndex + 1).ToString() + "...indented less than previous line, so ancestor set to object on line " + (ancestorLineIndex + 1).ToString() + "(" + newObject.parent.getDebugNounString() + ")...")
                                else:
                                    msg = "line " + (currentFileLineIndex + 1).ToString() + ": could not find ancestor via decreasing indent, though this object is a child and should have a parent indented by 2 fewer characters."
                                    self._thisYAMLSyntaxErrors.Add(msg)
                                    Console.Error.WriteLine(msg)
                            else:
                                msg = "YAML parser failure on line " + (currentFileLineIndex + 1).ToString() + ": could not find previous line, though this line is less indented than previous line."
                                self._thisYAMLSyntaxErrors.Add(msg)
                                Console.Error.WriteLine(msg)
                        colonIndex = line_Trim.IndexOf(":")
                        if colonIndex > 0: #indentionally > instead of >= since starting with colon would be YAML syntax error
                            thisName = line_Trim.Substring(0, colonIndex).Trim()
                            thisValue = line_Trim.Substring(colonIndex + 1).Trim()
                            if thisName.Length > 0:
                                newObject.Name = thisName
                                if thisValue.Length > 0: #this line is a variable
                                    newObject.Value = thisValue
                                    YAMLObject.addVerboseSyntaxMessage("line " + (currentFileLineIndex + 1).ToString() + "...OK (variable)")
                                else: #this line is an object or array
                                    #newObject.Name=thisName;
                                    YAMLObject.addVerboseSyntaxMessage("line " + (currentFileLineIndex + 1).ToString() + "...OK (name of object or of array)")
                            else:
                                msg = "YAML syntax error on line " + (currentFileLineIndex + 1).ToString() + ": missing name--got colon instead."
                                self._thisYAMLSyntaxErrors.Add(msg)
                                Console.Error.WriteLine(msg)
                        else:
                            msg = "YAML syntax error on line " + (currentFileLineIndex + 1).ToString() + ": missing colon where new object should start"
                            self._thisYAMLSyntaxErrors.Add(msg)
                            Console.Error.WriteLine(msg)
                else: #end else line is an object or variable
                    #} #end if line_Trim.Length>0
                    newObject = prevLineYAMLObject
        except Exception, e: #end if lines!=null
            #           int currentFileLineIndex=0;
            #           string original_line=null;
            #           while ( (original_line=inStream.ReadLine()) != null ) {
            #               //loadNext(inStream, ref currentFileLineIndex);
            #               //loadLine(original_line, ref currentFileLineIndex);
            #           }
            msg = "YAML parser failure (parser could not finish) on line " + (currentFileLineIndex + 1).ToString() + ": " + e.ToString()
            self._thisYAMLSyntaxErrors.Add(msg)
            Console.Error.WriteLine(msg)
        finally:
        return newObject

    getYAMLObject = staticmethod(getYAMLObject)
 #end loadYAMLObject
    def loadYAMLLines(self, lines):
        if lines != None:
            if self._thisYAMLSyntaxErrors == None:
                self._thisYAMLSyntaxErrors = ArrayList()
            else:
                self._thisYAMLSyntaxErrors.Clear()
            #int prevWhitespaceCount=0;
            #int whitespaceCount=0;
            currentFileLineIndex = 0
            prevObject = None
            #int prevLineType
            while currentFileLineIndex < lines.Length:
                prevObject = self.getYAMLObject(lines, currentFileLineIndex, self, prevObject)
                currentFileLineIndex += 1
 #end loadYAMLLines
    def loadYAML(self, fileName):
        """ <summary>
         Top level is self, but with no name is needed, to allow for multiple variables--for example, if file begins with "groups," this object will have no name but this object's subtree will contain an object named groups, and then you can get the values like: getArrayAsStrings("groups.SuperAdmin.permissions")
         </summary>
         <param name="fileName"></param>
        """
        thisAL = self.getLines(fileName)
        lines = None
        if thisAL != None and thisAL.Count > 0:
            lines = Array.CreateInstance(str, thisAL.Count)
            index = 0
            enumerator = thisAL.GetEnumerator()
            while enumerator.MoveNext():
                line = enumerator.Current
                lines[index] = line
                index += 1
        self.loadYAMLLines(lines)
 #end loadYAML
    def saveYAMLSelf(self, outStream, setIndentCount):
        #string thisIndentString=getMyIndent();
        try:
            myRealIndentString = self.getMyRealIndent()
            if not self.isLeaf():
                subTreeIndentCount = setIndentCount + 1
                if self._parent != None:
                    outStream.WriteLine(myRealIndentString + self._Name + ":")
                else:
                    subTreeIndentCount = 0
                foundSubTreeCount = 0
                if self._namedSubObjects != None:
                    enumerator = namedSubObjects.GetEnumerator()
                    while enumerator.MoveNext():
                        subTree = enumerator.Current
                        subTree.saveYAMLSelf(outStream, subTreeIndentCount)
                        foundSubTreeCount += 1
                else:
                    self.addVerboseSyntaxMessage("namedSubObjects is null though this is not a leaf")
                msg = myRealIndentString + "Saved " + foundSubTreeCount.ToString() + " subtrees for YAMLObject named " + self.ValueToCSharp(self._Name)
                if self._lineIndex >= 0:
                    msg += " that had been loaded from line " + (self._lineIndex + 1).ToString()
                else:
                    msg += " that had been generated (not loaded from a file)"
                self.addVerboseSyntaxMessage(msg)
            elif self.isArray():
                outStream.WriteLine(myRealIndentString + self._Name + ":")
                count = 0
                enumerator = arrayValues.GetEnumerator()
                while enumerator.MoveNext():
                    thisValue = enumerator.Current
                    outStream.WriteLine(myRealIndentString + "- " + thisValue.getValue())
                    count += 1
                self.addVerboseSyntaxMessage(myRealIndentString + "Saved " + count.ToString() + "-length array")
            elif self._Value != None:
                self.addVerboseSyntaxMessage("Saved variable")
                outStream.WriteLine(myRealIndentString + self._Name + ": " + self._Value)
            else:
                msg = "ERROR in saveSelf: null Value (" + self.getDebugNounString() + ")"
                if YAMLObject.thisYAMLSyntaxErrors == None:
                    YAMLObject.thisYAMLSyntaxErrors = ArrayList()
                YAMLObject.thisYAMLSyntaxErrors.Add(msg)
                Console.Error.WriteLine(msg)
        except Exception, e:
            msg = "Could not finish saveYAMLSelf: " + e.ToString()
            Console.Error.WriteLine(msg)
            YAMLObject.thisYAMLSyntaxErrors.Add(msg)
        finally:
 #end saveYAMLSelf
    def getDebugNounString(self):
        """ <summary>
         formerly getDescription
         </summary>
         <returns></returns>
        """
        typeString = "array" if (self._arrayValues != None) else "object"
        lineTypeMessage = ""
        if self._lineIndex >= 0:
            lineTypeMessage += " that had been loaded from line " + (self._lineIndex + 1).ToString()
        else:
            lineTypeMessage += " that had been generated (not loaded from a file)"
        descriptionString = typeString + " named: " + self.ValueToCSharp(self._Name) + lineTypeMessage + "; is" + ("" if self.isLeaf() else " not") + " leaf"
        descriptionString += "; Value:" + self.ValueToCSharp(self._Value)
        descriptionString += "; parent:" + ((".Name:" + self.ValueToCSharp(self._parent.Name)) if (self._parent != None) else "null")
        return descriptionString

    def saveYAML(self, fileName):
        outStream = None
        try:
            outStream = StreamWriter(fileName)
            self.saveYAMLSelf(outStream, 0)
            outStream.Close()
            outStream = None
        except Exception, e:
            msg = "YAMLObject: Could not finish save: " + e.ToString()
            self.addVerboseSyntaxMessage(msg)
            Console.Error.WriteLine(msg)
            if outStream != None:
                try:
                    outStream.Close()
                    outStream = None
                except , :
                finally:
        finally:
 #don't care #end saveYAML
    def getIndent(count):
        val = System.String(self._indentDefaultString[0], count * self._indentDefaultString.Length)
        return val

    getIndent = staticmethod(getIndent)
 #return string.Concat(Enumerable.Repeat(indentDefaultString, count));
    def getMyIndent(self):
        return self.getIndent(self._indentCount)

    def getMyRealIndent(self):
        count = self.getMyRealIndentCount_Recursive(0)
        return self.getIndent(count)

    def getMyRealIndentCount_Recursive(self, i):
        if self._parent != None:
            if not self._parent.isRoot():
                i = self._parent.getMyRealIndentCount_Recursive(i + 1)
        return i

    def ValueToCSharp(val):
        """ <summary>
         Returns the string in quotes, otherwise the word "null" without quotes.
         </summary>
         <param name="val"></param>
         <returns></returns>
        """
        return (("\"" + val + "\"") if val != None else "null")

    ValueToCSharp = staticmethod(ValueToCSharp)

import re

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import filtertypes

SUFFIX = "suffix"
PREFIX = "prefix"

EDIT_INDEX_INSERT = "insert"
EDIT_INDEX_REPLACE = "replace"
EDIT_INDEX_REMOVE = "remove"


# -------------------------
# MAYA NAME
# -------------------------

def convertStringToMayaCompatibleStr(anyNameString):
    """Converts a string to a Maya name, useful when files are imported and given Maya names that don't support spaces.

    :param anyNameString: A string with any letters "the-filename adfaf??yes"
    :type anyNameString: str
    :return mayaCompatibleName: the string with all non alpha numeric letters replaced with _ "the_filename_adfaf__yes"
    :rtype mayaCompatibleName: str
    """
    return "".join([c if c.isalnum() else "_" for c in anyNameString])


# -------------------------
# SAFE RENAME
# -------------------------


def safeRename(objName, newName, uuid=None, renameShape=True, message=False, returnLongName=True):
    """Safe renames objects. Handles long names and if a uuid is supplied use the most current name instead.
    Checks for invalid names, numbers starting a name or locked nodes and will warn user without errors/issues

    Example:

        objName: "|group1|Cube"
        replace: "|group1|aBox" or "aBox"
        result: "|group1|aBox"

    Example with uuid:

        uuid: "B7EABB60-4578-A4D1-73DC-07B9A14F267F"
        replace: "|group1|aBox" or "aBox"
        result: "|group1|aBox"

    If a uuid is given will use that instead of the node name, handy with re-parenting and hierarchies longname lists

    :param objName: The name of the object to be renamed, can be in longname format
    :type objName: str
    :param newName: The new name of the object can be in long format
    :type newName: str
    :param uuid: optional unique hash identifier in case of long name issues while renaming hierarchies or reparenting
    :type uuid: str
    :param renameShape: also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param message: Report the message to the user
    :type message: bool
    :param returnLongName: If True will return a long name of the new name if successfully renamed
    :type returnLongName: bool
    :return newName: The new name of the object now potentially renamed
    :rtype newName: str
    """
    if uuid:  # if uuid then use the most current long name
        objName = cmds.ls(uuid, long=True)[0]
    objShortName = getShortName(objName)  # force short name, does not check Maya, removes >> |
    newShortName = getShortName(newName)
    if objShortName == newShortName:
        return objName
    if cmds.lockNode(objName, query=True)[0]:  # if the node is locked
        if message:
            om2.MGlobal.displayWarning("node {} is locked and cannot be renamed".format(objName))
        return objName

    if newShortName[0].isdigit():  # first letter is a digit which is illegal in Maya
        if message:
            om2.MGlobal.displayWarning("Maya names cannot start with numbers")
        return objName
    if ":" in newShortName:  # test for number as first letter with namespace
        newPureName = newShortName.split(":")[-1]
        if newPureName[0].isdigit():
            if message:
                om2.MGlobal.displayWarning("Maya names cannot start with numbers")
            return objName
    renamedName = cmds.rename(objName, newShortName, ignoreShape=not renameShape)
    if returnLongName:
        return getLongNameFromShort(renamedName)
    return renamedName


def safeRenameList(objList, renameList, uuidList=None, renameShape=True, message=False, returnLongName=True):
    """Safe renames a list of objects. Handles long names and will convert to uuids for safe renaming.
    Checks for invalid names, numbers starting a name or locked nodes and will warn user without errors/issues

    Example of each object in the list:

        objName: "|group1|Cube"
        replace: "|group1|aBox" or "aBox"
        result: "|group1|aBox"

    Example with uuid list:

        uuid: "B7EABB60-4578-A4D1-73DC-07B9A14F267F"
        replace: "|group1|aBox" or "aBox"
        result: "|group1|aBox"

    If a uuid list is given will use that instead of the node name list

    :param objList: The existing objectList to be renamed, can be in longname format
    :type objList: str
    :param renameList: The new name list object names, can be in long format
    :type renameList: str
    :param uuidList: optional unique hash identifier in case of long name issues while renaming hierarchies or reparenting
    :type uuidList: str
    :param renameShape: also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param message: Report the message to the user
    :type message: bool
    :param returnLongName: If True will return a long name of the new name if successfully renamed
    :type returnLongName: bool
    :return newName: The new name of the object now potentially renamed
    :rtype newName: str
    """
    returnedObjList = list()
    if not uuidList:  # Then create a UUID list
        uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):
        returnedObjList.append(
            safeRename(obj, renameList[i], uuid=uuidList[i], renameShape=renameShape, message=message,
                       returnLongName=returnLongName))
    return returnedObjList


# -------------------------
# MAYA PART NAMES (PURE NAMES)
# -------------------------


def mayaNamePartTypes(objName):
    """Breaks up a Maya node name now with the "longName prefix" and "namespace" (if exists) and "pureName"

    Example 1:

        objectName: "pCube1"
        return longPrefix: ""
        return namespace: ""
        return pureName: "pCube1"

    Example 2:

        objectName: "scene4:y:group2|scene4:y:locator2|scene4:x:pCube1"
        return longPrefix: "scene4:y:group2|scene4:y:locator2"
        return namespace: "scene4:x"
        return pureName: "pCube1"

    :param objName: The name of the maya object or node
    :type objName: str
    :return longPrefix: Path of the long name, not including the short name "|group1|x|pcube" is "group1|x"
    :rtype longPrefix: str
    :return namespace: the full namespace, may be multiple "scene1:char1:pCube1" becomes "scene1:char1"
    :rtype namespace: str
    :return pureName: the pure short name with the namespace "group1|scene1:char1:pCube1" becomes "pCube1"
    :rtype pureName: str
    """
    if "|" in objName:  # long name and or namespaces
        objName = str(objName)
        longNameParts = objName.split("|")
        longPrefix = "".join(longNameParts[:-1])
        shortName = longNameParts[-1]
    else:
        shortName = objName
        longPrefix = ""
    if ":" in shortName:  # then namespaces
        namespaceParts = shortName.split(":")
        pureName = namespaceParts[-1]
        namespace = ":".join(namespaceParts[:-1])
    else:
        pureName = shortName
        namespace = ""
    return longPrefix, namespace, pureName


def mayaNamePartsJoin(longPrefix, namespace, pureName):
    """Joins names from 3 potential components, longPrefi and namespace can be None or empty strings

    Example 1 (long names with namespaces):

        longPrefix: "xx:group1|group2"
        namespace: "x:y"
        pureName: "pCube1"
        result: "xx:group1|group2|x:y:pCube1"

    Example 2 (short names):

        longPrefix: ""
        namespace: ""
        pureName: "pCube1"
        result: "pCube1"

    Both longPrefix and namespace can be empty strings or None.

    :param longPrefix: The long name prefix "xx:group1|group2", can be None or ""
    :type longPrefix: str
    :param namespace: The namespace if it exists, can be multiple "x:y", can be None or ""
    :type namespace: str
    :param pureName: The name without longPrefix or namespace "pCube1"
    :type pureName: str
    :return fullName: The joined Maya name "xx:group1|group2|x:y:pCube1"
    :rtype fullName: str
    """
    fullName = pureName
    if namespace:
        fullName = ":".join([namespace, pureName])
    if longPrefix:
        fullName = "|".join([longPrefix, fullName])
    return fullName


# -------------------------
# LONG NAMES
# -------------------------


def getLongNameFromShort(objName):
    """Get the long name from a short name

    :param objName: any dag object name, can be long or short
    :type objName: str
    :return: A dag objects long name with "|" indicating it's hierarchy
    :rtype: str
    """
    return cmds.ls(objName, long=True)[0]


def getLongNameList(objectList):
    """From a mixed longname and shortname list, return all long names

    :param objectList: a list of maya objects/nodes/objectFaces etc
    :type objectList: list
    :return objectList: a list of maya objects/nodes/objectFaces now with longnames
    :rtype objectList: list
    """
    return cmds.ls(objectList, long=True)


# -------------------------
# SHORT NAMES
# -------------------------


def getShortName(longName):
    """Returns the short readable name of a Maya object, pure text function.
    Doesn't check nonUnique or care if the obj exists

    :param longName: Maya object/node long name
    :type longName: str
    :return: The last item separated by a "|" which is the short name of a Maya object
    :rtype: str
    """
    if "|" in longName:
        return longName.split("|")[-1]
    else:
        return longName


def getShortNameList(longNameList):
    """Returns the short names of a Maya object list, pure text function
    Doesn't check Maya for non-unique or care if the obj exists

    :param longNameList: Maya object/node list of long names
    :type longNameList: list
    :return shortNameList: the short names
    :rtype shortNameList: list
    """
    shortNameList = list()
    for longName in longNameList:
        shortNameList.append(getShortName(longName))
    return shortNameList


# -------------------------
# UNIQUE NAMES
# -------------------------


def getUniqueShortName(longName):
    """Returns the shortest unique name

    For example:
        "|grp|rig|geo|mesh"
        May not be a Maya unique name, it is the full path or long name
        Instead the unique name is the shortest path to the unique name so it could be
        "geo|mesh"

    Also invalid are names that start with a pipe such as unless they are parented to the world
        "|geo|mesh"

    For example world unique names may be valid
        "|sphere1" can be ok if shpere1 is duplicated elsewhere

    This is important for mel (or mel eval) functions such as the mel:
        findRelatedSkinCluster "geo|mesh"

    Which cannot be passed true long names

    :param longName: Maya object/node long name
    :type longName: str
    :return: The short name of a Maya object unless it's not unique, in that case return the longname
    :rtype: str
    """
    return cmds.ls(longName, shortNames=True)[0]


def getUniqueShortNameList(longNameList):
    """Returns a list of objs with unique names, will try short and if non-unique then will keep the longname

    :param longNameList: Maya object/node list of long names
    :type longNameList: list
    :return uniqueShortNameList: the short and unique names if duplicated are still kept as long
    :rtype uniqueShortNameList: list
    """
    return cmds.ls(longNameList, shortNames=True)


# -------------------------
# NUMBERS
# -------------------------


def trailingNumber(name):
    """Returns the trailing number of a string, the name with the number removed, and the padding of the number

    Examples:

        "shaderName" returns "shaderName", None, 0
        "shaderName2" returns "shaderName", 2, 1
        "shader1_Name04" returns "shader1_Name", 4, 2
        "shaderName_99" returns "shaderName_", 99, 2
        "shaderName_0009" returns "shaderName_", 9, 4

    :param name:  The string name incoming
    :type name: str
    :return nameNumberless: The name now with the number removed, will be the same if no number found
    :rtype nameNumberless: str
    :return number: the number if one exists, will be None if no number finishes the string
    :rtype number: int
    :return padding: the padding of the number
    :rtype padding: int
    """
    m = re.search(r'\d+$', name)  # get the number as an object
    if m:
        numberAsString = m.group()  # find the number from it's pointer
        nameNumberless = name[:-len(numberAsString)]  # remove the number at string's end
        padding = len(numberAsString)
        return nameNumberless, int(numberAsString), padding
    return name, None, 0


# -------------------------
# NUMBERED UNIQUE NAMES
# -------------------------


def nonUniqueNameNumber(name, shortNewName=True, paddingDefault=2):
    """If a short name is not-unique in Maya return the first numbered unique name

    Will detect padding automatically if the existing name already has a numbered suffix ie "objName_0001" is 4 padding
    Default padding is two if no number suffix exists

    Examples:

        "shaderName" becomes "shaderName_01"
        "shaderName2" becomes "shaderName3"
        "shader1_Name04" becomes "shader1_Name05"
        "shaderName_99" becomes "shaderName_100"
        "shaderName_0009" becomes "shaderName_0010"

    Handles infinite numbers will go up above 999 though the padding will expand

    :param name: the name to check
    :type name: str
    :param shortNewName: will shorten the new name if a long name
    :type shortNewName: bool
    :param paddingDefault: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type paddingDefault: str
    :return newUniqueName: the new name with a potential iterative number suffix newName5_01, can be long or short
    :rtype newUniqueName: str
    """
    separator = ""
    longPrefix, namespace, pureName = mayaNamePartTypes(name)
    nameNumberless, count, padding = trailingNumber(pureName)
    if not count:  # no number found so set count and padding
        count = 0
        padding = paddingDefault
        if nameNumberless[-1] != "_":  # add an underscore if is not the last letter of the numberless string
            separator = "_"
    cancel = False
    newUniqueName = pureName
    if cmds.objExists(newUniqueName):
        while not cancel:
            if not cmds.objExists(newUniqueName):
                break
            count += 1
            newUniqueName = separator.join((nameNumberless, str(count).zfill(padding)))  # zfill is a form of padding
    # return the result
    if not shortNewName:  # rejoin name
        return mayaNamePartsJoin(longPrefix, namespace, newUniqueName)
    return newUniqueName  # is already a short name


def uniqueNameFromList(name, nameList, paddingDefault=2):
    """Finds a unique name when compared against a list, Maya is not queried

    Will detect padding automatically if the existing name already has a numbered suffix ie "objName_0001" is 4 padding
    Default padding is two if no number suffix exists

    The returned name won't match any in the list

    Examples:

        "shaderName" becomes "shaderName_01"
        "shaderName2" becomes "shaderName3"
        "shader1_Name04" becomes "shader1_Name05"
        "shaderName_99" becomes "shaderName_100"
        "shaderName_0009" becomes "shaderName_0010"

    Handles infinite numbers will go up above 999 though the padding will expand

    :param name: the current name
    :type name: str
    :param nameList: the list of names to compare to
    :type nameList: list
    :param paddingDefault: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type paddingDefault: str
    :return name: the name now unique
    :rtype name: str
    """
    if name not in nameList:
        return name
    separator = ""
    nameNumberless, count, padding = trailingNumber(name)
    if not count:  # no number found so set count and padding
        count = 0
        padding = paddingDefault
        if nameNumberless[-1] != "_":  # add an underscore if is not the last letter of the numberless string
            separator = "_"
    cancel = False
    newName = name
    while not cancel:
        if newName in nameList:
            count += 1
            newName = separator.join([nameNumberless, str(count).zfill(padding)])  # zfill is a form of padding
        else:
            break
    return newName


def getUniqueNameSuffix(name, suffix, paddingDefault=2):
    """Returns a unique "_"join([name, suffix]) with a smart iterative number before the suffix, see examples

    Will detect padding automatically if the existing name already contains a numbered suffix
    ie "objName0001_PXR" is 4 pad
    Default padding is two if no number suffix exists

    Example:

        "shader_PXR" becomes "shader_01_PXR"
        "shader_04_PXR" becomes "shader_05_PXR"
        "shader99_PXR" becomes "shader100_PXR"
        "shader_1x9_PXR" becomes "shader_1x10_PXR"
        "shader_002_PXR" becomes "shader_003_PXR"

    Handles infinite numbers will go up above 999 though the padding will expand

    :param name: the name before the suffix
    :type name: str
    :param suffix: the suffix with no "_", suffix only
    :type suffix: str
    :param paddingDefault: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type paddingDefault: str
    """
    # TODO: This function shouldn't worry about the suffix name
    separator = ""
    nameNumberless, count, padding = trailingNumber(name)
    if not count:  # no number found so set count and padding
        count = 0
        padding = paddingDefault
        if nameNumberless[-1] != "_":  # add an underscore if is not the last letter of the numberless string
            separator = "_"
    newUniqueName = "_".join([name, suffix])
    cancel = False
    while not cancel:
        if not cmds.objExists(newUniqueName):
            break
        count += 1
        newUniqueName = "{}{}{}_{}".format(nameNumberless, separator, str(count).zfill(padding), suffix)  # zfill = pad
    return newUniqueName


def forceUniqueShortName(name, paddingDefault=2, uuid=None, ignoreShape=False, shortNewName=True):
    """Given a long name, if it is not unique then rename the Maya object to the first unique name with numbered suffix.

    Existing numbers are handled smartly with padding

    example:

        "shaderName" becomes "shaderName_01"
        "shaderName_2" becomes "shaderName_3"
        "shaderName_04" becomes "shaderName_04"
        "shaderName_99" becomes "shaderName_100"
        "shaderName_0009" becomes "shaderName_0010"

    :param name: the name to check and possibly rename, should be a long name "group2|objName"
    :type name: str
    :param paddingDefault: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type paddingDefault: str
    :param uuid: optional unique hash identifier in case of long name issues while renaming hierarchies or reparenting
    :type uuid: str
    :param ignoreShape: if on will not auto rename the shape node
    :type ignoreShape: str
    :param shortNewName: will shorten the new name if a long name
    :type shortNewName: bool
    :return newUniqueName: the new name with a potential iterative number suffix newName5_01, can be long or short
    :rtype newUniqueName: str
    """
    if uuid:  # if uuid then use the most current long name
        name = cmds.ls(uuid, long=True)[0]
    shortenedMixedName = getUniqueShortName(name)  # shortens the name if unique
    if "|" not in shortenedMixedName:  # will not return a long name if not unique, so if not then the name is unique
        return shortenedMixedName
    # is not unique so rename
    newName = nonUniqueNameNumber(shortenedMixedName, shortNewName=shortNewName, paddingDefault=paddingDefault)
    result = safeRename(name, newName, uuid=uuid, renameShape=not ignoreShape)
    return result


def forceUniqueShortNameList(nameList, paddingDefault=2, ignoreShape=False, shortNewName=True):
    """given a name list if a name is not unique then rename the Maya object to the first unique name
     By default adds an underscore and 2 padding

    example:

        "shaderName" becomes "shaderName_01"
        "shaderName_2" becomes "shaderName_3"
        "shaderName_04" becomes "shaderName_04"
        "shaderName_99" becomes "shaderName_100"
        "shaderName_0009" becomes "shaderName_0010"

    Uses uuid for safety while renaming long names lists and for re-parenting

    :param nameList: the name to check and possibly rename
    :type nameList: list(str)
    :param paddingDefault: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type paddingDefault: int
    :param ignoreShape: if on will not auto rename the shape node
    :type ignoreShape: bool
    :param shortNewName: will shorten the new name if a long name
    :type shortNewName: bool
    :return newUniqueName: the new name with a potential iterative number suffix newName5_01, can be long or short
    :rtype newUniqueName: str
    """
    # TODO this is a hacky/lazy function and should be removed from most code especially renderertransferlights.py
    returnedObjList = list()
    uuidList = cmds.ls(nameList, uuid=True)
    for i, mixName in enumerate(nameList):
        returnedObjList.append(forceUniqueShortName(mixName, uuid=uuidList[i], paddingDefault=paddingDefault,
                                                    ignoreShape=ignoreShape, shortNewName=False))
    return returnedObjList


def forceUniqueShortNameSelection(paddingDefault=2, ignoreShape=False, shortNewName=True):
    """For the selected object list if a name is not unique then rename the Maya object to the first unique name

    By default adds an underscore and 2 padding

    Example:

        "shaderName" becomes "shaderName_01"
        "shaderName_2" becomes "shaderName_3"
        "shaderName_04" becomes "shaderName_04"
        "shaderName_99" becomes "shaderName_100"
        "shaderName_0009" becomes "shaderName_0010"

    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        return list()
    return forceUniqueShortNameList(selObjs, paddingDefault=paddingDefault, ignoreShape=ignoreShape,
                                    shortNewName=shortNewName)


def forceUniqueShortNameFiltered(niceNameType, padding=2, shortNewName=True, renameShape=True, searchHierarchy=False,
                                 selectionOnly=True, dag=False, removeMayaDefaults=True, transformsOnly=True,
                                 message=True):
    """From a filtered list, filtered by node type (see filterTypes.TYPE_FILTER_LIST) force unique names on the result

    By default adds an underscore and 2 padding

    Example:

        "shaderName" becomes "shaderName_01"
        "shaderName_2" becomes "shaderName_3"
        "shaderName_04" becomes "shaderName_04"
        "shaderName_99" becomes "shaderName_100"
        "shaderName_0009" becomes "shaderName_0010"

    More documentation:

        See filterTypes.filterByNiceType() for more information about filtering by type

    :param niceNameType: A single string from the list filterTypes.TYPE_FILTER_LIST, describes a type of node/s in Maya
    :type niceNameType: str
    :param padding: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type padding: str
    :param shortNewName: Return the new short name and not a long name?
    :type shortNewName: bool
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param selectionOnly: If True search the selected objects not the whole scene
    :type selectionOnly: bool
    :param searchHierarchy: Also try to search the hierarchy below the objectList?  False will only filter objList
    :type searchHierarchy: bool
    :param dag: return only dag nodes?  Ie nodes that can be viewed in the outliner hierarchy tree?
    :type dag: bool
    :param transformsOnly: If True will not further filter the transforms with the function filterShapesFromList()
    :type transformsOnly: bool
    :param removeMayaDefaults: While filtering the whole scene don't include default nodes such as lambert1/persp etc
    :type removeMayaDefaults: bool
    :param message: Return the message to the user?
    :type message: bool
    :return objList: the object list with new names
    :rtype objList: list(str)
    """
    filteredObjList = filtertypes.filterByNiceType(niceNameType,
                                                   searchHierarchy=searchHierarchy,
                                                   selectionOnly=selectionOnly,
                                                   dag=dag,
                                                   removeMayaDefaults=removeMayaDefaults,
                                                   transformsOnly=transformsOnly,
                                                   message=True)
    if not filteredObjList:
        return  # should already produce a warning
    return forceUniqueShortNameList(filteredObjList, paddingDefault=padding, ignoreShape=not renameShape,
                                    shortNewName=shortNewName)


def nodeListIsUniqueName(nodeLongNameList, removeNamespaces=False):
    """Checks to see if any nodes in a node list are not unique
    Returns a list that of not unique names, or if None found returns an empty string

    :param nodeList: list of Maya nodes
    :type nodeList: list
    :param removeNamespaces: Remove namespaces from the names?
    :type removeNamespaces: bool
    :return listIsUnique: True if unique, false if not
    :rtype listIsUnique: bool
    """
    if removeNamespaces:
        nodeLongNameList = removeNamespaceLongnamesList(nodeLongNameList)
    nonUniqueNodeList = list()
    shortNameList = getUniqueShortNameList(nodeLongNameList)
    for nodeName in shortNameList:
        if "|" in nodeName:
            nonUniqueNodeList.append(nodeName)
    return nonUniqueNodeList


# -------------------------
# REMOVE NUMBERS
# -------------------------


def removeNumbersObj(objName, uuid=None, trailingOnly=False, renameShape=True, killUnderscores=True):
    """Removes numbers from a name.  Can remove underscores too:

        "name_001" becomes "name"
        "name1" becomes "name"

    trailingOnly True:

        "name_1_character3" becomes "name_1_character"

    trailingOnly False:

        "name_1_character3" becomes "name_character"

    killUnderscores False:

        "name_1_character_3" becomes "name__character_"

    :param objName: The name of the Maya object or node
    :type objName: str
    :param uuid: optional unique hash identifier in case of long name issues while renaming hierarchies or reparenting
    :type uuid: str
    :param trailingOnly: If True only remove numbers at the end of the name, leave numbers in the middle
    :type trailingOnly: bool
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param killUnderscores: Will remove the unwanted underscores "name_1_character_3" becomes "name_character"
    :type killUnderscores: bool
    :return newName: the new name of the object or node
    :rtype newName: str
    """
    newName = objName.split("|")[-1]
    if not trailingOnly:  # then remove all numbers
        newName = ''.join([i for i in newName if not i.isdigit()])
        if killUnderscores:
            newName = newName.replace("__", "_")  # may be leftover double underscores so remove them
    else:  # remove only the trailing number/s
        newName = objName.rstrip('0123456789')
    if newName[-1] == "_" and killUnderscores:  # remove the underscore at the end of the str
        newName = newName[:-1]
    return safeRename(objName, newName, uuid=uuid, renameShape=renameShape)


def removeNumbersList(objList, trailingOnly=False, renameShape=True, killUnderscores=True):
    """Removes numbers from an object/node list of names:

        See removeNumbersObj() for full documentation and examples.

    :param objList: A list of Maya object or node names
    :type objList: list
    :param trailingOnly: If True only remove numbers at the end of the name, leave numbers in the middle
    :type trailingOnly: bool
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param killUnderscores: Will remove the unwanted underscores "name_1_character_3" becomes "name_character"
    :type killUnderscores: bool
    :return objList: the object list with new names
    :rtype objList: list(str)
    """
    uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):
        removeNumbersObj(obj, uuid=uuidList[i], trailingOnly=trailingOnly, renameShape=renameShape,
                         killUnderscores=killUnderscores)
    return cmds.ls(uuidList, long=True)  # return new long names


def removeNumbersSelection(trailingOnly=False, renameShape=True, killUnderscores=True):
    """Removes numbers from a selection of objects or nodes:

        See removeNumbersObj() for cull documentation and examples.

    :param trailingOnly: If True only remove numbers at the end of the name, leave numbers in the middle
    :type trailingOnly: bool
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param killUnderscores: Will remove the unwanted underscores "name_1_character_3" becomes "name_character"
    :type killUnderscores: bool
    :return objList: the object list with new names
    :rtype objList: list(str)
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        return list()
    return removeNumbersList(selObjs, trailingOnly=trailingOnly, renameShape=renameShape,
                             killUnderscores=killUnderscores)


def removeNumbersFilteredType(niceNameType, trailingOnly=False, killUnderscores=True, renameShape=True,
                              searchHierarchy=False, selectionOnly=True, dag=False, removeMayaDefaults=True,
                              transformsOnly=True, message=True):
    """Removes numbers from objects/nodes depending on the kwargs and nicename node type:

        See removeNumbersObj() for documentation and examples about the rename.
        See filterTypes.filterByNiceType() for more information about filtering by type.

    :param niceNameType: A single string from the list filterTypes.TYPE_FILTER_LIST, describes a type of node/s in Maya
    :type niceNameType: str
    :param trailingOnly: If True only remove numbers at the end of the name, leave numbers in the middle
    :type trailingOnly: bool
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param killUnderscores: Will remove the unwanted underscores "name_1_character_3" becomes "name_character"
    :type killUnderscores: bool
    :param selectionOnly: If True search the selected objects not the whole scene
    :type selectionOnly: bool
    :param searchHierarchy: Also try to search the hierarchy below the objectList?  False will only filter objList
    :type searchHierarchy: bool
    :param dag: return only dag nodes?  Ie nodes that can be viewed in the outliner hierarchy tree?
    :type dag: bool
    :param transformsOnly: If True will not further filter the transforms with the function filterShapesFromList()
    :type transformsOnly: bool
    :param removeMayaDefaults: While filtering the whole scene don't include default nodes such as lambert1/persp etc
    :type removeMayaDefaults: bool
    :param message: Return the message to the user?
    :type message: bool
    :return objList: the object list with new names
    :rtype objList: list(str)
    """
    filteredObjList = filtertypes.filterByNiceType(niceNameType,
                                                   searchHierarchy=searchHierarchy,
                                                   selectionOnly=selectionOnly,
                                                   dag=dag,
                                                   removeMayaDefaults=removeMayaDefaults,
                                                   transformsOnly=transformsOnly,
                                                   message=True)
    if not filteredObjList:
        return  # should already produce a warning
    return removeNumbersList(filteredObjList, trailingOnly=trailingOnly, renameShape=renameShape)


# -------------------------
# RE-NUMBER
# -------------------------


def renumberObjList(objList, removeTrailingNumbers=True, addUnderscore=True, padding=2, renameShape=True,
                    message=False):
    """Renumbers from a list of objects/nodes:

    removeTrailingNumbers True, addUnderscore=True, padding=2:

        "[pCube1, pSphere1, pCylinder1]" becomes "[pCube_01, pSphere_02, pCylinder_03]"

    removeTrailingNumbers False, addUnderscore=True, padding=3:

        "[pCube1, pSphere1, pCylinder1]" becomes "[pCube1_001, pSphere1_002, pCylinder1_003]"

    removeTrailingNumbers True, addUnderscore=False, padding=1:

        "[pCube1, pSphere1, pCylinder1]" becomes "[pCube1, pSphere2, pCylinder3]"

    :param objList: A list of Maya object or node names
    :type objList: list
    :param removeTrailingNumbers: Removes trailing numbers before doing the renumber. "pCube1" becomes "pCube_##"
    :type removeTrailingNumbers: bool
    :param addUnderscore: Adds an underscore between the name and the new number
    :type addUnderscore: bool
    :param padding: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type padding: str
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param message: Return the message to the user?
    :type message: bool
    :return objList: the object list with new names
    :rtype objList: list(str)
    """
    uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):
        if removeTrailingNumbers:
            obj = removeNumbersObj(obj, uuid=uuidList[i], trailingOnly=True)
        numberSuffix = str(i + 1).zfill(padding)
        if addUnderscore:
            numberSuffix = "_{}".format(numberSuffix)
        newName = "".join([obj, numberSuffix])
        safeRename(obj, newName, uuid=uuidList[i], renameShape=renameShape, message=message)
    return cmds.ls(uuidList, long=True)  # return new long names


def renumberSelection(removeTrailingNumbers=True, addUnderscore=True, padding=2, renameShape=True, message=False):
    """Renumbers from a selection of objects or nodes:

        See renumberObjList() for documentation and examples about the renumbering.

    :param removeTrailingNumbers: Removes trailing numbers before doing the renumber. "pCube1" becomes "pCube_##"
    :type removeTrailingNumbers: bool
    :param addUnderscore: Adds an underscore between the name and the new number
    :type addUnderscore: bool
    :param padding: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type padding: str
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param message: Return the message to the user?
    :type message: bool
    :return objList: the object list with new names
    :rtype objList: list(str)
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        return list()
    return renumberObjList(selObjs, removeTrailingNumbers=True, addUnderscore=addUnderscore, padding=padding,
                           renameShape=True, message=False)


def renumberFilteredType(niceNameType, removeTrailingNumbers=True, padding=2, addUnderscore=True, renameShape=True,
                         searchHierarchy=False, selectionOnly=True, dag=False, removeMayaDefaults=True,
                         transformsOnly=True, message=True):
    """Renumbers objects/nodes depending on the kwargs and nicename node type:

        See renumberObjList() for documentation and examples about the renumbering.
        See filterTypes.filterByNiceType() for more information about filtering by type.

    :param niceNameType: A single string from the list filterTypes.TYPE_FILTER_LIST, describes a type of node/s in Maya
    :type niceNameType: str
    :param removeTrailingNumbers: Removes trailing numbers before doing the renumber. "pCube1" becomes "pCube_##"
    :type removeTrailingNumbers: bool
    :param padding: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type padding: str
    :param addUnderscore: Adds an underscore between the name and the new number
    :type addUnderscore: bool
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param searchHierarchy: Also try to search the hierarchy below the objectList?  False will only filter objList
    :type searchHierarchy: bool
    :param selectionOnly: If True search the selected objects not the whole scene
    :type selectionOnly: bool
    :param dag: return only dag nodes?  Ie nodes that can be viewed in the outliner hierarchy tree?
    :type dag: bool
    :param removeMayaDefaults: While filtering the whole scene don't include default nodes such as lambert1/persp etc
    :type removeMayaDefaults: bool
    :param transformsOnly: If True will not further filter the transforms with the function filterShapesFromList()
    :type transformsOnly: bool
    :param message: Return the message to the user?
    :type message: bool
    :return objList: the object list with new names
    :rtype objList: list(str)
    """
    filteredObjList = filtertypes.filterByNiceTypeKeepOrder(niceNameType,
                                                            searchHierarchy=searchHierarchy,
                                                            selectionOnly=selectionOnly,
                                                            dag=dag,
                                                            removeMayaDefaults=removeMayaDefaults,
                                                            transformsOnly=transformsOnly,
                                                            message=True)
    if not filteredObjList:
        return  # should already produce a warning
    newNameList = renumberObjList(filteredObjList,
                                  removeTrailingNumbers=removeTrailingNumbers,
                                  addUnderscore=addUnderscore,
                                  padding=padding,
                                  renameShape=renameShape,
                                  message=message)
    return newNameList


# -------------------------
# CHANGE PADDING
# -------------------------


def changeSuffixPadding(objName, uuid=None, padding=2, addUnderscore=True, renameShape=True, message=False):
    """Changes the suffix numerical padding of an objects or node:

    addUnderscore=True, padding=2:

        "pCube1" becomes "pCube_01"

    addUnderscore=False, padding=3:

        "pCube1" becomes "pCube001"

    :param objName: The name of the Maya object or node
    :type objName: str
    :param uuid: optional unique hash identifier in case of long name issues while renaming hierarchies or re-parenting
    :type uuid: str
    :param padding: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type padding: str
    :param addUnderscore: Adds an underscore between the name and the new number
    :type addUnderscore: bool
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param message: Return the message to the user?
    :type message: bool
    :return newName: the new name of the object or node
    :rtype newName: str
    """
    nameNoNumber, number, currentPadding = trailingNumber(objName)
    if not number:  # no trailing number
        return objName
    newPadding = str(number).zfill(padding)
    if nameNoNumber[-1] == "_":  # remove the trailing underscore if exists
        nameNoNumber = nameNoNumber[:-1]
    if addUnderscore:
        newName = "_".join([nameNoNumber, newPadding])
    else:
        newName = "".join([nameNoNumber, newPadding])
    safeRename(objName, newName, uuid=uuid, renameShape=renameShape, message=message)


def changeSuffixPaddingList(objList, padding=2, addUnderscore=True, renameShape=True, message=False):
    """Changes the suffix numerical padding from a list of objects or nodes:

        See changeSuffixPadding() for documentation and examples about changing suffix padding.

    :param objList: A list of Maya object or node names
    :type objList: list
    :param uuid: optional unique hash identifier in case of long name issues while renaming hierarchies or re-parenting
    :type uuid: str
    :param padding: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type padding: str
    :param addUnderscore: Adds an underscore between the name and the new number
    :type addUnderscore: bool
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param message: Return the message to the user?
    :type message: bool
    :return objList: the object list with new names
    :rtype objList: list(str)
    """
    uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):
        changeSuffixPadding(obj, uuid=uuidList[i], padding=padding, addUnderscore=addUnderscore,
                            renameShape=renameShape, message=message)
    return cmds.ls(uuidList, long=True)  # return new long names


def changeSuffixPaddingSelection(padding=2, addUnderscore=True, renameShape=True, message=False):
    """Changes the suffix numerical padding from a selection of objects or nodes:

        See changeSuffixPadding() for documentation and examples about changing suffix padding.

    :param padding: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type padding: str
    :param addUnderscore: Adds an underscore between the name and the new number
    :type addUnderscore: bool
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param message: Return the message to the user?
    :type message: bool
    :return objList: the object list with new names
    :rtype objList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return list()
    return changeSuffixPaddingList(selObjs, padding=padding, addUnderscore=addUnderscore, renameShape=renameShape,
                                   message=message)


def changeSuffixPaddingFilter(niceNameType, padding=2, addUnderscore=True, renameShape=True, searchHierarchy=False,
                              selectionOnly=True, dag=False, removeMayaDefaults=True, transformsOnly=True,
                              message=True):
    """Changes the suffix numerical padding of objects/nodes depending on the kwargs and nicename node type:

        See changeSuffixPadding() for documentation and examples about changing suffix padding.
        See filterTypes.filterByNiceType() for more information about filtering by type.

    :param niceNameType: A single string from the list filterTypes.TYPE_FILTER_LIST, describes a type of node/s in Maya
    :type niceNameType: str
    :param padding: the amount of numerical padding.  2 = 01, 3 = 001, etc, only used if no number exists
    :type padding: str
    :param addUnderscore: Adds an underscore between the name and the new number
    :type addUnderscore: bool
    :param renameShape: Rename the shape nodes automatically to match transform renames
    :type renameShape: bool
    :param searchHierarchy: Also try to search the hierarchy below the objectList?  False will only filter objList
    :type searchHierarchy: bool
    :param selectionOnly: If True search the selected objects not the whole scene
    :type selectionOnly: bool
    :param dag: return only dag nodes?  Ie nodes that can be viewed in the outliner hierarchy tree?
    :type dag: bool
    :param removeMayaDefaults: While filtering the whole scene don't include default nodes such as lambert1/persp etc
    :type removeMayaDefaults: bool
    :param transformsOnly: If True will not further filter the transforms with the function filterShapesFromList()
    :type transformsOnly: bool
    :param message: Return the message to the user?
    :type message: bool
    :return objList: the object list with new names
    :rtype objList: list(str)
    """
    filteredObjList = filtertypes.filterByNiceType(niceNameType,
                                                   searchHierarchy=searchHierarchy,
                                                   selectionOnly=selectionOnly,
                                                   dag=dag,
                                                   removeMayaDefaults=removeMayaDefaults,
                                                   transformsOnly=transformsOnly,
                                                   message=message)
    if not filteredObjList:
        return  # should already produce a warning
    return changeSuffixPaddingList(filteredObjList, padding=padding, addUnderscore=addUnderscore,
                                   renameShape=renameShape, message=message)


# -------------------------
# SEARCH REPLACE
# -------------------------


def searchReplaceName(objName, searchTxt, replaceText, uuid=None, renameShape=True, message=False):
    """For a single object search and replace on the object name.

    Example:

        search: "Cube"
        replace: "Koala"
        result: "pCube1" becomes "pKoala1"

    If a uuid is given will use that instead of the node name, can be handy with re-parenting/hierarchies with renaming

    :param objName: The name of the object to be renamed
    :type objName: str
    :param searchTxt: The text to search for, this text will be replaced
    :type searchTxt: str
    :param replaceText: The replace text that replaces the search text
    :type replaceText: str
    :param uuid: optional unique hash identifier in case of long name issues while renaming hierarchies or re-parenting
    :type uuid: str
    :param renameShape: also rename the shape node if a transform or joint?
    :type renameShape: bool
    :return newName: The new name of the object now potentially renamed
    :rtype newName: str
    """
    longPrefix, namespace, pureName = mayaNamePartTypes(objName)
    pureName = pureName.replace(searchTxt, replaceText)
    newName = mayaNamePartsJoin(longPrefix, namespace, pureName)
    return safeRename(objName, newName, uuid=uuid, renameShape=True, message=message)


def searchReplaceObjList(objList, searchTxt, replaceText, renameShape=True, message=False):
    """Renames a list of object/node names with the replaceText replacing the searchTxt:

        See searchReplaceName() for documentation.

    :param objList: a list of Maya nodes/objects
    :type objList: list
    :param searchTxt: The text to search for, this text will be replaced
    :type searchTxt: str
    :param replaceText: The replace text that replaces the search text
    :type replaceText: str
    :param renameShape: also rename the shape node if a transform or joint?
    :type renameShape: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):
        searchReplaceName(obj, searchTxt, replaceText, uuid=uuidList[i], renameShape=renameShape, message=message)
    return cmds.ls(uuidList, long=True)  # return new long names


def searchReplaceSelection(searchTxt, replaceText, renameShape=True, message=True):
    """Renames the selected objects/nodes with the replaceText replacing the searchTxt:

        See searchReplaceName() for documentation

    :param searchTxt: The text to search for, this text will be replaced
    :type searchTxt: str
    :param replaceText: The replace text that replaces the search text
    :type replaceText: str
    :param renameShape: also rename the shape node if a transform or joint?
    :type renameShape: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        return list()
    return searchReplaceObjList(selObjs, searchTxt, replaceText, renameShape=renameShape, message=message)


def searchReplaceFilteredType(searchTxt, replaceText, niceNameType, renameShape=True, searchHierarchy=False,
                              selectionOnly=True, dag=False, removeMayaDefaults=True, transformsOnly=True,
                              message=True):
    """From a special filter type will filter the search and replace to only rename the returned type of object:

        See filterTypes.filterByNiceType() for more information about filtering by type

    :param searchTxt: The text to search for, this text will be replaced
    :type searchTxt: str
    :param replaceText: The replace text that replaces the search text
    :type replaceText: str
    :param niceNameType: A nice name of an object type, as found in filterTypes.TYPE_FILTER_LIST eg "Polygon", "Locator"
    :type niceNameType: str
    :param renameShape: also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param searchHierarchy: Also search the hierarchy of the selected objects?
    :type searchHierarchy: bool
    :param selectionOnly: Only search within the current selection
    :type selectionOnly: bool
    :param dag: filter dag (viewport hierarchy) nodes only?
    :type dag: bool
    :param removeMayaDefaults: If not searching the selection will remove default Maya objects like persp and lambert1
    :type removeMayaDefaults: bool
    :param transformsOnly: filter out the shape nodes, usually True
    :type transformsOnly: bool
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    filteredObjList = filtertypes.filterByNiceType(niceNameType,
                                                   searchHierarchy=searchHierarchy,
                                                   selectionOnly=selectionOnly,
                                                   dag=dag,
                                                   removeMayaDefaults=removeMayaDefaults,
                                                   transformsOnly=transformsOnly,
                                                   message=message)
    if not filteredObjList:
        return  # should already produce a warning
    newNameList = searchReplaceObjList(filteredObjList, searchTxt, replaceText, renameShape=renameShape,
                                       message=message)
    return newNameList


# -------------------------
# SUFFIX/PREFIX
# -------------------------

def checkSuffixPrefixExists(objName, suffixPrefix, sptype=SUFFIX):
    """Checks to see if the suffix, or prefix already exists, returns True if a match, false if not found.

    :param objName: The name of the object to be renamed
    :type objName: str
    :param suffixPrefix: string to add at the start/finish of the name, add underscore with "addUnderscore" flag
    :type suffixPrefix: str
    :param sptype: Check the suffix or prefix, use globals SUFFIX or PREFIX
    :type sptype: str
    :return suffixPrefixFound: True if a suffixPrefix is found, False if not found
    :rtype suffixPrefixFound: bool
    """
    if sptype == SUFFIX:
        objPartList = objName.split("_")
        if objPartList[-1] == suffixPrefix.replace('_', ''):  # suffix with underscores removed
            return True
        return False
    if sptype == PREFIX:
        longPrefix, namespace, pureName = mayaNamePartTypes(objName)  # potential namespace handling
        pureNamePartList = pureName.split("_")
        if pureNamePartList[0] == suffixPrefix.replace('_', ''):  # prefix with underscores removed
            return True
        return False


def stripSuffixExact(fullName, suffix, seperator="_"):
    """Removes the suffix if given the exact letters to match and remove

    Example:

        "name_suffix" becomes "name"

    If the suffix isn't found returns the fullName

    :param fullName: the full name with the suffix
    :type fullName: str
    :param suffix: the suffix with no underscore
    :type suffix: str
    :return nameNoSuffix: the name now with no suffix
    :rtype nameNoSuffix: str
    """
    suffix = "".join([seperator, suffix])
    if fullName.endswith(suffix):
        return fullName[:-len(suffix)]
    return fullName


def addPrefixSuffix(objName, prefixSuffix, sptype=SUFFIX, uuid=None, addUnderscore=False, renameShape=True,
                    message=False, checkExistingSuffixPrefix=True):
    """Uses the safeName() function to rename with a prefix or suffix,

    Pass in a uuid if having trouble with hierarchy naming or parenting/re-parenting and long names

    Example:

        objName: "|group1|Cube"
        prefixSuffix: "_jnt"
        sptype: "suffix"
        result: "|group1|Cube_jnt" (object renamed)

    Example with uuid:

        uuid: "B7EABB60-4578-A4D1-73DC-07B9A14F267F"
        prefixSuffix: "jnt"
        addUnderscore: True
        sptype: "prefix"
        result: "|group1|jnt_Cube" (object renamed)

    :param objName: The name of the object to be renamed
    :type objName: str
    :param prefixSuffix: string to add at the start/finish of the name, add underscore with "addUnderscore" flag
    :type prefixSuffix: str
    :param sptype: Suffix or Prefix, use SUFFIX or PREFIX
    :type sptype: str
    :param uuid: optional unique hash identifier in case of long name issues while renaming hierarchies or re-parenting
    :type uuid: str
    :param addUnderscore: Will add an underscore to the suffix ie "pCube1suffix" becomes pCube1_suffix"
    :type addUnderscore: bool
    :param renameShape: also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param checkExistingSuffixPrefix: checks if the suffix/prefix exists and if so doesn't add another
    :type checkExistingSuffixPrefix: bool
    :param message: also rename the shape node if a transform or joint?
    :type message: bool
    :return newName: The new name of the object now potentially renamed
    :rtype newName: str
    """
    suffixPrefixExists = False
    if checkExistingSuffixPrefix:
        suffixPrefixExists = checkSuffixPrefixExists(objName, prefixSuffix, sptype)
    if sptype == SUFFIX:
        if not suffixPrefixExists:  # Add the suffix
            if addUnderscore:
                prefixSuffix = "_{}".format(prefixSuffix)
            newName = "".join([objName, prefixSuffix])
        else:  # no need to rename
            newName = objName
    else:  # == PREFIX
        if not suffixPrefixExists:  # Add the prefix
            if addUnderscore:
                prefixSuffix = "{}_".format(prefixSuffix)
            longPrefix, namespace, pureName = mayaNamePartTypes(objName)  # potential namespace handling
            pureName = "".join([prefixSuffix, pureName])
            newName = mayaNamePartsJoin(longPrefix, namespace, pureName)
        else:  # no need to rename
            newName = objName
    # do the rename
    return safeRename(objName, newName, uuid=uuid, renameShape=True, message=message)


def addPrefixSuffixList(objList, prefixSuffix, sptype=SUFFIX, uuid=None, addUnderscore=False, renameShape=True,
                        checkExistingSuffixPrefix=True, message=False):
    """Uses the safeName() function to rename and object list adding a prefix or suffix.

    Uses uuid's in case of hierarchies or re-parenting long name issues:

        See addPrefixSuffix() documentation for more information about how this function renames.

    :param objList: Objects to be renamed as a list
    :type objList: list
    :param prefixSuffix: string to add at the start/finish of the name, add underscore with "addUnderscore" flag
    :type prefixSuffix: str
    :param uuid: optional unique hash identifier in case of long name issues while renaming hierarchies or re-parenting
    :type uuid: str
    :param addUnderscore: Will add an underscore to the suffix ie "pCube1suffix" becomes pCube1_suffix"
    :type addUnderscore: bool
    :param renameShape: also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param checkExistingSuffixPrefix: checks if the suffix/prefix exists and if so doesn't add another
    :type checkExistingSuffixPrefix: bool
    :param message: also rename the shape node if a transform or joint?
    :type message: bool
    :param renameShape: also rename the shape node if a transform or joint?
    :type renameShape: bool
    :return newNameList: The new names of all objects now potentially renamed
    :rtype newNameList: list
    """
    uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):
        addPrefixSuffix(obj, prefixSuffix, sptype=sptype, uuid=uuidList[i], addUnderscore=addUnderscore,
                        renameShape=renameShape, checkExistingSuffixPrefix=checkExistingSuffixPrefix,
                        message=message)
    return cmds.ls(uuidList, long=True)  # return new long names


def addSuffixSelection(prefixSuffix, sptype=SUFFIX, uuid=None, addUnderscore=False, renameShape=True, message=False):
    """Uses the safeName() function to rename the current selection adding a prefix or suffix to every selected object

    Uses uuid's in case of hierarchies or re-parenting avoiding long name issues:

        See addPrefixSuffix() documentation for more information about how this function renames.

    :param prefixSuffix: string to add at the start/finish of the name, add underscore with "addUnderscore" flag
    :type prefixSuffix: str
    :param addUnderscore: Will add an underscore to the suffix ie "prefixpCube1" becomes "prefix_pCube1"
    :type addUnderscore: bool
    :param renameShape: also rename the shape node if a transform or joint?
    :type renameShape: bool
    :return newNameList: The new names of all objects now potentially renamed
    :rtype newNameList: list
    """
    selObj = cmds.ls(selection=True)
    if not selObj:  # bail
        return list()
    return addPrefixSuffixList(selObj, prefixSuffix, sptype=sptype, addUnderscore=False, renameShape=True,
                               message=message)


def prefixSuffixFilteredType(prefixSuffix, niceNameType, sptype=SUFFIX, renameShape=True, searchHierarchy=False,
                             selectionOnly=True, dag=False, removeMayaDefaults=True, transformsOnly=True,
                             message=True):
    """With a niceNameType, this function will filter and prefix or suffix by the filtered object type:

        See addPrefixSuffix() documentation for more information about how this function renames.
        See filterTypes.filterByNiceType() for more information about filtering by niceNameType.

    :param prefixSuffix: string to add at the start/finish of the name, add underscore with "addUnderscore" flag
    :type prefixSuffix: str
    :param niceNameType: A nice name of an object type, as found in filterTypes.TYPE_FILTER_LIST eg "Polygon", "Locator"
    :type niceNameType: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param searchHierarchy: Also search the hierarchy of the selected objects?
    :type searchHierarchy: bool
    :param selectionOnly: Only search within the current selection
    :type selectionOnly: bool
    :param dag: filter dag (viewport hierarchy) nodes only?
    :type dag: bool
    :param removeMayaDefaults: If not searching the selection will remove default Maya objects like persp and lambert1
    :type removeMayaDefaults: bool
    :param transformsOnly: filter out the shape nodes, usually True
    :type transformsOnly: bool
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    filteredObjList = filtertypes.filterByNiceType(niceNameType,
                                                   searchHierarchy=searchHierarchy,
                                                   selectionOnly=selectionOnly,
                                                   dag=dag,
                                                   removeMayaDefaults=removeMayaDefaults,
                                                   transformsOnly=transformsOnly,
                                                   message=True)
    if not filteredObjList:
        return  # should already produce a warning
    return addPrefixSuffixList(filteredObjList, prefixSuffix, sptype=sptype, addUnderscore=False, renameShape=True,
                               message=message)


# -------------------------
# AUTO SUFFIX/PREFIX
# -------------------------


def autoPrefixSuffixObj(objName, uuid=None, sptype=SUFFIX, renameShape=True):
    """Will auto suffix or prefix a node automatically in Maya by it's node type.

    Suffix example:

        "group1" becomes "group1_grp"
        "pCube1" becomes "pCube1_geo"

    Suffix types must be defined in filterTypes.SUFFIXLIST(), later would like to add to a JSON so users can modify
    in a GUI.

    The suffix in some cases is intelligent, for example a transform node selection will look for the first shape node
    to define its type. And in special cases such as groups or controls the code intelligently figures the suffix since
    there are no node types in Maya for controls or groups.

    Suffix examples, refer to filterTypes.SUFFIXLIST() for latest:

        filterTypes.GEO_SX = 'geo'
        filterTypes.JOINT_SX = 'jnt'
        filterTypes.CONTROLLER_SX = 'ctrl'
        filterTypes.GROUP_SX = 'grp'
        filterTypes.SRT_SX = 'srt'
        filterTypes.LEFT_SX = 'L'
        filterTypes.LEFT2_SX = 'lft'
        filterTypes.RIGHT_SX = 'R'
        filterTypes.RIGHT2_SX = 'rgt'
        filterTypes.CENTER_SX = 'M'
        filterTypes.CENTER2_SX = 'cntr'
        filterTypes.CENTER3_SX = 'mid'
        filterTypes.CURVE_SX = 'crv'
        filterTypes.CLUSTER_SX = 'cstr'
        filterTypes.FOLLICLE_SX = 'foli'
        filterTypes.NURBS_SX = 'geo'
        filterTypes.IMAGEPLANE_SX = 'imgp'
        filterTypes.LOCATOR_SX = 'loc'
        filterTypes.LIGHT_SX = 'lgt'
        filterTypes.SHADER_SX = 'shdr'
        filterTypes.SHADINGGROUP_SX = 'shdg'
        filterTypes.CAMERA_SX = 'cam'

    :param objName: The current name of the object or node, can be long or unique names
    :type objName: str
    :param uuid: Optional unique hash identifier in case of long name issues while renaming hierarchies or re-parenting
    :type uuid: str
    :param sptype: Suffix Prefix type, eg filterTypes.GROUP_SX is "grp".  "group1" becomes "group1_grp"
    :type sptype: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :return newName: The new name of the object now potentially renamed
    :rtype newName: str
    """
    if uuid:  # if uuid then use the most current long name
        objName = cmds.ls(uuid, long=True)[0]
    cmds.listRelatives(objName, shapes=True)
    objType = cmds.objectType(objName)
    # check if transform is a group --------------
    if objType == "transform":  # check if group
        shapeNodes = cmds.listRelatives(objName, shapes=True, fullPath=True)
        if not shapeNodes:  # then is a group
            objType = "group"
        else:
            objType = cmds.objectType(shapeNodes[0])
    # check if joint is a control --------------
    elif objType == "joint":  # check if has a curve shape child
        shapeNodes = cmds.listRelatives(objName, shapes=True, fullPath=True)
        if shapeNodes and cmds.objectType(shapeNodes[0]) == "nurbsCurve":  # then is a control
            objType = "controller"
    # check if curve is a control (controller tag) --------------
    if objType == "nurbsCurve":
        connections = cmds.listConnections("{}.message".format(objName))
        if connections:
            for node in connections:
                if cmds.objectType(node) == "controller":
                    objType = "controller"
                    break
    # objType is now set, check the dict for matches
    if not objType in filtertypes.AUTO_SUFFIX_DICT:  # objectType is not in the AUTO_SUFFIX_DICT so bail
        return objName  # suffix not found
    else:  # Found a suffix so continue
        prefixSuffix = filtertypes.AUTO_SUFFIX_DICT[objType]
    # check if already suffixed
    existingSuffix = objName.split("_")[-1]
    if existingSuffix == prefixSuffix:
        return objName  # already suffixed
    # do the rename
    return addPrefixSuffix(objName, prefixSuffix, sptype=sptype, uuid=uuid, addUnderscore=True, renameShape=renameShape)


def autoPrefixSuffixList(objList, sptype=SUFFIX, renameShape=True):
    """Will auto suffix or prefix a object/node list automatically in Maya by it's node type:

        See autoPrefixSuffixObj() for full documentation.

    :param objList: Objects to be renamed as a list
    :type objList: list
    :param sptype: Suffix Prefix type, eg filterTypes.GROUP_SX is "grp".  "group1" becomes "group1_grp"
    :type sptype: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :return newNameList: The new names of all objects now potentially renamed
    :rtype newNameList: list
    """
    uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):
        autoPrefixSuffixObj(obj, sptype=sptype, uuid=uuidList[i], renameShape=renameShape)
    return cmds.ls(uuidList, long=True)  # return new long names


def autoPrefixSelection(sptype=SUFFIX, renameShape=True):
    """Will auto suffix or prefix selected nodes/objects automatically in Maya by it's node type:

        See autoPrefixSuffixObj() for full documentation.

    :param sptype: Suffix Prefix type, eg filterTypes.GROUP_SX is "grp".  "group1" becomes "group1_grp"
    :type sptype: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :return newNameList: The new names of all objects now potentially renamed
    :rtype newNameList: list
    """
    selObj = cmds.ls(selection=True)
    if not selObj:  # bail
        return list()
    return autoPrefixSuffixList(selObj, sptype=sptype, renameShape=True)


def autoPrefixSuffixFilteredType(niceNameType, sptype=SUFFIX, renameShape=True, searchHierarchy=False,
                                 selectionOnly=True, dag=False, removeMayaDefaults=True, transformsOnly=True,
                                 message=True):
    """Auto suffix/prefix nodes/objects automatically by node type.  Uses filtering to restrict the renaming:

        See autoPrefixSuffixObj() for full documentation.
        See filterTypes.filterByNiceType() for more information about filtering by type.

    :param niceNameType: A single string from the list filterTypes.TYPE_FILTER_LIST, describes a type of node/s in Maya
    :type niceNameType: str
    :param sptype: Suffix Prefix type, eg filterTypes.GROUP_SX is "grp".  "group1" becomes "group1_grp"
    :type sptype: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param searchHierarchy: Also search the hierarchy of the selected objects?
    :type searchHierarchy: bool
    :param selectionOnly: Only search within the current selection
    :type selectionOnly: bool
    :param dag: filter dag (viewport hierarchy) nodes only?
    :type dag: bool
    :param removeMayaDefaults: If not searching the selection will remove default Maya objects like persp and lambert1
    :type removeMayaDefaults: bool
    :param transformsOnly: filter out the shape nodes, usually True
    :type transformsOnly: bool
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    filteredObjList = filtertypes.filterByNiceType(niceNameType,
                                                   searchHierarchy=searchHierarchy,
                                                   selectionOnly=selectionOnly,
                                                   dag=dag,
                                                   removeMayaDefaults=removeMayaDefaults,
                                                   transformsOnly=transformsOnly,
                                                   message=message)
    if not filteredObjList:
        return  # should already produce a warning
    return autoPrefixSuffixList(filteredObjList, sptype=sptype, renameShape=True)


# -------------------------
# INDEX ITEM EDITING
# -------------------------


def checkIndexIntInList(nameList, index):
    """Checks to see if an index is in a nameList (the name broken up by the separator usually by underscore).

    Returns exists: True or False

    Example:

        nameList: ["pCube1", "grp"]
        0 exists, it is "pCube1" return True
        1 exists, it is "grp" return True
        2 does not exist, return False
        -1 exists, it is "grp, return True
        -2 exists, it is "pCube1", return True
        -3 does not exist, return False

    :param nameList: A single name split into components usually by underscore.  ["pCube1", "grp"]
    :type nameList: list(str)
    :param index: The index number, can be negative.  ["pCube1", "grp"] 0 is "pCube1", 1 is "grp" -1 is "grp"
    :type index: int
    :return exists: The index is in the nameList True, or isn't False
    :rtype exists: bool
    """
    listLength = len(nameList)
    if index < 0:  # is negative so make postive
        checkLength = abs(index)
    else:  # is positive so add one
        checkLength = index + 1
    if checkLength > listLength:  # index is not in list
        return False
    return True


# -------------------------
# REMOVE ITEM
# -------------------------


def editIndexItem(objName, index, text="", mode=EDIT_INDEX_INSERT, separator="_", renameShape=True, uuid=None,
                  message=False):
    """Split an object/node name by it's separator (usually underscore), edit the position based by it's index number.

    Modes:

        EDIT_INDEX_INSERT: "insert", will insert (add) a new value into that position
        EDIT_INDEX_REMOVE: "remove", will delete the text by index at that position
        EDIT_INDEX_REPLACE: "replace", will overwrite the text at that position

    Example args/kwargs:

        objName: "pCube_01_geo" (index 0 is "pCube". 1 is "01". 2 is "geo". -1 is "geo" etc)
        index: 1
        text: "variantA"

    Results:

        Insert result: "pCube_variantA_01_geo"
        Replace result: "pCube_variantA_geo"
        Remove result: "pCube_geo"

    Optional uuid can be used in case of hierarchies or re-parenting avoiding long name issues.

    :param objName: The current name of the object or node, can be long or unique names
    :type objName: str
    :param index: The index number, can be negative.  ["pCube1", "grp"] 0 is "pCube1", 1 is "grp" -1 is "grp"
    :type index: int
    :param text: The text to "insert" or "replace".  "remove" no text is needed.
    :type text: str
    :param mode: The three modes for this function... EDIT_INDEX_INSERT, EDIT_INDEX_REMOVE, EDIT_INDEX_REPLACE
    :type mode: str
    :param separator: The text used to split the text, usually an underscore "_"
    :type separator: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param uuid: Optional unique hash identifier in case of long name issues while renaming hierarchies or re-parenting
    :type uuid: str
    :param message: Report a message to the user?
    :type message: bool
    :return newName: The new name of the object now potentially renamed
    :rtype newName: str
    """
    longPrefix, namespace, pureName = mayaNamePartTypes(objName)  # break up long or namespace name
    pureNameList = pureName.split(separator)
    if not checkIndexIntInList(pureNameList, index):  # if the index isn't in the list
        return objName
    if mode == EDIT_INDEX_REMOVE:  # remove -------------------------
        if len(pureNameList) == 1:
            om2.MGlobal.displayWarning("Not enough name parts to rename: {}".format(pureNameList[0]))
            return objName
        del pureNameList[index]
    elif mode == EDIT_INDEX_REPLACE:  # replace --------------------
        if not text:  # if empty string then remove item
            del pureNameList[index]  # remove
        else:
            pureNameList[index] = text  # replace item
    else:  # insert --------------------------------------------------
        if not text:  # can't insert empty string bail
            return objName
        neg = False
        if index < 0:  # if index is neg +1, insert is not intuitive for neg numbers
            index += 1
            neg = True
        if index == 0 and neg:  # if zero and negative append to the end instead of insert
            pureNameList.append(text)
        elif index == 0 and not neg:  # if zero and positive add to the start instead of insert
            pureNameList = [text] + pureNameList
        else:  # can insert as per normal
            pureNameList.insert(index, text)  # insert
    pureName = separator.join(pureNameList)
    newName = mayaNamePartsJoin("", namespace, pureName)  # build name again
    return safeRename(objName, newName, uuid=uuid, renameShape=renameShape, message=message)


def editIndexItemList(objList, index, text="", mode=EDIT_INDEX_INSERT, separator="_", renameShape=True, message=False):
    """Split an object/node list by it's separator (usually underscore), edit the position based by it's index number:

        See editIndexItem() for full documentation.

    :param objList: Objects to be renamed as a list
    :type objList: list
    :param index: The index number, can be negative.  ["pCube1", "grp"] 0 is "pCube1", 1 is "grp" -1 is "grp"
    :type index: int
    :param text: The text to "insert" or "replace".  "remove" no text is needed.
    :type text: str
    :param mode: The three modes for this function... EDIT_INDEX_INSERT, EDIT_INDEX_REMOVE, EDIT_INDEX_REPLACE
    :type mode: str
    :param separator: The text used to split the text, usually an underscore "_"
    :type separator: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param message: Report a message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):
        editIndexItem(obj, index, text=text, mode=mode, separator=separator, renameShape=renameShape,
                      uuid=uuidList[i], message=message)
    return cmds.ls(uuidList, long=True)  # return new long names


def editIndexItemSelection(index, text="", mode=EDIT_INDEX_INSERT, separator="_", renameShape=True,
                           message=False):
    """Split a selection by it's separator (usually underscore), edit the position based by it's index number:

        See editIndexItem() for full documentation.

    :param index: The index number, can be negative.  ["pCube1", "grp"] 0 is "pCube1", 1 is "grp" -1 is "grp"
    :type index: int
    :param text: The text to "insert" or "replace".  "remove" no text is needed.
    :type text: str
    :param mode: The three modes for this function... EDIT_INDEX_INSERT, EDIT_INDEX_REMOVE, EDIT_INDEX_REPLACE
    :type mode: str
    :param separator: The text used to split the text, usually an underscore "_"
    :type separator: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param message: Report a message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:  # bail
        return list()
    return editIndexItemList(selObj, index, text=text, mode=mode, separator=separator, renameShape=renameShape,
                             message=message)


def editIndexItemFilteredType(index, niceNameType, text="", mode=EDIT_INDEX_INSERT, separator="_", renameShape=True,
                              searchHierarchy=False, selectionOnly=True, dag=False, removeMayaDefaults=True,
                              transformsOnly=True, message=True):
    """Split object/s by their separator (usually underscore), edit the position by it's index number, uses filtering:

        See editIndexItem() for full documentation.
        See filterTypes.filterByNiceType() for more information about filtering by type.

    :param index: The index number, can be negative.  ["pCube1", "grp"] 0 is "pCube1", 1 is "grp" -1 is "grp"
    :type index: int
    :param niceNameType: A single string from the list filterTypes.TYPE_FILTER_LIST, describes a type of node/s in Maya
    :type niceNameType: str
    :param text: The text to "insert" or "replace".  "remove" no text is needed.
    :type text: str
    :param mode: The three modes for this function... EDIT_INDEX_INSERT, EDIT_INDEX_REMOVE, EDIT_INDEX_REPLACE
    :type mode: str
    :param separator: The text used to split the text, usually an underscore "_"
    :type separator: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param selectionOnly: Only search within the current selection
    :type selectionOnly: bool
    :param dag: filter dag (viewport hierarchy) nodes only?
    :type dag: bool
    :param removeMayaDefaults: If not searching the selection will remove default Maya objects like persp and lambert1
    :type removeMayaDefaults: bool
    :param transformsOnly: filter out the shape nodes, usually True
    :type transformsOnly: bool
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    filteredObjList = filtertypes.filterByNiceType(niceNameType,
                                                   searchHierarchy=searchHierarchy,
                                                   selectionOnly=selectionOnly,
                                                   dag=dag,
                                                   removeMayaDefaults=removeMayaDefaults,
                                                   transformsOnly=transformsOnly,
                                                   message=message)
    if not filteredObjList:
        return  # should already produce a warning
    return editIndexItemList(filteredObjList, index, text=text, mode=mode, separator=separator, renameShape=renameShape,
                             message=message)


# -------------------------
# INDEX ITEM SHUFFLING
# -------------------------


def shuffleItemByIndex(objName, index, offset=1, uuid=None, renameShape=True, separator="_", message=False):
    """Shuffles the position of a text item usually split by an underscore. offset 1 is forwards, -1 is backwards.

    Index is the text to move/shuffle, can be a negative number so "pCube_variant01_geo":

        0: "pCube1"
        1: "pCube_variant01_geo"
        -1: "geo"

    Example shuffle index 0 forwards:

        "pCube_variant01_geo" becomes "variant01_pCube_geo"

    Example shuffle index -1 backwards

        "pCube_variant01_geo" becomes "pCube_geo_variant01"

    This function comes with error checking so if certain tasks can't be completed it will return early and bail
    no errors will be reported for the shuffle even with message on.  Usually in the GUI shuffle errors aren't critical.

    Optional uuid can be used in case of hierarchies or re-parenting avoiding long name issues.

    :param objName: The current name of the object or node, can be long or unique names
    :type objName: str
    :param index: The index number, can be negative.  ["pCube1", "grp"] 0 is "pCube1", 1 is "grp" -1 is "grp"
    :type index: int
    :param offset: The of the shuffle/move, can only be 1 (forwards) or -1 (backwards)
    :type offset: int
    :param uuid: Optional unique hash identifier in case of long name issues while renaming hierarchies or re-parenting
    :type uuid: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param separator: The text used to split the text, usually an underscore "_"
    :type separator: str
    :param message: Report the message to the user?
    :type message: bool
    :return newName: The new name of the object now potentially renamed
    :rtype newName: str
    """
    if uuid:  # if uuid then use the most current long name
        objName = cmds.ls(uuid, long=True)[0]
    longPrefix, namespace, pureName = mayaNamePartTypes(objName)
    pureNameParts = pureName.split(separator)
    # check index is in objName ----------------------------------------------
    if len(pureNameParts) == 1 or offset == 0:  # no parts found in name, or changes to pure name
        return objName
    inList = checkIndexIntInList(pureNameParts, index)  # find if index is in the pureNameParts list
    if not inList:  # bail as the index is too deep
        return objName
    if index == 0 and offset < 0:  # can't offset from 0 into a neg number, already prefix
        return objName
    if index == -1 and offset > 0:  # can't offset from -1 into a pos number, already suffix
        return objName
    # index is in name, continue ---------------------------------------------
    checkIndex = index + offset
    inList = checkIndexIntInList(pureNameParts, checkIndex)
    if not inList:  # bail as can't switch to next/previous
        return objName
    # do the switch shuffle
    indexPart = pureNameParts[index]
    pureNameParts[index] = pureNameParts[index + offset]
    pureNameParts[index + offset] = indexPart
    # success so combine names back together and rename ---------------------
    newName = mayaNamePartsJoin(longPrefix, namespace, "_".join(pureNameParts))
    return safeRename(objName, newName, uuid=uuid, renameShape=renameShape, message=message)


def shuffleItemByIndexList(objList, index, offset=1, renameShape=True, separator="_", message=False):
    """Shuffles the position of a txt item usually split by an underscore in an obj/node list. 1 forwards, -1 backwards:

        See shuffleItemByIndex() for full documentation.

    :param objList: Objects to be renamed as a list
    :type objList: list
    :param index: The index number, can be negative.  ["pCube1", "grp"] 0 is "pCube1", 1 is "grp" -1 is "grp"
    :type index: int
    :param offset: The of the shuffle/move, can only be 1 (forwards) or -1 (backwards)
    :type offset: int
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param separator: The text used to split the text, usually an underscore "_"
    :type separator: str
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):
        shuffleItemByIndex(obj, index, offset=offset, uuid=uuidList[i], renameShape=renameShape,
                           separator=separator, message=message)
    return cmds.ls(uuidList, long=True)  # return new long names


def shuffleItemByIndexSelection(index, offset=1, renameShape=True, separator="_", message=False):
    """Shuffles the position of a txt item usually split by an underscore in the selection. 1 forwards, -1 backwards:

        See shuffleItemByIndex() for full documentation.

    :param index: The index number, can be negative.  ["pCube1", "grp"] 0 is "pCube1", 1 is "grp" -1 is "grp"
    :type index: int
    :param offset: The of the shuffle/move, can only be 1 (forwards) or -1 (backwards)
    :type offset: int
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param separator: The text used to split the text, usually an underscore "_"
    :type separator: str
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:  # bail
        return list()
    return shuffleItemByIndexList(selObjs, index, offset=offset, renameShape=renameShape, separator=separator,
                                  message=message)


def shuffleItemByIndexFilteredType(index, niceNameType, offset=1, separator="_", renameShape=True,
                                   searchHierarchy=False, selectionOnly=True, dag=False, removeMayaDefaults=True,
                                   transformsOnly=True, message=True):
    """Shuffles the position of a txt item usually split by an underscore with filters. 1 forwards, -1 backwards:

        See shuffleItemByIndex() for full documentation.
        See filterTypes.filterByNiceType() for more information about filtering by type.

    :param index: The index number, can be negative.  ["pCube1", "grp"] 0 is "pCube1", 1 is "grp" -1 is "grp"
    :type index: int
    :param niceNameType: A single string from the list filterTypes.TYPE_FILTER_LIST, describes a type of node/s in Maya
    :type niceNameType: str
    :param offset: The of the shuffle/move, can only be 1 (forwards) or -1 (backwards)
    :type offset: int
    :param separator: The text used to split the text, usually an underscore "_"
    :type separator: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param searchHierarchy: Also search the hierarchy of the selected objects?
    :type searchHierarchy: bool
    :param selectionOnly: Only search within the current selection
    :type selectionOnly: bool
    :param dag: filter dag (viewport hierarchy) nodes only?
    :type dag: bool
    :param removeMayaDefaults: If not searching the selection will remove default Maya objects like persp and lambert1
    :type removeMayaDefaults: bool
    :param transformsOnly: filter out the shape nodes, usually True
    :type transformsOnly: bool
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    filteredObjList = filtertypes.filterByNiceType(niceNameType,
                                                   searchHierarchy=searchHierarchy,
                                                   selectionOnly=selectionOnly,
                                                   dag=dag,
                                                   removeMayaDefaults=removeMayaDefaults,
                                                   transformsOnly=transformsOnly,
                                                   message=message)
    if not filteredObjList:
        return  # should already produce a warning
    return shuffleItemByIndexList(filteredObjList, index, offset=offset, renameShape=renameShape, separator=separator,
                                  message=message)


# -------------------------
# NAMESPACES CREATE DELETE RENAME
# -------------------------


def removeEmptyNamespaces(message=True):
    """Removes all empty namespaces in the scene

    Recursive function that starts at the bottom and empties namespaces one by one until the top of the namespace
    hierarchy is reached.

    Credit bob.w http://discourse.techart.online/t/deleting-namespace-the-python-way/5179/3

    :param message: Report the message to the user?
    :type message: bool
    :return delNamespaceList: the list of namespace names deleted
    :rtype delNamespaceList: list
    """
    delNamespaceList = list()

    # Used as a sort key, this will sort namespaces by how many children they have.
    def num_children(ns):
        return ns.count(':')

    namespaceList = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
    # Reverse list, so namespaces with more children are at the front
    namespaceList.sort(key=num_children, reverse=True)
    for namespace in namespaceList:
        try:
            cmds.namespace(removeNamespace=namespace)
            delNamespaceList.append(namespace)
        except RuntimeError:  # namespace is empty
            pass
    if message and delNamespaceList:
        om2.MGlobal.displayInfo("Namespaces removed: {}".format(delNamespaceList))
    return delNamespaceList


def assignNamespace(objName, existingNamespace, removeNamespace=False, uuid=None, renameShape=True, message=False):
    """Will assign (or remove) a namespace to an object. The namespace must already exist in the scene.

    Assign Example:

        objName: "pCube1"
        existingNamespace: "chair"
        removeNamespace: False
        result: "chair:pCube1"

    Remove Example:

        objName: "chair:pCube1"
        existingNamespace: "chair"
        removeNamespace: False
        result: "pCube1"

    :param objName: The current name of the object or node, can be long or unique names
    :type objName: str
    :param existingNamespace: The name of the namespace to assign, it must currently exist in the scene
    :type existingNamespace: str
    :param removeNamespaces: Remove namespaces from the name?  Returned name will not have a namespace
    :type removeNamespaces: bool
    :param uuid: Optional unique hash identifier in case of long name issues while renaming hierarchies or re-parenting
    :type uuid: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param message: Report the message to the user?
    :type message: bool
    :return newName: The new name of the object now potentially renamed
    :rtype newName: str
    """
    longPrefix, namespace, pureName = mayaNamePartTypes(objName)
    if existingNamespace == namespace and not removeNamespace:
        return objName
    if not removeNamespace:
        newName = mayaNamePartsJoin(longPrefix, existingNamespace, pureName)
    else:  # remove namespace
        newName = mayaNamePartsJoin(longPrefix, "", pureName)
    return safeRename(objName, newName, uuid=uuid, renameShape=renameShape,
                      message=message)


def createAssignNamespaceList(objList, namespaceName, removeNamespace=False, renameShape=True, message=False):
    """Will assign (or remove) a namespace to an object list. The namespace will be created if it doesn't exist:

        See assignNamespace() for more information.

    :param objList: Objects to be renamed as a list
    :type objList: list
    :param namespaceName: The new or existing namespace name to assign or remove (if removeNamespace=True)
    :type namespaceName: str
    :param removeNamespaces: Remove namespaces from the name?  Returned name will not have a namespace
    :type removeNamespaces: bool
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    if not cmds.namespace(exists=namespaceName):  # If doesn't exist then
        cmds.namespace(set=':')
        cmds.namespace(add=namespaceName)  # Create
    uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):
        assignNamespace(obj, namespaceName, removeNamespace=removeNamespace, uuid=uuidList[i],
                        renameShape=renameShape, message=message)
    # Delete unused namespaces
    cmds.namespace(set=':')
    removeEmptyNamespaces(message=message)
    return cmds.ls(uuidList, long=True)  # Return new long names


def createAssignNamespaceSelected(namespaceName, removeNamespace=False, renameShape=True, message=False):
    """Will assign (or remove) a namespace to a obj/node selection. The namespace will be created if it doesn't exist:

        See assignNamespace() for more information.

    :param namespaceName: The new or existing namespace name to assign or remove (if removeNamespace=True)
    :type namespaceName: str
    :param removeNamespaces: Remove namespaces from the name?  Returned name will not have a namespace
    :type removeNamespaces: bool
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:  # bail
        return list()
    return createAssignNamespaceList(selObj, namespaceName, renameShape=renameShape, message=message)


def createAssignNamespaceFilteredType(namespaceName, niceNameType, removeNamespace=False, renameShape=True,
                                      searchHierarchy=False, selectionOnly=True, dag=False, removeMayaDefaults=True,
                                      transformsOnly=True, message=True):
    """Will assign (or remove) a namespace to a obj/nodes based off filters.
    The namespace will be created if it doesn't exist:

        See assignNamespace() for more information.
        See filterTypes.filterByNiceType() for more information about filtering by type.

    :param namespaceName: The new or existing namespace name to assign or remove (if removeNamespace=True)
    :type namespaceName: str
    :param niceNameType: A single string from the list filterTypes.TYPE_FILTER_LIST, describes a type of node/s in Maya
    :type niceNameType: str
    :param removeNamespaces: Remove namespaces from the name?  Returned name will not have a namespace
    :type removeNamespaces: bool
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param searchHierarchy: Also search the hierarchy of the selected objects?
    :type searchHierarchy: bool
    :param selectionOnly: Only search within the current selection
    :type selectionOnly: bool
    :param dag: filter dag (viewport hierarchy) nodes only?
    :type dag: bool
    :param removeMayaDefaults: If not searching the selection will remove default Maya objects like persp and lambert1
    :type removeMayaDefaults: bool
    :param transformsOnly: filter out the shape nodes, usually True
    :type transformsOnly: bool
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    filteredObjList = filtertypes.filterByNiceType(niceNameType,
                                                   searchHierarchy=searchHierarchy,
                                                   selectionOnly=selectionOnly,
                                                   dag=dag,
                                                   removeMayaDefaults=removeMayaDefaults,
                                                   transformsOnly=transformsOnly,
                                                   message=message)
    if not filteredObjList:
        return  # should already produce a warning
    return createAssignNamespaceList(filteredObjList, namespaceName, removeNamespace=removeNamespace,
                                     renameShape=renameShape, message=message)


def removeNamespaceFromObj(objName, uuid=None, renameShape=True, message=True):
    """Removes the namespace from an object by renaming it.  Will leave the namespace in the scene.

    Remove Example:

        objName: "chair:pCube1"
        result: "pCube1"

    Multiple namespaces will also be removed

        objName: "scene1:chair:pCube1"
        result: "pCube1"

    :param objName: The current name of the object or node, can be long or unique names
    :type objName: str
    :param uuid: Optional unique hash identifier in case of long name issues while renaming hierarchies or re-parenting
    :type uuid: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param message: Report the message to the user?
    :type message: bool
    :return newNameList: The new names of the objects now potentially renamed
    :rtype newNameList: list
    """
    longPrefix, namespace, pureName = mayaNamePartTypes(objName)
    newName = mayaNamePartsJoin(longPrefix, "", pureName)
    return safeRename(objName, newName, uuid=uuid, renameShape=renameShape, message=message)


def removeNamespaceFromObjList(objNameList, renameShape=True, message=True):
    """Safe removes the namespace from an object by renaming it with UUIDs.  Will leave the namespace in the scene.

        Remove Example, for each item in list:

            objName: "chair:pCube1"
            result: "pCube1"

        Multiple namespaces will also be removed, for each item in list

            objName: "scene1:chair:pCube1"
            result: "pCube1"

        :param objNameList: The current name of the object or node, can be long or unique names
        :type objNameList: str
        :param renameShape: Also rename the shape node if a transform or joint?
        :type renameShape: bool
        :param message: Report the message to the user?
        :type message: bool
        :return newNameList: The new names of the objects now potentially renamed
        :rtype newNameList: list
        """
    return safeRenameList(objNameList, list(removeNamespaceLongnamesList(objNameList)), renameShape=True, message=False)


def emptyAndDeleteNamespace(namespaceName, renameShape=True, message=True):
    """Given a namespace name, remove it from the scene renaming all associated objects/nodes:

    Remove Example:

        objName: "chair:pCube1"
        result: "pCube1"
        deletedNamespace: "chair"

    Namespace may have namespace children and may not be removed in all cases

    :param namespaceName: The new or existing namespace name to assign or remove (if removeNamespace=True)
    :type namespaceName: str
    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param message: Report the message to the user?
    :type message: bool
    :return namespaceRemoved: True if the namespace was successfully removed
    :rtype namespaceRemoved: bool
    """
    # get all members of the namespace
    objList = cmds.namespaceInfo(namespaceName, listNamespace=True, fullName=True, dagPath=True)
    uuidList = cmds.ls(objList, uuid=True)
    if objList:  # remove them from the namespace
        for i, obj in enumerate(objList):
            removeNamespaceFromObj(obj, uuid=uuidList[i], renameShape=renameShape, message=message)
    try:  # remove the empty namespace
        cmds.namespace(removeNamespace=namespaceName)
        return True
    except RuntimeError:
        if message:
            om2.MGlobal.displayWarning("The current namespace '{}' "
                                       "is either not empty or not found".format(namespaceName))
        return False


def deleteSelectedNamespace(renameShape=True, message=True):
    """From the first selected object, remove the namespace from the scene.  Will affect all associated objects.

    Remove Example:

        selectedObjs[0]: "chair:pCube1"
        result: "pCube1"
        deletedNamespace: "chair"

    :param renameShape: Also rename the shape node if a transform or joint?
    :type renameShape: bool
    :param message: Report the message to the user?
    :type message: bool
    :return namespaceRemoved: True if the namespace was successfully removed
    :rtype namespaceRemoved: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected, please select an object with a namespace.")
            return
    selObj = selObjs[0]
    namespace = mayaNamePartTypes(selObj)[1]
    if not namespace:
        if message:
            om2.MGlobal.displayWarning("Namespace not found on first selected object '{}'".format(selObj))
            return
    success = emptyAndDeleteNamespace(namespace, renameShape=renameShape, message=message)
    if success:
        if message:
            om2.MGlobal.displayInfo("Namespace '{}' was emptied and deleted".format(namespace))
    else:
        if message:
            om2.MGlobal.displayInfo("Namespace could not be fully removed, see script editor".format(namespace))
    return success


# -------------------------
# NAMESPACES STRINGS ONLY - MISC
# -------------------------


def getNamespacesFromList(nodeList):
    """Gets the namespaces from a node list

    :param nodeList: list of maya node names, can be long or short
    :type nodeList: str
    :return namespaceList: A list of Maya namespacesFound
    :rtype namespaceList: list
    """
    namespaceList = list()
    for node in nodeList:
        if ":" in node:
            namespace = node.split(":")[0]
            if "|" in namespace:
                namespace = namespace.replace("|", "")
            namespaceList.append(namespace)
    return list(set(namespaceList))


def removeNamespaceFaceAssign(objFaces):
    """special case for namespaces in objectFace assigns as they may have a ":" colon

        NewNamespace1:pCube1.f[1:5]
        becomes
        pCube1.f[1:5]

    :param faceAssign: a maya object/face assign eg "NewNamespace1:pCube1.f[1:5]"
    :type faceAssign: str
    :return faceAssign: a maya obj/face assign, no namespace removed "pCube1.f[1:5]"
    :rtype faceAssign:
    """
    splitObjFace = objFaces.split("[")
    if ":" not in splitObjFace[0]:  # no namespace found
        return objFaces
    obj = splitObjFace[0].split(":")[-1]
    return "[".join([obj, splitObjFace[-1]])


def removeNamespaceShortName(nodeName, checkFaceAssign=False):
    """Removes a Maya namespace "name:" from a shortname string

    NOTE: This does not remove the actual namespace in Maya only the from the string name

    :param nodeName: a maya node short name, no "|"
    :type nodeName: str
    :param checkFaceAssign: this is True if the node is a obj/face assign eg "NewNamespace1:pCube1.f[1:5]"
    :type checkFaceAssign: bool
    :return nodeName: a maya node short name, no "|" now with no names space "nmspc:"
    :rtype nodeName: str
    """
    if ":" not in nodeName:
        return nodeName
    if checkFaceAssign:
        if "[" in nodeName:
            return removeNamespaceFaceAssign(nodeName)
    return nodeName.split(":")[-1]


def removeNamespaceLongnames(nodeLongName, checkFaceAssign=False, checkShortNames=False):
    """Removes a Maya namespace "name:" from a longname string

    NOTE:  This does not remove the actual namespace in Maya only the from the string name

    :param nodeLongName: a maya long name with "|" in the name
    :type nodeLongName: str
    :param checkFaceAssign: this is True if the node is a obj/face assign eg "NewNamespace1:pCube1.f[1:5]"
    :type checkFaceAssign: bool
    :param checkShortNames: use this flag if the list may also contain short names/longname mix
    :type checkShortNames: bool
    :return nodeLongName: a maya long name with "|" in the name, now with no namespaces
    :rtype nodeLongName: str
    """
    if checkShortNames:
        if "|" not in nodeLongName:
            return removeNamespaceShortName(nodeLongName, checkFaceAssign=checkFaceAssign)
    if ":" not in nodeLongName:
        return nodeLongName
    splitHierarchy = nodeLongName.split("|")
    for i, obj in enumerate(splitHierarchy):
        splitHierarchy[i] = removeNamespaceShortName(obj, checkFaceAssign=checkFaceAssign)
    return '|'.join(splitHierarchy)


def removeNamespaceShortNameList(nodeShortNameList, checkFaceAssign=False):
    """Removes a Maya namespace "name:" from a shortname list

    NOTE: This does not remove the actual namespace in Maya only the from the string names

    :param nodeShortNameList: list of maya shortname node names
    :type nodeShortNameList: list
    :param checkFaceAssign: this is True if the node is a obj/face assign eg "NewNamespace1:pCube1.f[1:5]"
    :type checkFaceAssign: bool
    :return nodeShortNameList: the list now with no namespaces
    :rtype nodeShortNameList: list
    """
    for i, nodeName in enumerate(nodeShortNameList):
        nodeShortNameList[i] = removeNamespaceShortName(nodeName, checkFaceAssign=checkFaceAssign)
    return nodeShortNameList


def removeNamespaceLongnamesList(nodeLongNameList, checkFaceAssign=False, checkShortNames=False):
    """Removes a Maya namespace "name:" from a longname list

    NOTE: This does not remove the actual namespace in Maya only the from the string names

    :param nodeLongNameList: list of Maya longname objects with "|" in the name
    :type nodeLongNameList: list
    :param checkFaceAssign: this is True if the node is a obj/face assign eg "NewNamespace1:pCube1.f[1:5]"
    :type checkFaceAssign: bool
    :param checkShortNames: use this flag if the list may also contain short names/longname mix
    :type checkShortNames: bool
    :return nodeLongNameList:  list of Maya longname objects with "|" in the name, now with namespaces removed
    :rtype nodeLongNameList: list
    """
    nodeLongNameListRtrn = list()  # needs to be a new list to avoid returning
    for i, nodeName in enumerate(nodeLongNameList):
        nodeLongNameListRtrn.append(removeNamespaceLongnames(nodeName, checkFaceAssign=checkFaceAssign,
                                                             checkShortNames=checkShortNames))
    return nodeLongNameListRtrn


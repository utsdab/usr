from maya import cmds
from maya.api import OpenMaya as om2

from zoovendor.six.moves import range

from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import plugs

shapeInfo = {"cvs": (),
             "degree": 3,
             "form": 1,
             "knots": (),
             "matrix": (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0),
             "outlinerColor": (0.0, 0.0, 0.0),
             "overrideColorRGB": (0.0, 0.0, 0.0),
             "overrideEnabled": False,
             "overrideRGBColors": False,
             "useOutlinerColor": False
             }


def getCurveData(shape, space=om2.MSpace.kObject):
    """From a given NurbsCurve shape node serialize the cvs positions, knots, degree, form rgb colours

    :param shape: MObject that represents the NurbsCurve shape
    :return: dict
    :param space:
    :type space: om2.MSpace

    .. code-block:: python

        nurbsCurve = cmds.circle()[1]
        # requires an MObject of the shape node
        data = curve_utils.getCurveData(api.asMObject(nurbsCurve))

    """
    if isinstance(shape, om2.MObject):
        shape = om2.MFnDagNode(shape).getPath()
    data = nodes.getNodeColourData(shape.node())
    curve = om2.MFnNurbsCurve(shape)
    # so we can deserialize in world which maya does in to steps
    data.update({"knots": tuple(curve.knots()),
                 "cvs": map(tuple, curve.cvPositions(space)),
                 "degree": curve.degree,
                 "form": curve.form,
                 "matrix": tuple(nodes.getWorldMatrix(curve.object()))})
    return data


def createCurveShape(parent, data):
    """Create a specified nurbs curves based on the data

    :param parent: The transform that takes ownership of the shapes, if None is supplied then one will be created
    :type parent: MObject
    :param data: {"shapeName": {"cvs": [], "knots":[], "degree": int, "form": int, "matrix": []}}
    :type data: dict
    :return: A 2 tuple the first element is the MObject of the parent and the second is a list /
    of mobjects represents the shapes created.
    :rtype: tuple(MObject, list(MObject))
    """
    if parent is None:
        parent = om2.MObject.kNullObj

    newCurve = om2.MFnNurbsCurve()
    newShapes = []
    for shapeName, curveData in iter(data.items()):
        cvs = om2.MPointArray(curveData["cvs"])  # om2 allows a list of lists which converts to om2.Point per element
        knots = curveData["knots"]
        degree = curveData["degree"]
        form = curveData["form"]
        enabled = curveData["overrideEnabled"]
        shape = newCurve.create(cvs, knots, degree, form, False, False, parent)
        newShapes.append(shape)
        if parent == om2.MObject.kNullObj and shape.apiType() == om2.MFn.kTransform:
            parent = shape
        if enabled:
            plugs.setPlugValue(newCurve.findPlug("overrideEnabled", False),
                               int(curveData["overrideEnabled"]))
            colours = curveData["overrideColorRGB"]
            outlinerColour = curveData.get("outlinerColor")
            nodes.setNodeColour(newCurve.object(),
                                colours,
                                outlinerColour=outlinerColour,
                                useOutlinerColour=curveData.get("useOutlinerColor", False)
                                )
    return parent, newShapes


def createCurveFromPoints(name, points, shapeDict=shapeInfo, parent=None):
    # create the shape name
    name = name + "Shape"
    # shapeData
    deg = 3
    ncvs = len(points)
    # append two zeros to the front of the knot count so it lines up with maya specs
    # (ncvs - deg) + 2 * deg - 1
    knots = [0, 0] + range(ncvs)
    # remap the last two indices to match the third from last
    knots[-2] = knots[len(knots) - deg]
    knots[-1] = knots[len(knots) - deg]
    shapeDict["cvs"] = points
    shapeDict["knots"] = knots
    return createCurveShape(parent, {name: shapeDict})


def serializeCurve(node, space=om2.MSpace.kObject):
    """From a given transform serialize the shapes curve data and return a dict

    :param node: The MObject that represents the transform above the nurbsCurves
    :type node: MObject
    :return: returns the dict of data from the shapes
    :rtype: dict
    """
    shapes = nodes.shapes(om2.MFnDagNode(node).getPath(), filterTypes=(om2.MFn.kNurbsCurve,))
    data = {}
    for shape in shapes:
        dag = om2.MFnDagNode(shape.node())
        isIntermediate = dag.isIntermediateObject
        if not isIntermediate:
            data[om2.MNamespace.stripNamespaceFromName(dag.name())] = getCurveData(shape, space=space)

    return data


def mirrorCurveCvs(curveObj, axis="x", space=None):
    """Mirrors the the curves transform shape cvs by a axis in a specified space

    :param curveObj: The curves transform to mirror
    :type curveObj: mobject
    :param axis: the axis the mirror on, accepts: 'x', 'y', 'z'
    :type axis: str
    :param space: the space to mirror by, accepts: MSpace.kObject, MSpace.kWorld, default: MSpace.kObject
    :type space: int

    :Example:

            nurbsCurve = cmds.circle()[0]
            mirrorCurveCvs(api.asMObject(nurbsCurve), axis='y', space=om.MSpace.kObject)

    """
    space = space or om2.MSpace.kObject

    axis = axis.lower()
    axisDict = {'x': 0, 'y': 1, 'z': 2}
    axisToMirror = set(axisDict[ax] for ax in axis)

    shapes = nodes.shapes(om2.MFnDagNode(curveObj).getPath())
    for shape in shapes:
        curve = om2.MFnNurbsCurve(shape)
        cvs = curve.cvPositions(space=space)
        # invert the cvs MPoints based on the axis
        for i in cvs:
            for ax in axisToMirror:
                i[ax] *= -1
        curve.setCVPositions(cvs)
        curve.updateCurve()


def iterCurvePoints(dagPath, count, space=om2.MSpace.kObject):
    """Generator Function to iterate and return the position, normal and tangent for the curve with the given point count.

    :param dagPath: the dagPath to the curve shape node
    :type dagPath: om2.MDagPath
    :param count: the point count to generate
    :type count: int
    :param space: the coordinate space to query the point data
    :type space: om2.MSpace
    :return: The first element is the Position, second is the normal, third is the tangent
    :rtype: tuple(MVector, MVector, MVector)
    """
    crvFn = om2.MFnNurbsCurve(dagPath)
    length = crvFn.length()
    dist = length / float(count - 1)  # account for end point
    current = 0.001
    maxParam = crvFn.findParamFromLength(length)
    defaultNormal = [1.0, 0.0, 0.0]
    defaultTangent = [0.0, 1.0, 0.0]
    for i in range(count):
        param = crvFn.findParamFromLength(current)
        # maya fails to get the normal when the param is the maxparam so we sample with a slight offset
        if param == maxParam:
            param = maxParam - 0.0001
        point = om2.MVector(crvFn.getPointAtParam(param, space=space))
        # in case where the curve is flat eg. directly up +y
        # this causes a runtimeError in which case the normal is [1.0,0.0,0.0] and tangent [0.0,1.0,0.0]
        try:
            yield point, crvFn.normal(param, space=space), crvFn.tangent(param, space=space)
        except RuntimeError:
            yield point, defaultNormal, defaultTangent
        current += dist


def matchCurves(driver, targets, space=om2.MSpace.kObject):
    """Function that matches the curves from the driver to all the targets.

    :param driver: the transform node of the shape to match
    :type driver: om2.MObject
    :param targets: A list of transform that will have the shapes replaced
    :type targets: list(om2.MObject) or tuple(om2.MObject)
    """
    driverdata = serializeCurve(driver, space)
    shapes = []
    for target in targets:
        cmds.delete([nodes.nameFromMObject(i.node()) for i in nodes.iterShapes(om2.MDagPath.getAPathTo(target))])
        shapes.extend(createCurveShape(target, driverdata)[1])
    return shapes


def curveCvs(dagPath, space=om2.MSpace.kObject):
    """Generator Function to iterate and return the position, normal and tangent for the curve with the given point count.

    :param dagPath: the dagPath to the curve shape node
    :type dagPath: om2.MDagPath
    :param space: the coordinate space to query the point data
    :type space: om2.MSpace
    :return: The first element is the Position, second is the normal, third is the tangent
    :rtype: tuple(om2.MPoint)
    """
    return om2.MFnNurbsCurve(dagPath).cvPositions(space=space)


def iterCurveParams(dagPath, count):
    """Generator Function to iterate and return the Parameter

    :param dagPath: the dagPath to the curve shape node
    :type dagPath: om2.MDagPath
    :param count: the Number of params to loop
    :type count: int
    :return: The curve param value
    :rtype: float
    """
    crvFn = om2.MFnNurbsCurve(dagPath)
    length = crvFn.length()
    dist = length / float(count)  # account for end point
    current = 0.1
    for i in range(count):
        yield crvFn.findParamFromLength(current)
        current += dist


def attachNodeToCurveAtParam(curve, node, param, name):
    """Attaches the given node to the curve using a motion path node.

    :param curve: nurbsCurve Shape to attach to
    :type curve: om2.MObject
    :param node: the node to attach to the curve
    :type node: om2.MObject
    :param param: the parameter float value along the curve
    :type param: float
    :param name: the motion path node name to use
    :type name: str
    :return: motion path node
    :rtype: om2.MObject
    """
    nodeFn = om2.MFnDependencyNode(node)
    crvFn = om2.MFnDependencyNode(curve)
    mp = nodes.createDGNode(name, "motionPath")
    mpFn = om2.MFnDependencyNode(mp)
    plugs.connectVectorPlugs(mpFn.findPlug("rotate", False), nodeFn.findPlug("rotate", False),
                             (True, True, True))
    plugs.connectVectorPlugs(mpFn.findPlug("allCoordinates", False), nodeFn.findPlug("translate", False),
                             (True, True, True))
    crvWorld = crvFn.findPlug("worldSpace", False)
    plugs.connectPlugs(crvWorld.elementByLogicalIndex(0), mpFn.findPlug("geometryPath", False))
    mpFn.findPlug("uValue", False).setFloat(param)
    mpFn.findPlug("frontAxis", False).setInt(0)
    mpFn.findPlug("upAxis", False).setInt(1)
    return mp


def iterGenerateSrtAlongCurve(dagPath, count, name):
    """Generator function to iterate the curve and attach transform nodes to the curve using a motionPath

    :param dagPath: the dagpath to the nurbscurve shape node
    :type dagPath: om2.MDagPath
    :param count: the number of transforms
    :type count: int
    :param name: the name for the transform, the motionpath will have the same name plus "_mp"
    :type name: str
    :return: Python Generator  first element is the created transform node, the second is the motionpath node
    :rtype: Generate(tuple(om2.MObject, om2.MObject))
    """
    curveNode = dagPath.node()
    for index, param in enumerate(iterCurveParams(dagPath, count)):
        transform = nodes.createDagNode(name, "transform")
        motionPath = attachNodeToCurveAtParam(curveNode, transform, param, "_".join([name, "mp"]))
        yield transform, motionPath

"""deformers.py
This modules handles maya native deformer queries including serializing weights etc.
"""
from maya.api import OpenMaya as om2
from maya.api import OpenMayaAnim as om2Anim

from zoovendor.six.moves import range

from zoo.libs.maya.api import scene
from zoo.libs.maya.api import generic
from zoo.libs.maya.api import nodes
from zoo.libs.utils import filesystem, zlogging

logger = zlogging.getLogger(__name__)


class SkinCluster(object):
    """Thin wrapper class around getting and setting skin weights
    """

    def __init__(self, cluster):
        """
        :param cluster: The skinCluster MObject
        :type cluster: om2.MObject
        """
        self.cluster = cluster
        self.mfn = om2Anim.MFnSkinCluster(cluster)
        self.shapeNode, self.component = geometryComponentsFromSet(self.mfn.deformerSet)

    def __getattr__(self, item):
        """Returns the MPlug from the skinCluster node

        :param item: the attribute Name
        :type item: str
        :rtype: om2.MPlug
        """
        fn = self.mfn
        if fn.hasAttribute(item):
            return fn.findPlug(item, False)
        return super(SkinCluster, self).__getattribute__(item)

    def influenceWeights(self):
        """Returns the influence objects data as a dict

        :return:
        :rtype: dict
        """
        influences = self.mfn.influenceObjects()
        influenceCount = len(influences)
        weights = self.mfn.getWeights(self.shapeNode, self.component, om2.MIntArray(range(influenceCount)))
        componentsPerInfluence = len(weights) / influenceCount
        influenceData = {}
        for i in range(influenceCount):
            partialName = generic.stripNamespaceFromName(influences[i].fullPathName())
            influenceData[partialName] = [weights[g * influenceCount + i] for g in range(componentsPerInfluence)]
        return influenceData

    def blendWeights(self):
        """Returns the blend weights of the cluster as a tuple
        :return:
        :rtype:
        """
        return tuple(self.mfn.getBlendWeights(self.shapeNode, self.component))

    def serialize(self):
        """ Serializes the skin cluster a dict

        :return:
        :rtype: dict
        """
        return {"name": self.mfn.name(),
                "weights": self.influenceWeights(),
                "blendWeights": self.blendWeights(),
                "normalized": self.normalizeWeights.asBool(),
                "skinningMethod": self.skinningMethod.asInt(),
                "maxInfluence": self.maxInfluences.asInt(),
                "maintainMaxInfluences": self.maintainMaxInfluences.asBool()}


def geometryComponentsFromSet(mobjectSet):
    """
    Returns the dagpath and geometry components from the maya set mobject
    """
    mfn = om2.MFnSet(mobjectSet)
    members = mfn.getMembers(flatten=False)  # selectionList
    if not members.length() > 0:
        return None, None
    return members.getComponent(0)


def skinClustersFromJoints(joints):
    """From a set of joints, find and retrieve the skinClusters as om2.MObject

    :param joints: a sequence of om2.MObjects representing kJoint
    :type joints: list or tuple(om2.MObject)
    :return: the retrieved skin clusters from the joints
    :rtype: list(om2.MObject)
    """
    clusters = []
    for jnt in joints:
        clusters.extend([dgIter.currentNode() for dgIter in
                         scene.dgIterator(jnt, om2.MFn.kSkinClusterFilter, om2.MItDependencyGraph.kDownStream)])
    return clusters


def clusterUpstreamFromNode(node):
    """Find's and returns the skin clusters upstream of the given node

    :param node: the DGNode to query
    :type node: om2.MObject
    :return: theA sequence of skin cluster nodes
    :rtype: list(om2.MObject)
    """
    return [dgIter.currentNode() for dgIter in
            scene.dgIterator(node, om2.MFn.kSkinClusterFilter, om2.MItDependencyGraph.kUpstream)]


def serializeClusters(clusters):
    """For the given skin clusters, serialize them to a dict

    :param clusters: A sequence of MObjects representing the skinClusters
    :type clusters: list(om2.MObject)
    :rtype: list(dict)
    """
    return [SkinCluster(cluster).serialize() for cluster in clusters]


def serializeSkinWeightsFromShapes(shapes):
    """Serialize's the geometry shape skinCluster weights to a dict

    :example:
        
        {my|objectName: {"points":   [[11.720806121826172,11.951449566072865,0.47714900970458984,1]],
            "skinData": [{
                "name": "roboRig:skinCluster_hand01_L",
                "maxInfluence": 5,
                "maintainMaxInfluences": true,
                "skinningMethod": 0,
                "weights": {
                    "|L_wrist": [1,0,1,0]
                    }]
                    }
        }
    
    :param shapes: The MObjects representing the shape nodes to serialize
    :type shapes: om2.MObject 
    :rtype: dict
    """

    data = {}
    for sh in shapes:
        clusters = clusterUpstreamFromNode(sh)
        if not clusters:
            continue
        fn = om2.MFnMesh(om2.MFnDagNode(sh).getPath())
        data[generic.stripNamespaceFromName(nodes.nameFromMObject(sh))] = {
            "points": map(tuple, fn.getPoints(om2.MSpace.kWorld)),
            "skinData": serializeClusters(clusters)
            }
    return data


def applyWeightsFromData(data, shape):
    pass


def createAndImportWeightsFromShapes(filePath, shapes):
    """Loads the skin data from the filePath and loads it on the shapeNodes.

    If any of the shapes have existing skinClusters then the weights will be replaced.
    Otherwise a skin cluster will be created.

    :param filePath: The json file to load, must be in the same format as the return data of :func:`serialzieSkinWeightsFromShapes`
    :type filePath: str
    :param shapes: list of om2.MObjects representing the geometry shape nodes to load the data onto
    :type shapes: [type]
    """

    # read in the json
    skinInfo = filesystem.loadJson(filePath)
    if not skinInfo:
        logger.error("Failed to load skin file: {}".format(filePath))
        raise RuntimeError("Failed to load skin file: {}".format(filePath))

    # ok now grab the mapping between the dataFile and the shape nodes this is done by name
    # :todo: custom mapping
    for shape in shapes:
        path = om2.MDagPath.getAPathTo(shape)
        name = generic.stripNamespaceFromName(path.fullPathName())
        mappedInfo = skinInfo.get(name)
        if mappedInfo is None:
            print("Skipping: {} since it doesn't exist")
            continue
        applyWeightsFromData(mappedInfo, path)

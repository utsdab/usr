from zoo.libs.utils import general
from zoo.libs.maya.meta import base


class MetaRigBase(base.MetaBase):
    icon = "user"
    SUPPORTSYSTEMATTR = "supportSystem"
    SUBSYSTEMATTR = "subSystem"

    def filterSubSystemByName(self, name):
        for subsys in iter(self.subSystems()):
            if subsys.name() == name:
                return subsys
        return None

    def filterSupportSystemByName(self, name):
        for subsys in iter(self.supportSystems()):
            if subsys.name() == name:
                return subsys
        return None

    def isSubSystem(self):
        return isinstance(self, MetaSubSystem)

    def isSupportSystem(self):
        return isinstance(self, MetaSupportSystem)

    def hasSupportSystemByName(self, name):
        for subsys in iter(self.supportSystems()):
            if subsys.name.name() == name:
                return True
        return False

    def hasSubSystemName(self, name):
        for subsys in iter(self.subSystems()):
            if subsys.name() == name:
                return True
        return False

    def addSupportSystem(self, node=None, name=None):
        if node is None:
            name = "{}_#".format(MetaRig.SUPPORTSYSTEMATTR) if not name else "_".join([name, "meta"])
            node = MetaSupportSystem(name=name).object()

        self.connectTo(MetaRig.SUPPORTSYSTEMATTR, node.mobject())

        return node

    def addSubSystem(self, node=None, name=None):
        if node is None:
            node = MetaSubSystem(name=name)

        self.connectTo(MetaRig.SUBSYSTEMATTR, node.mobject())

        return node

    def supportSystems(self):
        if isinstance(self, MetaSupportSystem):
            return
        return list(self.iterSupportSystems())

    def iterSupportSystems(self):
        if isinstance(self, MetaSubSystem) or self._mfn.hasAttribute(MetaRig.SUPPORTSYSTEMATTR):
            return
        plug = self.attribute(MetaRig.SUPPORTSYSTEMATTR)
        if not plug.isSource:
            return
        connections = plug.destinations()
        for i in connections:
            yield MetaSupportSystem(i.node().object())

    def iterSubSystems(self):
        if isinstance(self, MetaSubSystem) or not self.hasAttribute(MetaRig.SUBSYSTEMATTR):
            return
        plug = self.attribute(MetaRig.SUBSYSTEMATTR)
        if not plug.isSource:
            return
        connections = plug.destinations()
        for i in connections:
            yield MetaSubSystem(i.node().object())

    def subSystems(self):
        if isinstance(self, MetaSubSystem):
            return
        return list(self.iterSubSystems())


class MetaRig(MetaRigBase):
    pass


class MetaSupportSystem(MetaRigBase):
    pass


class MetaSubSystem(MetaRigBase):
    pass


class MetaFaceRig(MetaRigBase):
    pass


def findDuplicateRigInstances():
    """Searches all MetaRigs and checks the rigName for duplicates.

    :return: list of duplicate metaRig instances.
    :rtype: list(MetaRig)
    """
    metaRigs = [(i, i.rigName) for i in findRigs()]
    duplicates = general.getDuplicates([i[1] for i in metaRigs])
    return [i[0] for i in metaRigs if i in duplicates]


def findRigs():
    return base.findMetaNodesByClassType(MetaRig.__name__)

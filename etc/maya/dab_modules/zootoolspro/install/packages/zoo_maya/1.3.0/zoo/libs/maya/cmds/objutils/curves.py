import maya.mel as mel


def createCurveContext(degrees=3, bezier=0):
    """Enters the create curve context (user draws cvs).  Uses mel. Cubic Has option for curve degrees.

    More options can be added later.

    :param degrees: The curve degrees of the curve.  3 is Bezier, 1 is linear.
    :type degrees: int
    :param bezier: when the curves has 3 degrees make the curve bezier.  Default 0 is cubic.
    :type bezier: int
    """
    mel.eval("curveCVToolScript 4;\n"
             "curveCVCtx -e -d {} -bez {} `currentCtx`;".format(str(degrees), str(bezier)))


from maya import cmds


def playbackRangeStartToCurrentFrame(animationStartTime=True):
    """Sets the range slider start to be the current frame in time

    :param animationEndTime: if True sets the range to be the entire range, False is playback range only
    :type animationStartTime: bool
    """
    theCurrentTime = cmds.currentTime(query=True)
    if animationStartTime:
        cmds.playbackOptions(animationStartTime=theCurrentTime)
    else:
        cmds.playbackOptions(minTime=theCurrentTime)


def playbackRangeEndToCurrentFrame(animationEndTime=True):
    """Sets the range slider end to be the current frame in time

    :param animationEndTime: if True sets the range to be the entire range, False is playback range only
    :type animationEndTime: bool
    """
    theCurrentTime = cmds.currentTime(query=True)
    if animationEndTime:
        cmds.playbackOptions(animationEndTime=theCurrentTime)
    else:
        cmds.playbackOptions(maxTime=theCurrentTime)


def animMoveTimeForwardsBack(frames):
    """Moves the time slider back or forwards by these amount of frames.  Can be a negative number for backwards.

    :param frames: The amount of frames to offset from current time
    :type frames: float
    """
    theCurrentTime = cmds.currentTime(query=True)
    cmds.currentTime(theCurrentTime + frames)

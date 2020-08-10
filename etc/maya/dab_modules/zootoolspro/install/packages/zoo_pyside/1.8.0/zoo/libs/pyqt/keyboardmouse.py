from Qt import QtWidgets, QtCore


def cntrlShiftMultiplier(shiftMultiply=5.0, ctrlMultiply=0.2, altMultiply=1.0):
    """For offset functions multiply (shift) and minimise if (ctrl) is held down
    If (alt) then call the reset option

    :return multiplier: multiply value, 0.2 if ctrl 5.0 if shift 1.0 if None
    :rtype multiplier: float
    :return reset: Reset becomes True while resetting for alt
    :rtype reset: bool
    """
    modifiers = QtWidgets.QApplication.keyboardModifiers()
    if modifiers == QtCore.Qt.ShiftModifier:  # usually accelerate * 5.0
        return shiftMultiply, False
    elif modifiers == QtCore.Qt.ControlModifier:  # usually decelerate * 0.2
        return ctrlMultiply, False
    elif modifiers == QtCore.Qt.AltModifier:  # usually decelerate * 1.0 and reset is True
        return altMultiply, True
    return 1.0, False  # regular click


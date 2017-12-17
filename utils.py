import os
import math
from maya import cmds, mel, OpenMayaUI
from maya.api import OpenMaya

# import pyside, do qt version check for maya 2017 >
qtVersion = cmds.about(qtVersion=True)
if qtVersion.startswith("4") or type(qtVersion) not in [str, unicode]:
    from PySide.QtGui import *
    from PySide.QtCore import *
    import shiboken
else:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    import shiboken2 as shiboken
    
# ----------------------------------------------------------------------------

class UndoChunkContext(object):
    """
    The undo context is used to combine a chain of commands into one undo.
    Can be used in combination with the "with" statement.
    
    with UndoChunkContext():
        # code
    """
    def __enter__(self):
        cmds.undoInfo(openChunk=True)
        
    def __exit__(self, *exc_info):
        cmds.undoInfo(closeChunk=True)
    
# ----------------------------------------------------------------------------

FONT = QFont()
FONT.setFamily("Consolas")

BOLT_FONT = QFont()
BOLT_FONT.setFamily("Consolas")
BOLT_FONT.setWeight(100)  

# ----------------------------------------------------------------------------

def mayaWindow():
    """
    Get Maya's main window.
    
    :rtype: QMainWindow
    """
    window = OpenMayaUI.MQtUtil.mainWindow()
    window = shiboken.wrapInstance(long(window), QMainWindow)
    
    return window  
    
def getMayaTimeline():
    """
    Get the object name of Maya's timeline.
    
    :return: Object name of Maya's timeline
    :rtype: str
    """
    return mel.eval("$tmpVar=$gPlayBackSlider")
    
# ----------------------------------------------------------------------------
    
def findIcon(icon):
    """
    Loop over all icon paths registered in the XBMLANGPATH environment 
    variable ( appending the tools icon path to that list ). If the 
    icon exist a full path will be returned.

    :param str icon: icon name including extention
    :return: icon path
    :rtype: str or None
    """
    paths = []

    # get maya icon paths
    if os.environ.get("XBMLANGPATH"):     
        paths = os.environ.get("XBMLANGPATH").split(os.pathsep)                                 

    # append tool icon path
    paths.insert(
        0,
        os.path.join(
            os.path.split(__file__)[0], 
            "icons" 
        ) 
    )

    # loop all potential paths
    for path in paths:
        filepath = os.path.join(path, icon)
        if os.path.exists(filepath):
            return filepath
            
# ----------------------------------------------------------------------------
            
def displayConfirmDialog(invalidAttributes):
    """
    Display confirm dialog, presenting the user with the invalid attributes
    that were found.

    :param list invalidAttributes: List of invalid attributes
    :return: Continue state
    :rtype: bool
    """
    # construct message
    message = "{0}\n{1}\n\n{2}\n\n{3}".format(
        "The following invalid attributes where found",
        "and will be ignored!",
        "\n".join(invalidAttributes),
        "Would you like to continue?"
    )
    
    # create dialog
    ret = QMessageBox.warning(
        mayaWindow(), 
        "Invalid Attributes",
        message,
        QMessageBox.Ok | QMessageBox.Cancel
    )
    
    # return results
    if ret == QMessageBox.Ok:
        return True
        
    return False

# ----------------------------------------------------------------------------

ATTRIBUTES = ["translate", "rotate", "scale"]
CHANNELS = ["X", "Y", "Z"]

# ----------------------------------------------------------------------------

def getInvalidAttributes(transform):
    """
    Loop over the transform attributes of the transform and see if the 
    attributes are locked or connected to anything other than a animation 
    curve. If this is the case the attribute is invalid.
    
    :param str transform: Path to transform
    :return: List of invalid attributes.
    :rtype: list
    """
    invalidChannels = []
    for attr in ATTRIBUTES:
        # get connection of parent attribute
        node = "{0}.{1}".format(transform, attr)
        if cmds.listConnections(node, destination=False):
            invalidChannels.extend(
                [
                    node + channel
                    for channel in CHANNELS
                ]
            )
            continue

        # get connection of individual channels
        for channel in CHANNELS:
            node = "{0}.{1}{2}".format(transform, attr, channel)
            
            # get connections
            animInputs = cmds.listConnections(
                node, 
                type="animCurve",
                destination=False
            )
            allInputs = cmds.listConnections(
                node,
                destination=False,
            )
            
            # check if connections are not of anim curve type
            locked = cmds.getAttr(node, lock=True)
            if (not animInputs and allInputs) or locked:
                invalidChannels.append(node)
                
    return invalidChannels

# ----------------------------------------------------------------------------

def getMatrix(transform, time=None, matrixType="worldMatrix"):
    """
    Get the matrix of the desired matrix type from the transform in a specific
    moment in time. If the transform doesn't exist an empty matrix will be 
    returned. If not time is specified, the current time will be used.
    
    :param str transform: Path to transform
    :param float/int time: Time value
    :param str matrixType: Matrix type to query
    :return: Matrix
    :rtype: OpenMaya.MMatrix
    """
    if not transform:
        return OpenMaya.MMatrix()
        
    if not time:
        time = cmds.currentTime(query=True)
    
    rotatePivot = cmds.getAttr("{0}.rotatePivot".format(transform))[0]
    
    matrix = cmds.getAttr("{0}.{1}".format(transform, matrixType), time=time)
    return OpenMaya.MMatrix(matrix)
    
def decomposeMatrix(matrix, rotOrder, rotPivot):
    """
    Decompose a matrix into translation, rotation and scale values. A 
    rotation order has to be provided to make sure the euler values are 
    correct.
    
    :param OpenMaya.MMatrix matrix:
    :param int rotOrder: Rotation order
    :param list rotPivot: Rotation pivot
    :return: Translate, rotate and scale values
    :rtype: list
    """
    matrixTransform = OpenMaya.MTransformationMatrix(matrix)
    
    # set pivots
    matrixTransform.setRotatePivot(
        OpenMaya.MPoint(rotPivot), 
        OpenMaya.MSpace.kTransform, 
        True
    )
    
    # get rotation pivot translation
    posOffset =  matrixTransform.rotatePivotTranslation(
        OpenMaya.MSpace.kTransform
    )
    
    # get pos values
    pos = matrixTransform.translation(OpenMaya.MSpace.kTransform)
    pos += posOffset
    pos = [pos.x, pos.y, pos.z]
    
    # get rot values
    euler = matrixTransform.rotation()
    euler.reorderIt(rotOrder)
    rot = [math.degrees(angle) for angle in [euler.x, euler.y, euler.z]]
    
    # get scale values
    scale = matrixTransform.scale(OpenMaya.MSpace.kTransform)
    
    return [pos, rot, scale]
    
# ----------------------------------------------------------------------------

def getInTangent(animCurve, time):
    """
    Query the in tangent type of the key frame closest but higher than the 
    parsed time. 
    
    :param str animCurve: Animation curve to query
    :param int time:
    :return: In tangent type
    :rtype: str
    """
    times = cmds.keyframe(animCurve, query=True, timeChange=True) or []
    for t in times:
        if t <= time:
            continue
        
        tangent = cmds.keyTangent(
            animCurve, 
            time=(t,t), 
            query=True, 
            inTangentType=True
        )
        
        return tangent[0]

    return "auto"
    
def getOutTangent(animCurve, time):
    """
    Query the out tangent type of the key frame closest but lower than the 
    parsed time. 
    
    :param str animCurve: Animation curve to query
    :param int time:
    :return: Out tangent type
    :rtype: 
    """
    times = cmds.keyframe(animCurve, query=True, timeChange=True) or []
    for t in times:
        if t >= time:
            continue
        
        tangent = cmds.keyTangent(
            animCurve, 
            time=(t,t), 
            query=True, 
            outTangentType=True
        )
        
        return tangent[0]

    return "auto"
    
    
    
    

"""		
Anchor transforms in Maya.

.. figure:: https://github.com/robertjoosten/rjAnchorTransform/raw/master/README.gif
   :align: center
   
`Link to Video <https://vimeo.com/247672481>`_

Installation
============
Copy the **rjAnchorTransform** folder to your Maya scripts directory
::
    C:/Users/<USER>/Documents/maya/scripts

Usage
=====
Command Line
::
    import rjAnchorTransform
    rjAnchorTransform.anchorTransform(transform, driver, start, end)
    
Display UI
::
    import rjAnchorTransform.ui 
    rjAnchorTransform.ui.show()

Note
====
Anchor a transform to world space for a specific time range. Can be used to 
fix sliding feet on a walk cycle. The script uses the Maya API to calculate
local transforms to be key framed, by doing this there is no need to loop over 
the animation greatly speeding up the work flow. Existing in and out tangents 
will be copied when new key frames are inserted. Once all keys are set an 
euler filter is applied to the animation curves connected to the rotate
attributes.

Animation Demo Credits
====
rig: `Harry Gladwin-Geoghegan <https://www.highend3d.com/maya/downloads/character-rigs/c/dinorig-for-maya>`_
animation: `Jonathan Symmonds <http://jonathansymmonds.com/downloads_section/>`_

Code
====
"""

from maya import cmds
from maya.api import OpenMaya
from . import utils

__author__    = "Robert Joosten"
__version__   = "0.1.0"
__email__     = "rwm.joosten@gmail.com"
   
# ----------------------------------------------------------------------------

TANGENTS = [
    "auto", "clamped", "fast", 
    "flat", "linear", "plateau", 
    "slow", "spline", "stepnext"
]

# ----------------------------------------------------------------------------

def anchorSelection(driver, start, end):
    """
    Anchor the selected transform for the parsed time range. Uses the 
    :func:`anchorTransform` function. The selected transforms will be checked
    to see if all attribute channels are open for key frame if this is not 
    the case a dialog box will ask for the users permission to continue.
    
    :param str driver: Path to the driver transform
    :param int start: Start time value
    :param int end: End time value
    """
    invalidChannels = []
    
    # get selection
    transforms = cmds.ls(sl=True, transforms=True) or [] 
    
    # make sure the driver is not inside the transforms list
    transforms = [t for t in transforms if not t == driver]
    
    # check for invalid selection
    for transform in transforms:
        invalidChannels.extend(
            utils.getInvalidAttributes(transform)
        )
     
    if invalidChannels:
        if not utils.displayConfirmDialog(invalidChannels):
            return 
    
    # anchor transforms
    for transform in transforms:
        anchorTransform(transform, driver, start, end)
        
def anchorTransform(transform, driver, start, end):
    """
    Anchor a transform for the parsed time range, ideal to fix sliding feet. 
    Function will take into account the in and out tangents in case the 
    transform is already animated. 
    
    :param str transform: Path to transform
    :param str driver: Path to the driver transform
    :param int start: Start time value
    :param int end: End time value
    """ 
    # wrap in an undo chunk
    with utils.UndoChunkContext():
        # get parent
        rotOrder = cmds.getAttr("{0}.rotateOrder".format(transform))
        
        # get driver matrix
        driverInverseMatrix = utils.getMatrix(
            driver,
            start,
            "worldInverseMatrix"
        )

        # get start matrix
        anchorMatrix = utils.getMatrix(
            transform,
            start,
            "worldMatrix"
        )
        
        # get invalid attributes
        invalidAttributes = utils.getInvalidAttributes(transform)
        
        # key frame attributes
        for i in range(start, end+1):
            # get driver and transform matrices
            driverMatrix = utils.getMatrix(
                driver,
                i,
                "worldMatrix"
            )

            inverseMatrix = utils.getMatrix(
                transform, 
                i, 
                "parentInverseMatrix"
            )

            # get driver matrix difference
            differenceMatrix = driverInverseMatrix * driverMatrix

            # get local matrix
            localMatrix = differenceMatrix * anchorMatrix * inverseMatrix
                    
            # extract transform values from matrix
            rotPivot = cmds.getAttr("{0}.rotatePivot".format(transform))[0]   
            transformValues = utils.decomposeMatrix(
                localMatrix, 
                rotOrder, 
                rotPivot,
            )
            
            for attr, value in zip(utils.ATTRIBUTES, transformValues):
                for j, channel in enumerate(utils.CHANNELS):
                    # variables
                    node = "{0}.{1}{2}".format(transform, attr, channel)
                    tangents = {
                        "inTangentType": "linear",
                        "outTangentType": "linear"
                    }
                    
                    # skip if its an invalid attribute
                    if node in invalidAttributes:
                        continue
                    
                    # check if input connections are
                    animInputs = cmds.listConnections(
                        node, 
                        type="animCurve",
                        destination=False
                    )

                    # adjust tangents
                    if animInputs and i == end:
                        tangent = utils.getOutTangent(
                            animInputs[0], 
                            end
                        )
                        
                        if tangent in TANGENTS:
                            tangents["outTangentType"] = tangent
                            
                    elif animInputs and i == start:
                        tangent = utils.getInTangent(
                            animInputs[0], 
                            start
                        )
                        
                        if tangent in TANGENTS:
                            tangents["inTangentType"] = tangent
                        
                    # set key frame
                    cmds.setKeyframe(
                        node, 
                        t=i, 
                        v=value[j],
                        **tangents
                    )
        
        # apply euler filter
        utils.applyEulerFilter(transform)

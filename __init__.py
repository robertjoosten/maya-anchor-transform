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
    rjAnchorTransform.anchorTransform(transform, start, end)
    
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
will be copied when new key frames are inserted.

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

def anchorSelection(start, end):
    """
    Anchor the selected transform for the parsed time range. Uses the 
    :func:`anchorTransform` function. The selected transforms will be checked
    to see if all attribute channels are open for key frame if this is not 
    the case a dialog box will ask for the users permission to continue.
    
    :param int start: Start time value
    :param int end: End time value
    """
    invalidChannels = []
    
    # get selection
    transforms = cmds.ls(sl=True, transforms=True) or []
    
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
        anchorTransform(transform, start, end)
    
def anchorTransform(transform, start, end):
    """
    Anchor a transform for the parsed time range, ideal to fix sliding feet. 
    Function will take into account the in and out tangents in case the 
    transform is already animated. 
    
    :param str transform: Path to transform
    :param int start: Start time value
    :param int end: End time value
    """ 
    # wrap in an undo chunk
    with utils.UndoChunkContext():
        # get parent
        rotOrder = cmds.getAttr("{0}.rotateOrder".format(transform))

        # get start matrix
        anchorMatrix = utils.getMatrix(transform, start, "worldMatrix")
        
        # get invalid attributes
        invalidAttributes = utils.getInvalidAttributes(transform)
        
        # key frame attributes
        for i in range(start,end+1):
            # get local matrix
            inverseMatrix = utils.getMatrix(
                transform, 
                i, 
                "parentInverseMatrix"
            )
            
            localMatrix = anchorMatrix * inverseMatrix
                    
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
                        tangents["outTangentType"] = utils.getOutTangent(
                            animInputs[0], 
                            end
                        )
                    elif animInputs and i == start:
                        tangents["inTangentType"] = utils.getInTangent(
                            animInputs[0], 
                            start
                        )
                            
                    # set key frame
                    cmds.setKeyframe(
                        node, 
                        t=i, 
                        v=value[j],
                        **tangents
                    )

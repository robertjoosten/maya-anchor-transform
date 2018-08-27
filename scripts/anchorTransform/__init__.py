"""		
Anchor transforms to world or object space in Maya.

.. figure:: /_images/anchorTransformExample.gif
   :align: center
   
`Link to Video <https://vimeo.com/247672481>`_

Installation
============
* Extract the content of the .rar file anywhere on disk.
* Drag the anchorTransform.mel file in Maya to permanently install the script.

Note
====
Anchor a transform to world or object space for a specific time range. Can be
used to fix sliding feet on a walk cycle. The script uses the Maya API to
calculate local transforms to be key framed, by doing this there is no need to
loop over the animation greatly speeding up the work flow. Existing in and out
tangents will be copied when new key frames are inserted. Once all keys are
set an euler filter is applied to the animation curves connected to the rotate
attributes.
"""
from .commands import anchorSelection, anchorTransform

__author__    = "Robert Joosten"
__version__   = "0.1.1"
__email__     = "rwm.joosten@gmail.com"

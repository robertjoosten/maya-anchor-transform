# maya-anchor-transform
<img align="right" src="icons/AT_icon.png?raw=true">
Anchor transforms to world or object space in Maya.

<p align="center"><img src="docs/_images/anchorTransformExample.gif?raw=true"></p>
<a href="https://vimeo.com/247672481" target="_blank"><p align="center">Click for video</p></a>

## Installation
* Extract the content of the .rar file anywhere on disk.
* Drag the anchorTransform.mel file in Maya to permanently install the script.

## Note
Anchor a transform to world or object space for a specific time range. Can be used to fix sliding feet on a walk cycle. The script uses the Maya API to calculate local transforms to be key framed, by doing this there is no need to loop over the animation greatly speeding up the work flow. Existing in and out tangents will be copied when new key frames are inserted. Once all keys are set an euler filter is applied to the animation curves connected to the rotate attributes.

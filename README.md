# rjAnchorTransform
Anchor transforms in Maya.

<p align="center"><img src="https://github.com/robertjoosten/rjAnchorTransform/raw/master/README.gif"></p>
<a href="https://vimeo.com/247672481" target="_blank"><p align="center">Click for video</p></a>

## Installation
Copy the **rjAnchorTransform** folder to your Maya scripts directory:
> C:\Users\<USER>\Documents\maya\scripts

## Usage
Command line:
```python
import rjAnchorTransform
rjAnchorTransform.anchorTransform(transform, start, end)
```

Display UI:
```python
import rjAnchorTransform.ui 
rjAnchorTransform.ui.show()
```

## Note
Anchor a transform to world space for a specific time range. Can be used to fix sliding feet on a walk cycle. The script uses the Maya API to calculate local transforms to be key framed, by doing this there is no need to loop over the animation greatly speeding up the work flow. Existing in and out tangents will be copied when new key frames are inserted.

## Animation Demo Credits
rig: <a href="https://www.highend3d.com/maya/downloads/character-rigs/c/dinorig-for-maya" target="_blank"><p align="left">Harry Gladwin-Geoghegan</p></a>
animation: <a href="http://jonathansymmonds.com/downloads_section/" target="_blank"><p align="left">Jonathan Symmonds</p></a>
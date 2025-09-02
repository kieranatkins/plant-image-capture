# plant-image-capture
Allows controlling standardised imaging equipment for plant image capture, inc. GUI.

## Requirements
The software runs in python, using the `gphoto2` library for camera control, `PyQt5` for the GUI, and `pandas` for experimental CSV input.

To install these packages run the command ```python -m pip install gphoto2 pandas pyqt5```.

## Running
To run the software, run the command ```python plant_image_capture.py```.

## Known bugs
* Do not use the '/' character in any of the filename fields as this will break the file save path.

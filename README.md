__General information__

This is the source code written in python specifically designed for the Quantum Diamond Microscope (QDM) project located in MRL UIUC,
which is an imaging magnetometer based on Nitrogen-Vacancy (NV) center.
Code is compatible with the use of Stanford Research System instruments (including the lock-in amplifier SR series, e.g.SR830) and
Pypylon camera. If using the code for other similar purposes, it can be easily modified by changing the devices identified by the pyvisa package.

__package description__
This package includes the main program and all the other accompanying Python scripts that may or may not be used with the main file. __main.py__ initializes all the instruments connected and parameters needed. It also takes measurement automatically and creates 1-D contrast plot depicting the changes in the NV fluorecence intensity along with the generated magnetic image. We use this code most often for this project as to see if the signal to noise ratio is enough
to create a reasonably clear magnetic image that shows the relative magnitude of local magnetic field domains. The code can be modified to show the polarity of magnetic fields as well, which will be described in more detail below. __Quantitative measurement.py__ is a developing script that can be used indepedently of the main program. Similar to the main program, it generates magnetic image showing the domain infomration of sample used, but additionaly, it is capable of showing the quantitative values of the fields as measured from the experiment. However,this code needs a very high signal-to-noise ratio in order to work appropriately, and thus, is rarely used. Lastly, __Histogram equalization.py__ is the script used to enhance the image contrast quality. Under low signal to noise ratio condition, we can use this script to obtain a better image as created from main.py. Script can be used either by calling in main.py or as post-measurement tool.

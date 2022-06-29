## General information

This is the source code written in python specifically designed for the Quantum Diamond Microscope (QDM) project located in MRL UIUC,
which is an imaging magnetometer based on Nitrogen-Vacancy (NV) center.
Code is compatible with the use of Stanford Research System instruments (including the lock-in amplifier SR series, e.g.SR830) and
Pypylon camera. If using the code for other similar purposes, it can be easily modified by changing the devices identified by the pyvisa package.

## Package description

This package includes the main program and all the other accompanying Python scripts that may or may not be used with the main file. __main.py__ initializes all the instruments connected and parameters needed. It also takes measurement automatically and creates 1-D contrast plot depicting the changes in the NV fluorecence intensity along with the generated magnetic image. We use this code most often for this project as to see if the signal to noise ratio is enough
to create a reasonably clear magnetic image that shows the relative magnitude of local magnetic field domains. The code can be modified to show the polarity of magnetic fields as well, which will be described in more detail below. __Quantitative measurement.py__ is a developing script that can be used indepedently of the main program. Similar to the main program, it generates magnetic image showing the domain infomration of sample used, but additionaly, it is capable of showing the quantitative values of the fields as measured from the experiment. However,this code needs a very high signal-to-noise ratio in order to work appropriately, and thus, is rarely used. Lastly, __Histogram equalization.py__ is the script used to enhance the image contrast quality. Under low signal to noise ratio condition, we can use this script to obtain a better image as created from main.py. Script can be used either by calling in main.py or as post-measurement tool.

__NOTE:__ package is used with python version at least 3.0.0, to use properly with all the functions, some other python packages may be installed firstly: 1.__pyvisa__, https://pyvisa.readthedocs.io/en/latest/introduction/getting.html
2.__pypylon__, https://github.com/basler/pypylon
3.__mpl_toolkits.axes_grid1.anchored_artists__, 
4.__PIL__. 
If you download Python from anaconda distribution, the other necessary packages should be included automatically. 

## How to use the files

Before using the files, make sure that the instrument has been connected properly, including the lock-in aplifier SR830 used at MRL, Pypyler camera, power supply. To verify, simply run the code main.py, if the instrument is not connected, error code will be displayed for respective disconnections. If no error code is displayed, then we can proceed with the following steps.
To be concise, a few __key lines__ will be introduced in __main.py__:
1. line 57: this sets the __camera acquisition time__. A high acquisition time will make the camera image saturate and will not be of any value; on the other hand, a low acquisition time may make the signal not strong enough to create good-quality image. To determine the appropriate acquisition time, open "Pylon Viewer" software, and manually set different acquisition time to see which one can create moderate brightness (usually at least 100 and at most 220 for maximum pixel intensity in 8-bit scale). Note that the value entered is in unit of microseconds (us).
2. line 70: this sets the __power output for MW coil__. A higher power usually has a better signal to noise ratio, but also a wider bandwidth (dip) in 1-D contrast plot, lowering the sensitivity. But given the current setup, it is recommended to use the maximum power, and therefore, it is usually not needed to change this line.
3. lines 73-75: these lines set the __MW coil frequency scan parameters and number of trials to perform in a single measurement__. In particular, line 73 is used in frequency scan, while line 74 is used as a "probe frequency" to get faster measurement and has many purposes. Overall, I recommend comment line 74 firstly to get a 1-D contrast plot that shows how the fluoresence signal changes as a function of MW coil frequency. Then choose a frequency where the dip position is (usually when no bias field is applied from the Helmholtz coil, use 2.87 GHz; if a bias field is applied, use the frequency that corresponds to side dips) for line 74 and uncomment the line to get a fast magnetic image generation. Line 75 is used to increase/decrease signal strength (image quality)/total session time.
4. lines 121-124: these set the __region boundaries on the image to integrate for 1-D contrast plotting__. In other words, to get a better 1-D contrast plotting, a larger region should be chosen, but it also mix signals from different areas on the sample. For signal purpose, either choose to increase the number of trials performed as in line 75, or increase the region selected. As for how to set the value, refer to the comment behind these lines.
5. lines 271-272: these set the __desired pixels you want for the generated magnetic image__. Usually, to gain a moderate quality image, we need at least a 5 times 5 superpixel from the original acquired image, and thus, the resolution for the new generated image will be 384×240 in this case. You can set any value you want for these numbers to obtain different images.

These parameters should be enough to begin the experiment. Under most circumstances, no action is needed to change the other parts of the code, but it is always welcome to modify as you may need. To run "Histogram equalization.py" script, uncomment line 392; to obtain a polarity magnetic image, apply bias field using the power supply panel for the Helmholtz coil, and take a scan plot as indicated in the above number 3 tip. Then use the discovered probe frequency to modify line 74 to take measurement and obtain images.

## How to debug
Below we list common bugs that may happen during experiment:
1. The first time you use the code, make sure that the file addresses are correct. The default address is the OS direct folder, so you can change the addresses to whatever you desire before measurement. Addresses lines include 179, 256, 262, 299, and 392. 
2. If you interrupt the operation during a single run, you may receive error message that "the current device is not available" during the next run. This is common, and you can just go ahead and re-run the whole program, and the error message should disappear. In case it does not, check that the software "Pylon Viewer" has been closed, because the Python code cannot access the camera device when the Pylon Viewer software is open and using the camera.
3. If you receive error message related to camera not being able to acquire an image, usually this is because the acquisition is longer than what the program is set to wait. To change the setting, access lines 86, 96 and change the values. Note these values are in unit of miliseconds. I have set the values to 10000 (10 seconds). Unless you use acquistion time 10 seconds or system crashes due to computer malfunction, usually you won't receive related error message.

Any question, please contact shunjie2@illinois.edu for help.

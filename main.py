#!/usr/bin/env python3
import pyvisa as visa
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import numpy as np
import time
from pypylon import pylon
from PIL import Image

###########################################################################
############################### function definitions ######################

#calculate the contrast for each super pixel of the magnetic image
def sum_Area(width, height, i, j):
    sum_regions = []
    for f in range(len(freqs)):
        sum_regions.append((np.sum(images[f,j*height:(j+1)*height,i*width:(i+1)*width])-
                            np.sum(images_reference[f,j*height:(j+1)*height,i*width:(i+1)*width]))/
                            np.sum(images_reference[f,j*height:(j+1)*height,i*width:(i+1)*width]))
    sum_regions = np.array(sum_regions)
    return sum_regions

#essentially keep the original camera image as a comparison
def sum_Area_2(width, height, i, j):
    sum_regions = []
    for f in range(len(freqs)):
        sum_regions.append((np.sum(images[f,j*height:(j+1)*height,i*width:(i+1)*width])))
    sum_regions = np.array(sum_regions)
    return sum_regions

#take the peak point, for purposes of accuracy, this function can be further modified
def find_peak(spectrum):
    return -min(spectrum)

###########################################################################
############################### Variable initialization ######################

curtime = datetime.now() #will be used to save data for this run

rm = visa.ResourceManager()

#access and open the camera
tl_factory = pylon.TlFactory.GetInstance()
devices = tl_factory.EnumerateDevices()
#for device in devices:
    #print("Connected cameras:", device.GetFriendlyName())
camera = pylon.InstantCamera()
camera.Attach(tl_factory.CreateDevice(devices[0])) #Index 0 for Physical Camera, 1 for Emulation when USB is connected 
camera.Open()
#Set parameters for the camera
camera.PixelFormat.SetValue("Mono12") #Set Pixel Format either as Monon8 or Mono12
camera.Width.SetValue(1920)  #Set the desired image width
camera.Height.SetValue(1200)  #Set the desired image height
camera.OffsetX.SetValue(0)  #Set the horizontal offset for the image
camera.OffsetY.SetValue(0)  #Set the vertical offset for the image
camera.ExposureTime.SetValue(5000000)  #Set Exposure time for the camera
#camera.TriggerSelector.SetValue("FrameStart")  #Set Trigger Selector Value for camera
camera.TriggerMode.SetValue("On")   #Set Trigger mode as on
camera.TriggerSource.SetValue("Software")  #Set Trigger source
print("Readout time for this run is", camera.SensorReadoutTime.GetValue())

#open RF generator source
sg384 = rm.open_resource('GPIB0::27::INSTR')
sg384.write('TYPE 0') #amplitude modulation
sg384.write('ADEP 100.0') #100% amplitude modulation depth
sg384.write('RATE 1 kHz') #modulation rate
sg384.write('MODL 1') #enable modulationsg
sg384.write('ENBR 0') #turn off the MW output for next background signal measurement
sg384.write('AMPR 10 dBm') #set MW source output power

#Create arrays for storing results and initialize parameters
freqs = np.arange(2.835, 2.915, 0.002) 
freqs = np.linspace(2.87, 2.87, 1)
number_of_trials = 10
images = np.zeros((len(freqs),camera.Height.GetValue(), camera.Width.GetValue()))
images_contrast = np.zeros((len(freqs),camera.Height.GetValue(), camera.Width.GetValue()))
images_reference = np.zeros((len(freqs),camera.Height.GetValue(), camera.Width.GetValue()))
camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

###########################################################################
############################### data acquisition ######################
for i, val in np.ndenumerate(freqs):
    for j in range(number_of_trials):
        camera.TriggerSoftware.Execute()
        grab_1 = camera.RetrieveResult(10000, pylon.TimeoutHandling_Return)
        if grab_1.GrabSucceeded():
           images_reference[i] += grab_1.GetArray()/number_of_trials #take the image when RF field is not applied
        else:
           print("ERROR: Time out, Exposure Time exceeds the maximum allowed time interval")
           break
        sg384.write('FREQ ' + str(val) + ' GHz') #Set MW output frequency
        sg384.write('ENBR 1') #turn on MW output
        time.sleep(5)
        camera.TriggerSoftware.Execute()
        grab_2 = camera.RetrieveResult(10000, pylon.TimeoutHandling_Return)
        if grab_2.GrabSucceeded():
           images[i] += grab_2.GetArray()/number_of_trials
           #images_contrast[i] += (images[i] - images_reference[i])/(images[i] + images_reference[i]) #take the contrast image for applied RF field
           #images_def[i] += images[i] - images_reference[i]
           #images_sum[i] += (images[i] + images_reference[i])/2
        else:
           print("ERROR: Time out, Exposure Time exceeds the maximum allowed time interval")
           break
        sg384.write('ENBR 0') #turn off the MW output for next background signal measurement
        time.sleep(0)
    images_contrast[i] = (images[i] - images_reference[i])/(images[i] + images_reference[i])*2

#Devices closing
sg384.close()
camera.StopGrabbing()
camera.Close()

###########################################################################
############################### 1-D contrast plotting ######################

#Specify the coordinates/regions for plotting and mode for plotting
x = 550 #pixel plotting coordinate row
y = 1000 #pixel plotting coordinate column

x1 = 0 #low coordinate for row boundary (height) in a region
x2 = 1200 #high coordinate for row boundary in a region, x2 > x1 should be assumed
y1 = 0 #low coordinate for column boundary (width) in a region
y2 = 1920 #high coordinate for column boundary in a region, y2 > y1 should be assumed
factor = (x2-x1)*(y2-y1)
mode_region_plotting = 1 #0 for single pixel plotting, 1 for plotting over some region bounded by (x1,y1) and (x2,y2), other numbers will skip this process
show_signal = 1 #elect to plot signal plot for this run (1->plot it, 0->skip it)
show_reference = 1 #elect to plot reference plot for this run 
show_slope = 1 #plot the first derivative of the contrast plot with respect to frequency
save_En_1D = 1 #elect this to 1 if the contrast plot result is expected to be saved to .txt file
save_En_2D = 1 #elect this to 1 if the whole picture's intensity profile is expected to be saved to .txt file


sum_regions = [] #global variable used to store the contrast/signal/reference versus frequency array data
sum_slope = [] #global variable used to store the slope of contrast versus frequency array data


#single pixel contrast plot with pixel coordinates specified
if mode_region_plotting == False:
    plt.figure()
    #plt.plot(freqs, images[:,x,y])
    plt.plot(freqs, images_contrast[:,x,y])
    #plt.title("Intensity Versus Frequency Spectum")
    plt.title("Contrast Versus Frequency Spectum")
    plt.xlabel("Freqency (GHz)")
    #plt.ylabel("Intensity at coordinates" + " (" + str(x) + "," + str(y) + ")")
    plt.ylabel("Contrast for coordinates" + " (" + str(x) + "," + str(y) + ")")
    plt.show()
    
    if show_signal == True:
        plt.figure()
        plt.plot(freqs, images[:,x,y])
        #plt.plot(freqs, images_contrast[:,x,y])
        plt.title("Intensity Versus Frequency Spectum")
        #plt.title("Contrast Versus Frequency Spectum")
        plt.xlabel("Freqency (GHz)")
        #plt.ylabel("Intensity at coordinates" + " (" + str(x) + "," + str(y) + ")")
        plt.ylabel("Intensity for coordinates" + " (" + str(x) + "," + str(y) + ")")
        plt.show()
    
    if show_reference == True:
         plt.figure()
         plt.plot(freqs, images_reference[:,x,y])
         #plt.plot(freqs, images_contrast[:,x,y])
         plt.title("Reference Versus Frequency Spectum")
         #plt.title("Contrast Versus Frequency Spectum")
         plt.xlabel("Freqency (GHz)")
         #plt.ylabel("Intensity at coordinates" + " (" + str(x) + "," + str(y) + ")")
         plt.ylabel("Reference for coordinates" + " (" + str(x) + "," + str(y) + ")")
         plt.show()
   
elif mode_region_plotting == True:
    for i in range(len(freqs)):
        #region = images[i,x1:x2,y1:y2]
        sum_regions.append((np.sum(images[i,x1:x2,y1:y2])-np.sum(images_reference[i,x1:x2,y1:y2]))/
                            np.sum(images_reference[i,x1:x2,y1:y2]))
    sum_regions = np.array(sum_regions)
    if save_En_1D == True:
       with open('/data_1D_contrast.txt', 'w') as f:
           np.savetxt(f, sum_regions)
       f.close()
    plt.figure()
    plt.plot(freqs, sum_regions)
    #plt.title("Average intensity Versus Frequency Spectum")
    plt.title("Average Contrast Versus Frequency Spectum")
    plt.xlabel("Freqency (GHz)")
    #plt.ylabel("Averge Intensity" + " (" + str(x1) + "," + str(y1) + ")" + " to (" + str(x2) + "," + str(y2) + ")")
    plt.ylabel("Averge Contrast" + " (" + str(x1) + "," + str(y1) + ")" + " to (" + str(x2) + "," + str(y2) + ")")
    #plt.ylim(-0.037,0.01)
    plt.show()
    
    if show_signal == True:
        sum_regions = []
        region = np.zeros((x2 - x1, y2 - y1))
        for i in range(len(freqs)):
            #region = images[i,x1:x2,y1:y2]
            region = images[i,x1:x2,y1:y2]
            sum_regions.append(region.sum())
        sum_regions = np.array(sum_regions)
        plt.figure()
        plt.plot(freqs, sum_regions/factor)
        #plt.title("Average intensity Versus Frequency Spectum")
        plt.title("Average signal Versus Frequency Spectum")
        plt.xlabel("Freqency (GHz)")
        #plt.ylabel("Averge Intensity" + " (" + str(x1) + "," + str(y1) + ")" + " to (" + str(x2) + "," + str(y2) + ")")
        plt.ylabel("Averge Signal" + " (" + str(x1) + "," + str(y1) + ")" + " to (" + str(x2) + "," + str(y2) + ")")
        plt.show()
    
    if show_reference == True:
        sum_regions = []
        region = np.zeros((x2 - x1, y2 - y1))
        for i in range(len(freqs)):
            #region = images[i,x1:x2,y1:y2]
            region = images_reference[i,x1:x2,y1:y2]
            sum_regions.append(region.sum())
        sum_regions = np.array(sum_regions)
        plt.figure()
        plt.plot(freqs, sum_regions/factor)
        #plt.title("Average intensity Versus Frequency Spectum")
        plt.title("Average Reference Versus Frequency Spectum")
        plt.xlabel("Freqency (GHz)")
        #plt.ylabel("Averge Intensity" + " (" + str(x1) + "," + str(y1) + ")" + " to (" + str(x2) + "," + str(y2) + ")")
        plt.ylabel("Averge Reference" + " (" + str(x1) + "," + str(y1) + ")" + " to (" + str(x2) + "," + str(y2) + ")")
        plt.show()
    
    if show_slope == True:
        sum_regions = []
        for i in range(len(freqs)):
           #region = images[i,x1:x2,y1:y2]
           sum_regions.append((np.sum(images[i,x1:x2,y1:y2])-np.sum(images_reference[i,x1:x2,y1:y2]))/
                            np.sum(images_reference[i,x1:x2,y1:y2]))
        sum_regions = np.array(sum_regions)
        for i in range(len(sum_regions)-1):
            sum_slope.append((sum_regions[i+1]-sum_regions[i])/(freqs[i+1]-freqs[i]))
        sum_slope = np.array(sum_slope)
        plt.figure()
        plt.plot(freqs[0:len(freqs)-1], sum_slope)
        #plt.title("Average intensity Versus Frequency Spectum")
        plt.title("slope Versus Frequency Spectum")
        plt.xlabel("Freqency (GHz)")
        #plt.ylabel("Averge Intensity" + " (" + str(x1) + "," + str(y1) + ")" + " to (" + str(x2) + "," + str(y2) + ")")
        plt.ylabel("Averge slope" + " (" + str(x1) + "," + str(y1) + ")" + " to (" + str(x2) + "," + str(y2) + ")")
        plt.show()
        
else:
    print('Proceed to generate 2D contrast plot if specified')
        
###########################################################################
############################### data saving in text file ######################   

#Election to write to file for data storage, if save_En = 1
#NOTE: modify the ADDRESS as necessary for each user
if save_En_2D == True:
    data_signal = np.array(images[0])
    data_signal = data_signal.T
    with open('/data_signal.txt', 'w') as f:
        np.savetxt(f, data_signal)
    f.close()
    
    data_reference = np.array(images_reference[0])
    data_reference = data_reference.T
    with open('/data_reference.txt', 'w') as f:
        np.savetxt(f, data_reference)
    f.close()
    
###########################################################################
############################### 2-D image plotting ######################

#plot maximum contrast within the image at different regions and generate 2D contrast plot 
#Create parameters for slicing the whole image, both parameters should satisfy mod(width(height), resolution)=0 
desired_width_resolution = int(384) #Number of segments sliced along the width
desired_height_resolution = int(240) #Number of segments sliced along the height
region_width = images_contrast.shape[2]/desired_width_resolution
region_height = images_contrast.shape[1]/desired_height_resolution
scalebar_width = 20 * int(desired_width_resolution/384)
plot_allow = 1 #enter 1 for plotting 2D plot, or 0 to skip this step
testing = 1
enhance_En = 1 #enter 1 for plotting enhanced version of the magnetic image 

if plot_allow == True:
    contrast_2D = np.zeros((desired_width_resolution, desired_height_resolution))
    maximum = -np.Inf
    for i in range(desired_width_resolution):
        for j in range(desired_height_resolution):
            spectrum = sum_Area(int(region_width), int(region_height), i, j)
            #plt.figure()
            #plt.plot(freqs, spectrum)
            #plt.title("Average Contrast Versus Frequency Spectum")
            #plt.xlabel("Freqency (GHz)")
            #plt.ylabel("Averge Contrast" + " (" + str(i*5) + "," + str(j*5) + ")" + " to (" + str(5*(i+1)) + "," + str(5*(j+1)) + ")")
            #plt.ylim(-0.035,0.01)
            peak_magnitude = find_peak(spectrum)
            if (maximum < peak_magnitude):
                maximum = peak_magnitude
            contrast_2D[i,j] = peak_magnitude
    print(maximum)
    contrast_2D = Image.fromarray(contrast_2D.T/maximum*255)
    if save_En_2D == True:
        with open('/magnetic image.txt', 'w') as f:
            np.savetxt(f, contrast_2D)
    f.close()
    plt.figure()
    plt.imshow(contrast_2D)
    plt.axis('tight')
    ax = plt.gca()
    scalebar = AnchoredSizeBar(ax.transData,
                           scalebar_width, '10 μm', 'lower right', 
                           pad=0.1,
                           color='white',
                           frameon=False,
                           size_vertical=1
                           )
    ax.add_artist(scalebar)
    ax.axis('off')
    plt.show()
    
    if testing == True:
        contrast_2D = np.zeros((desired_width_resolution, desired_height_resolution))
        maximum = -np.Inf
        for i in range(desired_width_resolution):
            for j in range(desired_height_resolution):
                spectrum = sum_Area_2(int(region_width), int(region_height), i, j)
            #plt.figure()
            #plt.plot(freqs, spectrum)
            #plt.title("Average Contrast Versus Frequency Spectum")
            #plt.xlabel("Freqency (GHz)")
            #plt.ylabel("Averge Contrast" + " (" + str(i*5) + "," + str(j*5) + ")" + " to (" + str(5*(i+1)) + "," + str(5*(j+1)) + ")")
            #plt.ylim(-0.035,0.01)
                peak_magnitude = find_peak(spectrum)
                if (maximum < peak_magnitude):
                    maximum = peak_magnitude
                contrast_2D[i,j] = peak_magnitude
        print(maximum)
        contrast_2D = Image.fromarray(contrast_2D.T/10/maximum*255)
        plt.figure()
        plt.imshow(contrast_2D)
        plt.axis('tight')
        ax = plt.gca()
        scalebar = AnchoredSizeBar(ax.transData,
                           scalebar_width, '10 μm', 'lower right', 
                           pad=0.1,
                           color='white',
                           frameon=False,
                           size_vertical=1
                           )
        ax.add_artist(scalebar)
        ax.axis('off')
        plt.show()
        
    if enhance_En == 1:
        contrast_2D = np.zeros((desired_width_resolution, desired_height_resolution))
        maximum = -np.Inf
        for i in range(desired_width_resolution):
            for j in range(desired_height_resolution):
                spectrum = sum_Area(int(region_width), int(region_height), i, j)
                #plt.figure()
                #plt.plot(freqs, spectrum)
                #plt.title("Average Contrast Versus Frequency Spectum")
                #plt.xlabel("Freqency (GHz)")
                #plt.ylabel("Averge Contrast" + " (" + str(i*5) + "," + str(j*5) + ")" + " to (" + str(5*(i+1)) + "," + str(5*(j+1)) + ")")
                #plt.ylim(-0.035,0.01)
                peak_magnitude = find_peak(spectrum)
                if (maximum < peak_magnitude):
                    maximum = peak_magnitude
                if peak_magnitude >= 0:
                    contrast_2D[i,j] = peak_magnitude
                else:
                    contrast_2D[i,j] = 0
        contrast_2D -= maximum*0.5
        contrast_2D *= -1
        enhanced_maximum = np.amax(contrast_2D)
        print("maximum after difference", enhanced_maximum)
        print("minimum after difference", np.amin(contrast_2D))
        contrast_2D = Image.fromarray(contrast_2D.T/enhanced_maximum*255)
        plt.figure()
        plt.imshow(contrast_2D)
        plt.axis('tight')
        ax = plt.gca()
        scalebar = AnchoredSizeBar(ax.transData,
                           scalebar_width, '10 μm', 'lower right', 
                           pad=0.1,
                           color='white',
                           frameon=False,
                           size_vertical=1
                           )
        ax.add_artist(scalebar)
        ax.axis('off')
        plt.show()

#uncomment the following line if an enhanced contrast image is needed and Histogram equalization script is 
#in the same folder; address may need to be changed.
#exec(open("/Users/shunjie2/Downloads/Histogram equalization.py").read())

curtime2 = datetime.now()
print("The starting time and the ending time of this session are", curtime,"and", curtime2)
print("session length", curtime2 - curtime)
        

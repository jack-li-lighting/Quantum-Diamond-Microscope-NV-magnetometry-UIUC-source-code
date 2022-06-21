import pyvisa as visa
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import numpy as np
import time
from pypylon import pylon
from PIL import Image

def sum_Area(width, height, i, j):
    sum_regions = []
    for f in range(len(freqs)):
        sum_regions.append((np.sum(images[f,j*height:(j+1)*height,i*width:(i+1)*width])-
                            np.sum(images_reference[f,j*height:(j+1)*height,i*width:(i+1)*width]))/
                            np.sum(images_reference[f,j*height:(j+1)*height,i*width:(i+1)*width]))
    sum_regions = np.array(sum_regions)
    return sum_regions

def sum_Area_2(width, height, i, j):
    sum_regions = []
    for f in range(len(freqs)):
        sum_regions.append((np.sum(images[f,j*height:(j+1)*height,i*width:(i+1)*width])-
                            np.sum(images_reference[f,j*height:(j+1)*height,i*width:(i+1)*width])))
    sum_regions = np.array(sum_regions)
    return sum_regions

def find_peak(spectrum):
    peak = np.Inf
    for i in range(len(spectrum)):
        if peak > spectrum[i]:
            peak = spectrum[i]
            peak_frequency = i
    return (peak_frequency, peak)

##################################### Measurement parameter setting #############################################
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
sg384.write('AMPR 10 dBm') #set MW source output power

#Create arrays for storing results and initialize parameters
reference_contrast = 0 #reference contrast is used to determine the slope approximately used in this run
probe_frequency = 0 #frequency determined to probe the contrast which can be used to calculate frequency shift from contrast differences with slope
frequency_bound1 = 2.84 #lower bound frequency used to scan the frequency range to find reference contrast
frequency_bound2 = 2.85 #higher bound frequency used to scan the frequency range to find reference contrast
step_size = 0.001
freqs = np.arange(frequency_bound1, frequency_bound2, step_size)
#freqs = np.linspace(2.87, 2.87, 1)
number_of_trials = 5
images = np.zeros((len(freqs),camera.Height.GetValue(), camera.Width.GetValue()))
images_contrast = np.zeros((len(freqs),camera.Height.GetValue(), camera.Width.GetValue()))
images_reference = np.zeros((len(freqs),camera.Height.GetValue(), camera.Width.GetValue()))
camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

################################################## taking data ####################################################
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
        time.sleep(0)
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
    images_contrast[i] = (images[i] - images_reference[i])/(images_reference[i])

#Devices closing
sg384.close()
camera.StopGrabbing()
camera.Close()

################################################# data processing ###################################################################
spectrum = sum_Area(1920, 1200, 0, 0)
probe_frequency, reference_contrast = find_peak(spectrum)

probe_frequency += 0.01/2/step_size #use a frequency which is in the middle of the curve
slope = reference_contrast/(0.01)
probe_frequency = int(probe_frequency)
reference_contrast = spectrum[probe_frequency]

#plot maximum contrast within the image at different regions and generate 2D contrast plot 
#Create parameters for slicing the whole image, both parameters should satisfy mod(width(height), resolution)=0 
desired_width_resolution = int(384) #Number of segments sliced along the width
desired_height_resolution = int(240) #Number of segments sliced along the height
region_width = images_contrast.shape[2]/desired_width_resolution
region_height = images_contrast.shape[1]/desired_height_resolution
scalebar_width = 20 * int(desired_width_resolution/384)
plot_allow = 1 #enter 1 for plotting 2D plot, or 0 to skip this step
testing = 0 

if plot_allow == True:
    contrast_2D = np.zeros((desired_width_resolution, desired_height_resolution))
    maximum = -np.Inf
    minimum = np.Inf
    for i in range(desired_width_resolution):
        for j in range(desired_height_resolution):
            spectrum = sum_Area(int(region_width), int(region_height), i, j)
            #plt.figure()
            #plt.plot(freqs, spectrum)
            #plt.title("Average Contrast Versus Frequency Spectum")
            #plt.xlabel("Freqency (GHz)")
            #plt.ylabel("Averge Contrast" + " (" + str(i*5) + "," + str(j*5) + ")" + " to (" + str(5*(i+1)) + "," + str(5*(j+1)) + ")")
            #plt.ylim(-0.035,0.01)
            frequency_shift = (reference_contrast - spectrum[probe_frequency])/slope
            
            if (maximum < frequency_shift):
                maximum = frequency_shift
            if (minimum > frequency_shift):
                minimum = frequency_shift
                
            contrast_2D[i,j] = frequency_shift
    print(maximum, minimum)
    contrast_2D[i,j] -= minimum 
    contrast_2D = Image.fromarray(contrast_2D.T/(maximum-minimum)*255)
    plt.figure()
    plt.imshow(contrast_2D, cmap = 'Greys')
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





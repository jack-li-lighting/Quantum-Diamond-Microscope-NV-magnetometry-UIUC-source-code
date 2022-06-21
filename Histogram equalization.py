import matplotlib.pyplot as plt
import numpy as np
from skimage import exposure

# Read the image
image_origin = np.loadtxt('/magnetic image.txt')

# Apply Histogram Equalization here
image_histeq = exposure.equalize_hist(image_origin)

# Show the results
fig_cam_origin = plt.figure(1)
fig_cam_origin.suptitle('Original Image')
plt.imshow(image_origin,cmap='gray')
fig_cam_bright = plt.figure(2)
fig_cam_bright.suptitle('HistEq Image')
plt.imshow(image_histeq,cmap='gray')
plt.show()

import tifffile
import SimpleITK as sitk
import numpy as np


load_filename = "C:/Users/Cookie/Downloads/test.tiff"
save_filename = "C:/Users/Cookie/Downloads/test.nii.gz"
image = tifffile.imread(load_filename)
image = np.rint(image).astype(np.int8)
# image = np.flip(image, axis=1)
image = sitk.GetImageFromArray(image)
sitk.WriteImage(image, save_filename)

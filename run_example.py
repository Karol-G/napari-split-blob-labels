from napari import Viewer
from src.adaptive_brush._function import MyWidget
import napari
from skimage import data
import SimpleITK as sitk

viewer = Viewer()
viewer.window.add_dock_widget(MyWidget(viewer))

# viewer.add_image(data.astronaut(), rgb=True)

# image = sitk.ReadImage("D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/3D_converted/images/SPP2315_160-250.nii.gz")
image = sitk.ReadImage("D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari-image.nii.gz")
image = sitk.GetArrayFromImage(image)
# offset = 400
# image = image[offset+100:offset+300, offset+100:offset+300, offset+100:offset+300]
# sitk.WriteImage(sitk.GetImageFromArray(image), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari-image.nii.gz")
viewer.add_image(image, rgb=False)

# labels = sitk.ReadImage("D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/processed/instance_segmentation_image/SPP2315_160-250.nii.gz")
labels = sitk.ReadImage("D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari-labels.nii.gz")
labels = sitk.GetArrayFromImage(labels)
# labels = labels[offset+100:offset+300, offset+100:offset+300, offset+100:offset+300]
# sitk.WriteImage(sitk.GetImageFromArray(labels), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari-labels.nii.gz")
viewer.add_labels(labels)

napari.run()

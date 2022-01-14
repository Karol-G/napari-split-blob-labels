from qtpy import QtWidgets
from qtpy.QtCore import Qt
from napari_plugin_engine import napari_hook_implementation
import napari
import numpy as np
from napari.layers.labels._labels_constants import Mode
from skimage.morphology import binary_erosion
from skimage.measure import label as ski_label
from skimage.measure import regionprops
from skimage.segmentation import flood_fill, watershed, random_walker
from src.adaptive_brush.utils import dynamic_slicing, normalize, rgb2gray
import copy
import SimpleITK as sitk
import GeodisTK

class MyWidget(QtWidgets.QWidget):
    def __init__(self, viewer: 'napari.viewer.Viewer') -> None:
        super().__init__()
        self.viewer = viewer
        self.btn_activate = QtWidgets.QPushButton('Activate')
        self.btn_activate.clicked.connect(self._on_click_init)
        # self.btn_split = QtWidgets.QPushButton('Split')
        # self.btn_split.clicked.connect(self.split_blobs)
        self.btn_save = QtWidgets.QPushButton('Save')
        self.btn_save.clicked.connect(self._save)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.btn_activate)
        # self.layout().addWidget(self.btn_split)
        self.layout().addWidget(self.btn_save)

        self.image_layer = None
        self.image = None
        self.label_layer = None
        self.preview_layer = None
        self.dims = None
        self.current_roi_indices = None
        self.current_roi_labels = None
        self.contrast_limits_changed = False

        self.initialized = False
        self.preview_computed = False
        self.label_color = 78
        self.brush_size = 1
        self.current_label = 0
        self.unused_id = None
        self.blob_point1 = None
        self.blob_point2 = None

    def _on_click_init(self):
        layers = self.viewer.layers

        image_layers, label_layers = [], []
        for layer in layers:
            if isinstance(layer, napari.layers.image.image.Image):
                image_layers.append(layer)
            elif isinstance(layer, napari.layers.labels.labels.Labels) and layer.name != ".preview":
                label_layers.append(layer)

        self.label_layer = label_layers[0]
        self.dims = len(self.label_layer.data.shape)
        self.init_preview()
        self.init_unused_id()

        @self.preview_layer.mouse_drag_callbacks.append
        def callback_draw_border(layer, event):
            if event.button == 1:  # Left click
                self.preview_layer.mode = Mode.PAINT
                yield
                # print("Left click")
                while event.type == "mouse_move":
                    # print("Left click drag")
                    yield
                self.split_blobs(event)
                self.label_layer.data = self.label_layer.data
            elif event.button == 3:  # Middle click
                # print("Middle click")
                self.pick_label(event)
                yield
            self.preview_layer.mode = Mode.PAN_ZOOM

    def split_blobs(self, event):
        # print("split_blobs")
        filtered = np.zeros_like(self.label_layer.data)
        filtered[self.label_layer.data == self.current_label] = 1
        props = regionprops(filtered)
        bbox = props[0].bbox
        roi = [[bbox[i], bbox[i+self.dims]] for i in range(self.dims)]  # Get slice indices from bbox independent of the image dimension
        label_roi = dynamic_slicing(self.label_layer.data, roi)
        preview_roi = dynamic_slicing(self.preview_layer.data, roi)
        new_label_roi = np.zeros_like(label_roi)
        new_label_roi[label_roi == self.current_label] = 1
        preview_roi[preview_roi > 0] = 1
        # if self.dims == 3:
        #     preview_roi = self.preview2D_to_preview3D(preview_roi, new_label_roi, event, roi)
        # point1_roi = np.zeros_like(new_label_roi, dtype=np.uint8)
        # dynamic_slicing(point1_roi, self.blob_point1, assign=1)
        # spacing = [1] * self.dims
        # spacing = np.asarray(spacing, dtype=np.float32)
        # # border_dist_roi = GeodisTK.geodesic3d_raster_scan(np.zeros_like(new_label_roi, dtype=np.float32), preview_roi.astype(np.uint8), spacing, 0.00, 1)
        # # point1_dist_roi = GeodisTK.geodesic3d_raster_scan(np.zeros_like(new_label_roi, dtype=np.float32), point1_roi, spacing, 0.00, 1)
        # # point2_dist_roi = GeodisTK.geodesic3d_raster_scan(np.zeros_like(new_label_roi, dtype=np.float32), preview_roi.astype(np.uint8), spacing, 0.00, 1)
        # sitk.WriteImage(sitk.GetImageFromArray(new_label_roi), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari_roi_label.nii.gz")
        # sitk.WriteImage(sitk.GetImageFromArray(preview_roi), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari_roi_preview.nii.gz")
        # sitk.WriteImage(sitk.GetImageFromArray(border_dist_roi), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari_roi_border_dist.nii.gz")

        # sitk.WriteImage(sitk.GetImageFromArray(new_label_roi), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari_roi_tmp1.nii.gz")
        # sitk.WriteImage(sitk.GetImageFromArray(preview_roi), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari_roi_tmp2.nii.gz")

        markers = np.zeros_like(new_label_roi)
        dynamic_slicing(markers, self.world2roi(self.blob_point1, roi), assign=1)
        dynamic_slicing(markers, self.world2roi(self.blob_point2, roi), assign=2)

        spacing = [1] * self.dims
        spacing = np.asarray(spacing, dtype=np.float32)
        border_dist_roi = GeodisTK.geodesic3d_raster_scan(np.zeros_like(new_label_roi, dtype=np.float32), preview_roi.astype(np.uint8), spacing, 0.00, 1)
        border_dist_roi = normalize(border_dist_roi)
        border_dist_roi = 1 - border_dist_roi
        border_dist_roi[new_label_roi == 0] = 1
        ignore_mask = np.zeros_like(new_label_roi, dtype=np.uint8)
        ignore_mask[new_label_roi == 1] = 1
        # sitk.WriteImage(sitk.GetImageFromArray(border_dist_roi), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/border_dist_roi.nii.gz")
        # sitk.WriteImage(sitk.GetImageFromArray(ignore_mask.astype(np.int8)), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/ignore_mask.nii.gz")
        new_label_roi = watershed(border_dist_roi.astype(np.float32), markers=markers.astype(np.uint8), mask=ignore_mask.astype(np.uint8))
        # label_roi = random_walker(border_dist_roi.astype(np.float32), labels=markers.astype(np.uint8))
        # sitk.WriteImage(sitk.GetImageFromArray(label_roi), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/watershed.nii.gz")
        # print("unique: ", np.unique(new_label_roi))
        label_roi[new_label_roi == 2] = self.unused_id
        dynamic_slicing(self.label_layer.data, roi, assign=label_roi)


        # Thresholding
        # new_label_roi[preview_roi == 1] = 0
        # new_label_roi_instance = ski_label(new_label_roi.astype(np.int8), connectivity=1).astype(np.int8)
        # label_roi[new_label_roi_instance == 2] = self.unused_id

        # roi_offset = np.asarray(bbox)[:self.dims]
        # blob_point1_roi = np.asarray(self.blob_point1) - roi_offset
        # point1_value = dynamic_slicing(border_dist_roi, blob_point1_roi)
        # print("point1_value: ", point1_value)
        # tolerance = point1_value - np.nextafter(0, 1)
        # border_dist_roi[border_dist_roi > point1_value] = point1_value
        # flood_result = flood_fill(border_dist_roi, tuple(blob_point1_roi), new_value=self.unused_id, tolerance=tolerance)
        # sitk.WriteImage(sitk.GetImageFromArray(flood_result), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari_roi_flood.nii.gz")

        # point1_border_dist = 0
        # point2_border_dist = 0
        #
        # label_roi[(label_roi == 1) & ((point1_dist_roi <= point1_border_dist) | (border_dist_roi < point2_dist_roi))] = self.current_label
        # label_roi[(label_roi == 1) & (border_dist_roi < point2_dist_roi)] = self.unused_id

        # distance_roi = normalize(distance_roi)
        # distance_roi = 1 - distance_roi
        # sitk.WriteImage(sitk.GetImageFromArray(distance_roi), "D:/Datasets/DKFZ/2021_Gotkowski_HZDR-HIF/napari_roi_distance2.nii.gz")

        self.preview_layer.data = np.zeros_like(self.preview_layer.data)
        self.unused_id += 1
        self.blob_point1 = None
        self.blob_point2 = None

    def preview2D_to_preview3D(self, preview, labels, event, roi):
        data_coordinates = self.label_layer.world_to_data(event.position)
        coords = np.round(data_coordinates).astype(int)
        coords = self.world2roi(coords, roi)
        shape = preview.shape
        preview = preview[coords[0], ...]
        preview = np.resize(preview, shape)
        return preview

    def world2roi(self, coords, roi):
        roi_offset = np.asarray([dim[0] for dim in roi])
        coords_roi = np.asarray(coords) - roi_offset
        return coords_roi

    def pick_label(self, event):
        data_coordinates = self.label_layer.world_to_data(event.position)
        coords = np.round(data_coordinates).astype(int)
        if self.blob_point1 is None:
            self.blob_point1 = coords
            self.current_label = dynamic_slicing(self.label_layer.data, coords)
            print("self.blob_point1: ", self.blob_point1)
            print("self.current_label: ", self.current_label)
        elif self.blob_point2 is None:
            self.blob_point2 = coords
            print("self.blob_point2: ", self.blob_point2)
        else:
            raise RuntimeError("???")
        # print("self.current_label: ", self.current_label)

    def _save(self):
        print("save")
        labels = self.label_layer.data
        labels = np.rint(labels).astype(np.int32)
        labels = sitk.GetImageFromArray(labels)
        sitk.WriteImage(labels, "labels.nii.gz")

    def init_preview(self):
        if not self.initialized:
            active_layer = self.viewer.layers.selection.active
            preview_layer = np.zeros(active_layer.data.shape, dtype=int)
            self.preview_layer = self.viewer.add_labels(preview_layer, name='.preview')
            self.preview_layer.selected_label = self.label_color
            self.preview_layer.brush_size = self.brush_size
            # self.preview_layer.mode = Mode.PAINT
            self.viewer.layers.selection.active = self.preview_layer
            self.initialized = True

    def init_unused_id(self):
        ids = np.unique(self.label_layer.data)
        max_id = np.max(ids)
        self.unused_id = max_id + 1


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return MyWidget



from qtpy import QtWidgets
from napari_plugin_engine import napari_hook_implementation
import napari
import numpy as np

class MyWidget(QtWidgets.QWidget):
    def __init__(self, viewer: 'napari.viewer.Viewer') -> None:
        super().__init__()
        self.viewer = viewer
        self.btn = QtWidgets.QPushButton('Activate bug')
        self.btn.clicked.connect(self._on_click_init)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.btn)

    def _on_click_init(self):
        my_layer = self.viewer.layers[0]

        @my_layer.mouse_move_callbacks.append
        def do_something1(layer, event):
            layer.data[...] = np.random.randint(low=0, high=255, size=(5, 10, 10))

        @my_layer.mouse_drag_callbacks.append
        def do_something2(layer, event):
            layer.data[...] = np.random.randint(low=0, high=255, size=(5, 10, 10))
            yield
            while event.type == "mouse_move":
                layer.data[...] = np.random.randint(low=0, high=255, size=(5, 10, 10))
                yield


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return MyWidget


image = np.random.randint(low=0, high=255, size=(5, 10, 10))
viewer = napari.Viewer()
viewer.window.add_dock_widget(MyWidget(viewer))
viewer.add_image(image)
napari.run()

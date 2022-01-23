"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
import magicgui
import napari
import numpy as np
from napari.layers import Image
from napari.utils.events import Event
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QVBoxLayout, QWidget


class BigWarpQWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.model = BigWarpModel(self.viewer)

        self.fixed_selection_widget = magicgui.magicgui(
            self._select_fixed_layer,
            layer={"label": "Fixed", "choices": self.get_input_layers},
            auto_call=True,
        )

        self.moving_selection_widget = magicgui.magicgui(
            self._select_moving_layer,
            layer={"label": "Moving", "choices": self.get_input_layers},
            auto_call=True,
        )

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.moving_selection_widget.native)
        self.layout().addWidget(self.fixed_selection_widget.native)

        self.viewer.layers.events.inserted.connect(self.moving_selection_widget.reset_choices)
        self.viewer.layers.events.removed.connect(self.moving_selection_widget.reset_choices)
        self.viewer.layers.events.inserted.connect(self.fixed_selection_widget.reset_choices)
        self.viewer.layers.events.removed.connect(self.fixed_selection_widget.reset_choices)

        self.fixed_selection_widget.reset_choices()
        self.moving_selection_widget.reset_choices()

    def _select_moving_layer(self, layer: str):
        self.model.moving_layer_name = layer

    def _select_fixed_layer(self, layer: str):
        self.model.fixed_layer_name = layer

    def get_input_layers(self, _):
        return [""] + [x.name for x in self.viewer.layers if isinstance(x, Image) and not x.name.startswith("[BW]")]


class BigWarpModel:
    def __init__(self, viewer: napari.Viewer):
        self._viewer = viewer
        self._moving_layer_name = ""
        self._fixed_layer_name = ""
        self.fixed_result_layer = None
        self.moving_result_layer = None
        self.fixed_points_layer = None
        self.moving_points_layer = None

    def _update_layers(self):
        if not self.moving_layer_name or not self.fixed_layer_name:
            return

        self.fixed_layer.translate = [0, 0]
        self.moving_layer.translate = [0, self.fixed_layer.data.shape[1]]

        if self.fixed_result_layer is None:
            self.fixed_result_layer = self._viewer.add_image(
                self.fixed_layer.data,
                name="[BW] Fixed result",
                translate=[
                    0,
                    self.moving_layer.data.shape[1] + self.fixed_layer.data.shape[1],
                ],
                colormap="red",
            )
        else:
            self.fixed_result_layer.data = self.fixed_layer.data

        if self.moving_result_layer is None:
            self.moving_result_layer = self._viewer.add_image(
                self.moving_layer.data,
                name="[BW] Moving result",
                translate=self.fixed_result_layer.translate,
                blending="additive",
                colormap="green",
            )
        else:
            self.moving_result_layer.data = self.moving_layer.data

        if self.fixed_points_layer is None:
            self.fixed_points_layer = self._viewer.add_points(
                name="[BW] Fixed points",
                face_color="red",
                edge_width=0.5,
                size=5,
                ndim=2,
                translate=self.fixed_layer.translate,
            )
        else:
            with self.fixed_points_layer.events.data.blocker():
                self.fixed_points_layer.data = np.zeros((0, 2), dtype=self.fixed_points_layer.data.dtype)

        if self.moving_points_layer is None:
            self.moving_points_layer = self._viewer.add_points(
                name="[BW] Moving points",
                face_color="green",
                edge_width=0.5,
                size=5,
                ndim=2,
                translate=self.moving_layer.translate,
            )
        else:
            with self.moving_points_layer.events.data.blocker():
                self.moving_points_layer.data = np.zeros((0, 2), dtype=self.moving_points_layer.data.dtype)

        self.moving_points_layer.mode = "add"
        self.moving_points_layer.events.data.connect(self.on_add_point)

        visible_layers = [
            self.fixed_layer,
            self.moving_layer,
            self.fixed_result_layer,
            self.moving_result_layer,
            self.fixed_points_layer,
            self.moving_points_layer,
        ]
        for layer in self._viewer.layers:
            layer.visible = layer in visible_layers

        self._viewer.reset_view()

    def on_add_point(self, event: Event):
        last_point_world = event.source.data_to_world(event.source.data[-1])
        moving_value = self.moving_layer.get_value(last_point_world, world=True)
        fixed_value = self.fixed_layer.get_value(last_point_world, world=True)

        with event.source.events.data.blocker():
            event.source.selected_data = {event.source.data.shape[0] - 1}
            event.source.remove_selected()

        if moving_value is not None:
            add_to_layer = self.moving_points_layer
        elif fixed_value is not None:
            add_to_layer = self.fixed_points_layer
        else:
            return

        with add_to_layer.events.data.blocker():
            add_to_layer.add(add_to_layer.world_to_data(last_point_world))
            if (len(self.moving_points_layer.data) > 0) and (
                len(self.moving_points_layer.data) == len(self.fixed_points_layer.data)
            ):
                # tests fail with cryptic message if this import is performed in the beginning of the file
                # (due to opencv import)
                from napari_bigwarp.bigwarp import bigwarp

                self.moving_result_layer.data = bigwarp(
                    fixed=self.fixed_layer.data,
                    moving=self.moving_layer.data,
                    fixed_points=self.fixed_points_layer.data,
                    moving_points=self.moving_points_layer.data,
                )

    @property
    def moving_layer(self) -> Image:
        return self._viewer.layers[self._moving_layer_name]

    @property
    def fixed_layer(self) -> Image:
        return self._viewer.layers[self._fixed_layer_name]

    @property
    def moving_layer_name(self) -> str:
        return self._moving_layer_name

    @moving_layer_name.setter
    def moving_layer_name(self, layer_name: str):
        self._moving_layer_name = layer_name
        self._update_layers()

    @property
    def fixed_layer_name(self) -> str:
        return self._fixed_layer_name

    @fixed_layer_name.setter
    def fixed_layer_name(self, layer_name: str):
        self._fixed_layer_name = layer_name
        self._update_layers()


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return BigWarpQWidget

import numpy as np
from napari.layers import Image, Points

from napari_bigwarp import BigWarpQWidget


def test_big_warp_q_widget_is_creating_layers(make_napari_viewer, capsys):
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)), name="fixed")
    viewer.add_image(np.random.random((100, 100)), name="moving")

    widget = BigWarpQWidget(viewer)

    assert widget.model.fixed_points_layer is None
    assert widget.model.moving_points_layer is None
    assert widget.model.fixed_result_layer is None
    assert widget.model.moving_result_layer is None

    widget._select_fixed_layer("fixed")
    widget._select_moving_layer("moving")

    assert isinstance(widget.model.fixed_points_layer, Points)
    assert isinstance(widget.model.moving_points_layer, Points)
    assert isinstance(widget.model.fixed_result_layer, Image)
    assert isinstance(widget.model.moving_result_layer, Image)

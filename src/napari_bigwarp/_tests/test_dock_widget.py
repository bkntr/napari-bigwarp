import numpy as np
from napari_bigwarp import BigWarpQWidget


def test_big_warp_q_widget(make_napari_viewer, capsys):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)))

    # create our widget, passing in the viewer
    _ = BigWarpQWidget(viewer)

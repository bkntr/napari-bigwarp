import cv2
import numpy as np


def bigwarp(
    fixed: np.ndarray,
    moving: np.ndarray,
    fixed_points: np.ndarray,
    moving_points: np.ndarray,
):
    moving_pts_init = np.array(
        [
            [0.0, 0.0],
            [0.0, moving.shape[1]],
            [moving.shape[0], moving.shape[1]],
            [moving.shape[0], 0.0],
        ]
    )
    fixed_pts_init = np.array(
        [
            [0.0, 0.0],
            [0.0, fixed.shape[1]],
            [fixed.shape[0], fixed.shape[1]],
            [fixed.shape[0], 0.0],
        ]
    )
    moving_pts = np.concatenate([moving_pts_init, moving_points[:, ::-1]])
    fixed_pts = np.concatenate([fixed_pts_init, fixed_points[:, ::-1]])

    matches = [cv2.DMatch(i, i, 0) for i in range(len(moving_pts))]
    tps = cv2.createThinPlateSplineShapeTransformer()
    tps.estimateTransformation(fixed_pts[None, ...], moving_pts[None, ...], matches)
    out_img = tps.warpImage(np.array(moving))
    return out_img

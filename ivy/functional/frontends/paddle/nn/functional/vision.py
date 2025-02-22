# local

import ivy
import math
from ivy.func_wrapper import with_unsupported_dtypes
from ivy.functional.frontends.paddle.func_wrapper import (
    to_ivy_arrays_and_back,
)
from ivy.utils.assertions import check_equal


@to_ivy_arrays_and_back
def pixel_shuffle(x, upscale_factor, data_format="NCHW"):
    input_shape = ivy.shape(x)
    check_equal(
        len(input_shape),
        4,
        message="pixel shuffle requires a 4D input, but got input size {}".format(
            input_shape
        ),
    )

    if not isinstance(upscale_factor, int):
        raise ValueError("upscale factor must be int type")

    if data_format not in ["NCHW", "NHWC"]:
        raise ValueError(
            "Attr(data_format) should be 'NCHW' or 'NHWC'."
            "But recevie Attr(data_format): {} ".format(data_format)
        )

    b = input_shape[0]
    c = input_shape[1] if data_format == "NCHW" else input_shape[3]
    h = input_shape[2] if data_format == "NCHW" else input_shape[1]
    w = input_shape[3] if data_format == "NCHW" else input_shape[2]

    upscale_factor_squared = upscale_factor**2

    check_equal(
        c % upscale_factor_squared,
        0,
        message=(
            "pixel shuffle expects input channel to be divisible by square of upscale"
            " factor, but got input with sizes {}, upscale factor={}, and"
            " self.size(1)={}, is not divisible by {}".format(
                input_shape, upscale_factor, c, upscale_factor_squared
            )
        ),
        as_array=False,
    )

    oc = int(c / upscale_factor_squared)
    oh = h * upscale_factor
    ow = w * upscale_factor

    if data_format == "NCHW":
        input_reshaped = ivy.reshape(x, (b, oc, upscale_factor, upscale_factor, h, w))
    else:
        input_reshaped = ivy.reshape(x, (b, h, w, upscale_factor, upscale_factor, oc))

    if data_format == "NCHW":
        return ivy.reshape(
            ivy.permute_dims(input_reshaped, (0, 1, 4, 2, 5, 3)), (b, oc, oh, ow)
        )
    return ivy.reshape(
        ivy.permute_dims(input_reshaped, (0, 1, 4, 2, 5, 3)), (b, oh, ow, oc)
    )


@to_ivy_arrays_and_back
@with_unsupported_dtypes({"2.5.1 and below": ("float16", "bfloat16")}, "paddle")
def affine_grid(theta, out_shape, align_corners=True):
    if len(out_shape) == 4:
        N, C, H, W = out_shape
        base_grid = ivy.empty((N, H, W, 3))
        if align_corners:
            base_grid[:, :, :, 0] = ivy.linspace(-1, 1, W)
            base_grid[:, :, :, 1] = ivy.expand_dims(ivy.linspace(-1, 1, H), axis=-1)
            height_values = ivy.expand_dims(ivy.linspace(-1, 1, H), axis=-1)
            base_grid[:, :, :, 1] = ivy.array(
                [[[height_values[i]] * W for i in range(H)]]
            )[:, :, :, 0]
            base_grid[:, :, :, 2] = ivy.full((H, W), 1)
            grid = ivy.matmul(base_grid.view((N, H * W, 3)), theta.swapaxes(1, 2))
            return grid.view((N, H, W, 2))
        else:
            base_grid[:, :, :, 0] = ivy.linspace(-1, 1, W) * (W - 1) / W
            base_grid[:, :, :, 1] = ivy.expand_dims(
                ivy.linspace(-1, 1, H) * (H - 1) / H, axis=-1
            )
            height_values = ivy.expand_dims(
                ivy.linspace(-1, 1, H) * (H - 1) / H, axis=-1
            )
            base_grid[:, :, :, 1] = ivy.array(
                [[[height_values[i]] * W for i in range(H)]]
            )[:, :, :, 0]
            base_grid[:, :, :, 2] = ivy.full((H, W), 1)
        grid = ivy.matmul(base_grid.view((N, H * W, 3)), ivy.swapaxes(theta, 1, 2))
        return grid.view((N, H, W, 2))
    else:
        N, C, D, H, W = out_shape
        base_grid = ivy.empty((N, D, H, W, 4))
        if align_corners:
            base_grid[:, :, :, :, 0] = ivy.linspace(-1, 1, W)
            base_grid[:, :, :, :, 1] = ivy.expand_dims(ivy.linspace(-1, 1, H), axis=-1)
            height_values = ivy.linspace(-1, 1, H)
            base_grid[:, :, :, :, 1] = ivy.array(
                [[[[height_values[i]] * W for i in range(H)]] * D]
            )
            base_grid[:, :, :, :, 2] = ivy.expand_dims(
                ivy.expand_dims(ivy.linspace(-1, 1, D), axis=-1), axis=-1
            )
            width_values = ivy.linspace(-1, 1, D)
            base_grid[:, :, :, :, 2] = ivy.array(
                [[ivy.array([[width_values[i]] * W] * H) for i in range(D)]]
            )
            base_grid[:, :, :, :, 3] = ivy.full((D, H, W), 1)
            grid = ivy.matmul(base_grid.view((N, D * H * W, 4)), theta.swapaxes(1, 2))
            return grid.view((N, D, H, W, 3))
        else:
            base_grid[:, :, :, :, 0] = ivy.linspace(-1, 1, W) * (W - 1) / W
            base_grid[:, :, :, :, 1] = ivy.expand_dims(
                ivy.linspace(-1, 1, H) * (H - 1) / H, axis=-1
            )
            height_values = ivy.linspace(-1, 1, H) * (H - 1) / H
            base_grid[:, :, :, :, 1] = ivy.array(
                [[[[height_values[i]] * W for i in range(H)]] * D]
            )
            base_grid[:, :, :, :, 2] = ivy.expand_dims(
                ivy.expand_dims(ivy.linspace(-1, 1, D) * (D - 1) / D, axis=-1), axis=-1
            )
            width_values = ivy.linspace(-1, 1, D) * (D - 1) / D
            base_grid[:, :, :, :, 2] = ivy.array(
                [[ivy.array([[width_values[i]] * W] * H) for i in range(D)]]
            )
            base_grid[:, :, :, :, 3] = ivy.full((D, H, W), 1)
            grid = ivy.matmul(base_grid.view((N, D * H * W, 4)), theta.swapaxes(1, 2))
            return grid.view((N, D, H, W, 3))


@to_ivy_arrays_and_back
@with_unsupported_dtypes({"2.5.1 and below": ("float16", "bfloat16")}, "paddle")
def grid_sample(input, grid, mode, padding_mode):
    if mode not in ["nearest", "bilinear"]:
        raise ValueError("Invalid mode. Supported modes are 'nearest' and 'bilinear'. ")

    if padding_mode not in ["zeros", "border", "reflection"]:
        raise ValueError(
            "Invalid padding mode. Supported modes are 'zeros', 'border' and"
            " 'reflection'. "
        )

    if len(grid.shape) != 4 or grid.shape[3] != 2:
        raise ValueError(
            "The grid should be a 4D tensor with the last dim having size 2."
        )  # size 2 representing (x,y) coordinates.

    if mode == "nearest":
        return grid_sample_nearest(input, grid, padding_mode)
    elif mode == "bilinear":
        return grid_sample_bilinear(input, grid, padding_mode)


def grid_sample_nearest(input, grid, padding_mode):
    # get the spatial dims of the input & grid
    input_shape = ivy.shape(input)
    ivy.shape(grid)
    batch, channels, in_height, in_width = input_shape
    # out_height, out_width = grid_shape[1], grid_shape[2]

    # normalise grid coordinates to the range [-1, 1]
    normalised_grid = 2.0 * grid / ivy.array([in_width - 1, in_height - 1])
    normalised_grid = normalised_grid - ivy.array([1.0, 1.0])

    # map the normalised grid coordinates to the output tensor using round operation
    if padding_mode == "zeros":
        grid_x = ivy.clip(math.round(normalised_grid[:, :, :, 0]), -1.0, 1.0)
        grid_y = ivy.clip(math.round(normalised_grid[:, :, :, 1]), -1.0, 1.0)
    else:
        grid_x = ivy.clip(math.round(normalised_grid[:, :, :, 0]), 0.0, 1.0)
        grid_y = ivy.clip(math.round(normalised_grid[:, :, :, 0]), 0.0, 1.0)

    # convert the grid coordinaates to indices
    x_indices = ((grid_x + 1.0) * 0.5 * (in_width - 1)).astype("int32")
    y_indices = ((grid_y + 1.0) * 0.5 * (in_height - 1)).astype("int32")
    # Gather values from input using indices
    gathered = input[:, :, y_indices, x_indices]

    return gathered
    # the shape of the gathered tensor is (batch, channels, out_height, out_width)


def grid_sample_bilinear(input, grid, padding_mode):
    # Get the spatial dimensions of the input and grid
    input_shape = ivy.shape(input)
    ivy.shape(grid)
    batch_size, channels, in_height, in_width = input_shape
    # out_height, out_width = grid_shape[1], grid_shape[2]

    # normalise grid cordinates to the range [-1, 1]
    normalised_grid = 2.0 * grid / ivy.array([in_width - 1, in_height - 1])
    normalised_grid = normalised_grid - ivy.array([1.0, 1.0])

    # map the normalised grid coordinates to the input tensor
    if padding_mode == "zeros":
        grid_x = ivy.clip(
            (normalised_grid[:, :, :, 0] + 1.0) * 0.5 * (in_width - 1),
            0.0,
            in_width - 1,
        )
        grid_y = ivy.clip(
            (normalised_grid[:, :, :, 1] + 1.0) * 0.5 * (in_height - 1),
            0.0,
            in_height - 1,
        )
    else:
        grid_x = ivy.clip(
            (normalised_grid[:, :, :, 0] + 1.0) * 0.5 * in_width, 0.0, in_width - 1
        )
        grid_y = ivy.clip(
            (normalised_grid[:, :, :, 1] + 1.0) * 0.5 * in_height, 0.0, in_height - 1
        )

    # Calculate the four corner points of the grid cells
    x0 = grid_x.floor().astype("int32")
    y0 = grid_y.floor().astype("int32")

    # Ensure that the grid_x and grid_y indices do not exceed input tensor dimensions
    x0 = ivy.clip(x0, 0, in_width - 1)
    y0 = ivy.clip(y0, 0, in_height - 1)
    x1 = ivy.clip(x0 + 1, 0, in_width - 1)
    y1 = ivy.clip(y0 + 1, 0, in_height - 1)

    # Calculate the relative distance of the grid coordinates from the corner points
    wx = grid_x - x0
    wy = grid_y - y0

    # Gather pixel values of the 4 corner points for each point in the output grid
    i00 = input[:, :, y0, x0]  # top-left corner
    i10 = input[:, :, y0, x1]  # top-right
    i01 = input[:, :, y1, x0]  # bottom-left
    i11 = input[:, :, y1, x1]  # bottomright

    #  bilinear interpolation
    interpolated = (
        i00 * (1 - wx) * (1 - wy)
        + i10 * wx * (1 - wy)
        + i01 * (1 - wx) * wy
        + i11 * wx * wy
    )

    return interpolated
    # the output shape batch, channels, out_height, out_width

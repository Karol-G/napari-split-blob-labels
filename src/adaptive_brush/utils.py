import numbers

def dynamic_slicing(array, slices, assign=None):
    """Dynamic slicing of an array with arbitrary number of dimensions.
    Slices must match number of dimensions. A single slice can either be None, i, [i, None],  [None, j] or [i, j].
    None is equal to ':'. i/j is the slice index and can be negative.
    There might be a faster version: https://stackoverflow.com/questions/24398708/slicing-a-numpy-array-along-a-dynamically-specified-axis/37729566#37729566"""
    slc = [slice(None)] * len(array.shape)
    axis_squeeze = []
    for axis in range(len(array.shape)):
        if slices[axis] is None:  # Take all element of axis: array[..., :, ...]
            slc[axis] = slice(None)
        elif isinstance(slices[axis], numbers.Number):  # Single index for axis: array[..., i, ...]
            slc[axis] = slice(slices[axis], slices[axis]+1)
            axis_squeeze.append(axis - len(axis_squeeze))
        else:  # Range from i to j: array[..., i:j, ...]
            slc[axis] = slice(slices[axis][0], slices[axis][1])
    if assign is None:  # Return the sliced array
        sliced_array = array[tuple(slc)]
        for axis in axis_squeeze:  # Squeeze axis with single index
            sliced_array = sliced_array.squeeze(axis)
        return sliced_array
    else:  # Assign value/s to the slice
        array[tuple(slc)] = assign
        return


def normalize(x, x_min=None, x_max=None):
    if x_min is None:
        x_min = x.min()

    if x_max is None:
        x_max = x.max()

    if x_min == x_max:
        return x * 0
    else:
        return (x - x.min()) / (x.max() - x.min())


def rgb2gray(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray
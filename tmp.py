import numpy as np

def dynamic_slicing(array, slices):
    """Dynamic slicing of an array with arbitrary number of dimensions.
    Slices must match number of dimensions. A single slice can either be [None], [i, None] or [None, j]. None is equal to ':'.
    i is the slice index and can be negative."""
    slc = [slice(None)] * len(array.shape)
    axis_squeeze = []
    for axis in range(len(array.shape)):
        if slices[axis] is None:
            slc[axis] = slice(None)
        elif isinstance(slices[axis], int):
            slc[axis] = slice(slices[axis], slices[axis]+1)
            axis_squeeze.append(axis - len(axis_squeeze))
        else:
            slc[axis] = slice(slices[axis][0], slices[axis][1])
    sliced_array = array[tuple(slc)]
    for axis in axis_squeeze:
        sliced_array = sliced_array.squeeze(axis)
    return sliced_array


my_arr = np.zeros((100, 100, 100))
new_arr = dynamic_slicing(my_arr, [1, 3, 4])
print(new_arr.shape)
print(new_arr)


new_arr = my_arr[1, 3, 4]
print(new_arr.shape)
print(new_arr)
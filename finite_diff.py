#!/usr/bin/env python3

import numpy as np

# [deri][accuracy_level][coefs]
fwd_coefs = {
    1: {
        1: np.array([-1, 1], dtype=np.double),
        2: np.array([-3/2, 2, -1/2], dtype=np.double),
        3: np.array([-11/6, 3, -3/2, 1/3], dtype=np.double),
        4: np.array([-25/12, 4, -3, 4/3, -1/4], dtype=np.double),
        5: np.array([-137/60, 5, -5, 10/3, -5/4, 1/5], dtype=np.double),
        6: np.array([-49/20, 6, -15/2, 20/3, -15/4, 6/5, -1/6], dtype=np.double),
    },
    2: {
        1: np.array([1, -2, 1], dtype=np.double),
        2: np.array([2, -5, 4, -1], dtype=np.double),
        3: np.array([35/12, -26/3, 19/2, -14/3, 11/12], dtype=np.double),
        4: np.array([15/4, -77/6, 107/6, -13, 61/12, -5/6], dtype=np.double),
        5: np.array([203/45, -87/5, 117/4, -254/9, 33/2, -27/5, 137/180], dtype=np.double),
        6: np.array([469/90, -223/10, 879/20, -949/18, 41, -201/10, 1019/180], dtype=np.double),
    },
}

cen_coefs = {
    1: {
        1: np.array([-1/2, 0], dtype=np.double),
        2: np.array([1/12, -2/3, 0], dtype=np.double),
        3: np.array([-1/60, 3/20, -3/4, 0], dtype=np.double),
        4: np.array([1/280, -4/105, 1/5, -4/5, 0], dtype=np.double),
    },
    2: {
        1: np.array([1, -2], dtype=np.double),
        2: np.array([-1/12, 4/3, -5/2], dtype=np.double),
        3: np.array([1/90, -3/20, 3/2, -49/18], dtype=np.double),
        4: np.array([-1/560, 8/315, -1/5, 8/5, -205/72], dtype=np.double),
    },
}


def forward(data, step, deri_order=1, accuracy_level=1, start_index=-1):
    """
    @brief
    Use forward finite difference method to calculate the derivatives.

    @param start_index: The starting index of the first data element corresponding
           to numerical step=0. Default to -1, which set the FIRST element in
           the array as the starting point.
    @param data: array like. Starting from `start_index` and looking up FORWARD
           for n elements to evalate the numerical derivative. Other elements,
           if there are, are ignored. These found data elements correspond to
           numerical step=0, 1, 2 and so on.
    @param step: double. numerical step length.
    @param deri_order: integer. derivative order, default to 1.
    @param accuracy_level: interger. accuracy level, default to 1.
    @return deri: double. numerical derivative.
    """
    if deri_order < 0:
        raise Exception('deri_order needs to be positive integer.')
    if accuracy_level < 0:
        raise Exception('accuracy_level needs to be positive integer.')

    coef = np.zeros(0)
    try:
        global fwd_coefs
        coef = fwd_coefs[deri_order][accuracy_level]
    except:
        raise Exception(
            'Cannot find coefficient. deri_order or accuracy_level is wrong.')

    data = np.array(data, dtype=np.double)
    n = int(coef.size)
    if start_index < 0:
        start_index = 0
    right = start_index + n
    if right > data.size:
        raise Exception('No enough number of data.')
    used_data = data[start_index:] if right == data.size else data[start_index: right]
    return coef.dot(used_data) / (abs(step)**deri_order)


def backward(data, step, deri_order=1, accuracy_level=1, start_index=-1):
    """
    @brief
    Use backward finite difference method to calculate the derivatives.

    @param start_index: The starting index of the first data element corresponding
           to numerical step=0. Default to -1, which set the LAST element in
           the array as the starting point.
    @param data: array like. Starting from `start_index` and looking up BACKWARD
           for n elements to evalate the numerical derivative. Other elements,
           if there are, are ignored. These found data elements correspond to
           numerical step=0, -1, -2 and so on.
    @param step: double. numerical step length.
    @param deri_order: integer. derivative order, default to 1.
    @param accuracy_level: interger. accuracy level, default to 1.
    @return deri: double. numerical derivative.
    """
    sign = 1
    if deri_order % 2 == 1:
        sign = -1
    data = np.array(data)[-1::-1]

    if start_index >= 0:
        start_index = data.size - start_index - 1
    return sign * forward(data, -step, deri_order=deri_order,
                          accuracy_level=accuracy_level, start_index=start_index)


def central(data, step, deri_order=1, accuracy_level=1, mid_index=-1):
    """
    @brief
    Use backward finite difference method to calculate the derivatives.

    @param mid_index: the index of array element that corresponds to central step
           (step=0). Default to -1, which sets the middle point of the data array
           `data.size // 2` corresponding to the step=0.
    @param data: array like. The middle n elements are used to evalate the numerical
           derivative. The middle index is specified by `mid_index`
    @param step: double. numerical step length.
    @param deri_order: integer. derivative order, default to 1.
    @param accuracy_level: interger. accuracy level, default to 1.
    @return deri: double. numerical derivative.
    """
    if deri_order < 0:
        raise Exception('deri_order needs to be positive integer.')
    if accuracy_level < 0:
        raise Exception('accuracy_level needs to be positive integer.')

    coef = np.zeros(0)
    try:
        global cen_coefs
        sign = 1
        if deri_order % 2 == 1:
            sign = -1
        coef = cen_coefs[deri_order][accuracy_level]
        coef = np.append(coef, sign * coef[-2::-1])
    except:
        raise Exception(
            'Cannot find coefficient. deri_order or accuracy_level is wrong.')

    data = np.array(data, dtype=np.double)
    n = int(coef.size)
    if mid_index == -1:
        mid_index = int(data.size//2)
    left = mid_index - int(n//2)
    right = mid_index + int(n//2) + 1
    used_data = None
    if right == data.size and left >= 0:
        used_data = data[left:]
    elif right < data.size and left >= 0:
        used_data = data[left: right]
    else:
        raise Exception(
            f'No enough number of data for central method, starting at middle-index {mid_index}.')

    return coef.dot(used_data) / (step**deri_order)

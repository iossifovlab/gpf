'''
Created on Feb 23, 2016

@author: lubo
'''
import numpy as np


def colormap_pvalue(p_val, lessmore='more'):
    if p_val == "NaN":
        return "rgb(255,255,255)"

    scale = 0
    if p_val >= 0:
        if p_val > 0.05:
            scale = 0
        else:
            if p_val < 1E-10:
                scale = 10
            else:
                scale = -np.log10(p_val)
            if scale > 5:
                scale = 5
            elif scale < 0:
                scale = 0

    intensity = int((5.0 - scale) * 255.0 / 5.0)
    if lessmore == 'more':
        color = "rgba(%d,%d,%d,180)" % (255, intensity, intensity)
    elif lessmore == 'less':
        color = "rgba(%d,%d,%d,180)" % (intensity, intensity, 255)
    else:
        color = "rgb(255,255,255)"
    return color


def format_pvalue(p_val):
    if p_val >= 0.0001:
        return str(round(p_val, 4))
    else:
        return str('%.1E' % p_val)

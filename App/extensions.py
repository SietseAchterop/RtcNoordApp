"""
Here some extentions for interactive use

doesn't work yet, gd not visible here.
How to solve cleanly?
"""

def myFirstExtension(n):
    # some stuff with the data
    s_1_data = gd.dataObject[0:n, 1]
    s_2_data = gd.dataObject[0:n, 2]
    return s_1_data + s_2_data

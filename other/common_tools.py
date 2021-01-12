import random
from time import sleep
from datetime import datetime
import numpy as np
import matplotlib.image as mimg
import os


def got_image(user):
    path = os.getcwd() + "/img/" + user
    return os.path.isfile(path + ".png")


def add_alpha(img_path):
    src = np.array(mimg.imread(img_path + ".jpg")) / 255
    n_pixels = src.shape[0]  # assuming square shape

    xx, yy = np.mgrid[:n_pixels, :n_pixels]
    circle = (xx - n_pixels // 2) ** 2 + (yy - n_pixels // 2) ** 2
    donut = (circle < (n_pixels // 2) ** 2)
    donut = donut.reshape(n_pixels, n_pixels, -1)
    array = np.concatenate((src, donut), axis=-1)

    mimg.imsave(img_path + ".png", array)


def string_to_int(x):
    res = x.replace('m', "000000")
    res = res.replace('k', "000")
    res = res.replace(',', "")
    res = res.replace('.', "")
    return int(res)


# TODO add capcbility to manage need of sleep based on data / sleep ratios
class Senpai:
    def __init__(self):
        self.sleeps = []  # [(start_time, end_time)]
        self.scrapes = []  # TODO

    def hibernate(self, time=400):
        print("-- sleeping for {}s --".format(time))
        self._sleep(time)

    # TODO add random hibernate
    def random_delay(self, time, can_hibernate=False):
        extra = random.random() * time / 3
        if time > 9:
            print("-- sleeping for {}s --".format(time))
        sleep(time + extra)
        # don't know if these should be tracked as well, how heavy the datetime object is

    def _sleep(self, time):
        sleep_start = datetime.now()
        interrupted = False
        t = 0
        while t < time:
            if interrupted:
                break
            sleep(5)
            t += 5
        sleep_end = datetime.now()
        self.sleeps.append((sleep_start, sleep_end))

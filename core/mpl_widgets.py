from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from global_variables import *
from PyQt5 import QtWidgets
import numpy as np


class MplAnimation(FigureCanvas):
    """ Функция отрисовки """
    def __init__(self, b, dpi=100):
        self.fig = Figure(dpi=dpi, facecolor=(.94, .94, .94))

        # Добавление области графа
        self.ax = self.fig.add_subplot(111, aspect='equal')
        self.clear_plot(b)

        # Инициализация
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot_circle(self, particle):
        # Рисование границ ячейки
        x, y, rad = particle.transform_world_to_screen()
        circle = plt.Circle((x, y), rad, facecolor='white', fill=True,
                            linewidth=0.9, antialiased=True, edgecolor="blue")
        self.ax.add_patch(circle)

    def plot_configuration(self, list_of_particles, title=""):
        for p in list_of_particles:
            self.plot_circle(p)
            self.ax.set_title(title)

    def plot_cell(self, b):
        self.ax.set_xlim(MPL_MIN_RANGE, MPL_MAX_RANGE)
        self.ax.set_ylim(MPL_MIN_RANGE, MPL_MAX_RANGE)

        # Сокрытие подписей осей
        self.ax.set_yticklabels([])
        self.ax.set_xticklabels([])

        # Отображения сетки - периода решетки
        # Перевод b в экранные координаты
        particle = Particle(b, 0)
        step, _, _ = particle.transform_world_to_screen()
        xy_positive = np.arange(0, MPL_MAX_RANGE, step/2.)
        xy_negative = xy_positive[::-1]
        xy_negative = [-x for x in xy_negative]
        xy_ticks = xy_negative + xy_positive

        self.ax.set_xticks(xy_ticks)
        self.ax.set_yticks(xy_ticks)

        self.ax.grid(linestyle="dotted", alpha=0.25)

        cell = plt.Rectangle((MPL_MIN_RANGE, MPL_MIN_RANGE),
                             2 * MPL_MAX_RANGE,
                             2 * MPL_MAX_RANGE,
                             color="black", fill=False, linestyle='dashdot')
        self.ax.add_patch(cell)

    def clear_plot(self, b):
        self.ax.clear()
        self.plot_cell(b)

    def get_ticks(self):
        x_ticks = list(self.ax.get_xticks())
        y_ticks = list(self.ax.get_yticks())
        return x_ticks, y_ticks

class MplGraphics(FigureCanvas):
    """ Функция отрисовки """
    def __init__(self, dpi=100):
        self.fig = Figure(dpi=dpi, facecolor=(.94, .94, .94), figsize=(7, 3))

        # Добавление области графа
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.add_text()

        # Инициализация
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def add_text(self):
        self.ax1.set_title("Усредненные параметры")
        self.ax1.set_xlabel("Временной шаг, с")
        self.ax1.set_ylabel("Энергия, Дж")

        self.ax2.set_xlabel("Временной шаг, с")
        self.ax2.set_ylabel("Температура, °C")

        self.ax1.grid(linestyle="dotted", alpha=0.65)
        self.ax2.grid(linestyle="dotted", alpha=0.65)

    def add_dot_ax1(self, x, y):
        self.ax1.plot(x, y, linestyle="dotted", marker="o", markersize=3, color='r')
        # ymin, ymax = min(y), max(y)
        # xmax, xmin = max(x), min(x)
        # additive_x = (xmax - xmin) * 0.1
        # additive_y = 0.5 * ymax
        # self.ax1.set_xlim(xmin, xmax + additive_x)
        # self.ax1.set_ylim(ymin - additive_y, ymax + additive_y)

    def add_dot_ax2(self, x, y):
        self.ax2.plot(x, y, linestyle="dotted", marker="o", markersize=3, color='b')

    def clear_plot(self):
        self.ax1.clear()
        self.ax2.clear()
        self.add_text()

    def get_ticks(self):
        x_ticks = list(self.ax.get_xticks())
        y_ticks = list(self.ax.get_yticks())
        return x_ticks, y_ticks
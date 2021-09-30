import interface_main_app

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtWidgets, QtCore
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import threading
import random
import sys
matplotlib.use('QT5Agg')

# Параметры частиц
PARTICLE_DIAMETER = 0.382e-9
PARTICLE_RADIUS = PARTICLE_DIAMETER / 2.
PARTICLE_MASS = 6.6335209e-26
L_CELL = 30. * PARTICLE_DIAMETER
L_MAX_RANGE = L_CELL / 2.
L_MIN_RANGE = -L_MAX_RANGE
TAO = 2e-12

# Параметры отрисовки
MPL_MAX_RANGE = 101.
MPL_MIN_RANGE = -101.
MPL_RADIUS = 2.

class Particle:
    def __init__(self, x, y, vx=0, vy=0, Ek=0, Ep=0, E=0, m=PARTICLE_MASS, radius=PARTICLE_RADIUS):
        # Координаты [метр]
        self.x = x
        self.y = y

        # Скорости [метр/с]
        self.vx = vx
        self.vy = vy

        # Энерегии [Дж]
        self.Ep = Ep
        self.Ek = Ek
        self.E = E

        # Масса [кг]
        self.mass = m
        self.radius = radius

    def transform_world_to_screen(self):
        del_xy_screen = MPL_MAX_RANGE - MPL_MIN_RANGE
        del_xy_world = L_MAX_RANGE - L_MIN_RANGE
        k = del_xy_screen / del_xy_world
        x = MPL_MIN_RANGE + k * (self.x - L_MIN_RANGE)
        y = MPL_MIN_RANGE + k * (self.y - L_MIN_RANGE)
        return x, y

class ParticleConfiguration:
    def __init__(self):
        print(1)

class MplCanvas(FigureCanvas):
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
        x, y = particle.transform_world_to_screen()
        circle = plt.Circle((x, y), MPL_RADIUS, facecolor="red", fill=True,
                            linewidth=0.5, antialiased=True, edgecolor="black")
        self.ax.add_patch(circle)

    def plot_cell(self, b):
        self.ax.set_xlim(MPL_MIN_RANGE, MPL_MAX_RANGE)
        self.ax.set_ylim(MPL_MIN_RANGE, MPL_MAX_RANGE)

        # Сокрытие подписей осей
        self.ax.set_yticklabels([])
        self.ax.set_xticklabels([])

        # Отображения сетки - периода решетки
        # Перевод b в экранные координаты
        particle = Particle(b, 0)
        step, _ = particle.transform_world_to_screen()
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
        x_ticks = self.ax.get_xticks()
        y_ticks = self.ax.get_yticks()
        print("x_ticks: ", x_ticks)
        print('y_ticks: ', y_ticks)
        return x_ticks, y_ticks

class Interface(QtWidgets.QMainWindow, interface_main_app.Ui_MainWindow):
    """ Класс-реализация интерфейса """
    def __init__(self):
        """ Конструктор """
        QtWidgets.QMainWindow.__init__(self)
        # Загрузка дизайна
        self.setupUi(self)
        # Конфигурация окна приложения
        self.setWindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint |
                            QtCore.Qt.WindowType.WindowCloseButtonHint |
                            QtCore.Qt.WindowType.WindowMinimizeButtonHint)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint)

        # Вывод констант в консоль
        print("\n[+] Параметры моделирования [+]\n")
        print("\tМасса частицы: ", PARTICLE_MASS)
        print("\tРадиус частицы: ", PARTICLE_RADIUS)
        print("\tРасчетная ячейка (30a): ", L_CELL)
        print("\tДиапазон значений расчетной ячейки: [", L_MIN_RANGE, ";", L_MAX_RANGE, "]")
        print("\n[+] Параметры моделирования [+]\n")

        # Вывод информации в GUI
        self.l_cell_edit.setText(str(L_CELL))
        self.a_parameter_edit.setText(str(PARTICLE_DIAMETER))
        self.tao_parameter_edit.setText(str(TAO))
        self.timestep_parameter_edit.setText(str(0.01 * TAO))

        # Связывание виджета анимации
        self.add_mpl()

        # Кнопка запуска
        self.set_particle_position_button.clicked.connect(self.draw_graph)
        self.clear_particle_position_button.clicked.connect(self.clear_graph)

        self.cell_period_combo.currentTextChanged.connect(self.cell_period_combo_logic)

    def cell_period_combo_logic(self, value):
        self.clear_graph()

    def add_mpl(self):
        self.canvas = MplCanvas(self.calc_b())
        self.toolbar = NavigationToolbar(self.canvas, self.canvas)
        self.verticalLayout_10.addWidget(self.canvas)

    def draw_graph(self):
        # Случайная частица
        x = random.uniform(L_MIN_RANGE, L_MAX_RANGE)
        y = random.uniform(L_MIN_RANGE, L_MAX_RANGE)
        particle = Particle(x, y)

        # Отрисовка
        self.canvas.clear_plot(self.calc_b())
        self.canvas.plot_circle(particle)
        self.canvas.draw()

    def clear_graph(self):
        self.canvas.clear_plot(self.calc_b())
        self.canvas.draw()

    def calc_b(self):
        b = self.cell_period_combo.currentText()
        b = float(b) * float(self.a_parameter_edit.text())
        return b

class StoppableThread(threading.Thread):
    """ Поток для вычисления переданной функции """
    def __init__(self, obj):
        """ Конструктор потока """
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()
        self.is_started = False
        self.is_finished = False
        self.object = obj

    def run(self):
        """ Запуск потока """
        self.is_started = True
        while not self.is_stopped():
            self.object()

    def stop(self):
        """ Завершение потока с помощью Event """
        self._stop.set()

    def is_stopped(self):
        """ Проверка состояния потока """
        return self._stop.is_set()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = Interface()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
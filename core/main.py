import interface_main_app

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtWidgets, QtCore
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import threading
import math
import sys
matplotlib.use('QT5Agg')

# Параметры частиц
PARTICLE_DIAMETER = 0.382e-9
PARTICLE_RADIUS = PARTICLE_DIAMETER / 2.
PARTICLE_MASS = 6.6335209e-26
# Параметры ячейки
L_CELL = 30. * PARTICLE_DIAMETER
L_MAX_RANGE = L_CELL / 2.
L_MIN_RANGE = -L_MAX_RANGE
# Характерное время системы
TAO = 2e-12
# Параметры обрезания
R1 = 1.1 * PARTICLE_DIAMETER
R2 = 1.8 * PARTICLE_DIAMETER
# Модуль потенциальной энергии взаимодействия при равновесии
D = 0.0103 * 1.602176487e-19

# Параметры отрисовки
MPL_MAX_RANGE = 101.
MPL_MIN_RANGE = -101.
MPL_RADIUS = 1.

class Particle:
    def __init__(self, x, y, vx=0, vy=0, m=PARTICLE_MASS, radius=PARTICLE_RADIUS):
        # Координаты [метр]
        self.x = x
        self.y = y

        # Скорости [метр/с]
        self.vx = vx
        self.vy = vy

        # Энергии [Дж]
        # Потенциальная энергия взаимодействия частицы со
        # всеми остальными частицами системы
        self.Ep = 0.0
        # Сила, действующая на i-ю частицу со стороны всех
        # других частиц
        self.F = 0.0

        # Масса [кг]
        self.mass = m
        self.radius = radius

    def transform_world_to_screen(self):
        del_xy_screen = MPL_MAX_RANGE - MPL_MIN_RANGE
        del_xy_world = L_MAX_RANGE - L_MIN_RANGE
        k = del_xy_screen / del_xy_world
        x = MPL_MIN_RANGE + k * (self.x - L_MIN_RANGE)
        y = MPL_MIN_RANGE + k * (self.y - L_MIN_RANGE)
        rad = MPL_MIN_RANGE + k * (self.radius - L_MIN_RANGE)
        return x, y, rad

    def transform_screen_to_world(self):
        del_xy_screen = MPL_MAX_RANGE - MPL_MIN_RANGE
        del_xy_world = L_MAX_RANGE - L_MIN_RANGE
        k = del_xy_screen / del_xy_world
        x = self.x - MPL_MIN_RANGE + k * L_MIN_RANGE
        x /= k
        y = self.y - MPL_MIN_RANGE + k * L_MIN_RANGE
        y /= k
        rad = self.radius - MPL_MIN_RANGE + k * L_MIN_RANGE
        rad /= k
        return x, y, rad

class ParticleConfiguration:
    def __init__(self, particles_quantity, a_parameter, b_parameter, canvas):
        self.particles_quantity = particles_quantity
        self.a = a_parameter
        self.b = b_parameter
        self.canvas = canvas
        self.ticks, _ = self.canvas.get_ticks()
        self.configuration = []
        self.configure_particles()

        # Энергии
        self.E = 0.0
        self.Ek = 0.0
        self.Ep = 0.0

    def configure_particles(self):
        configuration_coordinates = []
        # ВАЖНО! Рассматривается ТОЛЬКО число частиц формата n*n
        particles_count_in_line = round(math.sqrt(self.particles_quantity))
        for i in range(0, particles_count_in_line):
            middle_index = math.trunc(len(self.ticks) / 2)
            configuration_coordinates.append(self.ticks[middle_index])
            self.ticks.pop(middle_index)

        for coord_y in configuration_coordinates:
            for coord_x in configuration_coordinates:
                particle = Particle(coord_x, coord_y)
                x, y, rad = particle.transform_screen_to_world()
                particle.x = x
                particle.y = y

                self.configuration.append(particle)

    # Расчет энергий
    def calculate_kinetic(self):
        sum_v = 0.0
        for i, particle in enumerate(self.configuration):
            sum_v += particle.vx ** 2 + particle.vy ** 2
        kinetic_energy = PARTICLE_MASS / 2.
        kinetic_energy *= sum_v
        self.Ek = kinetic_energy
        print("Кинетическая энергия: ", self.Ek)

    def distance(self, particle1, particle2):
        """ Расстояние между частицами """
        dx = particle2.x - particle1.x
        dy = particle2.y - particle1.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        return distance

    def calculate_cutoff_ratio(self, distance):
        """ Вычисление коэффициента обрезания """
        if distance <= R1:
            return 1
        elif R1 <= distance <= R2:
            upper = distance - R1
            lower = R1 - R2
            buffer = (upper / lower) ** 2
            result = (1 - buffer) ** 2
            return result
        elif distance >= R2:
            return 0

    def potential_of_lennard_jones(self, particle1, particle2):
        """ Вычисление модифицированного потенциала Л-Д """
        # Обозначение переменных
        e = D
        sigma = self.a
        root_of = 6
        sigma = sigma / 2 ** (1/float(root_of))
        distance = self.distance(particle1, particle2)
        K = self.calculate_cutoff_ratio(distance)

        # Вычисление потенциала
        buffer_first = (sigma / distance) ** 12
        buffer_second = (sigma / distance) ** 6
        potential = 4 * e * (buffer_first - buffer_second) * K
        return potential

    def calculate_potential(self):
        potential_energy = 0.0
        for i, i_particle in enumerate(self.configuration):
            for j, j_particle in enumerate(self.configuration):
                if i < j:
                    potential_energy += self.potential_of_lennard_jones(i_particle, j_particle)

        self.Ep = potential_energy
        print("Потенциальная энергия: ", self.Ep)

    def calculate_full_energy(self):
        self.E = self.Ek + self.Ep
        print("Полная энергия: ", self.E)

    # Расчет сил, координат и скоростей
    def calculate_potential_for_particle(self):
        for i, i_particle in enumerate(self.configuration):
            potential = 0.0
            for j, j_particle in enumerate(self.configuration):
                if i != j:
                    potential += self.potential_of_lennard_jones(i_particle, j_particle)
            i_particle.Ep = potential

    def calculate_forces(self):
        print(1)

    def calculate_verle(self):
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
        x, y, rad = particle.transform_world_to_screen()
        circle = plt.Circle((x, y), rad, facecolor='white', fill=True,
                            linewidth=0.9, antialiased=True, edgecolor="red")
        self.ax.add_patch(circle)

    def plot_configuration(self, list_of_particles):
        for p in list_of_particles:
            self.plot_circle(p)

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
        self.config = []

        # Связывание элементов управления
        self.add_mpl()
        self.set_particle_position_button.clicked.connect(self.draw_graph)
        self.clear_particle_position_button.clicked.connect(self.clear_graph)
        self.cell_period_combo.currentTextChanged.connect(self.cell_period_combo_logic)
        self.start_button.clicked.connect(self.start_button_logic)

    def cell_period_combo_logic(self, value):
        self.clear_graph()

    def add_mpl(self):
        self.canvas = MplCanvas(self.calc_b())
        self.toolbar = NavigationToolbar(self.canvas, self.canvas)
        self.verticalLayout_10.addWidget(self.canvas)

    def draw_graph(self):
        # Конфигурация системы
        self.cfg = ParticleConfiguration(int(self.count_of_particles_combo.currentText()),
                                             float(self.a_parameter_edit.text()),
                                             self.calc_b(),
                                             self.canvas)

        # Отрисовка
        self.canvas.clear_plot(self.calc_b())
        self.canvas.plot_configuration(self.cfg.configuration)
        self.canvas.draw()

    def clear_graph(self):
        self.canvas.clear_plot(self.calc_b())
        self.canvas.draw()

    def calc_b(self):
        b = self.cell_period_combo.currentText()
        b = float(b) * float(self.a_parameter_edit.text())
        return b

    def start_button_logic(self):
        if len(self.cfg.configuration) > 0:
            self.cfg.calculate_potential()
            self.cfg.calculate_kinetic()
            self.cfg.calculate_full_energy()
            self.cfg.calculate_potential_for_particle()
        else:
            print("[+] Нет размещенных частиц!")

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
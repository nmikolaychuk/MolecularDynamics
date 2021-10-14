import random

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from mpl_widgets import MplAnimation, MplGraphics
from PyQt5 import QtWidgets, QtCore
from global_variables import *
import interface_main_app
import matplotlib
import threading
import math
import sys
import time
matplotlib.use('QT5Agg')


class ParticleConfiguration:
    def __init__(self, particles_quantity, a_parameter, b_parameter,
                 time_step, canvas, is_coords_rand, is_speeds_rand):
        self.particles_quantity = particles_quantity
        self.a = a_parameter
        self.b = b_parameter
        self.time_step = time_step
        self.canvas = canvas
        # Чекпоинты для внесения случайности в значения
        self.is_coords_random = is_coords_rand
        self.is_speeds_random = is_speeds_rand
        self.rand_percent = 0.05
        self.speeds_range_rand = 60

        self.ticks, _ = self.canvas.get_ticks()
        self.configuration = []
        self.configure_particles()
        self.start_summary_pulse()

        # Энергии
        self.E = 0.0
        self.Ek = 0.0
        self.Ep = 0.0
        self.temperature = 0.0

        self.calculate_potential_for_particle()
        self.calculate_forces()

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

                if self.is_coords_random:
                    rand_range = self.b * self.rand_percent
                    x_rand = random.uniform(-rand_range, rand_range)
                    y_rand = random.uniform(-rand_range, rand_range)
                    x += x_rand
                    y += y_rand

                particle.x = x
                particle.y = y

                if self.is_speeds_random:
                    x_rand = random.uniform(-self.speeds_range_rand, self.speeds_range_rand)
                    y_rand = random.uniform(-self.speeds_range_rand, self.speeds_range_rand)
                    particle.vx = x_rand
                    particle.vy = y_rand

                self.configuration.append(particle)

    def start_summary_pulse(self):
        vx_sum = 0.0
        vy_sum = 0.0
        for particle in self.configuration:
            vx_sum += particle.vx
            vy_sum += particle.vy

        particles_count = len(self.configuration)
        vx_sum /= particles_count
        vy_sum /= particles_count

        for particle in self.configuration:
            particle.vx -= vx_sum
            particle.vy -= vy_sum

        print(vx_sum, vy_sum)

    # Расчет энергий
    def calculate_kinetic(self):
        sum_v = 0.0
        for i, particle in enumerate(self.configuration):
            sum_v += particle.vx ** 2 + particle.vy ** 2
        kinetic_energy = PARTICLE_MASS / 2.
        kinetic_energy *= sum_v
        self.Ek = kinetic_energy
        # print("Кинетическая энергия: ", self.Ek)

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
        # print("Потенциальная энергия: ", self.Ep)

    def calculate_full_energy(self):
        self.E = self.Ek + self.Ep
        # print("Полная энергия: ", self.E)

    def calculate_temperature(self):
        v_sum = 0.0
        for particle in self.configuration:
            v_sum += particle.vx ** 2 + particle.vy ** 2

        upper = v_sum * self.configuration[0].mass
        lower = 2.0 * len(self.configuration) * K_B
        self.temperature = upper / lower
        self.temperature -= 273.15
        # print("Температура в системе: ", self.temperature)
        # print('\n')

    # Расчет сил, координат и скоростей
    def calculate_potential_for_particle(self):
        """ Расчет потецниальной энергии для каждой частицы """
        for i, i_particle in enumerate(self.configuration):
            potential = 0.0
            for j, j_particle in enumerate(self.configuration):
                if i != j:
                    potential += self.potential_of_lennard_jones(i_particle, j_particle)
            i_particle.Ep = potential

    def calculate_forces(self):
        """ Расчет сил """
        r0_6 = PARTICLE_DIAMETER ** 6
        for i, i_particle in enumerate(self.configuration):
            du_dx_sum = 0.0
            du_dy_sum = 0.0
            for j, j_particle in enumerate(self.configuration):
                if i != j:
                    # Квадрат расстояния между центрами i и j частицы
                    rij_2 = (i_particle.x - j_particle.x) ** 2 + (i_particle.y - j_particle.y) ** 2
                    buffer_x = (i_particle.x - j_particle.x) / rij_2 ** 4
                    buffer_y = (i_particle.y - j_particle.y) / rij_2 ** 4
                    # Рассчет обрезающего множителя
                    dist = self.distance(i_particle, j_particle)
                    K = self.calculate_cutoff_ratio(dist)
                    du_dx_sum += (r0_6 / rij_2 ** 3 - 1) * buffer_x * K
                    du_dy_sum += (r0_6 / rij_2 ** 3 - 1) * buffer_y * K

            du_dx = -12 * D * r0_6 * du_dx_sum
            du_dy = -12 * D * r0_6 * du_dy_sum
            i_particle.Fx = -du_dx
            i_particle.Fy = -du_dy

    def calculate_verle(self):
        """ Скоростная форма алгоритма Верле """
        Fk_x = []
        Fk_y = []
        for i_particle in self.configuration:
            # Расчет координат
            # Координата X
            accel_x = i_particle.Fx / (2 * i_particle.mass)
            accel_x *= self.time_step ** 2
            x_new = i_particle.x + i_particle.vx * self.time_step + accel_x
            i_particle.x = x_new
            Fk_x.append(i_particle.Fx)

            # Координата Y
            accel_y = i_particle.Fy / (2 * i_particle.mass)
            accel_y *= self.time_step ** 2
            y_new = i_particle.y + i_particle.vy * self.time_step + accel_y
            i_particle.y = y_new
            Fk_y.append(i_particle.Fy)

        # Пересчет сил
        self.calculate_forces()

        for i, i_particle in enumerate(self.configuration):
            # Расчет скоростей
            # Vx
            accel_avg_x = (i_particle.Fx + Fk_x[i]) / (2. * i_particle.mass)
            accel_avg_x *= self.time_step
            i_particle.vx += accel_avg_x

            # Vy
            accel_avg_y = (i_particle.Fy + Fk_y[i]) / (2. * i_particle.mass)
            accel_avg_y *= self.time_step
            i_particle.vy += accel_avg_y


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
        self.steps_quantity.setText(str(STEPS))
        self.timestep_parameter_edit.setText(str(0.01 * TAO))
        self.graph_interval_edit.setText(str(GRAPH_INTERVAL))
        self.cfg = None

        # Связывание элементов управления
        self.add_mpl()
        self.set_particle_position_button.clicked.connect(self.set_start_config)
        self.clear_particle_position_button.clicked.connect(self.clear_graph)
        self.cell_period_combo.currentTextChanged.connect(self.cell_period_combo_logic)
        self.steps_quantity.textChanged.connect(self.steps_quantity_logic)
        self.graph_interval_edit.textChanged.connect(self.graph_interval_logic)
        self.start_button.clicked.connect(self.start_button_logic)
        self.stop_button.clicked.connect(self.stop_button_logic)
        self.rand_coord_check.clicked.connect(self.rand_coord_logic)
        self.rand_speed_check.clicked.connect(self.rand_speed_logic)

        self.steps = STEPS
        self.graph_interval = GRAPH_INTERVAL
        self.anim = None
        self.paused = False
        self.frame = 0
        self.is_started = False
        self.thread = StoppableThread(self.calculation)

        self.average_e = 0.0
        self.average_t = 0.0

        self.x_values_e = []
        self.y_values_e = []

        self.x_values_t = []
        self.y_values_t = []
        self.counter = 0

        self.is_coords_random = False
        self.is_speeds_random = False

    def rand_coord_logic(self):
        if self.rand_coord_check.isChecked():
            self.is_coords_random = True
        else:
            self.is_coords_random = False
    def rand_speed_logic(self):
        if self.rand_speed_check.isChecked():
            self.is_speeds_random = True
        else:
            self.is_speeds_random = False

    def cell_period_combo_logic(self):
        self.clear_graph()

    def steps_quantity_logic(self):
        text = self.steps_quantity.text()
        if text:
            self.steps = int(text)
        else:
            self.steps = 5000

    def graph_interval_logic(self):
        text = self.graph_interval_edit.text()
        if text:
            self.graph_interval = int(text)
        else:
            self.graph_interval = 25

    def add_mpl(self):
        # Анимация
        self.canvas = MplAnimation(self.calc_b())
        spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.toolbar = NavigationToolbar(self.canvas, self.canvas, coordinates=False)
        self.verticalLayout_10.addWidget(self.toolbar)
        self.verticalLayout_10.addWidget(self.canvas)

        # Графики
        self.graphics = MplGraphics()
        self.toolbar = NavigationToolbar(self.graphics, self.graphics, coordinates=True)
        self.verticalLayout_11.addWidget(self.toolbar)
        self.verticalLayout_11.addWidget(self.graphics)

    def set_start_config(self):
        # Конфигурация системы
        self.cfg = ParticleConfiguration(int(self.count_of_particles_combo.currentText()),
                                         float(self.a_parameter_edit.text()),
                                         self.calc_b(),
                                         float(self.timestep_parameter_edit.text()),
                                         self.canvas,
                                         self.is_coords_random,
                                         self.is_speeds_random)
        self.draw_graph()

    def draw_graph(self, title=""):
        # Отрисовка
        self.canvas.clear_plot(self.calc_b())
        self.canvas.plot_configuration(self.cfg.configuration, title)
        self.canvas.draw()
        self.canvas.flush_events()
        time.sleep(0.001)

    def draw_plot1(self, x, y):
        self.graphics.add_dot_ax1(x, y)
        self.graphics.draw()
        self.graphics.flush_events()
        time.sleep(0.001)

    def draw_plot2(self, x, y):
        self.graphics.add_dot_ax2(x, y)
        self.graphics.draw()
        self.graphics.flush_events()
        time.sleep(0.001)

    def clear_graph(self):
        self.cfg = None
        self.canvas.clear_plot(self.calc_b())
        self.is_started = False
        self.paused = False
        self.frame = 0
        self.canvas.draw()
        self.graphics.clear_plot()
        self.graphics.draw()
        self.average_t = 0.0
        self.average_e = 0.0
        self.x_values_e = []
        self.y_values_e = []
        self.x_values_t = []
        self.y_values_t = []
        self.counter = 0

    def calc_b(self):
        b = self.cell_period_combo.currentText()
        b = float(b) * float(self.a_parameter_edit.text())
        return b

    def calculation(self):
        # Расчет параметров на новом временном шаге
        self.cfg.calculate_verle()
        self.cfg.calculate_kinetic()
        self.cfg.calculate_potential()
        self.cfg.calculate_full_energy()
        self.cfg.calculate_temperature()

        self.average_e += self.cfg.E
        self.average_t += self.cfg.temperature
        self.counter += 1

        # Вывод начальной потенциальной энергии системы
        if self.frame == 0:
            potential = str(self.cfg.Ep)
            self.start_potential_edit.setText(potential)

        self.frame += 1
        if self.frame % self.graph_interval == 0:
            self.draw_graph("Временной шаг: %s" % str(self.frame))

            self.average_e /= self.counter
            self.x_values_e.append(self.frame)
            self.y_values_e.append(self.average_e)

            self.draw_plot1(self.x_values_e, self.y_values_e)
            if self.frame >= 500:
                self.average_t /= self.counter

                self.x_values_t.append(self.frame)
                self.y_values_t.append(self.average_t)
                self.draw_plot2(self.x_values_t, self.y_values_t)

            self.average_e = 0.0
            self.average_t = 0.0
            self.counter = 0

        if self.frame >= self.steps:
            self.thread.is_finished = True
            self.thread.stop()

    def start_button_logic(self):
        if self.cfg is not None and self.frame < self.steps:
            if not self.thread.is_started:
                self.thread.start()
            elif self.thread.is_stopped() and self.thread.is_finished:
                self.thread = StoppableThread(self.calculation)
                self.thread.start()
        else:
            print("[+] Нет размещенных частиц или закончились шаги по времени!")

    def stop_button_logic(self):
        print("stop")
        if self.thread.is_started and not self.thread.is_stopped():
            self.thread.stop()
            self.thread.is_finished = True

    def keyPressEvent(self, event):
        super(Interface, self).keyPressEvent(event)

        if event.key() == QtCore.Qt.Key.Key_F11:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()

        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.stop_button.click()
            self.close()

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
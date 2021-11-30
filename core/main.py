from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from mpl_widgets import MplAnimation, MplGraphics, MplResearch
from PyQt5 import QtWidgets, QtCore
from global_variables import *
import interface_research_app
import interface_main_app
import matplotlib
import threading
import sys
import time
matplotlib.use('QT5Agg')


class ResearchApp(QtWidgets.QMainWindow, interface_research_app.Ui_MainWindow):
    """ Класс-реализация окна исследования """
    def __init__(self, parent_object):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        # Конфигурация окна приложения
        self.setWindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint |
                            QtCore.Qt.WindowType.WindowCloseButtonHint |
                            QtCore.Qt.WindowType.WindowMinimizeButtonHint)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint)
        self.parent_object = parent_object
        self.parent_object.is_research_running = True
        self.add_mpl()

        # Гиперпараметры для системы
        self.b_start_value = 0.9
        self.b_step_value = 0.02
        self.b_steps_quantity = 30
        self.iter_quantity = STEPS
        self.time_step = 0.01 * TAO
        self.particles_quantity = 100
        self.is_random_coords = False
        self.is_random_speeds = False
        self.current_out = 0
        self.current_step = 0
        self.sum_temperature = 0.0

        self.research_steps.setText(str(self.iter_quantity))
        self.research_steps.textChanged.connect(self.steps_quantity_logic)

        # Инициализируем конфигурацию частиц
        self.config = None
        self.x_values = []
        self.y_values = []

        self.research_thread = StoppableThread(self.calculate_research)

        self.start_button.clicked.connect(self.start_calculation)
        self.stop_button.clicked.connect(self.stop_calculation)
        self.clear_plot.clicked.connect(self.clear_plot_logic)

        self.title_text = "Зависимость скорости испарения капли от температуры"

    def clear_plot_logic(self):
        self.stop_calculation()
        self.x_values.clear()
        self.y_values.clear()
        self.graphics.clear_plot()
        self.graphics.draw()
        self.current_out = 0
        self.current_step = 0
        self.sum_temperature = 0.0

    def steps_quantity_logic(self):
        self.iter_quantity = int(self.research_steps.text())

    def add_mpl(self):
        # Графики
        self.graphics = MplResearch()
        self.toolbar = NavigationToolbar(self.graphics, self.graphics, coordinates=True)
        self.verticalLayout.addWidget(self.toolbar)
        self.horizontal_layout_graphics.addWidget(self.graphics)

    def research_inner_loop(self, print_text):
        # Расчет 5000 итераций для выбранного b
        self.sum_temperature = 0.0
        for iter in range(self.current_step, self.iter_quantity):
            sys.stdout.write(print_text + "; Текущий шаг: %s" % iter)
            sys.stdout.flush()
            if self.research_thread.is_stopped():
                self.current_step = iter
                return

            self.config.calculate_next_time_step()
            if iter >= 500:
                self.sum_temperature += self.config.temperature

        self.current_step = 0

        # Средняя температура
        self.sum_temperature /= (self.iter_quantity - 500)
        self.x_values.append(self.sum_temperature)

        # Количество испарившихся частиц
        evaporated_particles = self.particles_quantity - len(self.config.configuration)
        self.y_values.append(evaporated_particles)

        self.draw_plot(self.x_values, self.y_values)

        with open("../research.txt", mode="a") as f:
            f.write(str(evaporated_particles) + ", " + str(self.sum_temperature) + "\n")
        f.close()

    def calculate_research(self):
        # Гиперпараметры исследования
        for number in range(self.current_out, self.b_steps_quantity + 1):
            # Создание конфигурации
            self.config = ParticleConfiguration(self.particles_quantity,
                                                PARTICLE_DIAMETER,
                                                PARTICLE_DIAMETER,
                                                self.time_step,
                                                is_coords_rand=True,
                                                is_speeds_rand=True)

            print_text = "\rТекущий эксперимент: %s" % self.current_out
            self.research_inner_loop(print_text)

            if self.research_thread.is_stopped():
                self.current_out = number
                break

            self.current_out += 1

        self.research_thread.is_finished = True
        self.research_thread.stop()

    def start_calculation(self):
        if not self.research_thread.is_started:
            self.research_thread.start()
        elif self.research_thread.is_stopped() and self.research_thread.is_finished:
            self.research_thread = StoppableThread(self.calculate_research)
            self.research_thread.start()
        else:
            print("[+] Нет размещенных частиц или закончились шаги по времени!")

    def stop_calculation(self):
        if self.research_thread.is_started and not self.research_thread.is_stopped():
            print("stop")
            self.research_thread.stop()
            self.research_thread.is_finished = True

    def draw_plot(self, x, y, title="Зависимость скорости испарения капли от температуры"):
        self.graphics.add_dot_ax(x, y)
        self.graphics.ax.set_title(title)
        self.graphics.draw()
        self.graphics.flush_events()
        time.sleep(0.001)


    def keyPressEvent(self, event):
        super(ResearchApp, self).keyPressEvent(event)

        if event.key() == QtCore.Qt.Key.Key_F11:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()

        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.stop_button.click()
            self.close()

    def closeEvent(self, event):
        self.parent_object.is_research_running = False

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
        self.research_evaporation.clicked.connect(self.research_evaporation_logic)
        self.is_research_running = False
        self.research_object = None

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

    def research_evaporation_logic(self):
        if not self.is_research_running:
            self.research_object = ResearchApp(self)
            self.research_object.show()

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
        self.cfg.calculate_next_time_step()

        self.average_e += self.cfg.E
        self.average_t += self.cfg.temperature
        self.counter += 1

        # Вывод начальной потенциальной энергии системы
        if self.frame == 0:
            potential = str(self.cfg.Ep)
            self.start_potential_edit.setText(potential)

        if self.frame % self.graph_interval == 0:
            title_string = "Временной шаг: %s" % str(self.frame) +\
                           "; Количество частиц: %s" % str(len(self.cfg.configuration))
            self.draw_graph(title_string)

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

        self.frame += 1

        if self.frame > self.steps or len(self.cfg.configuration) == 0:
            title_string = "Временной шаг: %s" % str(self.frame) + \
                           "; Количество частиц: %s" % str(len(self.cfg.configuration))
            self.draw_graph(title_string)
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
import random
import math
import numpy as np


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

# Число шагов моделирования
STEPS = 5000

# Интервал отрисовки
GRAPH_INTERVAL = 25

# Параметры обрезания
R1 = 1.1 * PARTICLE_DIAMETER
R2 = 1.8 * PARTICLE_DIAMETER
# Модуль потенциальной энергии взаимодействия при равновесии
D = 0.0103 * 1.602176487e-19

# Параметры отрисовки
MPL_MAX_RANGE = 101.
MPL_MIN_RANGE = -101.
MPL_RADIUS = 1.

# Постоянная Больцмана
K_B = 1.380649e-23


class Particle:
    """ Класс, описывающий частицу """
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
        self.Fx = 0.0
        self.Fy = 0.0

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
    def __init__(self, particles_quantity, a_parameter, b_parameter,
                 time_step, is_coords_rand = False,
                 is_speeds_rand = False, is_research_speed=False, system_temp=0):
        self.particles_quantity = particles_quantity
        self.a = a_parameter
        self.b = b_parameter
        self.time_step = time_step
        self.ticks = self.get_ticks_by_b_parameter(self.b)
        # Чекпоинты для внесения случайности в значения
        self.is_coords_random = is_coords_rand
        self.is_speeds_random = is_speeds_rand
        self.is_research_speed = is_research_speed
        self.system_temp = system_temp

        self.rand_percent = 0.01
        self.speeds_range_rand = 20

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

    def get_ticks_by_b_parameter(self, b_world):
        buffer = Particle(b_world, 0)
        b_screen, _, _ = buffer.transform_world_to_screen()
        xy_positive = np.arange(0, MPL_MAX_RANGE, b_screen / 2.)
        xy_negative = xy_positive[::-1]
        xy_negative = [-x for x in xy_negative]
        xy_ticks = xy_negative + xy_positive
        return list(xy_ticks)

    def sign_randomization(self):
        return 1 if random.random() < 0.5 else -1

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

                if self.is_research_speed:
                    temp = self.system_temp
                    upper = 2 * K_B * temp
                    lower = PARTICLE_MASS
                    # Полная скорость каждой частицы для достижения заданной температуры
                    vi = upper / lower
                    sign_x = self.sign_randomization()
                    sign_y = self.sign_randomization()
                    partition_x = random.random() * vi
                    partition_y = vi - partition_x
                    particle.vx = sign_x * partition_x
                    particle.vy = sign_y * partition_y


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

    def check_evaporated_particles(self):
        """ Расчет числа испарившихся частиц """
        for i, particle in enumerate(self.configuration):
            if L_MIN_RANGE <= particle.x <= L_MAX_RANGE and L_MIN_RANGE <= particle.y <= L_MAX_RANGE:
                pass
            else:
                del self.configuration[i]

    def calculate_next_time_step(self):
        if len(self.configuration) > 0:
            self.calculate_verle()
            self.calculate_kinetic()
            self.calculate_potential()
            self.calculate_full_energy()
            self.calculate_temperature()
            self.check_evaporated_particles()

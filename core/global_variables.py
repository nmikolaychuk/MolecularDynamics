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
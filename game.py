import pygame
import sys
import math
import random
import time

class GameLoop:
    def __init__(self):
        # Inicializar o pygame
        pygame.init()

        # Configurações da tela
        self.WIDTH, self.HEIGHT = 1000, 600
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Drifter")

        # Cores
        self.WHITE = (255, 255, 255)
        self.RED = (255, 255, 255)
        self.BLACK = (0, 0, 0)

        # Clock para controlar a taxa de frames
        self.clock = pygame.time.Clock()

        # Criar o jogador e o alvo
        self.player = Player(self.WIDTH // 2, self.HEIGHT // 2, self.WIDTH, self.HEIGHT)
        self.target = Target(self.WIDTH, self.HEIGHT)

        self.bg_image = pygame.image.load('sprites/floor.jpg')
        self.bg = self.crop_bg()

        # Estado de controle
        self.running = True
        self.debug_mode = False

        # Configuração da fonte para exibir texto
        self.s_font = pygame.font.Font(None, 24)
        self.m_font = pygame.font.Font(None, 36)
        self.g_font = pygame.font.Font(None, 48)

        self.paused = True

        self.dark_overlay = self.create_dark_overlay()

    def create_dark_overlay(self):
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))  # Cria a surface do tamanho da tela
        overlay.set_alpha(100)  # Define a transparência (0 a 255, sendo 0 totalmente transparente)
        overlay.fill((0, 0, 0))  # Preenche a surface com preto

        return overlay

    def crop_bg(self):
        """Recorta a imagem de fundo para o tamanho da tela (WIDTH x HEIGHT)."""
        image_width, image_height = self.bg_image.get_size()

        # Calcular a posição do recorte (centro da imagem)
        x = (image_width - self.WIDTH) // 2
        y = (image_height - self.HEIGHT) // 2

        # Recortar a imagem para o tamanho da tela
        cropped_bg = self.bg_image.subsurface((x, y, self.WIDTH, self.HEIGHT))
        
        return cropped_bg

    def draw_text(self, *texts, x=0, y=0, color=(0, 0, 0), line_spacing=5):
        """Função para exibir várias linhas de texto na tela."""
        for text in texts:
            text_surface = self.s_font.render(text, True, color)
            self.screen.blit(text_surface, (x, y))
            y += text_surface.get_height() + line_spacing

    def draw_interface(self):
        speedometer = self.player.get_speedometer()
        speedometer_text = self.m_font.render('Velocímetro', True, (0, 0, 0))

        self.screen.blit(speedometer, (0, self.HEIGHT - speedometer.get_height()))
        self.screen.blit(speedometer_text, (0, self.HEIGHT - speedometer.get_height() - speedometer_text.get_height()))

    def tick(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.WIDTH, self.HEIGHT = event.w, event.h
                self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)

                self.player.update_boundaries(self.WIDTH, self.HEIGHT)
                self.target.update_boundaries(self.WIDTH, self.HEIGHT)

                self.bg = self.crop_bg()
                self.dark_overlay = self.create_dark_overlay()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    self.target.cycle_mode()

                elif event.key == pygame.K_d:
                    self.debug_mode = not self.debug_mode

                elif event.key == pygame.K_f:
                    self.player.drift_mode = not self.player.drift_mode
                    
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused

        if not self.paused:
            self.player.update()
            self.target.update(self.player)

        self.screen.blit(self.bg, (0, 0))

        if self.debug_mode:
            self.target.draw_debug(self.screen)
            self.player.draw_debug(self.screen, self.target)

        self.target.draw(self.screen)
        self.player.draw(self.screen)

        self.draw_interface()

        if self.debug_mode:
            self.draw_text(
                f'Distancia da parede: {self.get_distance_to_wall():.0f}',
                f'Angulo do objetivo: {self.get_angle_to_target():.0f}°',
                f'Velocidade atual: {self.player.speed:.2f}',
                x=2, y=2)
            
        if self.paused:
            paused_text = self.m_font.render('simulação pausada', True, (255, 255, 255))
            self.screen.blit(self.dark_overlay, (0, 0))
            self.screen.blit(paused_text, (self.WIDTH / 2 - paused_text.get_width() / 2, self.HEIGHT / 2 - paused_text.get_height() / 2))

        pygame.display.flip()
        self.clock.tick(60)

    def is_running(self):
        return self.running

    def get_distance_to_wall(self):
        _, _, distance = self.player.cast_ray()
        return distance

    def get_angle_to_target(self):
        return self.player.calculate_angle_to_target(self.target.rect.center)

    def rotate(self, direction):
        if self.paused:
            return

        self.player.rotate(direction)

    def apply_speed_change(self, amount):
        if self.paused:
            return
        
        self.player.change_speed_by(amount)

class Player:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.angle = 0  # Ângulo de rotação em graus
        self.speed = 0  # Velocidade inicial
        self.min_speed = 5
        self.max_speed = 20

        car_sprite = pygame.image.load("sprites/car.png")  # Altere para o caminho da sua imagem
        car_sprite = pygame.transform.scale(car_sprite, (49, 25))
        self.image = car_sprite
        self.original_image = self.image

        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.WIDTH = width
        self.HEIGHT = height

        self.drift_mode = True

        self.braked_hard = False
        self.drift_direction = ''
        self.drift_factor = 0
        self.target_drift_factor = 0

        self.tires_sprite = pygame.image.load("sprites/tires.png")
        self.tires_sprite = pygame.transform.scale(self.tires_sprite, (49, 25))
        self.drift_sprites = []

        self.speedometer_sprite = pygame.image.load("sprites/speedometer.jpg")

    def rotate(self, direction):
        amount = 5 * (1 - (self.speed - self.min_speed) / self.max_speed) ** 2 # Quando mais lento, mais vira
        if direction == 'left':
            amount *= -1
        
        if self.drift_mode:
            if self.braked_hard and abs(amount) > 3:
                self.target_drift_factor = amount * 10
                self.drift_direction = direction
            elif abs(amount) < 4.75:
                self.target_drift_factor = 0

            if self.drift_direction != direction:
                self.target_drift_factor = 0
        else:
            self.target_drift_factor = 0

        self.angle = (self.angle + amount) % 360
        self.image = pygame.transform.rotate(self.original_image, -(self.angle + self.drift_factor))
        self.rect = self.image.get_rect(center=(self.x, self.y))

        
    def change_speed_by(self, amount):
        if amount < -0.7:
            self.braked_hard = True
        else:
            self.braked_hard = False

        self.speed = max(self.min_speed, min(self.speed + amount, self.max_speed))

    def move(self):
        radians = math.radians(-self.angle)
        dx = math.cos(radians) * self.speed
        dy = math.sin(radians) * self.speed
        self.x += dx
        self.y -= dy
        self.rect.center = (self.x, self.y)

    def cast_ray(self):
        radians = math.radians(-self.angle)
        x, y = self.x, self.y
        while 0 < x < self.WIDTH and 0 < y < self.HEIGHT:
            x += math.cos(radians)
            y -= math.sin(radians)
        distance = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        return x, y, distance

    def calculate_target_distance(self, target_position):
        dx = target_position[0] - self.x
        dy = target_position[1] - self.y
        distance = math.sqrt(dx**2 + dy**2)
        return distance

    def calculate_angle_to_target(self, target_position):
        dx = target_position[0] - self.x
        dy = target_position[1] - self.y  
        target_angle = math.degrees(math.atan2(dy, dx)) % 360
        angle_difference = (target_angle - self.angle + 360) % 360
        if angle_difference > 180:
            angle_difference -= 360
        return angle_difference
    
    def get_speedometer(self):
        """Recorta o velocímetro da esquerda para a direita com base na velocidade atual."""
        # Obter as dimensões da imagem do velocímetro
        width, height = self.speedometer_sprite.get_size()
        
        # Calcula a largura visível com base na razão de speed / max_speed
        visible_width = int((self.speed / self.max_speed) * width)
        
        # Define o retângulo de corte (corta da esquerda para a direita)
        crop_rect = pygame.Rect(0, 0, visible_width, height)
        
        # Cria a subimagem recortada
        cropped_image = self.speedometer_sprite.subsurface(crop_rect)
        
        return cropped_image
    
    def update(self):
        self.move()

        if self.speed > 7.5: 
            self.target_drift_factor = 0

        if self.target_drift_factor < self.drift_factor:
            self.drift_factor -= 2
        elif self.target_drift_factor > self.drift_factor:
            self.drift_factor += 2

        if self.drift_factor:
            tire_image = pygame.transform.rotate(self.tires_sprite, -(self.angle + self.drift_factor))
            self.drift_sprites.append({
                'sprite': tire_image,
                'dest': self.rect.topleft,
                'time': time.time()
            })

        dead_drift_sprites = []
        for s in self.drift_sprites:
            if time.time() - s['time'] > 5:
                dead_drift_sprites.append(s)
            else:
                break
        for s in dead_drift_sprites:
            self.drift_sprites.remove(s)

    def draw(self, surface: pygame.Surface):
        for s in self.drift_sprites:
            surface.blit(s['sprite'], s['dest'])
        surface.blit(self.image, self.rect.topleft)

    def draw_debug(self, surface, target):
        wx, wy, _ = self.cast_ray()
        pygame.draw.line(surface, (0, 0, 255), self.rect.center, (wx, wy))
        pygame.draw.line(surface, (0, 255, 0), self.rect.center, target.rect.center)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=1)

    def update_boundaries(self, width, height):
        self.WIDTH = width
        self.HEIGHT = height


class Target:
    def __init__(self, width, height, margin=100):
        self.image = pygame.image.load("sprites/target.png")  # Altere para o caminho da sua imagem
        self.image = pygame.transform.scale(self.image, (20, 20))
        self.rect = self.image.get_rect()
        
        # Definição da margem e área de movimento
        self.MARGIN = margin
        self.WIDTH = width - 2 * self.MARGIN  # 100% da largura menos a margem
        self.HEIGHT = height - 2 * self.MARGIN  # 100% da altura menos a margem

        # Calcular as bordas (limites) de movimentação
        self.LEFT_BOUND = self.MARGIN
        self.TOP_BOUND = self.MARGIN

        # Velocidades iniciais
        self.x_speed = random.uniform(-10, 10)
        self.y_speed = random.uniform(-10, 10)
        
        self.move_to_random_position()
        self.last_direction_change = time.time()

        self.modes = ['static', 'moving', 'mouse']
        self.mode = 'static'

    def move_to_random_position(self):
        self.rect.x = random.randint(self.LEFT_BOUND, self.LEFT_BOUND + self.WIDTH - self.rect.width)
        self.rect.y = random.randint(self.TOP_BOUND, self.TOP_BOUND + self.HEIGHT - self.rect.height)

    def move(self, max_speed=7):
        self.rect.x += self.x_speed
        self.rect.y += self.y_speed

        # Alterar direção em intervalos aleatórios
        if time.time() - self.last_direction_change > random.uniform(0.3, 1):
            self.x_speed = random.uniform(-max_speed, max_speed)
            self.y_speed = random.uniform(-max_speed, max_speed)
            self.last_direction_change = time.time()

        if self.rect.left < self.LEFT_BOUND or self.rect.right > self.LEFT_BOUND + self.WIDTH:
            self.x_speed = -self.x_speed

        if self.rect.top < self.TOP_BOUND or self.rect.bottom > self.TOP_BOUND + self.HEIGHT:
            self.y_speed = -self.y_speed

    def set_position(self, x, y):
        self.rect.center = (x, y)

    def cycle_mode(self):
        index = self.modes.index(self.mode)
        next_mode = (index + 1) % 3
        self.mode = self.modes[next_mode]

    def update(self, player):
        if self.mode == 'static':
            if player.rect.colliderect(self.rect):
                self.move_to_random_position()

        elif self.mode == 'moving':
            self.move()

        elif self.mode == 'mouse':
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.set_position(mouse_x, mouse_y)

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)

    def draw_debug(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), (self.LEFT_BOUND, self.TOP_BOUND, self.WIDTH, self.HEIGHT), width=2)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=1)

    def update_boundaries(self, width, height, margin=None):
        """Atualiza os limites de largura e altura para a tela menos 'margin' de cada lado.
        Se a largura ou a altura forem menores que o tamanho mínimo necessário, usa o tamanho da tela.
        """
        if margin is not None:
            self.MARGIN = margin

        # Calcula a largura e a altura, mas nunca permite que sejam menores que o tamanho do sprite
        self.WIDTH = max(1, width - 2 * self.MARGIN)
        self.HEIGHT = max(1, height - 2 * self.MARGIN)

        # Certifique-se de que a largura seja pelo menos maior que a largura mínima do sprite
        if hasattr(self, 'rect'):
            self.WIDTH = max(self.WIDTH, self.rect.width)
            self.HEIGHT = max(self.HEIGHT, self.rect.height)
        
        # Define as bordas de acordo com o tamanho da largura e altura
        self.LEFT_BOUND = max(0, self.MARGIN)
        self.TOP_BOUND = max(0, self.MARGIN)

if __name__ == '__main__':
    game = GameLoop()
    while game.is_running():
        game.tick()
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
        self.WIDTH, self.HEIGHT = 800, 600
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Sprite Rotacionável e Movível")

        # Cores
        self.WHITE = (255, 255, 255)
        self.RED = (255, 255, 255)
        self.BLACK = (0, 0, 0)

        # Clock para controlar a taxa de frames
        self.clock = pygame.time.Clock()

        # Carregar imagem do sprite
        self.sprite_image = pygame.image.load("sprites/car.png")  # Altere para o caminho da sua imagem
        self.sprite_image = pygame.transform.scale(self.sprite_image, (49, 25))  # Redimensionar se necessário

        # Criar o jogador e o alvo
        self.player = Player(self.WIDTH // 2, self.HEIGHT // 2, self.sprite_image, self.WIDTH, self.HEIGHT)
        self.target = Target(self.WIDTH, self.HEIGHT)

        # Estado de controle
        self.running = True
        self.target_start_time = time.time()

        # Configuração da fonte para exibir texto
        self.font = pygame.font.Font(None, 20)  # Fonte padrão, tamanho 36

    def draw_text(self, *texts, x=0, y=0, color=(0, 0, 0), line_spacing=5):
        """Função para exibir várias linhas de texto na tela."""
        for i, text in enumerate(texts):
            text_surface = self.font.render(text, True, color)
            self.screen.blit(text_surface, (x, y + i * (text_surface.get_height() + line_spacing)))

    def tick(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.WIDTH, self.HEIGHT = event.w, event.h
                self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
                self.player.update_boundaries(self.WIDTH, self.HEIGHT)
                self.target.update_boundaries(self.WIDTH, self.HEIGHT)
        
        if __name__ == '__main__':
            keys = pygame.key.get_pressed()

            if keys[pygame.K_UP]:  # Tecla CIMA
                self.player.change_speed_by(0.1)
            
            if keys[pygame.K_DOWN]:  # Tecla BAIXO
                self.player.change_speed_by(-0.1)
            
            if keys[pygame.K_LEFT]:  # Tecla ESQUERDA
                self.player.rotate('left')
            
            if keys[pygame.K_RIGHT]:  # Tecla DIREITA
                self.player.rotate('right')

        mouse_x, mouse_y = pygame.mouse.get_pos()

        self.player.update()
        self.target.move()
        # self.target.set_position(mouse_x, mouse_y)

        if self.player.rect.colliderect(self.target.rect):
            self.target.move_to_random_position()

        self.screen.fill(self.WHITE)

        self.target.draw_debug(self.screen)
        self.player.draw_debug(self.screen, self.target)

        self.target.draw(self.screen)
        self.player.draw(self.screen)

        self.draw_text(
            f'Distancia da parede: {self.get_distance_to_wall():.0f}',
            f'Angulo do objetivo: {self.get_angle_to_target():.0f}',
            f'Velocidade atual: {self.player.speed:.0f}',
            x=0, y=0)

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
        self.player.rotate(direction)

    def apply_speed_change(self, amount):
        self.player.change_speed_by(amount)

class Player:
    def __init__(self, x, y, sprite_image, width, height):
        self.x = x
        self.y = y
        self.angle = 0  # Ângulo de rotação em graus
        self.speed = 1  # Velocidade inicial
        self.min_speed = 5
        self.max_speed = 20
        self.image = sprite_image
        self.original_image = self.image
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.WIDTH = width
        self.HEIGHT = height

        self.braked_hard = False
        self.speed_before_braking = 0
        self.drift_direction = ''
        self.drift_factor = 0
        self.target_drift_factor = 0

    def rotate(self, direction):
        amount = 5 * (1 - (self.speed - self.min_speed) / self.max_speed) ** 2 # Quando mais lento, mais vira
        if direction == 'left':
            amount *= -1

        if self.braked_hard and abs(amount) > 3:
            self.target_drift_factor = amount * 10
            self.drift_direction = direction
        elif abs(amount) < 4.75:
            self.target_drift_factor = 0

        if self.drift_direction != direction:
            self.target_drift_factor = 0

        self.angle = (self.angle + amount) % 360
        self.image = pygame.transform.rotate(self.original_image, -(self.angle + self.drift_factor))
        self.rect = self.image.get_rect(center=(self.x, self.y))
        
    def change_speed_by(self, amount):
        if amount < -0.7:
            self.braked_hard = True
            self.speed_before_braking = self.speed
        else:
            self.braked_hard = False

        self.speed = max(self.min_speed, min(self.speed + amount, self.max_speed))

    def move(self):
        radians = math.radians(-self.angle)
        dx = math.cos(radians) * self.speed
        dy = math.sin(radians) * self.speed
        self.x += dx
        self.y -= dy
        if self.rect.left < 0:
            self.x = self.rect.width // 2
        if self.rect.right > self.WIDTH:
            self.x = self.WIDTH - self.rect.width // 2
        if self.rect.top < 0:
            self.y = self.rect.height // 2
        if self.rect.bottom > self.HEIGHT:
            self.y = self.HEIGHT - self.rect.height // 2
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
    
    def update(self):
        self.move()

        if self.target_drift_factor < self.drift_factor:
            self.drift_factor -= 3
        elif self.target_drift_factor > self.drift_factor:
            self.drift_factor += 3

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)

    def draw_debug(self, surface, target):
        wx, wy, _ = self.cast_ray()
        pygame.draw.line(surface, (0, 0, 255), self.rect.center, (wx, wy))
        pygame.draw.line(surface, (0, 255, 0), self.rect.center, target.rect.center)

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

    def move_to_random_position(self):
        min_distance = 60  # Distância mínima das paredes
        self.rect.x = random.randint(self.LEFT_BOUND + min_distance, self.LEFT_BOUND + self.WIDTH - min_distance - self.rect.width)
        self.rect.y = random.randint(self.TOP_BOUND + min_distance, self.TOP_BOUND + self.HEIGHT - min_distance - self.rect.height)

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

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)

    def draw_debug(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), (self.LEFT_BOUND, self.TOP_BOUND, self.WIDTH, self.HEIGHT), width=2)

    def update_boundaries(self, width, height, margin=None):
        """Atualiza os limites de largura e altura para a tela menos 'margin' de cada lado."""
        if margin is not None:
            self.MARGIN = margin
        self.WIDTH = width - 2 * self.MARGIN
        self.HEIGHT = height - 2 * self.MARGIN
        self.LEFT_BOUND = self.MARGIN
        self.TOP_BOUND = self.MARGIN

if __name__ == '__main__':
    game = GameLoop()
    while game.is_running():

        game.tick()
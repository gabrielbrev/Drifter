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
        self.sprite_image = pygame.image.load("sprite.png")  # Altere para o caminho da sua imagem
        self.sprite_image = pygame.transform.scale(self.sprite_image, (49, 25))  # Redimensionar se necessário

        # Criar o jogador e o alvo
        self.player = Player(self.WIDTH // 2, self.HEIGHT // 2, self.sprite_image, self.WIDTH, self.HEIGHT)
        self.target = Target(self.WIDTH, self.HEIGHT)

        # Estado de controle
        self.running = True
        self.target_start_time = time.time()

        # Configuração da fonte para exibir texto
        self.font = pygame.font.Font(None, 20)  # Fonte padrão, tamanho 36

    def draw_text(self, *texts, x=0, y=0, color=(0, 0, 0), line_spacing=10):
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

        self.player.move()
        # self.target.move_eliptic(3, 0.3, 5)
        self.target.move_random()
        # self.target.set_position(mouse_x, mouse_y)

        if self.player.rect.colliderect(self.target.rect):
            self.target.move_to_random_position()
            self.target_start_time = time.time()

        self.screen.fill(self.WHITE)
        self.player.draw(self.screen, self.target)
        self.target.draw(self.screen)

        self.draw_text(
            f'Distancia da parede: {self.get_distance_to_wall():.0f}',
            f'Distancia do objevo: {self.get_target_distance():.0f}',
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

    def get_target_distance(self):
        return self.player.calculate_target_distance(self.target.rect.center)

    def get_angle_to_target(self):
        return self.player.calculate_angle_to_target(self.target.rect.center)

    def get_time_chasing_target(self):
        return time.time() - self.target_start_time

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

    def rotate(self, direction):
        amount = 5 * (1 - (self.speed - self.min_speed) / self.max_speed) # Quando mais lento, mais vira
        if direction == 'left':
            amount *= -1
        self.angle = (self.angle + amount) % 360
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def change_speed_by(self, amount):
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

    def draw(self, surface, target):
        surface.blit(self.image, self.rect.topleft)

    def update_boundaries(self, width, height):
        self.WIDTH = width
        self.HEIGHT = height


class Target:
    def __init__(self, width, height):
        self.image = pygame.image.load("target.png")  # Altere para o caminho da sua imagem
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.WIDTH = width
        self.HEIGHT = height
        self.x_speed = random.uniform(-10, 10)
        self.y_speed = random.uniform(-10, 10)
        self.move_to_random_position()
        self.last_direction_change = time.time()

    def move_to_random_position(self):
        min_distance = 60  # Distância mínima da parede
        self.rect.x = random.randint(min_distance, self.WIDTH - min_distance - self.rect.width)
        self.rect.y = random.randint(min_distance, self.HEIGHT - min_distance - self.rect.height)

    def move_random(self):
        self.rect.x += self.x_speed
        self.rect.y += self.y_speed

        # Alterar direção em intervalos aleatórios
        if time.time() - self.last_direction_change > random.uniform(0.3, 1):
            self.x_speed = random.uniform(-10, 10)
            self.y_speed = random.uniform(-10, 10)
            self.last_direction_change = time.time()

        if self.rect.left < 0 or self.rect.right > self.WIDTH:
            self.x_speed = -self.x_speed

        if self.rect.top < 0 or self.rect.bottom > self.HEIGHT:
            self.y_speed = -self.y_speed

    def move_eliptic(self, ellipse_speed=0.5, speed_variation=0.01, max_speed=1):
        # Parâmetros para controlar a forma e a variação do tamanho da elipse
        t = time.time()  # Tempo corrente
        a = (self.WIDTH // 4) * (1 + 0.2 * math.sin(t * 0.2))  # Semi-eixo maior varia lentamente
        b = (self.HEIGHT // 4) * (1 + 0.2 * math.cos(t * 0.2))  # Semi-eixo menor varia lentamente

        # Tempo normalizado no intervalo [0, 2π] com menor frequência controlada pelo usuário
        theta = (t * ellipse_speed % (2 * math.pi))  # Controlado pela velocidade da elipse

        # Calcula a posição elíptica usando funções seno e cosseno
        self.rect.x = int(self.WIDTH // 2 + a * math.cos(theta) + self.x_speed)
        self.rect.y = int(self.HEIGHT // 2 + b * math.sin(theta) + self.y_speed)

        # Pequena variação de velocidade para tornar o movimento mais orgânico
        self.x_speed += random.uniform(-speed_variation, speed_variation)  # Alteração controlada
        self.y_speed += random.uniform(-speed_variation, speed_variation)  # Alteração controlada

        # Limitação de velocidade para evitar acelerações excessivas
        self.x_speed = max(-max_speed, min(self.x_speed, max_speed))
        self.y_speed = max(-max_speed, min(self.y_speed, max_speed))

        # Garante que o target fique dentro dos limites da tela
        if self.rect.left < 0:
            self.rect.left = 0
            self.x_speed = abs(self.x_speed)  # Rebote
        if self.rect.right > self.WIDTH:
            self.rect.right = self.WIDTH
            self.x_speed = -abs(self.x_speed)  # Rebote
        if self.rect.top < 0:
            self.rect.top = 0
            self.y_speed = abs(self.y_speed)  # Rebote
        if self.rect.bottom > self.HEIGHT:
            self.rect.bottom = self.HEIGHT
            self.y_speed = -abs(self.y_speed)  # Rebote


    def set_position(self, x, y):
        self.rect.center = (x, y)

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)

    def update_boundaries(self, width, height):
        self.WIDTH = width
        self.HEIGHT = height

if __name__ == '__main__':
    game = GameLoop()
    while game.is_running():

        game.tick()
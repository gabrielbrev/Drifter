from fuzzy import FuzzyController
from game import GameLoop


game = GameLoop();
controller = FuzzyController()

while game.is_running():
    distancia_parede = game.get_distance_to_wall()
    distancia_objetivo = game.get_target_distance()
    angulo = game.get_angle_to_target()

    saidas = controller.compute(angulo, distancia_parede, distancia_objetivo)

    if saidas['virar'] > 0:
        game.rotate('right')
    elif saidas['virar'] < 0:
        game.rotate('left')

    game.apply_speed_change(saidas['velocidade'])

    game.tick()
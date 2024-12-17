from fuzzy import FuzzyController
from game import GameLoop

game = GameLoop();
controle = FuzzyController()

while game.is_running():
    distancia_parede = game.get_distance_to_wall()
    angulo = game.get_angle_to_target()

    saidas = controle.computar(angulo, distancia_parede, gerar_relatorio=game.requested_snapshot())

    if saidas['virar'] > 0:
        game.rotate('right')
    elif saidas['virar'] < 0:
        game.rotate('left')

    game.apply_speed_change(saidas['velocidade'])

    game.tick()
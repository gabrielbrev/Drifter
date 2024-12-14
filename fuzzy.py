import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt

class FuzzyController:
    def __init__(self):
        # Definindo as variáveis de entrada
        self.curva = ctrl.Antecedent(np.arange(-180, 181, 1), 'curva')
        self.distancia_parede = ctrl.Antecedent(np.arange(0, 1440, 1), 'distancia_parede')  # Agora o universo é maior que 200
        self.distancia_objetivo = ctrl.Antecedent(np.arange(0, 1440, 1), 'distancia_objetivo')

        # Definindo as variáveis de saída
        self.virar = ctrl.Consequent(np.arange(-1, 1.1, 0.5), 'virar')  # Comando de virar agora é -1, 0 ou 1
        self.velocidade = ctrl.Consequent(np.arange(-2.5, 0.3, 0.01), 'velocidade')  # Delta de velocidade no intervalo [-2.5, 0.3]

        self._define_membership_functions()
        self._define_rules()
        self._create_control_system()

    def _define_membership_functions(self):
        """Define as funções de pertinência (fuzzy sets) para as variáveis de entrada e saída."""
        # Funções de pertinência para a variável de entrada "distancia"
        self.distancia_parede['perto'] = fuzz.trapmf(self.distancia_parede.universe, [0, 0, 75, 100])
        self.distancia_parede['medio'] = fuzz.trimf(self.distancia_parede.universe, [75, 100, 150])
        self.distancia_parede['longe'] = fuzz.trapmf(self.distancia_parede.universe, [100, 150, np.inf, np.inf])

        self.distancia_objetivo['perto'] = fuzz.trapmf(self.distancia_objetivo.universe, [0, 0, 10, 30])
        self.distancia_objetivo['longe'] = fuzz.trapmf(self.distancia_objetivo.universe, [20, 50, np.inf, np.inf])

        # Funções de pertinência para a variável de entrada "curva"
        self.curva['fechada_esq'] = fuzz.trapmf(self.curva.universe, [-180, -180, -120, -45])
        self.curva['media_esq'] = fuzz.trimf(self.curva.universe, [-120, -45, -15])
        self.curva['aberta_esq'] = fuzz.trimf(self.curva.universe, [-45, -15, 0])
        self.curva['aberta_dir'] = fuzz.trimf(self.curva.universe, [0, 15, 45])
        self.curva['media_dir'] = fuzz.trimf(self.curva.universe, [15, 45, 120])
        self.curva['fechada_dir'] = fuzz.trapmf(self.curva.universe, [45, 120, 180, 180])

        # Funções de pertinência para a variável de saída "delta de velocidade"
        self.velocidade['frear_muito'] = fuzz.trapmf(self.velocidade.universe, [-2.5, -2.5, -2, -1.5])
        self.velocidade['frear_medio'] = fuzz.trimf(self.velocidade.universe, [-2, -1, 0])
        self.velocidade['frear_pouco'] = fuzz.trimf(self.velocidade.universe, [-0.5, 0, 0.1])
        self.velocidade['manter'] = fuzz.trimf(self.velocidade.universe, [0, 0.1, 0.2])
        self.velocidade['acelerar'] = fuzz.trapmf(self.velocidade.universe, [0.1, 0.2, 0.3, 0.3])

        # Funções de pertinência para a variável de saída "virar" (somente -1, 0 e 1)
        self.virar['esquerda'] = fuzz.trimf(self.virar.universe, [-1, -1, 0])
        self.virar['manter'] = fuzz.trimf(self.virar.universe, [-0.5, 0, 0.5])
        self.virar['direita'] = fuzz.trimf(self.virar.universe, [0, 1, 1])

    def _define_rules(self):
        """Define as regras fuzzy para controlar a lógica."""
        # Regras para controle de virar
        self.rules_virar = [
            # ctrl.Rule(self.curva['fechada_esq'] | self.curva['media_esq'], self.virar['esquerda']),
            # ctrl.Rule(self.curva['aberta_esq'] | self.curva['aberta_dir'], self.virar['manter']),
            # ctrl.Rule(self.curva['fechada_dir'] | self.curva['media_dir'], self.virar['direita']),

            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_parede['perto'], self.virar['esquerda']),
            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_parede['medio'], self.virar['esquerda']),
            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_parede['longe'], self.virar['esquerda']),

            ctrl.Rule(self.curva['media_esq'] & self.distancia_parede['perto'], self.virar['esquerda']),
            ctrl.Rule(self.curva['media_esq'] & self.distancia_parede['medio'], self.virar['esquerda']),
            ctrl.Rule(self.curva['media_esq'] & self.distancia_parede['longe'], self.virar['esquerda']),

            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_parede['perto'], self.virar['esquerda']),
            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_parede['medio'], self.virar['esquerda']),
            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_parede['longe'], self.virar['manter']),

            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_parede['perto'], self.virar['direita']),
            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_parede['medio'], self.virar['direita']),
            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_parede['longe'], self.virar['direita']),

            ctrl.Rule(self.curva['media_dir'] & self.distancia_parede['perto'], self.virar['direita']),
            ctrl.Rule(self.curva['media_dir'] & self.distancia_parede['medio'], self.virar['direita']),
            ctrl.Rule(self.curva['media_dir'] & self.distancia_parede['longe'], self.virar['direita']),

            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_parede['perto'], self.virar['direita']),
            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_parede['medio'], self.virar['direita']),
            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_parede['longe'], self.virar['manter']),
        ]

        # Regras para controle de velocidade
        self.rules_velocidade = [
            # ctrl.Rule((self.curva['fechada_esq'] | self.curva['fechada_dir']) & self.distancia_parede['perto'] & self.distancia_objetivo['perto'], self.velocidade['frear_muito']),
            # ctrl.Rule((self.curva['fechada_esq'] | self.curva['fechada_dir']) & self.distancia_parede['perto'] & self.distancia_objetivo['longe'], self.velocidade['frear_muito']),
            # ctrl.Rule((self.curva['fechada_esq'] | self.curva['fechada_dir']) & self.distancia_parede['medio'] & self.distancia_objetivo['perto'], self.velocidade['frear_muito']),
            # ctrl.Rule((self.curva['fechada_esq'] | self.curva['fechada_dir']) & self.distancia_parede['medio'] & self.distancia_objetivo['longe'], self.velocidade['frear_medio']),
            # ctrl.Rule((self.curva['fechada_esq'] | self.curva['fechada_dir']) & self.distancia_parede['longe'] & self.distancia_objetivo['perto'], self.velocidade['frear_pouco']),
            # ctrl.Rule((self.curva['fechada_esq'] | self.curva['fechada_dir']) & self.distancia_parede['longe'] & self.distancia_objetivo['longe'], self.velocidade['manter']),

            # ctrl.Rule((self.curva['media_esq'] | self.curva['media_dir']) & self.distancia_parede['perto'] & self.distancia_objetivo['perto'], self.velocidade['frear_muito']),
            # ctrl.Rule((self.curva['media_esq'] | self.curva['media_dir']) & self.distancia_parede['perto'] & self.distancia_objetivo['longe'], self.velocidade['frear_muito']),
            # ctrl.Rule((self.curva['media_esq'] | self.curva['media_dir']) & self.distancia_parede['medio'] & self.distancia_objetivo['perto'], self.velocidade['frear_pouco']),
            # ctrl.Rule((self.curva['media_esq'] | self.curva['media_dir']) & self.distancia_parede['medio'] & self.distancia_objetivo['longe'], self.velocidade['frear_medio']),
            # ctrl.Rule((self.curva['media_esq'] | self.curva['media_dir']) & self.distancia_parede['longe'] & self.distancia_objetivo['perto'], self.velocidade['frear_pouco']),
            # ctrl.Rule((self.curva['media_esq'] | self.curva['media_dir']) & self.distancia_parede['longe'] & self.distancia_objetivo['longe'], self.velocidade['manter']),

            # ctrl.Rule((self.curva['aberta_esq'] | self.curva['aberta_dir']) & self.distancia_parede['perto'] & self.distancia_objetivo['perto'], self.velocidade['frear_muito']),
            # ctrl.Rule((self.curva['aberta_esq'] | self.curva['aberta_dir']) & self.distancia_parede['perto'] & self.distancia_objetivo['longe'], self.velocidade['frear_muito']),
            # ctrl.Rule((self.curva['aberta_esq'] | self.curva['aberta_dir']) & self.distancia_parede['medio'] & self.distancia_objetivo['perto'], self.velocidade['frear_pouco']),
            # ctrl.Rule((self.curva['aberta_esq'] | self.curva['aberta_dir']) & self.distancia_parede['medio'] & self.distancia_objetivo['longe'], self.velocidade['acelerar']),
            # ctrl.Rule((self.curva['aberta_esq'] | self.curva['aberta_dir']) & self.distancia_parede['longe'] & self.distancia_objetivo['perto'], self.velocidade['frear_pouco']),
            # ctrl.Rule((self.curva['aberta_esq'] | self.curva['aberta_dir']) & self.distancia_parede['longe'] & self.distancia_objetivo['longe'], self.velocidade['acelerar']),

            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_parede['perto'], self.velocidade['frear_muito']),
            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_parede['medio'], self.velocidade['frear_medio']),
            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_parede['longe'], self.velocidade['frear_medio']),

            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_parede['perto'], self.velocidade['frear_muito']),
            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_parede['medio'], self.velocidade['frear_medio']),
            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_parede['longe'], self.velocidade['frear_medio']),

            ctrl.Rule(self.curva['media_esq'] & self.distancia_parede['perto'], self.velocidade['frear_medio']),
            ctrl.Rule(self.curva['media_esq'] & self.distancia_parede['medio'], self.velocidade['frear_pouco']),
            ctrl.Rule(self.curva['media_esq'] & self.distancia_parede['longe'], self.velocidade['manter']),

            ctrl.Rule(self.curva['media_dir'] & self.distancia_parede['perto'], self.velocidade['frear_medio']),
            ctrl.Rule(self.curva['media_dir'] & self.distancia_parede['medio'], self.velocidade['frear_pouco']),
            ctrl.Rule(self.curva['media_dir'] & self.distancia_parede['longe'], self.velocidade['manter']),

            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_parede['perto'], self.velocidade['frear_pouco']),
            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_parede['medio'], self.velocidade['acelerar']),
            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_parede['longe'], self.velocidade['acelerar']),

            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_parede['perto'], self.velocidade['frear_pouco']),
            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_parede['medio'], self.velocidade['acelerar']),
            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_parede['longe'], self.velocidade['acelerar']),
        ]

    def _create_control_system(self):
        """Cria os sistemas de controle fuzzy separados para virar e velocidade."""
        self.virar_ctrl = ctrl.ControlSystem(self.rules_virar)
        self.velocidade_ctrl = ctrl.ControlSystem(self.rules_velocidade)

        self.virar_sim = ctrl.ControlSystemSimulation(self.virar_ctrl)
        self.velocidade_sim = ctrl.ControlSystemSimulation(self.velocidade_ctrl)

    def compute(self, curva_input, distancia_parede_input, distancia_objetivo_input):
        """Calcula as saídas fuzzy com base nos valores de entrada."""
        # Processar a variável de saída "virar"
        self.virar_sim.input['curva'] = curva_input
        self.virar_sim.input['distancia_parede'] = distancia_parede_input
        self.virar_sim.compute()

        # Processar a variável de saída "velocidade"
        self.velocidade_sim.input['curva'] = curva_input
        self.velocidade_sim.input['distancia_parede'] = distancia_parede_input
        # self.velocidade_sim.input['distancia_objetivo'] = distancia_objetivo_input
        self.velocidade_sim.compute()

        return {
            'virar': round(self.virar_sim.output['virar']), 
            'velocidade': self.velocidade_sim.output['velocidade']
        } 

if __name__ == '__main__':
    fuzzy = FuzzyController()
    fuzzy.curva.view()
    fuzzy.distancia_parede.view()
    fuzzy.velocidade.view()
    fuzzy.virar.view()

    plt.show()
    resultado = fuzzy.compute(30, 70, 15)  # Entrada de exemplo: curva = 30, distancia_parede = 70
    print(f"Comando para virar: {resultado['virar']}")
    print(f"Delta de velocidade: {resultado['velocidade']:.2f}")

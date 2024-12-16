import os
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt

class FuzzyController:
    def __init__(self):
        self.curva = ctrl.Antecedent(np.arange(-180, 181, 1), 'curva')
        self.distancia_parede = ctrl.Antecedent(np.arange(0, 1920, 1), 'distancia_parede')

        self.virar = ctrl.Consequent(np.arange(-1, 1.1, 0.5), 'virar')
        self.velocidade = ctrl.Consequent(np.arange(-2.5, 0.3, 0.01), 'velocidade')

        self._define_membership_functions()
        self._definir_regras()
        self._criar_control_system()

    def _define_membership_functions(self):
        self.distancia_parede['perto'] = fuzz.trapmf(self.distancia_parede.universe, [0, 0, 75, 100])
        self.distancia_parede['medio'] = fuzz.trimf(self.distancia_parede.universe, [75, 100, 150])
        self.distancia_parede['longe'] = fuzz.trapmf(self.distancia_parede.universe, [100, 150, np.inf, np.inf])

        self.curva['fechada_esq'] = fuzz.trapmf(self.curva.universe, [-180, -180, -120, -45])
        self.curva['media_esq'] = fuzz.trimf(self.curva.universe, [-120, -45, -15])
        self.curva['aberta_esq'] = fuzz.trimf(self.curva.universe, [-45, -15, 0])
        self.curva['aberta_dir'] = fuzz.trimf(self.curva.universe, [0, 15, 45])
        self.curva['media_dir'] = fuzz.trimf(self.curva.universe, [15, 45, 120])
        self.curva['fechada_dir'] = fuzz.trapmf(self.curva.universe, [45, 120, 180, 180])

        self.velocidade['frear_muito'] = fuzz.trapmf(self.velocidade.universe, [-2.5, -2.5, -2, -1.5])
        self.velocidade['frear_medio'] = fuzz.trimf(self.velocidade.universe, [-2, -1, 0])
        self.velocidade['frear_pouco'] = fuzz.trimf(self.velocidade.universe, [-0.5, 0, 0.1])
        self.velocidade['manter'] = fuzz.trimf(self.velocidade.universe, [0, 0.1, 0.2])
        self.velocidade['acelerar'] = fuzz.trapmf(self.velocidade.universe, [0.1, 0.2, 0.3, 0.3])

        self.virar['esquerda'] = fuzz.trimf(self.virar.universe, [-1, -1, 0])
        self.virar['manter'] = fuzz.trimf(self.virar.universe, [-0.5, 0, 0.5])
        self.virar['direita'] = fuzz.trimf(self.virar.universe, [0, 1, 1])

    def _definir_regras(self):
        """Define as regras fuzzy para controlar a lógica."""
        self.rules_virar = [
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

        self.rules_velocidade = [
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

    def _criar_control_system(self):
        self.virar_ctrl = ctrl.ControlSystem(self.rules_virar)
        self.velocidade_ctrl = ctrl.ControlSystem(self.rules_velocidade)

        self.virar_sim = ctrl.ControlSystemSimulation(self.virar_ctrl)
        self.velocidade_sim = ctrl.ControlSystemSimulation(self.velocidade_ctrl)

    def computar(self, curva_input, distancia_parede_input, gerar_relatorio=False):        
        self.virar_sim.input['curva'] = curva_input
        self.virar_sim.input['distancia_parede'] = distancia_parede_input
        self.virar_sim.compute()
        virar_output = self.virar_sim.output['virar']
    
        self.velocidade_sim.input['curva'] = curva_input
        self.velocidade_sim.input['distancia_parede'] = distancia_parede_input
        self.velocidade_sim.compute()
        velocidade_output = self.velocidade_sim.output['velocidade']
    
        if gerar_relatorio:
            self._gerar_relatorio(
                curva_input=curva_input, 
                distancia_parede_input=distancia_parede_input, 
                virar_output=virar_output, 
                velocidade_output=velocidade_output
            )
    
        return {
            'virar': round(virar_output), 
            'velocidade': velocidade_output
        }
    
    def _gerar_relatorio(self, curva_input, distancia_parede_input, virar_output, velocidade_output):
        relatorio = f"""
        Relatório de Controle Fuzzy
        ===========================
        Entradas:
            Curva: {curva_input}
            Distância: {distancia_parede_input}
        
        Saídas:
            Virar: {virar_output} (Ação: {'Esquerda' if virar_output < 0 else 'Direita' if virar_output > 0 else 'Manter'})
            Velocidade: {velocidade_output:.2f}
        
        Pertinência:
            Curva:
                Fechada Esq: {fuzz.interp_membership(self.curva.universe, self.curva['fechada_esq'].mf, curva_input):.2f}
                Média Esq: {fuzz.interp_membership(self.curva.universe, self.curva['media_esq'].mf, curva_input):.2f}
                Aberta Esq: {fuzz.interp_membership(self.curva.universe, self.curva['aberta_esq'].mf, curva_input):.2f}
                Aberta Dir: {fuzz.interp_membership(self.curva.universe, self.curva['aberta_dir'].mf, curva_input):.2f}
                Média Dir: {fuzz.interp_membership(self.curva.universe, self.curva['media_dir'].mf, curva_input):.2f}
                Fechada Dir: {fuzz.interp_membership(self.curva.universe, self.curva['fechada_dir'].mf, curva_input):.2f}
    
            Distância da parede:
                Perto: {fuzz.interp_membership(self.distancia_parede.universe, self.distancia_parede['perto'].mf, distancia_parede_input):.2f}
                Médio: {fuzz.interp_membership(self.distancia_parede.universe, self.distancia_parede['medio'].mf, distancia_parede_input):.2f}
                Longe: {fuzz.interp_membership(self.distancia_parede.universe, self.distancia_parede['longe'].mf, distancia_parede_input):.2f}
    
        """
    
        os.makedirs('output', exist_ok=True)
        with open("output/relatorio_fuzzy.txt", "w") as file:
            file.write(relatorio)
    
        print("[INFO] Relatório gerado: relatorio_fuzzy.txt")
    
        self._gerar_graficos(curva_input, distancia_parede_input)
    
    def _gerar_graficos(self, curva_input, distancia_parede_input):
        self.curva.view(sim=self.virar_sim)
        plt.title(f'Curva = {curva_input}')
        plt.savefig('output/curva_fuzzy.png')
    
        self.distancia_parede.view(sim=self.velocidade_sim)
        plt.title(f'Distância da parede = {distancia_parede_input}')
        plt.xlim(0, 200)
        plt.savefig('output/distancia_parede_fuzzy.png')
    
        self.virar.view(sim=self.virar_sim)
        plt.title('Saída Fuzzy: Virar')
        plt.savefig('output/virar_fuzzy.png')
    
        self.velocidade.view(sim=self.velocidade_sim)
        plt.title('Saída Fuzzy: Velocidade')
        plt.savefig('output/velocidade_fuzzy.png')
    
        print("[INFO] Gráficos salvos: curva_fuzzy.png, distancia_fuzzy.png, virar_fuzzy.png, velocidade_fuzzy.png")

if __name__ == '__main__':
    fuzzy = FuzzyController()

    resultado = fuzzy.computar(30, 70, gerar_relatorio=True)

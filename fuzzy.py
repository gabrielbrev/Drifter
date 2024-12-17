import os
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt

class FuzzyController:
    def __init__(self):
        self.curva = ctrl.Antecedent(np.arange(-180, 181, 1), 'curva')
        self.distancia_borda = ctrl.Antecedent(np.arange(0, 1920, 1), 'distancia_borda')

        self.virar = ctrl.Consequent(np.arange(-1, 1.1, 0.5), 'virar')
        self.velocidade = ctrl.Consequent(np.arange(-2.5, 0.3, 0.01), 'velocidade')

        self._define_membership_functions()
        self._definir_regras()
        self._criar_control_system()

    def _define_membership_functions(self):
        self.distancia_borda['perto'] = fuzz.trapmf(self.distancia_borda.universe, [0, 0, 75, 100])
        self.distancia_borda['medio'] = fuzz.trimf(self.distancia_borda.universe, [75, 100, 150])
        self.distancia_borda['longe'] = fuzz.trapmf(self.distancia_borda.universe, [100, 150, np.inf, np.inf])

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
            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_borda['perto'], self.virar['esquerda']),
            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_borda['medio'], self.virar['esquerda']),
            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_borda['longe'], self.virar['esquerda']),

            ctrl.Rule(self.curva['media_esq'] & self.distancia_borda['perto'], self.virar['esquerda']),
            ctrl.Rule(self.curva['media_esq'] & self.distancia_borda['medio'], self.virar['esquerda']),
            ctrl.Rule(self.curva['media_esq'] & self.distancia_borda['longe'], self.virar['esquerda']),

            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_borda['perto'], self.virar['esquerda']),
            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_borda['medio'], self.virar['esquerda']),
            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_borda['longe'], self.virar['manter']),

            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_borda['perto'], self.virar['direita']),
            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_borda['medio'], self.virar['direita']),
            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_borda['longe'], self.virar['direita']),

            ctrl.Rule(self.curva['media_dir'] & self.distancia_borda['perto'], self.virar['direita']),
            ctrl.Rule(self.curva['media_dir'] & self.distancia_borda['medio'], self.virar['direita']),
            ctrl.Rule(self.curva['media_dir'] & self.distancia_borda['longe'], self.virar['direita']),

            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_borda['perto'], self.virar['direita']),
            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_borda['medio'], self.virar['direita']),
            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_borda['longe'], self.virar['manter']),
        ]

        self.rules_velocidade = [
            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_borda['perto'], self.velocidade['frear_muito']),
            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_borda['medio'], self.velocidade['frear_medio']),
            ctrl.Rule(self.curva['fechada_esq'] & self.distancia_borda['longe'], self.velocidade['frear_medio']),

            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_borda['perto'], self.velocidade['frear_muito']),
            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_borda['medio'], self.velocidade['frear_medio']),
            ctrl.Rule(self.curva['fechada_dir'] & self.distancia_borda['longe'], self.velocidade['frear_medio']),

            ctrl.Rule(self.curva['media_esq'] & self.distancia_borda['perto'], self.velocidade['frear_medio']),
            ctrl.Rule(self.curva['media_esq'] & self.distancia_borda['medio'], self.velocidade['frear_pouco']),
            ctrl.Rule(self.curva['media_esq'] & self.distancia_borda['longe'], self.velocidade['manter']),

            ctrl.Rule(self.curva['media_dir'] & self.distancia_borda['perto'], self.velocidade['frear_medio']),
            ctrl.Rule(self.curva['media_dir'] & self.distancia_borda['medio'], self.velocidade['frear_pouco']),
            ctrl.Rule(self.curva['media_dir'] & self.distancia_borda['longe'], self.velocidade['manter']),

            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_borda['perto'], self.velocidade['frear_pouco']),
            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_borda['medio'], self.velocidade['acelerar']),
            ctrl.Rule(self.curva['aberta_esq'] & self.distancia_borda['longe'], self.velocidade['acelerar']),

            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_borda['perto'], self.velocidade['frear_pouco']),
            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_borda['medio'], self.velocidade['acelerar']),
            ctrl.Rule(self.curva['aberta_dir'] & self.distancia_borda['longe'], self.velocidade['acelerar']),
        ]

    def _criar_control_system(self):
        self.virar_ctrl = ctrl.ControlSystem(self.rules_virar)
        self.velocidade_ctrl = ctrl.ControlSystem(self.rules_velocidade)

        self.virar_sim = ctrl.ControlSystemSimulation(self.virar_ctrl)
        self.velocidade_sim = ctrl.ControlSystemSimulation(self.velocidade_ctrl)

    def computar(self, curva_input, distancia_borda_input, gerar_relatorio=False):        
        self.virar_sim.input['curva'] = curva_input
        self.virar_sim.input['distancia_borda'] = distancia_borda_input
        self.virar_sim.compute()
        virar_output = self.virar_sim.output['virar']
    
        self.velocidade_sim.input['curva'] = curva_input
        self.velocidade_sim.input['distancia_borda'] = distancia_borda_input
        self.velocidade_sim.compute()
        velocidade_output = self.velocidade_sim.output['velocidade']
    
        if gerar_relatorio:
            self._gerar_relatorio(
                curva_input=curva_input, 
                distancia_borda_input=distancia_borda_input, 
                virar_output=virar_output, 
                velocidade_output=velocidade_output
            )
    
        return {
            'virar': round(virar_output), 
            'velocidade': velocidade_output
        }
    
    def _gerar_relatorio(self, curva_input, distancia_borda_input, virar_output, velocidade_output):
        relatorio = f"""
        Relatório de Controle Fuzzy
        ===========================
        Entradas:
            Curva: {curva_input:.0f}°
            Distância da borda: {distancia_borda_input:.0f}px
        
        Saídas:
            Virar: {virar_output:.2f} (Ação: {'Esquerda' if virar_output < 0 else 'Direita' if virar_output > 0 else 'Manter'})
            Velocidade: {velocidade_output:.2f}
        
        Pertinência:
            Curva:
                Fechada Esq: {fuzz.interp_membership(self.curva.universe, self.curva['fechada_esq'].mf, curva_input):.2f}
                Média Esq: {fuzz.interp_membership(self.curva.universe, self.curva['media_esq'].mf, curva_input):.2f}
                Aberta Esq: {fuzz.interp_membership(self.curva.universe, self.curva['aberta_esq'].mf, curva_input):.2f}
                Aberta Dir: {fuzz.interp_membership(self.curva.universe, self.curva['aberta_dir'].mf, curva_input):.2f}
                Média Dir: {fuzz.interp_membership(self.curva.universe, self.curva['media_dir'].mf, curva_input):.2f}
                Fechada Dir: {fuzz.interp_membership(self.curva.universe, self.curva['fechada_dir'].mf, curva_input):.2f}
    
            Distância da borda:
                Perto: {fuzz.interp_membership(self.distancia_borda.universe, self.distancia_borda['perto'].mf, distancia_borda_input):.2f}
                Médio: {fuzz.interp_membership(self.distancia_borda.universe, self.distancia_borda['medio'].mf, distancia_borda_input):.2f}
                Longe: {fuzz.interp_membership(self.distancia_borda.universe, self.distancia_borda['longe'].mf, distancia_borda_input):.2f}
    
        """
    
        os.makedirs('output/snapshot', exist_ok=True)
        with open("output/snapshot/relatorio_fuzzy.txt", "w") as file:
            file.write(relatorio)
    
        print("[INFO] Relatório gerado com sucesso.")
    
        self._gerar_graficos(curva_input, distancia_borda_input, virar_output, velocidade_output)
    
    def _gerar_graficos(self, curva_input, distancia_borda_input, virar_output, velocidade_output):
        self.curva.view(sim=self.virar_sim)
        plt.title(f'Curva = {curva_input:.0f}°')
        plt.savefig('output/snapshot/curva_fuzzy.png')
        plt.close()
    
        self.distancia_borda.view(sim=self.velocidade_sim)
        plt.title(f'Entrada: Distância da borda = {distancia_borda_input:.0f}px')
        if distancia_borda_input <= 200:
            plt.xlim(0, 200)
        else:
            plt.xlim(0, int(distancia_borda_input) + 100)
        plt.savefig('output/snapshot/distancia_borda_fuzzy.png')
        plt.close()
    
        self.virar.view(sim=self.virar_sim)
        plt.title(f'Saída: Virar = {virar_output:.2f}')
        plt.savefig('output/snapshot/virar_fuzzy.png')
        plt.close()
    
        self.velocidade.view(sim=self.velocidade_sim)
        plt.title(f'Saída: Velocidade = {velocidade_output:.2f}')
        plt.savefig('output/snapshot/velocidade_fuzzy.png')
        plt.close()
    
        print("[INFO] Gráficos gerados com sucesso.")

if __name__ == '__main__':
    fuzzy = FuzzyController()

    os.makedirs('output/demo', exist_ok=True)

    fuzzy.curva.view()
    plt.title('Função de pertinência para curva')
    plt.savefig('output/demo/curva.png')
    plt.close()

    fuzzy.distancia_borda.view()
    plt.title('Função de pertinência para distancia da borda')
    plt.xlim(0, 200)
    plt.savefig('output/demo/distancia_da_borda.png')
    plt.close()

    fuzzy.virar.view()
    plt.title('Função de pertinência para virar')
    plt.savefig('output/demo/virar.png')
    plt.close()

    fuzzy.velocidade.view()
    plt.title('Função de pertinência para velocidade')
    plt.savefig('output/demo/velocidade.png')
    plt.close()

    resultado = fuzzy.computar(30, 70, gerar_relatorio=True)

import json
import pandas as pd
from faker import Faker
import ollama

import random

from tqdm import tqdm

"""Prioridade,Natureza,TiposAgencia,Obs
Alerta Vermelho,Incêndio Em Edificação,GM;CdBM;PM
Alta,Incêndio Em Lixo,GM;CdBM
Alta,Subsidências e Colapsos,CdBM;DC
Alta,Incêndio Florestal,CdBM;DC
Média,Captura/resgate de Animal,GM;CdBM;PM
Média,Atendimento Ao Banhista,CdBM
Média,Perícia de Incêndio,CdBM
Média,Desinteligencia,GM;PM,Desinteligencia é
Baixa,Corte de Árvore,CdBM
Baixa,Risco de Desabamento,CdBM"""

agencias = {
    "Guarda Municipal": "GM",
    "Polícia Militar": "PM",
    "Corpo de Bombeiros Militar": "CdBM",
    "Agência Estadual de Trânsito": "AEdT",
    "Agência Municipal de Trânsito": "AMdT",
    "Polícia Rodoviária Federal": "PRF",
    "Polícia Civil": "PC",
    "Defesa Civil": "DC",
    "Perícia": "P",
    "Agência de Assistência Social e Cidadania": "AdASeC",
    "Força Nacional de Segurança Pública": "FNdSP",
    "Polícia Científica Federal": "PCF",
    "Polícia Federal": "PF",
    "Polícia Penal": "PP",
    "SAMU": "SAMU",
    "Outros": "Outros"
}

niveis_instrucao = [
    "Analfabetismo Completo",
    "Analfabestismo Funcional",
    "Ensino Fundamental",
    "Ensino Médio",
    "Ensino Técnico",
    "Graduação",
    "Mestrado",
    "Doutorado"
]

envolvimentos = [
    "Vitima", "Vizinho", "Pedestre Avisando"
]

agencias_inverso = {v: k for k, v in agencias.items()}

if __name__ == "__main__":
    naturezas_df = pd.read_csv("naturezas_exemplo.csv")
    n = 100

    naturezas_vec = naturezas_df['Natureza'].tolist()
    all_naturezas = [random.choice(naturezas_vec) for _ in range(n)]
    print(all_naturezas)
    idades = [random.randint(5, 95) for _ in range(n)]
    duracao_ligacao = [round(random.uniform(0.2, 6), 2) for _ in range(n)]
    hora = [random.randint(0, 23) for _ in range(n)]
    minutos = [random.randint(0, 59) for _ in range(n)]
    genero = ['H' if random.random() < 0.5 else 'M' for _ in range(n)]
    instrucao = [random.choice(niveis_instrucao) for _ in range(n)]
    envolvimento = [random.choice(envolvimentos) for _ in range(n)]
    desespero = [random.randint(0, 10) for _ in range(n)]

    chamadas = []

    fake = Faker('pt_BR')

    for i in range(n):
        nome = fake.name_male() if genero[i] == 'H' else fake.name_female()
        endereco = fake.address().split('\n')
        endereco[-1] = ''
        endereco = ', '.join(endereco) + '' + fake.city() + ' - ' + fake.state()
        numero = fake.cellphone_number()

        chamada_dict = {
            "Nome Solicitante": nome,
            "Endereco": endereco,
            "Numero": numero,
            "Natureza": all_naturezas[i],
            "Idade": idades[i],
            "Duração da Ligacao (Minutos)": duracao_ligacao[i],
            "Hora": str(hora[i]) + 'h' + str(minutos[i])+'min',
            "Genero": genero[i],
            "Instrucao": instrucao[i],
            "Envolvimento": envolvimento[i],
            "Desespero": desespero[i]
        }
        print(json.dumps(chamada_dict, indent=4, ensure_ascii=False))
        chamadas.append(chamada_dict)

    json.dump(chamadas, open('chamadas.json', 'w'), indent=4, ensure_ascii=False)
    
    for chamada in tqdm(chamadas):
        chamada_str = json.dumps(chamada, indent=4, ensure_ascii=False)
        prompt = (f"Eu preciso testar um sistema de chamadas de emergencia. Aqui está a descrição de uma chamada em json: {chamada_str}"
            + f"\nAgora, preciso que você gere a transcrição da conversa entre o solicitante e o operador. "
            +"Não quero nenhum tipo de elemento no texto que não seja a transcrição. Por favor, tente simular uma situação real."
            +"Obviamente, o solicitante não vai simplesmente listar os detalhes passados neste prompt perfeitamente. " 
            +"Dependendo do nível de desespero, informações podem faltar e ele pode ter muita dificuldade para explicar "
            +"detalhes que o operador quer. O operador tem o papel de realizar um atendimento humanizado e ajudar o solicitante "
            +"a dar todos os detalhes necessários. Pessoas de maior idade e menor nível de instrução poderão ter maior dificuldade "
            +"para explicar detalhes. Por outro lado, crianças podem ter dificuldades por não entender o que está acontecendo."
            +"O solicitante não saberá exatamente a natureza de ocorrencia, pois esse é um termo técnico. Dele vai descrever de forma leiga"
            +". O operador não tem interesse na idade, nivel de instrução, nivel de desespero, duração da ligação, hora do incidente e genero do solicitante. "
            +"Essas são apenas informações"
            +" descritivas para que você possa elaborar um roteiro mais realista."
            +"Nivel de instrução, duração da ligação e horarios não devem ser mencionados na chamada. O que importa é a emergencia.")
        result = ollama.generate(model='qwen3:4b', prompt=prompt)
        print(result['response'])
        chamada['roteiro'] = result['response']

        json.dump(chamadas, open('chamadas_roteirizadas.json', 'w'), indent=4, ensure_ascii=False)
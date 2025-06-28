import json
import sys
import pandas as pd
from faker import Faker
import ollama

import random
from os import mkdir
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

niveis_instrucao = {
    'Crianca': ["Analfabetismo Completo", "Analfabestismo Funcional"],
    'Adolescente': ["Analfabetismo Completo", "Analfabestismo Funcional", 
                    "Ensino Fundamental", "Ensino Médio"],
    'Adulto': ["Analfabetismo Completo", "Analfabestismo Funcional", 
               "Ensino Fundamental", "Ensino Médio",
               "Ensino Técnico", "Graduação", "Mestrado", "Doutorado"]
}

envolvimentos = [
    "Vitima", "Vizinho", "Pedestre Avisando"
]

agencias_inverso = {v: k for k, v in agencias.items()}

prompt1 = '''Eu preciso testar um sistema de chamadas de emergencia. 
    Aqui estão as informações chaves sobre a emergência e o solicitante: {info_dict}
    Agora, preciso que você gere a transcrição da conversa entre o solicitante e o operador. 
    Não quero nenhum tipo de elemento no texto que não seja a transcrição. Não incluir notas ao final.
    Não descrever elementos não falados, como o tom de voz. Quero apenas as palavras que serão ditas.
    Por favor, tente simular uma situação real.
    Operador:
    O operador não tem interesse na idade, nivel de instrução, nivel de desespero, duração da ligação, 
    hora do incidente e genero do solicitante. Essas são apenas informações descritivas para que você 
    possa elaborar um roteiro mais realista. Nivel de instrução, duração da ligação e horarios não devem 
    ser mencionados na chamada. O que importa é a emergencia. O operador tem o papel de realizar um 
    atendimento humanizado e ajudar o solicitante a dar todos os detalhes necessários.
    Solicitante (cidadão):
    Obviamente, o solicitante não vai simplesmente listar os detalhes passados neste prompt como uma máquina. 
    Dependendo do nível de desespero/estresse/medo, informações podem faltar e ele pode ter muita dificuldade para explicar 
    o que é a emergência.
    Pessoas de maior idade ou menor nível de instrução poderão ter maior dificuldade para explicar detalhes. 
    Por outro lado, crianças podem ter dificuldades por não entender o que está acontecendo.
    O solicitante não saberá exatamente a natureza de ocorrencia, pois esse é um termo técnico, ele vai descrever de forma leiga.'''

if __name__ == "__main__":
    naturezas_df = pd.read_csv("data/naturezas_exemplo.csv")
    #llm_name = 'qwen3:4b'
    llm_name = 'cnmoro/gemma3-gaia-ptbr-4b:q8_0'
    output_dir = 'generated/'+llm_name.replace(':', '_').replace('/', '-')+'/'
    addrs_json = 'generated/enderecos_brasil_final.json'
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    try:
        mkdir('generated')
    except Exception as err:
        pass
    try:
        mkdir(output_dir)
    except Exception as err:
        print(err)
    addrs_vec = json.load(open(addrs_json, 'r'))
    addrs = random.sample(addrs_vec, n)
    naturezas_vec = [{k: v for k, v in row.items()} for i, row in naturezas_df.iterrows()]
    n_naturezas = len(naturezas_vec)
    all_naturezas = [random.randint(0, n_naturezas - 1) for _ in range(n)]
    #print(all_naturezas)
    idades = [random.randint(5, 95) for _ in range(n)]
    duracao_ligacao = [round(random.uniform(0.2, 4), 2) for _ in range(n)]
    hora = [random.randint(0, 23) for _ in range(n)]
    minutos = [random.randint(0, 59) for _ in range(n)]
    genero = ['H' if random.random() < 0.5 else 'M' for _ in range(n)]
    instrucao = []
    for i in range(len(idades)):
        if idades[i] <= 14:
            instrucao.append(random.choice(niveis_instrucao['Crianca']))
        elif idades[i] <= 21:
            instrucao.append(random.choice(niveis_instrucao['Adolescente']))
        else:
            instrucao.append(random.choice(niveis_instrucao['Adulto']))
    envolvimento = [random.choice(envolvimentos) for _ in range(n)]
    desespero = []
    for i in range(len(all_naturezas)):
        nat_dict = naturezas_vec[all_naturezas[i]]
        prioridade = nat_dict['Prioridade']
        if prioridade == 'Baixa':
            desespero.append(random.randint(0, 2))
        elif prioridade == 'Média':
            desespero.append(random.randint(1, 3))
        else:
            desespero.append(random.randint(2, 10))

    chamadas = []

    fake = Faker('pt_BR')

    for i in range(n):
        nome = fake.name_male() if genero[i] == 'H' else fake.name_female()
        endereco = addrs[i]

        if endereco['numero'].count('-') == 1:
            num_parts = endereco['numero'].split('-')
            if len(num_parts) == 2:
                print('Street number range detected:', endereco)
                old_n = endereco['numero']
                endereco['numero'] = str(round(sum([int(x) for x in num_parts]) / 2))
                endereco['descricao'] = endereco['descricao'].replace(old_n, endereco['numero'])
                print('Updated', old_n, 'to', endereco['numero'])

        numero = fake.cellphone_number()
        numero = numero.split(' ')[-2] + ' ' + numero.split(' ')[-1]
        nat_dict = naturezas_vec[all_naturezas[i]]
        emergencia = {
            "Endereco": endereco,
            "Natureza": nat_dict,
            "Duração da Ligacao (Minutos)": duracao_ligacao[i],
            "Hora": str(hora[i]) + 'h' + str(minutos[i])+'min',
        }
        solicitante = {
            "Nome Solicitante": nome,
            "Idade": idades[i],
            "Genero": genero[i],
            "Numero": numero,
            "Instrucao": instrucao[i],
            "Envolvimento": envolvimento[i],
            "Nível de Desespero/Estresse/Medo (0 a 10)": desespero[i]
        }

        chamada_dict = {
            "Emergencia": emergencia,
            "Perfil do Solicitante": solicitante
        }

        #print(json.dumps(chamada_dict, indent=4, ensure_ascii=False))
        chamadas.append(chamada_dict)

    json.dump(chamadas, open(output_dir+'chamadas.json', 'w'), indent=4, ensure_ascii=False)
    
    for chamada in tqdm(chamadas):
        emergencia_minimal = {
            "Natureza": chamada["Emergencia"]["Natureza"],
            "Endereco": chamada["Emergencia"]["Endereco"]["descricao"],
            "Ponto_Referencia": chamada["Emergencia"]["Endereco"]["ref_name"],
            "Hora": chamada["Emergencia"]["Hora"],
            "Duração da Ligacao (Minutos)": chamada["Emergencia"]["Duração da Ligacao (Minutos)"]
        }

        chamaada_dict = {
            'Emergencia': emergencia_minimal,
            'Perfil do Solicitante': chamada['Perfil do Solicitante']
        }
        chamada_str = json.dumps(chamaada_dict, indent=4, ensure_ascii=False)
        prompt = prompt1.replace('{info_dict}', chamada_str)
        print(prompt)
        result = ollama.generate(model=llm_name, prompt=prompt)
        print(result['response'])
        chamada['roteiro'] = result['response']

        json.dump(chamadas, open(output_dir+'chamadas_roteirizadas.json', 'w'), indent=4, ensure_ascii=False)
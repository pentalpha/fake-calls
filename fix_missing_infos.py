from unidecode import unidecode
from tqdm import tqdm
import sys

def get_str_kmers(text: str, nmer: int):
    return set([text[i:i+nmer] for i in range(len(text)-nmer+1)])

def hard_norm_text_pt(text):
    text2 = unidecode(text.lower())
    for pont in ',.;:-?\t':
        text2 = text2.replace(pont, ' ')
    text2 = text2.replace('  ', ' ')
    text2 = text2.replace('  ', ' ')
    return text2

def find_infos_using_kmers(script: str, fields_to_find: dict, th = 0.5):
    script_norm = hard_norm_text_pt(script)
    kmer_lines = [get_str_kmers(script_line, 3)
        for script_line in script_norm.split('\n')
        if len(script_line) > 1]
    
    not_found = set()
    for field_name, field_content in fields_to_find.items():
        if field_content != "":
            content_norm = ' ' + hard_norm_text_pt(field_content) + ' '
            content_kmers = get_str_kmers(content_norm, 3)
            found = False
            for linemers in kmer_lines:
                n_found = len([mer for mer in content_kmers if mer in linemers])
                perc = n_found / len(content_kmers)
                if perc >= th:
                    found = True
                    break
            if not found:
                not_found.add(field_name)
    
    return not_found

infos_to_find_in_script = {
    'nome_solicitante': ['Perfil do Solicitante', 'Nome Solicitante'],
    'rua': ['Emergencia', 'Endereco', 'rua'],
    'numero': ['Emergencia', 'Endereco', 'numero'],
    'bairro': ['Emergencia', 'Endereco', 'bairro'],
    'cidade': ['Emergencia', 'Endereco', 'cidade'],
    'ref_name': ['Emergencia', 'Endereco', 'ref_name']
}

def fix_missing(roteirizado: dict):
    script = roteirizado['roteiro']

    infos_to_find = {}
    for info_name, keys_path in infos_to_find_in_script.items():
        if len(keys_path) == 2:
            infos_to_find[info_name] = roteirizado[keys_path[0]][keys_path[1]]
        elif len(keys_path) == 3:
            infos_to_find[info_name] = roteirizado[keys_path[0]][keys_path[1]][keys_path[2]]

    not_found = find_infos_using_kmers(script, infos_to_find)
    #if len(not_found) > 3:
    #    print(not_found)
    
    for not_f in not_found:
        keys_path = infos_to_find_in_script[not_f]
        if len(keys_path) == 2:
            roteirizado[keys_path[0]][keys_path[1]] = ""
        elif len(keys_path) == 3:
            roteirizado[keys_path[0]][keys_path[1]][keys_path[2]] = ""
    #if len(not_found) > 3:
    #    print(json.dumps(roteirizado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    '''
    a = "Operador: Bom diaááá, estou aqui para ajudar. O que está acontecendo?\n\nSolicitante: Aju"
    nmer = 3
    print(a)
    a_norm = hard_norm_text_pt(a)
    print(a_norm)
    kmers = get_str_kmers(a_norm, nmer)
    print(kmers)
    print([len(b) for b in kmers])'''

    import json
    from glob import glob
    inputs = glob('generated/*/chamadas_roteirizadas.json')
    for input_file in inputs:
        roteirizados = json.load(
            open(input_file, 'r'))
        roteirizados = [fix_missing(r) for r in tqdm(roteirizados)]
        output_file = input_file.replace('.json', '_final.json')
        json.dump(roteirizados, open(output_file, 'w'), indent=4, ensure_ascii=False)
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

def find_infos_using_kmers(script: str, fields_to_find: dict, th0 = 0.42, th1 = 0.5, th2 = 0.85):
    script_norm = hard_norm_text_pt(script)
    k_mer_len = 4
    kmer_lines = [get_str_kmers(script_line, k_mer_len)
        for script_line in script_norm.split('\n')
        if len(script_line) > 1]

    no_norm_kmer_lines = [get_str_kmers(script_line, k_mer_len)
        for script_line in script.split('\n')
        if len(script_line) > 1]
    
    not_found = set()
    for field_name, field_content in fields_to_find.items():
        is_small = len(field_content) <= 6
        th = th2 if is_small else th1
        if len(field_content) > 23:
            th = th0
        text_kmers = no_norm_kmer_lines if is_small else kmer_lines

        if field_content != "":
            if is_small:
                content_norm = field_content
            else:
                content_norm = ' ' + hard_norm_text_pt(field_content) + ' '
            found = False
            if len(content_norm) < k_mer_len:
                found = field_content in script
            else:
                content_kmers = get_str_kmers(content_norm, k_mer_len)
                for linemers in text_kmers:
                    n_found = len([mer for mer in content_kmers if mer in linemers])
                    try:
                        perc = n_found / len(content_kmers)
                        if perc >= th:
                            found = True
                            break
                    except ZeroDivisionError:
                        print(field_content, content_norm, content_kmers)
                        print(linemers)
                        quit(1)
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

    return roteirizado

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
        for i, r in enumerate(roteirizados):
            r['index'] = i
        output_file = input_file.replace('.json', '_final.json')
        json.dump(roteirizados, open(output_file, 'w'), indent=4, ensure_ascii=False)
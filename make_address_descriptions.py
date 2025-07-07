import sys
import json
import os
from tqdm import tqdm

def try_to_add_neighborhood(endereco: dict):
    bairro = None
    if 'ref_points' in endereco and len(endereco['ref_points']) > 0:
        ref_points = endereco['ref_points']
        for ref_point in ref_points:
            addr_str = ref_point['address']
            if ' - ' in addr_str:
                parts1 = addr_str.split(' - ')
                parts1_last = parts1[-1]
                if parts1_last.count(',') == 1:
                    parts2 = parts1_last.split(',')
                    if len(parts2) == 2:
                        bairro = parts2[0].strip()
                        break
    if bairro != None:
        endereco['Neighborhood'] = bairro

address_description_types = {
    "rua_numero",
    "rua_numero_cidade",
    "rua_cidade",
    "rua",
    "rua_numero_bairro",
    "rua_bairro",
    "rua_numero_bairro_cidade",
    "rua_bairro_cidade",
}

def make_address_description(endereco: dict, addr_desc_type: str) -> str:
    parts = addr_desc_type.split('_')
    descriptions_final = []
    for is_explicit_type in [True, False]:
        description_parts = []
        for part in parts:
            if part == "rua":
                description_parts.append(endereco["Street"])
            elif part == "numero":
                if is_explicit_type:
                    description_parts.append("Número " + endereco["HouseNumber"])
                else:
                    description_parts.append(endereco["HouseNumber"])
            elif part == "bairro":
                if is_explicit_type:
                    description_parts.append("Bairro " + endereco["Neighborhood"])
                else:
                    description_parts.append(endereco["Neighborhood"])
            elif part == "cidade":
                description_parts.append(endereco["Locality"])

        new_desc = ", ".join(description_parts)
        descriptions_final.append(new_desc)
    return descriptions_final

def alternate_descriptions(endereco: dict) -> list:
    descriptions = []
    for addr_desc_type in address_description_types:
        if not ('bairro' in addr_desc_type and not 'Neighborhood' in endereco):
            for desc in make_address_description(endereco, addr_desc_type):
                descriptions.append((desc, addr_desc_type))
    return descriptions

if __name__ == "__main__":
    enderecos_brasil_with_ref_points_path = "generated/enderecos_brasil_with_ref_points.json"
    enderecos_brasil_with_ref_points = json.load(open(enderecos_brasil_with_ref_points_path, 'r'))
    enderecos_brasil_final_path = "generated/enderecos_brasil_final.json"
    enderecos_brasil_final = []

    print('Defining neighborhoods...')
    for endereco in tqdm(enderecos_brasil_with_ref_points):
        try_to_add_neighborhood(endereco)
        if 'Neighborhood' not in endereco:
            print(f"Warning: Neighborhood not found for {endereco['Street']}, {endereco['HouseNumber']}, {endereco['Locality']}")
        else:
            print('Neighborhood found:', make_address_description(endereco, 'rua_numero_bairro_cidade')[0])
    
    print('Generating address descriptions...')
    for endereco in tqdm(enderecos_brasil_with_ref_points):
        for ref_point in endereco['ref_points']:
            if ref_point['distance'] >= 1 and 'political' not in ref_point['types']:
                for desc,desc_type in alternate_descriptions(endereco):
                    new_desc = {
                        "descricao": desc,
                        "desc_tipo": desc_type,
                        "rua": endereco['Street'],
                        "numero": endereco['HouseNumber'],
                        "bairro": endereco.get('Neighborhood', ''),
                        "cidade": endereco['Locality'],
                        "estado": endereco['Province'],
                        "CEP": endereco['PostalCode'],
                        "coords": [endereco['Latitude'], endereco['Longitude']],
                        "ref_name": ref_point['name'],
                        "ref_endereco_completo": ref_point['address'],
                        "ref_tipos": ref_point['types'],
                        "ref_distancia": ref_point['distance'],
                    }
                    same_as_last = False
                    if len(enderecos_brasil_final) > 0:
                        last_desc = enderecos_brasil_final[-1]
                        if (last_desc['descricao'] == new_desc['descricao'] and
                            last_desc['ref_name'] == new_desc['ref_name']):
                            same_as_last = True
                    if not same_as_last:
                        enderecos_brasil_final.append(new_desc)
    
    print(f"Total address descriptions generated: {len(enderecos_brasil_final)}")
    json.dump(enderecos_brasil_final, open(enderecos_brasil_final_path, 'w'), 
              indent=4, ensure_ascii=False)
    print(f"Address descriptions saved to {enderecos_brasil_final_path}")
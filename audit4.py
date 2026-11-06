import json
with open('AQI_non_linear.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

with open('nb_out.txt', 'w', encoding='utf-8') as f_out:
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            if 'outputs' in cell:
                for out in cell['outputs']:
                    if 'text' in out:
                        f_out.write("".join(out['text']))

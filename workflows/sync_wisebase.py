import os
import requests
import glob
from datetime import datetime

API_URL = os.environ.get('WISEBASE_API_URL', '')
API_KEY = os.environ.get('WISEBASE_API_KEY', '')

if not API_URL:
    print('AVISO: WISEBASE_API_URL nao configurada.')
    print('Cards disponiveis para sync futura:')
    for f in glob.glob('knowledge-base/**/*.md', recursive=True):
        print(f'  - {f}')
    exit(0)

md_files = glob.glob('knowledge-base/**/*.md', recursive=True)
print(f'Sincronizando {len(md_files)} cards...')
results = {'synced': 0, 'errors': 0}

for filepath in md_files:
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    card_id = os.path.splitext(os.path.basename(filepath))[0]
    payload = {'id': card_id, 'content': content, 'source': 'github-segundo-cerebro', 'updated_at': datetime.now().isoformat()}
    try:
        r = requests.post(API_URL, json=payload, headers={'Authorization': f'Bearer {API_KEY}'}, timeout=15)
        if r.status_code in (200, 201):
            print(f'OK {card_id}: {r.status_code}')
            results['synced'] += 1
        else:
            print(f'ERRO {card_id}: {r.status_code}')
            results['errors'] += 1
    except Exception as e:
        print(f'ERRO {card_id}: {e}')
        results['errors'] += 1

print(f"Sync concluida: {results['synced']} ok, {results['errors']} erros")

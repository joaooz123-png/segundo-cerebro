import feedparser
import os
from datetime import datetime

FEEDS = {
    'hackernews': 'https://hnrss.org/frontpage',
    'arxiv_ai': 'https://rss.arxiv.org/rss/cs.AI',
    'pubmed_reuma': 'https://pubmed.ncbi.nlm.nih.gov/rss/search/1hCJetkL7mVm4IhaqMjGH6yN_qK8e3OgZHpn3x5j0J6yJSxFMN/?limit=10&format=rss',
    'infomoney': 'https://www.infomoney.com.br/feed/'
}

date_str = datetime.now().strftime('%Y-%m-%d')
out_dir = f'data-feeds/{date_str}'
os.makedirs(out_dir, exist_ok=True)

for source, url in FEEDS.items():
    try:
        feed = feedparser.parse(url)
        entries = feed.entries[:5]
        md = f'# {source} - {date_str}\n\n'
        for e in entries:
            title = getattr(e, 'title', 'Sem titulo')
            link = getattr(e, 'link', '')
            summary = getattr(e, 'summary', '')[:400]
            md += f'## {title}\n**Link:** {link}\n**Resumo:** {summary}\n\n---\n\n'
        with open(f'{out_dir}/{source}.md', 'w', encoding='utf-8') as f:
            f.write(md)
        print(f'OK: {source} - {len(entries)} itens')
    except Exception as ex:
        print(f'ERRO {source}: {ex}')

print('Knowledge fetch concluido.')

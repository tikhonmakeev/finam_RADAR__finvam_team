"""
MOEX sector indices tickers for tracking market impact
"""
MOEX_INDEX_TICKERS = {
    'Информационные технологии': 'MOEXIT',
    'Металлы и добыча': 'MOEXMM', 
    'Нефть и газ': 'MOEXOG',
    'Потребительский сектор': 'MOEXCN',
    'Строительные компании': 'MOEXRE',
    'Телекоммуникации': 'MOEXTL',
    'Транспорт': 'MOEXTN',
    'Финансы': 'MOEXFN',
    'Электроэнергетика': 'MOEXEU',
    'Химия и нефтехимия': 'MOEXCH'
}

# Reverse mapping for quick lookup
TICKER_TO_SECTOR = {v: k for k, v in MOEX_INDEX_TICKERS.items()}

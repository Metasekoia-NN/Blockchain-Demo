import json

network = [
    {
        'host': '172.28.0.2',
        'port': 8080
    },
    {
        'host': '172.28.0.3',
        'port': 8080
    },
    {
        'host': '172.28.0.4',
        'port': 8080
    },
    {
        'host': '172.28.0.5',
        'port': 8080
    },
    {
        'host': '172.28.0.6',
        'port': 8080
    }
]

with open('conf/network_config.json', 'w') as f:
    json.dump(network, f, indent=4)

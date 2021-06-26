{
    'networks': [
        '10.0.0.0/24',
        '10.0.2.0/24',
        '10.0.9.0/24',
        '10.0.10.0/24',
    ],
    'routers': {
        '10.0.0.1': {
            '10.0.0.0/24': None,
            '10.0.0.2/24': None,
            '10.0.0.9/24': None,
        },
        '10.0.0.2': {
            '10.0.0.0/24': 'internal',
            '10.0.10.0/24': 'wg0',
        },
    },
}

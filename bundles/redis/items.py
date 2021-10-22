directories = {
    '/etc/redis': {
        'purge': True,
        'needs': [
            'pkg_apt:redis-server',
        ],
    },
    '/var/lib/redis': {
        'owner': 'redis',
        'needs': [
            'pkg_apt:redis-server',
        ],
    },
}

files = {
    '/etc/systemd/system/redis.service': {
        'delete': True,
        'needs': [
            'pkg_apt:redis-server',
        ],
    },
}

svc_systemd = {
    'redis': {
        'running': False,
        'enabled': False,
        'needs': [
            'pkg_apt:redis-server',
        ],
    },
}

for name, conf in node.metadata.get('redis').items():
    files[f'/etc/redis/{name}.conf'] = {
        'content': '\n'.join(
            f'{key} {value}'
                for key, value in sorted(conf.items())
                if value is not False
        ),
        'owner': 'redis',
        'triggers': [
            f'svc_systemd:redis-{name}:restart'
        ],
    }
    
    svc_systemd[f'redis-{name}'] = {
        'needs': [
            'svc_systemd:redis',
            f'file:/etc/redis/{name}.conf',
        ],
    }

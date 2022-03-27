from hashlib import sha3_256

defaults = {
    'apt': {
        'packages': {
            'icinga2': {},
            'icinga2-ido-pgsql': {},
            'icingacli': {},
        },
        'sources': {
            'deb https://packages.icinga.com/debian icinga-{release} main',
        },
    },
    'postgresql': {
        'databases': {
            'icinga2': {
                'owner': 'icinga2',
            },
        },
        'roles': {
            'icinga2': {
                'password': repo.vault.password_for(f'psql icinga2 on {node.name}'),
            },
        },
    },
    'zfs': {
        'datasets': {
            'tank/icinga2': {
                'mountpoint': '/var/lib/icinga2',
                'needed_by': {
                    'pkg_apt:icinga2',
                    'pkg_apt:icingaweb2',
                    'pkg_apt:icinga2-ido-pgsql',
                },
            },
        },
    },
}

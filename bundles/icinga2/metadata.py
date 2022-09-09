from hashlib import sha3_256

defaults = {
    'apt': {
        'packages': {
            'icinga2': {},
            'icinga2-ido-pgsql': {},
            'icingacli': {},
            'monitoring-plugins': {},
        },
        'sources': {
            'deb https://packages.icinga.com/debian icinga-{release} main',
        },
    },
    'icinga2': {
        'api_users': {
            'root': {
                'password': repo.vault.password_for(f'icinga2 api user root on {node.name}'),
                'permissions': {'*'},
            }
        },
    },
    'nftables': {
        'input': {
            'tcp dport 5665 accept',
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
    'users': {
        'nagios': {
            'home': '/var/lib/nagios',
            'shell': '/usr/sbin/nologin',
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


@metadata_reactor.provides(
    'nginx/vhosts',
)
def letsencrypt(metadata):
    return {
        'letsencrypt': {
            'domains': {
                metadata.get('icingaweb2/hostname'): {
                    'reload': {'icinga2'},
                    'owner': 'nagios',
                    'group': 'nagios',
                    'location': '/var/lib/icinga2/certs',
                    'privkey_name': metadata.get('hostname') + '.key',
                    'cert_name': metadata.get('hostname') + '.crt',
                },
            },
        },
    }

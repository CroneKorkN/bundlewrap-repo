from ipaddress import ip_interface

defaults = {
    'apt': {
        'packages': {
            'influxdb2': {},
        },
        'sources': [
            'deb https://repos.influxdata.com/debian {release} stable',
        ],
    },
    'influxdb': {
        'port': '8200',
        'username': 'admin',
        'org': 'default',
        'bucket': 'default',
        'config': {
            'bolt-path': '/var/lib/influxdb/influxd.bolt',
            'engine-path': '/var/lib/influxdb/engine',
            'reporting-disabled': True,
            'http-bind-address': ':8200',
        },
    },
    'zfs': {
        'datasets': {
            'tank/influxdb': {
                'mountpoint': '/var/lib/influxdb'
            },
        },
    },
}

@metadata_reactor.provides(
    'influxdb/password',
)
def admin_password(metadata):
    return {
        'influxdb': {
            'password': repo.vault.password_for(f"{metadata.get('id')} influxdb admin"),
            'admin_token': repo.vault.random_bytes_as_base64_for(f"{metadata.get('id')} influxdb default token", length=64),
        },
    }


@metadata_reactor.provides(
    'dns',
)
def dns(metadata):
    return {
        'dns': {
            metadata.get('influxdb/hostname'): repo.libs.dns.get_a_records(metadata),
        }
    }
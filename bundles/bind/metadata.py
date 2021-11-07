from ipaddress import ip_interface
from json import dumps
h = repo.libs.hashable.hashable
repo.libs.bind.repo = repo

defaults = {
    'apt': {
        'packages': {
            'bind9': {},
        },
    },
    'bind': {
        'slaves': {},
        'views': {
            'internal': {
                'is_internal': True,
                'acl': {
                    '127.0.0.1',
                    '10.0.0.0/8',
                    '169.254.0.0/16',
                    '172.16.0.0/12',
                    '192.168.0.0/16',
                },
                'keys': {},
                'zones': {},
            },
            'external': {
                'default': True,
                'name': 'external', 
                'is_internal': False,
                'acl': {
                    'any',
                },
                'keys': {},
                'zones': {},
            },
        },
        'keys': {
            'internal': {},
            'external': {},
        },
    },
    'telegraf': {
        'config': {
            'inputs': {
                'bind': [{
                    'urls': ['http://localhost:8053/xml/v3'],
                    'gather_memory_contexts': False,
                    'gather_views': True,
                }],
            },
        },
    },
}


@metadata_reactor.provides(
    'bind/type',
)
def type(metadata):
    return {
        'bind': {
            'type': 'slave' if metadata.get('bind/master_node', None) else 'master',
        }
    }


@metadata_reactor.provides(
    'dns',
)
def dns(metadata):
    return {
        'dns': {
            metadata.get('bind/hostname'): repo.libs.dns.get_a_records(metadata),
        }
    }


@metadata_reactor.provides(
    'bind/zones',
)
def collect_records(metadata):
    if metadata.get('bind/type') == 'slave':
        return {}
    
    views = {}

    for view_name, view_conf in metadata.get('bind/views').items():
        for other_node in repo.nodes:
            for fqdn, records in other_node.metadata.get('dns', {}).items():
                matching_zones = sorted(
                    filter(
                        lambda potential_zone: fqdn.endswith(potential_zone),
                        metadata.get('bind/zones').keys()
                    ),
                    key=len,
                )
                if matching_zones:
                    zone = matching_zones[-1]
                else:
                    continue

                name = fqdn[0:-len(zone) - 1]

                for type, values in records.items():                    
                    for value in values:
                        if repo.libs.bind.record_matches_view(value, type, name, zone, view_name, metadata):
                            views\
                                .setdefault(view_name, {})\
                                .setdefault('zones', {})\
                                .setdefault(zone, {})\
                                .setdefault('records', set())\
                                .add(
                                    h({'name': name, 'type': type, 'value': value})
                                )
    
    return {
        'bind': {
            'views': views,
        },
    }


@metadata_reactor.provides(
    'bind/zones',
)
def ns_records(metadata):
    if metadata.get('bind/type') == 'slave':
        return {}

    nameservers = [
        node.metadata.get('bind/hostname'),
        *[
            repo.get_node(slave).metadata.get('bind/hostname')
                for slave in node.metadata.get('bind/slaves')
        ]
    ]
    return {
        'bind': {
            'zones': {
                zone: {
                    'records': {
                        # FIXME: bw currently cant handle lists of dicts :(
                        h({'name': '@', 'type': 'NS', 'value': f"{nameserver}."})
                            for nameserver in nameservers
                    } 
                }
                    for zone in metadata.get('bind/zones').keys()
            },
        },
    }


@metadata_reactor.provides(
    'bind/slaves',
)
def slaves(metadata):
    if metadata.get('bind/type') == 'slave':
        return {}
    
    return {
        'bind': {
            'slaves': [
                other_node.name
                    for other_node in repo.nodes
                    if other_node.has_bundle('bind') and other_node.metadata.get('bind/master_node', None) == node.name
            ],
        },
    }


@metadata_reactor.provides(
    'bind/views',
)
def generate_keys(metadata):
    return {
        'bind': {
            'views': {
                view: {
                    'keys': {
                        f'{view}.{zone}': repo.libs.hmac.hmac_sha512(
                            zone,
                            str(repo.vault.random_bytes_as_base64_for(
                                f"{metadata.get('id')} bind {view} key {zone}",
                                length=32,
                            )),
                        )
                            for zone, conf in metadata.get('bind/zones').items()
                            if conf.get('dynamic', False)
                            and view in conf.get('views', metadata.get('bind/views').keys())
                    }
                }
                    for view in metadata.get('bind/views')
            }
        },
    }


@metadata_reactor.provides(
    'bind/views',
)
def allow_keys_in_acl(metadata):
    return {
        'bind': {
            'views': {
                view: {
                    'acl': {
                        f'key {key}'
                            for key in conf['keys']
                    }
                }
                    for view, conf in metadata.get('bind/views').items()
            }
        },
    }


@metadata_reactor.provides(
    'bind/views',
)
def reject_keys_from_other_views(metadata):
    return {
        'bind': {
            'views': {
                view: {
                    'acl': {
                        f'! key {key}'
                            for other_view, other_conf in metadata.get('bind/views').items()
                            if other_view != view
                            for key in other_conf['keys']
                    }
                }
                    for view, conf in metadata.get('bind/views').items()
                    if not conf.get('default')
            }
        },
    }

from ipaddress import ip_network, ip_interface

from bundlewrap.exceptions import NoSuchNode
from bundlewrap.metadata import atomic

repo.libs.wireguard.repo = repo


defaults = {
    'apt': {
        'packages': {
            'wireguard': {
                'backports': node.os_version < (11,),
                'triggers': [
                    'svc_systemd:systemd-networkd:restart',
                ],
            },
        },
    },
    'wireguard': {
        's2s': {},
        'clients': {},
    },
}


@metadata_reactor.provides(
    'wireguard/s2s',
)
def s2s_peer_specific(metadata):
    return {
        'wireguard': {
            's2s': {
                s2s: {
                    'id': repo.get_node(s2s).metadata.get(f'id'),
                    'ip': repo.get_node(s2s).metadata.get(f'wireguard/my_ip'),
                    'endpoint': f'{repo.get_node(s2s).hostname}:51820',
                    'route': [
                        str(ip_interface(repo.get_node(s2s).metadata.get(f'wireguard/my_ip')).network),
                    ],
                }
                    for s2s in metadata.get('wireguard/s2s')
            },
        },
    }


@metadata_reactor.provides(
    'wireguard/clients',
)
def client_peer_specific(metadata):
    return {
        'wireguard': {
            'clients': {
                client: {
                    'id': client,
                    'route': [
                        str(ip_interface(conf['ip']).network),
                    ]
                }
                    for client, conf in metadata.get('wireguard/clients').items()
            },
        },
    }


@metadata_reactor.provides(
    'systemd/units',
)
def systemd_networkd_networks(metadata):
    network = {
        'Match': {
            'Name': 'wg0',
        },
        'Address': {
            'Address': metadata.get('wireguard/my_ip'),
        },
        'Network': {
            'DHCP': 'no',
            'IPForward': 'yes',
            'IPv6AcceptRA': 'no',
        },
    }

    for peer, config in metadata.get('wireguard/s2s').items():
        for route in config.get('route', []):
            network.update({
                f'Route#{peer}_{route}': {
                    'Destination': route,
                    'Gateway': str(ip_interface(metadata.get('wireguard/my_ip')).ip),
                }
            })

    return {
        'systemd': {
            'units': {
                'wireguard.network':  network,
            },
        },
    }


@metadata_reactor.provides(
    'systemd/units',
)
def systemd_networkd_netdevs(metadata):
    netdev = {
        'NetDev': {
            'Name': 'wg0',
            'Kind': 'wireguard',
            'Description': 'WireGuard server',
        },
        'WireGuard': {
            'PrivateKey': repo.libs.wireguard.privkey(metadata.get('id')),
            'ListenPort': 51820,
        },
    }
    
    for peer, config in {
        **metadata.get('wireguard/s2s'),
        **metadata.get('wireguard/clients'),
    }.items():
        netdev.update({
            f'WireGuardPeer#{peer}': {
                'PublicKey': repo.libs.wireguard.pubkey(config['id']),
                'PresharedKey': repo.libs.wireguard.psk(config['id'], metadata.get('id')),
                'AllowedIPs': ', '.join([
                    # '172.30.0.0/24', # FIXME
                    *config.get('route', []),
                ]), # FIXME
                'PersistentKeepalive': 30,
            }
        })
        if config.get('endpoint'):
            netdev[f'WireGuardPeer#{peer}']['Endpoint'] = config['endpoint']
    
    return {
        'systemd': {
            'units': {
                'wireguard.netdev':  netdev,
            },
        },
    }

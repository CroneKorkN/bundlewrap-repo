from base64 import b64decode


defaults = {
    'users': {
        'root': {
            'home': '/root',
        },
    },
}


@metadata_reactor.provides(
    'users',
)
def user(metadata):
    users = {}

    for name, config in metadata.get('users').items():
        users[name] = {
            'authorized_keys': []
        }

        if not 'home' in config:
            users[name]['home'] = f'/home/{name}'

        if not 'shell' in config:
            users[name]['shell'] = '/bin/bash'
            
        if not 'password_hash' in config:
            users[name]['password_hash'] = 'x' if node.use_shadow_passwords else '*'

        if not 'privkey' in users[name]:
            privkey, pubkey = repo.libs.ssh.generate_ad25519_key_pair(
                b64decode(str(repo.vault.random_bytes_as_base64_for(metadata.get('id'), length=32)))
            )
            users[name]['keytype'] = 'ed25519'
            users[name]['privkey'] = privkey
            users[name]['pubkey'] = pubkey + f' {name}@{node.name}'
    
    return {
        'users': users,
    }

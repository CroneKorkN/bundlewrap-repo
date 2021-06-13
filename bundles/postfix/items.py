assert node.has_bundle('postgresql')
assert node.has_bundle('dovecot')
assert node.has_bundle('letsencrypt')

file_options = {
    'triggers': [
        'svc_systemd:postfix:restart',
    ],
    'needed_by': [
        'svc_systemd:postfix',
    ],
}

files = {
    '/etc/postfix/main.cf': {
        'content_type': 'mako',
        **file_options,
    },
    '/etc/postfix/master.cf': {
        **file_options,
    },
    '/etc/postfix/virtual_alias_maps.cf': {
        'content_type': 'mako',
        'context': node.metadata.get('mailserver/database'),
        **file_options,
    },
    '/etc/postfix/virtual_mailbox_domains.cf': {
        'content_type': 'mako',
        'context': node.metadata.get('mailserver/database'),
        **file_options,
    },
    '/etc/postfix/virtual_mailbox_maps.cf': {
        'content_type': 'mako',
        'context': node.metadata.get('mailserver/database'),
        **file_options,
    },
    '/etc/postfix/virtual_redirects.cf': {
        'content_type': 'mako',
        'context': node.metadata.get('mailserver/database'),
        **file_options,
    },
}

svc_systemd['postfix'] = {
    'needs': [
        'postgres_db:mailserver',
    ],
}

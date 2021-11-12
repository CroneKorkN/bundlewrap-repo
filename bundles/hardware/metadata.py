defaults = {
    'grafana_rows': {
        'health',
    },
    'sudoers': {
        'telegraf': {
            '/usr/local/share/icinga/plugins/cpu_frequency',
        },
    },
    'telegraf': {
        'config': {
            'inputs': {
                'exec': {
                    repo.libs.hashable.hashable({
                        'commands': ["sudo /usr/local/share/icinga/plugins/cpu_frequency"],
                        'name_override': "cpu_frequency",
                        'data_format': "influx",
                    }),
                    repo.libs.hashable.hashable({
                        'commands': ["/bin/bash -c 'expr $(cat /sys/class/thermal/thermal_zone0/temp) / 1000'"],
                        'name_override': "cpu_temperature",
                        'data_format': "value",
                        'data_type': "integer",
                    }),
                },
            },
        },
    },
}
from PyInquirer import prompt


def get_parameters():
    questions = [
        {
            'type':  'list',
            'name': 'service',
            'message': 'Which bot ?',
            'choices': [
                {
                    'name': 'Wattpad',
                    'value': 'wattpad'
                },
                {
                    'name': 'Webnovel',
                    'value': 'webnovel'
                },
                {
                    'name': 'More coming soon.',
                    'disabled': 'Under develepment.'
                },
            ]
        },
        {
            'type': 'checkbox',
            'name': 'actions',
            'message': 'What action(s) to do ?',
            'choices': [
                {
                    'name': 'Read',
                    'checked': True,
                },
                {
                    'name': 'Vote',
                    'disable': lambda answers: True if answers['service'] != 'wattpad' else False,
                },
            ],
            'when': lambda answers: answers['service'] == 'wattpad',
            'validate': lambda answer: 'You must choose at least one action.' if len(answer) == 0 else True
        },
        {
            'type': 'confirm',
            'message': 'Use user accounts ?',
            'name': 'use_user_accounts',
            'default': True,
            'when': lambda answers: True if answers['service'] == 'wattpad' else False,
        },
        {
            'type': 'input',
            'name': 'user_combos_file_path',
            'message': "Path of users combos file (TXT): ",
            'when': lambda answers:  answers.get('use_user_accounts', False),
            'default': lambda answers: f'{answers["service"]}.txt',
        },
        {
            'type': 'confirm',
            'message': 'Use Proxies ?',
            'name': 'use_proxies',
            'default': True,
        },
        {
            'type': 'confirm',
            'message': 'Use Local Proxies only ? (proxies.txt)',
            'name': 'use_local_proxies_only',
            'default': True,
        },
        {
            'type': 'confirm',
            'message': 'Filter bad proxies (Slow) ?',
            'name': 'filter_bad_proxies',
            'when': lambda answers:  answers.get('use_proxies', False),
            'default': False,
        },
        {
            'type': 'input',
            'name': 'novel_id',
            'message': "Id of novel: ",
            'default': lambda answers: '214056067' if answers['service'] == 'wattpad' else '12490080005604205',
        },
        {
            'type': 'input',
            'name': 'chapters_file_path',
            'message': "Path of chapters file (JSON): ",
            'default': lambda answers: f'{answers["novel_id"]}.json',
        },
        {
            'type': 'confirm',
            'message': 'Boost first chapter only ?',
            'name': 'boost_first_chapter_only',
            'default': False,
        },
    ]
    return prompt(questions)

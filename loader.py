from PyInquirer import prompt


def get_parameters():
    questions = [
        {
            'type': 'confirm',
            'message': 'Use Proxies ?',
            'name': 'use_proxies',
            'default': True,
        },
        {
            'type': 'confirm',
            'message': 'Filter bad proxies (Slow) ?',
            'name': 'filter_bad_proxies',
            'default': False,
        },
        {
            'type': 'input',
            'name': 'novel_id',
            'message': "Id of novel: ",
            'default': '12490080005604205',
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

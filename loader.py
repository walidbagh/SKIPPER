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
  ]
  return prompt(questions)

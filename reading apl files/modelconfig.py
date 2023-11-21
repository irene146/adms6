class ModelConfig:
    def __init__(self):
        self._config = {}

    def read(self, filename):
        self._config = {}
        with open(filename, 'r') as f:
            current_name = None
            current_key = None

            for line in f:
                if not line.strip():
                    continue
                if line.strip().startswith('&'):
                    current_name = line.strip()[1:]
                    self._config[current_name] = {}
                elif line.strip() == '/':
                    current_name = None
                else:
                    if current_name is None:
                        raise ValueError('Oh no!')
                    
                    if '=' in line:
                        current_key, value = line.split('=')
                        self._config[current_name][current_key.strip()] = value
                    else:
                        self._config[current_name][current_key.strip()] += line


    def __getitem__(self, key):
        return self._config[key]
    
    def __setitem__(self, group, key, value):
        self._config[group][key] = value

    def write(self, filename):
        with open(filename, 'w') as f:

            for group in self._config:
                f.write(f'&{group}\n')
                for key, value in self._config[group].items():
                    value = str(value)
                    if not '\n' in value:
                        value += '\n'
                    f.write(f'{key} = {value}')
                f.write('/\n\n')

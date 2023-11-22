######Irene trying to make sense of this######
##############################################


class ModelConfig:
    def __init__(self):
        self._config = {}

    def read(self, filename): #definig a function that reads a filename? 
        self._config = {}
        with open(filename, 'r') as f: #define opened file as f  
            current_name = None 
            current_key = None

            for line in f:
                if not line.strip(): #what is a strip
                    continue
                if line.strip().startswith('&'): # if the line of text starts wihth & (header) 
                    current_name = line.strip()[1:] # define current name as heder
                    self._config[current_name] = {} #not sure between this and line before 
                elif line.strip() == '/': #if line starts with tht dont define anything 
                    current_name = None
                else:
                    if current_name is None:
                        raise ValueError('Oh no!') # nothing in the file
                    # from lines 15 to 26 you indentify header
                    if '=' in line: # if there is an = in the line, value (key)
                        current_key, value = line.split('=') # derfine that position after = is where key goes 
                        self._config[current_name][current_key.strip()] = value #defineing things i can configure? 
                    else:
                        self._config[current_name][current_key.strip()] += line #something about line spaces? 


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

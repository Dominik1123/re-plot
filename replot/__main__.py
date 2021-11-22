import json
import re
import sys


if __name__ == '__main__':
    text = input()
    if not text.startswith('User Comment'):
        print('Please only provide the "User Comment" field, e.g. via '
              'exiftool example.png | grep "User Comment"')
        sys.exit(1)
    text = re.sub('^User Comment +: +', '', text)
    print(json.dumps(json.loads(text), indent=2))

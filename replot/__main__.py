from argparse import ArgumentParser
import json
import re
import sys

from PIL import Image

from .patch import EXIF_TAGS_BY_NAME


parser = ArgumentParser()
parser.add_argument('file', nargs='?')


def main():
    args = parser.parse_args()
    if args.file:
        img = Image.open(args.file)
        metadata = img.getexif()[EXIF_TAGS_BY_NAME['UserComment']]
    else:
        text = input()
        if text.startswith('User Comment'):
            metadata = re.sub('^User Comment +: +', '', text)
        else:
            print('"User Comment" field not found')
            return 1
    print(json.dumps(json.loads(metadata), indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())

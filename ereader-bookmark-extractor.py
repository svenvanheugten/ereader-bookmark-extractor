from common import extract
import argparse


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()

    argparser.add_argument('volume')
    argparser.add_argument('destination')

    args = argparser.parse_args()
    extract(args.volume, args.destination)

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import argparse
from client import PredictionClient

parser = argparse.ArgumentParser(description='Score some images')
parser.add_argument('host', type=str,
                    help='Host to score against')
parser.add_argument('images', nargs='+', type=str,
                    help='Path of images to score')
parser.add_argument('ssl', type=bool, default=False, help='Use SSL to Score')
parser.add_argument('key', type=str, default='', help='Auth key to use to score - only works with SSL')
args = parser.parse_args()


port = 443 if args.ssl else 80
client = PredictionClient(args.host, port, args.ssl, args.key)
for path in args.images:
    client.score_image(path)

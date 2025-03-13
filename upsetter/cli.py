import argparse
import logging
from . import upset
from fontTools.varLib.instancer import parseLimits


def main():
    parser = argparse.ArgumentParser(
        description="Modern font subsetter – mostly a wrapper around various existing tools",
        epilog="Example: upsetter -s wdth=100 -s wght=400:700 font1.ttf font2.ttf",
    )
    parser.add_argument(
        "-s",
        "--subspace",
        action="append",
        help="List of space separated locations. A location consists of the tag of a variation axis, followed by '=' and the literal, string 'drop', or colon-separated list of one to three values, each of which is the empty string, or a number. E.g.: wdth=100 or wght=75.0:125.0 or wght=100:400:700 or wght=:500: or wght=drop",
    )
    parser.add_argument(
        "-f",
        "--freeze",
        required=False,
        help="Comma-separated list of features to freeze. E.g.: 'ss01' or 'ss01,ss02'",
    )
    parser.add_argument(
        "-r",
        "--remove",
        required=False,
        help="Comma-separated list of features to remove. E.g.: 'ss01' or 'ss01,ss02'",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Be verbose. Set logging level to INFO.",
        action="store_true",
    )
    parser.add_argument("font_files", nargs="+", help="Font files to process (repeatable)")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    upset(
        args.font_files,
        parseLimits(args.subspace) if args.subspace else None,
        args.freeze.split(",") if args.freeze else None,
        args.remove.split(",") if args.remove else None,
    )


if __name__ == "__main__":
    main()

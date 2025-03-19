import argparse
import logging
from . import upset
from fontTools.varLib.instancer import parseLimits


def main():
    parser = argparse.ArgumentParser(
        description="Modern font subsetter – mostly a wrapper around various existing tools",
        epilog="Example: upsetter -s wdth=100,wght=400:700 font1.ttf font2.ttf",
    )
    parser.add_argument(
        "-s",
        "--subspace",
        required=False,
        type=str,
        help=(
            "Comma-separated list of locations. A location consists of the tag of a variation axis, followed by "
            "'=' and the literal, string 'drop', or colon-separated list of one to three values, each of which is "
            "the empty string, or a number. "
            "E.g.: wdth=100,wght=100 or wght=75.0:125.0 or wght=100:400:700 or wght=:500: or wght=drop"
        ),
    )
    parser.add_argument(
        "-u",
        "--unicodes",
        required=False,
        type=str,
        help=(
            "Comma-separated list of unicodes or unicode ranges. E.g.: 'U+0041-005A,U+0061-007A'. "
            "By default, all unicodes are kept."
        ),
    )
    parser.add_argument(
        "-f",
        "--freeze",
        required=False,
        type=str,
        help="Comma-separated list of features to freeze. E.g.: 'ss01' or 'ss01,ss02'",
    )
    parser.add_argument(
        "-r",
        "--remove",
        required=False,
        type=str,
        help="Comma-separated list of features to remove. E.g.: 'ss01' or 'ss01,ss02'",
    )
    # parser.add_argument(
    #     "-i",
    #     "--italic",
    #     help="Split Italic and Roman glyphs into separate fonts",
    #     required=False,
    #     action="store_true",
    # )
    parser.add_argument(
        "-n",
        "--name",
        required=False,
        type=str,
        help="Append suffix to family name, e.g. 'SC', so 'Garamond' becomes 'Garamond SC'.",
    )
    parser.add_argument(
        "--glyph-names",
        help="Keep glyph names intact. Default is to remove them to save space.",
        action="store_true",
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
    else:
        logging.basicConfig(level=logging.WARNING)

    upset(
        args.font_files,
        unicodes=args.unicodes or None,
        subspace=parseLimits(args.subspace.split(",")) if args.subspace else None,
        freeze_features=args.freeze.split(",") if args.freeze else None,
        remove_features=args.remove.split(",") if args.remove else None,
        name=args.name,
        # italic=args.italic,
        keep_glyph_names=args.glyph_names,
    )


if __name__ == "__main__":
    main()

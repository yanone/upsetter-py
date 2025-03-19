import os
from fontTools.ttLib import TTFont
import logging
from types import SimpleNamespace
import copy
from fontTools.varLib.instancer import parseLimits


def font_subspace(ttFont, subspace):
    from fontTools.varLib.instancer import instantiateVariableFont

    ttFont = copy.deepcopy(ttFont)

    assert "fvar" in ttFont, "Font is not a Variable Font"
    logging.info("#" * 40)
    logging.info(f"Subspacing {ttFont} with {subspace}")
    ttFont = instantiateVariableFont(ttFont, subspace, inplace=True)

    return ttFont


# Cycle through all features to freeze and decide whether to freeze them
# with pyft_featfreeze in case all lookups are of type 1 (Single Substitution)
# AND all source glyphs are encoded (otherwise no cmap-remapping is possible)
# OR with gftools-remap-layout in case of all other lookup types
def font_freeze_features(ttFont, freeze_features, name):

    ttFont = copy.deepcopy(ttFont)

    # Disable this check for now, always apply both tactics
    # encoded_glyphs = ttFont.getBestCmap().values()
    # pyft_featfreeze = []

    # if "GSUB" in ttFont:
    #     gsub = ttFont["GSUB"].table
    #     for feature in gsub.FeatureList.FeatureRecord:
    #         if feature.FeatureTag in freeze_features:
    #             found_lookuptypes = set()
    #             lookups = []
    #             for lookup_index in feature.Feature.LookupListIndex:
    #                 lookup = gsub.LookupList.Lookup[lookup_index]
    #                 found_lookuptypes.add(lookup.LookupType)
    #                 lookups.append(lookups)

    #             # All lookups are of type 1 (Single Substitution)
    #             if found_lookuptypes and found_lookuptypes == {1}:

    #                 # Check whether all substitution source glyphs are encoded
    #                 source_glyphs_have_unicodes = []
    #                 for lookup_index in feature.Feature.LookupListIndex:
    #                     lookup = gsub.LookupList.Lookup[lookup_index]
    #                     for subtable in lookup.SubTable:
    #                         for glyph_name in subtable.mapping.keys():
    #                             if glyph_name in encoded_glyphs:
    #                                 source_glyphs_have_unicodes.append(True)
    #                             else:
    #                                 source_glyphs_have_unicodes.append(False)

    #                 # All source glyphs are encoded
    #                 if all(source_glyphs_have_unicodes):
    #                     pyft_featfreeze.append(feature.FeatureTag)

    logging.info("#" * 40)
    logging.info(f"pyft_featfreeze {freeze_features}")

    from opentype_feature_freezer import RemapByOTL

    # Simulate command line arguments
    options = SimpleNamespace()
    options.inpath = ""  # input .otf or .ttf font file
    options.outpath = None  # output .otf or .ttf font file (optional)
    options.features = ",".join(
        freeze_features
    )  # comma-separated list of OpenType feature tags, e.g. 'smcp,c2sc,onum'
    options.script = None  # OpenType script tag, e.g. 'cyrl' (optional)
    options.lang = None  # OpenType language tag, e.g. 'SRB ' (optional)
    options.zapnames = False  # zap glyphnames from the font ('post' table version 3, .ttf only)
    options.suffix = False  # add a suffix to the font family name
    options.usesuffix = None  # use a custom suffix when --suffix is enabled
    options.replacenames = None  # replace in name table, 'search1/replace1,search2/replace2,...'
    options.info = False  # update font version string
    options.report = False  # report languages, scripts and features in font
    options.names = False  # report languages, scripts and features in font
    options.verbose = False

    pyft_featfreezer = RemapByOTL(options)
    pyft_featfreezer.ttx = ttFont

    pyft_featfreezer.remapByOTL()
    if name:
        old_ps_name = ttFont["name"].getName(6, 3, 1, 1033).toUnicode()

        options.suffix = bool(name)  # add a suffix to the font family name
        options.usesuffix = name  # use a custom suffix when --suffix is enabled
        pyft_featfreezer.renameFont()

        new_ps_name = old_ps_name.replace("-", f"{name.replace(' ', '')}-")
        logging.info(f"Replacing in name table: '{old_ps_name}' => '{new_ps_name}'")
        for record in ttFont["name"].names:
            record.string = record.toStr().replace(old_ps_name, new_ps_name)

    # For remap-layout, do all features here regardless of whether they've previously been treated
    # with pyft_featfreeze because remap-layout can handle all GSUB lookup types and also GPOS lookups
    # in case a feature has both GSUB and GPOS lookups.
    from .remap_layout import remap

    commands = [f"{feature}=>ccmp" for feature in freeze_features]
    logging.info("#" * 40)
    logging.info(f"remap_layout {commands}")

    # Continue with remap-layout here
    # Other possible target features are:
    # rclt, rvrn, ccmp, rlig
    remap(ttFont, commands)

    return ttFont


def font_subset(ttFont, unicodes=None, remove_features=None, keep_glyph_names=False):

    ttFont = copy.deepcopy(ttFont)

    # These are the default options when nothing is specifically set
    from fontTools.subset import Subsetter, Options, parse_unicodes

    options = Options()

    # layout features
    gsub = ttFont["GSUB"].table
    features = [FeatureRecord.FeatureTag for FeatureRecord in gsub.FeatureList.FeatureRecord]
    options.layout_features = list(set(features) - set(remove_features) if remove_features else set(features))
    options.glyph_names = keep_glyph_names  # Don't keep glyph names for now (file size optimization)

    # Keep all unicodes
    if unicodes is None:
        unicode_list = []
        for t in ttFont["cmap"].tables:
            if t.isUnicode():
                unicode_list.extend(t.cmap.keys())
                if t.format == 14:
                    unicode_list.extend(t.uvsDict.keys())
    else:
        unicode_list = parse_unicodes(unicodes)

    subsetter = Subsetter(options=options)
    subsetter.populate(unicodes=unicode_list)
    subsetter.subset(ttFont)

    return ttFont


def upset(
    font_files,
    unicodes=None,
    subspace=None,
    freeze_features=None,
    remove_features=None,
    italic=False,
    name="",
    keep_glyph_names=False,
):

    # Input validation
    if freeze_features is not None and remove_features is not None:
        assert (
            set(freeze_features) & set(remove_features) == set()
        ), f"Features to freeze and remove must not overlap: {set(freeze_features) & set(remove_features)}"

    # Cycle through all font files
    for font_file in font_files:
        ttFont = TTFont(font_file)

        # Sub-Spacing
        if subspace:
            ttFont = font_subspace(ttFont, subspace)

        # Feature-Freezing
        if freeze_features is not None:
            ttFont = font_freeze_features(ttFont, freeze_features, name)

        # Subset
        ttFont = font_subset(ttFont, unicodes, remove_features, keep_glyph_names)

        # # Italic
        # TODO: Keep this for later
        # if italic:

        #     # Roman
        #     ttFont_roman = font_subspace(ttFont, parseLimits("ital=0"))
        #     ttFont_roman = font_subset(ttFont_roman, remove_features=["ital"])

        #     # Adjust file name and save the font
        #     font_file = os.path.splitext(font_file)[0] + ".roman.subset" + os.path.splitext(font_file)[1]
        #     ttFont.save(font_file)

        #     # Italic
        #     ttFont_italic = font_subspace(ttFont, parseLimits("ital=1"))
        #     ttFont_italic = font_freeze_features(ttFont_italic, freeze_features=["ital"])
        #     ttFont_italic = font_subset(ttFont_italic)

        #     # Adjust file name and save the font
        #     font_file = os.path.splitext(font_file)[0] + ".italic.subset" + os.path.splitext(font_file)[1]
        #     ttFont.save(font_file)

        # Adjust file name and save the font
        font_file = os.path.splitext(font_file)[0] + ".subset" + os.path.splitext(font_file)[1]
        ttFont.save(font_file)

        ttFont.close()

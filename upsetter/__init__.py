import os
from fontTools.ttLib import TTFont
import logging
from types import SimpleNamespace


def upset(font_files, unicodes=None, subspace=None, freeze_features=None, remove_features=None):

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
            from fontTools.varLib.instancer import instantiateVariableFont

            assert "fvar" in ttFont, "Font is not a Variable Font"
            logging.info("#" * 40)
            logging.info(f"Subspacing {font_file} with {subspace}")
            ttFont = instantiateVariableFont(ttFont, subspace, inplace=True)

            # Adjust file name and save the font
            font_file = os.path.splitext(font_file)[0] + ".subspace" + os.path.splitext(font_file)[1]
            ttFont.save(font_file)

        # Feature-Freezing
        # Cycle through all features to freeze and decide whether to freeze them
        # with pyft_featfreeze in case all lookups are of type 1 (Single Substitution)
        # AND all source glyphs are encoded (otherwise no cmap-remapping is possible)
        # OR with gftools-remap-layout in case of all other lookup types
        if freeze_features is not None:
            encoded_glyphs = ttFont.getBestCmap().values()
            pyft_featfreeze = []

            if "GSUB" in ttFont:
                gsub = ttFont["GSUB"].table
                for feature in gsub.FeatureList.FeatureRecord:
                    if feature.FeatureTag in freeze_features:
                        found_lookuptypes = set()
                        lookups = []
                        for lookup_index in feature.Feature.LookupListIndex:
                            lookup = gsub.LookupList.Lookup[lookup_index]
                            found_lookuptypes.add(lookup.LookupType)
                            lookups.append(lookups)

                        # All lookups are of type 1 (Single Substitution)
                        if found_lookuptypes and found_lookuptypes == {1}:

                            # Check whether all substitution source glyphs are encoded
                            source_glyphs_have_unicodes = []
                            for lookup_index in feature.Feature.LookupListIndex:
                                lookup = gsub.LookupList.Lookup[lookup_index]
                                for subtable in lookup.SubTable:
                                    for glyph_name in subtable.mapping.keys():
                                        if glyph_name in encoded_glyphs:
                                            source_glyphs_have_unicodes.append(True)
                                        else:
                                            source_glyphs_have_unicodes.append(False)

                            # All source glyphs are encoded
                            if all(source_glyphs_have_unicodes):
                                pyft_featfreeze.append(feature.FeatureTag)

            if pyft_featfreeze:

                logging.info("#" * 40)
                logging.info(f"pyft_featfreeze {pyft_featfreeze}")

                from opentype_feature_freezer import RemapByOTL

                # Simulate command line arguments
                options = SimpleNamespace()
                options.inpath = ""  # input .otf or .ttf font file
                options.outpath = None  # output .otf or .ttf font file (optional)
                options.features = ",".join(
                    pyft_featfreeze
                )  # comma-separated list of OpenType feature tags, e.g. 'smcp,c2sc,onum'
                options.script = None  # OpenType script tag, e.g. 'cyrl' (optional)
                options.lang = None  # OpenType language tag, e.g. 'SRB ' (optional)
                options.zapnames = False  # zap glyphnames from the font ('post' table version 3, .ttf only)
                options.suffix = False  # add a suffix to the font family name
                options.usesuffix = ""  # use a custom suffix when --suffix is enabled
                options.replacenames = ""  # replace in name table, 'search1/replace1,search2/replace2,...'
                options.info = False  # update font version string
                options.report = False  # report languages, scripts and features in font
                options.names = False  # report languages, scripts and features in font
                options.verbose = False

                pyft_featfreezer = RemapByOTL(options)
                pyft_featfreezer.ttx = ttFont
                pyft_featfreezer.remapByOTL()

            # For remap-layout, do all features here regardless of whether they've previously been treated
            # with pyft_featfreeze because remap-layout can handle all GSUB lookup types and also GPOS lookups
            # in case a feature has both GSUB and GPOS lookups.
            if freeze_features:
                from .remap_layout import remap

                logging.info("#" * 40)
                logging.info(f"remap_layout {freeze_features}")

                # Continue with remap-layout here
                remap(ttFont, [f"{feature}=>rclt" for feature in freeze_features])

                # Adjust file name and save the font
                font_file = os.path.splitext(font_file)[0] + ".freeze" + os.path.splitext(font_file)[1]
                ttFont.save(font_file)

        # Subset

        # These are the default options when nothing is specifically set
        from fontTools.subset import Subsetter, Options, parse_unicodes

        options = Options()

        # layout features
        gsub = ttFont["GSUB"].table
        features = [FeatureRecord.FeatureTag for FeatureRecord in gsub.FeatureList.FeatureRecord]
        options.layout_features = list(set(features) - set(remove_features) if remove_features else set(features))
        options.glyph_names = True  # Keep glyph names

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

        # Adjust file name and save the font
        font_file = os.path.splitext(font_file)[0] + ".subset" + os.path.splitext(font_file)[1]
        ttFont.save(font_file)

        ttFont.close()

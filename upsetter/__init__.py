import os
from fontTools.ttLib import TTFont
import logging
from types import SimpleNamespace


def upset(font_files, subspace=None, freeze=None, remove=None):

    # Input validation
    if freeze is not None and remove is not None:
        assert (
            set(freeze) & set(remove) == set()
        ), f"Features to freeze and remove must not overlap: {set(freeze) & set(remove)}"

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
        if freeze is not None:
            encoded_glyphs = ttFont.getBestCmap().values()
            pyft_featfreeze = []
            remap_layout = []

            if "GSUB" in ttFont:
                gsub = ttFont["GSUB"].table
                for feature in gsub.FeatureList.FeatureRecord:
                    if feature.FeatureTag in freeze:
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
                            else:
                                remap_layout.append(feature.FeatureTag)
                        else:
                            remap_layout.append(feature.FeatureTag)

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

            if remap_layout:
                logging.info("#" * 40)
                logging.info(f"remap_layout {remap_layout}")

                # Continue with remap-layout here

            if pyft_featfreeze or remap_layout:
                # Adjust file name and save the font
                font_file = os.path.splitext(font_file)[0] + ".freeze" + os.path.splitext(font_file)[1]
                ttFont.save(font_file)

        ttFont.close()

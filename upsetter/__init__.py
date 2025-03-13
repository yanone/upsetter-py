import os
from fontTools.ttLib import TTFont
import logging


def upset(font_files, subspace=None, freeze=None, remove=None):

    # Input validation
    if freeze is not None and remove is not None:
        assert (
            set(freeze) & set(remove) == set()
        ), f"Features to freeze and remove must not overlap: {set(freeze) & set(remove)}"

    # Cycle through all font files
    for font_file in font_files:
        font = TTFont(font_file)

        # Sub-Spacing
        if subspace:
            from fontTools.varLib.instancer import instantiateVariableFont

            assert "fvar" in font, "Font is not a Variable Font"
            logging.info("#" * 40)
            logging.info(f"Subspacing {font_file} with {subspace}")
            font = instantiateVariableFont(font, subspace, inplace=True)

            # Adjust file name and save the font
            font_file = os.path.splitext(font_file)[0] + ".subspace" + os.path.splitext(font_file)[1]
            font.save(font_file)

        # Feature-Freezing
        # Cycle through all features to freeze and decide whether to freeze them
        # with pyftfeatfreeze in case all lookups are of type 1 (Single Substitution) or
        # with gftools-remap-layout in case of all other lookup types
        if freeze is not None:
            pyftfeatfreeze = []
            remaplayout = []
            if "GSUB" in font:
                gsub = font["GSUB"].table
                for feature in gsub.FeatureList.FeatureRecord:
                    found_lookuptypes = set()
                    if feature.FeatureTag in freeze:
                        for lookup_index in feature.Feature.LookupListIndex:
                            lookup = gsub.LookupList.Lookup[lookup_index]
                            found_lookuptypes.add(lookup.LookupType)

                    if feature.FeatureTag in freeze and found_lookuptypes:
                        if found_lookuptypes and found_lookuptypes == {1}:
                            pyftfeatfreeze.append(feature.FeatureTag)
                        else:
                            remaplayout.append(feature.FeatureTag)

            print("pyftfeatfreeze", pyftfeatfreeze)
            print("remaplayout", remaplayout)

        font.close()

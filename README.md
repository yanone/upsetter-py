# Upsetter

Modern-day font subspacer/feature freezer/subsetter/webfont compressor – mostly a wrapper around various existing tools, namely `fonttools`, `gftools-remap-layout` and `pyftfeatfreeze`.

The tool ties together four commonly used techniques to shrink file sizes, dominantly for the purpose of creating webfonts from fonts with large character sets and variable design spaces, or for creating fonts for environments with limited or non-existent user-facing support for OpenType feature selection, such as most office applications.

You can use `upsetter-py` standalone on your computer or server to shrink fonts, but it also operates under the surface of `upsetter-web`, an in-browser platform of the same functionality but with a user interface.

Note that both `upsetter-web` and `upsetter-py` are currently optimized for speed of development and simplicity of use, not execution speed. `upsetter-py` (for now) banks almost entirely on `fonttools` as it is readily-available as a precompiled package for Pyodide, whereas the faster Harfbuzz-based subspacing and subsetting tools are not readily available to use in a browser (and usable by Python). A faster implementation in pure JavaScript is possible in the future but not intended for a minimum viable product.

For subsetting, it takes a list of unicodes, which means that you need to make those decisions externally. This tool takes care of the technical side of shrinking the fonts.

The name Upsetter rhymes with _subsetter_ and is also a hat-tip to the late Lee “Scratch” Perry, the Upsetter, the Psychiatrist, the Disco Devil, the Madman himself, here with a dub cut on Max Romeo’s “Chase The Devil” that Perry also produced, for those who celebrate: https://www.youtube.com/watch?v=rbb192bVGAU.

# Functionality

### 1. Sub-Spacing

`fonttools.varLib.instancer` is employed to sub-space a variable design space, either turning a variable font into a static font entirely or reducing but keeping parts of the designspace by at least partially shrinking the `gvar` table.

### 2. Feature-Freezing

Feature-freezing bakes the functionality of previously _optional_ OpenType features (such as Stylistic Sets or Swashes etc.) into the font as _default_ functionality.

Here, two different techniques are employed. If a feature to freeze consists _entirely_ of single substitutions (GSUB Lookup Type 1), `pyftfeatfreeze` is employed to allow glyphs that become unaccessible as a result of the frozen single substitutions to later be removed from the font. `pyftfeatfreeze` simply remaps glyphs in the `cmap` table with the results that the previous default glyphs now become unreachable and will be removed in the subsetting stage.

In case the feature to freeze consists of a mixture of different lookup types (anything other than pure GSUB Lookup Type 1), a locally-bundled copy of `gftools-remap-layout` is used, with all lookups remapped to `rclt`. This allows for more complex subsitutions such as contextual substitutions to become available in the font by default, but sadly not resulting in a reduced file size.

### 3. Set-Setting

`fonttools.subset` is used to remove unwanted characters, features, and unreachable glyphs from the font.

### 4. Webfont Compressor (not yet implemented)

Finally, fonts can optionally be compressed to _woff2_ webfonts using the `zopfli` compression algorithm which `fonttools` uses and which is also available as a precompiled package for Pyodide.

# Installation

Install it with `pip` via the Python Packaging Index:

```
pip install upsetter
```
or update it with:
```
pip install -U upsetter
```

# Usage

Calling the tool with no arguments will just subset unreachable glyphs as well as some other optimizations via `fontools.subset`:
```
upsetter font.ttf
```

Otherwise, these are the arguments that correspond to each of the four aforementions areas:
```
upsetter -u U+00A0 -s wght=400 -f smcp -r ss01 -c -v font.ttf
```

`-u` or `--unicodes` takes a list of unicodes to keep in the font in the format `U+00A0-U+00B0,U+00C0-U+00F0`. All other encoded characters will be removed as well as glyphs that become unreachable as a consequence of that.

`-s` or `--subspace` takes a list of designspace locations in the format `wght=400:700,wdth=100`.

`-f` or `--freeze` takes a list of features to freeze: `smcp,c2sc`.

`-r` or `--remove` takes a list of features to remove entirely `ss01,ss02,ss03`.

`-c` or `--compress` will compress webfonts into `woff2` (not yet implemented).

`-v` or `--verbose` will print a bunch of stuff to the screen.

# Development Status

This tool is in **alpha** stage and may change at any moment. Don’t use for production purposes yet.
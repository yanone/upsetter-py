# Upsetter

Modern font subspacer/feature freezer/subsetter/webfont compressor – mostly a wrapper around various existing tools, namely `fonttools`, `gftools-remap-layout` and `pyftfeatfreeze`.

The `upsetter-py` tool operates in the background of `upsetter-web`, an in-browser platform of the same functionality, which is based on Pyodide, a WebAssembly-based Python distribution. In case anyone wants to make use of `upsetter-web`, but offline, they would just be pointed to `upsetter-py` instead of implementing an online API which would require a backend, as `upsetter-web` is a pure front-end/in-browser solution.

The name Upsetter rhymes with _subsetter_ and is also a hat-tip to the late Lee “Scratch” Perry, the Upsetter, the Psychiatrist, the Disco Devil, the Madman himself, here with a dub cut on Max Romeo’s “Chase The Devil” that Perry also produced: https://www.youtube.com/watch?v=rbb192bVGAU

# Functionality

The tool ties together four commonly used techniques to shrink file sizes, dominantly for the purpose of creating webfonts from fonts with large character sets and variable design spaces.

`upsetter-py` (for now) banks almost entirely on `fonttools` as it is readily-available as a precompiled package for Pyodide, whereas the faster Harfbuzz-based subspacing and subsetting tools are not readily available to use in a browser.

### 1. Sub-Spacing

`fonttools varLib.instancer` is employed to sub-space a variable design space, either turning a variable font into a static font entirely or reducing but keeping parts of the designspace by at least partially shrinking the `gvar` table.

### 2. Feature-Freezing

Feature-freezing bakes the functionality of previously _optional_ OpenType features (such as Stylistic Sets or Swashes etc.) into the font as _default_ functionality.

Here, two different techniques are employed. If a feature to freeze consists _entirely_ of single substitutions (GSUB Lookup Type 1), `pyftfeatfreeze` is employed to allow glyphs that become unaccessible as a result of the frozen single substitutions to later be removed from the font. `pyftfeatfreeze` simply remaps glyphs in the `cmap` table with the results that the previous default glyphs now become unreachable and will be removed in the subsetting stage.

In case the feature to freeze consists of a mixture of different lookup types (anything other than pure GSUB Lookup Type 1), a locally-bundled copy of `gftools-remap-layout` is used, with all lookups remapped to `rclt`. This allows for more complex subsitutions such as contextual substitutions to become available in the font by default, but sadly not resulting in a reduced file size.

### 3. Set-Setting

`fonttools subset` is used to remove unwanted characters, features, and unreachable glyphs from the font.

### 4. Webfont Compressor

Finally, fonts can optionally be compressed to _woff2_ webfonts using the `zopfli` compression algorithm which `fonttools` uses and which is also available as a precompiled package for Pyodide.
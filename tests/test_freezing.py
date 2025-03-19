# hb-shape --features=ss01,ss02,ss03 --no-positions --no-advances --no-clusters tests/fonts/SubstitutionTest-Regular.ttf a
# == [a.ss01.ss02.ss03]

import os
import subprocess


def system_call(command):
    result = subprocess.run(command.split(" "), capture_output=True, text=True)
    return result.stdout.strip()


def test_substitutiontest_ttf():

    # Check base font
    result = system_call(
        "hb-shape --features=ss01,ss02,ss03 --no-positions --no-advances --no-clusters tests/fonts/SubstitutionTest-Regular.ttf a"
    )
    assert result == "[a.ss01.ss02.ss03]"

    # Freeze ss01
    os.system("upsetter -f ss01 --glyph-names tests/fonts/SubstitutionTest-Regular.ttf")
    result = system_call(
        "hb-shape --features=ss02,ss03 --no-positions --no-advances --no-clusters tests/fonts/SubstitutionTest-Regular.upset.ttf a"
    )
    assert result == "[a.ss01.ss02.ss03]"

    # Freeze ss01,ss02
    os.system("upsetter -f ss01,ss02 --glyph-names tests/fonts/SubstitutionTest-Regular.ttf")
    result = system_call(
        "hb-shape --features=ss03 --no-positions --no-advances --no-clusters tests/fonts/SubstitutionTest-Regular.upset.ttf a"
    )
    assert result == "[a.ss01.ss02.ss03]"


def test_ysabeau():

    # Check base font
    result = system_call(
        "hb-shape --features=ss01,liga --no-positions --no-advances --no-clusters tests/fonts/Ysabeau[wght].ttf fl"
    )
    assert result == "[fl.ss01]"

    # Freeze ss01
    os.system("upsetter -f ss01 --glyph-names tests/fonts/Ysabeau[wght].ttf")
    result = system_call("hb-shape --no-positions --no-advances --no-clusters tests/fonts/Ysabeau[wght].upset.ttf fl")
    assert result == "[fl.ss01]"

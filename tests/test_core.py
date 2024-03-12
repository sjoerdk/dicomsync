import pytest

from dicomsync.core import make_slug


@pytest.mark.parametrize("string_in", ["oneword", "an_underscore", "", "234gffj4"])
def test_ensure_slug_works(string_in):

    assert make_slug(string_in) == string_in


@pytest.mark.parametrize("string_in", ["a space", "a-dash", "Capitals", "$#3548"])
def test_ensure_slug_fail(string_in):

    assert not make_slug(string_in) == string_in

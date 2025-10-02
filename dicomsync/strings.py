"""Functions that work with strings"""

from slugify import slugify


def make_slug(string_in: str) -> str:
    """Make sure the string is a valid slug, usable in a URL or path.
     Uses underscore seperator.

    Returns
    -------
    str Input unchanged

    Raises
    ------
    ValueError
        If string_in is not a valid slug.
    """
    response: str = slugify(string_in, separator="_", lowercase=True)

    return response

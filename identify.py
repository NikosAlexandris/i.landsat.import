from identifiers import LANDSAT_IDENTIFIERS
import re


def identify_product_collection(scene):
    """
    Identify the collection and the validity of a Landsat scene product
    identifier by trying to match it against pre-defined regular expression
    templates.

    Parameters
    ----------
    scene :
        A Landsat product identifier string

    template :
        A list of regular expression templates against which to validate the
        'scene' string

    Returns
    -------
    ...

    Raises
    ------
    ...
    """
    for template_key in LANDSAT_IDENTIFIERS['scene_template']:
        template = LANDSAT_IDENTIFIERS['scene_template'][template_key]
        try:
            # re.match(pattern, string, flags=0)
            if re.match(template, scene):
                return template_key
        except:
            g.fatal(_("No match"))


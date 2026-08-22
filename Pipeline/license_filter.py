"""
license_filter.py
Repository license filtering.
"""

from config import (
    ALLOWED_LICENSES
)

LICENSE_ALIASES = {

    "apache2": "apache-2.0",
    "apache 2.0": "apache-2.0",
    "mit license": "mit",
    "bsd3": "bsd-3-clause",
    "bsd2": "bsd-2-clause"
}

def normalize(license_name):
    if license_name is None:
        return ""

    license_name = (
        license_name
        .lower()
        .strip()
    )

    return LICENSE_ALIASES.get(
        license_name,
        license_name
    )

def filter_sample(sample):

    license_name = normalize(

        sample.get(

            "license",

            ""

        )

    )

    sample["license"] = license_name

    if not license_name:

        #
        # Unknown license.
        #
        # Current policy:
        # Reject.
        #
        return False

    return (

        license_name
        in
        ALLOWED_LICENSES

    )
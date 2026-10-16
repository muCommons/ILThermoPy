'''Checks if ilthermopy package is up-to-date with ILThermo 2.0 database'''

import re as _re
from datetime import datetime as _datetime

from ilthermopy import __updated__
import ilthermopy.errors as _err
import ilthermopy.requests as _req


def CheckLastUpdate() -> None:
    """Prints dates of the last ILThermo 2.0 and ilthermopy updates."""
    # The homepage is JS-driven; the update notice now lives in property-list
    # API metadata (cprmsg), with variable whitespace in the month/day string.
    response = _req.GetPropertyList()
    notice = response.get('cprmsg', '') if isinstance(response, dict) else ''
    match = _re.search(
        r'\bUpdated\s+on\s+([A-Za-z]+)\s+(\d{1,2})\s*,\s*(\d{4})',
        notice,
        _re.IGNORECASE,
    )
    if match is None:
        raise _err.ILThermoResponseError(
            'Property list API', 'cannot extract update date from cprmsg')
    try:
        db_updated = _datetime.strptime(' '.join(match.groups()), '%B %d %Y')
    except ValueError:
        raise _err.ILThermoResponseError(
            'Property list API', f'cannot parse extracted update date: {match.group(0)!r}')
    lib_updated = _datetime.strptime(__updated__, '%B %d, %Y')
    print(f'ILThermo 2.0 database was last updated on {db_updated.strftime("%B %d, %Y")}')
    print(f'ilthermopy package was last updated on {lib_updated.strftime("%B %d, %Y")}\n')
    if lib_updated >= db_updated:
        print('ilthermopy package is up-to-date')
    else:
        print('ilthermopy package is outdated, be careful when using SMILES-related features')

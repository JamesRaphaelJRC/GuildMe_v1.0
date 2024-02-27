#!/usr/bin/env python3
''' Models' helper functions '''


def is_sha256_hashed_password(password: str) -> bool:
    ''' Verifies if a password is a SHA256 hashed password '''
    import re
    if not isinstance(password, str):
        return False
    sha256_pattern = re.compile(r'^[a-fA-F0-9]{64}$')
    return bool(re.match(sha256_pattern, password))


def is_valid_location(location: dict) -> bool:
    ''' Verifies if a location is an already defined location according to
    the already defined location format, i.e. {
    'type': 'Points',
    'coordinates': [longitude, lattitude]
    }
    '''
    if not isinstance(location, dict):
        return False
    if 'type' not in location or 'coordinates' not in location:
        return False
    if location.get('type') != 'Point' and not isinstance(
            location.get('coordinates'), list):
        return False
    if not all(isinstance(x, (int, float)) for x in location.get(
                                            'coordinates')):
        return False
    return True

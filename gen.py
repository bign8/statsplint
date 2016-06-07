#!/usr/bin/env python

import os
import yaml
import json

SRC = '_data/'
DST = 'mlb/players/'
TAG = "<{0}>{1}</{0}>".format
TAGA = "<{0} {2}>{1}</{0}>".format
JEKYLL = '---\ntitle: {}\n---\n'.format

# https://en.wikipedia.org/wiki/Baseball_statistics
lookup = {
    'avg': 'Average',
    'era': 'Earned Run Average',
    'ops': 'On-base Plus Slugging',
    'rbi': 'Run Batted In',
    'ab': 'At Bat',
    'h': 'Hits',
    'bb': 'Base on Balls (Walk)',
    'so': 'Strikeot',
    'hr': 'Home Runs',
    'r': 'Runs Scored',
    'sb': 'Stolen Base',
    'cs': 'Caught Stealing',
    'w': 'Win',
    'l': 'Loss',
    'ip': 'Innings Pitched',
    'sv': 'Save',
    'whip': 'Walks and Hits per Inning Pitched'
}

def all_players():
    data, file_to_yaml = [], {}
    with open(SRC + 'all_players.csv', 'r') as fh:
        data = [l.strip().split(',') for l in fh.readlines()]

    keys, data = data[0], data[1:]
    for j, cell in enumerate(keys):
        if cell in lookup:
            cell = TAGA('abbr', cell.title(), 'title="{}"'.format(lookup.get(cell)))
        else:
            cell = cell.title()
        keys[j] = TAG('th', cell)
    title = TAG('tr', ''.join(keys))

    data.sort(key=lambda x: x[0].split(' ')[-1].lower())

    cnt = 0
    for i, row in enumerate(data):
        name, bits = get_name(row[0])
        if name:
            file_to_yaml[name] = bits
            row[0] = TAGA('a', row[0], 'href="{}"'.format(name))
        else:
            cnt += 1
            print 'Lost:', row[0]

        for j, cell in enumerate(row):
            cell = cell if cell else 'n/a'
            row[j] = TAG('td', cell)
        data[i] = TAG('tr', ''.join(row))
    data = '\n'.join(data)
    print 'Missed:', cnt

    bits = JEKYLL('Players') + TAGA('table', title + data, 'class="table"')
    with open(DST + 'index.html', 'w') as fh:
        fh.write(bits)

    return file_to_yaml


def get_name(
    name, reps=('_', '-',),
    full=lambda n: SRC + 'players/' + n + '.yml',
    res=lambda n: '/mlb/players/' + n + '.html',
    check=lambda n: os.path.exists(n) and os.path.isfile(n),
):
    """
    Replaces the spaces within the human readable name to the system safe name.

    :param name: The human readible name to be checked against the fs.
    :type name: str
    :param reps: A list of space replacement characters.
    :type reps: list or tuple
    :param full: A function that provides the full file path of the names.
    :type full: callable
    :param check: A function that tells if the destination is valid or not.
    :type check: callable
    :return: The file path found on the FS.
    :rtype: str

    Uses binary counting and change of base mathematics to replace spaces with
    values from the reps array.
    """
    parts, base = name.split(' '), len(reps)
    for i in range(base ** (len(parts) - 1)):
        name = parts[0]
        for chunk in parts[1:]:
            mod, i = i % base, i / base
            name += reps[mod] + chunk
        fname = full(name)
        if check(fname):
            return res(name), open(fname).read()
    return None, None


def write_player(path, bits):
    print 'Processing Player:', path
    data = yaml.load(bits)
    name = data['info']['first_name'] + data['info']['last_name']

    with open(path[1:], 'w') as fh: # remove leading /
        fh.write(JEKYLL(name) + bits)


if __name__ == '__main__':
    file_to_yaml = all_players()
    for fname, bits in file_to_yaml.iteritems():
        write_player(fname, bits)

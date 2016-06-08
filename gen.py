#!/usr/bin/env python

import os
import yaml
import json

SRC = '__data/'
DST = 'mlb/players/'
TAG = "<{0}>{1}</{0}>".format
TAGA = "<{0} {2}>{1}</{0}>".format
JEKYLL = '---\ntitle: {}\n---\n'.format

# https://en.wikipedia.org/wiki/Baseball_statistics
lookup = {
    'avg': 'Batting Average',
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
    data = []
    with open(SRC + 'all_players.csv', 'r') as fh:
        data = [l.strip().split(',') for l in fh.readlines()]

    keys, data = data[0], data[1:]
    for j, cell in enumerate(keys):
        if cell in lookup:
            cell = TAGA('abbr', cell.title(), 'title="{}"'.format(lookup.get(cell)))
        else:
            cell = cell.title()
        keys[j] = TAG('th', cell)
    title = '\n' + TAG('tr', '\n' + '\n'.join(keys) + '\n') + '\n'
    title = '\n' + TAGA('thead', title, 'class="thead-default"') + '\n'

    data.sort(key=lambda x: x[0].split(' ')[-1].lower())

    cnt, skp, first = 0, 0, 'A'
    for i, row in enumerate(data):
        real_name = row[0]
        name, bits = get_name(row[0])
        if name:
            if write_player(name, bits):
                row[0] = TAGA('a', row[0], 'href="{}"'.format(name))
            else:
                skp += 1
                # print 'Skipped:', row[0]
        else:
            cnt += 1
            print 'Lost:', row[0]

        for j, cell in enumerate(row):
            cell = cell if cell else 'n/a'
            row[j] = TAG('td', cell)
        data[i] = TAG('tr', '\n' + '\n'.join(row) + '\n')

        # Dividers between last names
        check = real_name.split(' ')[-1].upper()[0]
        if check != first:
            data[i] = title.replace('Name', check + "'s", 1) + data[i]
            first = check

    data = '\n'.join(data)
    print 'Missed:', cnt, 'Skipped:', skp

    bits = JEKYLL('Players') + TAGA('table', title + data, 'class="table table-sm"')
    with open(DST + 'index.html', 'w') as fh:
        fh.write(bits)


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
    info = data.pop('info')
    name = info['first_name'] + ' ' + info['last_name']

    cols, sections = set(), {'misc':{}}
    for key, value in data.iteritems():
        if not isinstance(value, dict):
            continue

        year = unicode(key[0:4])
        if len(key) > 3 and year.isnumeric():
            if year not in sections:
                sections[year] = {}
            sections[year][key[5:]] = value
        elif value.keys() <= lookup.keys():
            sections['misc'][key] = value
        else:
            continue

        cols.update(value.keys())

    # Setup vars for table generation
    rows = []
    cols -= set(['des']) # month designation
    cols = sorted(cols)

    # Table header
    keys = cols[:]
    for j, cell in enumerate(keys):
        if cell in lookup:
            cell = TAGA('abbr', cell.title(), 'title="{}"'.format(lookup.get(cell)))
        else:
            cell = cell.title()
        keys[j] = TAG('th', cell)
    title = '\n' + TAG('tr', '\n' + TAG('th', '&nbsp;') + '\n' + '\n'.join(keys) + '\n') + '\n'
    title = '\n' + TAGA('thead', title, 'class="thead-default"') + '\n'

    def add_row(name, data, emph=False):
        row = [TAG('th', name.replace('_', ' '))]
        row += [TAG('td', data.get(key, '-')) for key in cols]
        row = '\n' + '\n'.join(row) + '\n'
        row = TAGA('tr', row, 'class="table-active"') if emph else TAG('tr', row)
        rows.append(row)

    def add_section(name, data):
        if 'season' in data:
            add_row(name, data.pop('season'), True)
        for key, value in iter_order(data):

            if name.lower() == 'misc':
                key = key.title()
                if 'des' in value:
                    key += ' ({})'.format(value.pop('des'))

            add_row(value.get('des', key), value)

    # Process section data
    add_section('Misc', sections.pop('misc'))
    for key, value in iter_order(sections):
        add_section(key + ' Season', value)

    bits = TAGA('p', TAGA('a', 'Return to Players Page', 'href="/mlb/players/"'), ' class="text-xs-right"')
    bits += TAGA('table', title + '\n'.join(rows) + '\n', 'class="table table-sm"')
    with open(path[1:], 'w') as fh: # remove leading /
        fh.write(JEKYLL(name) + bits)
    return True


def iter_order(dic):
    assert isinstance(dic, dict), 'You stupid?'
    for key in sorted(dic.keys(), key=lambda x: x.lower()):
        yield key, dic[key]


if __name__ == '__main__':
    all_players()

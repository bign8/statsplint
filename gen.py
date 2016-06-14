#!/usr/bin/env python

import os
import yaml
import json
import csv 
import time  # Testing purposes only 

SRC = '__data/'
DST = 'mlb/players/'
TAG = "<{0}>{1}</{0}>".format
TAGA = "<{0} {2}>{1}</{0}>".format
JEKYLL = '---\ntitle: {}\n---\n'.format

biodata = None 

# https://en.wikipedia.org/wiki/Baseball_statistics
lookup = {
    'avg': 'Batting Average',
    'era': 'Earned Run Average',
    'ops': 'On-base Plus Slugging',
    'rbi': 'Run Batted In',
    'ab': 'At Bat',
    'h': 'Hits',
    'bb': 'Base on Balls (Walk)',
    'so': 'Strikeout',
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

def name_to_pid(name): 
    global biodata 
    if biodata is None: 
        with open(SRC + 'bios.yml', 'r') as f:
            biodata = yaml.load(f)
    
    sdn = name.strip().lower()
    for k, v in biodata.iteritems():
        bio_name = v['name'].strip().lower()
        if sdn == bio_name: 
            return str(k)

    print name + ' could not be matched!'
    return name


def get_pid_data(pid): 
    global biodata 
    if biodata is None: 
        with open(SRC + 'bios.yml', 'r') as f:
            biodata = yaml.load(f)
    
    sid = int(pid) 
    t = biodata.get(sid)
    if t is None: 
        print sid, biodata
    return t 

def all_players(): 
    ptypes = ['batters', 'pitchers'] 
    for p in ptypes: 
        some_players(p) 


def some_players(ptype='pitchers'):
    data = []
    with open(SRC + 'all_{}.csv'.format(ptype), 'r') as fh:
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
        name, csv_dat, yml_dat = get_name(row[0])
        time.sleep(0.01)
        
        if name:
            if write_player(name, csv_dat, yml_dat):
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
    full=lambda n: SRC + 'players/data_' + n + '.csv',
    res=lambda n: '/mlb/players/' + n + '.html',
    check=lambda n: os.path.exists(n) and os.path.isfile(n),
):
    """
    NOTE: Hi Nate! I broke all the stuff in here... sorry, I know you were 
    proud of it... 
    """
    str_name = name.replace(' ', '_')
    pid_name = name_to_pid(name)
    fname = full(pid_name)
    
    if check(fname):
        return res(str_name), csv.DictReader(open(fname)), get_pid_data(pid_name)
    return None, None, None


def write_player(path, csvbits, ymlbits):
    print 'Processing Player:', path
    info = ymlbits.copy()
    name = info['first_name'] + ' ' + info['last_name']

    # TODO: verify image is valid
    image = """
<p class="text-xs-center">
  <img src="http://mlb.mlb.com/mlb/images/players/head_shot/{id}.jpg" alt="{name}">
</p>""".format(
        name=name,
        id=info.get('id')
    ).strip()

    cols, sections = set(), {'misc':{}}
    for d_row in csvbits: 
        # FIXME: Hackey solution
        rt = d_row['month'] 
        del d_row['month'] 

        if '20' not in rt: 
            sections['misc'][rt] = d_row
            continue 

        year = unicode(rt[-4:])
        if year.isnumeric():
            if year not in sections: 
                sections[year] = {} 
            sections[year][rt[0:-6]] = d_row 

        else: 
            year = unicode(rt[0:4])
            if year.isnumeric():
                if year not in sections: 
                    sections[year] = {} 
                sections[year]['{} Season'.format(year)] = d_row 

            else:
                sections['misc'][rt] = d_row 

        cols.update(d_row.keys()) 
    # Setup vars for table generation
    rows = []
    #cols -= set(['des']) # month designation
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
        if data.get('ab') == '0': 
            return None
        row = [TAG('th', name.replace('_', ' '))]
        row += [TAG('td', data.get(key, '-')) for key in cols]
        row = '\n' + '\n'.join(row) + '\n'
        row = TAGA('tr', row, 'class="table-active"') if emph else TAG('tr', row)
        rows.append(row)

    def add_section(name, data):
        m_list = ['March', 'April', 'May', 'June', 'July', 'August', 
                'September', 'October', 'November']
        m_list.reverse() 

        if name.lower() != 'misc': 
            seas_val = '{} Season'.format(name)
            add_row(seas_val, data.pop(seas_val))
        
        else: 
            for k, v in data.iteritems(): 
                add_row(k, v)
        for m in m_list: 
            if data.get(m) is None: 
                continue 
            add_row(m, data.pop(m))
    
    add_section('misc', sections.pop('misc'))
    cur_years = [2016, 2015, 2014, 2013, 2012, 
            2011, 2010, 2009]  # TODO: Create this each run
    for _y in cur_years: 
        _yn = str(_y) 
        add_section(_yn, sections.get(_yn))

    bits = image + "\n"
    bits += TAGA('p', TAGA('a', 'Return to Players Page', 'href="/mlb/players/"'), ' class="text-xs-right"')
    bits += TAGA('table', title + '\n'.join(rows) + '\n', 'class="table table-sm"')
    with open(path[1:], 'w') as fh: # remove leading /
        fh.write(JEKYLL(name) + bits)
    return True


def iter_order(dic):
    assert isinstance(dic, dict), 'You stupid?'
    for key in sorted(dic.keys(), key=lambda x: x.lower()):
        yield key, dic[key]


def load_bios_teams():
    print 'Loading prefetch data...'
    bios, teams = {}, {}
    with open(SRC + 'bios.yml') as fh:
        bios = yaml.load(fh)
    with open(SRC + 'teams.yml') as fh:
        teams = yaml.load(fh)
    print 'Prefetch data loaded.'
    return bios, teams


def gen_teams(teams, bios):
    print 'Generating team pages...'
    objs = []  # obj['league'], obj['division']
    for slug, obj in teams.iteritems():
        obj['slug'] = slug
        obj['division'] = obj['division'].split(' ')[1]
        obj['league'] = 'American League' if obj['league'] == 'AL' else 'National League'
        obj['games'] = obj['wins'] + obj['loses']
        objs.append(obj)

    # TODO: generate stats for leagues/divisions

    rows = [
        """
        <thead class="thead-default">
            <tr>
                <th>Name</th>
                <th>Wins</th>
                <th>Loses</th>
                <th>Games</th>
            </tr>
        </thead>
        """
    ]

    l, d = '', ''
    for team in sorted(objs, key=lambda x: [x['league'], x['division'], -int(x['wins']), x['loses']]):
        if team['division'] != d:
            l, d = team['league'], team['division']
            rows.append("""
            <tr class="table-active">
                <th colspan="4">{} &mdash; {}</th>
            </tr>
            """.format(l, d))

        link = gen_team(team, bios)

        rows.append("""
        <tr>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
        </tr>
        """.format(link, team['wins'], team['loses'], team['wins'] + team['loses']))

    with open('mlb/teams/index.html', 'w') as fh:
        fh.write(JEKYLL('Teams') + TAGA('table', '\n'.join(rows) + '\n', 'class="table table-sm"'))
    print 'Team pages generated.'

team_tpl = """
<strong>League:</strong> {league}<br/>
<strong>Division:</strong> {division}<br/>
<strong>Wins:</strong> {wins}<br/>
<strong>Loses:</strong> {loses}<br/>
<strong>Games:</strong> {games}
""".format


def gen_team(team, bios):
    path, rows = 'mlb/teams/{}.html'.format(team['slug']),  ["""
    <thead class="thead-default">
        <tr>
            <th>&nbsp;</th>
            <th>Name</th>
            <th>Number</th>
        </tr>
    </thead>
    """]

    for player_id in team['players']:
        if player_id not in bios:
            print '\t', 'Missing Player ID:', player_id
            continue
        player = bios[player_id]
        rows.append("""
        <tr>
            <td>
                <img src="{imagefile}" alt="{name}">
            </td>
            <td>
                <a href="{link}">{name}</a>
            </td>
            <td>{jersey_number}</td>
        </tr>
        """.format(link=player_link(player), **player))

    bits = team_tpl(**team)
    bits += TAGA('table', '\n'.join(rows) + '\n', 'class="table table-sm"')
    with open(path, 'w') as fh:
        fh.write(JEKYLL(team['name']) + bits)

    return TAGA('a', team['name'], 'href="/{}"'.format(path))


def player_link(player):
    first = player['first_name'].replace(' ', '-')
    last = player['last_name'].replace(' ', '-')
    return '/mlb/players/' + first + '_' + last + '.html'


if __name__ == '__main__':
    bios, teams = load_bios_teams()
    gen_teams(teams, bios)
    all_players()

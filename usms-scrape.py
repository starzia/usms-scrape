#!/usr/bin/python
'''
Just run this without any paramenters.

This script scrapes the best swim times for members of the Evanston Wild Catfish Masters Swim team
and prints out a ranking of best times for each event.  The script was written because this view
of the data is not available on the usms.org website.

These rankings would be especially useful for coaches needing to assemble relay teams.
'''
from lxml import html
import requests
import datetime
from dateutil.relativedelta import relativedelta

def get_tree (url):
    page = requests.get(url)
    return html.fromstring(page.content)

def get_2year_roster():
    '''return rosters for both the current season and the prior one'''
    now = datetime.datetime.now()
    year = int(now.year)
    if now.month > 10:
        year += 1
    roster = get_roster(year-1);
    for id, name in get_roster(year-1).items():
        if id not in roster:
            roster[id] = name;
    return roster;


def get_roster(year):
    '''return a map of [USMS-id] -> [Fullname]'''
    import csv, io

    # download csv team roster
    team_url = 'http://www.usms.org/reg/members/jqs/lmscmembers.php?LMSCID=21&RegYear='+str(year)+'&oper=csv&_search=false&nd=1481396514766&rows=500&page=1&sidx=BinaryLastName+asc%2C+FirstName+asc%2C+RegDate&sord=asc&totalrows=-1';
    team_csv = requests.get(team_url).text;

    roster = {};
    # add each team member
    count = 0;
    for columns in csv.reader(io.StringIO(team_csv)):
        count += 1;
        # skip first line
        if count == 1: continue;

        if columns[4] != 'EVM': continue; # just include our workout group
        fullname = columns[0] + ' ' + columns[2];
        id = columns[5].split('-')[1]; # the part of the id after the hyphen is the permanent id
        roster[id] = fullname;
    return roster;


def get_best_results(swimmer_id, since_date):
    '''return a map of [event name] -> [time].
       Currently this gets your best SCY times from your current age group only.'''

    # download the HTMl for the individual's results
    page = get_tree('http://www.usms.org/comp/meets/indresults.php?SwimmerID=' + swimmer_id);

    # pick out the first table, which corresponds to most recent age group and SCY
    tables = page.xpath('//table')
    # if there are no results, stop
    if len(tables) == 0:
        return {};
    table = tables[0]

    # look through all swim result rows
    best_times = {};
    for row in table.xpath('.//tr[@valign="top"]'):
        # ignore header row
        if len(row.xpath('.//th')) is not 0: continue;
        # parse the columns
        event = row.xpath('(.//td)[5]')[0].text.strip();
        if event == '':
            event = row.xpath('.//td/strong')[0].text;
        # date of swim
        date = row.xpath('(.//td)[2]')[0].text;
        date = date[1:11];
        # ignore times more than 3 years old
        if date < since_date:
            continue;

        # time can either be in a link or not, and may have an asterisk or not
        race_time = row.xpath('(.//td)[7]')[0].text.strip();
        if race_time == '':
            e = row.xpath('(.//td)[7]//span');
            if len(e) > 0 and e[0].text is not None:
                race_time = e[0].text.strip();
            else:
                race_time = row.xpath('(.//td)[7]//a')[0].text.strip();
        # ignore "&nbsp;*" asterisk
        race_time = race_time.replace(u'\xa0*','')
        # ignore DQs
        if race_time == 'DQ' or race_time == 'DNF': continue;
        # prefix with spaces to make all times ten chars long so they can be sorted
        race_time = race_time.rjust(10);
        # HACK: suffix times with the age, for our information
        age = row.xpath('(.//td)[3]')[0].text.strip();
        race_time = race_time + ' (' + age + ')'
        # add the time, but only if it's faster than any other one we already recorded for him/her
        if event in best_times:
            other_time = best_times[event];
            if other_time < race_time: continue;
        best_times[event] = race_time;
    return best_times;


def scrape_team ():
    # define the earliest races to include
    since_date = (datetime.date.today() + relativedelta(years=-3)).strftime("%Y-%m-%d");

    # get the team index
    roster = get_2year_roster();

    # for each team member, get their best event results
    team_results = {};
    for usms_id in roster:
        team_results[usms_id] = get_best_results(usms_id, since_date);

    # aggregate results by event
    event_best_results = {}; # maps from "event" -> [[time, usms_id], ...]
    for usms_id, best_results in team_results.items():
        for event, time in best_results.items():
            if event not in event_best_results:
                event_best_results[event] = [];
            event_best_results[event].append({'time':time, 'usms_id':usms_id});
    # sort each list of times
    for event, results in event_best_results.items():
        event_best_results[event] = sorted(results, key=lambda result: result['time']);

    # print team rankings for each event
    for stroke in ['Free', 'Fly', 'Back', 'Breast', 'IM']:
        for distance in [50, 100, 200, 400, 500, 800, 1000, 1650]:
            event = "%d %s" % (distance, stroke)
            if event in event_best_results:
                results = event_best_results[event]
                print(event);
                for result in results:
                    print(result['time'] + ' ' + roster[result['usms_id']]);
                print()

if __name__ == '__main__':
    scrape_team();

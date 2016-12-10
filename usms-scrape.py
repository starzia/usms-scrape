#!/usr/bin/python
from lxml import html
import requests

def get_tree (url):
    page = requests.get(url)
    return html.fromstring(page.content)

'''return a map of [USMS-id] -> [Fullname]'''
def get_roster():
    # download csv team roster
    team_url = 'http://www.usms.org/reg/members/jqs/lmscmembers.php?LMSCID=21&RegYear=2017&oper=csv&_search=false&nd=1481396514766&rows=500&page=1&sidx=BinaryLastName+asc%2C+FirstName+asc%2C+RegDate&sord=asc&totalrows=-1';
    team_csv = requests.get(team_url).content;

    roster = {};
    # add each team member
    count = 0;
    for line in team_csv.splitlines():
        count += 1;
        # skip first line
        if count == 1: continue;

        columns = line.split(',')
        if columns[4] != 'EVM': continue; # just include our workout group
        fullname = columns[0] + ' ' + columns[2];
        id = columns[5];
        roster[id] = fullname;
    return roster;


'''return a map of [event name] -> [time].
   Currently this gets your best SCY times from your current age group only.'''
def get_best_results(usms_id):
    # download the HTMl for the individual's results
    swimmer_id = usms_id.split('-')[1];
    page = get_tree('http://www.usms.org/comp/meets/indresults.php?SwimmerID=' + swimmer_id);

    # pick out the first table, which corresponds to most recent age group and SCY
    tables = page.xpath('//table')
    # if there are no results, stop
    if len(tables) == 0:
        return {};
    table = tables[0]

    # pick out all the rows with bgcolor="#EEEEEE" which correspond to best times
    best_times = {};
    for best_row in table.xpath('//tr[@bgcolor="#EEEEEE"]'):
        # pick out the event name and time
        event = best_row.xpath('//td/strong')[0].text;
        # time can either be in a link or not, and may have an asterisk or not
        time = best_row.xpath('(//td)[7]')[0].text.strip();
        if time == '':
            e = best_row.xpath('(//td)[7]//span');
            if len(e) > 0 and e[0].text is not None:
                time = e[0].text.strip();
            else:
                time = best_row.xpath('(//td)[7]//a')[0].text.strip();
        # ignore "&nbsp;*" asterisk
        time = time.replace(u'\xa0*','')
        # prefix with spaces to make all times ten chars long so they can be sorted
        time = time.rjust(10);
        # HACK: suffix times with the age, for our information
        age = best_row.xpath('(//td)[3]')[0].text.strip();
        time = time + ' (' + age + ')'
        best_times[event] = time;
    return best_times;

def scrape_team ():
    # get the team index
    roster = get_roster();

    # for each team member, get their best event results
    team_results = {};
    for usms_id in roster:
        team_results[usms_id] = get_best_results(usms_id);

    # aggregate results by event
    event_best_results = {}; # maps from "event" -> [[time, usms_id], ...]
    for usms_id, best_results in team_results.iteritems():
        for event, time in best_results.iteritems():
            if event not in event_best_results:
                event_best_results[event] = [];
            event_best_results[event].append({'time':time, 'usms_id':usms_id});
    # sort each list of times
    for event, results in event_best_results.iteritems():
        event_best_results[event] = sorted(results, key=lambda result: result['time']);

    # print team rankings for each event
    for event, results in event_best_results.iteritems():
        print event;
        for result in results:
            print result['time'] + ' ' + roster[result['usms_id']];
        print

if __name__ == '__main__':
    scrape_team();
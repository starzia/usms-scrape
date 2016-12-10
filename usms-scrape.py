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
    for line in team_csv.splitlines():
        columns = line.split(',')
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
        # time can either be in a link or not
        time = best_row.xpath('(//td)[7]')[0].text.strip();
        if time == '':
            time = best_row.xpath('(//td)[7]//a')[0].text.strip();
        best_times[event] = time;
    return best_times;

def scrape_team ():
    # get the team index
    roster = get_roster();

    # for each team member, get their best event results
    for usms_id in roster:
        print usms_id;
        print get_best_results(usms_id);
        print;

    # print team rankings for each event

if __name__ == '__main__':
    scrape_team();
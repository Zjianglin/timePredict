# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from future.builtins import str
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib.ticker as ticker
import gzip, seaborn
seaborn.set() #Plot styling


class Log(object):
    def __init__(self, file=None):
        self.events = 0
        self.cases = []
        self.acivities =  set()
        self.global_trace = set('case_duration')
        self.global_event = set(['event_duration', 'activity_id'])
        self.__log_from_xes(file)

    def __log_from_xes(self, file):
        '''[filename] can be a file or filename'''
        if isinstance(file, str): #a filename
            filename=file
            if filename.endswith('.gz'):
                filename=gzip.open(filename, 'rb')
            else:
                pass # Just send the filename to xmltree.parse
        else:
             filename=file.name
        tree = ET.ElementTree(file=filename)
        root = tree.getroot()
        tagbase = '{http://www.xes-standard.org/}'
        for child_of_root in root:
            if child_of_root.tag == ''.join([tagbase, 'global']):
                if child_of_root.attrib['scope'] == 'trace':
                    for feature in child_of_root:
                        self.global_trace.add(feature.attrib['key'])
                else:
                    for feature in child_of_root:
                        self.global_event.add(feature.attrib['key'])
            elif child_of_root.tag == ''.join([tagbase, 'trace']):
                case = {}
                events = []
                for feature in child_of_root:
                    if feature.tag == ''.join([tagbase, 'event']):
                        event = {}
                        for s in feature:
                            event[s.attrib['key']] = s.attrib['value']
                        event['activity_id'] = ' '.join([event['concept:name'], event['lifecycle:transition']])
                        events.append(event)
                    else:#case context
                        case[feature.attrib['key']] = feature.attrib['value']
                events.sort(key=lambda e:e['time:timestamp'])
                case['events'] = events
                if case.get('endDate'):
                    case['case_duration'] = (dates.datestr2num(case['startDate']) - dates.datestr2num(case['endDate']))
                else:
                    case['case_duration'] = None
                self.cases.append(case)
        return None

    def abs_time_chart(self, title='Handling of Building Permit Applications in The Netherlands'):
        '''
        Dotted chart for the process of the building permit using absolute time
        '''
        case_ids = []
        fig, ax = plt.subplots(figsize=(18, 10))
        for case in self.cases:
            date = [e['time:timestamp'] for e in case['events']]
            date = np.array(dates.datestr2num(date))
            case_id = [int(case['concept:name'])] * len(date)
            case_ids.append(int(case['concept:name']))
            color = 'g' if case['caseStatus'] == 'G' else 'r'
            ax.plot_date(date, case_id, xdate=True, C=color)
        # format the ticks
        ax.xaxis.set_major_locator(dates.MonthLocator(3))
        ax.xaxis.set_major_formatter(dates.DateFormatter("%Y-%m"))
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
        ax.set_ylim(max(case_ids) + 10, min(case_ids) - 10)
        ax.set_title(title)
        ax.set_xlabel('Event: time:timestamp')
        ax.set_ylabel('Trace: concept:name')
        fig.autofmt_xdate()
        fig.show()
        fig.savefig("../resource/abs_time_chart.png")

    def rel_time_chart(self, title=''):
        '''
        Dotted chart for the process of the building permit using relative time
        '''
        case_ids = []
        fig, ax = plt.subplots(figsize=(16, 9))
        for case in self.cases:
            date = [e['time:timestamp'] for e in case['events']]
            date = np.array(dates.datestr2num(date))
            date -= dates.datestr2num(case['startDate'])
            date[date < 0] = 0
            case_id = [int(case['concept:name'])] * len(date)
            case_ids.append(int(case['concept:name']))
            color = 'g' if case['caseStatus'] == 'G' else 'r'
            ax.scatter(date, case_id, c=color)
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
        ax.set_ylim(max(case_ids) + 10, min(case_ids) - 10)
        ax.set_title(title)
        ax.set_xlabel('Event: time:timestamp(relative)')
        ax.set_ylabel('Trace: concept:name')
        #fig.show()
        fig.savefig("../resource/rev_time_chart.png")

    def statistics(self):
        if not self.acivities:
            for trace in self.cases:
                for event in trace.get('events'):
                    self.acivities.add(event.get('activity_id'))
                    self.events += 1

        all_cases = len(self.cases)
        all_events = self.events
        longest_trace = 0
        shortest_trace = 999
        for t in self.cases:
            l = len(t.get('events'))
            if l > longest_trace:
                longest_trace = l
            if shortest_trace > l:
                shortest_trace = l

        print('Number of cases: ', all_cases)
        print('Number of activities: ', len(self.acivities))
        print('Number of events: ', all_events)
        print('Length of longest case: ', longest_trace)
        print('Length of shortest case: ', shortest_trace)
        print('Average length of case: ', '{0:.1f}'.format(all_events/all_cases))

if __name__ == "__main__":
     log = Log("../resource/BPIC15_3.xes.xml")
     #log.abs_time_chart()
     #log.rel_time_chart()
     log.statistics()

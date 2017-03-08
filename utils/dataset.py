# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from future.builtins import str
from collections import defaultdict
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
                        self.events += 1
                    else:#case context
                        case[feature.attrib['key']] = feature.attrib['value']
                events.sort(key=lambda e:e['time:timestamp'])
                case['events'] = events
                if case.get('endDate'):
                    case['case_duration'] = (dates.datestr2num(case['endDate']) - dates.datestr2num(case['startDate']))
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

    def get_unique_activities(self):
        activities = set()
        for trace in self.cases:
            for event in trace.get('events'):
                activities.add(event.get('activity_id'))
        return activities

    def statistics(self):
        activities = self.get_unique_activities()
        all_cases = len(self.cases)
        all_events = self.events
        completed_cases = 0
        longest_trace = 0
        shortest_trace = 999
        for t in self.cases:
            completed_cases += 1 if t.get('caseStatus') == 'G' else 0
            l = len(t.get('events'))
            if l > longest_trace:
                longest_trace = l
            if shortest_trace > l:
                shortest_trace = l

        print('Number of cases: ', all_cases)
        print('Number of completed cases: ', completed_cases)
        print('Number of activities: ', len(activities))
        print('Number of events: ', all_events)
        print('Length of longest case: ', longest_trace)
        print('Length of shortest case: ', shortest_trace)
        print('Average length of case: ', '{0:.1f}'.format(all_events/all_cases))

    def activity_frequencies(self, case_count=True):
        '''
        Return a dicitionary mapping each activity to the number of occurances
        in the log.
        [case_count]If True, count the number of cases in which the activity appears,
        not the total occurances(each activity may appears multiple times per case).
        '''
        act_freq = defaultdict(int)
        for case in self.cases:
            trace = [e['activity_id'] for e in case.get('events')]
            if case_count:
                trace = set(trace)
            for act in trace:
                act_freq[act] += 1
        return act_freq

    def case_duration_histogram(self):
        '''
        Return a list of tuples(x, y) where x is the case identifier and y is
        its time duration
        '''
        hist = []
        for case in self.cases:
            if not case.get('caseStatus') == 'G':
                continue
            if case.get('case_duration') == None:
                continue
            hist.append((case.get('concept:name'), case.get('case_duration')))
        return hist

    def plot_histogram(self, hist, xlabel='', ylabel='', title=''):
        x, y = zip(*hist)
        xpos = np.arange(len(x))
        ax = plt.axes()
        ax.set_xticklabels(x)
        plt.bar(xpos, y)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.autoscale()
        plt.savefig('../resource/' + title.replace(' ', '_') + '.png')
        plt.show()


if __name__ == "__main__":
     log = Log("../resource/BPIC15_3.xes.xml")
     #log.abs_time_chart()
     #log.rel_time_chart()
     log.statistics()
     log.plot_histogram(log.case_duration_histogram(), xlabel='case: concept:name',
                        ylabel='case_duration(days)', title='case duration distribute')
     log.plot_histogram(log.activity_frequencies().items(), xlabel='activity',
                        ylabel='frequency', title='activity frequency distribute')


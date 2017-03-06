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
        self.event_num = 0
        self.cases = []
        self.acivities =  pd.Series([])
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
                        event['activity_id'] = ' '.join([event['concept:name'].split('_')[1], event['activityNameEN']])
                        events.append(event)
                    else:#case context
                        case[feature.attrib['key']] = feature.attrib['value']
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
        fig.savefig("abs_time_chart.png")

    def rel_time_chart(self, title=''):
        '''
        Dotted chart for the process of the building permit using relative time
        '''
        case_ids = []
        max_time = 0
        fig, ax = plt.subplots(figsize=(16, 9))
        for case in self.cases:
            date = [e['time:timestamp'] for e in case['events']]
            date = np.array(dates.datestr2num(date))
            date -= dates.datestr2num(case['startDate'])
            date[date < 0] = 0
            max_time = date.max()
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
        fig.savefig("rev_time_chart.png")


if __name__ == "__main__":
     log = Log("BPIC15_1.xes.xml")
     #log.abs_time_chart()
     log.rel_time_chart()

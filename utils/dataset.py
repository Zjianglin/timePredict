# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from future.builtins import str
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib.pylab as pl
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
                case['case_duration'] = None #!!! need to process tzinfo
                self.cases.append(case)
        return None

    def get_dotted_chart(self):
        fig, ax = plt.subplots()
        for case in self.cases:
            date = [e['time:timestamp'] for e in case['events']]
            date = dates.datestr2num(date)
            case_id = [int(case['concept:name'])] * len(date)
            color = 'g' if case['caseStatus'] == 'G' else 'o'
            ax.plot_date(date, case_id, xdate=True, C=color)
        #ax.xaxis.set_major_locator(dates.MonthLocator())
        ax.xaxis.set_major_formatter(dates.DateFormatter("%Y-%m"))
   #     ax.xaxis.set_minor_locator(dates.WeekdayLocator())
        ax.autoscale_view()
        ax.grid(True)
        fig.autofmt_xdate()
        plt.show()


if __name__ == "__main__":
     log = Log("BPIC15_1.xes.xml")
     log.get_dotted_chart()

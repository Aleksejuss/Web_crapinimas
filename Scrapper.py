import requests
from contextlib import closing
from bs4 import BeautifulSoup
import logging
import datetime
import csv
import pandas as pd
import WebReader as wr
import Data_cleaning as dc


forcal = []


def append_day_info(startlink):
    # Takes url representing certain day as parameter
    # Appends day info to forcal list

    table = wr.parse_content(startlink, 'table', 'calendar__table')
        # do not use the ".calendar__row--grey" css selector (reserved for historical data)
    trs = table.select("tr.calendar__row.calendar_row")
    fields = ["date","time","currency","impact","event","actual","forecast","previous"]
    # some rows do not have a date (cells merged)
    curr_year = startlink[-4:]
    curr_date = ""
    curr_time = ""
    for tr in trs:
        dict = {}
        # fields may mess up sometimes, see Tue Sep 25 2:45AM French Consumer Spending
        # in that case we append to errors.csv the date time where the error is
        try:
            for field in fields:
                data = tr.select("td.calendar__cell.calendar__{}.{}".format(field,field))[0]
                # print(data)
                if field=="date" and data.text.strip()!="":
                    curr_date = data.text.strip()
                elif field=="time" and data.text.strip()!="":
                    # time is sometimes "All Day" or "Day X" (eg. WEF Annual Meetings)
                    if data.text.strip().find("Day")!=-1:
                        curr_time = "12:00am"
                    else:
                        curr_time = data.text.strip()
                elif field=="currency":
                    currency = data.text.strip()
                elif field=="impact":
                    # when impact says "Non-Economic" on mouseover, the relevant
                    # class name is "Holiday", thus we do not use the classname
                    impact = data.find("span")["title"]
                elif field=="event":
                    event = data.text.strip()
                elif field=="actual":
                    actual = data.text.strip()
                elif field=="forecast":
                    forecast = data.text.strip()
                elif field=="previous":
                    previous = data.text.strip()
            date = datetime.datetime.strptime(",".join([curr_year,curr_date,curr_time]),"%Y,%a%b %d,%I:%M%p")
            # date = datetime.datetime.strptime(",".join([curr_year,curr_date,curr_time]),"%Y,%a%b %d,%I:%M%p")
            # date = datetime.datetime.strptime(",".join([curr_year,curr_date]),"%Y,%a%b")
            # time = datetime.datetime.strptime(curr_time, "%d,%I:%M%p")
            dict["Date"] = date.strftime("%Y-%m-%d %H:%M:%S")
            dict["Currency"] = currency
            dict["Impact"] = impact
            dict["Event"] = event
            dict["Actual"] = actual
            dict["Forecast"] = forecast
            dict["Previous"] = previous
            forcal.append(dict)
            # forcal.append(",".join([str(dt),currency,impact,event,actual,forecast,previous]))
        except:
            with open("errors.csv","a") as f:
                csv.writer(f).writerow([curr_year,curr_date,curr_time])


def getEconomicCalendar(startlink,endlink):
    # Function takes interval of days for which to scrape data
    # Scrapes for each day

    # write to console current status
    logging.info("Scraping data for link: {}".format(startlink))
    append_day_info(startlink)

    # exit recursion when last available link has reached
    if startlink == endlink:
        logging.info("Successfully retrieved data")
        #result_DF = pd.DataFrame(forcal)
        #print(result_DF)
        return pd.DataFrame(forcal)

    data = wr.get_url_content(startlink)
    soup = BeautifulSoup(data, "html.parser")
    # get the link for the next week and follow

    follow = soup.select("a.calendar__pagination.calendar__pagination--next.next")
    follow = 'https://www.forexfactory.com/' + follow[0]["href"]
    getEconomicCalendar(follow,endlink)


def setLogger():
    # Logs and presents status

    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='logs_file',
                    filemode='w')
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


if __name__ == '__main__':
    
    print('Main starts')
    setLogger()
    getEconomicCalendar('https://www.forexfactory.com/calendar?day=apr1.2020', 'https://www.forexfactory.com/calendar?day=apr3.2020')
    data = pd.DataFrame(forcal)
    print('test:', data)
    print(dc.cleaning_data(data, 'Forecast'))
    print(dc.chg_type_and_cleaning_ch(data, 'Forecast'))
    print(dc.filtration(data, 'Currency', 'EUR', 'Impact', 'Low'))



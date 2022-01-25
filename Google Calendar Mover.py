from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime, timezone, timedelta
import csv
import os

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def main():
    path="backups"
    if not os.path.isfile(path):
        try:
            os.mkdir(path)
        except OSError:
            print ("Creation of the directory %s failed" % path)
        else:
            print ("Successfully created the directory %s " % path)
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        calendars={}
        finishedId=''
        for calendar_list_entry in calendar_list['items']:
            if "finishedst" in calendar_list_entry['summary'].lower():
                   finishedId=calendar_list_entry['id']
                   finishedFileName=calendar_list_entry['summary']
        for calendar_list_entry in calendar_list['items']:
            
            if "$T" in calendar_list_entry['summary']:
                print(calendar_list_entry['summary'])

                # TimeFormatting
                now = (datetime.utcnow()).isoformat() + 'Z' # 'Z' indicates UTC time
                tommorrow = (datetime.utcnow()+timedelta(days=1)).isoformat() + 'Z' # 'Z' indicates UTC time
                local_time = datetime.now(timezone.utc).astimezone()
                daysRemove=timedelta(days=40)
                local_time_daysRemoved=local_time-daysRemove

                
                # CallAPi
                events_result = service.events().list(calendarId=calendar_list_entry['id'],maxResults=15,
                 timeMax=tommorrow,timeMin=local_time_daysRemoved.isoformat(), singleEvents=True,orderBy='startTime').execute()
                events = events_result.get('items', [])

                printCal=False
                for event in events:
                    subject=event['summary']
                    startDateString=getStartDate(event)
                    evDay=datetime.strptime(startDateString[0], '%Y-%m-%d')

                    print(str(subject)+" EVENT")
                    print(datetime.now().date())
                    if subject.lower().startswith("x") or subject.lower().endswith("x"):
                        printCal=True
                        print(stripEdgeX(subject))


                        startDateTime = event['start'].get('dateTime')
                        startDate= event['start'].get('date')

                        endDateTime = event['end'].get('dateTime')
                        endDate= event['end'].get('date')
                        
                        if startDateTime:
                            bawdy={'summary':stripEdgeX(subject),'description':event.get('description'),
                            'start':{'dateTime':event['start'].get('dateTime', event['start'].get('date'))},
                            'end':{'dateTime':event['end'].get('dateTime', event['start'].get('date'))}}
                        elif startDate:
                            bawdy={'summary':stripEdgeX(subject),'description':event.get('description'),
                            'start':{'date':event['start'].get('dateTime', event['start'].get('date'))},
                            'end':{'date':event['end'].get('dateTime', event['start'].get('date'))}}


                        updated_event = service.events().update(calendarId=calendar_list_entry['id'], eventId=event['id'], body=bawdy).execute()

                        updated_event = service.events().move(
                        calendarId=calendar_list_entry['id'], eventId=event['id'],
                        destination=finishedId).execute()
                    elif (not startDateString[1]) and evDay.date()<datetime.now().date():
                        print(str(subject)+" THIS ONE IS TO BE MOVED")
                        bawdy={'summary':subject,'description':event.get('description'),'start':{'date':str(datetime.now().date())},'end':{'date':str(datetime.now().date())}}
                        updated_event = service.events().update(calendarId=calendar_list_entry['id'], eventId=event['id'], body=bawdy).execute()
                    
                if printCal:
                    er = service.events().list(calendarId=calendar_list_entry['id'],
                     singleEvents=True,orderBy='startTime').execute()
                    ev = er.get('items', [])
                    calendars[calendar_list_entry['summary']]=ev
                    
            page_token = calendar_list.get('nextPageToken')

        
        er = service.events().list(calendarId=finishedId,
                singleEvents=True,orderBy='startTime').execute()
        ev = er.get('items', [])
        calendars[finishedFileName]=ev
        finishedRows=ev  

        if len(calendars)>0:
            calPrinter(finishedFileName,finishedRows)
        for key in calendars.keys():
            calPrinter(key,calendars.get(key))
        if not page_token:
            break

def writeToFile(filename,rows):
    with open("backups"+os.path.sep+datetime.now().strftime("%m%d%Y%H%M%S")+" "+filename+'.csv', 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerows(rows)
    

def eventToRow(event):
    startDateTime = event['start'].get('dateTime')
    startDate= event['start'].get('date')

    endDateTime = event['end'].get('dateTime')
    endDate= event['end'].get('date')
    
    subject=event['summary']
    sDate=''
    sTime=''
    eDate=''
    eTime=''
    description=''

    if startDateTime:
        sDate=startDateTime[0:startDateTime.rfind("T")]
        sTime=startDateTime[startDateTime.find("T")+1:startDateTime.rfind("-")]
        eDate=endDateTime[0:endDateTime.rfind("T")]
        eTime=endDateTime[endDateTime.find("T")+1:endDateTime.rfind("-")]
        allDay=False
    elif startDate:
        sDate=startDate
        eDate=endDate
        allDay=True
    description=event.get('description')
    
    return [subject,sDate,eDate,sTime,eTime,allDay,description]
def calPrinter(calName,events):
    totRows=[]
    totRows.append(["Subject","Start Date","End Date","Start Time","End Time","All Day Event ","Description"])
    for event in events:
        totRows.append(eventToRow(event))
    writeToFile(calName,totRows)

def getStartDate(event):
    startDateTime = event['start'].get('dateTime')
    startDate= event['start'].get('date')
    sDate=''

    if startDateTime:
        sDate=startDateTime[0:startDateTime.rfind("T")]
        allDay=True
    elif startDate:
        sDate=startDate
        allDay=False
    return [sDate,allDay]

def stripEdgeX(title):
    finalTitle=title
    if title.lower().startswith('x'):
        finalTitle=finalTitle[1:]
    if title.lower().endswith('x'):
        finalTitle=finalTitle[:-1]
    return finalTitle
    

if __name__ == '__main__':
    main()
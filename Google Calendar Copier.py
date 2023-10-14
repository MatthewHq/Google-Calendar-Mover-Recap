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
import json
import colorFinder


import sys

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

calendarCache = {}


def main():

    checkJsonOptionFile()
    transferCalendarList = getJSONFile("calendars.json")
    print(transferCalendarList)

    service = iniService()

    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    page_token = None
    colorBank = getColorBank(service)
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        dateBank = getDateBank(30, 90)
        calendarsBySummary = {}

        # ini calendarsBySummary
        for calendar_list_entry in calendar_list['items']:
            calendarsBySummary[calendar_list_entry["summary"]
                               ] = calendar_list_entry

        print(calendarsBySummary.keys())

        for mapping in transferCalendarList["mappings"]:
            for source in mapping["sources"]:

                # check if json object has entry for individual mapping
                if not transferCalendarList["eventMaps"].get(mapping["target"]):
                    transferCalendarList["eventMaps"][mapping["target"]] = {
                        "sourceToTarget": {},
                        "targetToSource": {}
                    }

                # iterate through every event in the indiv mapping group sources
                if source in calendarsBySummary:
                    calendar_list_entry = calendarsBySummary[source]
                    events_result = getCalendarCached(
                    calendar_list_entry["id"], dateBank, service)
                    currentCalendarColorId = calendar_list_entry.get('colorId')
                    if currentCalendarColorId:
                        translatedColorId = colorBank['event'][colorFinder.find_closest_color(
                            colorBank['calendar'][currentCalendarColorId], list(colorBank['event'].keys()))]
                    events = events_result.get('items', [])
                    for event in events:
                        currentMappingTarget = transferCalendarList['eventMaps'][mapping["target"]]
                        if not currentMappingTarget['sourceToTarget'].get(event['id']):
                            targetCalendarId = calendarsBySummary[mapping['target']]['id']
                            newEv = stripEvent(event)
                            print(newEv,targetCalendarId)
                            if translatedColorId:
                                newEv['colorId'] = translatedColorId
                            created_event = service.events().insert(calendarId=targetCalendarId,
                                                                    body=newEv).execute()

                            
                            currentMappingTarget['sourceToTarget'][event['id']] = {
                                'etag': event['etag'], 'summary': event['summary'], 'targetId': created_event['id']}
                            currentMappingTarget['targetToSource'][created_event['id']] = {
                                'summary': event['summary'], 'sourceEvId': event['id'], 'sourceCalId': calendar_list_entry['id']}
                            print("~~~~~CREATE TRIGGERED ON " +
                                  event['summary'])
                            
                        elif currentMappingTarget['sourceToTarget'][event['id']]['etag'] != event['etag']:
                            targetCalendarId = calendarsBySummary[mapping['target']]['id']

                            pairInfo = transferCalendarList['eventMaps'][mapping["target"]
                                                                         ]['sourceToTarget'][event['id']]
                            newEv=stripEvent(event)
                            print(event,targetCalendarId)
                            if translatedColorId:
                                newEv['colorId']=translatedColorId
                            updated_event = service.events().update(
                                calendarId=targetCalendarId, eventId=pairInfo['targetId'], body=newEv).execute()

                            currentMappingTarget['sourceToTarget'][event['id']] = {
                                'etag': event['etag'], 'summary': event['summary'], 'targetId': updated_event['id']}
                            currentMappingTarget['targetToSource'][updated_event['id']] = {
                                'summary': event['summary'], 'sourceEvId': event['id'], 'sourceCalId': calendar_list_entry['id']}

                            print("~~~~~~~~~UPDATE TRIGGERED ON" +
                                  event['summary'])
                            # needs update?
                        # print(event['summary'])
                        # print(event )
                        # print("\n~~~~")
                        if event['summary'] == 'TESTED123123123':
                            testSaved = event
            target = mapping["target"]
            if target in calendarsBySummary:
                calendar_list_entry = calendarsBySummary[target]
                events_result = getCalendarCached(
                    calendar_list_entry["id"], dateBank, service)
                events = events_result.get('items', [])

                # for every event in the target calendar
                for event in events:
                    t2s = transferCalendarList['eventMaps'][target]['targetToSource'][event['id']]
                    sEventId = t2s['sourceEvId']
                    sCalendarId = t2s['sourceCalId']
                    sourceCal = getCalendarCached(
                        sCalendarId, dateBank, service)
                    sourceEvents = sourceCal.get('items', [])

                    exists = False
                    for sEv in sourceEvents:
                        if sEventId == sEv['id']:
                            exists = True

                    if not exists:
                        print("DELETION TRIGGERED")
                        # transferCalendarList['eventMaps'][target]['sourceToTarget'].pop()
                        
                        service.events().delete(calendarId=calendar_list_entry["id"], eventId=event['id']).execute()
                        transferCalendarList['eventMaps'][target]['targetToSource'].pop(event['id'])
                        transferCalendarList['eventMaps'][target]['sourceToTarget'].pop(sEventId)
                        # THEN DELETE IT FROM TARGET
                        # DELETE ENTRIES FROM JSON
                        pass
        # print(testSaved)
        fakeEventTest = {'kind': 'calendar#event', 'status': 'confirmed', 'updated': '2023-10-07T18:02:23.456Z', 'summary': 'TESTED123123123', 'colorId': '5', 'creator': {'email': 'm4tthq@gmail.com', 'self': True}, 'organizer': {
            'email': 'm4tthq@gmail.com', 'self': True}, 'start': {'date': '2023-10-05'}, 'end': {'date': '2023-10-06'}, 'transparency': 'transparent', 'sequence': 0, 'reminders': {'useDefault': False}, 'eventType': 'default'}
        

        page_token = calendar_list.get('nextPageToken')

        # er = service.events().list(calendarId=finishedId,
        #         singleEvents=True,orderBy='startTime').execute()
        # ev = er.get('items', [])
        # calendars[finishedFileName]=ev
        # finishedRows=ev
        saveJsonObject("calendars.json", transferCalendarList)
        if not page_token:
            break

def getColorBank(service):
    colors = service.colors().get().execute()
    colorBank={"calendar":{},'event':{}}
    for id in colors['calendar']:
        palette= colors['calendar'][id]
        background=palette['background']
        colorBank['calendar'][id]=background
    for id in colors['event']:
        palette=colors['event'][id]
        background=palette['background']
        colorBank['event'][background]=id
    return colorBank

def stripEvent(originalEvent):
    stripList = ["etag", 'id', 'htmlLink', 'iCalUID','recurringEventId']
    event = originalEvent.copy()
    for key in stripList:
        if key in event:
            event.pop(key)

    return event


def getCalendarCached(id, dateBank, service):
    if id in calendarCache.keys():
        print("FROM CACHE")
        return calendarCache[id]
    else:
        events_result = service.events().list(calendarId=id, maxResults=2499,
                                              timeMax=dateBank["tomorrow"], timeMin=dateBank["pastDaysTime"], singleEvents=True, orderBy='startTime').execute()
        calendarCache[id] = events_result
        print("FROM API")
        return events_result


def getJSONFile(filename):
    # Read JSON data from the file
    with open(filename, 'r') as json_file:
        # Load JSON data into a Python object (dictionary in this case)
        data = json.load(json_file)
    return data


def saveJsonObject(filename, data):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def checkJsonOptionFile():
    # Specify the file path
    file_path = "calendars.json"
    # Check if the file exists
    if not os.path.exists(file_path):
        # If the file doesn't exist, create an empty JSON object
        data = {}
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file)
        print(f"File '{file_path}' created with empty JSON content.")
    else:
        print(f"File '{file_path}' already exists.")


def getDateBank(pastDays, futureDays):
    now = (datetime.utcnow()).isoformat() + 'Z'  # 'Z' indicates UTC time
    tomorrow = (datetime.utcnow()+timedelta(days=1)).isoformat() + \
        'Z'  # 'Z' indicates UTC time
    local_time = datetime.now(timezone.utc).astimezone()
    # daysRemove=timedelta(days=pastDays)
    # local_time_daysRemoved=local_time-daysRemove
    pastDaysTime = local_time-timedelta(days=pastDays)
    futureDaysTime = local_time+timedelta(days=futureDays)

    return {now: now,
            "tomorrow": tomorrow,
            "local_time": local_time,
            "pastDaysTime": pastDaysTime.isoformat(),
            "futureDaysTime": futureDaysTime.isoformat()}


def iniService():
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
    return service


def writeToFile(filename, rows):
    with open("backups"+os.path.sep+datetime.now().strftime("%m%d%Y%H%M%S")+" "+filename+'.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)


if __name__ == '__main__':
    main()

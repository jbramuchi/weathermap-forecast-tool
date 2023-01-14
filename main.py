# GAMEPLAN
# - use Promise.all() to make all api calls in paralleld
#      * Import lookup table for long/lats for api calls (no looking up,
#        simply pulling all of the values to iterate thru, all 21,000 or so)
#      * Set array of identifier values using the lookup from above
#        for each api call
#      * Call promise.all on the open weather api call
#        with the correct formating that each call will follow
#      * Store responses in an array
#      * Perform one big write to gsheet with all of this information

from __future__ import print_function

import os.path
from turtle import clear

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import tkinter as _tkinter
import asyncio
import aiohttp
import os
import time
import json

########################################################
# Define Global Vars

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
latitudes = []
longitudes = []
zipcodes = []
branches = []
alerts = []
APIKEY = '' # Openweathermap API KEY
spreadsheetid = '' # id of the google spreadsheet where the data transformations are applied
readRange = '' # the google-spreadsheet-formatted range of a lookup table of zipcodes to latitude-by-longitude coordinates
writeRange = '' # the google-spreadsheet-formatted range of where the api data is written to 
alertRange = '' # the google-spreadsheet-formatted range of where the weather alerts are indicated within your spreadsheet
url = "https://api.openweathermap.org/data/2.5/forecast/daily?lat={}&lon={}&cnt=7&exclude=current,minutely,hourly,alerts&units=imperial&lang=en&appid="+APIKEY

########################################################

def get_tasks(session):
    tasks = []
    length = len(zipcodes)
    i = 0
    while i < length:
        tasks.append(session.get(url.format(latitudes[i], longitudes[i] ), ssl=False))
        #print(url.format(latitudes[i], longitudes[i] ))
        #print(i)
        i += 1
    return tasks

async def get_symbols():
    #print("inside get_symbols")
    results = []
    #connector = aiohttp.TCPConnector(force_close=True)
    async with aiohttp.ClientSession() as session:
        tasks = get_tasks(session)
        responses = await asyncio.gather(*tasks)
        for response in responses:
            results.append(await response.json())
        return results
            
####################################################
# Import information from gsheet into three arrays


def getGSheetValues(spreadsheet_id, readRange):
    """
        Args: 
            spreadsheet_id = the id of the spreadsheet pulled from the url of the exact tab the data is on
            range = the cell range of the tab
    """

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=readRange).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        # print('CustomerID:')
        for row in values:
            # Print columns C, which correspond to indices 0.
            #print(row)
            latitudes.append(row[2])
            longitudes.append(row[3])
            zipcodes.append(row[0])

            
            #print('%s' % (row[0]))
    except HttpError as err:
        print(err)
    return

##################################################

def writeToGSheet(spreadsheet_id, writeRange, value_input_option, gsheetBody):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    try:
        service = build('sheets', 'v4', credentials=creds)

        body = {
            'values': gsheetBody
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=writeRange,
            valueInputOption=value_input_option, body=body).execute()
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


##################################################
# sendEmails

def sendEmails(spreadsheet_id, writeRange):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=alertRange).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        # print('CustomerID:')
        for row in values:
            # Print columns C, which correspond to indices 0.
            #print(row)
            branches.append(row[0])
            alerts.append(row[1])
            

    except HttpError as err:
        print(err)

    
    return


##################################################


def main():
    #Retrieve Lat/Long/Zipcode Values
    print("Accessing Google Spreadsheet: reading data.")
    getGSheetValues(spreadsheetid, readRange)
    print("Zipcodes and Coordinates retrieved.\n\n")

    #Make Preparations then invoke async API calls
    print("Starting asyncio loop:")
    start = time.time()
    results = asyncio.run(get_symbols())
    end = time.time()
    print("Retrieved {} Results in {}.\n\n".format((len(results)), (end-start)))
    

    #Write parsed JSON into GSheet
    print("Compiling API Data.")
    gsheetBody = []
    zipIndex = 0
    rowAppendage = ["Zip Codes",results[5]['list'][0]['dt'], results[5]['list'][1]['dt'], results[5]['list'][2]['dt'],
                                results[5]['list'][3]['dt'], results[5]['list'][4]['dt'], results[5]['list'][5]['dt'],
                                results[5]['list'][6]['dt']]
    gsheetBody.append(rowAppendage)
    
    for result in results:
        try:
            monPrecip = result['list'][0]['rain'] 
        except KeyError:
            monPrecip = '0'
        try:
            tuesPrecip = result['list'][1]['rain'] 
        except KeyError:
            tuesPrecip = '0'
        try:
            wedPrecip = result['list'][2]['rain'] 
        except KeyError:
            wedPrecip = '0'
        try:
            thursPrecip = result['list'][3]['rain'] 
        except KeyError:
            thursPrecip = '0'
        try:
            friPrecip = result['list'][4]['rain'] 
        except KeyError:
            friPrecip = '0'
        try:
            satPrecip = result['list'][5]['rain'] 
        except KeyError:
            satPrecip = '0'  
        try:
            sunPrecip = result['list'][6]['rain'] 
        except KeyError:
            sunPrecip = '0'  

        rowAppendage = [zipcodes[zipIndex], monPrecip, tuesPrecip, wedPrecip, thursPrecip, friPrecip,
                        satPrecip, sunPrecip]
        gsheetBody.append(rowAppendage)
        zipIndex += 1

    print("Accessing Google Spreadsheet: writing data.")

    print("gsheetBody: {}".format(gsheetBody[0]))
    start = time.time()
    writeToGSheet(spreadsheetid, writeRange, "USER_ENTERED", gsheetBody)
    end = time.time()
    print("Wrote to GSheet in {} seconds.\n".format(end-start))

    print("Sending emails out")
    start = time.time()
    # here
    end = time.time()
    print("Wrote to GSheet in {} seconds.\n".format(end-start))

if '__main__':
    main()

import grequests as grq
import pandas as pd
import requests as rq
from requests.exceptions import HTTPError
import random as rd
import time
from plotly import graph_objects as go
from plotly.subplots import make_subplots

import warnings
warnings.filterwarnings('ignore')

import environment
itemsDataLocation = environment.itemsDataLocation


#General REST request function, allows easier retries.
def restRequest(uRIList, maxTries = 50, currentTries = 0, multiThread = False):
    if currentTries == maxTries:
        raise Exception("Max retries reached.")
    
    if multiThread == True:
        try:
            response = (grq.get(u) for u in uRIList)
            jsonOut = []
            afterResponses = grq.map(response)
            for res in afterResponses:
                res.raise_for_status
                jsonOut.append(res.json())

        except HTTPError as http_err:
            currentTries = currentTries + 1
            time.sleep(rd.random()*10)
            print(f'http error is {http_err}')
            return restRequest(uRIList, maxTries = maxTries, currentTries = currentTries, multiThread= True)
        except Exception as err:
            currentTries = currentTries + 1
            time.sleep(rd.random()*10)
            print(f'current error {err}')
            return restRequest(uRIList, maxTries = maxTries, currentTries = currentTries, multiThread= True)

    else:
        uRI = uRIList
        try:
            response = rq.get(uRI)
            response.raise_for_status()

            jsonOut = response.json()

        except HTTPError as http_err:
            currentTries = currentTries + 1
            time.sleep(rd.random()*10)
            print(f'http error is {http_err}')
            return restRequest(uRIList, maxTries = maxTries, currentTries = currentTries, multiThread= False)
        except Exception as err:
            currentTries = currentTries + 1
            time.sleep(rd.random()*10)
            print(f'current error {err}')
            return restRequest(uRIList, maxTries = maxTries, currentTries = currentTries, multiThread= False)


    if jsonOut is None:
        jsonOut = []
        for res in afterResponses:
            jsonOut.append(res.json())
    
    return jsonOut

#Returns servers sorted by data center
def getServerList(keys):

    try:
            uRI = "https://xivapi.com/servers/dc"
            jsonOut = restRequest(uRIList=uRI, maxTries= 10, multiThread=False)

    except: return

    if keys == True:
        datacenters = []
        for x in jsonOut.keys():
            datacenters.append(x)

        return datacenters
    
    return jsonOut

#Gets items from data directory specified in environment file
def getDataFrameCsv(csvLoc):

    return pd.read_csv(csvLoc) 

#Uses xivapi to search for an item by name
def getItemOnline(itemName):
    try:

        uRI = "https://xivapi.com/search?string=" + itemName
        jsonOut = restRequest(uRI, maxTries= 10, multiThread=False)

    except: return

    if len(jsonOut['Results']) > 2: return

    return jsonOut['Results']

#Uses local file to get file data
def getItem(itemName):

    item = allItems.loc[allItems['Name'] == itemName]
    theItemObject = {'itemName': item['Name'].item(), 'itemID': item['ID'].item(), 'amountNeeded': 1}

    return theItemObject

#Uses xivapi to grab all info on an item, must be passed the ID.
def getItemByID(itemID):
    try:

        uRI = "https://xivapi.com/Item/" + str(itemID)
        jsonOut = restRequest(uRI, maxTries= 10, multiThread=False)
        
    except: return

    return jsonOut

#Uses xivapi to get the recipe for an item, recursively checks for raw materials of crafted mats if rawMatsOnly is True
def getRecipe(recipeID, numNeeded = 1, rawMatsOnly = True):
    try:

        uRI = "https://xivapi.com/Recipe/" + str(recipeID)
        jsonOut = restRequest(uRI, maxTries= 10, multiThread=False)
        
    except: return

    itemList = []
    i = 0
    while jsonOut['AmountIngredient' + str(i)] > 0:
        if jsonOut['ItemIngredient' + str(i)]['CanBeHq'] == 1 and rawMatsOnly == True:
            rowRecipeID = getItemByID(jsonOut['ItemIngredient' + str(i)]['ID'])['Recipes'][0]['ID']
            extraRows = getRecipe(rowRecipeID, jsonOut['AmountIngredient' + str(i)] / jsonOut['AmountResult'])
            for xRow in extraRows:
                if not any(item['itemName'] == xRow['itemName'] for item in itemList):
                    itemList.append(xRow)
                
                else: 
                    for j in range(0, len(itemList)):
                        if itemList[j]['itemName'] == xRow['itemName']: itemList[j]['amountNeeded'] = itemList[j]['amountNeeded'] + xRow['amountNeeded']
        else:
            itemRow = {'itemName' : jsonOut['ItemIngredient' + str(i)]['Name'], 'itemID' : jsonOut['ItemIngredient' + str(i)]['ID'], 'amountNeeded' : (jsonOut['AmountIngredient' + str(i)] * numNeeded), 'numProduced' : jsonOut['AmountResult']}
            itemList.append(itemRow)
        i = i + 1

    if jsonOut['AmountIngredient8'] > 0:
        if not any(item['itemName'] == jsonOut['ItemIngredient8']['Name'] for item in itemList):
            itemRow = {'itemName' : jsonOut['ItemIngredient8']['Name'], 'itemID' : jsonOut['ItemIngredient8']['ID'], 'amountNeeded' : (jsonOut['AmountIngredient8'] * numNeeded), 'numProduced' : jsonOut['AmountResult']}
            itemList.append(itemRow)
        else: 
            for j in range(0, len(itemList)):
                if itemList[j]['itemName'] == jsonOut['ItemIngredient8']['Name']: itemList[j]['amountNeeded'] = itemList[j]['amountNeeded'] + jsonOut['AmountIngredient8']

    if jsonOut['AmountIngredient9'] > 0:
        if not any(item['itemName'] == jsonOut['ItemIngredient9']['Name'] for item in itemList):
            itemRow = {'itemName' : jsonOut['ItemIngredient9']['Name'], 'itemID' : jsonOut['ItemIngredient9']['ID'], 'amountNeeded' : (jsonOut['AmountIngredient9'] * numNeeded), 'numProduced' : jsonOut['AmountResult']}
            itemList.append(itemRow)
        else: 
            for j in range(0, len(itemList)):
                if itemList[j]['itemName'] == jsonOut['ItemIngredient9']['Name']: itemList[j]['amountNeeded'] = itemList[j]['amountNeeded'] + jsonOut['AmountIngredient9']

    return itemList

#Uses universalis to get sales history of all items in a recipe or individual items if not passed a list
def getSalesHistory(recipe, weeksToGet, datacenter, currentTries = 0, maxToGet = 9001, hqOnly = False, maxTries = 1):
    
    if currentTries == maxTries: raise Exception("Error getting sales history.")
    secondsForWeeks = int(weeksToGet * 604800)
    
    if type(recipe) is list:
        uRIList = []
        for num in recipe:
            uRIList.append("https://universalis.app/api/v2/history/" + str(datacenter) + "/" + str(num['itemID']) + "?entriesToReturn=" + str(maxToGet) + "&entriesWithin=" + str(secondsForWeeks))

        try:
            jsonOut = restRequest(uRIList, maxTries= 15, multiThread=True)
        except: 
            getSalesHistory(recipe, weeksToGet, datacenter, (currentTries + 1), maxToGet, hqOnly, maxTries)
        
        returnListed = []
        i = 0
        for item in jsonOut:
            for entry in item['entries']:
                if hqOnly == True and entry['hq'] == False and item['hqSaleVelocity'] > 0: continue
                thisRow = entry
                thisRow['itemName'] = recipe[i]['itemName']
                thisRow['amountNeeded'] = recipe[i]['amountNeeded']
                returnListed.append(thisRow)
            
            i = i + 1
    else:
        item = recipe['itemID']
        uRI = "https://universalis.app/api/v2/history/" + str(datacenter) + "/" + str(item) + "?entriesToReturn=" + str(maxToGet) + "&entriesWithin=" + str(secondsForWeeks)
    
        try:
            jsonOut = restRequest(uRI, maxTries=15, multiThread=False)

        except: getSalesHistory(recipe, weeksToGet, datacenter, (currentTries + 1), maxToGet, hqOnly, maxTries)
    
        returnListed = []
        for entry in jsonOut['entries']:
            if hqOnly == True and entry['hq'] == False: continue
            thisRow = entry
            thisRow['itemName'] = recipe['itemName']
            thisRow['amountNeeded'] = recipe['amountNeeded']

            returnListed.append(thisRow)

    return returnListed

#Older function used for formatting an item object. May not be needed anymore
def makeItemObject(item):
    theItemObject = {'itemName': item['Name'], 'itemID': item['ID'], 'amountNeeded': 1}
    return theItemObject

#Leverages Pandas library to take a DataFrame of sales history and slice it up into segments of time.
#Then finds the average value of item sales across those periods of time and returns a DataFrame.
#This DataFrame has one row for each segment of time.
def findMean(inputDF, craftedItemName ,weeksToShow, numOfSteps, sales = 0, numRecipeOutput = 1):

    totalSeconds = weeksToShow * 604800
    rightNow = time.time()
    secondsPerStep = totalSeconds / numOfSteps
    sellingPrice = []
    daySteps = (weeksToShow * 7) / numOfSteps
    skipMe = False

    if sales == 0:
        uniqueIngred = len(inputDF.groupby('itemName'))

    for i in range(0, numOfSteps):
        beginTime = rightNow - (i * secondsPerStep)
        endTime = beginTime - secondsPerStep
        timeSlicedDF = inputDF[(inputDF['timestamp'] < beginTime) & (inputDF['timestamp'] > endTime)]
        if len(timeSlicedDF) < 1: continue
        thisRow = {}
        if sales == 1:
            thisRow['pricePerUnit'] = timeSlicedDF.groupby('itemName')['pricePerUnit'].mean().astype('int')[0]
            thisRow['totalSold'] = timeSlicedDF.groupby('itemName')['quantity'].sum().astype('int')[0]
            thisRow['timeStamp'] = timeSlicedDF.groupby('itemName')['timestamp'].mean().astype('int')[0]
            timeSlicedDF['timestamp'] = timeSlicedDF.groupby('itemName')['timestamp'].mean().astype('int')[0]
            thisRow['timeStampDT'] = pd.to_datetime(timeSlicedDF['timestamp'], unit='s')
    
        else:
            if len(timeSlicedDF.groupby('itemName')) < uniqueIngred: skipMe = True
            timeSlicedDF['pricePerUnit'] = round(timeSlicedDF.groupby('itemName')['pricePerUnit'].transform('mean'))
            productSlicedDF = timeSlicedDF.drop_duplicates(subset='itemName')
            productSlicedDF['modifiedPrice'] = (productSlicedDF['pricePerUnit'] * productSlicedDF['amountNeeded']) / numRecipeOutput
            thisRow['pricePerUnit'] = productSlicedDF['modifiedPrice'].sum().astype('int')

        thisRow['day'] = (i * daySteps)
        thisRow['craftedItemName'] = craftedItemName
        if skipMe == False: sellingPrice.append(thisRow)

        skipMe = False
    sellingPriceDF = pd.DataFrame(sellingPrice)
    return sellingPriceDF

#Used to create a Dataframe that has the sales history of a crafted item.
def fetchSalesData(itemName, datacenter, hqOnly = True, numOfWeeks = 1):
    craftedItemData = getItemOnline(itemName)
    craftedItemObject = getItem(itemName)
    if len(craftedItemData) == 2:
        craftedSalesHistory = getSalesHistory(craftedItemObject, numOfWeeks, datacenter, maxToGet = 99999, hqOnly = hqOnly, maxTries=25)
        craftedItemHistoryDF = pd.DataFrame(data = craftedSalesHistory)
        craftedItemHistoryDF['isCrafted'] = 1
        recipe = getRecipe(craftedItemData[1]['ID'])
        craftedItemHistoryDF['numProduced'] = recipe[0]['numProduced']

    else:
        craftedSalesHistory = getSalesHistory(craftedItemObject, numOfWeeks, datacenter, maxToGet = 99999, hqOnly = False, maxTries=25)
        craftedItemHistoryDF = pd.DataFrame(data = craftedSalesHistory)
        craftedItemHistoryDF['isCrafted'] = 0
    return craftedItemHistoryDF


#Used to create a large DataFrame that contains all the sales of each of the materials used to craft the item
def fetchSalesDataRecipe(itemName, datacenter, numOfWeeks = 1, rawMatsOnly = True):
    craftedItemData = getItemOnline(itemName)

    recipeID = craftedItemData[1]['ID']

    if rawMatsOnly == True: 
        recipe = getRecipe(recipeID, 1)
        salesHistory = getSalesHistory(recipe, numOfWeeks, datacenter, maxToGet = 99999, maxTries=25)
    
    else: 
        recipe = getRecipe(recipeID, 1, rawMatsOnly= False)
        salesHistory = getSalesHistory(recipe, numOfWeeks, datacenter, maxToGet = 99999, hqOnly=True, maxTries=25)
    
    salesHistoryDF = pd.DataFrame(data = salesHistory)
    return salesHistoryDF

#Use universalis to get current sales data.
def fetchCurrentMarket(itemList, datacenter, hqOnly=True):

    itemIDList = []
    for x in itemList['itemName'].unique():
        itemIDList.append(getItem(x))
    if len(itemIDList) > 1:
        uRIList = []
        for l in itemIDList:
            uRI = "https://universalis.app/api/v2/" + str(datacenter) + "/" + str(l['itemID'])
            if hqOnly == True: uRI = uRI + "?hq=" + str(hqOnly)
            uRIList.append(uRI)

        try:
            jsonOut = restRequest(uRIList=uRIList, maxTries=15, multiThread= True)

        except: return

    else: 
        uRI = "https://universalis.app/api/v2/" + str(datacenter) + "/" + str(itemIDList[0]['itemID'])
        if hqOnly == True: uRI = uRI + "?hq=" + str(hqOnly)

        try:
            jsonOut = restRequest(uRIList=uRI, maxTries=15)

        except: return

    if type(jsonOut) is list:
        currentListings = []
        for number in jsonOut:
            thisItemName = allItems[allItems['ID'] == number['itemID']]['Name'].item()
            for x in number['listings']:
                x['itemName'] = thisItemName
                currentListings.append(x)
        return pd.DataFrame(data=currentListings)

    else:
        jsonOutDF = pd.DataFrame(jsonOut['listings'])
        jsonOutDF['itemName'] = itemIDList[0]['itemName']
        return jsonOutDF 

def findCurrentMatsPrice(itemID, datacenter, hqOnly):
    recipeID = getItemByID(itemID)['Recipes'][0]['ID']
    recipe = getRecipe(recipeID, rawMatsOnly= True)
    recipeDF = pd.DataFrame(recipe)

    currentMarketData = fetchCurrentMarket(recipeDF, datacenter, hqOnly=hqOnly)

    recipeModified = []
    for item in recipe:
        thisRow = item
        minPrice = currentMarketData[currentMarketData['itemName'] == item['itemName']]['pricePerUnit'].min()
        thisRow['modifiedPrice'] = minPrice * item['amountNeeded']
        thisRow['quantity'] = currentMarketData[currentMarketData['itemName'] == item['itemName']][currentMarketData['pricePerUnit'] == minPrice]['quantity'].item()
        thisRow['serverName'] = currentMarketData[currentMarketData['itemName'] == item['itemName']][currentMarketData['pricePerUnit'] == minPrice]['worldName'].item()
        recipeModified.append(thisRow)

    
    return

#Used to add a line to the displayed graph
def addLineToGraph(inputDF, inputFigure, showSales):
    name = inputDF['craftedItemName'][0]
    if showSales == False:
        inputFigure = inputFigure.add_trace(go.Scatter( x=-inputDF['day'], 
                                                        y=inputDF['pricePerUnit'], 
                                                        name=name,
                                                        mode="lines+markers"),
                                                        secondary_y=False)

    else:
        inputFigure = inputFigure.add_trace(go.Scatter( x=-inputDF['day'], 
                                                        y=inputDF['pricePerUnit'], 
                                                        name=name,
                                                        mode="lines+markers"),
                                                        secondary_y=True)
    
    return inputFigure

#Used to add bars for total sales to the displayed graph
def addBarToGraph(inputDF, inputFigure):
    name = inputDF['craftedItemName'][0]
    inputFigure = inputFigure.add_trace(go.Bar( x=-inputDF['day'],
                                                y=inputDF['totalSold'],
                                                name=name + " sales"),
                                                secondary_y=False)

    return inputFigure

#Function that primarily creates the plotly graph
def buildLineGraph(itemDFList, matDFListRaw, matsDFList, numOfHours, numOfWeeks, showMaterials = True, showSales = True):
    if showSales == True: fig = make_subplots(specs=[[{"secondary_y": True}]])
    else: fig=make_subplots()
    numOfSteps = int((168 / numOfHours) * numOfWeeks)
    for i in range(0,len(itemDFList)):
        thisListItem = findMean(itemDFList[i], itemDFList[i]['itemName'][0], numOfWeeks, numOfSteps, sales = 1)
        fig = addLineToGraph(thisListItem, fig, showSales=showSales)
        if itemDFList[i]['isCrafted'][0] == 1 and showMaterials == True:
            numOfRecipe = itemDFList[i]['numProduced'][0]
            thisList = findMean(matDFListRaw[i], str(itemDFList[i]['itemName'][0]) + " mats raw", numOfWeeks, numOfSteps, numRecipeOutput= numOfRecipe)
            fig = addLineToGraph(thisList, fig, showSales=showSales)
            thisList = findMean(matsDFList[i], str(itemDFList[i]['itemName'][0]) + " mats", numOfWeeks, numOfSteps, numRecipeOutput= numOfRecipe)
            fig = addLineToGraph(thisList, fig, showSales=showSales)

        if showSales == True: fig = addBarToGraph(thisListItem, fig)
    now = time.time()
    fig.update_layout(title = dict(text="Sales of an item"))
    fig.update_xaxes(title_text="Days from today.")
    if showSales == True:
        fig.update_yaxes(title_text="Price in Gil", secondary_y=True)
        fig.update_yaxes(title_text="Number sold", secondary_y=False)
        fig.update_layout(
            yaxis=dict(side='right'),
            yaxis2=dict(side='left')
        )
    else: fig.update_yaxes(title_text="Price in Gil", secondary_y=False)
    return fig

#Function for creating the table listing specific information about the item
def updateInfoTable(listOfItems, totalResults):
    
    theChildren = []
    i = 0
    for x in listOfItems:
        thisTimestamp = pd.to_datetime(x['timestamp'][len(x) - 1], unit='s')
        thisHour = str(thisTimestamp.hour)
        while len(thisHour) < 2:
            thisHour = "0" + thisHour
        thisMinute = str(thisTimestamp.minute)
        while len(thisMinute) < 2:
            thisMinute = "0" + thisMinute
        formattedTimestamp = str(thisTimestamp.date()) + "  " + thisHour + ":" + thisMinute
        thisRow = {"Item Name" : x['itemName'][0],"Last Sell Price" : x['pricePerUnit'][0], "Oldest Transaction Found" :formattedTimestamp, "Total Units Sold" : totalResults[i]}
        theChildren.append(thisRow)
        i = i + 1
    
    theChildrenDF = pd.DataFrame(theChildren)
    return theChildrenDF.to_dict('records')

#Function used to output the recipe of the item as well as the most recent sales price of a given item
def updateRecipeTable(matDFList, itemList):

    theChildren = []
    j = 0
    thisRow = {"Material" : itemList[j],"Number needed to craft" : 0, 
               "Last Sell Price" : 0, "Oldest Transaction Found" : 0, "Latest Transaction Found" : 0}
    theChildren.append(thisRow)
    for matDF in matDFList:

        beginningGroupIndex = []
        endGroupIndex = []
        eachMatName = []
        for i in matDF.groupby('itemName').groups.keys():
            eachMatName.append(i)
        
        for i in eachMatName:
            firstIndex = matDF.groupby('itemName').groups[i][0]
            lastIndex = matDF.groupby('itemName').groups[i][0] + len(matDF.groupby('itemName').groups[i]) - 1
            beginningGroupIndex.append(firstIndex)
            endGroupIndex.append(lastIndex)
        
        for i in range(0, len(beginningGroupIndex)):
            thisOldTimestamp = pd.to_datetime(matDF['timestamp'][endGroupIndex[i]], unit='s')
            oldHour = str(thisOldTimestamp.hour)
            while(len(oldHour) < 2):
                oldHour = "0" + oldHour

            oldMinute = str(thisOldTimestamp.minute)
            while(len(oldMinute) < 2):
                oldMinute = "0" + oldMinute
            formattedOldTimestamp = str(thisOldTimestamp.date()) + "  " + oldHour + ":" + oldMinute

            thisNewTimestamp = pd.to_datetime(matDF['timestamp'][beginningGroupIndex[i]], unit='s')
            newHour = str(thisNewTimestamp.hour)
            while(len(newHour) < 2):
                newHour = "0" + newHour

            newMinute = str(thisNewTimestamp.minute)
            while(len(newMinute) < 2):
                newMinute = "0" + newMinute
            formattedNewTimestamp = str(thisNewTimestamp.date()) + "  " + newHour + ":" + newMinute
            thisRow = {"Material" : matDF['itemName'][beginningGroupIndex[i]],"Number needed to craft" : round(matDF['amountNeeded'][beginningGroupIndex[i]], ndigits=2), 
                       "Last Sell Price" : matDF['pricePerUnit'][beginningGroupIndex[i]], "Oldest Transaction Found" :formattedOldTimestamp, "Latest Transaction Found" : formattedNewTimestamp}
            theChildren.append(thisRow)
            
        j = j + 1
        if len(matDFList) > j:
                thisRow = {"Material" : itemList[j],"Number needed to craft" : 0, 
                           "Last Sell Price" : 0, "Oldest Transaction Found" : 0, "Latest Transaction Found" : 0}
                theChildren.append(thisRow)

    theChildrenDF = pd.DataFrame(theChildren)
    return theChildrenDF.to_dict('records')

#TODO Implement current market data prices
def updatePriceTable(itemDFList, matDFList, datacenter, hqOnly = False, worldOnly = False):
    
    itemPricesList = []
    if worldOnly == False:
        for df in itemDFList:
            currentMark = fetchCurrentMarket(df, datacenter, hqOnly=hqOnly)
            sortedDF = currentMark.sort_values('pricePerUnit', ascending=False)
            groupedAndSorted = sortedDF.groupby(['itemName', 'worldName'])
            #thisRow = {"Item Name" : df['itemName'][0], "Last time viewed" : 0, "Server of listing" : "", "hq" : False, 'Current lowest sale price' : 0}
            #itemPricesList.append(thisRow)
            for i in range(0, len(groupedAndSorted.head(1))):
                thisRow = {"Item Name" : currentMark['itemName'][groupedAndSorted.head(1).index[i]], 
                "Last time viewed" : pd.to_datetime(currentMark['lastReviewTime'][groupedAndSorted.head(1).index[i]], unit="s"), 
                "Server of listing" : currentMark['worldName'][groupedAndSorted.head(1).index[i]], 
                "hq" : currentMark['hq'][groupedAndSorted.head(1).index[i]],
                "Current lowest sale price" : groupedAndSorted['pricePerUnit'].min()[i]}
                itemPricesList.append(thisRow)

        for df in matDFList:
            currentMark = fetchCurrentMarket(df, datacenter, hqOnly=False)
            sortedDF = currentMark.sort_values('pricePerUnit', ascending=False)
            groupedAndSorted = sortedDF.groupby(['itemName', 'worldName'])
            #thisRow = {"Item Name" : df['itemName'][0], "Last time viewed" : 0, "Server of listing" : "", "hq" : False}
            #itemPricesList.append(thisRow)
            for i in range(0, len(groupedAndSorted.head(1))):
                thisRow = {"Item Name" : currentMark['itemName'][groupedAndSorted.head(1).index[i]], 
                "Last time viewed" : pd.to_datetime(currentMark['lastReviewTime'][groupedAndSorted.head(1).index[i]], unit="s"), 
                "Server of listing" : currentMark['worldName'][groupedAndSorted.head(1).index[i]], 
                "hq" : currentMark['hq'][groupedAndSorted.head(1).index[i]],
                "Current lowest sale price" : groupedAndSorted['pricePerUnit'].min()[i]}
                itemPricesList.append(thisRow)

    else:
        for df in itemDFList:
            currentMark = fetchCurrentMarket(df, datacenter, hqOnly=hqOnly)
            sortedDF = currentMark.sort_values('pricePerUnit', ascending=False)
            groupedAndSorted = sortedDF.groupby(['itemName'])
            thisRow = {"Item Name" : df['itemName'][0], "Last time viewed" : 0, "Server of listing" : "", "hq" : False, 'Current lowest sale price' : 0}
            itemPricesList.append(thisRow)
            for i in range(0, len(groupedAndSorted.head(1))):
                thisRow = {"Item Name" : currentMark['itemName'][groupedAndSorted.head(1).index[i]], 
                "Last time viewed" : pd.to_datetime(currentMark['lastReviewTime'][groupedAndSorted.head(1).index[i]], unit="s"), 
                "Server of listing" : datacenter, 
                "hq" : currentMark['hq'][groupedAndSorted.head(1).index[i]],
                "Current lowest sale price" : groupedAndSorted['pricePerUnit'].min()[i]}
                itemPricesList.append(thisRow)

        for df in matDFList:
            currentMark = fetchCurrentMarket(df, datacenter, hqOnly=False)
            sortedDF = currentMark.sort_values('pricePerUnit', ascending=False)
            groupedAndSorted = sortedDF.groupby(['itemName'])
            #thisRow = {"Item Name" : df['itemName'][0], "Last time viewed" : 0, "Server of listing" : "", "hq" : False}
            #itemPricesList.append(thisRow)
            for i in range(0, len(groupedAndSorted.head(1))):
                thisRow = {"Item Name" : currentMark['itemName'][groupedAndSorted.head(1).index[i]], 
                "Last time viewed" : pd.to_datetime(currentMark['lastReviewTime'][groupedAndSorted.head(1).index[i]], unit="s"), 
                "Server of listing" : datacenter, 
                "hq" : currentMark['hq'][groupedAndSorted.head(1).index[i]],
                "Current lowest sale price" : groupedAndSorted['pricePerUnit'].min()[i]}
                itemPricesList.append(thisRow)


    itemPricesDF = pd.DataFrame(itemPricesList)
    itemPricesDF = itemPricesDF.sort_values(['Item Name', 'Current lowest sale price'])
    return itemPricesDF.to_dict('records')

allItems = getDataFrameCsv(itemsDataLocation)
allItemNames = allItems['Name']

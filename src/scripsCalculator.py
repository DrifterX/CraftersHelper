import functions as f
import environment

rarefiedItems = f.getDataFrameCsv(environment.rarefiedItems)
scripValues = f.getDataFrameCsv(environment.scripValues)
scripItemCosts = f.getDataFrameCsv(environment.scriptItemCosts)

materia = scripItemCosts[scripItemCosts['statValue'] > 0]

materiaMarketData = f.fetchCurrentMarket(materia, "Aether", False)

rarefiedItems = rarefiedItems.rename(columns={"Name" : "itemName"})

rarefiedRecipesRaw = []
rarefiedRecipes = []

allRarefiedItems = False

if allRarefiedItems is True:
    for item in rarefiedItems['itemName']:
        rarefiedRecipesRaw.append(f.fetchSalesDataRecipe(item, "Aether", numOfWeeks=(1/7)))
        rarefiedRecipes.append(f.fetchSalesDataRecipe(item, "aether", numOfWeeks=(1/7), rawMatsOnly=False))


itemID = f.getItemByID(rarefiedItems['ID'][150])
recipeOfItem = f.getRecipe(itemID['Recipes'][0]['ID'])
recipeOfItemDF = f.pd.DataFrame(recipeOfItem)
salesHistory = f.getSalesHistory(recipeOfItem, (1/7), "Aether", maxToGet = 99999)
salesHistoryDF = f.pd.DataFrame(salesHistory)
currentCost = f.fetchCurrentMarket(recipeOfItemDF, "Aether", hqOnly = False)
theMean = f.findMean(salesHistoryDF, rarefiedItems['itemName'][150], weeksToShow= (1/7), numOfSteps=1)
scriptsReturned = scripValues[scripValues['iLevel'] < rarefiedItems['Level{Item}'][150]].max()[['return','type']]
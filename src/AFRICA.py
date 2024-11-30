#pip install geopandas shapely pandas numpy geopy requests

#Imports
from cmu_graphics import *
import geopandas as gpd
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from shapely.geometry import Polygon
import pandas as pd
import json
import requests
import random
import numpy as np
import os
from PIL import Image
###########################################################################################
# Json File Reading


with open('./src/geojson-maps.json', 'r') as f:
    json_data = json.load(f)

data = []
for feature in json_data["features"]:
    properties = feature["properties"]

    if properties.get("adm0_a3") == "SDS":  # I HATE SOUTH SUDAN
        properties["adm0_a3"] = "SSD"

    if "adm0_a3" in properties and "name" in properties and "pop_est" in properties and "subregion" in properties:
        data.append({
            "adm0_a3": properties["adm0_a3"],
            "name": properties["name"],
            "pop_est": properties["pop_est"],
            "subregion": properties["subregion"]
        })

df = pd.DataFrame(data)
exceptions = ["GRL", "ISL"]

filtered_df = df[(df["pop_est"] >= 2000000) & (df["adm0_a3"] != "SLE") & (df["adm0_a3"] != "BDI") & (df["adm0_a3"] != "LSO") & (df["adm0_a3"] != "GAM")]
filtered_df = filtered_df[filtered_df["subregion"].str.contains("Africa")]


# GeoPandas file reading
geojson_path = './src/datahub.geojson'
world_data = gpd.read_file(geojson_path)
filtered_world_data = world_data[world_data['ISO_A3'].isin(filtered_df['adm0_a3'])]
filtered_world_data = pd.merge(
    filtered_world_data,
    filtered_df,
    left_on='ISO_A3',
    right_on='adm0_a3',
    how='left'
)

###########################################################################################
# Start of ChatGPT generated/supported segment ######################################################
def geo_to_screen(lon, lat, width, height):
    # Africa bounding box (approximate)
    min_lon, max_lon = -20, 55    # Longitude range of Africa
    min_lat, max_lat = -35, 37    # Latitude range of Africa

    # Earth radius in meters
    R = 6378137  

    # Convert latitude and longitude to Mercator coordinates
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    mercator_x = R * lon_rad
    mercator_y = R * np.log(np.tan(np.pi / 4 + lat_rad / 2))

    # Convert bounding box lat/lon to Mercator coordinates
    min_lat_rad = np.radians(min_lat)
    max_lat_rad = np.radians(max_lat)
    min_mercator_x = R * np.radians(min_lon)
    max_mercator_x = R * np.radians(max_lon)
    min_mercator_y = R * np.log(np.tan(np.pi / 4 + min_lat_rad / 2))
    max_mercator_y = R * np.log(np.tan(np.pi / 4 + max_lat_rad / 2))

    # Compute scaling factors
    scale_x = width / (max_mercator_x - min_mercator_x)
    scale_y = height / (max_mercator_y - min_mercator_y)
    scale = min(scale_x, scale_y)  # Preserve aspect ratio

    # Map Mercator coordinates to screen space
    screen_x = int((mercator_x - min_mercator_x) * scale)
    screen_y = int((max_mercator_y - mercator_y) * scale)
    return screen_x, screen_y


def screen_to_geo(screen_x, screen_y, width, height):
    # Africa bounding box (approximate)
    min_lon, max_lon = -20, 55    # Longitude range of Africa
    min_lat, max_lat = -35, 37    # Latitude range of Africa

    # Earth radius in meters
    R = 6378137  

    # Convert bounding box lat/lon to Mercator coordinates
    min_lat_rad = np.radians(min_lat)
    max_lat_rad = np.radians(max_lat)
    min_mercator_x = R * np.radians(min_lon)
    max_mercator_x = R * np.radians(max_lon)
    min_mercator_y = R * np.log(np.tan(np.pi / 4 + min_lat_rad / 2))
    max_mercator_y = R * np.log(np.tan(np.pi / 4 + max_lat_rad / 2))

    # Compute scaling factors
    scale_x = width / (max_mercator_x - min_mercator_x)
    scale_y = height / (max_mercator_y - min_mercator_y)
    scale = min(scale_x, scale_y)  # Preserve aspect ratio

    # Convert screen space to Mercator coordinates
    mercator_x = screen_x / scale + min_mercator_x
    mercator_y = max_mercator_y - screen_y / scale

    # Convert Mercator coordinates back to latitude and longitude
    lat_rad = np.arctan(np.sinh(mercator_y / R))
    lon_rad = mercator_x / R
    lat = np.degrees(lat_rad)
    lon = np.degrees(lon_rad)

    return lon, lat


# End of ChatGPT generated/supported segment ########################################################
###########################################################################################

#Generate Shapes and Helper Functions
country_shapes = {}
for _, row in filtered_world_data.iterrows():
    country_name = row['name']
    geom = row['geometry']
    if isinstance(geom, MultiPolygon):
        polygons = list(geom.geoms)
    else:
        polygons = [geom]

    screen_polygons = []
    for polygon in polygons:
        simplified_polygon = polygon.simplify(0.1) ###IMPORTANT FOR FASTER LOADING SPEED: simplify the higher float the more simple
        screen_coords = [geo_to_screen(x, y, 1200, 550) for x, y in simplified_polygon.exterior.coords]        
        screen_polygons.append(screen_coords)
        country_shapes[country_name] = screen_polygons

def getPopulation(country_name):
    matching_country = filtered_world_data.loc[filtered_world_data['name'] == country_name]
    if not matching_country.empty:
        return int(matching_country['pop_est'].values[0])
    else:
        return None

def getCountryBox(name): #Iterates through countries' polygon coordinates, finds lowest and highest x and y respectively

    name_polygons = country_shapes[name]
    leftTop = [float('inf'), float('inf')]
    rightBot = [0, 0]

    left=leftTop[0]
    top=leftTop[1]
    right=rightBot[0]
    bot=rightBot[1]

    for polygon in name_polygons:
        for x, y in polygon:
            if x < leftTop[0]:
                leftTop[0] = x
            if y < leftTop[1]:
                leftTop[1] = y
            if x > rightBot[0]:
                rightBot[0] = x
            if y > rightBot[1]:
                rightBot[1] = y

    return (leftTop,rightBot)


def getSubregionBoxDict():
    subregion_boxes_dict={}
    subregions_list = filtered_world_data['subregion'].unique()

    for subregion in subregions_list:
        leftTop = [float('inf'), float('inf')]
        rightBot = [0, 0]

        for _, row in filtered_world_data[filtered_world_data['subregion'] == subregion].iterrows():
            country_name = row['name']
            if country_name in country_shapes.keys():

                name_polygons = country_shapes[country_name]

                for polygon in name_polygons:
                    for x, y in polygon:

                        if x < leftTop[0]:
                            leftTop[0] = x
                        if y < leftTop[1]:
                            leftTop[1] = y

                        if x > rightBot[0]:
                            rightBot[0] = x
                        if y > rightBot[1]:
                            rightBot[1] = y

        subregion_boxes_dict[subregion]=(leftTop,rightBot)
    return subregion_boxes_dict

subregion_boxes_dict=getSubregionBoxDict()

def getSubregionCountries():
    sub_countries_dict = {}
    for subregion in subregion_boxes_dict:
        subregion_countries_dict = {}
        countries_in_subregion = filtered_world_data[filtered_world_data['subregion'] == f'{subregion}']['name'].tolist()
        sub_countries_dict.update({str(subregion):countries_in_subregion})


    return sub_countries_dict
sub_countries_dict=getSubregionCountries()


def drawCountry(name):
    name_polygons = country_shapes[name]
    for polygon in name_polygons:
        L=[]
        for x, y in polygon:
            L += [x] + [y]

    drawPolygon(*L,fill='lightGray', border='Black', borderWidth=1,
             opacity=100, rotateAngle=0, dashes=False, visible=True)

def find_nearest_country(mouse_x, mouse_y, country_shapes, app):
    click_point = Point(mouse_x, mouse_y)

    nearest_country = None
    min_distance = 0

    if not app.countriesIn:
        return None

    for country_name in app.countriesIn:
        if country_name in country_shapes:
            for screen_polygon in country_shapes[country_name]:
                shapely_polygon = Polygon(screen_polygon)

                if shapely_polygon.contains(click_point):
                    return country_name

                distance = shapely_polygon.distance(click_point)
                if distance < min_distance:
                    min_distance = distance
                    nearest_country = country_name

    return nearest_country

country_codes = set(filtered_world_data['adm0_a3'])
def get_country_neighbors():
    response = requests.get("https://restcountries.com/v3.1/all?fields=cca3,borders")

    response.raise_for_status()
    
    countries_data = response.json()
    
    country_neighbors = {}
    
    for country in countries_data:
                
        country_code = country.get("cca3")
            
        neighbors = list(country.get("borders", [])) 
        
        
        if country_code in country_codes:
            country_neighbors[country_code] = neighbors

    return country_neighbors


country_neighbors = get_country_neighbors()
country_neighbors['MOZ']=country_neighbors.get('MOZ')+['MDG']
country_neighbors['MDG']=country_neighbors.get('MDG')+['MOZ']


country_code_to_name = {}
country_code_to_name[None]=None

country_name_to_code = {}
country_name_to_code[None]=None

for _, row in filtered_world_data.iterrows():
    country_code = row['adm0_a3']
    country_name = row['name']

    country_code_to_name[country_code]=country_name
    country_name_to_code[country_name]=country_code


territories={1: ['EGY', 'LBY', 'TUN', 'DZA', 'MAR', 'SDN'],  # North Africa
    2: ['CIV', 'BEN', 'TGO', 'GHA', 'SEN', 'NGA', 'GMB', 'MLI', 'BFA', 'NER', 'GNB', 'GHA', 'MRT'],  # West Africa
    3: ['CAM', 'GAB', 'CAF', 'COD','GAB', 'COG','CMR'],  # Central Africa
    4: ['ETH', 'KEN', 'TZA', 'SOM', 'UGA', 'RWA', 'ERI', 'SSD'],  # East Africa
    5: ['ZAF', 'BWA', 'NAM', 'ZWE', 'AGO'],  # Southern Africa
    6: ['MDG'],  # Island Countries
    7: ['MOZ', 'LBR', 'ZMB','MWI'],  # Central and Southern Regions
             }

region_colors = {
        1: "lightBlue",  # North Africa
        2: "lightGreen",  # West Africa
        3: "lightYellow",  # Central Africa
        4: "lightCoral",   # East Africa
        5: "lightPink",    # Southern Africa
        6: "black",  # Horn of Africa
        7: "red",  # Great Lakes Region
    }

def get_neighbors(country_code):
    return country_neighbors.get(country_code, [])

def get_center(name_polygons):
    x_coords = []
    y_coords = []
    
    for polygon in name_polygons:
        for x, y in polygon:
            x_coords.append(x)
            y_coords.append(y)
    
    mean_x = sum(x_coords) / len(x_coords) if x_coords else None
    mean_y = sum(y_coords) / len(y_coords) if y_coords else None
    
    return (mean_x, mean_y)


###########################################################################################
#Helper Functions for MVC
def rollDie():
    return random.randint(1, 6)

def rollBlitz(attacker, defender):

    attacker_rolls = sorted([rollDie() for dice in range(min(attacker, 3))], reverse=True)
    defender_rolls = sorted([rollDie() for dice in range(min(defender, 2))], reverse=True)

    attacker_wins = 0
    defender_wins = 0

    for i in range(len(defender_rolls)):
        if attacker_rolls[i] > defender_rolls[i]:
            attacker_wins += 1
        else:
            defender_wins += 1

    return attacker_wins, defender_wins

# Simulate rounds until attack is successful or attacker runs out of troops
def blitz(attacker, defender):
    attacker_losses = 0
    defender_losses = 0

    while attacker > 1 and defender > 0:  # basic requirements for attacking
        attacker_wins, defender_wins = rollBlitz(attacker, defender)

        #  defender loses one troop for each of the attacker's wins
        defender_losses += defender_wins
        attacker_losses += attacker_wins

        attacker -= attacker_losses
        defender -= defender_losses

        # print(f"Attacker: {attacker} troops remaining, Defender: {defender} troops remaining.")

    return attacker_losses, defender_losses

def monteCarloBlitzSimulation(attacker_initial, defender_initial, simulations=30000):
    attacker_wins_total = 0
    defender_wins_total = 0
    
    for _ in range(simulations):
        attacker_losses, defender_losses = blitz(attacker_initial, defender_initial)
        
        if defender_losses >= defender_initial:
            attacker_wins_total += 1
        else:
            defender_wins_total += 1

    attacker_win_prob = pythonRound(attacker_wins_total / simulations,3)
    defender_win_prob = pythonRound(defender_wins_total / simulations,3)
    
    return attacker_win_prob

def withinSubregion(app,mouseX,mouseY):
    app.subregionsIn=[]
    for subregion, (leftTop, rightBot) in subregion_boxes_dict.items():
            leftX, leftY = leftTop
            rightX, rightY = rightBot

            if leftX <= mouseX <= rightX and leftY <= mouseY <= rightY:
                app.subregionsIn.append(subregion)

    if len(app.subregionsIn) == 0:
        app.subregionsIn = []

def withinCountryinSub(app, mouseX, mouseY):
    app.countriesIn = []

    if len(app.subregionsIn) == 0:
        return app.countriesIn

    SubDict = getSubregionCountries()
    for subregion in app.subregionsIn:

        for country_name in SubDict[subregion]:
            if country_name in country_shapes.keys():

                leftTop, rightBot = getCountryBox(country_name)

                leftX, leftY = leftTop
                rightX, rightY = rightBot

                if leftX <= mouseX <= rightX and leftY <= mouseY <= rightY:
                    app.countriesIn.append(country_name)

def distance(x0,y0,x1,y1):
    return ((x1-x0)**2+(y1-y0)**2)**0.5

def get_random_half_countries(country_shapes):
    country_list = list(country_shapes.keys())
    random.shuffle(country_list) 

    half_count = len(country_list) // 2  
    return country_list[:half_count]


class Country:
    def __init__(self,name):
        self.name=name
        self.polygons=country_shapes[self.name]
        self.code=country_name_to_code[self.name]
        for player in app.players:
            if self.name in app.players.owned:
                self.owner=player
        
        

        

class Player:

    def __init__(self,startingCountries,color):
        self.active=False
        self.owned= {key: 1 for key in startingCountries}
        self.color=color
        self.phases=['Reinforcement','Attack','Fortification']
        self.phaseIndex=0
        self.gamePhase=self.phases[self.phaseIndex]
        self.name="Hans"
    
    def __repr__(self):
        return f"{self.name}"
    
    def drawArmies(self):
        for country in self.owned:
            pass
    
    def fortify(self):
        pass

    
        

class Game:
    def __init__(self,app):
        self.players=[]

    def start(self,app):
        
        starting1 = set(get_random_half_countries(country_shapes))

        starting2 = set(country_shapes.keys()).difference(starting1)

        app.player1 = Player(starting1,'lightgreen')

        app.player2 = Player(starting2,'lightblue')

        
        self.players = [app.player1, app.player2]
        app.players = [app.player1, app.player2]


    

###########################################################################################
#Actual App Functions for MVC

def onAppStart(app):
    app.background='mediumBlue'
    app.width=1200
    app.height=800
    app.UIy=550
    app.nearest_country='Congo'
    app.population=None
    app.subregionsIn=[]
    app.countriesIn = []
    app.neighbors= []
    app.tView=False
    app.probability=""
    app.message=''


    app.attackCountry=None
    app.defendCountry=None
    app.draggingLine = False
    app.lineStartLocation = None
    app.lineEndLocation = None

    app.fortStart=None
    app.fortStartCenter=None


    app.activeGame=Game(app)
    app.activeGame.start(app)


    app.activePlayer=app.players[0]





def drawCountries(app):
    for country_name in list(country_shapes.keys()):
        name_polygons = country_shapes[country_name]
        

        for polygon in name_polygons:
            L=[]
            for x, y in polygon:
                L += (x,y)


            if app.tView:

                region = None
                for region_id, countries in territories.items():
                    if country_name_to_code[country_name] in countries:
                        region = region_id
                        break
                
                # If a region is found, color the country accordingly
                if region is not None:
                    color = region_colors.get(region, "lightGray")
                else:
                    color = "lightGray"  # Default color if no region is found
                        


            else:       
                if (country_name_to_code[country_name] in app.neighbors 
                      and app.nearest_country in app.activePlayer.owned 
                      and country_name not in app.activePlayer.owned 
                      and app.activePlayer.phases[app.activePlayer.phaseIndex]=='Attack'):
                    color='red'
                else:
                    if country_name in app.player1.owned:
                        color=app.player1.color
                    
                    elif country_name in app.player2.owned:
                        color=app.player2.color
                
                
            
            drawPolygon(*L,fill=color, border='Black', borderWidth=1,
                opacity=100, rotateAngle=0, dashes=False, visible=True)

            if country_name==app.nearest_country:
                    drawPolygon(*L,fill='black', border=None, borderWidth=1,
                opacity=60, rotateAngle=0, dashes=False, visible=True)
        
        
    
    circleCenter=[]
    if not app.tView:
        for country_name in list(country_shapes.keys()):
            name_polygons = country_shapes[country_name]
            x,y=get_center(name_polygons)
            circleCenter.append((x,y))
            if country_name in app.player1.owned:
                drawCircle(x,y,10,fill="green")
                drawLabel(f'{app.player1.owned[country_name]}',x,y,size=18,bold=True)
            else:
                drawCircle(x,y,10,fill="aqua")
                drawLabel(f'{app.player2.owned[country_name]}',x,y,size=18,bold=True)

def onKeyPress(app,key):
    if key=='t':
        app.tView=not app.tView

    if key=='space':        
        if app.activePlayer.phaseIndex==2:
            app.activePlayer.phaseIndex=0
        else:
            app.activePlayer.phaseIndex+=1
        
def onMouseDrag(app, mouseX, mouseY):
     if mouseY<app.UIy:
        if app.activePlayer.phases[app.activePlayer.phaseIndex]=='Attack':
            app.draggingline = True
            app.lineEndLocation = (mouseX, mouseY)
            withinSubregion(app,mouseX,mouseY)
            withinCountryinSub(app,mouseX,mouseY)
            app.defendCountry = find_nearest_country(mouseX, mouseY, country_shapes, app)

        
        
def onMouseRelease(app, mouseX, mouseY):
    
    app.draggingline = False

    withinSubregion(app,mouseX,mouseY)
    withinCountryinSub(app,mouseX,mouseY)

    
    app.defendCountry = find_nearest_country(mouseX, mouseY, country_shapes, app)

    if country_name_to_code[app.defendCountry] not in get_neighbors(country_name_to_code[app.attackCountry]):        
        app.defendCountry=None 
        return None
    
    for player in app.activeGame.players:
            if app.defendCountry in player.owned:
                defendPlayer=player
                break
    

    if app.attackCountry in app.activePlayer.owned and app.defendCountry not in app.activePlayer.owned:
        app.probability=monteCarloBlitzSimulation(app.activePlayer.owned[app.attackCountry],defendPlayer.owned[app.defendCountry])
    else:
        app.probability='N/A'
        app.message='not valid attack'
    

def onMousePress(app,mouseX,mouseY):
    app.nearest_country = find_nearest_country(mouseX, mouseY, country_shapes, app)
    
    if mouseY<app.UIy:
        if app.activePlayer.phases[app.activePlayer.phaseIndex]=='Reinforcement':

            for player in app.activeGame.players:
                if app.nearest_country in player.owned:
                    player.owned[app.nearest_country]+=1

        elif app.activePlayer.phases[app.activePlayer.phaseIndex]=='Attack':
            app.lineStartLocation=mouseX,mouseY
            app.attackCountry=app.nearest_country
        
        elif app.activePlayer.phases[app.activePlayer.phaseIndex]=='Fortify':
            app.fortStart=app.nearest_country
            app.fortStartCenter=get_center(app.fortStart)




def redrawAll(app):
    
    drawCountries(app)

    drawPhaseUI(app)

    if app.activePlayer.phases[app.activePlayer.phaseIndex]=='Attack':
        drawAttack(app)

    drawUI(app)

def drawUI(app):
    # drawRect(0,app.UIy,app.width,app.height-app.UIy,fill='linen')

    drawImages(app)
    drawPlayers(app)

    drawRect(50,600,100,100,fill='gray') #Attack Button 

    
    drawLabel(f"Country: {country_name_to_code[app.nearest_country]}",650,600,size=25)
    drawLabel(f"Population: {app.population}",650,625,size=25)
    drawLabel(f"Neighbor(s): {app.neighbors}",650,650,size=25)
    drawLabel(f"In Countries: {app.countriesIn}",650,675,size=25)

def CMU_imaging(file_path):
    image=Image.open(file_path)
    imageWidth, imageHeight = image.size

    

    
    return CMUImage(image)

def drawPlayers(app):
    x=1100
    y=80
    for player in app.players:

        drawRect(x,y-50,200,100,fill='black',opacity=50,border=player.color)

        drawCircle(x,y,60,fill=player.color,border='black',borderWidth=3)
        
        drawLabel(f'{player.name}',x,y,size=25)
        y+=120

def drawImages(app):
    mapUI=CMU_imaging('Images/mapUI.png')
    drawImage(mapUI, -50, app.UIy-20)



def drawAttack(app):
    
    if app.lineStartLocation != None and app.lineEndLocation != None:
        drawLabel(f'Attacking Country: {app.attackCountry}',
                  800, 280, size=16, bold=True, fill=app.activePlayer.color)
        drawLabel(f'Defending Country: {app.defendCountry}',
                  800, 320, size=16, bold=True, fill=app.activePlayer.color)
        
        x0, y0 = app.lineStartLocation
        x1, y1 = app.lineEndLocation
        
        if distance(x0, y0,x1, y1)>=10 and app.defendCountry!=None:
            drawLine(x0, y0, x1, y1, fill='black', lineWidth=3, dashes=app.draggingline,arrowEnd=True)
        

def drawPhaseUI(app):
    drawRect(600,250,400,275,fill='black',opacity=30)
    drawLabel(f"Current Player: {app.activePlayer}",
          800, 360, size=16, bold=True, fill=app.activePlayer.color)
    drawLabel(f"Current Phase: {app.activePlayer.phases[app.activePlayer.phaseIndex]}",
          800, 400, size=16, bold=True, fill=app.activePlayer.color)
    drawLabel(f"Attacker win probability: {app.probability}",
          800, 440, size=16, bold=True, fill=app.activePlayer.color)
    drawLabel(f"{app.message}",
          800, 480, size=16, bold=True, fill='black')


def onMouseMove(app, mouseX, mouseY):
    if mouseY<app.UIy:
        withinSubregion(app,mouseX,mouseY)
        withinCountryinSub(app,mouseX,mouseY)
        app.nearest_country = find_nearest_country(mouseX, mouseY, country_shapes, app)
        app.population = getPopulation(app.nearest_country)
        app.neighbors=get_neighbors(country_name_to_code[app.nearest_country])

app.setMaxShapeCount(4000)

runApp()
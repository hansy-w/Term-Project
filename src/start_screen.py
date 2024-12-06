#pip install geopandas shapely pandas numpy geopy requests

#Imports
from cmu_graphics import *
import geopandas as gpd
from shapely.geometry import MultiPolygon, GeometryCollection
from shapely.geometry import Point
from shapely.geometry import Polygon
import pandas as pd
import json
import numpy as np
from PIL import Image
from AFRICA import *
#All sound files belong to their respective owners, accessible by the url
###########################################################################################
# Json File Reading
def getJsonData():
    with open('src/geojson-maps.json', 'r') as f:
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

    filtered_df = df[(df["pop_est"] >= 2000000) | (df["adm0_a3"].isin(exceptions))]

    # GeoPandas file reading
    geojson_path = 'src/datahub.geojson'
    world_data = gpd.read_file(geojson_path)
    filtered_world_data = world_data[world_data['ISO_A3'].isin(filtered_df['adm0_a3'])]
    filtered_world_data = pd.merge(
        filtered_world_data,
        filtered_df,
        left_on='ISO_A3',
        right_on='adm0_a3',
        how='left')
    
    return filtered_world_data

filtered_world_data=getJsonData()
###########################################################################################
# Start of ChatGPT generated/supported segment ######################################################
def geo_to_screen(lon, lat, width, height):
    R = 6378137  
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    mercator_x = R * lon_rad
    mercator_y = R * np.log(np.tan(np.pi / 4 + lat_rad / 2))

    screen_x = int((mercator_x + 20037508.34) * (width / 40075016.68))
    screen_y = int((20037508.34 - mercator_y) * (height / 40075016.68))
    return screen_x, screen_y

territories = {
    1: ['United States of America'],
    2: ['Mexico', 'Guatemala', 'Honduras', 'El Salvador', 'Nicaragua', 'Costa Rica', 'Panama','Jamaica', 'Haiti', 'Dominican Rep.', 'Cuba', 'Puerto Rico'],
    3: ['Colombia', 'Venezuela', 'Ecuador'],
    4: ['Brazil'],
    5: ['Argentina', 'Chile', 'Uruguay', 'Paraguay'],
    6: ['Peru', 'Bolivia'],
    7: ['United Kingdom', 'Ireland', 'Iceland'],
    8: ['France', 'Belgium', 'Netherlands', 'Switzerland'],
    9: ['Germany', 'Austria', 'Czechia'],
    10: ['Spain', 'Portugal'],
    11: ['Italy', 'Greece', 'Albania', 'Croatia', 'Bosnia and Herz.'],
    12: ['Norway', 'Sweden', 'Denmark'],
    13: ['Finland', 'Lithuania', 'Latvia', 'Estonia'],
    14: ['Poland', 'Hungary', 'Slovakia', 'Slovenia'],
    15: ['Romania', 'Bulgaria', 'Serbia', 'North Macedonia'],
    16: ['Ukraine', 'Moldova', 'Belarus'],
    17: ['Russia'],
    18: ['Kazakhstan', 'Uzbekistan', 'Turkmenistan', 'Kyrgyzstan', 'Tajikistan'],
    19: ['Azerbaijan', 'Armenia', 'Georgia','Turkey', 'Cyprus'],
    20: ['Iran', 'Iraq', 'Syria', 'Lebanon', 'Jordan', 'Israel'],
    21: ['Saudi Arabia', 'Yemen', 'Oman', 'United Arab Emirates', 'Qatar', 'Kuwait'],
    22: ['Egypt', 'Libya', 'Sudan', 'S. Sudan'],
    23: ['Morocco', 'Algeria', 'Tunisia', 'Mauritania'],
    24: ['Nigeria', 'Niger', 'Chad'],
    25: ['Cameroon', 'Central African Rep.', 'Congo', 'Dem. Rep. Congo', 'Gabon'],
    26: ['Ethiopia', 'Somalia', 'Eritrea'],
    27: ['Kenya', 'Uganda', 'Tanzania', 'Rwanda', 'Burundi'],
    28: ['Angola', 'Zambia', 'Malawi'],
    29: ['Mozambique', 'Zimbabwe', 'Botswana'],
    30: ['South Africa', 'Namibia', 'Lesotho', 'Eswatini'],
    31: ['India', 'Sri Lanka','Bangladesh', 'Nepal', 'Bhutan'],
    32: ['Pakistan', 'Afghanistan'],
    33: ['China', 'Taiwan'],
    34: ['Japan', 'South Korea', 'North Korea'],
    35: ['Mongolia'],
    36: ['Vietnam', 'Laos', 'Cambodia'],
    37: ['Thailand', 'Myanmar'],
    38: ['Philippines', 'Malaysia', 'Singapore','Indonesia', 'Papua New Guinea'],
    39: ['Australia', 'New Zealand'],
    40: ['Mali', 'Burkina Faso', "Côte d'Ivoire", 'Ghana', 'Benin', 'Togo'],
    41: ['Senegal', 'Gambia', 'Guinea', 'Sierra Leone', 'Liberia'],
    42: ['Madagascar'],
    43: ['Canada'],
    44:['Greenland']
}
# End of ChatGPT generated/supported segment ##############################################
###########################################################################################

def map_countries_to_territories(territories):
    country_to_territory = {}
    for territory_num, countries in territories.items():
        for country in countries:
            country_to_territory[country] = territory_num

    return country_to_territory
country_to_territory = map_countries_to_territories(territories)

region_colors = {
    "Europe": "blue",
    "North America": "green",
    "Central America": "yellow",
    "South America": "red",
    "Africa": "orange",
    "Oceania": "purple",
    "Asia": "gray"
}

# Map territories to regions
territory_regions = {
    "Europe": [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
    "North America": [1, 43, 44],
    "Central America": [2],
    "South America": [3, 4, 5, 6],
    "Africa": [22, 23, 24, 25, 26, 27, 28, 29, 30,40,41],
    "Oceania": [38, 39, 42],
    "Asia":[20, 21, 31, 32, 33, 34, 35, 36, 37]
}

colors_to_rgb={
    "blue":(65, 105, 225),
    "green":(34, 139, 34),
    "yellow":(255, 228, 181),
    "red":(178, 34, 34),
    "orange":(255, 99, 71),
    "purple":(138, 43, 226),
    "gray":(47, 79, 79),
    "lightGray":(211, 211, 211)
}

# Helper function to adjust brightness for gradients
def adjust_brightness(color, factor):
    r, g, b = colors_to_rgb[color]
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))
    return rgb(r,g,b)

#Generate Shapes and Helper Functions
country_shapes = {}
for _, row in filtered_world_data.iterrows():
    country_name = row['name']
    geom = row['geometry']
    
    if isinstance(geom, MultiPolygon):
        polygons = list(geom.geoms)
    elif isinstance(geom, Polygon):
        polygons = [geom]
    elif isinstance(geom, GeometryCollection):
        # If it's a GeometryCollection, collect all polygons within it
        polygons = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon))]
    else:
        continue  # Skip if not a Polygon or MultiPolygon

    screen_polygons = []
    for polygon in polygons:
        simplified_polygon = polygon.simplify(0.5)  # Simplify for faster loading
        screen_coords = [geo_to_screen(x, y, 1200, 800) for x, y in simplified_polygon.exterior.coords]
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
        countries_in_subregion = filtered_world_data[filtered_world_data['subregion'] == f'{subregion}']['name'].tolist()
        sub_countries_dict.update({str(subregion):countries_in_subregion})


    return sub_countries_dict

def drawRisk(app):
    file_path='Images/risk.png'
    image=Image.open(file_path)
    imageWidth, imageHeight = image.size
    image=CMUImage(image)
    drawImage(image,app.width//2-imageWidth//2, app.riskY-imageHeight,opacity=app.riskOpacity)




def find_nearest_country(mouse_x, mouse_y, country_shapes, app):
    click_point = Point(mouse_x, mouse_y)

    nearest_country = None

    if not app.countriesIn:
        return None

    for country_name in app.countriesIn:
        if country_name in country_shapes:
            for screen_polygon in country_shapes[country_name]:
                shapely_polygon = Polygon(screen_polygon)

                if shapely_polygon.contains(click_point):
                    return country_name
 
    return nearest_country
###########################################################################################
#Helper Functions for MVC
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



###########################################################################################
#Actual App Functions for MVC

def onAppStart(app):
    app.changeOne=False
    app.changeTwo=False

    playSound(app,'https://archive.org/download/WiiSportsTheme/Wii%20Sports%20Theme.mp3')
    app.background='lightCyan'
    app.width = 1200
    app.height = 800
    app.UIy = 550
    app.nearest_country = None
    app.population = None
    app.subregionsIn = []
    app.countriesIn = []
    app.selected_territory = None

    app.startGame = 'gray'
    app.howTo = 'gray'
    app.riskOpacity=0
    app.riskY=400
    app.opacityStep = 10
    app.yStep = 2
    app.stepsPerSecond=40
    

    app.name=None
    app.players=[]
    app.valid=False
    app.r=150
    

    

    


def start_onStep(app):
    

    app.riskOpacity += app.opacityStep
    if app.riskOpacity >= 100 or app.riskOpacity <= 0:
        app.opacityStep *= -1  

    # Oscillate riskY between 300 and 500
    app.riskY += app.yStep
    if app.riskY >= 400 or app.riskY <= 300:
        app.yStep *= -1

def drawCountry(name):
    name_polygons = country_shapes[name]
    for polygon in name_polygons:
        L=[]
        for x, y in polygon:
            L += [x] + [y]

    drawPolygon(*L,fill='lightGray', border='Black', borderWidth=1,
             opacity=100, rotateAngle=0, dashes=False, visible=True)
    
def drawCountries(app):
    for territoryId, countryList in territories.items():
        # get region color
        region = None
        for regionName, regionTerritories in territory_regions.items():
            if territoryId in regionTerritories:
                region = regionName
                break

        base_color = region_colors.get(region, "lightGray")
        
        # adjust brightness 
        gradient_factor_step = 0.8 / len(countryList)
        for i, country_name in enumerate(countryList):
            if country_name not in country_shapes:
                continue
            
            # Calculate  color 
            gradient_factor = 1.2 - (i * gradient_factor_step)
            country_color = adjust_brightness(base_color, gradient_factor)

            for polygon in country_shapes[country_name]:
                L = []
                for x, y in polygon:
                    L += [x, y]
                drawPolygon(*L, fill=country_color, border="black", borderWidth=1,
                            opacity=100, rotateAngle=0, dashes=False, visible=True)



def start_redrawAll(app):
    drawCountries(app)

    drawLabel(f"Country: {app.nearest_country}   Population: {app.population}",app.width//2,740,size=25)

    gap=80
    
    drawRect(app.width//2-100, app.height//2+200-gap, 200, 50, fill = 'lightgray', border = app.startGame, borderWidth = 3)
    drawRect(app.width//2-100, app.height//2+200, 200, 50, fill = 'lightgray', border = app.howTo, borderWidth = 2)

    drawLabel('Start Game', app.width//2, app.height//2+200-gap+25, size = 20, fill = 'black')
    drawLabel('How to Play', app.width//2, app.height//2+200+25, size = 20, fill = 'black')

    drawRisk(app)

def start_onMouseMove(app, mouseX, mouseY):
    gap=80
    if inButton(app, mouseX, mouseY, app.width//2-100, app.height//2+200-gap, 200, 50): #about
        app.startGame = 'black'
        return
    else:
        app.startGame = 'gray'
    if inButton(app,mouseX, mouseY, app.width//2-100, app.height//2+200, 200, 50): #how to play
        app.howTo = 'black'
        return
    else:
        app.howTo = 'gray'
    
    if mouseY < app.UIy:
        withinSubregion(app, mouseX, mouseY)
        withinCountryinSub(app, mouseX, mouseY)
        app.nearest_country = find_nearest_country(mouseX, mouseY, country_shapes, app)

        app.population = getPopulation(app.nearest_country)
    
    

def inButton(app, mouseX, mouseY, rectX, rectY, width, height):
    if (rectX <= mouseX <= rectX + width) and (rectY <= mouseY <= rectY + height):
        return True
    else:
        return False
    
def start_onMousePress(app,mouseX,mouseY,button):
    if app.startGame == 'black':
        setActiveScreen('setup')
    elif app.howTo == 'black':
        app.showMessage("""Welcome to Risk! \n Prepare for a thrilling battle of strategy, diplomacy, and conquest! 
                        In Risk, players compete to dominate the world by deploying armies, conquering territories, and forging alliances. 
                        The game unfolds in three main phases: 
                        Reinforcement, where you receive new troops based on your controlled territories; 
                        Attack, where you launch daring offensives to conquer enemy lands; 
                        and Fortification, where you move your forces to strengthen your defenses. 
                        The ultimate goal is to control every territory on the board, achieving world domination. 
                        Can you outwit your opponents and lead your armies to victory?""")
        app.showMessage("""Press t at any time during the game to view major regions. Conquering all territories in that region will grant bonus troops to deploy!""")






def setup_onMousePress(app, mouseX, mouseY,button):

    if inButton(app,mouseX,mouseY,app.width//2-100, app.height//2+160, 200, 50) and app.players:
        if checkValid(app):
            activate(app)
            setActiveScreen('game')
    
    elif distance(app.width//2, app.height//2-220, mouseX, mouseY) <= app.r and app.players:
        angle=90-rounded(angleTo(app.width//2, app.height//2-220, mouseX, mouseY))
        angle=angle%360
        print(angle)
        print(gradient_color(angle,360))
        if app.changeOne==True:
            app.players[0]['color']=gradient_color(angle,360)
        elif app.changeTwo==True:
            app.players[1]['color']=gradient_color(angle,360)

    else:
        app.players = []
        colorIndex=0
        for i in range(2):
            name_response = app.getTextInput(f'Enter the name for Player {i + 1}:')
            name = 'Unknown' if not name_response else name_response

            colorList=['lightgreen','lightblue']
            color = colorList[colorIndex]
            colorIndex+=1
            app.players.append({'name': name, 'color': color})

        app.showMessage('Player setup complete!')

def setup_onKeyPress(app,key):
    if key=='enter':
        app.changeOne=False
        app.changeTwo=False

    elif key=='1':
        app.changeOne=True
        app.changeTwo=False

    elif key=='2':
        app.changeOne=False
        app.changeTwo=True

def checkValid(app):
    names = {player['name'] for player in app.players}
    if len(names) < len(app.players):
        app.showMessage('Invalid names detected. Please enter a different name.')
        return False
    
    return True

def drawColorWheel(cx, cy, radius,app):
    arcs = 360
    radius=app.r
    for i in range(arcs):
        startAngle = i
        sweepAngle = 1

        color = gradient_color(i, arcs)

        drawArc(cx, cy, 2 *radius, 2 *radius, 
                startAngle, sweepAngle, 
                fill=color, border=None)

#gradient_color was created by ChatGPT
def gradient_color(angle, max_angle):
    # Normalize the angle to [0, 1]
    normalized = angle / max_angle
    # Calculate the RGB values based on the normalized angle
    red = int(255 * max(0, min(1, abs(normalized * 6 - 3) - 1)))
    green = int(255 * max(0, min(1, 2 - abs(normalized * 6 - 2))))
    blue = int(255 * max(0, min(1, 2 - abs(normalized * 6 - 4))))
    return rgb(red, green, blue)

def distance(x0, y0, x1, y1):
    return ((x1 - x0)**2 + (y1 - y0)**2)**0.5
    
def setup_redrawAll(app):
    drawColorWheel(app.width // 2, app.height // 2-220, app.r,app)
    if app.changeOne==False and app.changeTwo==False:
        drawLabel('Click in empty space to set up players, then start game! Press 1 to change P1 Color, Press 2 to change P2 Color!',
              app.width / 2, app.height / 2 - 50, size=20, bold=False)
    elif app.changeOne==True:
        drawLabel('Changing P1 Color... Press enter to submit changes!',
              app.width / 2, app.height / 2 - 50, size=24, bold=True)
    elif app.changeTwo==True:
        drawLabel('Changing P2 Color... Press enter to submit changes!',
              app.width / 2, app.height / 2 - 50, size=24, bold=True)

    if app.players:
        for i, player in enumerate(app.players):
            drawLabel(f'Player {i + 1}: {player["name"]}, Color: {player["color"]}',
                      app.width / 2, app.height / 2 + i * 30, size=20)
    
    drawRect(app.width//2-100, app.height//2+160, 200, 50, fill = 'lightgray', border = app.startGame, borderWidth = 3)

    drawLabel('Start Game', app.width//2, app.height//2+180, size = 20, fill = 'black')

app.setMaxShapeCount(4000)

def main():
    

    runAppWithScreens(initialScreen="start",width=1200,height=800)

main()
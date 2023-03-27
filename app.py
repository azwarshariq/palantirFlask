from flask import Flask, jsonify, request
import math
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List
import math
from math import cos, sin, radians

app = Flask(__name__)

class CollectedData:
    def __init__(self, reference_id, bssids, frequencies, strengths, x, y):
        self.reference_id = reference_id
        self.bssids = bssids
        self.frequencies = frequencies
        self.strengths = strengths
        self.x = x
        self.y = y

    def set_values(self, reference_id, bssids, frequencies, strengths, x, y):
        self.reference_id = reference_id
        self.bssids = bssids
        self.frequencies = frequencies
        self.strengths = strengths
        self.x = x
        self.y = y

counterCollectedData = []
relevantCollectedData = []
counter = []

def getDistance(noOfRouters, distance):
    temp = []
    temp1 = []
    array = []
    for i in range(noOfRouters):
        for j in range(360):
            temp.append(distance[i] * (cos(radians(j))))
            temp.append(distance[i] * (sin(radians(j))))
            temp1.append(temp)
            temp = []
        array.append(temp1)
        temp1 = []
    for j in range(len(array)):
      print(array[j])
    return array

def getPixel(noOfRouters, routerDistance):
    temp = []
    temp1 = []
    array = []

    for i in range(noOfRouters):
        for j in range(360):
            temp.append(((routerDistance[i][j][0] * 700) / 24.5) + 82.5) #create own values for routers
            temp.append(((routerDistance[i][j][1] * 1200) / 41) + 87.4)
            temp1.append(temp)
            temp = []
        array.append(temp1)
        temp1 = []
    for j in range(len(array)):
      print(array[j])
    return array

def getIntersectingPoints(router1, router2, routerPixel, length1, length2):
    index1 = []
    index2 = []
    
    for i in range(length1):
        for j in range(length2):
          if round(int(routerPixel[router1][i][0]) /10) * 10 == round(int(routerPixel[router2][j][0])/10) * 10:
           
            if round(int(routerPixel[router1][i][1]) / 10) * 10 == round(int(routerPixel[router2][j][1]) / 10)* 10:
              index1.append(i)
              index2.append(j)
    
    return [index1, index2]

def getIntersectingPointsRange(router1, router2, index1, index2, routerPixel):
    intersectingLine = []
    temp = []

    if len(index1) != 0:
        temp = index1
        temp.sort()
        if temp[-1] - temp[0] < 180:
            for i in range(temp[0], temp[-1] + 1):
                intersectingLine.append(routerPixel[router1][i])
        else:
            for i in range(temp[-1], 360):
                intersectingLine.append(routerPixel[router1][i])
            for i in range(0, temp[0]):
                intersectingLine.append(routerPixel[router1][i])

    temp = index2
    temp.sort()
    if len(index2) != 0:
        if temp[-1] - temp[0] < 180:
            for i in range(temp[0], temp[-1] + 1):
                intersectingLine.append(routerPixel[router2][i])
        else:
            for i in range(temp[-1], 360):
                intersectingLine.append(routerPixel[router2][i])
            for i in range(0, temp[0]):
                intersectingLine.append(routerPixel[router2][i])

    return intersectingLine

def getIntersectingRegion(router1, router2, index1, index2, intersectingLine):
    intersectingRegion = []
    if index1:
        for i in index1:
            intersectingRegion.append(intersectingLine[router1][i])
    if index2:
        for i in index2:
            intersectingRegion.append(intersectingLine[router2][i])
    return intersectingRegion

def hypotenuseToBase(distances: List[float]) -> List[float]:
    # Assuming the Perpendicular value (in meters)
    perp = 2.8 # 9 feet approx.

    for i in range(len(distances)):
        distances[i] = math.sqrt( pow(distances[i], 2) - pow(perp, 2) )
        if math.isnan(distances[i]):
            distances[i] = 1
    return distances

def contextualiseValues(x, y, collectedPoints):
    inaccuracyX = 0.0
    inaccuracyY = 0.0
    meanCollectedX = 0.0
    meanCollectedY = 0.0

    for i in range(len(collectedPoints)):
        meanCollectedX += collectedPoints[i].x
        meanCollectedY += collectedPoints[i].y

    meanCollectedX /= len(collectedPoints)
    meanCollectedY /= len(collectedPoints)

    inaccuracyX = abs(x - meanCollectedX)
    inaccuracyY = abs(y - meanCollectedY)

    print(f'- Mean of Collected Data: ({meanCollectedX}, {meanCollectedY})')
    print(f'- Positioned values: ({x}, {y})')
    print(f'- Inaccuracy: ({inaccuracyX}, {inaccuracyY}) ')

    if inaccuracyX < 10 and inaccuracyY < 10:
        return [x, y]
    elif inaccuracyX < 25 and inaccuracyY < 25:
        return [x*(0.5) + meanCollectedX*(0.5), y*(0.5) + meanCollectedY*(0.5)]
    else:
        return [meanCollectedX, meanCollectedY]

def getCollectedPoints():
    print("Building Collected Points List")
    dataCollection = datab.collection(u'Data')  
    docs = dataCollection.where(u'floorRef',u'==', current_floor_ref_id).stream()

    print(type(docs))

    data = []
    temp = []
    count = 0

    if cf_collected_data_points == 0:
        print("Floor doesn't have any collected points")

    for doc in docs:
        data.append(doc.to_dict())
        dataPoint = CollectedData(
            current_floor_ref_id + ' ' + str(count), 
            data[count]['listOfBSSIDs'], 
            data[count]['listOfFrequencies'], 
            data[count]['listOfStrengths'], 
            data[count]['x'], 
            data[count]['y']
        )
        temp.append(dataPoint)
        count += 1

    print("Found " + str(len(temp)) + " data points")
    return temp

def useCollectedData(collectedDataPoints):
    meanCollectedX = 0.0
    meanCollectedY = 0.0
    for i in range(len(collectedDataPoints)):
        for j in range(len(collectedDataPoints[i].strengths)):
            for k in range(len(access_points_bssids)):
                if access_points_bssids[k] == collectedDataPoints[i].bssids[j]:
                    if abs(access_points_levels[k] - collectedDataPoints[i].strengths[j]) <= 1:
                        print("Collected Data Info In useCollectedData()")
                        print(collectedDataPoints[i].listOfBSSIDs[j])
                        print(collectedDataPoints[i].listOfStrengths[j])
                        print(collectedDataPoints[i].referenceId)
                        counterCollectedData.append(collectedDataPoints[i].referenceId)
                        relevantCollectedData.append(collectedDataPoints[i])

    collectedDataPoints = relevantCollectedData

    print(f"Collected Data Points Length: {len(collectedDataPoints)}")
    meanCollectedX = 0
    meanCollectedY = 0
    for point in collectedDataPoints:
        meanCollectedX += point.x
        meanCollectedY += point.y
    meanCollectedX /= len(collectedDataPoints)
    meanCollectedY /= len(collectedDataPoints)

    print(f'- Positioned using Collected Data: ({meanCollectedX}, {meanCollectedY})')

    x_coordinate = meanCollectedX
    y_coordinate = meanCollectedY
    return [x_coordinate, y_coordinate]

def trilateration(collectedDataPoints, floorRelevantDistances):

    Router_X = [(floor_routers[0][0]/100)*700, (floor_routers[1][0]/100)*700, (floor_routers[2][0]/100)*700] 
    Router_Y = [(floor_routers[0][1]/100)*1200, (floor_routers[1][1]/100)*1200, (floor_routers[2][1]/100)*1200]

    print("Router: ")
    print(Router_X)
    print(Router_Y)

    relevantCollectedDataByDistance = []

    for i in range(len(collectedDataPoints)):
        for j in range(len(collectedDataPoints[i].strengths)):
            for k in range(len(access_points_bssids)):
                if access_points_bssids[k] == collectedDataPoints[i].bssids[j]:
                  print(abs(access_points_levels[k] - collectedDataPoints[i].strengths[j]))
                  if abs(access_points_levels[k] - collectedDataPoints[i].strengths[j]) <= 5:
                    print("Collected Data Info")
                    print(collectedDataPoints[i].bssids[j])
                    print(collectedDataPoints[i].strengths[j])
                    print(collectedDataPoints[i].reference_id)
                    counter.append(collectedDataPoints[i].reference_id)
                    relevantCollectedDataByDistance.append(collectedDataPoints[i])

        print("\nRelevantCollectedDataByDistance:")
        for l in range(len(relevantCollectedDataByDistance)):
          print(relevantCollectedDataByDistance[l].strengths)
        collectedDataPoints = relevantCollectedDataByDistance

        print("\nfloorRelevantDistances: ", floorRelevantDistances)

        print("\nrouterDistance: ")
        routerDistance = getDistance(len(floorRelevantDistances), floorRelevantDistances)
        for l in range(len(routerDistance)):
          print(routerDistance[l])

        print("\nrouterPixel:")
        routerPixel = getPixel(len(floorRelevantDistances), routerDistance)
        for l in range(len(routerPixel)):
          print(routerPixel[l])

        print("\ngetIntersectingPoints:")
        index = []
        index.append(getIntersectingPoints(0, 1, routerPixel, 360, 360))
        index.append(getIntersectingPoints(0, 2, routerPixel, 360, 360))
        index.append(getIntersectingPoints(1, 2, routerPixel, 360, 360))
        for l in range(len(index)):
          print(index[l])

        intersectingLine = []
        intersectingLine.append(getIntersectingPointsRange(0, 1, index[0][0], index[0][1], routerPixel))
        intersectingLine.append(getIntersectingPointsRange(0, 2, index[1][0], index[1][1], routerPixel))
        intersectingLine.append(getIntersectingPointsRange(1, 2, index[2][0], index[2][1], routerPixel))

        index1 = []
        index1.append(getIntersectingPoints(0, 1, intersectingLine, len(intersectingLine[0]), len(intersectingLine[1])))
        index1.append(getIntersectingPoints(0, 2, intersectingLine, len(intersectingLine[0]), len(intersectingLine[2])))
        index1.append(getIntersectingPoints(1, 2, intersectingLine, len(intersectingLine[1]), len(intersectingLine[2])))

        intersectingRegion = []
        intersectingRegion.append(getIntersectingRegion(0, 1, index1[0][0], index1[0][1], intersectingLine))
        intersectingRegion.append(getIntersectingRegion(0, 2, index1[1][0], index1[1][1], intersectingLine))
        intersectingRegion.append(getIntersectingRegion(1, 2, index1[2][0], index1[2][1], intersectingLine))

        sum_x = 0
        sum_y = 0
        count = 0

        for i in range(len(intersectingRegion)):
            for j in range(len(intersectingRegion[i])):
                count += 1
                sum_x += intersectingRegion[i][j][0]
                sum_y += intersectingRegion[i][j][1]

        avg_x = sum_x/count
        avg_y = sum_y/count
        avg_y = 1200 - avg_y
        print(avg_x)
        print(avg_y)

        x_coordinate = (avg_x/700)*100
        y_coordinate = (avg_y/1200)*100
        print(x_coordinate)
        print(y_coordinate)

        if math.isnan(x_coordinate) or math.isnan(y_coordinate):
          useCollectedData(collectedDataPoints)
          print("Used Collected Data Points")
        else:
          get_x_y = contextualiseValues(x_coordinate, y_coordinate, collectedDataPoints)
          x_coordinate = get_x_y[0]
          y_coordinate = get_x_y[1]
          print("Used Trilateration")

    return x_coordinate, y_coordinate


@app.route('/api/get', methods=['GET'])
def get_data():
    return jsonify({'status': 'Working'})

@app.route('/api/post', methods=['POST'])
def post_data():
    cred = credentials.Certificate('palantir-34aa7-firebase-adminsdk-q4vrk-7edc65d413.json')
    firebase_admin.initialize_app(cred)
    datab = firestore.client()

    data = request.get_json()

    floor_routers = data['floor_routers']
    access_points_bssids = data['access_points_bssids']
    access_points_levels = data['access_points_levels']
    access_points_frequencies = data['access_points_frequencies']
    current_floor_ref_id = data['current_floor_ref_id']
    cf_collected_data_points = data['cf_collected_data_points']
    floorRelevantDistances = data['floor_relevant_distances']

    '''
    floor_routers = [
        [26,19],
        [73,47],
        [27,74]
        ] # Get from JSON (floorRouters[i].x, floorRouters[i].y)

    access_points_bssids = ['c0:f6:c2:01:e9:20','b0:95:75:a0:4c:57', '8e:aa:b5:13:8a:cb' ] # Get from JSON (accessPoints[i].bssid)
    access_points_levels = [-68, -60, -58] # Get from JSON (accessPoints[i].level)
    access_points_frequencies = [2462, 2472, 2412] # Get from JSON (accessPoints[i].frequency)

    current_floor_ref_id = 'CentaurusGround Floor' # Get from JSON (currentFloor.referenceId)
    cf_collected_data_points = 4 # Get from JSON (currentFloor.collectedDataPoints)

    floorRelevantDistances = [6.85822851131906, 6.087676046935739, 7.854575100980902]
    '''
    
    global collectedDataPoints

    print("Current Floor: " + current_floor_ref_id)

    collectedDataPoints = getCollectedPoints()

    x, y = trilateration(collectedDataPoints, floorRelevantDistances)

    response = {
        'x': x,
        'y': y
    }

    print(len(collectedDataPoints))

    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)

#!/usr/bin/env python3

import time
from ev3dev2.motor import *
from ev3dev.ev3 import *
from time import sleep
from math import fabs

cs = ColorSensor()
cs.mode = 'RGB-RAW'

def scanColors(rangeVal):
    colorsList = []
    
    # Put the color sensor into RGB mode.

    for _ in range(rangeVal):
        while True:
            if Button().any():
                break
            else:
                sleep(0.1)

        scanList = []
        for _ in range(20):
            scanList.append(getColor())
        colorsList.append(getAverageColor(scanList))
        print("Scanned",getAverageColor(scanList))

    return colorsList
        
    

def getColor():
    return (cs.value(0), cs.value(1),cs.value(2))

def getAverageColor(colorsList):
    averageColor = [0, 0,0]

    for x in range(2):
        averageColor[0] += colorsList[x][0]
        averageColor[1] += colorsList[x][1]
        averageColor[2] += colorsList[x][2]

    return int(averageColor[0] / 2), int(averageColor[1] / 2), int(averageColor[2] / 2)

def isTheSameColor(color1, color2, margin):
    if color1[0] > (color2[0] + margin) or color1[0] < (color2[0] - margin):
        return False
    if color1[1] > (color2[1] + margin) or color1[1] < (color2[1] - margin):
        return False
    if color1[2] > (color2[2] + margin) or color1[2] < (color2[2] - margin):
        return False
    return True

def getMargin(colorsList):
    margin = 80

    while True:
        modified = False
        for x in range(len(colorsList)):
            for y in range(x+1,len(colorsList)):
                if(isTheSameColor(colorsList[x],colorsList[y],margin)):
                    margin -= 1
                    modified = True
                if(modified):break
            if(modified):break
        if(not modified):break
        print("Margin compute : ",margin)
    
    return margin - 5

if __name__ == '__main__':

    previous_time = time.time()

    print("Ready to scan")

    colorsList = scanColors(2)
    #colorsList.append((101, 111, 54))
    #colorsList.append((4, 4, 2))


    targetValue = getAverageColor([colorsList[0],colorsList[1]])
    print("current average is ",targetValue)
    previous_time = time.time()
    margin = getMargin(colorsList)
    print("current margin is",margin)

    #PID tuning

    timer = 0.05 #Given in seconds

    while True:
        #Time calculation
        now = time.time()
        timeChange = now - previous_time

        if(timeChange >= timer):
            seenColor = getColor()

            multiplicator = (100/abs((sum(list(targetValue))/3 - sum(colorsList[0])/3)) + abs(100/(sum(list(targetValue))/3 - sum(colorsList[1])/3)))/2

            inputColor = sum(list(seenColor))/3
            error = min(100,max(-100,(sum(list(targetValue))/3 - inputColor) * multiplicator))
            print("RGB :",seenColor,"Error :",error,', 1 :',isTheSameColor(seenColor,colorsList[1],margin),', 2 :',isTheSameColor(seenColor,colorsList[2],margin))

#!/usr/bin/env python3

import time
from ev3dev2.motor import *
from ev3dev.ev3 import *
from time import sleep
from math import fabs


motor_left = LargeMotor(OUTPUT_A)
motor_right = LargeMotor(OUTPUT_D)
tank_drive = MoveSteering(OUTPUT_A, OUTPUT_D)
cs = ColorSensor()
cs.mode = 'RGB-RAW'
lcd = Screen()
seenColor = 0,0,0

SPEED = 20 #Maximum speed allowed to the robot in percentage (0 <= x <= 100)
MINSTEER = 10 #Minimum steer allowed to the robot in percentage (0 < x <= 100)
MAXSTEER = 65 #Maximum steer allowed to the robot in percentage (0 <= x <= 100)
STEERINGMULTIPLICATOR = 1 #Multiplicator for how fast the steering will be done

# Color Sensor need to be connected on INPUT 1 or 2
# Scans for 3 colors then returns them in the form a list of tuples (r,g,b) of size 3
# For proper operation, scan the floor first, then the line
def scanColors(rangeVal):
    colorsList = []
    
    # Put the color sensor into RGB mode.

    for _ in range(rangeVal):
        while True:
            if Button().any():
                break
            else:
                sleep(0.1)

        Sound.beep('-f 50')

        scanList = []
        for _ in range(20):
            scanList.append(getColor())
        colorsList.append(getAverageColor(scanList))
        print("Scanned",getAverageColor(scanList))
        
        Sound.beep('-f 50')

    return colorsList

# Takes a list of tuples (r,g,b) and returns an average tuple
def getAverageColor(colorsList):
    averageColor = [0, 0,0]

    for x in range(len(colorsList)):
        averageColor[0] += colorsList[x][0]
        averageColor[1] += colorsList[x][1]
        averageColor[2] += colorsList[x][2]

    return int(averageColor[0] / len(colorsList)), int(averageColor[1] / len(colorsList)), int(averageColor[2] / len(colorsList))

def getColor():
    return (cs.value(0), cs.value(1),cs.value(2))

# Returns True if colors are the same, else False
def isTheSameColor(color1, color2, margin):
    if color1[0] > (color2[0] + margin) or color1[0] < (color2[0] - margin):
        return False
    if color1[1] > (color2[1] + margin) or color1[1] < (color2[1] - margin):
        return False
    if color1[2] > (color2[2] + margin) or color1[2] < (color2[2] - margin):
        return False
    return True

#Find back the line and resume following
def helpImLost(colorsList,margin):
    tank_drive.on(0, SpeedPercent(0))
    sleep(0.5)
    tank_drive.on(100, SpeedPercent(10))

    while True:
        seenColor = getColor()
        if isTheSameColor(colorsList[1], seenColor, margin) or isTheSameColor(colorsList[2], seenColor, margin): #I found the line !
            break #When the line is found again, the robot isn't lost anymore and can resume line following

def getMargin(colorsList):
    margin = 80

    marginColorsList = colorsList.copy()
    del marginColorsList[3]
    marginColorsList.append(getAverageColor([colorsList[1],colorsList[2]]))
    marginColorsList.append(getAverageColor([colorsList[0],colorsList[2]]))

    while True:
        modified = False
        for x in range(len(marginColorsList)):
            for y in range(x+1,len(marginColorsList)):

                upperX = ((marginColorsList[x][0]+10),(marginColorsList[x][1]+10),(marginColorsList[x][2]+10))
                lowerX = ((marginColorsList[x][0]-10),(marginColorsList[x][1]-10),(marginColorsList[x][2]-10))
                upperY = ((marginColorsList[y][0]+10),(marginColorsList[y][1]+10),(marginColorsList[y][2]+10))
                lowerY = ((marginColorsList[y][0]-10),(marginColorsList[y][1]-10),(marginColorsList[y][2]-10))
                
                if(isTheSameColor(marginColorsList[x],marginColorsList[y],margin) or isTheSameColor(upperX,lowerY,margin) or isTheSameColor(lowerX,upperY,margin)):
                    margin -= 1
                    modified = True
                    #print(marginColorsList[x],",",x," is too close to ",marginColorsList[y],",",y,"with margin ",margin+1,"now reducing to ",margin)
                if(modified):break
            if(modified):break
        if(not modified):break
        
    print("Calculated margin :",max(10,margin - 3))
    return max(10,margin - 3)

# Improved followLine
def followLine(colorsList):

    steerAngle = MINSTEER #Angle of the steering
    STATE = -2  # -1 for negative steering, 0 for forward, 1 for positive steering
    lostCounter = 0 #Check if the robot is lost

    lastTimeOnFloor = time.time()
    previous_time = time.time()
    margin = getMargin(colorsList)

    timer = 0.05 #Given in seconds

    while True:

        #Time calculation
        now = time.time()
        timeChange = now - previous_time
        
        if(timeChange >= timer):
            seenColor = getColor() #Scan a color to then be used by the rest of the function

            if(isTheSameColor(colorsList[3], seenColor, margin)):
                seenColor = colorsList[1]

            #Lost timer
            if(not isTheSameColor(seenColor,colorsList[0],margin)):
                lastTimeOnFloor = time.time()

            #Lost launcher
            if(now - lastTimeOnFloor >= 1.5):
                helpImLost(colorsList,margin)


            #Cross detection, average
            if(margin >= 15 and (isTheSameColor(seenColor,getAverageColor([colorsList[1],colorsList[2]]),margin) or isTheSameColor(seenColor,getAverageColor([colorsList[0],colorsList[2]]),margin))):
                tank_drive.on_for_seconds(0,SpeedPercent(SPEED), 1, False)
                lastTimeOnFloor = time.time()

            #Cross detection, raw color
            elif(isTheSameColor(seenColor,colorsList[2],margin)):#Check for the orange line
                tank_drive.on_for_seconds(0,SpeedPercent(SPEED), 1, False)
                lastTimeOnFloor = time.time()


            if isTheSameColor(colorsList[1], seenColor, margin) or isTheSameColor(colorsList[3], seenColor, margin):
                if STATE != -1:
                    steerAngle = MINSTEER
                    STATE = -1
                    lostCounter = 0 #lostCounter is reinitialized upon seeing this color for the first time
                lostCounter += 1
                steerAngle = min(steerAngle+(lostCounter * STEERINGMULTIPLICATOR),MAXSTEER)
                tank_drive.on(steerAngle, SpeedPercent(SPEED))

            else : #If seenColor is the same color as the ground
                if STATE != 1: #Used to check for successive scans of the same color and to reinitialise upon scanning a new color
                    steerAngle = MINSTEER #steerAngle is reinitialized to MAXSTEER upon seeing this color for the first time
                    STATE = 1 #Each color is assigned to a different state
                    lostCounter = 0 #lostCounter is reinitialized upon seeing this color for the first time
                lostCounter += 1
                steerAngle = min(steerAngle+(lostCounter * STEERINGMULTIPLICATOR),MAXSTEER) #steerAngle is doubled for each successive scan of the same color but no greater than MAXSTEER
                tank_drive.on(-steerAngle, SpeedPercent(SPEED)) #Drive at an of steerAngle at a speed of speed

            

                

if __name__ == '__main__':

    Sound.beep("-f 200")
    Sound.beep("-f 300")
    Sound.beep("-f 400")

    colorsList = scanColors(4)

    while True:
        update = False
        if Button().enter:
            break
        if Button().up:
            SPEED += 5
            Sound.beep("-f "+str(SPEED * 10))
            update = True
        if Button().down:
            SPEED -= 5
            Sound.beep("-f "+str(SPEED * 10))
            update = True
        if Button().left:
            MAXSTEER -= 5
            Sound.beep("-f "+str(MAXSTEER * 10))
            update = True
        if Button().right:
            MAXSTEER += 5
            Sound.beep("-f "+str(MAXSTEER * 10))
            update = True

        if update:
            lcd.clear()
            lcd.draw.text((10,10),"Current speed = "+str(SPEED))
            lcd.draw.text((10,20),"Current steer = "+str(MAXSTEER))
            lcd.update()
        sleep(0.1)

    Sound.beep("-f 200")
    Sound.beep("-f 300")
    Sound.beep("-f 400")

    followLine(colorsList)
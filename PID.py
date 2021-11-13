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
margin = 0

Speed = 20

maxOutput = 100
minOutput = -maxOutput

isAverageOk = True

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
        #print("Scanned",getAverageColor(scanList))
        
        Sound.beep('-f 50')
    
    return colorsList

# Takes a list of tuples (r,g,b) and returns an average tuple
def getAverageColor(colorsList):
    averageColor = [0, 0,0]

    for x in range(2):
        averageColor[0] += colorsList[x][0]
        averageColor[1] += colorsList[x][1]
        averageColor[2] += colorsList[x][2]

    return int(averageColor[0] / 2), int(averageColor[1] / 2), int(averageColor[2] / 2)

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
        if isTheSameColor(colorsList[1], seenColor, margin) or isTheSameColor(getAverageColor([colorsList[0],colorsList[1]]), seenColor, margin) or isTheSameColor(colorsList[2], seenColor, margin): #I found the line !
            break #When the line is found again, the robot isn't lost anymore and can resume line following

def setTuning(kp, ki, kd, timer):
    return (kp,(ki*timer),(kd/timer))

def getMargin(colorsList):
    margin = 80
    isAverageOk = True

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
        
    #print("Calculated margin :",margin)
    if(margin - 5 <= 12):
        isAverageOk = False
        margin = 80

        marginColorsList = colorsList.copy()
        del marginColorsList[3]

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
    #print("Final calculated margin :",margin)
    return max(10,margin - 5),isAverageOk

def proportionalFollower(colorsList):

    targetValue = getAverageColor([colorsList[0],colorsList[1]])
    previous_time = time.time()
    
    
    #PID tuning
    timer = 0.05 #Given in seconds
    multiplicator = (100/abs((sum(list(targetValue))/3 - sum(colorsList[0])/3)) + abs(100/(sum(list(targetValue))/3 - sum(colorsList[1])/3)))/2
    settings = setTuning(0.45,0.9,0,timer)

    '''print("Margin :",margin)
    print("Target value :",targetValue)
    print("Multiplicator : (100/(",abs(sum(list(targetValue))/3)," - ",abs(sum(colorsList[0])/3),")) + (100/(",abs((sum(list(targetValue))))/3," - ",abs(sum(colorsList[1])/3),"))/2 = ",multiplicator)
    print("isAverageOk :",isAverageOk)'''

    Kp = settings[0]
    Ki = settings[1]
    Kd = settings[2]

    #Error manipulation
    error_sum = 0
    lastInput = sum(list(targetValue))/3

    #Lost count
    lastTimeOnFloor = time.time()
    lastSprint = time.time()

    while True:
        
        #Time calculation
        now = time.time()
        timeChange = now - previous_time
        
        if(timeChange >= timer):
            seenColor = getColor()
            trueColor = seenColor

            #Lost timer
            if(not isTheSameColor(trueColor,colorsList[0],22)):
                lastTimeOnFloor = time.time()

            #Lost launcher
            if(now - lastTimeOnFloor >= 1.5):
                helpImLost(colorsList,margin)
                error_sum = 0

            #Start line detection
            if(isTheSameColor(trueColor,colorsList[3],margin)):
                seenColor = colorsList[1]

            #Cross detection, last ressort, only used when the margin of error is too low and the gap has to crossed, cannot be used at high speeds
            elif((not isAverageOk or margin <= 12) and (isTheSameColor(trueColor,colorsList[1],margin))):
                if(now - lastSprint >= 2):
                    tank_drive.on_for_seconds(0,SpeedPercent(Speed), 1, False)
                    lastSprint = time.time()
                lastTimeOnFloor = time.time()

            #Cross detection, average, cannot be used when the margin of error is too low
            elif(isAverageOk and (isTheSameColor(trueColor,getAverageColor([colorsList[1],colorsList[2]]),margin) or isTheSameColor(trueColor,getAverageColor([colorsList[0],colorsList[2]]),margin))):
                if(now - lastSprint >= 2):
                    tank_drive.on_for_seconds(0,SpeedPercent(Speed), 1, False)
                    lastSprint = time.time()
                lastTimeOnFloor = time.time()

            #Cross detection, raw color
            elif(isTheSameColor(trueColor,colorsList[2],margin)):
                if(now - lastSprint >= 2):
                    tank_drive.on_for_seconds(0,SpeedPercent(Speed), 1, False)
                    lastSprint = time.time()
                lastTimeOnFloor = time.time()

            #Error calculations
            inputColor = sum(list(seenColor))/3
            error = min(100,max(-100,(sum(list(targetValue))/3 - inputColor) * multiplicator))
            error_sum += error * Ki #Ki decreases rampup time
            error_sum = min(max(error_sum,-65),65)#Max/min value for Ki error                
            derivative_input = inputColor - lastInput

            #PID calculations
            output = Kp * error + error_sum + Kd * derivative_input
            output = min(max(output,minOutput),maxOutput)

            #print(seenColor," | ",(int)(Kp * error)," + ",(int)(error_sum)," + ",(int)(Kd * derivative_input)," = ",(int)(output))
            #print(time.time() - startingTime,",",u,",",error)
            #print(Kp * error,"|",(int)(error_sum),"|",(int)(Kd * derivative_input),"|",(int)(output)," | ",speed)

            #Direction input
            tank_drive.on(output, SpeedPercent(Speed))

            #End of loop operations
            error_sum = error_sum * 0.925
            previous_time = now
            lastInput = inputColor

if __name__ == '__main__':

    Sound.beep("-f 200")
    Sound.beep("-f 300")
    Sound.beep("-f 400")

    colorsList = scanColors(4)
    margin, isAverageOk = getMargin(colorsList)

    lcd.clear()
    lcd.draw.text((10,10),"Current speed = "+str(Speed))
    lcd.draw.text((10,20),"Current margin = "+str(margin))
    lcd.draw.text((10,30),"IsAverageOk = "+str(isAverageOk))
    lcd.update()

    while True:
        update = False
        if Button().enter:
            break
        if Button().up:
            Speed += 5
            Sound.beep("-f "+str(Speed * 10))
            update = True
        if Button().down:
            Speed -= 5
            Sound.beep("-f "+str(Speed * 10))
            update = True
        if Button().left:
            margin -= 1
            Sound.beep("-f "+str(margin * 10))
            update = True
        if Button().right:
            margin += 2
            Sound.beep("-f "+str(margin * 10))
            update = True

        if update:
            lcd.clear()
            lcd.draw.text((10,10),"Current speed = "+str(Speed))
            lcd.draw.text((10,20),"Current margin = "+str(margin))
            lcd.draw.text((10,30),"IsAverageOk = "+str(isAverageOk))
            lcd.update()
        sleep(0.25)

    Sound.beep("-f 200")
    Sound.beep("-f 300")
    Sound.beep("-f 400")

    proportionalFollower(colorsList)
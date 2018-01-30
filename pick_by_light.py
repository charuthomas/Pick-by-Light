#!/usr/bin/env python3
#to do: - get rid of key error for carts; try to minimze sleep while getting all bits; make stop time for each; finish timer


import re
import time
import json
from sys import argv
from socket import *
from time import sleep, clock
from random import choice

"""Networking setup"""
sockhub = socket(AF_INET, SOCK_DGRAM) # UDP
sockhub.bind(('', 3865))
sockhub.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

"""Number codes"""
rightdisplay={'0':63,'1':6,'2':91,'3':79,'4':102,'5':109,'6':125,'7':7,'8':127,'9':111}
leftdisplay={'0':16128,'1':1536,'2':23296,'3':20224,'4':26112,'5':27904,'6':32000,'7':1792,'8':32512,'9':28416}
outputCarts = {0: 'C11', 1: 'C12', 2: 'C13'}

"""Default pick path"""
pp = {"A11": 88, "A12": 88, "A13": 88, "A21": 88, "A22": 88, "A23": 88, "A31": 88, "A32": 88, "A33": 88, "A41": 88, 
"A42": 88, "A43": 88, "B11": 88, "B12": 88, "B13": 88, "B21": 88, "B22": 88, "B23": 88, "B31": 88, "B32": 88, 
"B33": 88, "B41": 88, "B42": 88, "B43": 88}

"""Carts list"""
carts = ["C11", "C12", "C13"]

'''----------------------------Change A Single Display ----------------------------------
    inputs: display is format <section><row><column>, where rack is [A,B] and 
            row is [1-4] and column is [1-3] (ex. 'A21')
            pattern is the integer value you want to display (0-100, where 100=off)
    ----------------------------------------------------------------------------------'''
def ChangeDisplay(sockcntrl,display,number, setup):
    message1='xpl-cmnd\n{\nhop=1\nsource=bnz-sender.orderpick\ntarget=smgpoe-lamp.'
    message2='\n}\ncontrol.basic\n{\ndevice=display\ntype=variable\ncurrent='
    message3='\n}\n'
    # number = NumberConvert(number, setup)
    message = message1+display+message2+str(number)+message3
    message = message.encode('utf-8')
    #print(message)
    return sockcntrl.sendto(message,('192.168.2.255',3865))


''' -----------------------Convert Number to Display Equivalent---------------------------
    Converts number to correct display value
    ----------------------------------------------------------------------------------'''
def NumberConvert(number, setup=True):
    onesdigit = number % 10
    number //= 10
    tensdigit = number % 10
    if (onesdigit == 0 and tensdigit == 0):
        if setup:
            return 0
        else:
            return 32896 # this actually displays decimal points on each display
    if (tensdigit == 0):
        return rightdisplay[str(onesdigit)]
    else:
        return leftdisplay[str(tensdigit)]+rightdisplay[str(onesdigit)]


"""Resets the display"""
def reset():
    dispNum = NumberConvert(0, True)
    ChangeDisplay(sockhub, '*', dispNum, False)

"""Resets a specific display"""
def resetDisplay(display):
    dispNum = NumberConvert(0, True)
    ChangeDisplay(sockhub, display, dispNum, False)

"""Draws the randomly generated pickpath on the screen"""
def loadPickpath(pickpath):
    dispPickpath = {}
    for k, v in pickpath.items():
        dispPickpath[k] = NumberConvert(int(v), True)
        ChangeDisplay(sockhub, k, dispPickpath[k], True)
        sleep(.13)

"""Cycle through every pixel in cell to test cell"""
def testCell(display):
    while True:
        for i in range(20):
            ChangeDisplay(sockhub, display, 2**i, False)
            sleep(.05)

def generatePickpath(pickPathLength=5):
    pp = {}
    shelfPopulation = ['A11', 'A12', 'A13', 'A21', 'A22', 'A23', 'A31', 'A32',
    'A33', 'A41', 'A42', 'A43', 'B11', 'B12', 'B13', 'B21', 'B22', 'B23',
    'B31', 'B32', 'B33', 'B41', 'B42', 'B43'];
    for shelf in shelfPopulation:
        pp[shelf] = 0
    while pickPathLength > 0:
        shelf = choice(shelfPopulation)
        if shelf in pp.keys():
            pp[shelf] += 1
        else:
            pp[shelf] = 0
            pp[shelf] += 1
        pickPathLength -= 1
    return pp

def cartButtonPress():
    while True: #always checking for signals
        for shelf in ["C11", "C12", "C13"]:
            pickPathLength = 5
            while pickPathLength > 0:
                data,address = sockhub.recvfrom(4096)
                #print(data)
                if data and "hbeat".encode("utf-8") not in data:
                    if "HIGH".encode('utf-8') in data:
                        ChangeDisplay(sockhub, shelf, "125", False)
                        display = re.findall('[ABC]\d{2}'.encode("utf-8"),data)[0] # get which button was pressed as usable string
                        pickpath[display.decode("utf-8")] -= 1    
                        dispNum = NumberConvert(pickpath[display.decode("utf-8")], True)
                        ChangeDisplay(sockhub, display.decode("utf-8"), dispNum, False)
                        dispTotal = NumberConvert(total, True)
                        ChangeDisplay(sockhub, shelf, dispTotal, False)
                        pickPathLength -= 1
                if all(v == 0 for v in pickpath.values()):
                    reset()
                    pickpath = generatePickpath() # generates a randomly generated pickpath
                    pickPathLength+= 1
                    loadPickpath(pickpath) # loads the default pick path

def main():
    reset()
    f = open('tasks', 'a')

    while True:
        for currentCart in carts:

            pickPathLength = 5
            pickpath = generatePickpath(pickPathLength)

            previousCart = carts[carts.index(currentCart) - 1]
            ChangeDisplay(sockhub, currentCart, 47375, False)

            startButtonPush = False
            ChangeDisplay(sockhub, currentCart, 47375, False)
            while not startButtonPush:
                data,address = sockhub.recvfrom(4096)
                #print(data)
                if data and "hbeat".encode("utf-8") not in data:
                        if ("HIGH".encode('utf-8') in data) or ("LOW".encode('utf-8') in data):
                            display = re.findall('[ABC]\d{2}'.encode("utf-8"),data)[0] # get which button was pressed as usable string
                            #print(display)
                            if (display.decode("utf-8") == currentCart):
                                startTime = time.clock()
                                print(startTime)
                                f.write(str(startTime))
                                dispPickPathLength = NumberConvert(pickPathLength, True)
                                ChangeDisplay(sockhub, currentCart, dispPickPathLength, False)
                                startButtonPush = True

            loadPickpath(pickpath)
            f.write(str(pickpath) + "/n")

            while pickPathLength > 0:
                data,address = sockhub.recvfrom(4096)
                #print(data)
                if data and "hbeat".encode("utf-8") not in data:
                    if "HIGH".encode('utf-8') in data:
                        display = re.findall('[ABC]\d{2}'.encode("utf-8"),data)[0] # get which button was pressed as usable string
                        displayStr = display.decode("utf-8")
                        if (displayStr not in carts and pickpath[displayStr] != 0):
                            pickPathLength -= pickpath[displayStr]
                            pickpath[displayStr] = 0
                        else:
                            continue
                        
                        dispNum = NumberConvert(pickpath[displayStr], True)
                        ChangeDisplay(sockhub, displayStr, dispNum, False)
                        dispTotal = NumberConvert(pickPathLength, True)
                        ChangeDisplay(sockhub,  currentCart, dispTotal, False)
            
            ChangeDisplay(sockhub,  currentCart, 63, False)
            sleep(0.7)



    f.close()


if __name__ == '__main__':
    main()

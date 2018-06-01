from mesa import Agent, Model
import random
import getDataFromExcel as data
import numpy as np
import scipy.stats as sts

WIND_DATA = data.getData() #data from wind farm

class SolarPanelAgent(Agent):
    def __init__(self,unique_id, model,solarPanel):
        super().__init__(unique_id, model)
        self.solarPanel = solarPanel

        self.energy = 0
        self.readyToSell = True
        self.traided = None
        self.currentDemand = 0

        self.priceHistory = []
        self.quantityHistorySell = []

        self.hour = 0
        self.day = 0
        self.week = 0


    def calculatePrice(self):
        if self.readyToSell:
            self.price = round(random.uniform(1.9,0.3),1)
        else:
            self.price = 0.0
        print("Price {}".format(self.price))

    def checkSolarEnergy(self):
        self.energy = self.solarPanel.amountOfEnergyGenerated
        print("Amount of Solar energy {}".format(self.solarPanel.amountOfEnergyGenerated))

    def checkStatus(self):
        if self.energy > 0:
            self.readyToSell = True
        else:
            self.readyToSell = False

    def name_func(self):
        print("Seller agent {0}".format(self.unique_id))

    def step(self):
        self.checkSolarEnergy()
        self.checkStatus()
        self.calculatePrice()
        self.traided = False
        print("Ready to Sell {}".format(self.readyToSell))

        self.hour +=1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

class WindEnergyAgent(Agent):
    def __init__(self,unique_id, model):
        super().__init__(unique_id, model)
        self.hour = 0
        self.day = 0
        self.week = 0

        self.energy = 0
        self.readyToSell = True
        self.traided = False
        self.currentDemand = 0

        self.priceHistory = []
        self.quantityHistorySell = []

    def calculatePrice(self):
        if self.readyToSell:
            self.price = round(random.uniform(1.9,0.3),1)
        else:
            self.price = 0.0
        print("Price {}".format(self.price))

    def checkStatus(self):
        if self.energy > 0:
            self.readyToSell = True
        else:
            self.readyToSell = False
        print("Ready to Sell {}".format(self.readyToSell))

    def getWindData(self):
        windList = WIND_DATA
        self.energy = np.random.choice(windList)

    def step(self):
        self.getWindData()
        print("Wind energy {}".format(self.energy))
        self.checkStatus()
        self.calculatePrice()
        self.traided = False

        self.hour +=1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

class HeatedFloorAgent(Agent):
    def __init__(self,unique_id, model):
        super().__init__(unique_id, model)

        self.isInRoom = None
        self.minConsumption = 0.4
        self.readyToBuy = True
        self.traided = False
        self.energy = 0

        self.hour = 0
        self.day = 0
        self.week = 0
        self.currentDemand = 0 #0.8 Kwh for average bathroom
        self.price = 0

    def calculatePrice(self):
        self.price = round(random.uniform(1.9,0.3),2) #price for KWh, NOK
        print("Price {}".format(self.price))

    def calculateDemand(self):
        if self.isInRoom:
            self.calculatePrice()
            self.currentDemand = 0.8
            self.readyToBuy = True
        else:
            self.currentDemand = 0
            self.readyToBuy = False
        print("Heated floor demand {}".format(self.currentDemand))

    def checkIfisInRoom(self):
        if self.hour >= 0 and self.hour < 7:
            self.isInRoom = np.random.choice(
                [True,False],
                1,
                p=[0.9, 0.1,])[0]
        elif self.hour > 7 and self.hour <= 16:
            if self.day < 5:
                self.isInRoom = np.random.choice(
                    [True, False],
                    1,
                    p=[0.1, 0.9])[0]
            else:
                self.isInRoom = np.random.choice(
                    [True, False],
                    1,
                    p=[0.6, 0.4])[0]
        elif self.hour >= 17 and self.hour <= 21:
            self.isInRoom = np.random.choice(
                [True, False],
                1,
                p=[0.7, 0.3])[0]

        elif self.hour >= 22 and self.hour <= 23:
            self.isInRoom = np.random.choice(
                [True, False],
                1,
                p=[0.9, 0.1])[0]
        print("Person is in the room {}".format(self.isInRoom))

    def name_func(self):
        print("Agent {}".format(self.unique_id))

    def step(self):
        self.name_func()
        self.traided = False
        self.checkIfisInRoom()
        self.calculateDemand()
        self.hour +=1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

class TradeInterface(Agent): #interface for trading agents
    def __init__(self,unique_id, model):
        super().__init__(unique_id, model)

        self.buyers = []
        self.sellers = []
        self.demands = []
        self.productions = []
        self.demandPrice = []
        self.supplyPrice = []
        self.clearPrice = 0
        self.surplus = 0

        self.hour = 0
        self.day = 0
        self.week = 0
        self.stepCount = 0

        self.currentSeller = 0
        self.currentBuyer = 0

        self.numberOfBuyers = 0
        self.numberOfSellers = 0

        self.solarEnergyDistribution = []
        self.windEnergyDistribution = []

        self.distributedDemands = []
        self.boughtFromTheGrid = []

        self.satisfiedDemands = []
        self.demandCount = 0

    def getSolarEnergyDistribution(self):
        for agent in self.model.schedule.agents:
            if (isinstance(agent, SolarPanelAgent)):
                self.solarEnergyDistribution.append(agent.energy)

    def getWindEnergyDistribution(self):
        for agent in self.model.schedule.agents:
            if (isinstance(agent, WindEnergyAgent)):
                self.windEnergyDistribution.append(agent.energy)


    def getSellers(self):
        self.sellers = []
        self.numberOfSellers = 0
        supplyValue = 0.0
        for agent in self.model.schedule.agents:
            if (isinstance(agent, SolarPanelAgent) or isinstance(agent,StorageAgent )or isinstance(agent,WindEnergyAgent)):
                if agent.readyToSell is True:
                    self.numberOfSellers += 1
                    self.sellers.append(agent.unique_id)
                    supplyValue = round(supplyValue+agent.energy,3)

        self.productions.append(supplyValue)
        print("Sellers {}".format(self.sellers))
        print("Number of sellers {}".format(self.numberOfSellers))

    def getBuyres(self):
        self.buyers = []
        demandValue = 0.0
        self.numberOfBuyers = 0
        for agent in self.model.schedule.agents:
            if (isinstance(agent, HeaterAgent) or isinstance(agent,LightAgent) or isinstance(agent,StorageAgent) or isinstance(agent,HeatedFloorAgent)):
                if agent.readyToBuy is True:
                    self.numberOfBuyers += 1
                    self.buyers.append(agent.unique_id)
                    demandValue = round(demandValue+agent.currentDemand,3)
        self.demands.append(demandValue)
        print("Buyers {}".format(self.buyers))
        print("Number of buyers {}".format(self.numberOfBuyers))

    def chooseSeller(self,buyer,price = None,amount = None):
        seller = np.random.choice(self.sellers) #choose seller randomly
        for agent in self.model.schedule.agents:
            if (isinstance(agent, SolarPanelAgent) or isinstance(agent,StorageAgent) or isinstance(agent,WindEnergyAgent)):
                if agent.readyToSell is True and agent.unique_id == seller and agent.traided is False:
                    print("Seller {}".format(agent.unique_id))
                    print("Seller price {}".format(agent.price))
                    print("Seller energy {}".format(agent.energy))

                    if buyer.price >= agent.price:
                        print("Deal !")
                        amount = min(agent.energy,buyer.currentDemand)
                        if buyer.currentDemand > amount:
                            buyer.currentDemand = round(buyer.currentDemand-agent.energy,3)
                            buyer.energy += agent.energy

                            agent.energy = 0
                            agent.traided = True
                            agent.readyToSell = False

                            self.numberOfSellers -= 1
                            self.sellers.remove(agent.unique_id)
                            print("Number of sellers {}".format(self.numberOfSellers))
                        elif buyer.currentDemand <= amount:
                            agent.energy = round(agent.energy-buyer.currentDemand,3)
                            buyer.energy += buyer.currentDemand

                            buyer.currentDemand = 0
                            buyer.traided = True
                            buyer.readyToBuy = False
                            self.numberOfBuyers -= 1
                            self.buyers.remove(buyer.unique_id)

                            if agent.energy > 0:
                                agent.price = np.mean([agent.price,buyer.price])
                                agent.priceHistory.append(agent.price)
                            else:
                                agent.traided = True
                                self.numberOfSellers -= 1
                        print("Buyer demand {}".format(buyer.currentDemand))
                        print("Buyer traided status {}".format(buyer.traided))
                        print("Remaining amount of energy {}".format(agent.energy))

                        print("Number of sellers {}".format(self.numberOfSellers))
                        print("Number of buyers {}".format(self.numberOfBuyers))
                    else:
                        print('No deal')
                        agent.price = round(np.mean([agent.price, buyer.price]),1)
                        agent.priceHistory.append(agent.price)
                        buyer.calculatePrice()

    def buyFromGrid(self,buyer):
        gridPrice = 0
        for agent in self.model.schedule.agents:
            if (isinstance(agent, SmartGridAgent)):
                gridPrice = agent.price
        if buyer.price >= gridPrice:
            print("Trade with Grid")
            buyer.energy += buyer.currentDemand
            print("Bought form Grid {}".format(buyer.currentDemand))
            buyer.currentDemand = 0

        else:
            print("No trade, bought for max price")
            buyer.energy += buyer.currentDemand
            print("Bought form Grid {}".format(buyer.currentDemand))
            buyer.currentDemand = 0

    def sellToGrid(self,amount):
        gridPrice = 0
        for agent in self.model.schedule.agents:
            if (isinstance(agent, SmartGridAgent)):
                gridPrice = agent.price
        profit = round(amount*gridPrice,3)
        return profit

    def distributeEnergy(self):
        self.sellPrice = 0
        self.buyPrice = 0
        self.demandCount = 0.0
        while(not(self.numberOfSellers <= 0 or self.numberOfBuyers <= 0)):
            buyer_id = np.random.choice(self.buyers)#random buyers
            print("Buyer Random ID {}".format(buyer_id))
            for agent in self.model.schedule.agents:
                if (isinstance(agent, HeaterAgent) or isinstance(agent,LightAgent)or isinstance(agent,StorageAgent) or isinstance(agent,HeatedFloorAgent)):
                    if agent.readyToBuy is True and agent.traided is False:
                        if agent.unique_id == buyer_id:
                            print("Buyer {}".format(agent.unique_id))
                            print("Buy price {}".format(agent.price))
                            print("Buyer demand {}".format(agent.currentDemand))
                            self.chooseSeller(agent,self.buyPrice,agent.currentDemand)

        self.satisfiedDemands.append(self.demandCount)

        if self.numberOfBuyers > 0 and self.numberOfSellers == 0:
            print("Not enough energy, need to buy from grid")
            #check buyers, buy from grid
            for agent in self.model.schedule.agents:
                if (isinstance(agent, HeaterAgent) or isinstance(agent, LightAgent) or isinstance(agent,StorageAgent)):
                    if agent.readyToBuy == True and agent.traided == False:
                        self.buyFromGrid(agent)

        elif self.numberOfBuyers == 0 and self.numberOfSellers > 0:
            self.surplus = 0
            print("Energy left")
            for agent in self.model.schedule.agents: #check if renewable energy left
                if (isinstance(agent, SolarPanelAgent) or isinstance(agent,WindEnergyAgent)):
                    print("Renewable energy {}".format(agent.energy))
                    print("Ready to sell {}".format(agent.readyToSell))
                    if agent.energy > 0:
                        self.surplus += agent.energy
                        agent.energy = 0

            if self.surplus > 0:
                print("Surplus {}".format(self.surplus)) #possible sell to grid
                for agent in self.model.schedule.agents:
                    if (isinstance(agent, StorageAgent)):
                        print("Stored energy left {}".format(agent.energy))
                        energySurplus = agent.addEnergy(self.surplus)
                        print("Energy in storage {}".format(agent.energy))
                        print("Surplus which can be sold {}".format(energySurplus))
                        print("Sold to Grid {} NOK".format(self.sellToGrid(energySurplus)))

        else:
            print("No sellers and No buyers")

    def step(self):
        print("Trade")
        self.getBuyres()
        self.getSellers()
        self.getWindEnergyDistribution()
        self.getSolarEnergyDistribution()
        self.distributeEnergy()

        #time
        self.hour +=1
        self.stepCount +=1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

class SmartGridAgent(Agent):
    def __init__(self,unique_id, model):
        super().__init__(unique_id, model)
        self.price = 0
        self.tariffCoef = 1

        self.hour = 0
        self.day = 0
        self.week = 0

    def checkTariff(self):
        if self.hour >= 0 and self.hour < 7:
            self.tariffCoef = 0.6

        elif self.hour >= 7 and self.hour <= 10:
            self.tariffCoef = 1.5

        elif self.hour >= 12 and self.hour <= 14:
            self.tariffCoef = 1.9

        elif self.hour >= 18 and self.hour <= 20:
            self.tariffCoef = 1.5

        elif self.hour >= 23:
            self.tariffCoef = 0.5
        else:
            self.tariffCoef = 1
        print("Grid Tariff {}".format(self.tariffCoef))

    def calculatePrice(self):
        self.price = 4*self.tariffCoef
        print("Grid Price {}".format(self.price))

    def name_func(self):
        print("Smart Grid agent {0}".format(self.unique_id))

    def step(self):
        self.checkTariff()
        self.calculatePrice()
        self.hour +=1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

class StorageAgent(Agent):
    def __init__(self,unique_id, model):
        super().__init__(unique_id, model)

        self.amperHour = 500
        self.voltage = 24
        self.wCapacity = (self.amperHour*self.voltage)/1000

        self.capacity = self.wCapacity
        self.energy = 12.0
        self.price = 0

        self.readyToSell = True
        self.readyToBuy = False
        self.traided = False

        self.currentDemand = 0
        self.status = None

        self.hour = 0
        self.day = 0
        self.week = 0

        self.priceHistory = []
        self.quantityHistorySell = []
        self.quantityHistoryBuy = []

    def calculateDemand(self):
        if self.status == 'max' or self.status == 'stable':
            self.currentDemand = 0.0
        else:
            self.currentDemand = np.random.choice([(self.capacity/2) - self.energy,(self.capacity-self.energy)])
            self.currentDemand = round(self.currentDemand,3)
        print("Energy demand {}".format(self.currentDemand))


    def checkBatteryCondition(self):
        if self.energy >= 12.0:
            self.energy = 12.0
        if self.energy <= 12.0 and self.energy >= 10.0:
            print("Maximum output, discharge disarable")
            self.status = 'max'
        elif self.energy <=10.0 and self.energy >= 6.0:
            print("Stable with slow discharge")
            self.status = 'stable'
        else:
            self.status = 'unstable'
            print("Unstable state, discharge not desirable, needs charging")

    def calculatePrice(self):
        self.price = round(random.uniform(1.9,0.3),1) #price for KWh, NOK
        print("Price {}".format(self.price))

    def addEnergy(self,energy):
        if (energy + self.energy >= self.capacity):
            print("Possible overcharging")
            surplus = ((self.energy+energy)-self.capacity)
            self.energy += (energy - ((self.energy+energy)-self.capacity))
            self.energy = round(self.energy,3)
            print("Energy level {}".format(self.energy))
        elif energy + self.energy < self.capacity:
            self.energy += energy
            self.energy = round(self.energy, 3)
            surplus = 0
            print("Energy level {}".format(self.energy))
        surplus = round(surplus, 3)
        return surplus

    def getStatus(self):
        print("Status {}".format(self.status))

    def checkStatus(self):
        if self.status == 'max' or self.status == 'stable':
            self.readyToSell = True
            self.readyToBuy = False
        else:
            self.readyToSell = False
            self.readyToBuy = True
        print("Available energy {}".format(self.energy))

    def name_func(self):
        print("Agent {0}".format(self.unique_id))

    def step(self):
        self.name_func()
        self.checkBatteryCondition()
        self.getStatus()
        self.checkStatus()
        self.calculateDemand()
        self.calculatePrice()
        self.traided = False
        print("Ready to Sell {}".format(self.readyToSell))
        print("Ready to Buy {}".format(self.readyToBuy))

        self.hour +=1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

class SolarPanel(object):
    def __init__(self,peakPower,sunLevel):
        self.peakPower = peakPower
        self.sunLevel = sunLevel
        self.size = 0
        self.amountOfEnergyGenerated = 0

class OutdoorLight(object):
    def __init__(self):
        self.outdoorLight = 0

class InitAgent(Agent):
    def __init__(self,unique_id, model,solarPanel,outdoorLight = None,days=7):
        super().__init__(unique_id, model)
        self.weatherCondition = 0

        self.days = days
        self.solarPanel = solarPanel
        self.outLight = outdoorLight
        self.hourCount = 0
        self.outdoorL = 0
        self.outdoorTemp = 0
        self.weatherCoeff = 0

        self.luxDistribution = []

        self.hour = 0
        self.day = 0
        self.week = 0

    def getWeatherCondition(self):
        self.weatherCondition = random.choice(['sunny','partly cloudy','cloudy','rainy'])
        print("Weather is {}".format(self.weatherCondition))
        return self.weatherCondition

    def calculateWeatherCoeff(self):
        if self.weatherCondition == 'sunny':
            self.weatherCoeff = 1.1
        elif self.weatherCondition == 'partly cloudy':
            self.weatherCoeff = 0.8
        elif self.weatherCondition == 'cloudy':
            self.weatherCoeff = 0.2
        elif self.weatherCondition == 'rainy':
            self.weatherCoeff = 0

    def getOutdoorTemp(self):
        self.outdoorTemp = round(np.random.choice(sts.norm.rvs(9, 2, size=24)))
        print("Outdoor temperature {}".format(self.outdoorTemp))

    def calculateSolarEnergy(self):
        amountOfEnergy = 0
        if self.hour >= 0 and self.hour <= 4:
            self.solarPanel.amountOfEnergyGenerated = 0
            amountOfEnergy = 0
            print("Amount of Solar energy {}".format(self.solarPanel.amountOfEnergyGenerated))
        elif self.hour > 4 and self.hour <= 21:
            if self.hour >= 6 and self.hour <=7:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(0.26, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 7 and self.hour <= 9:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(0.56, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 8 and self.hour <= 10:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(0.97, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 10 and self.hour <= 11:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(1.4, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 11 and self.hour <= 12:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(2.5, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 12 and self.hour <= 13:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(3.68, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 13 and self.hour <= 14:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(2.9, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 14 and self.hour <= 15:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(1.9, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 15 and self.hour <= 16:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(2, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 16 and self.hour <= 17:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(1.8, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 17 and self.hour <= 18:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(0.8, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 18 and self.hour <= 19:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(0.4, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour > 19 and self.hour <= 20:
                amountOfEnergy = abs(round(np.random.choice(sts.norm.rvs(0.1, 1, size=self.days))*self.weatherCoeff,2))
            elif self.hour >= 21:
                amountOfEnergy = 0
            print("Amount of energy Kwh {}".format(amountOfEnergy)) #real data multiplied on weather coefficient
            self.solarPanel.amountOfEnergyGenerated = amountOfEnergy
            print("Amount of Solar energy {}".format(self.solarPanel.amountOfEnergyGenerated))
        else:
            self.solarPanel.amountOfEnergyGenerated = 0
            print("Amount of Solar energy {}".format(self.solarPanel.amountOfEnergyGenerated))

    #amount of lux
    def calculateOutdoorLight(self):
        if self.hour >= 0 and self.hour < 7:
            self.outLight.outdoorLight = 20
        elif self.hour == 7 and self.weatherCondition == 'sunny':
            self.outLight.outdoorLight = 400
        elif self.hour == 7 and self.weatherCondition == 'partly cloudy':
            self.outLight.outdoorLight = 100
        elif self.hour == 7 and self.weatherCondition == 'cloudy':
            self.outLight.outdoorLight = 40
        elif self.hour > 7 and self.hour < 18:
            if self.weatherCondition == 'sunny':
                self.outLight.outdoorLight = 2000
            if self.weatherCondition == 'partly cloudy':
                self.outLight.outdoorLight = 200
            if self.weatherCondition == 'cloudy':
                self.outLight.outdoorLight = 100
        elif self.hour == 18 and self.weatherCondition == 'sunny':
            self.outLight.outdoorLight = 400
        elif self.hour == 18 and self.weatherCondition == 'partly cloudy':
            self.outLight.outdoorLight = 80
        else:
            self.outLight.outdoorLight = 20
        self.luxDistribution.append(self.outLight.outdoorLight)
        print("Outdoor light {}".format(self.outLight.outdoorLight))


    def step(self):
        print("Hour {}".format(self.hour))
        print("Day {}".format(self.day))
        print("Week {}".format(self.week))

        self.getWeatherCondition()
        self.calculateWeatherCoeff()
        self.calculateSolarEnergy()
        self.calculateOutdoorLight()
        self.getOutdoorTemp()
        self.hourCount += 1
        self.hour +=1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

class HeaterAgent(Agent):
    def __init__(self, unique_id, model,temperature = 20,roomSize = None):
        super().__init__(unique_id, model)
        self.energy = 0
        self.minTemp = 20
        self.desiredTemp = 0
        self.readyToBuy = None
        self.price = 0

        self.supply = 0
        self.priceHistory = []
        self.quantityHistoryBuy = []
        self.temperatureDistribution = []

        #formula coefficients
        self.outdoorTemp = 16
        self.roomSize = roomSize
        self.power = 1
        self.hour = 0
        self.day = 0
        self.week = 0

        self.personProbability = []

        self.isInRoom = True
        self.isInHome = True

        self.turnedOn = True
        self.traided = False

        self.price = 0
        self.demandKwh = 0

        self.gamma = 0.5

        self.tempRange = 0

        self.currentTemp = 0
        self.currentDemand = 0
        self.minDemand = 0
        self.maxDemand = 0

    def calculatePrice(self):
        self.price = round(random.uniform(1.9,0.3),1) #price for KWh, NOK
        print("Price {}".format(self.price))

    def checkStatus(self):
        if self.currentDemand > 0:
            self.readyToBuy = True
        else:
            self.readyToBuy = False
        print("Ready to Buy {}".format(self.readyToBuy))

    def getTempRange(self):
        if self.turnedOn:
            if self.currentTemp > self.minTemp:
                self.tempRange = list(range(self.currentTemp, self.desiredTemp + 1))
            else:
                self.tempRange = list(range(self.minTemp, self.desiredTemp + 1))
            print("Temperature range {}".format(self.tempRange))
        else:
            print("Heater is turned off")

    def checkIfIsIn(self):
        if self.hour >= 0 and self.hour < 7:
            self.isInRoom = np.random.choice([True, False],1,p=[0.9, 0.1])[0]
        elif self.hour > 7 and self.hour <= 16:
            if self.day < 5:
                self.isInRoom = np.random.choice([True, False],1,p=[0.1, 0.9])[0]
            else:
                self.isInRoom = np.random.choice([True, False],1,p=[0.6, 0.4])[0]
        elif self.hour >= 17 and self.hour <= 21:
            self.isInRoom = np.random.choice([True, False],1,p=[0.8, 0.2])[0]
        elif self.hour >= 22 and self.hour <= 23:
            self.isInRoom = np.random.choice([True, False], 1, p=[0.9, 0.1])[0]
        print("Person is in the room {}".format(self.isInRoom))
        self.personProbability.append(self.isInRoom)

    def getCurrentTemp(self)->int:
        self.previousTemp = self.currentTemp
        self.currentTemp = random.choice(sts.norm.rvs(20,2,size=24))
        self.currentTemp = int(self.currentTemp)
        print("Current temperature {}".format(self.currentTemp))
        return self.currentTemp

    def getDesiredTemp(self)->int:
        if self.isInRoom:
            self.desiredTemp = random.choice(list(range(20,31)))
        else:
            self.desiredTemp = self.minTemp
        print("initial desired temperature {}".format(self.desiredTemp))
        return self.desiredTemp

    def checkTempDifference(self):
        if self.desiredTemp <= self.currentTemp:
            print("no difference or temperature is lower")
            self.turnedOn = False
        else:
            self.turnedOn = True

    def computeDemand(self):
        self.energyKJ = 0
        self.roomSize = 15
        dryAirHeat = 1
        dryAirDencity = 1275
        roomHeight = 2.5
        if self.turnedOn == True:
            self.energyKJ = dryAirHeat*dryAirDencity*self.roomSize*roomHeight*(self.desiredTemp-self.currentTemp)
            self.demandKwh = round((self.energyKJ/1000)*0.00028,3)
            self.currentDemand = self.demandKwh*10
            print("Demand KWh {}".format(self.demandKwh))
        else:
            self.currentDemand = 0

    def name_func(self):
        print("{0}".format(self.unique_id))

    def step(self):
        self.name_func()
        self.traided = False

        self.checkIfIsIn()
        self.getCurrentTemp()
        self.getDesiredTemp()

        print("Status {}".format(self.turnedOn))
        self.checkTempDifference()
        print("check temperature difference...")
        print("Status {}".format(self.turnedOn))

        self.getTempRange()
        self.calculatePrice()
        self.computeDemand()
        self.checkStatus()

        self.hour +=1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

class LightAgent(Agent):#light/light intencity
    def __init__(self, unique_id, model, power = 0.075,lumens = 90,area = 15):
        super().__init__(unique_id, model)
        self.energy = 0
        self.power  = power
        self.lumens = lumens #lumens/Watt
        self.utilizationCoeff = 0.6
        self.lightLossFactor = 0.8
        self.area = area
        self.lux = 0
        self.userProfile = 0
        self.readyToBuy = None
        self.traided = None

        self.isInHome = True
        self.isInRoom = True

        self.priceHistory = []
        self.quantityHistoryBuy = []

        self.turnedOn = False
        self.bill = 0
        self.price = 0
        self.value = 0

        self.hour = 0
        self.day = 0
        self.week = 0

        self.desiredLight = None
        self.outdoorLight = 0
        self.currentDemand = 0

    def calculatePrice(self):
        self.price = round(random.uniform(1.9,0.3),1) #price for KWh, NOK
        print("Price {}".format(self.price))

    def checkStatus(self):
        if self.currentDemand > 0:
            self.readyToBuy = True
        else:
            self.readyToBuy = False
        print("Ready to Buy {}".format(self.readyToBuy))

    def setUserProfile(self):
        self.userProfile = random.randrange(1,5)
        if self.userProfile == 4:
            self.desiredLight = 1500

        elif self.userProfile == 3:
            self.desiredLight = 500

        elif self.userProfile == 2:
            self.desiredLight = 100

        elif self.userProfile == 1:
            self.desiredLight = 0
            self.turnedOn = False
        print("User profile {}".format(self.userProfile))
        print("Desired Light level {}".format(self.desiredLight))

    def getOutdoorLight(self): #get info from init agent
        for agent in self.model.schedule.agents:
            if (isinstance(agent, InitAgent)):
                self.outdoorLight = agent.outLight.outdoorLight
        print("Calculated outdoor light {}".format(self.outdoorLight))

    def calculateDemand(self):
        if self.turnedOn:
            if self.outdoorLight >= self.desiredLight: #set desired light level according to the user
                powerDemand = (self.desiredLight*self.area)/self.lumens
                self.currentDemand = round(powerDemand / 1000,2)
                print("Desired light {}".format(self.desiredLight))
                print("Power {}".format(powerDemand))

            elif self.outdoorLight < self.desiredLight: #calculate difference for adjusting
                luxDiff = self.desiredLight - self.outdoorLight
                powerDemand = (luxDiff*self.area)/self.lumens
                self.currentDemand = round(powerDemand / 1000,2)
            else:
                self.currentDemand = 0
                print("Too bright")
        else:
            print("no movement")
            self.currentDemand = 0
        print("Light demand {} kW".format(self.currentDemand))

    def getStatus(self):
        if self.isInRoom:
            self.turnedOn = True
        else:
            self.turnedOn = False

    def checkMovement(self):
        if self.hour >= 0 and self.hour < 7:
            self.isInRoom = np.random.choice([True, False],1,p=[0.9, 0.1, ])[0]
        elif self.hour > 7 and self.hour <= 16:
            if self.day < 5:
                self.isInRoom = np.random.choice([True, False],1,p=[0.1, 0.9])[0]
            else:
                self.isInRoom = np.random.choice([True, False],1,p=[0.6, 0.4])[0]
        elif self.hour >= 17 and self.hour <= 21:
            self.isInRoom = np.random.choice([True, False],1,p=[0.8, 0.2])[0]
        elif self.hour >= 22 and self.hour <= 23:
            self.isInRoom = np.random.choice([True, False], 1, p=[0.9, 0.1])[0]
        print("Person is in the room {}".format(self.isInRoom))

    def name_func(self):
        print("{0}".format(self.unique_id))

    def step(self):
        self.name_func()
        self.traided = False
        self.getOutdoorLight()
        self.setUserProfile()

        self.checkMovement()
        self.getStatus()

        self.calculatePrice()
        self.calculateDemand()
        self.checkStatus()

        self.hour +=1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

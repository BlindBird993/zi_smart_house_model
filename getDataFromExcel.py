import pandas as pd
import numpy as np
from pandas import ExcelWriter
from pandas import ExcelFile
from mesa import Agent, Model


def getData():
    df = pd.read_excel('wind.xlsx', sheet_name='Sheet1')
    ds = df
    ds['energy'] = ds['energy'].astype(str)
    print("Column headings:")
    print(df.columns)

    energyList = ds['energy']
    df = pd.DataFrame({'energy': energyList})

    energyList = ds['energy']
    energyList = [x.replace('.', '') for x in energyList]
    energyList = [x.replace(',', '.') for x in energyList]
    energyList = [x.replace('-', '0') for x in energyList]
    energyData = pd.DataFrame({'energy': energyList})
    energyData = energyData.astype(float)

    for index, row in energyData.iterrows():
        energyData.iat[index, 0] = round(energyData.iat[index, 0] / 1000, 2)
    energyList = energyData['energy'].tolist()
    return  energyList


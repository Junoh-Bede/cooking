import csv
import os
import pandas as pd
from datetime import datetime


def cooking_hours(usage, db_path):
    meal_hour = ['7', '8', '9', '11', '12', '13', '17', '18', '19']
    occupancy_file = f"{db_path}/archetypes/use_types/{usage}.csv"
    with open(occupancy_file, 'r') as fr:
        rdr = list(csv.reader(fr))
        week_day = [int(i[1]) for i in rdr if i[0] == 'WEEKDAY' and i[1] in meal_hour and float(i[2]) != 0]
        sat_day = [int(i[1]) for i in rdr if i[0] == 'SATURDAY' and i[1] in meal_hour and float(i[2]) != 0]
        sun_day = [int(i[1]) for i in rdr if i[0] == 'SUNDAY' and i[1] in meal_hour and float(i[2]) != 0]
        total_hours = len(week_day) * 246 + len(sat_day) * 52 + len(sun_day) * 67
        return total_hours, week_day, sat_day, sun_day


def agricultural_hours(db_path):
    occupancy_file = f"{db_path}/archetypes/use_types/AGRICULTURAL.csv"
    with open(occupancy_file, 'r') as fr:
        rdr = list(csv.reader(fr))
        week_day = [float(i[2]) for i in rdr if i[0] == 'WEEKDAY' and i[1]]
        sat_day = [float(i[2]) for i in rdr if i[0] == 'SATURDAY' and i[1]]
        sun_day = [float(i[2]) for i in rdr if i[0] == 'SUNDAY' and i[1]]
        total_hours = sum(week_day) * 246 + sum(sat_day) * 52 + sum(sun_day) * 67
        return total_hours, week_day, sat_day, sun_day


def fill_cooking(row, usage, area, cooking_days, energy_type):
    energy = {
        'NG': 'COOKING_NG',
        'E': 'COOKING_E'
    }
    total_hours, week_day, sat_day, sun_day = cooking_days[usage]
    day = datetime.fromisoformat(row['DATE']).weekday()
    hour = datetime.fromisoformat(row['DATE']).time().hour
    if day in range(5):
        if hour in week_day:
            return energy[energy_type][usage] * area * 1.1622 / total_hours
        else:
            return 0
    elif day == 5:
        if hour in sat_day:
            return energy[energy_type][usage] * area * 1.1622 / total_hours
        else:
            return 0
    elif day == 6:
        if hour in sun_day:
            return energy[energy_type][usage] * area * 1.1622 / total_hours
        else:
            return 0
    else:
        return 0


def fill_agriculture(row, usage, area):
    total_hours, week_day, sat_day, sun_day = agricultural_hours()
    day = datetime.fromisoformat(row['DATE']).weekday()
    hour = datetime.fromisoformat(row['DATE']).time().hour
    if usage == 'AGRICULTURAL':
        if day in range(5):
            if week_day[hour] != 0:
                return 5.543257971 * area * 0.2777778 * 37.7 / total_hours
            else:
                return 0
        elif day == 5:
            if sat_day[hour] != 0:
                return 5.543257971 * area * 0.2777778 * 37.7 / total_hours
            else:
                return 0
        elif day == 6:
            if sun_day[hour] != 0:
                return 5.543257971 * area * 0.2777778 * 37.7 / total_hours
            else:
                return 0
        else:
            return 0
    else:
        return 0
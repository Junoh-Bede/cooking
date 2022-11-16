import pandas as pd
import geopandas as gpd
from datetime import datetime
from multiprocessing import Pool, cpu_count


# 건물 용도에 따른 연중 전체 취사 시간(total_hours) 및 일별 취사 시간(result) 계산
def cooking_hours(db_path, usage):
    meal_hour = [7, 8, 9, 11, 12, 13, 17, 18, 19]
    occupancy_file = f"{db_path}/inputs/technology/archetypes/use_types/{usage}.csv"
    occupancy = pd.read_csv(occupancy_file, header=2)
    result = {}
    for day in ['WEEKDAY', 'SATURDAY', 'SUNDAY']:
        day_df = occupancy[occupancy['DAY'] == day]
        day_df = day_df[day_df['OCCUPANCY'] != 0]
        result[day] = list(day_df[day_df['HOUR'].isin(meal_hour)]['HOUR'])
    total_hours = len(result['WEEKDAY']) * 246 + len(result['SATURDAY']) * 52 + len(result['SUNDAY']) * 67
    return total_hours, result


# CEA 결과 데이터에 취사 에너지 추가 (데이터프레임 수정)
def fill_cooking(row, usage, area, path, cooking_loads):
    total_hours, result = cooking_hours(path, usage)
    week_day = result['WEEKDAY']
    saturday = result['SATURDAY']
    sunday = result['SUNDAY']
    day = datetime.fromisoformat(row['DATE']).weekday()
    hour = datetime.fromisoformat(row['DATE']).time().hour
    if day in range(5):
        if hour in week_day:
            return cooking_loads[usage] * area / total_hours
        else:
            return 0
    elif day == 5:
        if hour in saturday:
            return cooking_loads[usage] * area / total_hours
        else:
            return 0
    elif day == 6:
        if hour in sunday:
            return cooking_loads[usage] * area / total_hours
        else:
            return 0
    else:
        return 0


# CEA 결과 데이터에 취사 에너지 추가
def calculate_cooking_loads(item):
    path = item['path']
    area = item['AREA']
    cook = item['cooking']
    usage = item['1ST_USE']
    data = pd.read_csv(path)
    data['cooking'] = data.apply(fill_cooking, axis=1, args=(usage, area, path, cook))
    data.to_csv(path)


# 건축물 용도와 면적 정보 계산
def get_building_info(db_path):
    architecture = gpd.read_file(f'{db_path}/inputs/building-properties/architecture.dbf')
    architecture.drop(columns=['geometry'], inplace=True)
    typology = gpd.read_file(f'{db_path}/inputs/building-properties/typology.dbf')
    typology.drop(columns=['geometry'], inplace=True)
    shape = gpd.read_file(f'{db_path}/inputs/building-geometry/zone.shp')
    building = shape.merge(typology, right_on='Name', left_on='Name')
    building = building.merge(architecture, right_on='Name', left_on='Name')
    building['AREA'] = building.area * building['floors_ag'] * building['Hs_ag']
    building = building[['Name', 'AREA', '1ST_USE']]
    return building


# 건물 용도별 단위면적당 연간 취사 에너지 소요량 parsing
def get_cooking_loads(db_path, energy_type):
    building_info = get_building_info(db_path)
    internal_loads = pd.read_excel(f"{db_path}/inputs/technology/archetypes/use_types/USE_TYPE_PROPERTIES.xlsx",
                                   sheet_name='INTERNAL_LOADS')
    internal_loads.set_index('code', inplace=True)
    internal_loads_dict = internal_loads.to_dict()
    cooking_loads = internal_loads_dict[f'{energy_type}cook_kWhm2']
    building_info['cooking'] = building_info.apply(lambda x: cooking_loads[x['1ST_USE']], axis=1)
    building_info = building_info[['Name', 'AREA', 'cooking', '1ST_USE']]
    return building_info


def process_cooking_loads(db_path, energy_type, multi_processing=True):
    check_energy_type(energy_type)
    building_info = get_cooking_loads(db_path, energy_type)
    building_info['path'] = db_path
    data = list(building_info.transpose().to_dict())
    if multi_processing:
        multi = cpu_count() - 1
        Pool(multi).map(calculate_cooking_loads, data)
    else:
        for datum in data:
            calculate_cooking_loads(datum)


def check_energy_type(energy_type):
    if energy_type in ['E', 'NG']:
        return True
    else:
        raise NameError('It is not supported cooking energy type!')


def main():
    energy_type = input('Please input the energy type (NG or E): ')
    db_path = input("Please input CEA scenario path: ")
    multi = input("Are you going to run multiprocessing? (y/n) : ")
    if multi == 'y':
        process_cooking_loads(db_path, energy_type)
    elif multi == 'n':
        process_cooking_loads(db_path, energy_type, multi_processing=False)


if __name__ == '__main__':
    main()

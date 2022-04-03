#!/usr/bin/python
import sys
import os
import argparse
from KnowledgeExtractor import KnowledgeExtractor as KExtractor


def initArguments():
    """
    Установка аргументов для путей к таблицам
    """
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-f_table', help='Путь до Excel таблицы Ф имен', type=str, required=True)
    argParser.add_argument('-k_table', help='Путь до Excel таблицы К имен и норм', type=str, required=True)
    argParser.add_argument('-b_table', help='Путь до Excel таблицы Б временных характеристик', type=str, required=True)
    argParser.add_argument('-ch_table', help='Путь до Excel таблицы Ч имен и числовых норм', type=str, required=True)
    argParser.add_argument('-input', help='Путь до Excel таблицы исходных данных', type=str, required=True)
    args = argParser.parse_args()
    return args

# TODO не забыть поменять пути к файлам
def getFullPath(fileName):
    return f"{os.getcwd()}\\{fileName}"


def isValidResourcesPath(args):
    """
    Валидация существования файлов таблиц Excel
    """
    pathes = [args.f_table, args.k_table, args.b_table, args.ch_table, args.input]

    for filePath in pathes:
        exist = os.path.exists(f"{getFullPath(filePath)}")
        if(exist == False):
            print(f"Не найден Excel файл по переданному пути: {filePath}")
            return False

        _, ext = os.path.splitext(filePath)
        if(ext != '.xlsx'):
            print("Расширение файла должно быть .xlsx")
            return False
    
    return True


# Точка входа приложения
if __name__ == '__main__':
    args = initArguments()
    isValidArgs = isValidResourcesPath(args)
    if(isValidArgs == False):
        exit()

    kExtractor = KExtractor(
        inputFilePath=getFullPath(args.input),
        fTableFilePath=getFullPath(args.f_table),
        kTableFilePath=getFullPath(args.k_table),
        bTableFilePath=getFullPath(args.b_table),
        chTableFilePath=getFullPath(args.ch_table),
    )

    # Шаг № 1
    kExtractor.createRoughLikenessTable()
    # Шаг № 2.1 и 2.2
    kExtractor.createSplittingUnNormTable()


# Строка запуска программы в консоли
# python App.py -f_table DataSets\Таблица_Ф_имен.xlsx -k_table DataSets\Таблица_К_имен_и_норм.xlsx -b_table DataSets\Таблица_В_временных_характеристик.xlsx -ch_table DataSets\Таблица_Ч_имен_и_числовых_норм.xlsx -input DataSets\Пример_исх_данных_для_ВГУ.xlsx
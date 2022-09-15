import pandas
from loguru import logger
import pathlib
import random


class KnowledgeExtractor:
    maxCategoryAttribute = ''
    maxNumberAttribute = ''
    # конструктор
    def __init__(self, inputFilePath: str,
                 fTableFilePath: str = ".\\DataSets\\Таблица_Ф_имен.xlsx",
                 kTableFilePath: str = ".\\DataSets\\Таблица_К_имен_и_норм.xlsx",
                 bTableFilePath: str = ".\\DataSets\\Таблица_В_временных_характеристик.xlsx",
                 chTableFilePath : str = ".\\DataSets\\Таблица_Ч_имен_и_числовых_норм.xlsx",
                 outputDirPath: str = "Output"):
        try:
            # запись данных Excel таблиц в поля класса
            self.inputData = self.__importData(inputFilePath)
            self.fNameTable = self.__importData(fTableFilePath)
            self.kNameAndNormTable = self.__importData(kTableFilePath)
            self.bTimeCharacteristicTable = self.__importData(bTableFilePath)
            self.chNameAndDigitNormTable = self.__importData(chTableFilePath)

            logger.info(f'Входные файлы успешно считаны')
        except BaseException as e:
            logger.exception(f'Во время чтения данных с файлов произошла ошибка. Exception: {e}')

        try:
            pathlib.Path(outputDirPath).mkdir(parents=True, exist_ok=True)
        except BaseException as e:
            logger.exception(f'Во время создания выходного каталога произошла ошибка. Exception: {e}')

        self.chNameAndDigitNorms = self.chNameAndDigitNormTable['Название'].values()
        self.kNamesAndNorms = self.kNameAndNormTable['Название'].values()
        logger.info(f'Названия полей категориальных и числовых норм считаны')
        # logger.debug(f"self.chNameAndDigitNormTable['Название'].values(): {self.chNameAndDigitNorms}")
        # logger.debug(f"self.kNameAndNormTable['Название'].values(): {self.kNamesAndNorms}")

        self.roughLikenessTable = []
        self.CategoriesClustersTable = []
        self.variantTable = []

    def createRoughLikenessTable(self, FillPercent: int = 40):
        """ Шаг № 1 - получение таблицы ROUGH LIKENESS """
        try:
            worksheetRow = 0
            worksheetColumn = 0
            validColumns = []
            roughLikenessData = []
            aviableColumns = [
                "БольЖив.Локализ",
                "Боль.Интенсивн",
                "Рвота.Характеристики",
                "Температура тела",
                "ВлажностьЯзыка",
                "Налет на языке",
                "ПрочиеЖКТжалобы",
                "Чувствит-ть при пальп",
                "Чувствит-ть.Локализ",
                "УЗИ-СтенкиЖП, мм",
                "Лечен.Эфф",
                "Гематокрит, %",
                "Лейкоциты, 10^9/л",
                "Состояние",
                "Билирубин общ, мкмоль/л",
                "Тошнота.Время",
            ]

            # отбор тех колонок у которых значений заполнено более 40% (переменная FillPercent)
            for col in aviableColumns:
                if col not in self.inputData.keys():
                    logger.warning(
                        f"Во входных данных не была найдена колонка: \"{col}\". Проверьте ее существование и корректность названия.")
                    continue

                columnData = self.inputData[col]
                isValid = self.__isFillInPercent(columnData.values(), FillPercent)
                if (isValid == True):
                    validColumns.append(col)

            # обработка колонок
            for validColumnName in validColumns:
                roughLikenessRow = {}
                outItemsKeys = []
                higherItemsKeys = []
                lowerItemsKeys = []

                if 'Название' not in self.kNameAndNormTable.keys():
                    logger.error(
                        f"Завершение работы. В таблице \"Таблица_К_имен_и_норм\" не была найдена колонка: \"Название\". Проверьте ее существование и корректность написания.")
                    return

                if 'Название' not in self.chNameAndDigitNormTable.keys():
                    logger.error(
                        f"Завершение работы. В таблице \"Таблица_Ч_имен_и_числовых_норм\" не была найдена колонка: \"Название\". Проверьте ее существование и корректность написания.")
                    return

                # если колонка есть в числовых характеристиках
                if validColumnName in self.chNameAndDigitNorms:
                    for index, currentValue in self.inputData[validColumnName].items():
                        key = [k for k, v in self.chNameAndDigitNormTable['Название'].items() if v == validColumnName][
                            0]
                        # logger.debug(f"validColumnName = {validColumnName}; index = {index}; currentValue = {currentValue}; key = {key}")
                        if 'Ниж гр нормы' not in self.chNameAndDigitNormTable.keys():
                            logger.error(
                                f"Завершение работы. В таблице \"Таблица_Ч_имен_и_числовых_норм\" не была найдена колонка: \"Ниж гр нормы\". Проверьте ее существование и корректность написания.")
                            return

                        if 'Верх гран нормы' not in self.chNameAndDigitNormTable.keys():
                            logger.error(
                                f"Завершение работы. В таблице \"Таблица_Ч_имен_и_числовых_норм\" не была найдена колонка: \"Верх гран нормы\". Проверьте ее существование и корректность написания.")
                            return

                        minValue = self.chNameAndDigitNormTable['Ниж гр нормы'][key]
                        maxValue = self.chNameAndDigitNormTable['Верх гран нормы'][key]

                        if not pandas.notna(minValue) or not pandas.notna(maxValue) or not pandas.notna(currentValue):
                            continue

                        if isinstance(currentValue, str) and 'нет' in currentValue.lower():
                            continue

                        currentValue = self.__validateDigitValue(currentValue)
                        minValue = self.__validateDigitValue(minValue)
                        maxValue = self.__validateDigitValue(maxValue)

                        if currentValue < minValue:
                            lowerItemsKeys.append(index + 2) # index == 0 это индекс в массиве, +2 что бы он стал как индекс в excel
                        elif currentValue > maxValue:
                            higherItemsKeys.append(index + 2)
                        else:
                            continue

                # если колонка есть в качественных характеристиках
                elif validColumnName in self.kNamesAndNorms:
                    for index, currentValue in self.inputData[validColumnName].items():
                        key = [k for k, v in self.kNameAndNormTable['Название'].items() if v == validColumnName][0]

                        if 'Норма (если есть)' not in self.kNameAndNormTable.keys():
                            logger.error(
                                f"Завершение работы. В таблице \"Таблица_К_имен_и_норм\" не была найдена колонка: \"Норма (если есть)\". Проверьте ее существование и корректность написания.")
                            return

                        normValue = self.kNameAndNormTable['Норма (если есть)'][key]

                        if not pandas.notna(normValue) or not pandas.notna(currentValue):
                            continue

                        if currentValue not in normValue:
                            outItemsKeys.append(
                                index + 2)  # index == 0 это индекс в массиве, +2 что бы он стал как индекс в excel
                        else:
                            continue

                # если нет ни в качественных ни в числовых характеристиках
                else:
                    continue

                # если что-то собрали
                if len(outItemsKeys) != 0 or len(higherItemsKeys) != 0 or len(lowerItemsKeys) != 0:
                    roughLikenessRow['ObsNm'] = validColumnName
                    roughLikenessRow['Out'] = ','.join(map(str, outItemsKeys)) or ''
                    roughLikenessRow['Q-Out'] = len(outItemsKeys) or ''
                    roughLikenessRow['Higher'] = ','.join(map(str, higherItemsKeys)) or ''
                    roughLikenessRow['Q-Higher'] = len(higherItemsKeys) or ''
                    roughLikenessRow['Lower'] = ','.join(map(str, lowerItemsKeys)) or ''
                    roughLikenessRow['Q-Lower'] = len(lowerItemsKeys) or ''
                    roughLikenessData.append(roughLikenessRow)

            self.__printTable(roughLikenessData)

            self.roughLikenessTable = roughLikenessData

            self.__listOfDictToExcel('Output\\RoughLikenessTable.xlsx', self.roughLikenessTable)

            logger.info(f'Таблица ROUGH LIKENESS успешно сформирована')
        except BaseException as e:
            logger.exception(f'Во время генерации таблицы ROUGH LIKENESS произошла ошибка. Exception: {e}')

    def createSplittingUnNormTable(self, firstPercentBorder: float = 0.02, secondPercentBorder: float = 0.5):
        global maxCategoryAttribute
        global maxNumberAttribute
        """ Шаг № 2 """
        # Находим наиболее рейтинговый признак
        rowMaxQOut, rowMaxNumOut, isQ_Higher = self.__getRowMaxQOut()

        if rowMaxQOut == {}:
            return

        if rowMaxQOut['ObsNm'] in self.kNamesAndNorms:  # Если признак качественный
            """ Шаг № 2.1 """
            try:
                CategoriesClustersData = []
                maxCategoryAttribute = rowMaxQOut['ObsNm']
                for nRowQQut in rowMaxQOut['Out'].split(','):  # Для каждой строки
                    categories = self.inputData[maxCategoryAttribute][int(nRowQQut) - 2]
                    # logger.debug(f"categories = {categories}")
                    for category in categories.split(','):  # Для каждого значения из перечня;
                        # изменил разделитель с ';' на ',' так как в исх данных не нашёл ни одного применения ';' в качестве разделителя между качественными значениями

                        if len(CategoriesClustersData) == 0:  # Если таблица пуста
                            self.__addRowCategoriesClustersData(CategoriesClustersData, category,
                                                                nRowQQut)  # Добавь значение

                        else:  # Иначе ищи среди существующих значений
                            isFind = False
                            for nCategoriesRow in range(len(CategoriesClustersData)):
                                if CategoriesClustersData[nCategoriesRow]["Val"] == category:  # Если нашел совпадение
                                    CategoriesClustersData[nCategoriesRow]["Out"] = CategoriesClustersData[nCategoriesRow]["Out"] + "," + nRowQQut  # Допиши номер строки
                                    CategoriesClustersData[nCategoriesRow]["Count"] += 1  # Увеличь счетчик
                                    isFind = True
                                    break
                            if not isFind:  # Если не нашел
                                self.__addRowCategoriesClustersData(CategoriesClustersData, category,
                                                                    nRowQQut)  # Добавь значение
                valCount = len(rowMaxQOut['Out'].split(','))
                for CategoriesClustersRow in CategoriesClustersData:  # Для каждого значения категории
                    CategoriesClustersRow["%"] = CategoriesClustersRow["Count"] / valCount * 100  # Рассчитай % вхождения в выборку

                self.__printTable(CategoriesClustersData)  # Выведи таблицу
                self.CategoriesClustersTable = CategoriesClustersData  # Сохрани таблицу
                self.__listOfDictToExcel('Output\\SplittingUnNormCategories.xlsx', self.CategoriesClustersTable)  # Выгрузи таблицу

                logger.info(f'Таблица SplittingUnNormCategories успешно сформирована (2.1)')
            except BaseException as e:
                logger.exception(f'Во время получения таблицы SplittingUnNormCategories произошла ошибка (2.1). Exception: {e}')

        if rowMaxNumOut == {}:
            return

        if rowMaxNumOut['ObsNm'] in self.chNameAndDigitNorms:  # Если признак числовой
            """ Шаг № 2.2 """
            try:
                NumbersClustersData = []
                validArray = []
                fstCatArray = []
                scndCatArray = []
                thrdCatArray = []
                borderValue = 0
                if firstPercentBorder >= secondPercentBorder:
                    raise Exception(f'firstPercentBorder ({firstPercentBorder}) должен быть меньше secondPercentBorder ({secondPercentBorder}).')

                maxNumberAttribute = rowMaxNumOut['ObsNm']

                if isQ_Higher:
                    validArray = rowMaxNumOut['Higher'].split(',')
                else:
                    validArray = rowMaxNumOut['Lower'].split(',')

                key = [k for k, v in self.chNameAndDigitNormTable['Название'].items() if v == maxNumberAttribute][0]

                borderValue = self.chNameAndDigitNormTable['Верх гран нормы'][key] \
                     if isQ_Higher \
                         else self.chNameAndDigitNormTable['Ниж гр нормы'][key]

                borderValue = self.__validateDigitValue(borderValue)
                # if len(lowerArray) > len(higherArray):
                #     validArray = lowerArray
                #     borderValue = self.chNameAndDigitNormTable['Ниж гр нормы'][key]
                # else:
                #     validArray = higherArray
                #     borderValue = self.chNameAndDigitNormTable['Верх гран нормы'][key]

                for elem in validArray:
                    number = self.inputData[maxNumberAttribute][int(elem) - 2]
                    if not pandas.notna(number):
                        continue

                    number = self.__validateDigitValue(number)

                    firstBorder = borderValue * firstPercentBorder
                    secondBorder = borderValue * secondPercentBorder

                    if isQ_Higher:
                        if number > borderValue and number <= borderValue + firstBorder:
                            fstCatArray.append(elem)  # Заменила number на elem
                        elif number > borderValue + firstBorder and number <= borderValue + secondBorder:
                            scndCatArray.append(elem)  # Заменила number на elem
                        elif number > borderValue + secondBorder:
                            thrdCatArray.append(elem)  # Заменила number на elem
                    else:
                        if number < borderValue and number >= borderValue - firstBorder:
                            fstCatArray.append(elem)
                        elif number < borderValue + firstBorder and number >= borderValue - secondBorder:
                            scndCatArray.append(elem)
                        elif number < borderValue - secondBorder:
                            thrdCatArray.append(elem)

                val = rowMaxNumOut['Q-Higher'] + rowMaxNumOut['Q-Lower']

                self.__createNumbersClustersData(NumbersClustersData, f'> Граница, но <= Граница + {firstPercentBorder*100}%', fstCatArray, val)
                self.__createNumbersClustersData(NumbersClustersData, f'> Граница + {firstPercentBorder*100}%, но <= Граница + {secondPercentBorder*100}%', scndCatArray, val)
                self.__createNumbersClustersData(NumbersClustersData, f'> Граница + {secondPercentBorder*100}%', thrdCatArray, val)

                self.__printTable(NumbersClustersData)

                self.NumbersClustersTable = NumbersClustersData
                self.__listOfDictToExcel('Output\\SplittingUnNormNumbersClusters.xlsx', NumbersClustersData)

                logger.info(f'Таблица SplittingUnNormNumbersClusters успешно сформирована (2.2)')
            except BaseException as e:
                logger.exception(f'Во время получения таблицы SplittingUnNormNumbersClusters произошла ошибка (2.2); Exception: {e}')

    def _generateVariantTable(self, ClusterTable, maxAttribute):
        cnt = 0
        cnt_out = 0
        cnt_high = 0
        cnt_low = 0
        variantRow = {'ObsNm': '',
                      'Clust-Val': '',
                      'Q-Val': '',
                      'list-Val': '',
                      'Q-Out': '',
                      'list-Out': '',
                      'Q-High': '',
                      'list-High': '',
                      'Q-Low': '',
                      'list-Low': ''}
        variantRowData = []
        # logger.debug(f"maxAttribute = {maxAttribute}")
        for row in ClusterTable:  # ДОДЕЛАТЬ чтобы работало с self.NumbersClustersTable:
            cnt += 1
            variantRow['ObsNm'] = maxAttribute  # сделать так, чтобы в соответствии с тем какая таблица
            # (NumbersClustersTable или CategoriesCluster) бралась maxAttribute
            # в пункте 2.2. доделать заполнение maxAttribute, как в 2.1.
            variantRow['Clust-Val'] = row['Val']
            variantRow['Q-Val'] = row['Count']
            variantRow['list-Val'] = row['Out']
            # logger.debug(f"variantRow = {variantRow}")
            variantRowData.append(variantRow)
            variantRow = {'ObsNm': '',
                          'Clust-Val': '',
                          'Q-Val': '',
                          'list-Val': '',
                          'Q-Out': '',
                          'list-Out': '',
                          'Q-High': '',
                          'list-High': '',
                          'Q-Low': '',
                          'list-Low': ''}

            # Для каждой строки в RoughLikenessTable
            for rowRLT in self.roughLikenessTable:  # row['Out'].split(','):
                cnt_out = 0
                cnt_high = 0
                cnt_low = 0

                # Проверка соответствия с таблицей roughLikenessTable
                if rowRLT['ObsNm'] != maxAttribute:
                    variantRow['ObsNm'] = rowRLT['ObsNm']

                    # logger.debug(f"variantRow = {variantRow}")
                    if rowRLT['Out']:
                        for index in rowRLT['Out'].split(','):
                            if index in row['Out'].split(','):
                                cnt_out += 1
                                variantRow['list-Out'] = variantRow['list-Out'] + index + ','
                                variantRow['Q-Out'] = cnt_out
                    # logger.debug(f"variantRow = {variantRow}")
                    if rowRLT['Higher']:
                        for index in rowRLT['Higher'].split(','):
                            if index in row['Out'].split(','):
                                cnt_high += 1
                                variantRow['list-High'] = variantRow['list-High'] + index + ','
                                variantRow['Q-High'] = cnt_high
                    # logger.debug(f"variantRow = {variantRow}")
                    if rowRLT['Lower']:
                        for index in rowRLT['Lower'].split(','):
                            if index in row['Out'].split(','):
                                cnt_low += 1
                                variantRow['list-Low'] = variantRow['list-Low'] + index + ','
                                variantRow['Q-Low'] = cnt_low
                    # logger.debug(f"variantRow = {variantRow}")
                    if cnt_out + cnt_high + cnt_low != 0:
                        variantRowData.append(variantRow)
                        # logger.debug(f"variantRow = {variantRow}")
                        variantRow = {'ObsNm': '',
                                      'Clust-Val': '',
                                      'Q-Val': '',
                                      'list-Val': '',
                                      'Q-Out': '',
                                      'list-Out': '',
                                      'Q-High': '',
                                      'list-High': '',
                                      'Q-Low': '',
                                      'list-Low': ''}

            self.variantTable.append(variantRowData)

            self.__printTable(variantRowData)
            self.__listOfDictToExcel(f'Output\\Variant{self.__cleanUpString(maxAttribute)}.{str(cnt)}.xlsx', variantRowData)
            logger.info(f'Таблица Variant{self.__cleanUpString(maxAttribute)}.{str(cnt)} успешно сформирована')
            variantRowData.clear()

    def createVariantTables(self):
        """ Шаг № 3 """
        global maxCategoryAttribute
        global maxNumberAttribute
        try:

            self._generateVariantTable(self.CategoriesClustersTable, maxCategoryAttribute)
            self._generateVariantTable(self.NumbersClustersTable, maxNumberAttribute)

            logger.info(f'Все таблицы Variant ({self.__cleanUpString(maxCategoryAttribute)}, {self.__cleanUpString(maxNumberAttribute)}) успешно сформированы')
        except BaseException as e:
            logger.exception(f'Во время получения таблицы Variant произошла ошибка (3); Exception: {e}')

    def __validateDigitValue(self, digit) -> float:
        if isinstance(digit, (str)):
            # Если значение строковое типа '3-4', то возвращаю наибольшее значение
            if '-' in digit:
                splitted = digit.split('-')
                return float(self.__validateDigitValue(splitted[0])) if float(
                    self.__validateDigitValue(splitted[0])) >= float(self.__validateDigitValue(splitted[1])) else float(
                    self.__validateDigitValue(splitted[1]))

            # Если значение строковое типа '3,5'
            elif ',' in digit:
                return float(digit.replace(',', '.'))

            # Если значение строковое типа '3'
            else:
                return float(digit)
        elif isinstance(digit, (int, float)):
            return float(digit)
        else:
            return float(digit)

    def __isFillInPercent(self, data, precent):
        allCount = len(data)
        isNullCount = self.__getNanValuesCount(data)
        precentCount = round(precent * allCount / 100)
        # не меннее precent заполнено
        return (allCount - isNullCount) > precentCount

    def __getNanValuesCount(self, data):
        nanCount = 0
        for item in data:
            if not pandas.notnull(item):
                nanCount += 1
        return nanCount

    def __listOfDictToExcel(self, filePath, data):
        output = pandas.DataFrame(data)
        output.to_excel(filePath, index=False)

    def __trimDictKeys(self, dictData: dict) -> dict:
        newDict = {}
        for dictKey, dictValues in dictData.items():
            newDict[dictKey.strip()] = dictValues

        return newDict

    def __importData(self, filePath: str) -> dict:
        data = pandas.read_excel(filePath).to_dict()
        resultDict = self.__trimDictKeys(data)
        return resultDict

    def __getRowMaxQOut(self):
        maxQOut = 0
        rowMaxQOut = {}

        maxNumOut = 0
        rowMaxNumOut = {}
        isQ_Higher = False
        for row in self.roughLikenessTable:

            # Для численных значений у которых Q-Out отсутствует
            if row['Q-Out'] == '':
                if row['Q-Lower'] == '':
                    qLower = 0
                    row['Q-Lower'] = qLower
                else:
                    qLower = row['Q-Lower']
                if row['Q-Higher'] == '':
                    qHigher = 0
                    row['Q-Higher'] = qHigher
                else:
                    qHigher = row['Q-Higher']
                qVal = qHigher if qHigher > qLower else qLower

                if int(qVal) > int(maxNumOut):
                    maxNumOut = qVal
                    rowMaxNumOut = row
                    isQ_Higher = qHigher > qLower

            # Для качественных значений у которых есть Q-Out
            elif row['Q-Out'] > maxQOut:
                maxQOut = row['Q-Out']
                rowMaxQOut = row

        return rowMaxQOut, rowMaxNumOut, isQ_Higher

    def __printTable(self, table):
        for nomRow in range(len(table)):
            print("{0}:{1}".format(nomRow, table[nomRow]))

    def __addRowCategoriesClustersData(self, CategoriesClustersData, categorie, nRowQQut):
        clustersRow = {"Val": categorie,
                       "Out": nRowQQut,
                       "Count": 1,
                       "%": 0, }
        CategoriesClustersData.append(clustersRow)
    def __cleanUpString(selfself, string_0: str):
        result = "".join(c for c in string_0 if c.isalpha())
        return result

    def __createNumbersClustersData(self, NumbersClustersData, val, array, precentVal):
        NumbersClustersData.append({
            'Val': val,
            'Out': ','.join(map(str, array)) or '',
            'Count': len(array),
            '%': round(len(array) / (precentVal) * 100, 2)
        })
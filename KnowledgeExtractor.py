import pandas

class KnowledgeExtractor:
    # конструктор
    def __init__(self, inputFilePath, fTableFilePath, kTableFilePath, bTableFilePath, chTableFilePath):
        # запись данных Excel таблиц в поля класса
        self.inputData = pandas.read_excel(inputFilePath, sheet_name="Первичный осмотр").to_dict()
        self.fNameTable = pandas.read_excel(fTableFilePath, sheet_name="Лист1").to_dict()
        self.kNameAndNormTable = pandas.read_excel(kTableFilePath, sheet_name="Лист1").to_dict()
        self.bTimeCharacteristicTable = pandas.read_excel(bTableFilePath, sheet_name="Лист1").to_dict()
        self.chNameAndDigitNormTable = pandas.read_excel(chTableFilePath, sheet_name="Лист1").to_dict()


    def createRoughLikenessTable(self):
        """
        Шаг № 1 - получение таблицы ROUGH LIKENESS
        """
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

        # отбор тех колонок у которых значений заполнено более 40%
        for col in aviableColumns:
            columnData = self.inputData[col]
            isValid = self.__isFillInPercent(columnData.values(), 40)
            if(isValid == True):
                validColumns.append(col)

        # обработка колонок
        for validColumnName in validColumns:
            roughLikenessRow = {}
            outItemsKeys = []
            higherItemsKeys = []
            lowerItemsKeys = []

            kNamesAndNorms = self.kNameAndNormTable['название'].values()
            chNameAndDigitNorms = self.chNameAndDigitNormTable['название'].values()

            # если колонка есть в числовых характеристиках
            if validColumnName in chNameAndDigitNorms:
                for index, currentValue in self.inputData[validColumnName].items():
                    key = [k for k, v in self.chNameAndDigitNormTable['название'].items() if v == validColumnName][0]
                    
                    minValue = self.chNameAndDigitNormTable['Ниж гр нормы'][key]
                    maxValue = self.chNameAndDigitNormTable['Верх гран нормы'][key]

                    if currentValue < minValue:
                        lowerItemsKeys.append(currentValue)
                    elif currentValue > minValue:
                        higherItemsKeys.append(currentValue)
                    else:
                        continue

            # если колонка есть в качественных характеристиках
            elif validColumnName in kNamesAndNorms:
                for index, currentValue in self.inputData[validColumnName].items():
                    key = [k for k, v in self.kNameAndNormTable['название'].items() if v == validColumnName][0]
                    normValue = self.kNameAndNormTable['Норма (если есть)'][key]
                    if not pandas.notnull(normValue):
                        continue

                    if currentValue not in normValue:
                        outItemsKeys.append(index + 2) # index == 0 это индекс в массиве, +2 что бы он стал как индекс в excel
                    else:
                        continue

            # если нет ни в качественных ни в числовых характеристиках
            else:
                continue

            if len(outItemsKeys) != 0 or len(higherItemsKeys) != 0 or len(lowerItemsKeys) != 0:
                roughLikenessRow['ObsNm'] = validColumnName
                roughLikenessRow['Out'] = ','.join(map(str, outItemsKeys)) or ''
                roughLikenessRow['Q-Out'] = len(outItemsKeys) or ''
                roughLikenessRow['Higher'] = ','.join(map(str, higherItemsKeys)) or ''
                roughLikenessRow['Q-Higher'] = len(higherItemsKeys) or ''
                roughLikenessRow['Lower'] = ','.join(map(str, lowerItemsKeys)) or ''
                roughLikenessRow['Q-Lower'] = len(lowerItemsKeys) or ''
                roughLikenessData.append(roughLikenessRow)

        print(roughLikenessData)
        self.roughLikenessTable = roughLikenessData
        self.__listOfDictToExcel('Output\\RoughLikenessTable.xlsx', roughLikenessData)
        
    

    def createSplittingUnNormTable(self):
        """
        Шаг № 2
        """
        #Находим наиболее рейтинговый признак  
        rowMaxQOut = self.__getRowMaxQOut()
        kNamesAndNorms = self.kNameAndNormTable['название'].values()
        chNameAndDigitNorms = self.chNameAndDigitNormTable['название'].values()
        if rowMaxQOut['ObsNm'] in kNamesAndNorms: #Если признак качественный
            """
            Шаг № 2.1
            """
            CategoriesClustersData = []
            for nRowQQut in rowMaxQOut['Out'].split(','):  #Для каждой строки
                categories = self.inputData[rowMaxQOut['ObsNm']][int(nRowQQut)-2]
                
                for categorie in categories.split(';'): #Для каждого значения из перечня

                    if len(CategoriesClustersData) == 0: #Если таблица пуста
                        self.__addRowCategoriesClustersData(CategoriesClustersData,categorie,nRowQQut) #Добавь значение

                    else:   #Иначе ищи среди существующих значений
                        isFind = False
                        for nCategoriesRow in range(len(CategoriesClustersData)):
                            if CategoriesClustersData[nCategoriesRow]["Val"] == categorie: #Если нашел совпадение
                                CategoriesClustersData[nCategoriesRow]["Out"] = CategoriesClustersData[nCategoriesRow]["Out"]+","+nRowQQut #Допиши номер строки
                                CategoriesClustersData[nCategoriesRow]["Count"] += 1 #Увеличь счетчик
                                isFind = True 
                                break
                        if not isFind: #Если не нашел
                            self.__addRowCategoriesClustersData(CategoriesClustersData,categorie,nRowQQut) #Добавь значение

            for CategoriesClustersRow in CategoriesClustersData: #Для каждого значения категории
                CategoriesClustersRow["%"] = CategoriesClustersRow["Count"]/len(rowMaxQOut['Out'].split(','))*100 #Рассчитай % вхождения в выборку

            self.__printTable(CategoriesClustersData) #Выведи таблицу
            self.CategoriesClustersTable = CategoriesClustersData #Сохрани таблицу
            self.__listOfDictToExcel('Output\\SplittingUnNormCategories.xlsx', CategoriesClustersData) #Выгрузи таблицу
        
        elif rowMaxQOut['ObsNm'] in chNameAndDigitNorms: #Если признак числовой
            """
            Шаг № 2.2
            """

    def __printTable(self,table):
        for nomRow in range(len(table)):
            print("{0}:{1}".format(nomRow,table[nomRow]))
 
    def __addRowCategoriesClustersData(self,CategoriesClustersData,categorie,nRowQQut):
        clustersRow = { "Val":categorie,
                        "Out":nRowQQut,
                        "Count":1,
                        "%":0,}
        CategoriesClustersData.append(clustersRow)
        
    def __getRowMaxQOut(self):
        maxQOut = 0
        rowMaxQOut = {}
        for row in self.roughLikenessTable:
            if row['Q-Out'] > maxQOut:
               maxQOut = row['Q-Out']
               rowMaxQOut = row
        return rowMaxQOut

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
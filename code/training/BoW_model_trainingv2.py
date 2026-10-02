import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from performance_stats import PerformanceStats
from pandas import read_csv

def main():
    BoWPath = 'BoWModel.pkl'
    vectorizerPath = 'vectorizer.pkl'
    DataPath = 'injection_detector_datasetv2.csv'

    #dataFrame1 = read_parquet(path=DataPath)

    #Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    #Combine it with your filename
    file_path = os.path.join(script_dir, DataPath)
    
    with open(file_path, 'rb') as f:
        dataFrame1 = read_csv(f)

    dataList = dataFrame1.values.tolist()

    sentenceList = []
    labelList = []

    #Select the column for text and subID (0 = not imperitive, 1 = benign imperitive, 2 = malicious)
    for entry in dataList:
        sentenceList.append(entry[0])
        labelList.append(entry[10])

    #Change all values greater than 1 into 1
    for index, value in enumerate(labelList):
        if value > 0:
            labelList[index] = 1

    print("Data Loading Complete")
    XTrain, XTest, YTrain, YTest = train_test_split(sentenceList, labelList, test_size=.2, random_state=10)

    #Set up vectorizer
    sentenceVectorizer = CountVectorizer()

    #Vectorize training set
    sentenceTrainingBag = sentenceVectorizer.fit_transform(XTrain)

    #Vectorize testing set
    sentenceTestingBag = sentenceVectorizer.transform(XTest)

    #Initialize model
    BoWModel = MultinomialNB()

    #Train model
    BoWModel.fit(sentenceTrainingBag,YTrain)

    #Predict on testing set
    testSetPredictions = BoWModel.predict(sentenceTestingBag)

    #Check accuracy
    BoWStats = PerformanceStats(YTest, testSetPredictions)
    BoWStats.confusion_matrix(filename="BoW_matrixv2.png")
    BoWStats.stats(filename="BoW_statsv2.txt")

    #Save BoW model to code/models/, where sanitizer/detect.py loads it from
    model_dir = os.path.join(os.path.dirname(script_dir), 'models')
    os.makedirs(model_dir, exist_ok=True)
    with open(os.path.join(model_dir, BoWPath), 'wb+') as f:
        pickle.dump(BoWModel, f)
    #Save Vectorizer
    with open(os.path.join(model_dir, vectorizerPath), 'wb+') as f:
            pickle.dump(sentenceVectorizer, f)

    print("Model Trained on Dataset V2")
    

if __name__ == "__main__":
    main()
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from performance_stats import PerformanceStats
from pandas import read_csv

def main():
    BoWPath = 'BoWModelMalicious.pkl'
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

    for entry in dataList:
        sentenceList.append(entry[0])
        labelList.append(entry[1])

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
    BoWStats.confusion_matrix(filename="BoW_matrix_maliciousv2.png")
    BoWStats.stats(filename="BoW_stats_maliciousv2.txt")

    #Save BoW model
    with open(os.path.join(script_dir, BoWPath), 'wb+') as f:
        pickle.dump(BoWModel, f)
    #Save Vectorizer
    with open(os.path.join(script_dir, vectorizerPath), 'wb+') as f:
            pickle.dump(sentenceVectorizer, f)

    print("Model Trained on Dataset V2")

if __name__ == "__main__":
    main()
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from performance_stats import PerformanceStats
from pandas import read_csv
import joblib

def main():
    path = 'RFModel.pkl'
    joblibPath = 'RFModelv2.joblib'
    DataPath = 'injection_detector_datasetv2.csv'
    NGramMin = 1
    NGramMax = 3

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

    NGramWordVectorizer = TfidfVectorizer(
        analyzer='word',
        ngram_range=(NGramMin, NGramMax)
        #consider turning on sublinear tf and comparing
        #sublinear_tf=True
    )

    NGramCharVectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(3,6)
    )

    
    RandomForestHolder = RandomForestClassifier(
        n_estimators=100

    )

    RandomForestModel = Pipeline([('tfidf', NGramWordVectorizer), ('classifier', RandomForestHolder)])

    RandomForestModel.fit(XTrain, YTrain)
    
    testSetPredictions = RandomForestModel.predict(XTest)

    #Check accuracy
    RFStats = PerformanceStats(YTest, testSetPredictions)
    RFStats.confusion_matrix(filename="RF_matrixv2.png")
    RFStats.stats(filename="RF_statsv2.txt")

    '''
    #Save model
    with open(os.path.join(script_dir, path), 'wb+') as f:
        pickle.dump(RandomForestModel, f)
    #Save Vectorizer
    with open(os.path.join(script_dir, vectorizerPath), 'wb+') as f:
        pickle.dump(NGramWordVectorizer, f)
    '''

    #pickle is annoying and finnicky. I want to use joblib and see if it helps.
    joblib.dump(RandomForestModel, joblibPath)

    print("Model Trained on Dataset V2")

if __name__ == "__main__":
    main()
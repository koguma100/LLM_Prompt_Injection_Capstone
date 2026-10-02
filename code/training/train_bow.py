# Train the Bag-of-Words sentence classifiers used by sanitizer/detection/bow.py. From the code/ directory run:
#     python training/train_bow.py                       # both models on dataset v2
#     python training/train_bow.py --dataset v1 --mode malicious
# Models are saved to code/models/, test-set stats and confusion matrices to code/results/.
import argparse
import os
import pickle

from pandas import read_csv
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

from sanitizer.config import MODELS_DIR
from sanitizer.detection.bow import IMPERATIVE_MODEL, MALICIOUS_MODEL
from sanitizer.metrics import PerformanceStats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "results")

# imperative: subtype_id (0 = not imperative, 1 = benign imperative, 2 = malicious), with every value > 0 treated as 1
# malicious: label (0 = benign, 1 = prompt injection)
MODES = {
    "imperative": (IMPERATIVE_MODEL, lambda df: (df["subtype_id"] > 0).astype(int)),
    "malicious": (MALICIOUS_MODEL, lambda df: df["label"]),
}


def train(dataFrame, mode, dataset):
    modelName, getLabels = MODES[mode]
    sentenceList = dataFrame["text"].tolist()
    labelList = getLabels(dataFrame).tolist()

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
    BoWModel.fit(sentenceTrainingBag, YTrain)

    #Predict on testing set
    testSetPredictions = BoWModel.predict(sentenceTestingBag)

    #Check accuracy
    BoWStats = PerformanceStats(YTest, testSetPredictions)
    BoWStats.confusion_matrix(filename=os.path.join(RESULTS_DIR, f"BoW_matrix_{mode}_{dataset}.png"))
    BoWStats.stats(filename=os.path.join(RESULTS_DIR, f"BoW_stats_{mode}_{dataset}.txt"))

    #Save BoW model and its vectorizer
    with open(os.path.join(MODELS_DIR, f"{modelName}.pkl"), 'wb') as f:
        pickle.dump(BoWModel, f)
    with open(os.path.join(MODELS_DIR, f"{modelName}_vectorizer.pkl"), 'wb') as f:
        pickle.dump(sentenceVectorizer, f)

    print(f"{mode} model trained on dataset {dataset}, saved to {MODELS_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Train the BoW sentence classifiers.")
    parser.add_argument("--dataset", choices=["v1", "v2"], default="v2",
                        help="training/injection_detector_dataset<version>.csv to train on (default: v2)")
    parser.add_argument("--mode", choices=["imperative", "malicious", "both"], default="both",
                        help="which model to train (default: both)")
    args = parser.parse_args()

    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    dataFrame = read_csv(os.path.join(SCRIPT_DIR, f"injection_detector_dataset{args.dataset}.csv"))
    print("Data Loading Complete")

    modes = ["imperative", "malicious"] if args.mode == "both" else [args.mode]
    for mode in modes:
        train(dataFrame, mode, args.dataset)


if __name__ == "__main__":
    main()

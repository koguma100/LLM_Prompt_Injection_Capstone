import pickle
import re
import joblib
import os

#4 Models. Best stats is RFModelv1.joblib. Malicious are unreliable.

testedModel = 'RFModelv1.joblib'

def detectSentence (stringDetect):

    #Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    model = joblib.load(os.path.join(script_dir, testedModel))

    #Leaving pickle loading here just in case
    #with open(os.path.join(script_dir, 'RFModel.pkl'), 'rb') as pickledModel:
        #model = pickle.load(pickledModel)
        
    results = []
    #simple sentence splitting. Definately want to make this more robust, but requires a more comprehensive NLP 
    sentences = re.split(r'(?<=[.!?])\s+', stringDetect)

    #OH MY GOD IM STUPID KILL PURGE PURGE PURGE  
    sentenceResults = model.predict(sentences)

    for sentence, result in zip(sentences, sentenceResults):
        if result == 1:
            results.append(sentence)

    return results

def main ():
    predictMe = input()
    detectedInjections = detectSentence(predictMe)
        #"Is this a piece of news regarding world politics, sports, business, or science and technology?\nMozilla To Add Support For XForms, World Yawns It's ironic that Microsoft could help further cement its dominance in the browser market by joining its largest rival in an effort to support web standards.  nbsp;At the same time, that act would go a long way towards improving the web in general for developers and users alike.")
    for injection in detectedInjections:
        print("Detected: " + injection + "\n")

if __name__ == "__main__":
    main()
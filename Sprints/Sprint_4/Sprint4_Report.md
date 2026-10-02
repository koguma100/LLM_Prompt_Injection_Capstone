# Sprint 4 Report (08/27/26 to 09/30/26)
## YouTube link of Sprint 4 Video 
https://youtu.be/8ucKQGb6slM

## What's New (User Facing)
* Addition of sanitization report in user interface
* Introduction of machine learning model to detect imperative statements
## Work Summary (Developer Facing)
* further sanitization testing
* improved labeled dataset for model training

## Unfinished Work
* imperative machine learning model needs refinement for better metrics (accuracy, recall, etc) 
* features need to be fully integrated into an intuitive user interface for final demo

## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:

## Incomplete Issues/User Stories
N/A
## Code Files for Review
Please review the following code files, which were actively developed during this
sprint, for quality:
* Data_Sanitization_Engine.py: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/7d9ca5fe3c89d1db82658a0edb453e68bd03cb1c/code/prototype/Data_Sanitization_Engine.py
* sanitize.py : https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/7d9ca5fe3c89d1db82658a0edb453e68bd03cb1c/code/prototype/sanitize.py
* base.html : https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/7d9ca5fe3c89d1db82658a0edb453e68bd03cb1c/code/flask-app/app/templates/base.html
* routes.py: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/7d9ca5fe3c89d1db82658a0edb453e68bd03cb1c/code/flask-app/app/routes.py
* api_call.py: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/7d9ca5fe3c89d1db82658a0edb453e68bd03cb1c/code/prototype/api_call.py
*prompt_hardening.py: https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/7d9ca5fe3c89d1db82658a0edb453e68bd03cb1c/code/prototype/prompt_hardening.py
*build_injection_dataset.py:
https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/dataset-generation/build_injection_dataset.py
*validate_injection_dataset.py:
https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/dataset-generation/validate_injection_dataset.py
*BoW_model_training_malicious_only_v1.py
https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/7d9ca5fe3c89d1db82658a0edb453e68bd03cb1c/code/machine-learning-suite/BoW_model_training_malicious_only_v1.py 
*BoW_model_training_malicious_only_v2.py
https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/7d9ca5fe3c89d1db82658a0edb453e68bd03cb1c/code/machine-learning-suite/BoW_model_training_malicious_only_v2.py 
*BoW_model_trainingv1.py
https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/7d9ca5fe3c89d1db82658a0edb453e68bd03cb1c/code/machine-learning-suite/BoW_model_trainingv1.py 
*BoW_model_trainingv2.py
https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/7d9ca5fe3c89d1db82658a0edb453e68bd03cb1c/code/machine-learning-suite/BoW_model_trainingv2.py 

## Retrospective Summary
Here's what went well:
* Team members all contributed 
* Client sprint demo went well
Here's what we'd like to improve:
* 
* The backend code is starting to get a little messy, and it’s coming time to clean up and refine how we use our modules.
* Create more sophisticated machine learning models for more accurate classification
Here are changes we plan to implement in the next sprint:
* Focusing on cleaning up/integrating disparate features
* More 




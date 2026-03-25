# Sprint 2 Report  2/22- 3/24

## Sprint 2 Video: https://www.youtube.com/watch?v=9AElb5QVHL0

## What's New (User Facing)
* Output validation 
* Obfuscation sanitation module 
* Regex updates
* Research poster finalized

## Work Summary (Developer Facing)
Our team created a final research poster that was accepted to the 2026 VICEROY Symposium which will be presented on April 14th. Our team also expanded the detection and sanitization step of our project by adding a module to detect and clean common obfuscation techniques, continued developing our regex patterns for prompt injection detection, and we also identified a major issue with how we were gathering performance statistics.

## Unfinished Work
Since our work this sprint revolved around creating better figures for accuracy of detection and sanitization, we still have features for our user interface and overall usability of our code we have to address. This includes developing features such as report generation for the UI, containerizing our code for ease of use through Docker, and continuing to research and develop sanitization techniques. 

## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:
* https://github.com/koguma100/LLM_Prompt_Injection_Capstone/issues/11
* https://github.com/koguma100/LLM_Prompt_Injection_Capstone/issues/16

## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint:
* https://github.com/koguma100/LLM_Prompt_Injection_Capstone/issues/17 - This feature was not completed due to time constraints from more important tasks.

## Code Files for Review
Please review the following code files, which were actively developed during this
sprint, for quality:
* Normalize_fuzzy.py - obfuscation module (https://github.com/koguma100/LLM_Prompt_Injection_Capstone/code/prototype/normalize/normalize_fuzzy.py)
* [test_normalize.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/code/prototype/normalize/test_normalize.py)  
* [Data_Sanitization_Engine](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/main/code/prototype/Data_Sanitization_Engine.py)  
*[prompt_hardening.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/output-validation/code/prototype/prompt_hardening.py)  
*[api_call.py](https://github.com/koguma100/LLM_Prompt_Injection_Capstone/blob/output-validation/code/prototype/api_call.py)  

## Retrospective Summary
Here's what went well:
* The prototype is coming together
* Key milestone completed – submitted the poster over Spring Break
* We’ve improved our dataset to be more realistic to the use case
* Touched base with client and ironed out miscommunication.
Here's what we'd like to improve:
* We believe that the regex recognition system can be further improved.
* Now that we’ve identified the issue with our testing sets and found a potentially better dataset  based on resumes, we’d like to implement it as our default test set..

Here are changes we plan to implement in the next sprint:
* Changed approach to detection (removing LLM classification feature)
* Creation of a Dockerfile for ease of development
* Finish connecting UI to backend
* Add report generation to UI


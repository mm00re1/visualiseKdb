# visualiseKdb
Demo displaying live and historical data from kdb with a flask api and a react frontend

# Setup Instructions
**Begin streaming dummy kdb data**

Start the kdb server, load in the q script, and set the timer

    >> q -p 5000
    KDB+ 4.0 2023.08.11 Copyright (C) 1993-2023 Kx Systems
    ...
    q)\l dataGeneration.q
    q)\t 100

**Setup the Flask Api**

Make a virtual python environment, activate it, install the required modules, and run app.py
    
    >> python -m venv venv
    >> ./venv/Scripts/activate
    >> pip install -r requirements.txt
    >> python app.py

**Launch Demo React Frontend**

In the frontend_react folder, run the first line below to install the necessary modules, and the second to launch the site locally

    >> npm install
    >> npm start

# visualiseKdb
Demo displaying live and historical data from kdb with a python/fastapi api and a react frontend
The main purpose and most valuable part of this repo is to show a worked example of using a python api to serve live kdb data over a websocket

# Setup Instructions
**Begin streaming dummy kdb data**

Start the kdb server

    >> q .\dataGeneration.q -p 5000 -t 100

**Setup the Python Api**

Make a virtual python environment, activate it, install the required modules, and run the api
    
    >> python -m venv venv
    >> ./venv/Scripts/activate
    >> pip install -r requirements.txt
    >> uvicorn main:app --workers 4

**Launch Demo React Frontend**

In the frontend_react folder, run the first line below to install the necessary modules, and the second to launch the site locally

    >> npm install
    >> npm start

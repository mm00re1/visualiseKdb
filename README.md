# visualiseKdb
Demo displaying live and historical data from kdb with a flask api and a react frontend

# Setup Instructions
**Begin streaming dummy kdb data**

Start the kdb server

    >> q .\dataGeneration.q -p 5000 -t 100

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

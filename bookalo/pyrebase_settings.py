import pyrebase
from pyrebase_config import config
firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()

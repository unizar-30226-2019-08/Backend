import pyrebase
config = {
    "apiKey": "AIzaSyDdIfkRbI2nbeYd080yulCjHglJN5S1aOQ",
    "authDomain": "bookalo-234418.firebaseapp.com",
    "databaseURL": "https://bookalo-234418.firebaseio.com",
    "storageBucket": "bookalo-234418.appspot.com",
}
firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()

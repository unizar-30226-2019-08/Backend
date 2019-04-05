import pyrebase
config = {
    "apiKey": "AIzaSyBj3cdsnqqdapIOjts02y8kRiiLsZg6ETY",
    "authDomain": "bookalo-234418.firebaseapp.com",
    "databaseURL": "https://bookalo-234418.firebaseio.com",
    "storageBucket": "bookalo-234418.appspot.com",
}
firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()

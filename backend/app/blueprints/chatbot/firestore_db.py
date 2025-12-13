import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("C:\\Users\\ASUS\\Documents\\GitHub\\IOT_AquaNova\\IoT_AquaNova\\serviceAccount.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def get_latest_reading():
    docs = (
        db.collection("readings")
        .order_by("ts", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )

    for doc in docs:
        return doc.to_dict()

    return None

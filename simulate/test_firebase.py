from firebase_admin_init import init_firebase

def main():
    db = init_firebase()
    doc_ref = db.collection("test").document("hello")
    doc_ref.set({"msg": "Xin chào AquaNova!"})
    print("OK: Ghi Firestore thành công. Kiểm tra collection 'test' trong Console.")

if __name__ == "__main__":
    main()

try:
    import face_recognition_models
    print("✅ Modèles trouvés !")
    import face_recognition
    print("✅ Face Recognition fonctionnel !")
except Exception as e:
    print(f"❌ Erreur : {e}")
from sqlalchemy.orm import Session
from app.models.utilisateurs import Utilisateur
from app.schemas.utilisateur import UserProfileUpdate, ChangePassword, ThemeUpdate
from app.core.securite import verify_password, hash_password
from fastapi import HTTPException, status

from fastapi import UploadFile
import shutil, os
from app.core.config import PROFILES_DIR

def get_user_profile(current_user: Utilisateur):
    return current_user


def get_user_theme(current_user: Utilisateur) -> dict:
    return {"theme": current_user.theme}


def update_user_theme(db: Session, current_user: Utilisateur, data: ThemeUpdate) -> dict:
    try:
        current_user.theme = data.theme
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        raise

    return {"theme": current_user.theme}

def update_user_profile(db: Session, current_user: Utilisateur, data: UserProfileUpdate):
    update_data = data.model_dump(exclude_unset=True)
    try:
        for key, value in update_data.items():
            setattr(current_user, key, value)
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        raise
    
    return current_user

def change_user_password(db: Session, current_user: Utilisateur, data: ChangePassword):
    if not verify_password(data.current_password, current_user.mot_de_passe_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe actuel est incorrect."
        )
    
    if data.new_password != data.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe et la confirmation ne correspondent pas."
        )
    if verify_password(data.new_password, current_user.mot_de_passe_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe ne peut pas être le même que l'ancien."
        )
    
    try:
        current_user.mot_de_passe_hash = hash_password(data.new_password)
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        raise
    
    return {"message": "Mot de passe mis à jour avec succès."}

def upload_profile_photo(db: Session, current_user: Utilisateur, file: UploadFile):
    # supprimer l'ancienne photo si elle existe (résolu par rapport au backend)
    if current_user.photo_profil:
        old_basename = os.path.basename(current_user.photo_profil)
        old_file = PROFILES_DIR / old_basename
        if old_file.exists():
            old_file.unlink()
            
    # Vérifier si le fichier est une image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier téléchargé n'est pas une image."
        )
    # recuperer l'extension du fichier
    
    extension = file.filename.split(".")[-1].lower()
    extension = os.path.splitext(file.filename)[1].lower().replace(".", "")
    allowed_extensions = ["jpg", "jpeg", "png","webp", "heic"]
    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension de fichier non autorisée. Les extensions autorisées sont : {', '.join(allowed_extensions)}."
        )
    
    # nom unique
    
    filename = f"user_{current_user.user_id}.{extension}"
    
    # Chemin physique sur le disque (résolu par rapport au backend)
    file_path = PROFILES_DIR / filename

    # Chemin qui sera enregistré en base (relatif au montage /uploads)
    db_path = f"/uploads/profiles/{filename}"

    # Créer le dossier si nécessaire
    os.makedirs(PROFILES_DIR, exist_ok=True)

    # Sauvegarder l'image
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    file.file.close()  # fermer le fichier après l'avoir utilisé
    
    # Mettre à jour la base
    try:
        current_user.photo_profil = db_path
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        raise
    
    return {"message": "Photo de profil mise à jour avec succès.", "photo_profil": db_path}

# main.py - Munir Face Recognition Backend (PRODUCTION READY)
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
from insightface.app import FaceAnalysis
from PIL import Image
import io
import logging
from typing import List, Optional
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime
import uuid
import os
import json

# ============================================================
# Logging Setup
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# FastAPI App
# ============================================================
app = FastAPI(
    title="Munir Face Recognition API",
    version="3.4.0",
    description="Production-ready Face Recognition API using InsightFace + Firebase"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Firebase Setup
# ============================================================
def initialize_firebase():
    global db, bucket
    try:
        try:
            firebase_admin.get_app()
            logger.info("🔄 Firebase already initialized")
            return
        except ValueError:
            pass
        
        logger.info("🔄 Initializing Firebase...")
        
        firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
        
        if firebase_creds_json:
            logger.info(f"✅ FIREBASE_CREDENTIALS found: {len(firebase_creds_json)} characters")
            logger.info(f"✅ First 50 chars: {firebase_creds_json[:50]}...")
            logger.info("✅ Loading Firebase credentials from environment variable")
            try:
                cred_dict = json.loads(firebase_creds_json)
                logger.info(f"✅ JSON parsed successfully")
                logger.info(f"✅ Project ID: {cred_dict.get('project_id', 'NOT FOUND')}")
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError as je:
                logger.error(f"❌ JSON parsing error: {je}")
                raise
        else:
            logger.error("❌ FIREBASE_CREDENTIALS environment variable NOT FOUND!")
            logger.info("📝 Available env vars: " + ", ".join([k for k in os.environ.keys() if 'FIRE' in k.upper()]))
            logger.info("✅ Attempting to load from file...")
            cred = credentials.Certificate('firebase-credentials.json')
        
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'munir-21f4a.firebasestorage.app'
        })
        
        db = firestore.client()
        bucket = storage.bucket()
        
        logger.info("✅ Firebase connected successfully")
        logger.info(f"📦 Storage Bucket: munir-21f4a.firebasestorage.app")
        
    except Exception as e:
        logger.error(f"❌ Firebase connection error: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        db = None
        bucket = None

# Initialize Firebase
db = None
bucket = None
initialize_firebase()

# ============================================================
# InsightFace Model
# ============================================================
logger.info("⏳ Loading InsightFace model...")
try:
    face_app = FaceAnalysis(
        name='buffalo_sc',
        providers=['CPUExecutionProvider']
    )
    face_app.prepare(ctx_id=0, det_size=(320, 320))
    logger.info("✅ InsightFace model loaded successfully!")
except Exception as e:
    logger.error(f"❌ InsightFace loading failed: {e}")
    face_app = None

# ============================================================
# Helper Functions
# ============================================================

def read_image(image_bytes: bytes) -> np.ndarray:
    """Convert image bytes to OpenCV format"""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    except Exception as e:
        raise ValueError(f"Failed to read image: {str(e)}")

def extract_embedding(image: np.ndarray):
    """Extract face embedding from image - single face only"""
    try:
        faces = face_app.get(image)
        
        if len(faces) == 0:
            return None, "No face detected in image"
        
        if len(faces) > 1:
            faces = sorted(
                faces,
                key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]),
                reverse=True
            )
            logger.warning(f"Multiple faces detected ({len(faces)}), using largest")
        
        embedding = faces[0].embedding
        embedding = embedding / np.linalg.norm(embedding)
        return embedding, None
        
    except Exception as e:
        return None, f"Embedding extraction failed: {str(e)}"

def extract_all_embeddings(image: np.ndarray):
    """
    Extract embeddings for ALL faces in an image.
    Returns list of (embedding, bbox) tuples.
    """
    try:
        faces = face_app.get(image)
        
        if len(faces) == 0:
            return []
        
        results = []
        for face in faces:
            emb = face.embedding
            emb = emb / np.linalg.norm(emb)
            bbox = [float(v) for v in face.bbox]  # [x1, y1, x2, y2]
            results.append((emb, bbox))
        
        logger.info(f"👥 Detected {len(results)} face(s) in image")
        return results
        
    except Exception as e:
        logger.error(f"Embedding extraction failed: {e}")
        return []

def cosine_similarity(emb1, emb2):
    """Calculate cosine similarity between two embeddings"""
    return float(np.dot(emb1, emb2))

def find_match(query_emb, user_id):
    """Find matching person in database for a single embedding"""
    try:
        persons = db.collection('users').document(user_id).collection('persons').stream()
        best_match = None
        best_score = -1
        
        for person in persons:
            data = person.to_dict()
            
            flat_embeddings = data.get('embeddings_flat', [])
            embedding_dim = data.get('embedding_dim', 512)
            num_embeddings = data.get('num_embeddings', 0)
            
            if not flat_embeddings or num_embeddings == 0:
                continue
            
            for i in range(num_embeddings):
                start = i * embedding_dim
                end = start + embedding_dim
                stored_emb = flat_embeddings[start:end]
                
                if len(stored_emb) != embedding_dim:
                    continue
                
                stored_emb = np.array(stored_emb)
                stored_emb = stored_emb / np.linalg.norm(stored_emb)
                score = cosine_similarity(query_emb, stored_emb)
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        "person_id": person.id,
                        "person_name": data.get('name'),
                        "score": score
                    }
        
        return best_match, best_score
        
    except Exception as e:
        logger.error(f"Error in find_match: {e}")
        return None, -1

def get_all_persons_embeddings(user_id):
    """
    Load all persons and their embeddings from Firebase once.
    Used for multi-face recognition to avoid repeated DB calls.
    Returns list of dicts with person info + embeddings.
    """
    try:
        persons = db.collection('users').document(user_id).collection('persons').stream()
        all_persons = []
        
        for person in persons:
            data = person.to_dict()
            flat_embeddings = data.get('embeddings_flat', [])
            embedding_dim = data.get('embedding_dim', 512)
            num_embeddings = data.get('num_embeddings', 0)
            
            if not flat_embeddings or num_embeddings == 0:
                continue
            
            # Parse embeddings
            embeddings = []
            for i in range(num_embeddings):
                start = i * embedding_dim
                end = start + embedding_dim
                stored_emb = flat_embeddings[start:end]
                if len(stored_emb) == embedding_dim:
                    stored_emb = np.array(stored_emb)
                    stored_emb = stored_emb / np.linalg.norm(stored_emb)
                    embeddings.append(stored_emb)
            
            if embeddings:
                all_persons.append({
                    "person_id": person.id,
                    "person_name": data.get('name'),
                    "embeddings": embeddings
                })
        
        return all_persons
        
    except Exception as e:
        logger.error(f"Error loading persons embeddings: {e}")
        return []

def find_match_from_persons(query_emb, all_persons):
    """
    Find best match for a single embedding from pre-loaded persons list.
    Much faster than querying DB each time.
    """
    best_match = None
    best_score = -1
    
    for person in all_persons:
        for stored_emb in person['embeddings']:
            score = cosine_similarity(query_emb, stored_emb)
            if score > best_score:
                best_score = score
                best_match = {
                    "person_id": person['person_id'],
                    "person_name": person['person_name'],
                }
    
    return best_match, best_score

# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "api": "Munir Face Recognition API",
        "version": "3.4.0",
        "status": "running",
        "environment": os.environ.get('ENVIRONMENT', 'production'),
        "insightface": "loaded" if face_app else "not loaded",
        "firebase": "connected" if db else "not connected",
        "encryption": "AES-256-CBC (End-to-End)",
        "storage_bucket": "munir-21f4a.firebasestorage.app",
        "storage_mode": "ENCRYPTED - Images stored encrypted"
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    is_healthy = face_app is not None and db is not None
    
    if not is_healthy:
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    return {
        "status": "healthy",
        "insightface": True,
        "firebase": True,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# NEW: Verify Same Person
# ============================================================

@app.post("/verify_same_person")
async def verify_same_person(
    files: List[UploadFile] = File(...)
):
    """
    Check if all uploaded images belong to the same person.
    Used during enrollment to validate photos before saving.
    Requires at least 2 images.
    """
    try:
        if not face_app:
            raise HTTPException(503, "Service not ready")

        if len(files) < 2:
            raise HTTPException(400, "Need at least 2 images to compare")

        logger.info("=" * 60)
        logger.info(f"🔍 Verify same person — {len(files)} images received")

        embeddings = []

        for idx, file in enumerate(files):
            try:
                img_bytes = await file.read()
                img = read_image(img_bytes)
                emb, error = extract_embedding(img)

                if emb is None:
                    logger.warning(f"  ⚠️ Image {idx + 1}: {error}")
                    return {
                        "success": False,
                        "same_person": False,
                        "message": f"No face detected in image {idx + 1}",
                        "image_index": idx
                    }

                embeddings.append(emb)
                logger.info(f"  ✅ Image {idx + 1}: Embedding extracted")

            except Exception as e:
                logger.error(f"  ❌ Image {idx + 1}: {e}")
                return {
                    "success": False,
                    "same_person": False,
                    "message": f"Error processing image {idx + 1}: {str(e)}",
                    "image_index": idx
                }

        # حساب cosine similarity بين كل الأزواج
        scores = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                score = cosine_similarity(embeddings[i], embeddings[j])
                scores.append(score)
                logger.info(f"  📊 Image {i + 1} vs Image {j + 1}: {score:.4f}")

        avg_score = sum(scores) / len(scores)
        min_score = min(scores)

        # threshold واقعي لـ InsightFace مع زوايا مختلفة (أمام/يمين/يسار)
        # buffalo_sc أقل دقة من buffalo_l لذا نخفف الـ threshold شوي
        THRESHOLD = 0.30

        same_person = min_score >= THRESHOLD

        logger.info(f"  📊 Avg Score: {avg_score:.4f} | Min Score: {min_score:.4f}")
        logger.info(f"  {'✅ Same person' if same_person else '❌ Different persons'}")
        logger.info("=" * 60)

        return {
            "success": True,
            "same_person": same_person,
            "average_score": round(avg_score, 4),
            "min_score": round(min_score, 4),
            "num_images": len(files),
            "message": "Same person confirmed" if same_person else "Photos appear to be different persons"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Verify same person error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Verification failed: {str(e)}")

# ============================================================
# Enroll Person
# ============================================================

@app.post("/enroll_person")
async def enroll_person(
    name: str = Form(...),
    user_id: str = Form(...),
    files: List[UploadFile] = File(...),
    encrypted_thumbnail: Optional[UploadFile] = File(None),
    person_id: Optional[str] = Form(None)
):
    """Enroll a new person with multiple face images (or update existing person)"""
    try:
        if not face_app or not db:
            raise HTTPException(503, "Service not ready")
        
        if len(files) < 3:
            raise HTTPException(400, f"Need at least 3 images, got {len(files)}")
        
        is_update = person_id is not None
        
        if not person_id:
            person_id = f"{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        
        logger.info("=" * 60)
        if is_update:
            logger.info(f"🔄 Updating: {name} (Person ID: {person_id}, User: {user_id})")
        else:
            logger.info(f"📝 Enrolling: {name} (User: {user_id})")
        logger.info("=" * 60)
        
        embeddings = []
        success_count = 0
        failed_count = 0
        
        logger.info(f"📸 Processing {len(files)} images...")
        
        for idx, file in enumerate(files):
            try:
                img_bytes = await file.read()
                img = read_image(img_bytes)
                emb, error = extract_embedding(img)
                
                if emb is not None:
                    embeddings.append(emb.tolist())
                    success_count += 1
                    logger.info(f"  ✅ Image {idx + 1}: Face detected")
                else:
                    failed_count += 1
                    logger.warning(f"  ⚠️ Image {idx + 1}: {error}")
            except Exception as e:
                failed_count += 1
                logger.warning(f"  ❌ Image {idx + 1}: Error - {e}")
                continue
        
        if len(embeddings) < 3:
            raise HTTPException(400, f"Only {len(embeddings)} valid faces found, need at least 3")
        
        flattened_embeddings = []
        for emb in embeddings:
            flattened_embeddings.extend(emb)
        
        person_data = {
            'name': name,
            'embeddings_flat': flattened_embeddings,
            'embedding_dim': 512,
            'num_embeddings': len(embeddings),
            'num_angles': len(embeddings),
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        if not is_update:
            person_data['created_at'] = firestore.SERVER_TIMESTAMP
        
        thumbnail_url = None
        if encrypted_thumbnail:
            try:
                logger.info("🔐 Uploading ENCRYPTED thumbnail...")
                encrypted_bytes = await encrypted_thumbnail.read()
                logger.info(f"📥 Received encrypted file: {len(encrypted_bytes)} bytes")
                
                blob = bucket.blob(f"users/{user_id}/thumbnails/{person_id}.enc")
                blob.upload_from_string(encrypted_bytes, content_type='application/octet-stream')
                blob.make_public()
                thumbnail_url = blob.public_url
                person_data['thumbnail_url'] = thumbnail_url
                
                logger.info(f"✅ Encrypted thumbnail uploaded!")
                
            except Exception as e:
                logger.warning(f"⚠️ Thumbnail upload failed: {e}")
        
        db.collection('users').document(user_id).collection('persons').document(person_id).set(
            person_data,
            merge=True
        )
        
        logger.info("=" * 60)
        if is_update:
            logger.info(f"✅ Successfully updated {name}!")
        else:
            logger.info(f"✅ Successfully enrolled {name}!")
        logger.info(f"   Person ID: {person_id}")
        logger.info(f"   Embeddings: {success_count}/{len(files)} images")
        logger.info(f"   Thumbnail: {'✅ Yes (ENCRYPTED)' if thumbnail_url else '❌ No'}")
        logger.info("=" * 60)
        
        return {
            "success": True,
            "message": f"Successfully {'updated' if is_update else 'enrolled'} {name}",
            "person_id": person_id,
            "person_name": name,
            "total_embeddings": len(embeddings),
            "successful_images": success_count,
            "failed_images": failed_count,
            "thumbnail_url": thumbnail_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Enrollment error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Enrollment failed: {str(e)}")

# ============================================================
# Recognize Single Face
# ============================================================

@app.post("/recognize")
async def recognize(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Recognize a single face in an image"""
    try:
        if not face_app or not db:
            raise HTTPException(503, "Service not ready")
        
        img_bytes = await file.read()
        img = read_image(img_bytes)
        query_emb, error = extract_embedding(img)
        
        if error:
            raise HTTPException(400, error)
        
        match, score = find_match(query_emb, user_id)
        
        THRESHOLD = 0.40
        
        if match and score >= THRESHOLD:
            logger.info(f"✅ Recognized: {match['person_name']} (score: {score:.3f})")
            return {
                "success": True,
                "recognized": True,
                "person_name": match["person_name"],
                "person_id": match["person_id"],
                "confidence": round(score, 4),
                "similarity_score": round(score * 100, 2),
                "message": f"Welcome {match['person_name']}!"
            }
        else:
            logger.info(f"❌ Unknown person (best score: {score:.3f})")
            return {
                "success": True,
                "recognized": False,
                "message": "Unknown person",
                "confidence": round(score, 4) if match else 0.0,
                "similarity_score": round(score * 100, 2) if match else 0.0
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Recognition error: {e}")
        raise HTTPException(500, f"Recognition failed: {str(e)}")

# ============================================================
# Recognize Multiple Faces
# ============================================================

@app.post("/recognize_multiple")
async def recognize_multiple(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Recognize ALL faces in a single image.
    Returns a list with a result for each detected face.
    """
    try:
        if not face_app or not db:
            raise HTTPException(503, "Service not ready")
        
        logger.info("=" * 60)
        logger.info(f"👥 Multi-face recognition request (User: {user_id})")
        
        img_bytes = await file.read()
        img = read_image(img_bytes)
        
        faces_data = extract_all_embeddings(img)
        
        if not faces_data:
            logger.info("⚠️ No faces detected in image")
            return {
                "success": True,
                "total_faces": 0,
                "recognized_count": 0,
                "faces": [],
                "message": "No faces detected in image"
            }
        
        logger.info(f"👥 Found {len(faces_data)} face(s), starting recognition...")
        
        all_persons = get_all_persons_embeddings(user_id)
        logger.info(f"📂 Loaded {len(all_persons)} enrolled person(s) from DB")
        
        THRESHOLD = 0.40
        results = []
        recognized_count = 0
        
        for idx, (emb, bbox) in enumerate(faces_data):
            logger.info(f"  🔍 Processing face {idx + 1}/{len(faces_data)}...")
            
            if not all_persons:
                results.append({
                    "face_index": idx,
                    "success": True,
                    "recognized": False,
                    "person_name": None,
                    "person_id": None,
                    "confidence": 0.0,
                    "similarity_score": 0.0,
                    "bbox": bbox,
                    "message": "No enrolled persons found"
                })
                continue
            
            match, score = find_match_from_persons(emb, all_persons)
            
            if match and score >= THRESHOLD:
                recognized_count += 1
                logger.info(f"  ✅ Face {idx + 1}: Recognized as {match['person_name']} (score: {score:.3f})")
                results.append({
                    "face_index": idx,
                    "success": True,
                    "recognized": True,
                    "person_name": match["person_name"],
                    "person_id": match["person_id"],
                    "confidence": round(score, 4),
                    "similarity_score": round(score * 100, 2),
                    "bbox": bbox,
                    "message": f"Recognized: {match['person_name']}"
                })
            else:
                logger.info(f"  ❌ Face {idx + 1}: Unknown (best score: {score:.3f})")
                results.append({
                    "face_index": idx,
                    "success": True,
                    "recognized": False,
                    "person_name": None,
                    "person_id": None,
                    "confidence": round(score, 4) if match else 0.0,
                    "similarity_score": round(score * 100, 2) if match else 0.0,
                    "bbox": bbox,
                    "message": "Unknown person"
                })
        
        logger.info(f"✅ Done: {recognized_count}/{len(faces_data)} face(s) recognized")
        logger.info("=" * 60)
        
        return {
            "success": True,
            "total_faces": len(faces_data),
            "recognized_count": recognized_count,
            "faces": results,
            "message": f"Detected {len(faces_data)} face(s), recognized {recognized_count}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Multi-face recognition error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Multi-face recognition failed: {str(e)}")

# ============================================================
# List / Update / Delete Persons
# ============================================================

@app.get("/list_persons/{user_id}")
def list_persons(user_id: str):
    """Get list of all enrolled persons for a user"""
    try:
        persons_ref = db.collection('users').document(user_id).collection('persons')
        persons = persons_ref.stream()
        
        result = []
        for p in persons:
            data = p.to_dict()
            result.append({
                "person_id": p.id,
                "name": data.get('name', 'Unknown'),
                "num_photos": data.get('num_embeddings', 0),
                "thumbnail_url": data.get('thumbnail_url', None)
            })
        
        result.sort(key=lambda x: x['name'].lower())
        
        logger.info(f"📋 Listed {len(result)} persons for user {user_id}")
        
        return {
            "success": True,
            "persons": result,
            "count": len(result)
        }
        
    except Exception as e:
        logger.error(f"❌ List persons error: {e}")
        raise HTTPException(500, f"Failed to list persons: {str(e)}")

@app.put("/update_person/{user_id}/{person_id}")
async def update_person(
    user_id: str,
    person_id: str,
    name: str = Form(...)
):
    """Update person's name"""
    try:
        if not db:
            raise HTTPException(503, "Service not ready")

        ref = db.collection('users').document(user_id).collection('persons').document(person_id)
        doc = ref.get()

        if not doc.exists:
            raise HTTPException(404, f"Person {person_id} not found")

        ref.update({
            'name': name,
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        logger.info(f"✅ Updated name for {person_id} → {name}")

        return {
            "success": True,
            "message": f"Successfully updated name to {name}",
            "person_id": person_id,
            "new_name": name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update person error: {e}")
        raise HTTPException(500, f"Failed to update person: {str(e)}")

@app.delete("/delete_person/{user_id}/{person_id}")
def delete_person(user_id: str, person_id: str):
    """Delete a person and their data"""
    try:
        ref = db.collection('users').document(user_id).collection('persons').document(person_id)
        doc = ref.get()
        
        if not doc.exists:
            raise HTTPException(404, f"Person {person_id} not found")
        
        data = doc.to_dict()
        name = data.get('name', 'Unknown')
        
        if 'thumbnail_url' in data and data['thumbnail_url']:
            try:
                blob = bucket.blob(f"users/{user_id}/thumbnails/{person_id}.enc")
                if blob.exists():
                    blob.delete()
                    logger.info(f"  🗑️ Deleted encrypted thumbnail for {name}")
            except Exception as e:
                logger.warning(f"  ⚠️ Failed to delete thumbnail: {e}")
        
        ref.delete()
        
        logger.info(f"✅ Deleted person: {name} ({person_id})")
        
        return {
            "success": True,
            "message": f"Successfully deleted {name}",
            "person_id": person_id,
            "person_name": name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete person error: {e}")
        raise HTTPException(500, f"Failed to delete person: {str(e)}")

# ============================================================
# Startup Event
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info("🚀 Munir Face Recognition API Started!")
    logger.info(f"   Environment: {os.environ.get('ENVIRONMENT', 'production')}")
    logger.info(f"   Version: 3.4.0")
    logger.info(f"   InsightFace: {'✅ Loaded' if face_app else '❌ Not Loaded'}")
    logger.info(f"   Firebase: {'✅ Connected' if db else '❌ Not Connected'}")
    logger.info("=" * 60)

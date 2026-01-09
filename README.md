# Munir Face Recognition API

Production-ready Face Recognition API using InsightFace and Firebase.

## Features

- 🔐 **End-to-End Encryption**: Images stored encrypted in Firebase Storage
- 🎯 **High Accuracy**: Using InsightFace buffalo_l model
- ☁️ **Cloud-Ready**: Deployable to Railway, Render, or any Docker platform
- 🔥 **Firebase Integration**: Firestore for metadata, Storage for encrypted images
- 📱 **Mobile-Friendly**: Designed for Munir assistive technology app

## API Endpoints

### Health Check
```
GET /health
```

### Recognize Face
```
POST /recognize
Content-Type: multipart/form-data

Parameters:
- user_id: string
- file: image file
```

### Enroll Person
```
POST /enroll_person
Content-Type: multipart/form-data

Parameters:
- name: string
- user_id: string
- files: list of image files (minimum 3)
- encrypted_thumbnail: encrypted image file (optional)
```

### List Persons
```
GET /list_persons/{user_id}
```

### Delete Person
```
DELETE /delete_person/{user_id}/{person_id}
```

## Local Development

### Prerequisites
- Python 3.10+
- Firebase project credentials

### Setup

1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/munir-api.git
cd munir-api
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Add Firebase credentials
```bash
# Create firebase-credentials.json with your credentials
```

5. Run the server
```bash
python main.py
# or
uvicorn main:app --reload --port 8000
```

6. Test the API
```bash
curl http://localhost:8000/health
```

## Deployment

### Railway

1. Create Railway account at https://railway.app

2. Create new project from GitHub repo

3. Add environment variable:
```
FIREBASE_CREDENTIALS = {paste your Firebase credentials JSON}
```

4. Deploy! Railway will automatically detect Dockerfile

5. Get your API URL:
```
https://munir-api-production.up.railway.app
```

### Render

1. Create Render account at https://render.com

2. Create new Web Service from GitHub repo

3. Add environment variable in Dashboard:
```
FIREBASE_CREDENTIALS = {paste your Firebase credentials JSON}
```

4. Deploy!

5. Get your API URL:
```
https://munir-api.onrender.com
```

## Environment Variables

Required:
- `FIREBASE_CREDENTIALS`: Firebase service account JSON (as string)

Optional:
- `PORT`: Server port (default: 8000)
- `RECOGNITION_THRESHOLD`: Face matching threshold (default: 0.40)
- `MIN_ENROLLMENT_IMAGES`: Minimum images for enrollment (default: 3)
- `ENVIRONMENT`: Environment name (default: production)

## Flutter App Integration

Update your Flutter app's API URL:

```dart
// lib/services/face_recognition_api.dart
class FaceRecognitionAPI {
  static const String BASE_URL = "https://munir-api-production.up.railway.app";
  
  // الباقي نفسه!
}
```

## Security Notes

⚠️ **IMPORTANT**:
- Never commit `firebase-credentials.json` to Git
- Always use environment variables for credentials in production
- Images are stored encrypted in Firebase Storage
- API uses CORS - configure allowed origins for production

## Performance

- **Cold Start**: ~30-60 seconds (first request after idle)
- **Recognition**: ~500ms - 1.5s per image
- **Enrollment**: ~2-5s for 5 images
- **Concurrent Users**: Supports 10-50 concurrent requests (depends on server resources)

## Cost Estimation

### Free Tier (Railway)
- $5 credit monthly = ~500 hours
- Perfect for academic projects and demos

### Free Tier (Render)
- Completely free
- Server sleeps after 15 min of inactivity
- 30-60s cold start time

### Paid (Production)
- Railway: $5/month (Hobby plan)
- Render: $7/month (Starter plan)
- Firebase: Free tier sufficient for small-medium usage

## Troubleshooting

### Model Loading Issues
```bash
# Pre-download InsightFace model
python -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='buffalo_l'); app.prepare(ctx_id=0)"
```

### Memory Issues
- Reduce `det_size` in model configuration
- Use lighter model (buffalo_s instead of buffalo_l)

### Slow Recognition
- Optimize image size before upload
- Use GPU provider if available
- Implement caching for embeddings

## License

This project is part of Munir assistive technology system.
For academic and research purposes.

## Contact

For support: [Your Email]
Project: Munir - AI-Powered Assistive Technology

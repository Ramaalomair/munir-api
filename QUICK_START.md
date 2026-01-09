# ⚡ Quick Start Guide - نشر سريع في 10 دقائق

## الخطوات السريعة:

### 1️⃣ تجهيز Firebase (دقيقة واحدة)

```bash
# حوّل firebase credentials لـ string
cat firebase-credentials.json | tr -d '\n' | tr -d ' ' > firebase-oneline.txt

# انسخ المحتوى
cat firebase-oneline.txt
# احفظه في مكان آمن - بنحتاجه!
```

### 2️⃣ رفع على GitHub (دقيقتين)

```bash
# في مجلد المشروع
git init
git add .
git commit -m "Munir API v1.0"

# إنشاء repo على GitHub، ثم:
git remote add origin https://github.com/YOUR_USERNAME/munir-api.git
git push -u origin main
```

### 3️⃣ Deploy على Railway (5 دقائق)

1. روح https://railway.app
2. Login with GitHub
3. "Deploy from GitHub" → اختر munir-api
4. Variables → Add:
   ```
   FIREBASE_CREDENTIALS = {الصق المحتوى من الخطوة 1}
   ```
5. انتظر الـ deployment (2-3 دقائق)
6. انسخ الـ URL: `https://munir-api-production.up.railway.app`

### 4️⃣ تحديث Flutter (دقيقة واحدة)

```dart
// lib/services/face_recognition_api.dart
static const String BASE_URL = "https://munir-api-production.up.railway.app";
```

```bash
flutter clean
flutter run --release
```

### 5️⃣ اختبر! (دقيقة واحدة)

```bash
# Test من terminal
curl https://munir-api-production.up.railway.app/health

# Test من التطبيق
افتح التطبيق → جرب face recognition
```

---

## ✅ خلصنا!

**API شغّال على الإنترنت!** 🎉

---

## 🆘 مشاكل؟

### Model loading failed؟
انتظر 2-3 دقائق (cold start)

### Firebase error؟
تأكد من FIREBASE_CREDENTIALS صحيحة

### 503 error؟
الـ server بيجهز نفسه، جرب بعد دقيقة

---

## 📊 Monitoring

شوف الـ logs في Railway Dashboard:
```
Dashboard → Deployments → View Logs
```

---

**التفاصيل الكاملة في:** `DEPLOYMENT_GUIDE.md`

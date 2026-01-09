# 🚀 دليل النشر - Munir API Deployment Guide

## المحتويات
1. [تجهيز Firebase Credentials](#1-تجهيز-firebase-credentials)
2. [تجهيز GitHub Repository](#2-تجهيز-github-repository)
3. [النشر على Railway](#3-النشر-على-railway)
4. [النشر على Render](#4-النشر-على-render)
5. [تحديث Flutter App](#5-تحديث-flutter-app)
6. [الاختبار](#6-الاختبار)

---

## 1. تجهيز Firebase Credentials

### الطريقة 1: تحويل JSON لـ String واحد

```bash
# في terminal/cmd
cd path/to/firebase-credentials.json

# Mac/Linux:
cat firebase-credentials.json | tr -d '\n' | tr -d ' '

# Windows (PowerShell):
Get-Content firebase-credentials.json -Raw | ForEach-Object { $_ -replace '\s+', '' }

# النتيجة: انسخها كلها - ستحتاجها في الخطوة التالية
```

### الطريقة 2: استخدام أداة online

1. روح https://www.text-utils.com/json-formatter/
2. الصق محتوى `firebase-credentials.json`
3. اضغط "Minify"
4. انسخ النتيجة

---

## 2. تجهيز GitHub Repository

### الخطوة 1: إنشاء Repository

```bash
# في terminal
cd /path/to/munir-api

# تهيئة Git
git init

# إضافة الملفات
git add .

# أول commit
git commit -m "Initial commit - Munir Face Recognition API"
```

### الخطوة 2: إنشاء Repo على GitHub

1. روح https://github.com
2. اضغط "New repository"
3. الاسم: `munir-api`
4. Public أو Private (حسب رغبتك)
5. **لا** تختار "Add README" (عندنا README جاهز)
6. Create repository

### الخطوة 3: رفع الكود

```bash
# ربط مع GitHub
git remote add origin https://github.com/YOUR_USERNAME/munir-api.git

# رفع الكود
git branch -M main
git push -u origin main
```

⚠️ **مهم جداً**: تأكد أن `firebase-credentials.json` **مو** موجود في الـ repo (الـ .gitignore يمنعه)

---

## 3. النشر على Railway

### الخطوة 1: إنشاء حساب

1. روح https://railway.app
2. "Start a New Project"
3. Login with GitHub

### الخطوة 2: ربط Repository

1. "Deploy from GitHub repo"
2. اختر `munir-api`
3. Railway يبدأ يبني المشروع تلقائياً

### الخطوة 3: إضافة Environment Variables

```
في Railway Dashboard:
1. اختر المشروع
2. Variables tab
3. Add Variable:

Name: FIREBASE_CREDENTIALS
Value: {الصق الـ JSON اللي حولناه string في الخطوة 1}

⚠️ تأكد من:
- القيمة تبدأ بـ { وتنتهي بـ }
- ما فيه spaces زيادة
```

### الخطوة 4: إعادة Deploy

```
1. Deployments tab
2. اضغط "Redeploy" (أو انتظر auto-deploy)
3. شاهد الـ logs
```

### الخطوة 5: الحصول على URL

```
Settings tab → Domains

Railway يعطيك URL:
https://munir-api-production.up.railway.app

انسخه - بنستخدمه في Flutter!
```

---

## 4. النشر على Render

### الخطوة 1: إنشاء حساب

1. روح https://render.com
2. Sign up with GitHub

### الخطوة 2: إنشاء Web Service

```
1. Dashboard → "New +"
2. "Web Service"
3. Connect to GitHub repo: munir-api
4. Settings:
   - Name: munir-api
   - Region: Singapore (الأقرب للسعودية)
   - Branch: main
   - Build Command: (يكتشف Dockerfile تلقائياً)
   - Start Command: (يستخدم Dockerfile CMD)
   - Instance Type: Free
```

### الخطوة 3: إضافة Environment Variables

```
Environment tab → Add Environment Variable:

Key: FIREBASE_CREDENTIALS
Value: {الصق الـ JSON المحول}

⚠️ الصق القيمة كاملة بين علامات تنصيص إذا طلب
```

### الخطوة 4: Deploy

```
1. اضغط "Create Web Service"
2. Render يبدأ البناء (5-10 دقائق)
3. شاهد الـ logs في الشاشة
```

### الخطوة 5: الحصول على URL

```
بعد نجاح الـ deployment:
https://munir-api.onrender.com

انسخه!
```

---

## 5. تحديث Flutter App

### تعديل ملف واحد فقط:

```dart
// lib/services/face_recognition_api.dart

class FaceRecognitionAPI {
  // ✅ بدل هذا السطر فقط!
  static const String BASE_URL = "https://munir-api-production.up.railway.app";
  
  // أو إذا استخدمت Render:
  // static const String BASE_URL = "https://munir-api.onrender.com";
  
  // ❌ كان (localhost):
  // static const String BASE_URL = "http://192.168.1.238:8000";
  
  // الباقي ما يتغير! 🎉
}
```

### إعادة Build:

```bash
cd /path/to/flutter/app

# تنظيف
flutter clean

# Build للـ Android
flutter build apk --release

# أو للـ iOS
flutter build ios --release

# تثبيت على الجهاز
flutter run --release
```

---

## 6. الاختبار

### Test 1: Health Check

```bash
# من terminal
curl https://munir-api-production.up.railway.app/health

# المتوقع:
{
  "status": "healthy",
  "insightface": true,
  "firebase": true,
  "timestamp": "2024-01-XX..."
}
```

### Test 2: من Flutter App

```
1. افتح التطبيق
2. جرب Face Recognition
3. جرب Enrollment
4. تأكد من:
   ✅ Recognition يشتغل
   ✅ Enrollment يشتغل
   ✅ List persons يشتغل
```

### Test 3: Firebase

```
1. روح Firebase Console
2. Firestore Database
3. شوف:
   ✅ users/{user_id}/persons - فيه بيانات؟
   
4. Storage
5. شوف:
   ✅ users/{user_id}/thumbnails - فيه صور مشفرة؟
```

---

## المشاكل الشائعة وحلولها

### Problem 1: Model Loading Failed

```
Logs show: "Failed to load InsightFace model"

Solution:
- زد الـ timeout في health check
- تأكد من Memory كافية (2GB+)
- انتظر 2-3 دقائق للـ cold start
```

### Problem 2: Firebase Connection Error

```
Error: "Failed to initialize Firebase"

Solution:
1. تأكد من FIREBASE_CREDENTIALS صحيحة
2. تأكد من format JSON سليم
3. تأكد من Firebase project active
```

### Problem 3: CORS Error من Flutter

```
Error: "CORS policy blocked"

Solution:
في main.py، غيّر:
allow_origins=["*"]

أو حدد domain معين:
allow_origins=["https://your-flutter-app.com"]
```

### Problem 4: 503 Service Unavailable (Render)

```
Render Free tier - Server نائم

Solution:
- أول request يأخذ 30-60 ثانية (cold start)
- انتظر شوي وأعد المحاولة
- في production، استخدم Paid plan
```

---

## Monitoring & Logs

### Railway:

```
Dashboard → Deployments → Logs

شوف:
- Build logs
- Runtime logs
- Errors
```

### Render:

```
Dashboard → Logs

شوف:
- Event logs
- Runtime logs
```

---

## الخطوات التالية

بعد النشر الناجح:

✅ **للمشروع الأكاديمي:**
- خلاص! جاهز للـ demo والعرض

✅ **للـ production:**
- أضف monitoring (Sentry, LogRocket)
- فعّل SSL pinning في Flutter
- أضف rate limiting
- سوي backup strategy

---

## التكلفة المتوقعة

### Railway (الموصى به):
```
Free tier: $5 شهرياً
= حوالي 500 ساعة تشغيل
= كافي جداً للمشروع الأكاديمي

بعد Free tier:
Hobby Plan: $5/شهر
```

### Render:
```
Free tier: مجاني تماماً! ✅
لكن:
- Server ينام بعد 15 دقيقة
- Cold start: 30-60 ثانية

Paid:
Starter: $7/شهر
```

---

## الدعم

واجهتك مشكلة؟

1. شوف الـ logs أولاً
2. تأكد من environment variables
3. جرب local deployment أولاً
4. اسأل في المشروع!

---

**🎉 مبروك! API جاهز للـ production!**

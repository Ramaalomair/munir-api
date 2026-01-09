# Firebase Credentials Setup

## ⚠️ IMPORTANT: Never commit actual credentials to Git!

This is a template file. Replace with your actual Firebase credentials.

## How to get your credentials:

1. Go to Firebase Console: https://console.firebase.google.com
2. Select your project (munir-21f4a)
3. Project Settings (⚙️) → Service Accounts
4. Click "Generate new private key"
5. Save the downloaded JSON file as `firebase-credentials.json`
6. Place it in the project root (it's in .gitignore)

## File structure:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "xxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com",
  "client_id": "xxx",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "xxx"
}
```

## For deployment:

Convert JSON to single-line string:

```bash
# Mac/Linux:
cat firebase-credentials.json | tr -d '\n' | tr -d ' '

# Copy the output and paste as FIREBASE_CREDENTIALS environment variable
```

# SmartPlan Medical — Android Distribution (TWA + Capacitor)

## Option A: Trusted Web Activity (TWA)

The simplest way to package the PWA for Android. Zero custom code needed.

### Prerequisites
- Android Studio installed
- JDK 11+
- Your signing keystore

### Steps

1. **Install Bubblewrap CLI**:
```bash
npm install -g @nickvdkrogt/pwa-to-twa@latest
# or
npm install -g @nickvdkrogt/nickvdkrogt-pwa-to-twa@latest
```

2. **Generate TWA project**:
```bash
npx @nickvdkrogt/pwa-to-twa init \
  --url "https://reunion.eg-smartplan.solutions" \
  --name "SmartPlan Medical" \
  --packageId "com.smartplan.medical" \
  --themeColor "#0D1B2A" \
  --backgroundColor "#0D1B2A" \
  --iconUrl "https://reunion.eg-smartplan.solutions/assets/smartplan_medical/icons/icon-512x512.png"
```

3. **Digital Asset Links** — Host this at `/.well-known/assetlinks.json`:
```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.smartplan.medical",
    "sha256_cert_fingerprints": ["YOUR_APP_SIGNING_FINGERPRINT"]
  }
}]
```

4. **Build APK/AAB**:
```bash
cd twa-project
./gradlew assembleRelease
# APK at: app/build/outputs/apk/release/
```

---

## Option B: Capacitor (Recommended for more control)

### Setup

1. **Initialize Capacitor project**:
```bash
mkdir smartplan-mobile && cd smartplan-mobile
npm init -y
npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios
npx cap init "SmartPlan Medical" "com.smartplan.medical" --web-dir=www
```

2. **Create `capacitor.config.ts`**:
```typescript
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.smartplan.medical',
  appName: 'SmartPlan Medical',
  webDir: 'www',
  server: {
    url: 'https://reunion.eg-smartplan.solutions',
    cleartext: false,
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      backgroundColor: '#0D1B2A',
      showSpinner: false,
    },
  },
  android: {
    backgroundColor: '#0D1B2A',
  },
};

export default config;
```

3. **Add platforms**:
```bash
npx cap add android
npx cap add ios
```

4. **Create minimal `www/index.html`** (just redirects to the PWA):
```html
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url=https://reunion.eg-smartplan.solutions/app">
</head>
<body>Loading...</body>
</html>
```

5. **Build and open in Android Studio**:
```bash
npx cap sync
npx cap open android
```

6. **Generate signed APK** in Android Studio:
   - Build → Generate Signed Bundle / APK
   - Choose APK or AAB
   - Sign with your keystore

---

## Digital Asset Links Setup

For TWA to work without the Chrome address bar, you MUST host `assetlinks.json`.

### Using Frappe/Bench
Create the file at:
```
sites/<your-site>/public/.well-known/assetlinks.json
```

Or serve it via nginx:
```nginx
location /.well-known/assetlinks.json {
    alias /path/to/assetlinks.json;
    add_header Content-Type application/json;
}
```

### Get your fingerprint
```bash
keytool -list -v -keystore your-keystore.jks -alias your-alias
# Copy the SHA-256 fingerprint
```

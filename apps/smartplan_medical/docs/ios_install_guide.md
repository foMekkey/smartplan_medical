# SmartPlan Medical — iOS Installation Guide

## Method 1: Safari PWA (Recommended)

iOS supports PWA installation directly from Safari. The PWA will run in full-screen mode with its own icon on the home screen.

### For End Users

1. Open **Safari** on your iPhone/iPad
2. Navigate to: `https://reunion.eg-smartplan.solutions`
3. Tap the **Share** button (⬆️) at the bottom
4. Scroll down and tap **"Add to Home Screen"**
5. Optionally rename the app, then tap **"Add"** in the top right
6. The app will now appear on your home screen with its own icon

### Limitations on iOS
- Push notifications require iOS 16.4+
- Background sync is not fully supported
- The app refreshes when returning from background after ~3 minutes

---

## Method 2: Capacitor IPA (Enterprise Distribution)

For enterprise deployment (no App Store), you can build a Capacitor-based IPA.

### Prerequisites
- macOS with Xcode 15+
- Apple Developer Account ($99/year)
- Apple Enterprise Program (for enterprise distribution, $299/year)

### Steps

1. **Set up Capacitor** (same as Android guide):
```bash
mkdir smartplan-mobile && cd smartplan-mobile
npm init -y
npm install @capacitor/core @capacitor/cli @capacitor/ios
npx cap init "SmartPlan Medical" "com.smartplan.medical" --web-dir=www
npx cap add ios
```

2. **Create `www/index.html`**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url=https://reunion.eg-smartplan.solutions/app">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
</head>
<body style="background:#0D1B2A;">Loading...</body>
</html>
```

3. **Sync and open Xcode**:
```bash
npx cap sync ios
npx cap open ios
```

4. **Configure in Xcode**:
   - Set Bundle Identifier: `com.smartplan.medical`
   - Configure signing team
   - Set deployment target: iOS 14.0+
   - Add app icons (drag the generated icons to Assets.xcassets)

5. **Build IPA**:
   - Product → Archive
   - Distribute App → Ad Hoc / Enterprise
   - Export IPA

6. **Install via OTA or MDM**:
   - Use Diawi, App Center, or enterprise MDM
   - Create a `.plist` manifest for OTA installation

---

## iOS PWA Capabilities (iOS 17+)

| Feature | Support |
|---------|---------|
| Home Screen Install | ✅ |
| Full Screen Mode | ✅ |
| Custom Icons | ✅ |
| Splash Screen | ✅ |
| Push Notifications | ✅ (iOS 16.4+, via Web Push) |
| Service Worker | ✅ (with limitations) |
| Background Sync | ❌ |
| Persistent Storage | ⚠️ (7-day eviction if not used) |

### Tips for iOS Users
- Use the app regularly to prevent cache eviction
- For push notifications, grant permission when prompted
- The status bar color matches the theme when in standalone mode

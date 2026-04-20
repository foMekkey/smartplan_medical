# SmartPlan Medical — PWA Deployment Guide

## 1. Installation on Bench

### Install the app:
```bash
cd /home/frappeuser/frappe-bench

# The app is already in apps/smartplan_medical
# Install it on your target site:
bench --site <your-site> install-app smartplan_medical

# Build assets:
bench build --app smartplan_medical

# Restart:
bench restart
```

### If installing on a new site:
```bash
bench new-site reunion.eg-smartplan.solutions --admin-password <password>
bench --site reunion.eg-smartplan.solutions install-app erpnext
bench --site reunion.eg-smartplan.solutions install-app smartplan_medical
bench build
bench restart
```

---

## 2. Nginx Configuration

Add these headers to your nginx configuration for optimal PWA behavior:

```nginx
# In your site's nginx config (usually in /etc/nginx/conf.d/)

# Service Worker scope
location /assets/smartplan_medical/js/service-worker.js {
    add_header Service-Worker-Allowed /;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    expires 0;
}

# Manifest
location /api/method/smartplan_medical.api.get_manifest {
    add_header Cache-Control "public, max-age=3600";
}

# PWA icons
location /assets/smartplan_medical/icons/ {
    add_header Cache-Control "public, max-age=31536000, immutable";
}

# Offline page
location /assets/smartplan_medical/offline.html {
    add_header Cache-Control "public, max-age=86400";
}

# Digital Asset Links (for Android TWA)
location /.well-known/assetlinks.json {
    add_header Content-Type application/json;
    add_header Cache-Control "public, max-age=3600";
}
```

After editing, regenerate nginx config:
```bash
bench setup nginx
sudo service nginx reload
```

---

## 3. HTTPS Requirement

PWA requires HTTPS. Ensure your site has SSL:
```bash
bench setup lets-encrypt <your-site>
```

---

## 4. Theme Conflicts

If you want the cleanest experience, uninstall conflicting theme apps:
```bash
bench --site <your-site> uninstall-app datavalue_theme_15
bench --site <your-site> uninstall-app tekton_theme
bench --site <your-site> uninstall-app owl_theme
bench --site <your-site> uninstall-app business_theme_v14
bench --site <your-site> uninstall-app netmanthan_themes
```

Or keep them installed — SmartPlan PWA uses high-specificity selectors scoped
under `.smartplan-pwa` to override without conflicts.

---

## 5. Customization

### Change Brand Colors
Edit `apps/smartplan_medical/smartplan_medical/public/scss/_variables.scss`:
```scss
$sp-navy: #YOUR_DARK_COLOR;
$sp-accent: #YOUR_ACCENT_COLOR;
```

Then rebuild:
```bash
bench build --app smartplan_medical
```

### Change App Name
Update in ERPNext: **Setup → Website Settings → App Name**

The manifest and branding will update dynamically.

### Custom Logo
Replace the icons in:
```
apps/smartplan_medical/smartplan_medical/public/icons/
```

Sizes needed: 72, 96, 128, 144, 152, 192, 384, 512 (all PNG).

---

## 6. Verification

### Lighthouse Audit
1. Open Chrome DevTools → Lighthouse
2. Select "Progressive Web App"
3. Run audit — target score ≥ 90

### Check PWA Installation
1. Open site in Chrome mobile
2. Wait for install prompt banner
3. Or use Chrome menu → "Install app"

### Check Service Worker
1. Open Chrome DevTools → Application
2. Check "Service Workers" section
3. Verify it's registered and activated

### Check Manifest
1. Open Chrome DevTools → Application → Manifest
2. Verify all fields populated
3. Check icons are loading

---

## 7. Troubleshooting

| Issue | Solution |
|-------|----------|
| SW not registering | Verify HTTPS and SW URL path |
| Icons not loading | Run `bench build` and clear cache |
| Install prompt not showing | Check manifest and service worker in DevTools |
| Theme not applying | Clear browser cache, check `.smartplan-pwa` class on `<html>` |
| Bottom nav not showing | Verify viewport ≤ 768px or mobile UA |
| Offline page not working | Check SW install event pre-caching |

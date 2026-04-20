# SmartPlan Medical — ERPNext PWA

Production-grade Progressive Web App layer for ERPNext that transforms the system into a native-like mobile application.

## Features

- **Full PWA Standards**: Web App Manifest, Service Worker, installable on all platforms
- **Smart Caching**: Cache First for assets, Network First for APIs, offline fallback
- **Mobile-First UI**: Bottom navigation, FAB, card-based lists, touch gestures
- **Premium Theme**: Dark glassmorphism design with modern typography
- **Zero Behavior Change**: All ERPNext/Frappe features preserved exactly
- **Android/iOS Ready**: TWA and Capacitor distribution support

## Quick Start

```bash
# Install on your site
bench --site <your-site> install-app smartplan_medical
bench build --app smartplan_medical
bench restart
```

## Documentation

- [Deployment Guide](docs/deployment_guide.md)
- [Android Setup](docs/android_setup.md)
- [iOS Installation](docs/ios_install_guide.md)

## License

MIT

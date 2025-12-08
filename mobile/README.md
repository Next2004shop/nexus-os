# NEXUS MOBILE COMPANION APP (APK)

> **Status**: Ready for Packaging
> **Target**: Android (via Capacitor)

## Overview
Since Nexus runs as a powerful Backend (`nexus_bridge.py`) + Frontend (`PHP`), the optimal mobile strategy is a **Hybrid App**. The APK acts as a "Remote Control" for the core intelligence running on your PC.

## Build Instructions (Android)

### Option A: Local Network Remote (Recommended)
1.  **Host**: Run `start_nexus.bat` on your PC.
2.  **IP**: Find your PC's LAN IP (e.g., `192.168.1.15`).
3.  **Config**: Update `config.js` in the mobile logic to point to `http://192.168.1.15:8000`.
4.  **Wrap**: Use Capacitor to wrap the `http://...` URL into an APK.

### Option B: Full Bundle
*Packaging Python/PHP inside an APK is theoretically possible but highly unstable. We stick to Option A for professional reliability.*

## Project Structure
This folder (`mobile/`) is reserved for the Capacitor project files.
1.  Install Node/Capacitor: `npm install @capacitor/core @capacitor/cli @capacitor/android`
2.  Initialize: `npx cap init NexusMobile com.nexus.ai`
3.  Set Web Dir: `../` (The root PHP interface)
4.  Add Android: `npx cap add android`
5.  Build: `npx cap open android` -> Build APK in Android Studio.

## Mobile Features (Active)
-   **Responsive Layout**: `style.css` has been updated with media queries.
-   **Bottom Navigation**: Sidebar becomes a bottom tab bar on mobile.
-   **Touch Optimized**: Large tap targets for "BUY" / "SELL" and "APPROVE".

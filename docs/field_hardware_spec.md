# CivicSense — Field Data Collector Hardware Spec

This spec is written around the current CivicSense app: a Flask web app with a web intake form and a JSON intake API, with a central SQLite database as the source of truth in the demo/pilot.

It gives two deployment paths:

- Online-only field capture to a central server
- Offline capture with later sync

## Current readiness

| Capability | Status |
|---|---|
| Web intake form | Available |
| JSON intake API | Available |
| Dashboard and reports | Available |
| Central SQLite source of truth | Available for pilot |
| Device/collector identity | Not yet implemented |
| Offline queue and sync | Not yet implemented |
| Safe remote access from outside the LAN | Not yet implemented |

Bottom line: online field capture is close; offline capture and sync needs both hardware and a small app extension.

## Deployment paths

| Aspect | Online-only | Offline+sync |
|---|---|---|
| Main assumption | Devices usually have network access | Devices must work where network is missing or weak |
| Where processing happens | Central server at submission time | Central server, but submission is later |
| Main risk | Connectivity drops make intake painful | Queue, timestamps, duplicates, and conflicts become real |
| App changes | Mostly connectivity, mobile-friendly access, and a clear source label | Device/collector identity, local queue, sync replay, and reconciliation |

## Component list

### Field device

| Component | Role | Online-only | Offline+sync | Notes |
|---|---|---|---|---|
| Android phone or tablet | Field intake UI or sync client | 1 per collector or shared | Same | Business-grade preferred; camera helps; 7–10 in screen is a reasonable default |
| Battery and charging | Keeps intake running through a shift | Useful | Important | Spare battery or charging cradle helps for shared devices |
| SIM or Wi-Fi | Reaches the server | Needed | Needed when syncing | Mobile data is the common fallback when ward Wi-Fi is weak |
| Optional ruggedization | Survives outdoor use | Optional | Optional | Add casing or rugged handheld only if the environment demands it |
| Optional GPS | Auto-capture location | Helpful | Helpful | Only buy if your workflow needs it; the app already has ward selection |

### Central server

| Component | Role | Online-only | Offline+sync | Notes |
|---|---|---|---|---|
| Always-on machine | Runs Flask, SQLite, reports | 1 | 1 | Mini PC, office PC, or small server is enough for a pilot |
| Memory and CPU | Loads classifier, serves requests, builds reports | Modest modern hardware is fine | Same | Current app is not a large-cluster workload |
| Storage, SSD preferred | Holds DB, models, reports | Needed | Needed | SSD is better for DB and report I/O reliability |
| Reliable power | Keeps server available | Important | Important | Use UPS if outages are common |
| Local network hardware | Connects on-site devices to server | Helpful if on-prem | Helpful | Small router/switch and stable server IP or DNS are usually enough |

Because the current app uses one SQLite file, the central server is the practical source of truth. If you later need many offices writing at the same time, that becomes a database and architecture decision before you scale.

### Network and connectivity

| Component | Role | Online-only | Offline+sync | Notes |
|---|---|---|---|---|
| Internet route to server | Lets devices reach the API and web form | Essential | Only when syncing | Usually the make-or-break part of field capture |
| LAN/router if on-site | Lets devices talk to server inside the office | Helpful | Helpful | Keep addressing simple and stable |
| Secure remote access | Lets remote devices talk to server safely | Needed if not on same LAN | Needed if not on same LAN | Do not expose the default dev server directly to the open internet; use VPN or equivalent controlled access with HTTPS |
| Mobile data fallback | Backup path when Wi-Fi is missing | Recommended | Recommended | SIM data or a supervisor hotspot can be the difference between usable and frustrating |

### Offline queue and sync components

These only matter for the offline+sync path.

| Component | Role | Online-only | Offline+sync | Notes |
|---|---|---|---|---|
| Local storage on device | Holds queued complaints until sync | Not required | Needed | Include photos if your workflow captures them |
| Device/collector identity | Lets records be traced after sync | Optional but useful | Needed | Could be device ID, collector ID, or both, surfaced as source or a new field |
| Sync trigger | Sends queued records when connectivity returns | Not required | Needed | Can be manual sync now or automatic when network appears |
| Time source on device | Timestamps matter for age, fraud, and frequency signals | Helpful | Important | Device clock should be reasonable |
| Sync supervision point | Where devices are charged and forced to sync | Optional | Useful | End-of-shift checkpoint or charging station works well |

### Optional convenience hardware

| Component | Role | Online-only | Offline+sync | Notes |
|---|---|---|---|---|
| Label or thermal printer | Prints a ticket or receipt number | Optional | Optional | Only if your workflow wants a physical handover |
| Power bank | Backs up devices during long rounds | Useful | Useful | Good for shared devices and long ward coverage |
| Charging cradle or dock | Central charging for a small fleet | Useful if shared | Useful if shared | Helps if devices are rotated rather than issued one-to-one |
| Keyboard, stand, or mount | Makes the device usable as a counter or kiosk | Optional | Optional | Primarily for office helper stations, not mobile collectors |

## Example pilot spec

For a pilot from one municipality office with a small number of field collectors, a reasonable starting spec is:

- Field devices: 2–4 business Android phones/tablets
- Central server: 1 always-on machine
- Local network: 1 router/switch if collectors are often on-site
- Connectivity: reliable Wi-Fi or mobile data path from devices to the server
- Power protection: UPS if power is unstable
- Field support: spare battery or charging point if shifts are long
- Optional: charging dock and/or label printer only if the workflow asks for them

That is enough to test the real question: can field staff capture complaints easily, and do those complaints land cleanly in CivicSense with classification, priority, fraud scoring, and duplicate handling intact.

## What each path still needs from the app

### Online-only field capture

Mostly a deployment and ergonomics change, not a new feature:

- Make the intake experience easy to use on a phone screen, or wrap it in a lightweight app/kiosk browser.
- Give field submissions a clear source value such as Field App so they can be filtered and traced.
- Make sure field devices can reach the server reliably, preferably over HTTPS and a controlled network or VPN rather than an open dev server.
- Confirm the existing fraud-frequency and duplicate-detection behavior still makes sense when many field submissions arrive from one ward in a short window.

### Offline capture and sync

This path needs both hardware support and a small software extension:

- Add device/collector identity so a synced record can be traced back to the device or person that captured it.
- Add a local queue on the device for complaints captured while offline.
- Add a sync/replay path that sends queued complaints to the central API when connectivity returns.
- Decide what happens if the same incident is reported from more than one device before sync completes; the app should have a reconciliation view for duplicates, failed syncs, or near-identical submissions.
- Keep timestamps sensible, because priority age and fraud/frequency signals depend on submission time.

## Verification plan once hardware is available

### Online-only path

- From a field device on the network, submit a complaint through the web form or the JSON API.
- Confirm it appears in the dashboard/database with category, priority, fraud fields, and duplicate handling.
- Confirm the source value reflects field capture if you set one.

### Offline+sync path

- Capture a complaint while offline and confirm it is stored locally.
- Reconnect and trigger sync.
- Confirm the complaint arrives in CivicSense with a sensible timestamp and a traceable source, device, or collector label.
- Confirm queued records that fail to sync can be retried or surfaced for review.

### Shared-ward behavior

- Have more than one device submit in the same ward within a short window.
- Confirm the fraud-frequency signal and duplicate detection still behave as expected under normal field conditions.

## What not to buy too early

- Rugged industrial handhelds, unless the environment actually requires them
- Built-in GPS or barcode/QR hardware, unless your process needs it
- Label printers, kiosks, or docking stations before you see how the devices are actually used
- A multi-office database architecture before you have proof that one server is the bottleneck

## How to use this spec

- Start with the online-only column if field collectors usually have network access.
- Move to the offline+sync column if field work regularly happens where connectivity is missing or unreliable.
- Treat the app-change notes as the bridge between hardware that can reach CivicSense and hardware that can usefully run CivicSense in the field.

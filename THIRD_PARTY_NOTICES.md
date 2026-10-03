# Third-party notices

The Waveshare e-Paper driver sources in `firmware/CoupleFrame/src/waveshare/` are based on Waveshare's ESP32 e-Paper Driver Board code. Their original copyright and license notices remain in each source file. The vendor package identifies LGPL 2.1; its license text is included as `THIRD_PARTY_LICENSE_LGPL-2.1.txt`.

Source package and official resources are documented in [`docs/Waveshare-driver-source.md`](docs/Waveshare-driver-source.md). Local changes add a BUSY timeout and fail-stop handling; display initialization and data-transfer routines retain the upstream notices.

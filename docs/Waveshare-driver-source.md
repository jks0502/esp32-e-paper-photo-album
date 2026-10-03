# Waveshare driver source

Official resource page: https://docs.waveshare.net/E-Paper_ESP32_Driver_Board/Resources-And-Documents/

The driver files in `firmware/CoupleFrame/src/waveshare/` were copied from the vendor's `E-Paper_ESP32_Driver_Board_Code` package. Original copyright and license comments are retained in source files. The accompanying LGPL 2.1 license is included at the repository root.

Local changes add a 20-second timeout to both `ReadBusy` loops. `DEV_Config` logs the failure and holds reset low. The original initialization commands, LUT, SPI pin mapping, and image transfer sequence were retained. The board pin mapping is SCK=13, MOSI=14, CS=15, DC=27, RST=26, BUSY=25.

The panel revisions use different BUSY levels and initialization commands. Match the driver to the panel revision documented by the vendor; similar dimensions do not imply compatibility. Software simulation cannot replace a real hardware check.

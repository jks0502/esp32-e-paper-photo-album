# 硬件与装配说明

## 目标硬件

- Waveshare e-Paper ESP32 Driver Board（ESP32-WROOM 系列）
- Waveshare 4.2 英寸黑白裸屏，400×300，V2 驱动
- 板载 Type-C 接口和 USB 5 V 电源

该固件面向 `FRAME_PANEL_VERSION=2`。电子纸外观尺寸相近不代表驱动兼容；请核对屏幕标签和对应厂商手册，不确定时不要直接上电刷新。

## IDE 配置

- Board：`ESP32 Dev Module`
- Flash Size：`4MB (32Mb)`
- Partition Scheme：`Huge APP (3MB No OTA/1MB SPIFFS)`
- Serial Monitor：`115200`

屏幕版本通过 [`firmware/CoupleFrame/FrameConfig.h`](../firmware/CoupleFrame/FrameConfig.h) 中的 `FRAME_PANEL_VERSION` 选择。驱动板型号和屏幕版本是两项独立设置。

## 接线和上电

1. 断开 USB 电源后再插拔屏幕 FPC / FFC 排线。
2. 按驱动板对应版本的厂商手册设置拨码和排线方向；不要仅凭排线颜色猜触点方向。
3. 排线平直插到底并锁紧卡扣，避免弯折、拉扯或压住玻璃。
4. 首次使用保持屏幕平放，上传后观察完整刷新是否结束。
5. 连接器、板卡或屏幕发热、出现异常气味或刷新持续卡住时，立即断电并检查硬件。

## 行为与限制

- 全屏刷新时黑白闪烁是电子纸正常刷新过程。
- 自动计时从一次刷新开始计时，约 60 秒后开始下一次刷新。
- BOOT 手动切图会重置自动计时；刷新期间不缓存按键事件。
- 断电后屏幕通常保留最后画面；程序重新上电后从首张图片开始。
- 本项目没有联网功能，也没有实际外壳打印与试装保证。以你手里的硬件版本和供应商资料为准。

驱动源码来源和局部修改说明见 [`Waveshare-driver-source.md`](Waveshare-driver-source.md)。

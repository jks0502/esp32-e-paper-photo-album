# 基于ESP32的墨水屏相册

一款离线电子相框：ESP32 将黑白点阵图片保存在板载 Flash，通过 4.2 英寸、400 × 300 的黑白电子纸轮播展示。项目包含 Arduino 固件、图片转换工具、硬件接线说明和可打印外壳设计。

> 本仓库中的点阵画只作公开演示素材。相册固件原先包含私人照片；为保护隐私，发布版本不包含任何实拍原图、大图源稿或由实拍图生成的固件包。示例固件数据需在本地从公开点阵参考图或你自己的图片生成。

## 功能

- 断网运行，图片和程序存于 ESP32 Flash，USB 5 V 供电。
- 约每 60 秒自动切换一张；短按 BOOT 可切到下一张。
- 400 × 300、1 bit 黑白图片；图片转换工具支持完整构图留白或中心裁切。
- 提供 4.2 英寸 V2 电子纸驱动、接线说明和 FreeCAD 外壳源文件及打印模型。

## 方案思路

电子纸刷新时才耗电，画面在断电后仍会保留。把相册放在 ESP32 内部 Flash，可以省去 SD 卡、Wi-Fi、蓝牙和 RTC 模块。完整刷新通常会出现黑白闪烁，因此本方案以照片展示为主，采用分钟级轮播，并在每次刷新后让屏幕休眠。

## 硬件目标

- Waveshare e-Paper ESP32 Driver Board（板载 ESP32）
- 4.2 英寸黑白 e-Paper V2，400 × 300
- USB 5 V 电源

驱动板和屏幕具体版本会影响驱动选择。当前 `FrameConfig.h` 默认 `FRAME_PANEL_VERSION 2`；请先核对屏幕背标，再使用对应驱动。硬件装配说明见 [`docs/hardware-and-assembly.md`](docs/hardware-and-assembly.md)。

## 编译和烧录

1. 安装 Arduino IDE 2 和 Espressif ESP32 Arduino Core。
2. 打开 `firmware/CoupleFrame/CoupleFrame.ino`，选择 `ESP32 Dev Module`。
3. 设置 Flash Size 为 4 MB，Partition Scheme 为 `Huge APP (3MB No OTA/1MB SPIFFS)`，选中板子的串口。
4. 先生成本地相册数据，再编译：

   ```powershell
   python -m pip install Pillow
   python tools/prepare_photos.py assets/dot-matrix `
     --sketch firmware/CoupleFrame `
     --preview local-preview
   ```

   `Photos.cpp`、`Photos.h` 和 `local-preview/` 是本机生成文件，已列入 `.gitignore`。本地照片放进 `photos/` 后，可把命令中的 `assets/dot-matrix` 改为 `photos`；这些本地照片目录也会被 Git 忽略。

5. 在 Arduino IDE 编译并上传。串口监视器设为 115200 baud。

固件源码不包含 Wi-Fi 密码、云服务密钥或其它联网配置。

## 替换图片

图片转换脚本接受 JPG、JPEG、PNG、BMP 和 WebP；HEIC 请先在本地导出为 JPEG。图片先转换为灰度，再以 Floyd–Steinberg 抖动编码为 400 × 300 的黑白画面。原始输入文件不会被脚本修改。转换结果和固件数组留在本地生成目录；不要把自己的照片或生成文件提交到公开仓库。

仓库提供五张低分辨率点阵参考画，位于 [`assets/dot-matrix/`](assets/dot-matrix/)。

## 外壳

FreeCAD 源文件、生成脚本以及 STL、STEP、OBJ 打印模型位于 [`enclosure/simple-frame/`](enclosure/simple-frame/)。外壳为 4.2 英寸屏设计，实际打印前请按手头驱动板、转接板和 USB 插头复核空间；目前的 CAD 检查不能代替实物试装。

## 验证范围

软件源码和验证记录来自 ESP32 Arduino 环境下的编译与主机模拟工作。主机模拟覆盖轮播计时、按钮防抖、图像数据发送和 BUSY 超时。发布包已移除原私人相册，必须先生成本机 `Photos.cpp`/`Photos.h` 才能编译。没有把固件二进制作为发布内容；真实屏幕效果、实际接线和外壳试装仍需由使用者检查。

## 许可

项目自行编写的代码按 MIT 许可发布；外壳设计文件和文档按 CC BY 4.0 发布。公开点阵参考图仅包含屏幕尺寸的黑白版本，不含原始实拍图。Waveshare 驱动文件保留原版权及许可声明，第三方许可证见 [`THIRD_PARTY_LICENSE_LGPL-2.1.txt`](THIRD_PARTY_LICENSE_LGPL-2.1.txt)。


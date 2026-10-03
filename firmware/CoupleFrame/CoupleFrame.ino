// 富哥方案 · 产品 1：离线照片相框，每 60 秒开始切换下一张。
// Arduino IDE: ESP32 Dev Module. No external Arduino libraries needed.
#include <Arduino.h>
#include <string.h>
#include "FrameConfig.h"
#include "Slideshow.h"
#include "DebouncedButton.h"
#include "Photos.h"
#include "src/waveshare/DEV_Config.h"
#if FRAME_PANEL_VERSION == 2
#include "src/waveshare/EPD_4in2_V2.h"
#else
#include "src/waveshare/EPD_4in2.h"
#endif

static_assert(kPhotoCount > 0, "At least one photo is required");
static_assert(kPhotoBytes == kFrameBytes, "Photos must be 400 x 300, 1-bit");
static uint8_t frameBuffer[kFrameBytes];
static Slideshow slideshow(kPhotoCount, kPhotoIntervalMs);
static DebouncedButton nextButton(kButtonDebounceMs);

static void showPhoto(size_t index) {
  // ESP32 flash is memory mapped; only the current image needs a RAM buffer.
  memcpy(frameBuffer, kPhotos[index], sizeof(frameBuffer));
  Serial.printf("[frame] t=%lu ms, photo=%u/%u, panel=%d\n",
                (unsigned long)millis(), (unsigned)(index + 1),
                (unsigned)kPhotoCount, FRAME_PANEL_VERSION);
#if FRAME_PANEL_VERSION == 2
  EPD_4IN2_V2_Init();
  EPD_4IN2_V2_Display(frameBuffer);
  EPD_4IN2_V2_Sleep();
#else
  EPD_4IN2_Init_Fast();
  EPD_4IN2_Display(frameBuffer);
  EPD_4IN2_Sleep();
#endif
  Serial.println("[frame] done; screen asleep, next start in the 60-second cycle");
  // Refresh blocks polling. Ignore presses during refresh and held buttons.
  nextButton.begin(digitalRead(kNextButtonPin) == LOW, millis());
}

void setup() {
  DEV_Module_Init();
  pinMode(kNextButtonPin, INPUT_PULLUP);
  Serial.println("CoupleFrame: offline / 400x300 / 60 seconds / BOOT=next");
  // Timing is measured from refresh start to refresh start, not 60 seconds
  // after refreshing. Display work therefore does not accumulate time drift.
  if (!slideshow.begin(millis())) DEV_FailStop("Invalid slideshow settings");
  showPhoto(slideshow.index());
}

void loop() {
  const uint32_t now = millis();
  if (nextButton.pressed(digitalRead(kNextButtonPin) == LOW, now)) {
    if (slideshow.advance(now)) {
      Serial.println("[button] BOOT: next photo; automatic timer restarted");
      showPhoto(slideshow.index());
    }
  } else if (slideshow.advanceIfDue(now)) {
    showPhoto(slideshow.index());
  }
  delay(10); // Yield to the ESP32 scheduler while keeping the minute boundary.
}

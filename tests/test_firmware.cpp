// Executes the real Arduino setup/loop and vendor drivers against fake GPIO.
// This verifies software transactions, not physical e-paper waveforms.
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
#include "Arduino.h"
#include "../firmware/CoupleFrame/FrameConfig.h"
#include "../firmware/CoupleFrame/Photos.h"
#include "../firmware/CoupleFrame/Slideshow.h"
#include "../firmware/CoupleFrame/DebouncedButton.h"
#include "../firmware/CoupleFrame/src/waveshare/DEV_Config.h"

void setup();
void loop();
MockSerial Serial;
static uint32_t clockMs;
static int pins[40];
static int pinModes[40];
static bool bootPressed = false;
static bool pressBootDuringRefresh = false;
static bool stuckBusy = false;
static bool failed = false;
static std::string logs;
static uint8_t shiftedByte;
static unsigned bitCount;
struct Transfer { uint8_t command; std::vector<uint8_t> data; };
static std::vector<Transfer> transfers;

unsigned long millis() { return clockMs; }
void delay(unsigned long duration) {
  if (failed && duration == 1000) throw std::runtime_error("firmware halted");
  if (pressBootDuringRefresh && duration != 10) bootPressed = true;
  clockMs += static_cast<uint32_t>(duration);
}
void pinMode(int pin, int mode) { pinModes[pin] = mode; }
int digitalRead(int pin) {
  if (pin == kNextButtonPin) return bootPressed ? LOW : HIGH;
  assert(pin == EPD_BUSY_PIN);
  const int busyLevel = FRAME_PANEL_VERSION == 1 ? LOW : HIGH;
  return stuckBusy ? busyLevel : !busyLevel;
}
void digitalWrite(int pin, int value) {
  // Decode the actual software SPI output from the vendor DEV_Config.cpp.
  if (pin == EPD_CS_PIN && value == LOW) { shiftedByte = 0; bitCount = 0; }
  if (pin == EPD_SCK_PIN && value == HIGH && pins[EPD_CS_PIN] == LOW) {
    shiftedByte = uint8_t((shiftedByte << 1) | (pins[EPD_MOSI_PIN] ? 1 : 0));
    ++bitCount;
  }
  if (pin == EPD_CS_PIN && value == HIGH && bitCount == 8) {
    if (pins[EPD_DC_PIN] == LOW) transfers.push_back({shiftedByte, {}});
    else { assert(!transfers.empty()); transfers.back().data.push_back(shiftedByte); }
    bitCount = 0;
  }
  pins[pin] = value;
}
void MockSerial::print(const char *text) {
  logs += text;
  if (std::strstr(text, "[ERROR]")) failed = true;
}
void MockSerial::println(const char *text) { print(text); logs += '\n'; }
void MockSerial::printf(const char *format, ...) {
  char buffer[256];
  va_list args;
  va_start(args, format);
  vsnprintf(buffer, sizeof(buffer), format, args);
  va_end(args);
  print(buffer);
}

static void checkFrame(size_t index) {
  const uint8_t imageCommand = FRAME_PANEL_VERSION == 1 ? 0x13 : 0x24;
  size_t matches = 0;
  for (const auto &transfer : transfers) {
    if (transfer.command == imageCommand && transfer.data.size() == kPhotoBytes) {
      assert(std::memcmp(transfer.data.data(), kPhotos[index], kPhotoBytes) == 0);
      ++matches;
    }
  }
  assert(matches == 1);
  assert(!transfers.empty());
  const auto &last = transfers.back();
  assert(last.command == (FRAME_PANEL_VERSION == 1 ? 0x07 : 0x10));
  assert(last.data == std::vector<uint8_t>{uint8_t(FRAME_PANEL_VERSION == 1 ? 0xA5 : 0x01)});
  transfers.clear();
}

static void testScheduler() {
  Slideshow invalid(0, 60000);
  assert(!invalid.advance(0));
  assert(!invalid.begin(0));
  assert(!invalid.advanceIfDue(60000));
  Slideshow zeroInterval(3, 0);
  assert(!zeroInterval.begin(0));
  Slideshow slide(3, 60000);
  assert(slide.begin(500));
  assert(slide.index() == 0);
  assert(!slide.advanceIfDue(60499));
  assert(slide.advanceIfDue(60500) && slide.index() == 1);
  assert(!slide.advanceIfDue(60500));
  assert(slide.advanceIfDue(120500) && slide.index() == 2);
  assert(slide.advanceIfDue(180500) && slide.index() == 0);
  assert(slide.advanceIfDue(999999) && slide.index() == 1);
  assert(!slide.advanceIfDue(999999)); // No rapid catch-up refreshes.
  assert(slide.begin(0xFFFF0000U));
  uint32_t now = 0xFFFF0000U;
  for (size_t i = 1; i <= 144000; ++i) { // 100 simulated days, multiple wraps.
    assert(!slide.advanceIfDue(now + 59999U));
    now += 60000U;
    assert(slide.advanceIfDue(now));
    assert(slide.index() == i % 3);
  }
  Slideshow single(1, 60000);
  assert(single.begin(0));
  assert(single.advanceIfDue(60000) && single.index() == 0);
  Slideshow manual(3, 60000);
  assert(manual.begin(0xFFFF0000U));
  const uint32_t manualStart = 0xFFFFFFF0U;
  assert(manual.advance(manualStart) && manual.index() == 1);
  assert(!manual.advanceIfDue(manualStart + 59999U));
  assert(manual.advanceIfDue(manualStart + 60000U) && manual.index() == 2);
}

static void testButton() {
  DebouncedButton button(30);
  button.begin(true, 0); // Initially held: no synthetic press.
  assert(!button.pressed(true, 100));
  assert(!button.pressed(false, 110));
  assert(!button.pressed(false, 140));
  assert(!button.pressed(true, 200));
  assert(!button.pressed(true, 229));
  assert(button.pressed(true, 230));
  assert(!button.pressed(true, 1000));
  button.begin(false, 0xFFFFFFF0U);
  assert(!button.pressed(true, 0xFFFFFFF8U));
  assert(!button.pressed(true, 0x15U));
  assert(button.pressed(true, 0x16U)); // Debounce crosses millis rollover.
}

static void sampleButton(uint32_t at, bool pressed) {
  clockMs = at;
  bootPressed = pressed;
  loop();
}

static void testManualPaging() {
  bootPressed = false;
  clockMs = 0;
  setup();
  checkFrame(0);
  assert(pinModes[kNextButtonPin] == INPUT_PULLUP);
  // Contact bounce must not change the image until 30 ms of stable press.
  sampleButton(10000, true);
  sampleButton(10010, false);
  sampleButton(10020, true);
  sampleButton(10049, true);
  assert(transfers.empty());
  const uint32_t manualStart = 10050;
  sampleButton(manualStart, true);
  checkFrame(1);
  const uint32_t afterRefresh = clockMs;
  sampleButton(afterRefresh + 100, true); // Long hold: no repeat.
  sampleButton(afterRefresh + 200, false);
  sampleButton(afterRefresh + 230, false);
  assert(transfers.empty());
  sampleButton(manualStart + 59999, false);
  assert(transfers.empty());
  sampleButton(manualStart + 60000, false);
  checkFrame(2); // Automatic interval restarts at the manual refresh start.

  bootPressed = false;
  clockMs = 0;
  setup();
  checkFrame(0);
  sampleButton(59970, true);
  assert(transfers.empty());
  sampleButton(60000, true);
  checkFrame(1); // Manual press and automatic deadline: one refresh, not two.

  bootPressed = false;
  clockMs = 0;
  setup();
  checkFrame(0);
  pressBootDuringRefresh = true;
  sampleButton(60000, false); // BOOT becomes held while the driver is busy.
  pressBootDuringRefresh = false;
  checkFrame(1);
  assert(bootPressed);
  const uint32_t refreshedAt = clockMs;
  sampleButton(refreshedAt + 100, true);
  assert(transfers.empty()); // No queued or repeated press after refresh.
  sampleButton(refreshedAt + 200, false);
  sampleButton(refreshedAt + 230, false);
  sampleButton(refreshedAt + 300, true);
  sampleButton(refreshedAt + 330, true);
  checkFrame(2); // Release then press works again.

  bootPressed = false;
  clockMs = 0;
  setup();
  checkFrame(0);
  for (size_t i = 1; i <= kPhotoCount; ++i) {
    const uint32_t pressAt = clockMs + 100;
    sampleButton(pressAt, true);
    assert(transfers.empty());
    sampleButton(pressAt + 30, true);
    checkFrame(i % kPhotoCount); // All actual SPI bytes, including last-to-first.
    const uint32_t releaseAt = clockMs + 10;
    sampleButton(releaseAt, false);
    sampleButton(releaseAt + 30, false);
    assert(transfers.empty());
  }
}

int main() {
  testScheduler();
  testButton();
  clockMs = 0;
  setup();
  checkFrame(0);
  for (uint32_t minute = 1; minute <= 60; ++minute) {
    clockMs = minute * 60000U - 1;
    loop();
    assert(transfers.empty());
    clockMs = minute * 60000U;
    loop();
    checkFrame(minute % kPhotoCount);
    assert(clockMs < minute * 60000U + 60000U);
  }
  // Restart always starts at the first image. Cross the millis rollover.
  clockMs = 0xFFFF0000U;
  setup();
  checkFrame(0);
  for (uint32_t i = 1; i <= 3; ++i) {
    clockMs = uint32_t(0xFFFF0000U + i * 60000U);
    loop();
    checkFrame(i % kPhotoCount);
  }
  testManualPaging();
  // A permanently busy screen must stop with a diagnostic, not hang silently.
  stuckBusy = true;
  failed = false;
  transfers.clear();
  const uint32_t before = clockMs;
  bool halted = false;
  try { setup(); } catch (const std::runtime_error &) { halted = true; }
  assert(halted && failed);
  assert(uint32_t(clockMs - before) >= 20000U);
  assert(uint32_t(clockMs - before) < 22000U);
  assert(pins[EPD_RST_PIN] == LOW);
  assert(logs.find("BUSY timeout") != std::string::npos);
  std::printf("PASS panel %d: 100-day scheduler, 60-minute real loop/SPI bytes, "
              "BOOT debounce/hold/wrap/manual timer/deadline, "
              "wrap/restart, sleep commands, BUSY timeout\n", FRAME_PANEL_VERSION);
}


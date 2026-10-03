#pragma once
#include <stdint.h>

// 1 = official epd4in2-demo; 2 = official epd4in2_V2-demo.
// Select using the actual panel label; this is NOT the ESP32 board revision.
// Default target: a Waveshare 4.2-inch e-Paper V2 panel.
#ifndef FRAME_PANEL_VERSION
#define FRAME_PANEL_VERSION 2
#endif
#if FRAME_PANEL_VERSION != 1 && FRAME_PANEL_VERSION != 2
#error "FRAME_PANEL_VERSION must be 1 or 2"
#endif

constexpr uint32_t kPhotoIntervalMs = 60000UL;
constexpr uint8_t kNextButtonPin = 0; // Rev 3 BOOT button, active low.
constexpr uint32_t kButtonDebounceMs = 30UL;
constexpr uint16_t kFrameWidth = 400;
constexpr uint16_t kFrameHeight = 300;
constexpr uint32_t kFrameBytes = kFrameWidth * kFrameHeight / 8;


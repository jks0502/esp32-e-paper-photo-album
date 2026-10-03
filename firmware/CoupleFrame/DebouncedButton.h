#pragma once
#include <stdint.h>

// One event per stable press. A button held at begin() must be released first.
class DebouncedButton {
 public:
  explicit DebouncedButton(uint32_t debounceMs) : debounceMs_(debounceMs) {}

  void begin(bool pressed, uint32_t now) {
    rawPressed_ = stablePressed_ = pressed;
    changedAt_ = now;
  }

  bool pressed(bool rawPressed, uint32_t now) {
    if (rawPressed != rawPressed_) {
      rawPressed_ = rawPressed;
      changedAt_ = now;
    }
    if (rawPressed_ == stablePressed_ ||
        uint32_t(now - changedAt_) < debounceMs_) return false;
    stablePressed_ = rawPressed_;
    return stablePressed_;
  }

 private:
  uint32_t debounceMs_;
  uint32_t changedAt_ = 0;
  bool rawPressed_ = false;
  bool stablePressed_ = false;
};

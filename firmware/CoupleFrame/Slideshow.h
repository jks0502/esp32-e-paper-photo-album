#pragma once
#include <stddef.h>
#include <stdint.h>

// Unsigned subtraction remains correct when millis() wraps after ~49.7 days.
// A delayed loop advances once, never rapidly replays missed frames.
class Slideshow {
 public:
  Slideshow(size_t count, uint32_t interval)
      : count_(count), interval_(interval) {}

  bool begin(uint32_t now) {
    if (count_ == 0 || interval_ == 0 || interval_ >= 0x80000000UL) return false;
    index_ = 0;
    lastStart_ = now;
    started_ = true;
    return true;
  }

  bool advanceIfDue(uint32_t now) {
    if (!started_ || uint32_t(now - lastStart_) < interval_) return false;
    return advance(now);
  }

  // Manual paging starts a fresh automatic interval.
  bool advance(uint32_t now) {
    if (!started_) return false;
    index_ = (index_ + 1) % count_;
    lastStart_ = now;
    return true;
  }

  size_t index() const { return index_; }

 private:
  size_t count_;
  uint32_t interval_;
  size_t index_ = 0;
  uint32_t lastStart_ = 0;
  bool started_ = false;
};

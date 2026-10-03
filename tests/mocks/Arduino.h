#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#define HIGH 1
#define LOW 0
#define INPUT 0
#define INPUT_PULLUP 2
#define OUTPUT 1
#define PROGMEM
struct MockSerial {
  void begin(unsigned long) {}
  void print(const char *text);
  void println(const char *text);
  void printf(const char *format, ...);
};
extern MockSerial Serial;
unsigned long millis();
void delay(unsigned long duration);
void pinMode(int pin, int mode);
void digitalWrite(int pin, int value);
int digitalRead(int pin);

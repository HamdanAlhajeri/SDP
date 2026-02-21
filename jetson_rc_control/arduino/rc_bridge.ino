/*
 * RC Bridge - Arduino Firmware
 * 
 * Receives serial commands from Jetson and outputs PWM signals
 * to control steering servo and ESC on Traxxas RC car.
 * 
 * Hardware connections:
 *   - Steering servo signal -> Pin D9
 *   - ESC signal -> Pin D10
 *   - Common ground between ESC, servo, and Arduino
 * 
 * Serial protocol:
 *   Format: S<steer_us> T<throttle_us>\n
 *   Example: S1500 T1600\n
 *   Range: 1000-2000 microseconds
 */

#include <Servo.h>

// Pin definitions
#define STEERING_PIN 9
#define THROTTLE_PIN 10

// PWM limits (microseconds)
#define MIN_US 1000
#define MAX_US 2000
#define NEUTRAL_US 1500

// Timeout for safety shutdown (milliseconds)
#define SERIAL_TIMEOUT_MS 500

// Servo objects
Servo steeringServo;
Servo throttleServo;

// Current values
int steer_us = NEUTRAL_US;
int throttle_us = NEUTRAL_US;

// Timing
unsigned long lastSerialTime = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  
  // Attach servos
  steeringServo.attach(STEERING_PIN);
  throttleServo.attach(THROTTLE_PIN);
  
  // Set neutral positions
  steeringServo.writeMicroseconds(NEUTRAL_US);
  throttleServo.writeMicroseconds(NEUTRAL_US);
  
  // Wait for ESC to arm
  delay(2000);
  
  Serial.println("RC Bridge Initialized");
  Serial.println("Waiting for commands: S<steer_us> T<throttle_us>");
  
  lastSerialTime = millis();
}

void loop() {
  // Check for serial data
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    
    if (parseCommand(command)) {
      // Apply clamping
      steer_us = constrain(steer_us, MIN_US, MAX_US);
      throttle_us = constrain(throttle_us, MIN_US, MAX_US);
      
      // Write to servos
      steeringServo.writeMicroseconds(steer_us);
      throttleServo.writeMicroseconds(throttle_us);
      
      lastSerialTime = millis();
    }
  }
  
  // Safety timeout: if no commands received for SERIAL_TIMEOUT_MS, return to neutral
  if (millis() - lastSerialTime > SERIAL_TIMEOUT_MS) {
    // Gradually return throttle to neutral for safety
    if (throttle_us > NEUTRAL_US) {
      throttle_us--;
    } else if (throttle_us < NEUTRAL_US) {
      throttle_us++;
    }
    
    throttleServo.writeMicroseconds(throttle_us);
    
    // Update last serial time to avoid constant triggering
    lastSerialTime = millis();
  }
}

bool parseCommand(String cmd) {
  // Expected format: S<steer_us> T<throttle_us>
  // Example: S1200 T1800
  
  int steerIndex = cmd.indexOf('S');
  int throttleIndex = cmd.indexOf('T');
  
  // Validate format
  if (steerIndex == -1 || throttleIndex == -1) {
    Serial.println("Error: Missing S or T prefix");
    return false;
  }
  
  // Parse steering value
  String steerStr = cmd.substring(steerIndex + 1, throttleIndex);
  steerStr.trim();
  int newSteer = steerStr.toInt();
  
  // Parse throttle value
  String throttleStr = cmd.substring(throttleIndex + 1);
  throttleStr.trim();
  int newThrottle = throttleStr.toInt();
  
  // Validate ranges (basic sanity check)
  if (newSteer == 0 || newThrottle == 0) {
    Serial.println("Error: Invalid numeric values");
    return false;
  }
  
  // Update values
  steer_us = newSteer;
  throttle_us = newThrottle;
  
  return true;
}

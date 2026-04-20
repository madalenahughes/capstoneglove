#include <Arduino.h>
#include <HardwareSerial.h>

// Sensor pins
const int FIST_PIN      = 34;
const int PINCH_PIN     = 39;
const int EXTENSION_PIN = 36;

const int delayTime = 50;  // ms between reads

// --- UART2 to Raspberry Pi ---
HardwareSerial mySerial(2);

// --- Moving average (smoothing) ---
const int AVG_N = 20;
int bufF[AVG_N], bufP[AVG_N], bufE[AVG_N];
int idxF = 0, idxP = 0, idxE = 0;
long sumF = 0, sumP = 0, sumE = 0;

// --- Rolling min/max (normalization to 0-100) ---
const int NORM_N = 100;
int normBufF[NORM_N], normBufP[NORM_N], normBufE[NORM_N];
int normIdx = 0;

// --- Thresholds on normalized 0-100 scale ---
const int TH_FIST      = 50;
const int TH_PINCH     = 50;
const int TH_EXTENSION = 50;
// sample count
int timeCount = 0;
// TODO: add thresholds for remaining gestures after dataset analysis

enum Gesture {
  REST = 0,
  FIST,
  PINCH,
  EXTENSION,
  PEACE,
  POINT,
  THUMB,
  INDEX_FINGER,
  MIDDLE,
  RING,
  PINKY,
  OKTH,
  MIDTH,
  TWISTLEFT,
  TWISTRIGHT
};


// In loop(), replace gestureName(g) with:
  //Serial.println(g);

int updateAvg(int raw, int *buf, int &idx, long &sum) {
  sum -= buf[idx];
  buf[idx] = raw;
  sum += raw;
  idx = (idx + 1) % AVG_N;
  return (int)(sum / AVG_N);
}

int normalizeChannel(int avg, int *normBuf) {
  normBuf[normIdx] = avg;

  int mn = normBuf[0], mx = normBuf[0];
  for (int i = 1; i < NORM_N; i++) {
    if (normBuf[i] < mn) mn = normBuf[i];
    if (normBuf[i] > mx) mx = normBuf[i];
  }

  if (mx == mn) return 0;
  return (int)((float)(avg - mn) / (mx - mn) * 100);
}

Gesture classifyGesture(int F, int P, int E) {
  // Check in priority order — most distinctive first

  // TWISTLEFT: F spikes dramatically (mean ~383, others ~80-170)
  if (F > 250) return TWISTLEFT;

  // POINT: E very high (mean ~546)
  if (E > 490) return POINT;

  // Finger isolation gestures — P is LOW (they have small/no pinch activation)
  // and E is HIGH (extension electrodes active)
  if (E > 340 && P < 260)              return PINKY;
  if (E > 310 && P < 280)              return RING;
  if (E > 300 && P < 290 && F < 120)  return MIDDLE;

  // OKTH (OK thumb): high E, slightly higher P than RING/PINKY
  if (E > 370 && P < 330)             return OKTH;

  // INDEX: high P, moderate-high E
  if (P > 430 && E > 280 && E < 450)  return INDEX_FINGER;

  // THUMB: high P, moderate E, F elevated
  if (P > 400 && E >= 230 && E < 380 && F > 120) return THUMB;

  // MIDTH: moderate E, moderate P
  if (E >= 230 && E < 320 && P > 350) return MIDTH;

  // PEACE: moderate E, moderate P
  if (E >= 220 && E < 310 && P > 300 && P < 420) return PEACE;

  // Core 3 gestures
  if (P > 420 && E < 235)             return FIST;
  if (E >= 190 && E < 230 && F < 180) return EXTENSION;
  if (P > 340 && P < 430 && E < 200 && F < 145) return PINCH;

  return REST;
}

const char* gestureName(Gesture g) {
  switch (g) {
    case FIST:         return "FIST";
    case PINCH:        return "PINCH";
    case MIDDLE_PINCH: return "MIDDLE-PINCH";
    case PEACE:        return "PEACE";
    case THUMBS_UP:    return "THUMBS-UP";
    case POINT:        return "POINT";
    case THUMB:        return "THUMB";
    case INDEX:        return "INDEX";
    case MIDDLE:       return "MIDDLE";
    case RING:         return "RING";
    case PINKY:        return "PINKY";
    case EXTENSION:    return "EXTENSION";
    case REST:         return "REST";
  }
  return "UNKNOWN";
}

void setup() {
  Serial.begin(115200);                        // USB — for debugging on computer
  mySerial.begin(115200, SERIAL_8N1, -1, 17); // UART2 GPIO17 — to Pi
}

void loop() {
  int rawF = analogRead(FIST_PIN);
  int rawP = analogRead(PINCH_PIN);
  int rawE = analogRead(EXTENSION_PIN);

  int avgF = updateAvg(rawF, bufF, idxF, sumF);
  int avgP = updateAvg(rawP, bufP, idxP, sumP);
  int avgE = updateAvg(rawE, bufE, idxE, sumE);

  int normF = normalizeChannel(avgF, normBufF);
  int normP = normalizeChannel(avgP, normBufP);
  int normE = normalizeChannel(avgE, normBufE);

  normIdx = (normIdx + 1) % NORM_N;

  Gesture g = classifyGesture(normF, normP, normE);

  mySerial.println(gestureName(g));  // ← send to Pi
  Serial.println(gestureName(g));    // ← keep for USB debugging
  Serial.print(", ");
  Serial.println(timeCount);
  timeCount ++;

  delay(delayTime);
}

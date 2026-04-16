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
// TODO: add thresholds for remaining gestures after dataset analysis

enum Gesture { REST, FIST, PINCH, MIDDLE_PINCH, PEACE, THUMBS_UP, POINT, THUMB, INDEX, MIDDLE, RING, PINKY, EXTENSION };

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

Gesture classifyGesture(int nF, int nP, int nE) {
  bool fistHigh      = nF > TH_FIST;
  bool pinchHigh     = nP > TH_PINCH;
  bool extensionHigh = nE > TH_EXTENSION;

  if (!fistHigh && !pinchHigh && !extensionHigh) return REST;

  // Implemented
  if (nF >= nP && nF >= nE && fistHigh)      return FIST;
  if (nP >= nF && nP >= nE && pinchHigh)     return PINCH;
  if (nE >= nF && nE >= nP && extensionHigh) return EXTENSION;

  // TODO: implement thresholds for these gestures after dataset analysis
  // if (...) return MIDDLE_PINCH;
  // if (...) return PEACE;
  // if (...) return THUMBS_UP;
  // if (...) return POINT;
  // if (...) return THUMB;
  // if (...) return INDEX;
  // if (...) return MIDDLE;
  // if (...) return RING;
  // if (...) return PINKY;

  return REST;
}

const char* gestureName(Gesture g) {
  switch (g) {
    case FIST:          return "FIST";
    case PINCH:         return "PINCH";
    case MIDDLE-PINCH:  return "MIDDLE-PINCH";
    case PEACE:         return "PEACE";
    case THUMBS-UP:     return "THUMBS-UP";
    case POINT:         return "POINT";
    case THUMB:         return "THUMB";
    case INDEX:         return "INDEX";
    case MIDDLE:        return "MIDDLE";
    case RING:          return "RING";
    case PINKY:         return "PINKY";
    case REST:          return "REST";
  }
  return "UNKNOWN";
}

void setup() {
  Serial.begin(115200);
  Serial.println("rawF, rawP, rawE, gesture, sample");
}

  while (counter <= datasetSize) {
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

  // Output: raw values + gesture label + sample counter
  if (counter <= datasetSize) {
    Serial.print(rawF);
    Serial.print(", ");
    Serial.print(rawP);
    Serial.print(", ");
    Serial.print(rawE);
    Serial.print(", ");
    Serial.print(gestureName(g));
    Serial.print(", ");
    Serial.println(counter);
    counter++;
  }
  
  delay(delayTime);
}

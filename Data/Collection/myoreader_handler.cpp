#include <Arduino.h>

// Sensor pins
const int FIST_PIN      = 34;
const int PINCH_PIN     = 39;
const int EXTENSION_PIN = 36;

const int delayTime  = 50;   // ms between reads
const int datasetSize = 9500; // number of samples to capture

int counter = 1;

// --- Moving average (smoothing) ---
const int AVG_N = 20;
int bufF[AVG_N], bufP[AVG_N], bufE[AVG_N];
int idxF = 0, idxP = 0, idxE = 0;
long sumF = 0, sumP = 0, sumE = 0;

// --- Rolling min/max (normalization to 0-100) ---
const int NORM_N = 100;
int normBufF[NORM_N], normBufP[NORM_N], normBufE[NORM_N];
int normIdx = 0;

// --- Thresholds on normalized 0-100 scale — tune after analyzing dataset ---
const int TH_FIST      = 50;
const int TH_PINCH     = 50;
const int TH_EXTENSION = 50;

enum Gesture { REST, FIST, PINCH, EXTENSION };

// Smooth raw value into moving average
int updateAvg(int raw, int *buf, int &idx, long &sum) {
  sum -= buf[idx];
  buf[idx] = raw;
  sum += raw;
  idx = (idx + 1) % AVG_N;
  return (int)(sum / AVG_N);
}

// Normalize avg to 0-100 using rolling min/max window
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

    // Dominant channel wins
    if (nF >= nP && nF >= nE && fistHigh)      return FIST;
    if (nP >= nF && nP >= nE && pinchHigh)     return PINCH;
    if (nE >= nF && nE >= nP && extensionHigh) return EXTENSION;

    return REST;
}

const char* gestureName(Gesture g) {
    switch (g) {
        case REST:          return 1;
        case FIST:          return 2;
        case PINCH:         return 3;
        case MIDDLE-PINCH:  return 4;
        case POINT:         return 5;
        case THUMBS-UP:     return 6;
        case PEACE:         return 7;
        case THUMB:         return 8;
        case INDEX:         return 9;
        case MIDDLE:        return 10;
        case RING:          return 11;
        case PINKY:         return 12;
    }
    return 0;
}

void setup() {
    Serial.begin(115200);
}

void loop() {
    int rawF = analogRead(FIST_PIN);
    int rawP = analogRead(PINCH_PIN);
    int rawE = analogRead(EXTENSION_PIN);

    // Smooth with moving average
    int avgF = updateAvg(rawF, bufF, idxF, sumF);
    int avgP = updateAvg(rawP, bufP, idxP, sumP);
    int avgE = updateAvg(rawE, bufE, idxE, sumE);

    // Normalize each channel to 0-100
    int normF = normalizeChannel(avgF, normBufF);
    int normP = normalizeChannel(avgP, normBufP);
    int normE = normalizeChannel(avgE, normBufE);

    // Advance shared normalization index
    normIdx = (normIdx + 1) % NORM_N;

    // Classify gesture from normalized values
    Gesture g = classifyGesture(normF, normP, normE);

    // serial print only gesture label
    Serial.print(gestureName(g));
  
    delay(delayTime);
}
#include <Arduino.h>
#include <HardwareSerial.h>
#include <math.h>

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

// sample count
int timeCount = 0;

// --- Batch averaging before classification (raw ADC scale) ---
const int BATCH_N = 10;
int batchCount = 0;
long batchSumF = 0, batchSumP = 0, batchSumE = 0;
long batchSumSqF = 0, batchSumSqP = 0, batchSumSqE = 0;

enum Gesture {
  REST = 0,
  FIST,
  PINCH,
  PEACE,
  POINT,
  THUMB,
  INDEX,
  MIDDLE,
  RING,
  PINKY,
  OKTH,
  MIDTH,
};

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

// Thresholds derived from Nathan's EMG dataset (batch means of 20-sample moving
// averages, raw ADC units). E channel is the primary discriminator.
Gesture classifyGesture(int F, int F_std, int P, int P_std, int E, int E_std) {
  if (E < 220) {
    if (P > 360)  return PINCH;   // very high P, very low E
    if (P > 310)  return FIST;    // high P, low E
    return REST;
  }
  if (E < 290) {
    if (P > 325)  return MIDTH;   // medium E, high P
    if (P > 290)  return PEACE;   // medium E, medium P
    return OKTH;                   // medium E, low P
  }
  if (E < 335) {
    if (P > 305)  return INDEX;   // medium-high E, medium-high P
    if (F < 93)   return MIDDLE;  // medium-high E, low P, low F
    return THUMB;                  // medium-high E, low P, higher F
  }
  // E >= 335
  if (P > 385)    return PINKY;   // very high E and P
  if (F > 130)    return POINT;   // very high E, high F
  return RING;                     // high E, lower P and F
}

const char* gestureName(Gesture g) {
  switch (g) {
    case FIST:    return "FIST";
    case PINCH:   return "PINCH";
    case MIDTH:   return "MIDTH";
    case PEACE:   return "PEACE";
    case OKTH:    return "OKTH";
    case POINT:   return "POINT";
    case THUMB:   return "THUMB";
    case INDEX:   return "INDEX";
    case MIDDLE:  return "MIDDLE";
    case RING:    return "RING";
    case PINKY:   return "PINKY";
    case REST:    return "REST";
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

  normIdx = (normIdx + 1) % NORM_N;

  batchSumF += avgF;
  batchSumP += avgP;
  batchSumE += avgE;
  batchSumSqF += (long)avgF * avgF;
  batchSumSqP += (long)avgP * avgP;
  batchSumSqE += (long)avgE * avgE;
  batchCount++;

  if (batchCount >= BATCH_N) {
    int batchF = (int)(batchSumF / BATCH_N);
    int batchP = (int)(batchSumP / BATCH_N);
    int batchE = (int)(batchSumE / BATCH_N);

    int stdF = (int)sqrt((float)(batchSumSqF / BATCH_N) - (float)batchF * batchF);
    int stdP = (int)sqrt((float)(batchSumSqP / BATCH_N) - (float)batchP * batchP);
    int stdE = (int)sqrt((float)(batchSumSqE / BATCH_N) - (float)batchE * batchE);

    Gesture g = classifyGesture(batchF, stdF, batchP, stdP, batchE, stdE);

    mySerial.println(gestureName(g));
    Serial.print(gestureName(g));

    batchSumF = 0; batchSumP = 0; batchSumE = 0;
    batchSumSqF = 0; batchSumSqP = 0; batchSumSqE = 0;
    batchCount = 0;
  }

  Serial.print(rawF);
  Serial.print(", "); Serial.print(rawP);
  Serial.print(", "); Serial.print(rawE);
  Serial.print(", "); Serial.println(timeCount);

  timeCount++;

  delay(delayTime);
}

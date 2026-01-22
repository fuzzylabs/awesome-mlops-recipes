// Minimal TFLite Micro runner for ESP32-S3.

#include <Arduino.h>

#include "model_data.h"
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

namespace {
constexpr int kTensorArenaSize = 64 * 1024;
alignas(16) uint8_t tensor_arena[kTensorArenaSize];
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Vision on the Edge: TFLite Micro");

  const tflite::Model *model = tflite::GetModel(g_model);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    Serial.println("Model schema mismatch.");
    while (true) {
      delay(1000);
    }
  }

  static tflite::AllOpsResolver resolver;
  static tflite::MicroInterpreter interpreter(model, resolver, tensor_arena,
                                               kTensorArenaSize);
  if (interpreter.AllocateTensors() != kTfLiteOk) {
    Serial.println("AllocateTensors failed.");
    while (true) {
      delay(1000);
    }
  }

  TfLiteTensor *input = interpreter.input(0);
  if (input == nullptr) {
    Serial.println("Input tensor not found.");
    while (true) {
      delay(1000);
    }
  }

  // Fill input with a default value (all zeros in real-world terms).
  // Replace this block with real input capture (camera, sensor, serial, etc).
  const int8_t zero_point = input->params.zero_point;
  const int input_bytes = input->bytes;
  for (int i = 0; i < input_bytes; ++i) {
    input->data.int8[i] = zero_point;
  }

  if (interpreter.Invoke() != kTfLiteOk) {
    Serial.println("Invoke failed.");
    while (true) {
      delay(1000);
    }
  }

  Serial.println("Inference complete. Update input source in main.cpp to test.");
}

void loop() {
  delay(1000);
}

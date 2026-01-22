// Minimal ExecuTorch runner for ESP32-S3.

#include <Arduino.h>
#include <FS.h>
#include <LittleFS.h>
#include <vector>

#include <executorch/extension/module/module.h>
#include <executorch/extension/tensor/tensor.h>

#include "model_data.h"

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Vision on the Edge: ExecuTorch");

  if (!LittleFS.begin(true)) {
    Serial.println("LittleFS mount failed.");
    while (true) {
      delay(1000);
    }
  }

  const char *model_path = "/model.pte";
  if (!LittleFS.exists(model_path)) {
    File model_file = LittleFS.open(model_path, "wb");
    if (!model_file) {
      Serial.println("Failed to open model file.");
      while (true) {
        delay(1000);
      }
    }
    model_file.write(g_model, g_model_len);
    model_file.close();
  }

  executorch::extension::Module module(model_path);
  std::vector<float> input_data(1 * 1 * 28 * 28, 0.0f);
  auto input_tensor =
      executorch::extension::make_tensor_ptr({1, 1, 28, 28}, input_data);
  auto outputs = module.forward(input_tensor);

  (void)outputs;
  Serial.println("Inference complete. Update input source in main.cpp to test.");
}

void loop() {
  delay(1000);
}

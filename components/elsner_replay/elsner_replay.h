#pragma once

#include "esphome/core/component.h"
#include "esphome/core/helpers.h"
#include "esphome/components/cc1101/cc1101.h"
#ifdef USE_BUTTON
#include "esphome/components/button/button.h"
#endif
#include "esphome/components/elsner_arexa/elsner_arexa.h"
#include <vector>

namespace esphome::elsner_replay {

// Sends whole frames (38 bytes with the CRC, as the 'Letzter Rahmen' text sensor of elsner_arexa shows them) that
// were recorded from a Remo pro. It uses the radio setup of elsner_arexa and puts the radio back into receive mode
// after each frame.
class ElsnerReplay : public Component {
 public:
  void set_radio(cc1101::CC1101Component *radio) { this->radio_ = radio; }
  void set_arexa(elsner_arexa::ElsnerArexa *arexa) { this->arexa_ = arexa; }
  void set_output_power(float power) { this->output_power_ = power; }

  void loop() override;
  void dump_config() override;

  // Queues the frames: frame i goes out i * gap_ms after the call, each one as `copies` copies 30 ms apart.
  void send(const std::vector<std::vector<uint8_t>> &frames, uint32_t gap_ms, uint8_t copies);

 protected:
  struct Pending {
    std::vector<uint8_t> frame;
    uint32_t due;
  };
  void transmit_(const std::vector<uint8_t> &frame);

  cc1101::CC1101Component *radio_{nullptr};
  elsner_arexa::ElsnerArexa *arexa_{nullptr};
  float output_power_{11.0f};
  std::vector<Pending> queue_;
};

#ifdef USE_BUTTON
class ReplayButton : public button::Button, public Parented<ElsnerReplay> {
 public:
  void add_frame(const std::vector<uint8_t> &frame) { this->frames_.push_back(frame); }
  void set_gap(uint32_t gap_ms) { this->gap_ms_ = gap_ms; }
  void set_copies(uint8_t copies) { this->copies_ = copies; }

 protected:
  void press_action() override { this->parent_->send(this->frames_, this->gap_ms_, this->copies_); }
  std::vector<std::vector<uint8_t>> frames_;
  uint32_t gap_ms_{100};
  uint8_t copies_{3};
};
#endif

}  // namespace esphome::elsner_replay

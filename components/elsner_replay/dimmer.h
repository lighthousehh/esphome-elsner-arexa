#pragma once

#include "elsner_replay.h"
#include "esphome/components/output/float_output.h"
#include <vector>

namespace esphome::elsner_replay {

// A dimmer for a light entity (use it as the output of a monochromatic light). The brightness is set the way the
// Remo pro does it: a press frame, after hold_delay the dim frame (the dimmer dims from now on), and after the time
// needed for the change the end frame. The level is only an estimate (the dimmer reports nothing): it goes to the
// bottom or the top (with 10% more time) when 0..5% or 99..100% is asked, which brings it back in line.
class ReplayDimmer : public output::FloatOutput, public Component, public Parented<ElsnerReplay> {
 public:
  // kind: 0 switch_on (press, release), 1 switch_off (press, release), 2 dim_up and 3 dim_down (press, dim, end)
  void add_frame(uint8_t kind, const std::vector<uint8_t> &frame) {
    if (kind < 4)
      this->frames_[kind].push_back(frame);
  }
  void set_dim_time(uint32_t ms) { this->dim_ms_ = ms; }
  void set_hold_delay(uint32_t ms) { this->hold_ms_ = ms; }
  void set_copies(uint8_t copies) { this->copies_ = copies; }

  void loop() override;
  void dump_config() override;

 protected:
  void write_state(float state) override;
  void apply_(float target);

  struct Step {
    uint32_t due;
    uint8_t kind;
    uint8_t index;
  };
  std::vector<std::vector<uint8_t>> frames_[4];
  std::vector<Step> steps_;
  uint32_t dim_ms_{4000};
  uint32_t hold_ms_{1000};
  uint8_t copies_{3};
  bool on_{false};
  float level_{-1.0f};  // the estimated level, -1: not known yet
  uint32_t busy_until_{0};
  bool has_pending_{false};
  float pending_{0.0f};
};

}  // namespace esphome::elsner_replay

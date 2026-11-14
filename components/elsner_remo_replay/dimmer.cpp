#include "dimmer.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"
#include <cmath>

namespace esphome::elsner_remo_replay {

static const char *const TAG = "elsner_remo_replay.dimmer";
static constexpr float MIN_LEVEL = 0.02f;

void ReplayDimmer::write_state(float state) {
  // a sequence is still running: remember only the last wish
  if (!this->steps_.empty() || static_cast<int32_t>(this->busy_until_ - millis()) > 0) {
    this->pending_ = state;
    this->has_pending_ = true;
    return;
  }
  this->apply_(state);
}

void ReplayDimmer::loop() {
  const uint32_t now = millis();
  for (auto it = this->steps_.begin(); it != this->steps_.end();) {
    if (static_cast<int32_t>(now - it->due) >= 0) {
      std::vector<std::vector<uint8_t>> one;
      one.push_back(this->frames_[it->kind][it->index]);
      this->parent_->send(one, 0, this->copies_);
      it = this->steps_.erase(it);
    } else {
      ++it;
    }
  }
  if (this->has_pending_ && this->steps_.empty() && static_cast<int32_t>(now - this->busy_until_) >= 0) {
    this->has_pending_ = false;
    this->apply_(this->pending_);
  }
}

void ReplayDimmer::apply_(float target) {
  if (this->frames_[0].size() < 2 || this->frames_[1].size() < 2 || this->frames_[2].size() < 3 ||
      this->frames_[3].size() < 3) {
    ESP_LOGE(TAG, "Not enough frames configured");
    return;
  }
  uint32_t t = millis();
  if (target <= 0.01f) {
    this->steps_.push_back({t, 1, 0});
    this->steps_.push_back({t + 70, 1, 1});
    this->on_ = false;
    this->busy_until_ = t + 400;
    ESP_LOGI(TAG, "Off");
    return;
  }
  if (!this->on_) {
    // the dimmer comes on with its last value
    this->steps_.push_back({t, 0, 0});
    this->steps_.push_back({t + 70, 0, 1});
    this->on_ = true;
    t += 600;
  }
  // one dimming run: press, the dim frame after hold_delay, the end frame after the dimming time
  auto dim = [&](bool up, uint32_t duration) {
    const uint8_t kind = up ? 2 : 3;
    this->steps_.push_back({t, kind, 0});
    this->steps_.push_back({t + this->hold_ms_, kind, 1});
    this->steps_.push_back({t + this->hold_ms_ + duration, kind, 2});
    t += this->hold_ms_ + duration + 300;
  };
  const uint32_t full = this->dim_ms_ + this->dim_ms_ / 10;
  if (this->level_ < 0.0f) {  // the level is not known: go to the bottom first
    dim(false, full);
    this->level_ = MIN_LEVEL;
  }
  if (target >= 0.99f) {
    dim(true, full);
    this->level_ = 1.0f;
  } else if (target <= 0.05f) {
    dim(false, full);
    this->level_ = MIN_LEVEL;
  } else {
    const float delta = target - this->level_;
    const uint32_t duration = static_cast<uint32_t>(fabsf(delta) * this->dim_ms_);
    if (duration >= 150) {
      dim(delta > 0.0f, duration);
      this->level_ = target;
    }
  }
  this->busy_until_ = t;
  ESP_LOGI(TAG, "Target %.0f %%, estimated level %.0f %%", target * 100.0f, this->level_ * 100.0f);
}

void ReplayDimmer::dump_config() {
  ESP_LOGCONFIG(TAG, "Replay dimmer:");
  ESP_LOGCONFIG(TAG, "  Dim time (dark to bright): %u ms", (unsigned) this->dim_ms_);
  ESP_LOGCONFIG(TAG, "  Hold delay: %u ms", (unsigned) this->hold_ms_);
}

}  // namespace esphome::elsner_remo_replay

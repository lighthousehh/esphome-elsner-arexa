#include "elsner_replay.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"

namespace esphome::elsner_replay {

static const char *const TAG = "elsner_replay";

void ElsnerReplay::send(const std::vector<std::vector<uint8_t>> &frames, uint32_t gap_ms, uint8_t copies) {
  const uint32_t now = millis();
  for (size_t i = 0; i < frames.size(); i++)
    for (uint8_t c = 0; c < copies; c++)
      this->queue_.push_back({frames[i], now + static_cast<uint32_t>(i) * gap_ms + c * 30u});
  ESP_LOGI(TAG, "Queued %u frame(s), %u copies each", (unsigned) frames.size(), (unsigned) copies);
}

void ElsnerReplay::loop() {
  if (this->queue_.empty())
    return;
  const uint32_t now = millis();
  for (auto it = this->queue_.begin(); it != this->queue_.end(); ++it) {
    if (static_cast<int32_t>(now - it->due) >= 0) {
      Pending p = *it;
      this->queue_.erase(it);
      this->transmit_(p.frame);
      return;
    }
  }
}

// The same way elsner_arexa sends: the chip does the Manchester coding; sync word 00 0a (the zero byte gives 16
// alternating chips like the RC's preamble, 0a is the anchor), then the 38 frame bytes.
void ElsnerReplay::transmit_(const std::vector<uint8_t> &frame) {
  if (this->radio_ == nullptr || this->radio_->is_failed() || frame.size() != 38)
    return;
  auto *r = this->radio_;
  r->set_manchester(true);
  r->set_sync1(0x00);
  r->set_sync0(0x0a);
  r->set_packet_length(frame.size());
  r->set_num_preamble(0);
  r->set_fsk_deviation(40e3f);
  r->set_output_power(this->output_power_);
  ESP_LOGI(TAG, "Sending %s", format_hex(frame.data(), frame.size()).c_str());
  const auto err = r->transmit_packet(frame);
  if (err != cc1101::CC1101Error::NONE)
    ESP_LOGW(TAG, "transmit_packet failed: %d", (int) err);
  if (this->arexa_ != nullptr)
    this->arexa_->start_listening();
}

void ElsnerReplay::dump_config() {
  ESP_LOGCONFIG(TAG, "Elsner Replay:");
  ESP_LOGCONFIG(TAG, "  Output power: %.1f dBm", this->output_power_);
}

}  // namespace esphome::elsner_replay

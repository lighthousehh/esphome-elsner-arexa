Post in HA forum (original project): https://community.home-assistant.io/t/elsner-arexa-solexa-868-mhz-radio-in-home-assistant-with-esphome-cc1101

# Elsner Connect with Remo pro: conservatory control for LED light and awning

An ESPHome component set that controls a conservatory (Wintergarten) from Home Assistant through an Elsner **Remo pro**:
an **RF-L LED-ST** dimmer for the LED light and an **RF-MSG-ST** receiver for the awning (Markise). With an ESP32 and a
CC1101 868 MHz module it gives you in Home Assistant:

- **A dimmable light** for the LED dimmer: on, off and brightness, set the way the Remo pro does it.
- **An awning cover** with position, open, close and stop (travel times are set in the YAML).
- **Buttons** for short steps and full runs of the awning (up and down).
- **Diagnostics:** the radio level of the Remo pro and a text sensor with every frame received and sent, to record new frames.

Nothing has to be opened or re-paired: the receivers stay paired to your Remo pro, and the ESP only sends frames that
were recorded from it. The Remo pro keeps working as before.

It is based on [dbuezas/esphome-elsner-arexa](https://github.com/dbuezas/esphome-elsner-arexa) (the radio and the protocol for the
Elsner Arexa window control), which is still included as `elsner_remo`.

## Setup

It needs ESPHome's `cc1101` component (ESPHome 2026.10 or newer).

```yaml
external_components:
  - source: github://lighthousehh/esphome-elsner-remo@main
    components: [elsner_remo, elsner_remo_replay]

cc1101:
  - id: radio_arexa
    cs_pin: GPIO5
    gdo0_pin: GPIO4
    packet_mode: true    # needed: elsner_remo sets all other radio settings itself
    packet_length: 64    # any value: elsner_remo sets its own

elsner_remo:
  id: remo
  cc1101_id: radio_arexa
  # frequency: 868.19MHz   # 868.19 MHz + your module's crystal error

elsner_remo_replay:
  id: replay
  cc1101_id: radio_arexa
  elsner_remo_id: remo

output:
  - platform: elsner_remo_replay
    id: dimmer_out
    dim_time: 4s
    switch_on: [<frame>, <frame>]
    switch_off: [<frame>, <frame>]
    dim_up: [<frame>, <frame>, <frame>]
    dim_down: [<frame>, <frame>, <frame>]

light:
  - platform: monochromatic
    name: Wintergarten Licht
    output: dimmer_out

button:
  - platform: elsner_remo_replay
    id: markise_auf_fahren
    name: Markise Auf fahren
    gap: 1000ms
    frames: [<frame>, <frame>, <frame>]
  # more buttons: Auf kurz, Ab kurz, Ab fahren

cover:
  - platform: time_based
    name: Markise
    open_duration: 21.80s
    close_duration: 22.11s
    # open_action, close_action, stop_action: see the full example
```

Every `<frame>` is a frame recorded from the Remo pro: 38 bytes = 76 hex digits, as the `last_frame` text sensor shows it
(without the `ok -61` in front). The full example with light and awning is in
[examples/wintergarten-komplett.yaml](https://github.com/lighthousehh/esphome-elsner-remo/blob/main/examples/wintergarten-komplett.yaml).

| Platform | Component | Keys |
|---|---|---|
| `output` | `elsner_remo_replay` | `switch_on`, `switch_off`, `dim_up`, `dim_down`, `dim_time`, `hold_delay`, `copies` |
| `button` | `elsner_remo_replay` | `frames`, `gap`, `copies` |
| `sensor` | `elsner_remo` | `rc_rssi` (radio level of the Remo pro), `rc_freq_offset` |
| `text_sensor` | `elsner_remo` | `pairing`, `last_frame`: every frame received and sent, raw, to record new ones |

## Remo pro: elsner_remo_replay

`elsner_remo_replay` sends frames that were recorded from a Remo pro, with the same CC1101 and radio setup as
`elsner_remo`. It controls receivers that are paired to a Remo pro (tested with an RF-L LED-ST dimmer and an
RF-MSG-ST awning receiver) without pairing them again. It does not decode or build frames itself. A frame sent this way is
only valid for a receiver that takes its counter (see Counter), so record your own and do not copy the ones from the examples.

**Recording the frames:** with `elsner_remo` in your YAML, press a button on the Remo pro (a short tap, or hold and
release) and copy the frames from the `last_frame` text sensor (`Letzter Rahmen`): each one is 38 bytes = 76 hex
digits (without the `ok -61` in front). A tap is two frames (press, release). Hold-and-release is three
(press, hold, end). The channel of the Remo pro is in byte 19 of the descrambled packet (`08` for the light, `0c` for the
awning on my system); the command codes are the same for all channels.

Defaults: `gap` `100ms`, `copies` 3 (each frame is sent 3 times, 30 ms apart), `dim_time` `4s` (the time from the darkest to
the brightest), `hold_delay` `1000ms`.

**Dimmer:** the `output` is for a `monochromatic` light. It sets the brightness the way the Remo pro does it: a press frame,
the dim frame after `hold_delay`, and the end frame after the time needed for the change. The receiver reports nothing, so
the level is an estimate: it goes to the bottom or the top when 0 to 5 % or 99 to 100 % is asked, which brings it back
in line.

**Awning:** a `time_based` cover that presses the `Auf fahren` and `Ab fahren` buttons works well. The awning has no
stop command; a short tap of the opposite direction stops it. The cover has to send that tap only between the end
positions, otherwise it moves the awning a little after every full run.

## Radio and sending

**Frequency:** cheap CC1101 modules are often 20 to 40 kHz off. The default is 868.19 MHz (`frequency` of `elsner_remo`;
allowed are 867.9 to 868.5 MHz). If a receiver does not react, try steps of 10 kHz between 868.15 and 868.24 MHz: in the
original project one module needed 868.227 MHz to come out at 868.19 MHz. The `rc_rssi` sensor and the `last_frame` text sensor show
whether packets arrive.

**Sending:** a button press or a dimmer change puts its frames into a queue: frame number i goes out i times `gap` after the
press, each one as `copies` copies 30 ms apart. A new press adds its frames to the queue. `output_power` of
`elsner_remo_replay` (default 11 dBm, from -30 to 11) sets the transmit power. After every frame the radio goes back into
receive mode.

**No confirmation:** the receivers do not answer, so the ESP cannot tell whether a command arrived. You see it on the light
or the awning. The light level and the awning position are estimates (the dimmer from `dim_time`, the awning from the travel
times of the `time_based` cover); a full run to an end position brings them back in line. If the light or the awning is
moved some other way (with the Remo pro, by hand), the value in Home Assistant is wrong until the next full run.

**Sharing the radio:** if something else uses the same CC1101 (for example a `remote_transmitter` in OOK mode), call
`id(remo).start_listening();` after it (use the id of your `elsner_remo`), to put the radio back into receive mode.

## Arexa window control

The component `elsner_remo` also contains the Elsner Arexa window control (buttons, weather sensors and the window's state) of
the original project. It is documented in the [original README](https://github.com/dbuezas/esphome-elsner-arexa#readme); there it is
called `elsner_arexa`, here `elsner_remo`. An example is in [examples/elsner-arexa.yaml](examples/elsner-arexa.yaml).

## How it works

I decoded the protocol with an RTL-SDR, starting from the rtl_433 decoder `elsner_solexa` (364), which knows the
frame and the CRC. The Solexa (the shade version) uses the same radio protocol: my model also decodes its
recordings in rtl_433_tests (the same commands, and its sensor packet differs only in bytes 19, 20), so the
buttons may work there too. rtl_433's decoder describes the same scrambling differently (a bit transform plus a
"rolling state"); its `spread_k(seed)` is the seed part of the running sum here. Other Elsner RF devices (Solexa
II, Solexa Home, WS1, Remo remotes, RF-MSG-ST) use "Elsner RF" at 868.2 MHz too; I found no public decoding of them.
The Remo pro, the RF-L LED-ST and the RF-MSG-ST can be controlled with recorded frames (see "Remo pro: elsner_remo_replay").

Receiving: the chip decodes the Manchester itself, synced on the first two frame bytes `ce ad` (the preamble is
too short to fix the chip phase; the sync word does). The 36 bytes after it, with the CRC, fit the 64-byte FIFO.
Only packets whose CRC matches are used: the chip's decoder does not say which bytes are broken. Where a chip pair
is broken, it guesses the bit, so many damaged packets have just one wrong bit: the CRC finds and repairs it. A
repair can also turn a packet with 3 or more wrong bits into a wrong one (about 1 in 230 of those), so a repaired
packet only confirms a send (it must carry the station's address, my system ID and the exact counter sent); the
sensors, the counter and the RC events come only from packets whose CRC matched as received. I also tried raw
chips decoded on the ESP (sync on the 16 chips of `ce`, 74 FIFO bytes read while the packet arrives, damaged packets
used for the fields with a check of their own): over 4 hours alternating, 29% of the station's packets came in
with a matching CRC that way, against 42% with the chip's decoder. The station answers the RC 14 ms after its packet, so the component sets the main loop interval to 2 ms (the
default 16 ms misses most answers). The gain is fixed (no AGC): with the AGC, the gain was still low from the
RC's packet when the station answered, 16 dB weaker, and 43% of its packets came with wrong bits; with the gain
fixed, 6% (4 hours alternating). FSK needs no gain control. The gain is fixed with the DVGA's 3 highest steps left
out: without that limit it did not always settle at the same level, and the higher ones broke the station's
packets (87% of them usable with the limit against 46% without, 6 hours alternating). Sending: the chip does
the Manchester coding itself (an ESP8266 cannot time 10 µs chips in software while WiFi runs).

## Protocol

### Radio

- 868.19 MHz, 2-FSK. Deviation about ±35 kHz (RC) and ±45 kHz (station).
- Manchester: a 1 is the chips `10`, a 0 is `01`. Chips of exactly **10.000 µs** (100 kbaud). rtl_433's flex
  setting `short=11` works only because it is tolerant.
- A short preamble (about 13 alternating chips), the anchor byte `0a`, then the 38-byte frame.
- The RC and the station talk once a minute (the RC sends its status, the station answers 14 ms later), and on
  every button press (the RC repeats a command until the station answers).

### Frame

| Bytes | Content |
|---|---|
| 0..3 | `ce ad 93 ba` |
| 4 | seed: random for every packet |
| 5..35 | payload, scrambled (below) |
| 36..37 | CRC-16 over bytes 0..35: polynomial 0x1021, init 0x68b3 |

### Scrambling

With `d[k] = c[k] - 2 * c[k-1]` (mod 256, on the raw bytes `c` as sent), every payload byte is

```
d[k] = value[k] + (parity(seed & mask[k]) ^ inv[k])        seed = c[4]
```

| k | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mask | 01 | 01 | 01 | 01 | 01 | 01 | 01 | 81 | c1 | e1 | f1 | f9 | fd | ff | fe | ff | fe | ff | fe | ff | fe | ff | 7e | bf | 5e | af | 56 | ab | 54 | aa | 55 |
| inv | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 1 |

So `value[k] = c[k] - 2 * c[k-1] - (parity(seed & mask[k]) ^ inv[k])`. To build a frame: pick a seed, compute
`d[k]` and then `c[k] = d[k] + 2 * c[k-1]` from k = 5 on. This model rebuilds all 353 frames of my RC bit for bit.

### Values

The descrambled bytes `v[k]` hold the header as is, but numbers in a second, simpler form: a running sum.

| Bytes | Content |
|---|---|
| 5..7 | the counter (below) |
| 8, 9 | system ID (set by the teach-in), repeated in 13, 14 |
| 10 | sender address |
| 15 | receiver address |
| 11, 12, 16 | device type |
| 17.. | the command (RC) or the measurements (station), as a running sum (below) |

### Counter

`n = k << 8 | (v5 - 1)` with `k = v6 + 2 * v5`: 16 bits, counting down by one per packet (the RC's own wraps:
`ae00`, `adff`, `adfe`). Byte 7 is a check: `v7 + 2 * k` is the same in every packet of a system (`f7` on mine, `48`
on the Solexa of rtl_433's recordings). The station takes a command whose counter is newer than its last one: lower,
mod 2^16 (so up to 32767 steps ahead). That also covers the RC after a command from the gateway: its next status has
an older counter, the station ignores it, the RC shows "err" and resyncs (below). To send:
`v5 = (n & ff) + 1`, `v6 = k - 2 * v5`, `v7 = check - 2 * k`.

### Running sum

From byte 17 on, `u[17] = v[17]` and `u[k] = v[k] + 2 * u[k-1]`. Then every value is a plain number: a 16-bit value
is `(b0 - u[k]) | (b1 - u[k+1]) << 8` with these bases (in the raw `v`, every byte after a value looked like a check
byte `constant - 2 * value`: that was this sum).

| Sender | Bytes (`u`) | Content |
|---|---|---|
| RC | 17, 18 | command: `25 04` open, `27 04` stop, `36 04` close, `6a f3` automatic mode, `6a e7` manual mode, `6a 04` status (once a minute) |
| RC status | 22, 23 | inside temperature in 0.1 °C, signed, bases `40 80` |
| station | 17, 18 | outside temperature in 0.1 °C, signed, bases `9a 34` |
| station | 19, 20 | wind in 0.1 m/s, bases `68 d0` |
| station | 21 | rain alarm: `52` dry, `4e` wet (byte 26 the same: `b2`, `ae`) |
| station | 22, 23 | brightness, about 1.05 lx per step, bases `3c 80`; byte 24 `00` |
| station | 25 | mode: `b3` manual, `bf` automatic |
| station | 28 | wind flag: `8b` calm |
| station | 29 | rain sensor reading: `bc` dry, lower = wetter |
| station | 27 | not decoded: `b2` in all packets so far |
| both | rest | filler: `d0` (`30` in `v`) |

The RC sends the commands as `v` (bytes 17..19, also on the Solexa): `25 ba 30` open, `27 b6 30` stop, `36 98 30`
close, `6a 1f 52` automatic, `6a 13 6a` manual, `6a 30 30` status. A start-up packet after a battery change has
`00`/`ff` in bytes 31..35 instead of the filler.

Checked on a week of station packets (1189, all decode; seen from -0.7 to 12.4 °C), the RC from -1 to 25 °C, and
on rtl_433's Solexa recordings: the same commands, the RC's inside temperature with the same bases (20.6 °C), and
the station's packet the same except bytes 19, 20 (the Solexa's sensor has no wind there).

In `v` this looked like a different formula for each value (a sign bit in byte 18, the temperature's high part in
the wind byte, bit 7 of the brightness only in byte 23), and a value that changed (the rain alarm) broke the next
one (the brightness while it rained).

### Resync

When the RC's counter is stale (it got an "err", for example after the gateway sent commands), it picks a new
counter at random and announces it. The station answers, and both count down from there. Nothing in it is secret:
the request names the new counter in clear.

| Bytes | Request (RC) | Answer (station) |
|---|---|---|
| 5..7 | the new counter (any value; byte 7 with the system's check) | the same |
| 10, 15 | RC, station address | station, RC address |
| 11, 12 | `82 ff` | `4d 01` |
| 16 | `2 * seed + 53 + p` | `2 * seed + 87 + p` |
| 17..35 | one bit per byte (`00` = 0, `ff` = 1) | the same, its own bits |

Bits 17..31 are a random tag. The rest follows from it: `b32 = b17 ^ b31`, `b33 = b32 ^ b18`, `b34 = b33 ^ b19`,
`b35 = b34 ^ b20`, and `p = b30 ^ b31 ^ 1`. The answer's tag is new, not a copy of the request's. The station does
not check the tag: it also answered requests with a wrong check bit.

This model rebuilds all 59 recorded requests bit for bit from the counter, the seed and the tag; in all 59 the RC's
next packets continue from the counter it announced.

Tested by sending requests from the gateway (2026-11-07):

- A recorded request, replayed as is: answered.
- The same with a new seed, or a new tag (check bits computed): answered.
- Made-up requests (counter, seed, tag): answered, also with a wrong check bit (`b35`, or `p` in byte 16). A Stop on
  such a counter was confirmed.
- Requests with a wrong counter check (byte 7): no answer, 3 tries each.

The component uses this: without a counter (after a start), or when no send of a command is answered, it announces
a random counter and sends the command on it. A resync can put the station's counter behind the RC's: then the
station takes the RC's next status (newer), and the RC needs no resync.

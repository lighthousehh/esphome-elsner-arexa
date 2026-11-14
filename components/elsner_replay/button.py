import esphome.codegen as cg
from esphome.components import button
import esphome.config_validation as cv

from . import CONF_ELSNER_REPLAY_ID, ElsnerReplay, elsner_replay_ns

DEPENDENCIES = ["elsner_replay"]

ReplayButton = elsner_replay_ns.class_("ReplayButton", button.Button)

CONF_FRAMES = "frames"
CONF_GAP = "gap"
CONF_COPIES = "copies"


def frame(value):
    """A whole captured frame: 38 bytes = 76 hex digits, as the 'Letzter Rahmen' text sensor shows it."""
    text = cv.string(value).replace(" ", "").lower()
    if len(text) != 76 or any(ch not in "0123456789abcdef" for ch in text):
        raise cv.Invalid(
            "a frame is 38 bytes = 76 hex digits, as the 'Letzter Rahmen' text sensor shows them (without 'ok -61')"
        )
    return [int(text[i : i + 2], 16) for i in range(0, 76, 2)]


CONFIG_SCHEMA = button.button_schema(ReplayButton).extend(
    {
        cv.GenerateID(CONF_ELSNER_REPLAY_ID): cv.use_id(ElsnerReplay),
        # the frames are sent one after the other, each one `gap` after the one before
        cv.Required(CONF_FRAMES): cv.ensure_list(frame),
        cv.Optional(CONF_GAP, default="100ms"): cv.positive_time_period_milliseconds,
        # copies of each frame, 30 ms apart (like the Arexa RC)
        cv.Optional(CONF_COPIES, default=3): cv.int_range(min=1, max=5),
    }
)


async def to_code(config):
    hub = await cg.get_variable(config[CONF_ELSNER_REPLAY_ID])
    b = await button.new_button(config)
    await cg.register_parented(b, hub)
    for f in config[CONF_FRAMES]:
        cg.add(b.add_frame(f))
    cg.add(b.set_gap(config[CONF_GAP]))
    cg.add(b.set_copies(config[CONF_COPIES]))

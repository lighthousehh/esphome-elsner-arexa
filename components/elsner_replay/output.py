import esphome.codegen as cg
from esphome.components import output
import esphome.config_validation as cv
from esphome.const import CONF_ID

from . import CONF_ELSNER_REPLAY_ID, ElsnerReplay, elsner_replay_ns

DEPENDENCIES = ["elsner_replay"]

ReplayDimmer = elsner_replay_ns.class_("ReplayDimmer", output.FloatOutput, cg.Component)

CONF_DIM_TIME = "dim_time"
CONF_HOLD_DELAY = "hold_delay"
CONF_COPIES = "copies"

# the order of the kinds in dimmer.h: switch_on, switch_off: press + release; dim_up, dim_down: press + hold + end
KINDS = {"switch_on": 2, "switch_off": 2, "dim_up": 3, "dim_down": 3}


def frame(value):
    """A whole captured frame: 38 bytes = 76 hex digits, as the 'Letzter Rahmen' text sensor shows it."""
    text = cv.string(value).replace(" ", "").lower()
    if len(text) != 76 or any(ch not in "0123456789abcdef" for ch in text):
        raise cv.Invalid(
            "a frame is 38 bytes = 76 hex digits, as the 'Letzter Rahmen' text sensor shows them (without 'ok -61')"
        )
    return [int(text[i : i + 2], 16) for i in range(0, 76, 2)]


def frames(count):
    return cv.All(cv.ensure_list(frame), cv.Length(min=count, max=count))


CONFIG_SCHEMA = output.FLOAT_OUTPUT_SCHEMA.extend(
    {
        cv.Required(CONF_ID): cv.declare_id(ReplayDimmer),
        cv.GenerateID(CONF_ELSNER_REPLAY_ID): cv.use_id(ElsnerReplay),
        # the time the dimmer needs from the darkest to the brightest, from the start of the dimming (after hold_delay)
        cv.Optional(CONF_DIM_TIME, default="4s"): cv.positive_time_period_milliseconds,
        # the time between the press frame and the dim frame (the Remo pro sends it after about 1 s)
        cv.Optional(CONF_HOLD_DELAY, default="1000ms"): cv.positive_time_period_milliseconds,
        cv.Optional(CONF_COPIES, default=3): cv.int_range(min=1, max=5),
        **{cv.Required(key): frames(count) for key, count in KINDS.items()},
    }
).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await output.register_output(var, config)
    hub = await cg.get_variable(config[CONF_ELSNER_REPLAY_ID])
    await cg.register_parented(var, hub)
    cg.add(var.set_dim_time(config[CONF_DIM_TIME]))
    cg.add(var.set_hold_delay(config[CONF_HOLD_DELAY]))
    cg.add(var.set_copies(config[CONF_COPIES]))
    for kind, key in enumerate(KINDS):
        for f in config[key]:
            cg.add(var.add_frame(kind, f))

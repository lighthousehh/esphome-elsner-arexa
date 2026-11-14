import esphome.codegen as cg
from esphome.components import button
import esphome.config_validation as cv

from . import CONF_ELSNER_REMO_ID, ElsnerRemo, elsner_remo_ns

DEPENDENCIES = ["elsner_remo"]

RemoButton = elsner_remo_ns.class_("RemoButton", button.Button)

# the RC buttons, in the order of the Command enum (elsner_remo.h)
TYPES = {
    "open": "mdi:window-open-variant",
    "stop": "mdi:stop",
    "close": "mdi:window-closed-variant",
    "auto": "mdi:refresh-auto",
    "manual": "mdi:hand-back-right",
}

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_ELSNER_REMO_ID): cv.use_id(ElsnerRemo),
        **{cv.Optional(k): button.button_schema(RemoButton, icon=icon) for k, icon in TYPES.items()},
    }
)


async def to_code(config):
    hub = await cg.get_variable(config[CONF_ELSNER_REMO_ID])
    for cmd, key in enumerate(TYPES):
        if key in config:
            b = await button.new_button(config[key])
            await cg.register_parented(b, hub)
            cg.add(b.set_command(cmd))

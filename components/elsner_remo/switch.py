import esphome.codegen as cg
from esphome.components import switch
import esphome.config_validation as cv

from . import CONF_ELSNER_REMO_ID, ElsnerRemo, elsner_remo_ns

DEPENDENCIES = ["elsner_remo"]

RemoAutoModeSwitch = elsner_remo_ns.class_("RemoAutoModeSwitch", switch.Switch)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_ELSNER_REMO_ID): cv.use_id(ElsnerRemo),
        # on: automatic mode, off: manual (the state follows the station)
        cv.Optional("auto_mode"): switch.switch_schema(RemoAutoModeSwitch, icon="mdi:refresh-auto"),
    }
)


async def to_code(config):
    hub = await cg.get_variable(config[CONF_ELSNER_REMO_ID])
    if "auto_mode" in config:
        s = await switch.new_switch(config["auto_mode"])
        await cg.register_parented(s, hub)
        cg.add(hub.set_auto_mode_switch(s))

import esphome.codegen as cg
from esphome.components import cc1101, elsner_remo
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_OUTPUT_POWER

CODEOWNERS = ["@lighthousehh"]
DEPENDENCIES = ["cc1101", "elsner_remo"]
AUTO_LOAD = ["output"]

CONF_CC1101_ID = "cc1101_id"
CONF_ELSNER_REMO_ID = "elsner_remo_id"
CONF_ELSNER_REMO_REPLAY_ID = "elsner_remo_replay_id"

elsner_remo_replay_ns = cg.esphome_ns.namespace("elsner_remo_replay")
ElsnerRemoReplay = elsner_remo_replay_ns.class_("ElsnerRemoReplay", cg.Component)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(ElsnerRemoReplay),
        cv.Required(CONF_CC1101_ID): cv.use_id(cc1101.CC1101Component),
        cv.Required(CONF_ELSNER_REMO_ID): cv.use_id(elsner_remo.ElsnerRemo),
        cv.Optional(CONF_OUTPUT_POWER, default=11): cv.float_range(min=-30.0, max=11.0),
    }
).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    radio = await cg.get_variable(config[CONF_CC1101_ID])
    remo = await cg.get_variable(config[CONF_ELSNER_REMO_ID])
    cg.add(var.set_radio(radio))
    cg.add(var.set_remo(remo))
    cg.add(var.set_output_power(config[CONF_OUTPUT_POWER]))

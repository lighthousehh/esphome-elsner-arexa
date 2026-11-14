import esphome.codegen as cg
from esphome.components import cc1101, elsner_arexa
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_OUTPUT_POWER

CODEOWNERS = ["@lighthousehh"]
DEPENDENCIES = ["cc1101", "elsner_arexa"]

CONF_CC1101_ID = "cc1101_id"
CONF_ELSNER_AREXA_ID = "elsner_arexa_id"
CONF_ELSNER_REPLAY_ID = "elsner_replay_id"

elsner_replay_ns = cg.esphome_ns.namespace("elsner_replay")
ElsnerReplay = elsner_replay_ns.class_("ElsnerReplay", cg.Component)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(ElsnerReplay),
        cv.Required(CONF_CC1101_ID): cv.use_id(cc1101.CC1101Component),
        cv.Required(CONF_ELSNER_AREXA_ID): cv.use_id(elsner_arexa.ElsnerArexa),
        cv.Optional(CONF_OUTPUT_POWER, default=11): cv.float_range(min=-30.0, max=11.0),
    }
).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    radio = await cg.get_variable(config[CONF_CC1101_ID])
    arexa = await cg.get_variable(config[CONF_ELSNER_AREXA_ID])
    cg.add(var.set_radio(radio))
    cg.add(var.set_arexa(arexa))
    cg.add(var.set_output_power(config[CONF_OUTPUT_POWER]))

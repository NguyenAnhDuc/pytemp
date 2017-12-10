#!/usr/bin/python
# -*- coding: utf8 -*-
""" Author: Ly Tuan Anh
    github nick: ongxabeou
    mail: lytuananh2003@gmail.com
    Date created: 2017/04/28
"""

from controllers import CUSTOMER_STRUCTURE, META_CLASS
from controllers.base_controller import BaseController
from libs.http_validator import Required, Length, Unicode, Range, In, Equals, InstanceOf
from models import BOT_STRUCTURE, CONSUMER
from models.bot_config_repository import BotConfigRepository


class BotController(BaseController):
    def __init__(self, bot_id):
        super(BotController, self).__init__()
        self.abort_if_param_empty_error(bot_id, 'bot_id')
        self.bot_id = bot_id

    def put(self, customer):
        self.abort_if_param_empty_error(customer, 'thông tin khách hàng')

        rules = {
            CUSTOMER_STRUCTURE.ID: [Required, InstanceOf(str), Length(0, maximum=36)],
            CUSTOMER_STRUCTURE.NAME: [Required, InstanceOf(str), Unicode(), Length(0, maximum=64)],
            CUSTOMER_STRUCTURE.AGE: [InstanceOf(int), Range(13, 100)],
            CUSTOMER_STRUCTURE.GENDER: [InstanceOf(int), In([0, 1, 2])],
            CUSTOMER_STRUCTURE.MESSAGE: [Required, InstanceOf(str), Length(0, maximum=1024)],
        }

        self.abort_if_validate_error(rules, customer)

        return 'say hello, đây là project mẫu'

    def delete(self):
        return BotConfigRepository().delete(self.bot_id)

    def set(self, bot_config):
        self.abort_if_param_empty_error(bot_config, 'bot config')

        rules = {
            BOT_STRUCTURE.ID: [Required, Length(0, maximum=36)],
            BOT_STRUCTURE.NAME: [Required, Unicode(), Length(0, maximum=64)],
            BOT_STRUCTURE.DESC: [Required, Length(0, maximum=1024)],
            BOT_STRUCTURE.TOKEN: [Required, Length(0, maximum=64)],
            BOT_STRUCTURE.NLP_KEY: [Required, Length(0, maximum=64)],
            BOT_STRUCTURE.META_CLASS: [Required],
            BOT_STRUCTURE.CONSUMER: [Required]
        }

        self.abort_if_validate_error(rules, bot_config)

        rules_for_mata_class = {
            META_CLASS.MODULE_NAME: [Required, Length(0, maximum=64)],
            META_CLASS.CLASS_NAME: [Required, Length(0, maximum=64)],
        }

        self.abort_if_validate_error(rules_for_mata_class, bot_config[BOT_STRUCTURE.META_CLASS])

        rules_for_consumer = {
            CONSUMER.ID: [Required, Length(0, maximum=64)],
            CONSUMER.NAME: [Required, Length(0, maximum=64)],
            CONSUMER.ADDRESS: [Required, Length(0, maximum=128)],
            CONSUMER.PRODUCT: [Required, Length(0, maximum=128)],
            CONSUMER.PHONE: [Required, Length(0, maximum=16)],
            CONSUMER.UNIT: [Required, Length(0, maximum=64)],
        }
        self.abort_if_validate_error(rules_for_consumer, bot_config[BOT_STRUCTURE.CONSUMER])

        return BotConfigRepository().set(self.bot_id, bot_config)

    def get(self):
        return BotConfigRepository().get(self.bot_id)

    def register(self, bot_config):
        self.abort_if_param_empty_error(bot_config, 'bot config')
        rules = {
            BOT_STRUCTURE.ID: [Required, Length(0, maximum=36)],
            BOT_STRUCTURE.NAME: [Required, Unicode(), Length(0, maximum=64)],
            BOT_STRUCTURE.DESC: [Required, Length(0, maximum=1024)],
            BOT_STRUCTURE.TOKEN: [Required, Length(0, maximum=64)],
            BOT_STRUCTURE.NLP_KEY: [Required, Length(0, maximum=64)],
            BOT_STRUCTURE.META_CLASS: [Required],
            BOT_STRUCTURE.CONSUMER: [Required]
        }
        self.abort_if_validate_error(rules, bot_config)

        rules_for_mata_class = {
            META_CLASS.MODULE_NAME: [Required, Length(0, maximum=64)],
            META_CLASS.CLASS_NAME: [Required, Length(0, maximum=64)],
        }
        self.abort_if_validate_error(rules_for_mata_class, bot_config[BOT_STRUCTURE.META_CLASS])

        rules_for_consumer = {
            CONSUMER.ID: [Required, Length(0, maximum=64)],
            CONSUMER.NAME: [Required, Length(0, maximum=64)],
            CONSUMER.ADDRESS: [Required, Length(0, maximum=128)],
            CONSUMER.PRODUCT: [Required, Length(0, maximum=128)],
            CONSUMER.PHONE: [Required, Length(0, maximum=16)],
            CONSUMER.UNIT: [Required, Length(0, maximum=64)],
        }
        self.abort_if_validate_error(rules_for_consumer, bot_config[BOT_STRUCTURE.CONSUMER])

        return BotConfigRepository().register(self.bot_id, bot_config)

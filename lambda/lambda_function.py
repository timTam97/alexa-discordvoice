import ast
import logging
from typing import Tuple

import ask_sdk_core.utils as ask_utils
import auth
import requests
from ask_sdk_core.dispatch_components import (AbstractExceptionHandler,
                                              AbstractRequestHandler)
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


members = []


def create_grammar(num_members: int, num_channels: int) -> Tuple[str, str]:
    member_addresser = "people"
    ch_addresser = "channels"
    if num_channels == 1:
        ch_addresser = "channel"
    if num_members == 1:
        member_addresser = "person"
    return member_addresser, ch_addresser


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        global members
        voice_data = requests.get(
            auth.API_BASE_URL + "/members",
            headers={"Authorization": auth.HEADER_AUTH},
        ).json()
        member_count = voice_data["member_count"]
        channel_count = voice_data["occupied_channels"]
        members = list(
            map(
                lambda x: x.get("name"),
                [
                    item
                    for sublist in [sub for sub in voice_data["channels"].values()]
                    for item in sublist
                ],
            )
        )
        people, channels = create_grammar(member_count, channel_count)
        speak_output = "There are {} {} in {} {} on the server.".format(
            member_count, people, channel_count, channels
        )

        if len(members) > 0:
            speak_output += " Would you like to know who they are?"
            return (
                handler_input.response_builder.speak(speak_output)
                .ask(speak_output)
                .response
            )
        return handler_input.response_builder.speak(speak_output).response


class ListMembersIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name("ListMembersIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.speak(", ".join(members)).response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder.speak(speak_output)
            .ask(speak_output)
            .response
        )


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ListMembersIntentHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()

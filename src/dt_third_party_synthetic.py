# use an override of the original Dynatrace API wrapper to let me create a test with no result (only alarms)
from dynatrace_local_override import Dynatrace
from dynatrace.environment_v1.synthetic_third_party import SYNTHETIC_EVENT_TYPE_OUTAGE

from datetime import datetime
from typing import Optional

import json
import socket

engine = "SikuliX"


def build_proxy_url(proxy_address, proxy_username, proxy_password):

    if proxy_address:
        protocol, address = proxy_address.split("://")
        proxy_url = f"{protocol}://"
        if proxy_username:
            proxy_url += proxy_username
        if proxy_password:
            proxy_url += f":{proxy_password}"
        proxy_url += f"@{address}"
        return {"https": proxy_url}

    return {}


def get_client(
    api_url: str,
    api_token: str,
    proxy_address: Optional[str] = None,
    proxy_username: Optional[str] = None,
    proxy_password: Optional[str] = None
):
    # The Dynatrace API client
    return Dynatrace(api_url, api_token, proxies=build_proxy_url(
        proxy_address, proxy_username, proxy_password))


# send test execution results to Dynatrace with Synthetic third party API
def process_third_party_results(
    script: str,
    result_file: str,
    log: str,
    url: str,
    dt_client: Dynatrace,
    is_error: bool,
    frequency: int
):

    the_test_id = engine + "_" + script
    the_test_title = script

    # get results from last execution

    details = []

    f = open(result_file, "r")
    for line in f:
        details.append(json.loads(line))
    f.close()

    scenario_status = True

    test_step_list = []
    test_step_results_list = []

    # process response times
    for step in details:

        test_step = dt_client.third_part_synthetic_tests.create_synthetic_test_step(
            step['id'], step['title'])
        test_step_list.append(test_step)

        test_time = datetime.fromtimestamp(round(step["startTimestamp"])/1000)
        test_step_results = dt_client.third_part_synthetic_tests.create_synthetic_test_step_result(
            step['id'], test_time, round(step['responseTimeMillis']))

        if 'error' in step:
            test_step_results._raw_element["error"] = step['error']
            scenario_status = False

        test_step_results_list.append(
            test_step_results)

    dt_client.third_part_synthetic_tests.report_simple_thirdparty_synthetic_test(
        engine_name=engine,
        timestamp=datetime.timestamp(datetime.now()),
        location_id=socket.gethostname(),
        location_name=socket.gethostname(),
        test_id=the_test_id,
        test_title=the_test_title,
        detailed_steps=test_step_list,
        detailed_step_results=test_step_results_list,
        schedule_interval=frequency,
        success=scenario_status,
        response_time=0,
        edit_link=url,
        icon_url="https://raw.githubusercontent.com/RaiMan/SikuliX1/master/IDE/src/main/resources/icons/sikulix-icon.png",
    )

    # process errors
    if is_error:
        scenario_status = False

        dt_client.third_part_synthetic_tests.report_simple_thirdparty_synthetic_test_event(
            test_id=the_test_id,
            name=engine+" reported error for "+the_test_title,
            location_id=socket.gethostname(),
            timestamp=datetime.now(),
            state="open",
            event_type=SYNTHETIC_EVENT_TYPE_OUTAGE,
            reason=log,
            engine_name=engine,
        )

    else:
        for step in details:
            if 'error' in step:
                # send event
                dt_client.third_part_synthetic_tests.report_simple_thirdparty_synthetic_test_event(
                    test_id=the_test_id,
                    name=engine+" reported error for "+the_test_title,
                    location_id=socket.gethostname(),
                    timestamp=step['startTimestamp'],
                    state="open",
                    event_type=SYNTHETIC_EVENT_TYPE_OUTAGE,
                    reason=step['error']['message'],
                    engine_name=engine,
                )
                # stop iterating after having found and reported first error
                break

    if(scenario_status == True):
        # send event to close last open problem (if any)
        dt_client.third_part_synthetic_tests.report_simple_thirdparty_synthetic_test_event(
            test_id=the_test_id,
            name="",
            location_id="",
            timestamp=datetime.now(),
            state="resolved",
            event_type=SYNTHETIC_EVENT_TYPE_OUTAGE,
            reason="",
            engine_name=engine,
        )


def test_api_validity(dt_client: Dynatrace):

    return dt_client.third_part_synthetic_tests.report_simple_thirdparty_synthetic_test_event(
        test_id="x",
        name="x",
        location_id="x",
        timestamp=datetime.now(),
        state="resolved",
        event_type=SYNTHETIC_EVENT_TYPE_OUTAGE,
        reason="",
        engine_name="x",
    )


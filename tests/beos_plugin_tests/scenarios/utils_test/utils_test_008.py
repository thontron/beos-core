#!/usr/bin/python3

import os
import sys
import time
import datetime

currentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from beos_test_utils.beos_utils_pack import (
    init,
    ActionResult,
    ResourceResult,
    VotersResult,
)

if __name__ == "__main__":
    try:
        node, summary, args, log = init(__file__)

        summary.action_status(ActionResult(False, ""), ActionResult(True, ""))

    except Exception as _ex:
        log.exception(
            "Exception `{0}` occures while executing `{1}` tests.".format(
                str(_ex), __file__
            )
        )
    finally:
        summary_status = summary.summarize()
        node.stop_node()
        log.info(
            "Summary of Error Action: `{0}`, Error user block: `{1}`, Error equal: `{2}` and summary status: `{3}`".format(
                summary.error_action,
                summary.error_user_block,
                summary.error_equal,
                summary_status,
            )
        )
        assert summary.error_action == 1
        assert summary.error_user_block == 0
        assert summary.error_equal == 0
        assert summary_status == 1
        exit(summary_status != 1)
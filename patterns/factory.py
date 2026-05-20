import re
from textual.widgets import (
    Log,
    TabPane
)


class TopicTabFactory:

    @staticmethod
    def create(topic):

        safe_id = re.sub(
            r"[^a-zA-Z0-9]",
            "-",
            topic
        )

        pane = TabPane(
            f"📁 {topic}",
            id=f"tab-{safe_id}"
        )

        log = Log(
            id=f"log-{safe_id}",
            highlight=True
        )

        return pane, log

from patterns.factory import (
    TopicTabFactory
)


class DynamicTabManager:

    def __init__(self):
        self.topics = set()

    async def create_topic_tab(
        self,
        tabs,
        topic
    ):
        if topic in self.topics:
            return

        self.topics.add(topic)

        pane, log = (
            TopicTabFactory.create(
                topic
            )
        )

        await tabs.add_pane(
            pane
        )

        await pane.mount(
            log
        )

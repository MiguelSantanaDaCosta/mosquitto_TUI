from textual.widgets import Log


def create_log_widget(
    widget_id
):
    widget = Log(
        id=widget_id,
        highlight=True
    )

    widget.styles.height = "1fr"

    return widget

class EventTypeError(TypeError):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

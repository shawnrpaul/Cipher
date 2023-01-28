class EventTypeError(TypeError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

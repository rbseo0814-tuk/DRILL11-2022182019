from pico2d import *
from transitions import Machine


class Idle:
    @staticmethod
    def enter(boy, e):
        boy.dir = 0

    @staticmethod
    def exit(boy, e):
        pass

    @staticmethod
    def do(boy):
        boy.frame = (boy.frame + 1) % 8

    @staticmethod
    def draw(boy):
        row = 300 if boy.face_dir == 1 else 200
        boy.image.clip_draw(boy.frame * 100, row, 100, 100, boy.x, boy.y)


STATES = {'IDLE': Idle}

KEY_EVENTS = {}


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.dir = 0
        self.image = load_image('animation_sheet.png')
        self.machine = Machine(
            model=self,
            states=list(STATES),
            initial='IDLE',
            auto_transitions=False,
            ignore_invalid_triggers=True,   # 현재 상태에 없는 이벤트는 무시
            send_event=True,
            before_state_change='exit_state',
            after_state_change='enter_state',
        )

        # 초기 상태는 transition 없이 정해지므로 enter를 직접 호출
        Idle.enter(self, None)

    def exit_state(self, event_data):
        STATES[event_data.transition.source].exit(self, event_data.event.name)

    def enter_state(self, event_data):
        STATES[self.state].enter(self, event_data.event.name)

    def handle_event(self, event):
        trigger = KEY_EVENTS.get((event.type, getattr(event, 'key', None)))
        if trigger:
            self.trigger(trigger)

    def update(self):
        STATES[self.state].do(self)

    def draw(self):
        STATES[self.state].draw(self)

from pico2d import *
from transitions import Machine

SLEEP_TIMEOUT = 5.0         # Idle에서 Sleep까지 (초)


class Idle:
    @staticmethod
    def enter(boy, e):
        boy.dir = 0
        boy.wait_start_time = get_time()   # Idle로 돌아올 때마다 타이머 재시작

    @staticmethod
    def exit(boy, e):
        pass

    @staticmethod
    def do(boy):
        boy.frame = (boy.frame + 1) % 8
        if get_time() - boy.wait_start_time >= SLEEP_TIMEOUT:
            boy.time_out()

    @staticmethod
    def draw(boy):
        row = 300 if boy.face_dir == 1 else 200
        boy.image.clip_draw(boy.frame * 100, row, 100, 100, boy.x, boy.y)


class Sleep:
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
        # 바라보던 방향으로 90도 눕혀서 그린다
        if boy.face_dir == 1:
            boy.image.clip_composite_draw(boy.frame * 100, 300, 100, 100,
                                          3.141592 / 2, '', boy.x - 25, boy.y - 25, 100, 100)
        else:
            boy.image.clip_composite_draw(boy.frame * 100, 200, 100, 100,
                                          -3.141592 / 2, '', boy.x + 25, boy.y - 25, 100, 100)


STATES = {'IDLE': Idle, 'SLEEP': Sleep}

KEY_EVENTS = {
}


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

        self.machine.add_transition('time_out', 'IDLE', 'SLEEP')


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

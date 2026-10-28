from pico2d import *
from transitions import Machine

RUN_SPEED = 5
AUTO_RUN_SPEED = 15         # 일반 Run의 3배
AUTO_RUN_SCALE = 2          # 100x100 -> 200x200
SLEEP_TIMEOUT = 5.0         # Idle에서 Sleep까지 (초)
AUTO_RUN_DURATION = 5.0     # AutoRun 유지 시간 (초)


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


class Run:
    @staticmethod
    def enter(boy, e):
        # 왼쪽/오른쪽을 따로 두지 않고, 들어오게 한 키 이벤트로 방향을 정한다
        # (left_up으로 들어왔다면 아직 눌려 있는 오른쪽으로 계속 달린다)
        boy.dir = boy.face_dir = 1 if e in ('right_down', 'left_up') else -1

    @staticmethod
    def exit(boy, e):
        pass

    @staticmethod
    def do(boy):
        boy.frame = (boy.frame + 1) % 8
        boy.x = clamp(25, boy.x + boy.dir * RUN_SPEED, 800 - 25)

    @staticmethod
    def draw(boy):
        row = 100 if boy.dir == 1 else 0
        boy.image.clip_draw(boy.frame * 100, row, 100, 100, boy.x, boy.y)


class AutoRun:
    HALF_W = 25 * AUTO_RUN_SCALE

    @staticmethod
    def enter(boy, e):
        boy.dir = boy.face_dir                 # 바라보던 방향으로 출발
        boy.auto_run_start_time = get_time()

    @staticmethod
    def exit(boy, e):
        pass

    @staticmethod
    def do(boy):
        boy.frame = (boy.frame + 1) % 8
        boy.x += boy.dir * AUTO_RUN_SPEED

        # 화면 좌우 끝에서 자동 방향 전환
        if boy.x >= 800 - AutoRun.HALF_W:
            boy.x, boy.dir = 800 - AutoRun.HALF_W, -1
        elif boy.x <= AutoRun.HALF_W:
            boy.x, boy.dir = AutoRun.HALF_W, 1
        boy.face_dir = boy.dir

        if get_time() - boy.auto_run_start_time >= AUTO_RUN_DURATION:
            boy.time_out()

    @staticmethod
    def draw(boy):
        row = 100 if boy.dir == 1 else 0
        size = 100 * AUTO_RUN_SCALE
        # 확대해도 발이 땅에 붙어 있도록 중심을 올린다
        boy.image.clip_draw(boy.frame * 100, row, 100, 100,
                            boy.x, boy.y + (size - 100) // 2, size, size)


STATES = {'IDLE': Idle, 'SLEEP': Sleep, 'RUN': Run, 'AUTO_RUN': AutoRun}

KEY_EVENTS = {
    (SDL_KEYDOWN, SDLK_RIGHT): 'right_down',
    (SDL_KEYDOWN, SDLK_LEFT): 'left_down',
    (SDL_KEYUP, SDLK_RIGHT): 'right_up',
    (SDL_KEYUP, SDLK_LEFT): 'left_up',
    (SDL_KEYDOWN, SDLK_SPACE): 'space_down',
    (SDL_KEYDOWN, SDLK_a): 'a_down',
}


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.dir = 0
        self.held = {SDLK_LEFT: False, SDLK_RIGHT: False}
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
        self.machine.add_transition('right_down', 'IDLE', 'RUN')
        self.machine.add_transition('left_down', 'IDLE', 'RUN')
        self.machine.add_transition('a_down', 'IDLE', 'AUTO_RUN')

        self.machine.add_transition('space_down', 'SLEEP', 'IDLE')
        self.machine.add_transition('right_down', 'SLEEP', 'RUN')
        self.machine.add_transition('left_down', 'SLEEP', 'RUN')

        self.machine.add_transition('right_down', 'RUN', 'RUN')
        self.machine.add_transition('left_down', 'RUN', 'RUN')
        # 달리던 방향 키를 뗐을 때 반대쪽 키가 눌려 있으면 그쪽으로 계속 달린다 (먼저 등록된 전이가 우선)
        self.machine.add_transition('right_up', 'RUN', 'RUN', conditions=['moving_right', 'left_held'])
        self.machine.add_transition('left_up', 'RUN', 'RUN', conditions=['moving_left', 'right_held'])
        self.machine.add_transition('right_up', 'RUN', 'IDLE', conditions='moving_right')
        self.machine.add_transition('left_up', 'RUN', 'IDLE', conditions='moving_left')

        self.machine.add_transition('time_out', 'AUTO_RUN', 'IDLE')
        self.machine.add_transition('right_down', 'AUTO_RUN', 'RUN')
        self.machine.add_transition('left_down', 'AUTO_RUN', 'RUN')

        # 초기 상태는 transition 없이 정해지므로 enter를 직접 호출
        Idle.enter(self, None)

    def exit_state(self, event_data):
        STATES[event_data.transition.source].exit(self, event_data.event.name)

    def enter_state(self, event_data):
        STATES[self.state].enter(self, event_data.event.name)

    def moving_right(self, event_data):
        return self.dir == 1

    def moving_left(self, event_data):
        return self.dir == -1

    def left_held(self, event_data):
        return self.held[SDLK_LEFT]

    def right_held(self, event_data):
        return self.held[SDLK_RIGHT]

    def handle_event(self, event):
        key = getattr(event, 'key', None)
        if event.type in (SDL_KEYDOWN, SDL_KEYUP) and key in self.held:
            self.held[key] = event.type == SDL_KEYDOWN

        trigger = KEY_EVENTS.get((event.type, key))
        if trigger:
            self.trigger(trigger)

    def update(self):
        STATES[self.state].do(self)

    def draw(self):
        STATES[self.state].draw(self)

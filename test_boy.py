# 상태 전이 자동 테스트: python test_boy.py
# 키 이벤트를 흉내 내고 get_time을 바꿔치기해서 5초 타이머를 바로 확인한다.
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

from pico2d import *

open_canvas()
import boy as B

now = [0.0]
B.get_time = lambda: now[0]


class Ev:
    def __init__(self, t, k):
        self.type, self.key = t, k


def key(t, k, b):
    b.handle_event(Ev(t, k))


def step(b, n=1):
    for _ in range(n):
        b.update()
        clear_canvas()
        b.draw()
        update_canvas()


fails = []


def check(cond, msg):
    print(('PASS ' if cond else 'FAIL ') + msg)
    if not cond:
        fails.append(msg)


b = B.Boy()
check(b.state == 'IDLE', 'initial IDLE')

# AutoRun 진입, 속도, 화면 끝 방향 전환, 5초 후 Idle
key(SDL_KEYDOWN, SDLK_a, b); check(b.state == 'AUTO_RUN', 'a -> AUTO_RUN')
x0 = b.x; step(b); check(b.x - x0 == B.AUTO_RUN_SPEED, 'auto run speed')
key(SDL_KEYDOWN, SDLK_a, b); check(b.auto_run_start_time == 0.0, 'a again ignored, timer not reset')
step(b, 40); check(b.dir == -1 and b.x <= 800 - B.AutoRun.HALF_W, 'bounced at right edge')
step(b, 60); check(b.dir == 1 and b.x >= B.AutoRun.HALF_W, 'bounced at left edge')
now[0] = 4.9; step(b); check(b.state == 'AUTO_RUN', 'still AUTO_RUN at 4.9s')
now[0] = 5.0; step(b); check(b.state == 'IDLE', 'AUTO_RUN -> IDLE at 5s')
check(b.wait_start_time == 5.0, 'idle timer restarted')

# AutoRun 중 방향키 -> Run
key(SDL_KEYDOWN, SDLK_a, b)
key(SDL_KEYUP, SDLK_RIGHT, b); check(b.state == 'AUTO_RUN', 'key up ignored in AUTO_RUN')
key(SDL_KEYDOWN, SDLK_LEFT, b); check(b.state == 'RUN' and b.dir == -1, 'AUTO_RUN + left -> RUN left')
x0 = b.x; step(b); check(x0 - b.x == B.RUN_SPEED, 'normal run speed restored')
key(SDL_KEYUP, SDLK_LEFT, b); check(b.state == 'IDLE', 'RUN key up -> IDLE')
key(SDL_KEYDOWN, SDLK_a, b); key(SDL_KEYDOWN, SDLK_RIGHT, b)
check(b.state == 'RUN' and b.dir == 1, 'AUTO_RUN + right -> RUN right')
key(SDL_KEYUP, SDLK_RIGHT, b)

# 양쪽 키를 함께 누르고 하나만 뗐을 때
key(SDL_KEYDOWN, SDLK_RIGHT, b); key(SDL_KEYDOWN, SDLK_LEFT, b)
check(b.state == 'RUN' and b.dir == -1, 'right held + left down -> run left')
key(SDL_KEYUP, SDLK_LEFT, b); check(b.state == 'RUN' and b.dir == 1, 'left up while right held -> run right')
key(SDL_KEYUP, SDLK_RIGHT, b); check(b.state == 'IDLE', 'all keys up -> IDLE')

# Sleep
now[0] = 20.0; step(b); check(b.state == 'SLEEP', 'IDLE 5s -> SLEEP')
key(SDL_KEYDOWN, SDLK_a, b); check(b.state == 'SLEEP', 'a ignored in SLEEP')
key(SDL_KEYDOWN, SDLK_SPACE, b); check(b.state == 'IDLE', 'SLEEP space -> IDLE')
key(SDL_KEYDOWN, SDLK_RIGHT, b); key(SDL_KEYDOWN, SDLK_a, b); check(b.state == 'RUN', 'a ignored in RUN')

close_canvas()
print(f'{len(fails)} failed' if fails else 'ALL PASS')
sys.exit(1 if fails else 0)

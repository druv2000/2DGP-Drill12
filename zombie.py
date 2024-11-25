from pico2d import *

import random
import math

import game_framework
from behavior_tree import BehaviorTree, Action, Sequence, Condition, Selector
import play_mode


# zombie Run Speed
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 10.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# zombie Action Speed
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 10.0

animation_names = ['Walk', 'Idle']


class Zombie:
    images = None

    def load_images(self):
        if Zombie.images == None:
            Zombie.images = {}
            for name in animation_names:
                Zombie.images[name] = [load_image("./zombie/" + name + " (%d)" % i + ".png") for i in range(1, 11)]
            Zombie.font = load_font('ENCR10B.TTF', 40)
            Zombie.marker_image = load_image('hand_arrow.png')


    def __init__(self, x=None, y=None):
        self.x = x if x else random.randint(100, 1180)
        self.y = y if y else random.randint(100, 924)
        self.tx, self.ty = 0, 0
        self.load_images()
        self.dir = 0.0      # radian 값으로 방향을 표시
        self.speed = 0.0
        self.frame = random.randint(0, 9)
        self.state = 'Idle'
        self.ball_count = 0
        self.build_behavior_tree()


    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50


    def update(self):
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
        self.bt.run()

    def draw(self):
        if math.cos(self.dir) < 0:
            Zombie.images[self.state][int(self.frame)].composite_draw(0, 'h', self.x, self.y, 100, 100)
        else:
            Zombie.images[self.state][int(self.frame)].draw(self.x, self.y, 100, 100)
        self.font.draw(self.x - 10, self.y + 60, f'{self.ball_count}', (0, 0, 255))
        draw_rectangle(*self.get_bb())
        Zombie.marker_image.draw(self.tx, self.ty)

    def handle_event(self, event):
        pass

    def handle_collision(self, group, other):
        if group == 'zombie:ball':
            self.ball_count += 1

    def distance_less_than(self, x1, y1, x2, y2, r):
        distance = (x1-x2)**2 + (y1-y2)**2
        return distance <= (PIXEL_PER_METER * r) ** 2
        pass

    def move_slightly_to(self, tx, ty):
        self.dir = math.atan2(ty - self.y, tx - self.x)
        distance = RUN_SPEED_PPS * game_framework.frame_time
        self.x += distance * math.cos(self.dir)
        self.y += distance * math.sin(self.dir)
        pass

    def run_slightly_from(self, tx, ty):
        self.dir = math.atan2(self.y - play_mode.boy.y, self.x - play_mode.boy.x)
        distance = RUN_SPEED_PPS * game_framework.frame_time
        self.x += distance * math.cos(self.dir)
        self.y += distance * math.sin(self.dir)
        pass

    def move_to(self, r=0.5):
        self.state = 'Walk'
        self.move_slightly_to(self.tx, self.ty)
        if self.distance_less_than(self.x, self.y, self.tx, self.ty, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING
        pass

    def set_random_location(self):
        self.tx, self.ty = random.randint(100, 1200 - 100), random.randint(100, 1024 - 100)
        return BehaviorTree.SUCCESS

    def is_boy_nearby(self, distance):
        if self.distance_less_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, distance):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL
        pass

    def move_to_boy(self, r=0.5):
        self.state = 'Walk'
        self.move_slightly_to(play_mode.boy.x, play_mode.boy.y)
        if self.distance_less_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING

    def run_from_boy(self):
        self.state = 'Walk'
        self.run_slightly_from(play_mode.boy.x, play_mode.boy.y)
        return BehaviorTree.RUNNING

    def is_boy_having_more_balls(self):
        if self.ball_count <= play_mode.boy.ball_count:
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL

    def is_boy_having_less_balls(self):
        if self.ball_count > play_mode.boy.ball_count:
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL

    def build_behavior_tree(self):
        a1 = Action('Move to boy', self.move_to_boy)
        a2 = Action('Run from boy', self.run_from_boy)
        a3 = Action('Set random location', self.set_random_location)
        a4 = Action('Move to', self.move_to)
        c1 = Condition('Is_boy_having_more_balls', self.is_boy_having_more_balls)
        c2 = Condition('Is_boy_having_less_balls', self.is_boy_having_less_balls)
        c3 = Condition('Is_boy_nearby', self.is_boy_nearby, 7)

        root = chase = Sequence('Chase', c2, a1)
        root = flee = Sequence('Flee', c1, a2)
        root = chase_or_flee = Selector('Chase or flee', chase, flee)
        root = decision_or_wander = Sequence('Decision or wander', c3, chase_or_flee)
        root = wander = Sequence('Wander', a3, a4)
        root = chase_or_flee_or_wander = Selector('Chase or flee or wander', decision_or_wander, wander)

        self.bt = BehaviorTree(root)
        pass

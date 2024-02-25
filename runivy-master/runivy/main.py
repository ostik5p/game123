import random

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.audio import SoundLoader
from kivy.core.image import Image
from kivy.properties import ObjectProperty, ListProperty, NumericProperty, BooleanProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout

Config.set('graphics', 'resizable', 0)

GRAVITY = -0.25
FREQUENCY = 1.0 / 120.0

LEVEL_SPEEDS = {
    'easy': 2,
    'medium': 4,
    'hard': 6
}


class RunivyObject(Widget):
    speed = NumericProperty(0)
    obstacle = False

    def __init__(self, **kwargs):
        super(RunivyObject, self).__init__(**kwargs)
        self.speed = kwargs.get('speed', 2)

    def move(self):
        self.x -= self.speed

    def is_out(self):
        return self.x + self.width <= 0


class RunivyCloud(RunivyObject):
    pass


class RunivySkyscraper(RunivyObject):
    obstacle = True


class RunivyNuclearSilo(RunivyObject):
    obstacle = True


class RunivyPhoneTower(RunivyObject):
    obstacle = True


class RunivyPlayer(Widget):
    jumping = BooleanProperty(False)
    velocity = NumericProperty(0)
    source = StringProperty("atlas://data/runivy/dino-run-1")
    roar = ObjectProperty(None, allownone=True)
    sounds = ["data/roar1.wav", "data/roar2.mp3", "data/roar3.wav", ]

    frame_per_picture = 9
    current_animation_frame = 0
    animation = [
        "atlas://data/runivy/dino-run-1",
        "atlas://data/runivy/dino-run-2",
        "atlas://data/runivy/dino-run-3",
        "atlas://data/runivy/dino-run-2",
    ]

    def __init__(self, **kwargs):
        super(RunivyPlayer, self).__init__(**kwargs)
        self.sounds = [SoundLoader.load(sound) for sound in self.sounds]
        self.jump_button = Button(text='Jump', size_hint=(None, None), size=(100, 50))
        self.jump_button.bind(on_press=self.on_jump_button_press)
        self.jump_button.bind(on_release=self.on_jump_button_release)
        self.add_widget(self.jump_button)

    def on_jump_button_press(self, instance):
        self.jump()

    def on_jump_button_release(self, instance):
        self.stop_jump()

    def stop_jump(self):
        if self.velocity > 4.0:
            self.velocity = 4.0

    def jump(self):
        if not self.jumping:
            self.velocity = 10.0
            self.jumping = True
            if self.roar is None or self.roar.state is 'stop':
                self.roar = random.choice(self.sounds)
                self.roar.seek(0)
                self.roar.play()

    def stop(self):
        self.jumping = False
        self.y = 104
        self.velocity = 0

    def _update_source(self):
        if self.jumping:
            self.source = "atlas://data/runivy/dino-jump"
        else:
            current_picture = int(self.current_animation_frame / self.frame_per_picture)
            self.source = self.animation[current_picture]
            self.current_animation_frame = (self.current_animation_frame + 1) % (self.frame_per_picture * len(self.animation))

    def move(self):
        self._update_source()
        self.y += self.velocity
        self.velocity += GRAVITY
        if self.y < 104:
            self.stop()


class RunivyGame(Widget):
    player = ObjectProperty(None)
    score = ObjectProperty(None)
    objects = ListProperty([])
    ground = ObjectProperty(None)
    scroll = NumericProperty(0.0)
    music = ObjectProperty(None)
    button = ObjectProperty(None)
    level = StringProperty('easy')
    level_popup = None

    running = False
    last_tick = None
    next_cloud = 0
    next_obstacle = 0
    obstacles = [RunivySkyscraper, RunivyNuclearSilo, RunivyPhoneTower]

    def __init__(self, **kwargs):
        super(RunivyGame, self).__init__(**kwargs)
        self.ground = Image('data/ground.png').texture
        self.ground.wrap = "repeat"
        self.music = SoundLoader.load("data/music.mp3")
        self.music.loop = True
        self.music.play()
        self.level_popup = LevelPopup(callback=self.set_level)
        self.level_popup.open()

    def reset(self):
        self.player.stop()
        for obj in self.objects:
            self.remove_widget(obj)
        self.objects.clear()
        self.score.text = "0"
        self.last_tick = None
        self.running = True
        self.button.x = -5000

    def set_level(self, level):
        self.level = level
        self.player.velocity = LEVEL_SPEEDS[level]

    def should_spawn_obstacle(self):
        return self.next_obstacle <= 0

    def spawn_obstacle(self):
        obstacle = random.choice(self.obstacles)(x=self.width, y=104)
        self.objects.append(obstacle)
        self.add_widget(obstacle)
        self.next_obstacle = random.randint(120, 360)

    def spawn_cloud(self):
        top = self.height - random.randint(100, 400)
        speed = random.randint(1, 4)
        cloud = RunivyCloud(x=self.width, y=top, speed=speed)
        self.objects.append(cloud)
        self.add_widget(cloud, canvas='before')
        self.next_cloud = random.randint(120, 360)

    def move_objects(self):
        for obj in self.objects[:]:
            obj.move()
            if obj.is_out():
                self.remove_widget(obj)
                self.objects.remove(obj)
                if obj.obstacle:
                    self.score.text = str(int(self.score.text) + 1)
        self.scroll = (self.scroll * self.width + 2) % self.width / self.width

    def check_obstacles(self):
        for obj in self.objects:
            if obj.obstacle and obj.collide_widget(self.player):
                self.running = False
                self.button.center_x = self.center_x

    def tick(self):
        self.player.move()

        self.move_objects()
        if self.should_spawn_obstacle():
            self.spawn_obstacle()
        self.check_obstacles()
        if self.next_cloud <= 0:
            self.spawn_cloud()
        else:
            self.next_cloud -= 1
        self.next_obstacle -= 1

    def update(self, dt):
        if not self.running:
            return

        if self.last_tick is None:
            self.last_tick = Clock.get_boottime()

        current_tick = Clock.get_boottime() - FREQUENCY
        while current_tick > self.last_tick:
            self.last_tick += FREQUENCY
            self.tick()


class RunivyApp(App):
    def build(self):
        game = RunivyGame()
        Clock.schedule_interval(game.update, FREQUENCY)
        return game


class LevelPopup(Popup):
    def __init__(self, callback, **kwargs):
        self.callback_function = callback
        super(LevelPopup, self).__init__(**kwargs)
        self.title = 'Select Level'

        content_layout = BoxLayout(orientation='vertical')

        easy_button = Button(text='Easy')
        easy_button.bind(on_press=self.set_easy_level)
        content_layout.add_widget(easy_button)

        medium_button = Button(text='Medium')
        medium_button.bind(on_press=self.set_medium_level)
        content_layout.add_widget(medium_button)

        hard_button = Button(text='Hard')
        hard_button.bind(on_press=self.set_hard_level)
        content_layout.add_widget(hard_button)

        self.content = content_layout

    def set_easy_level(self, instance):
        self.dismiss()
        self.callback_function('easy')

    def set_medium_level(self, instance):
        self.dismiss()
        self.callback_function('medium')

    def set_hard_level(self, instance):
        self.dismiss()
        self.callback_function('hard')


if __name__ == '__main__':
    RunivyApp().run()

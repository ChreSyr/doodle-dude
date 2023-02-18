
import math
import random
import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))  # executable from console
import sys
sys.path.insert(0, 'C:\\Users\\symrb\\Documents\\python\\baopig')
import baopig as bp


class MainScene(bp.Scene):

    def __init__(self, app):

        bp.Scene.__init__(self, app, background_color="orange4")

        self.start_btn = bp.Button(self, text="START", sticky="midbottom", pos=(0, -200), command=self.start_game,
                                   size=(250, 100), text_style={"font_height":50})


        self.gravity = bp.Vector2(0, .3)
        self.platforms = [
            Platform(self, (0, 700, 600, 100)),
            ClassicPlatform(self, (20, 500)),
            ClassicPlatform(self, (500, 500)),
            ClassicPlatform(self, (120, 300)),
            ClassicPlatform(self, (400, 200)),
            ClassicPlatform(self, (200, 50)),
        ]
        self.arma = Arma(self, midbottom=(300, 400))

        self.space_timer = bp.RepeatingTimer(.01, self.step)

        self.score = 0
        self.score_label = bp.DynamicText(self, get_text=lambda: f"Score : {self.score}", sticky="topright",
                                          font_height=18, visible=False)

        self.fail_zone = bp.Zone(self, size=(300, 300), sticky="center", background_color=(0, 0, 0, 64), visible=False,
                                 layer_level=2)
        self.score_text = bp.Text(self.fail_zone, "", align_mode="center", sticky="midtop",
                                  pos=(0, 25), font_height=30, padding=20)
        bp.Button(self.fail_zone, text="RESTART", sticky="midbottom", pos=(0, -25), command=self.start_game,
                  size=(250, 100), text_style={"font_height":50})

    def start_game(self):

        self.arma.hitbox.midbottom = (300, 400)
        self.arma.widget.set_pos(topleft=self.arma.hitbox.topleft)
        self.arma.second_widget.hide()
        for pf in self.platforms:
            pf.hitbox.top -= self.score
            pf.widget.set_pos(topleft=pf.hitbox.topleft)

        self.score = 0
        self.fail_zone.hide()
        self.start_btn.hide()
        self.space_timer.start()
        self.score_label.show()

    def step(self):
        
        self.arma.velocity.x = self.arma.direction * self.arma.speed

        # PRE STEP
        self.arma.acceleration += self.gravity

        # STEP
        # On applique l'acceleration et le frottement de l'air sur la vitesse
        self.arma.velocity += self.arma.acceleration

        # On applique la vitesse sur la position
        self.arma.move(self.arma.velocity)
        self.arma.acceleration *= 0

        for pf in self.platforms:
            react_pf = self.arma.get_react_brick(pf.hitbox)
            if react_pf is True:
                self.arma.velocity.y = 0
                self.arma.hitbox.bottom = pf.hitbox.top
                self.arma.remaining_jumps = self.arma.max_jumps

        max_top = 300
        if self.arma.hitbox.top < max_top:
            d = max_top - self.arma.hitbox.top
            self.arma.hitbox.top = max_top
            for pf in self.platforms:
                pf.hitbox.top += d
                pf.widget.set_pos(topleft=pf.hitbox.topleft)
            self.score += d

            if self.platforms[-1].hitbox.top > 150:
                self.platforms.append(ClassicPlatform(self, (random.randint(0, 500), -20)))

        self.arma.widget.set_pos(midbottom=self.arma.hitbox.midbottom)
        if self.arma.widget.rect.left < 0:
            if self.arma.widget.rect.right < 0:
                self.arma.hitbox.left += self.rect.width
                self.arma.second_widget.hide()
            else:
                self.arma.second_widget.set_pos(midbottom=self.arma.hitbox.midbottom)
                self.arma.second_widget.move(dx=self.rect.width)
                self.arma.second_widget.update_orientation()
                self.arma.second_widget.show()
        elif self.arma.widget.rect.right > self.rect.width:
            if self.arma.widget.rect.left > self.rect.width:
                self.arma.hitbox.left -= self.rect.width
                self.arma.second_widget.hide()
            else:
                self.arma.second_widget.set_pos(midbottom=self.arma.hitbox.midbottom)
                self.arma.second_widget.move(dx=-self.rect.width)
                self.arma.second_widget.update_orientation()
                self.arma.second_widget.show()
        else:
            self.arma.second_widget.hide()

        if self.arma.hitbox.top > self.rect.height:
            self.space_timer.cancel()
            self.score_text.set_text(f"Score : {self.score}")
            self.fail_zone.show()

    def handle_event(self, event):

        if event.type == bp.KEYDOWN or event.type == bp.KEYUP:
            self.arma.update_orientation()

            if event.type == bp.KEYDOWN:
                if event.key == bp.K_z:
                    self.arma.jump()


class Body:

    def __init__(self, hitbox):

        self.hitbox = hitbox
        self.velocity = bp.Vector2(0, 0)
        self.acceleration = bp.Vector2(0, 0)

    def move(self, d):

        self.hitbox.move_ip(*d)


class Arma(Body):

    def __init__(self, sc, midbottom):

        self.widget = ArmaWidget(self, sc, midbottom)
        self.second_widget = ArmaWidget(self, sc, midbottom)
        self.second_widget.hide()

        Body.__init__(self, hitbox=bp.Rect(self.widget.rect))

        self.direction = 0
        self.space = sc

        self.pos = (300, 0)
        self.speed = 5
        self.jump_height = 250  # unit : pixels
        self.max_jumps = 2
        self.remaining_jumps = self.max_jumps

    def jump(self):

        if self.remaining_jumps > 0:
            jump_strengh = math.sqrt(2.0 * self.jump_height * self.space.gravity.y)
            self.velocity.y = - jump_strengh
            self.acceleration.y = 0
            self.remaining_jumps -= 1

    def get_react_brick(self, brick_rect):

        if self.hitbox.bottom >= self.space.rect.height:
            return False

        if not brick_rect.colliderect(self.hitbox):
            if self.second_widget.is_hidden:
                return False

            hitbox_2 = bp.Rect(self.hitbox)
            if self.second_widget.rect.centerx < 300:
                hitbox_2.left -= self.space.rect.width
            else:
                hitbox_2.left += self.space.rect.width
            if not brick_rect.colliderect(hitbox_2):
                return False

        if self.velocity.y <= 0:
            return False

        if self.hitbox.bottom - self.velocity.y > brick_rect.top:
            return False

        return True

    def update_orientation(self):

        self.direction = bp.keyboard.is_pressed(bp.K_d) - bp.keyboard.is_pressed(bp.K_q)
        self.widget.update_orientation()


class ArmaWidget(bp.Zone):

    def __init__(self, controller, sc, midbottom):

        bp.Zone.__init__(self, sc, midbottom=midbottom, size=(64, 64), layer_level=2)

        self.controller = controller
        self.body = bp.Circle(self, center=self.auto_rect.center, radius=32, color="green3")
        self.left_eye = bp.Circle(self, center=(17, 30), radius=9, color=(200, 200, 200))
        self.right_eye = bp.Circle(self, center=(41, 30), radius=9, color=(200, 200, 200))
        self.left_pupil = bp.Circle(self, center=(15, 30), radius=3, color="black")
        self.right_pupil = bp.Circle(self, center=(39, 30), radius=3, color="black")

    def update_orientation(self):

        if self.controller.direction == -1:
            self.left_eye.set_pos(centerx=17)
            self.right_eye.set_pos(centerx=41)
            self.left_pupil.set_pos(centerx=15)
            self.right_pupil.set_pos(centerx=39)
        elif self.controller.direction == 1:
            self.left_eye.set_pos(centerx=32 + 15)
            self.right_eye.set_pos(centerx=32 - 9)
            self.left_pupil.set_pos(centerx=32 + 17)
            self.right_pupil.set_pos(centerx=32 - 7)


class Platform(Body):

    def __init__(self, sc, rect):

        self.widget = PlatformWidget(sc, rect)
        Body.__init__(self, hitbox=bp.Rect(self.widget.rect))


class ClassicPlatform(Platform):

    def __init__(self, sc, pos):

        Platform.__init__(self, sc, pos + (100, 20))


class PlatformWidget(bp.Rectangle):

    def __init__(self, sc, rect):

        bp.Rectangle.__init__(self, sc, pos=rect[:2], size=rect[2:], color=(114, 50, 0, 255))


app = bp.Application(size=(600, 800))
app.set_style_for(bp.Text, font_file="monospace")
app.set_style_for(bp.Button, background_color="green4")

scene = MainScene(app)



app.launch()

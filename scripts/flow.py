from manim import *


class FlowChart(Scene):
    def construct(self):
        # set background to gray
        user = ImageMobject("assets/bohemian.png").scale(0.7).to_edge(LEFT)
        recorder = ImageMobject(
            "assets/mic.png").scale(0.4).to_edge(UP)

        db = ImageMobject(
            "assets/database.png").scale(0.5).to_edge(RIGHT)
        translate = ImageMobject(
            "assets/translate-2.png").scale(0.3).to_edge(DOWN)

        line1 = ArcBetweenPoints(
            user.get_right(), recorder.get_left(), angle=-PI/4,
            arc_center=(recorder.get_left() + user.get_right())/2)
        line1 = Line(user.get_right(), recorder.get_left())
        line2 = Line(recorder.get_right(), db.get_left())
        line3 = Line(db.get_left(), translate.get_right())
        self.play(FadeIn(user),
                  FadeIn(recorder),
                  FadeIn(db),
                  FadeIn(translate),
                  Create(line1),
                  Create(line2),
                  Create(line3),
                  run_time=2)

        updater = VMobject()
        self.add(updater)
        audio = ImageMobject(
            "assets/audio-2.png").scale(0.1)
        text1 = Text("1. record audio with PyAudio", font="Georgia",
                     font_size=31, weight=BOLD,
                     color=BLUE)
        text1.move_to(user.get_right() + RIGHT*4)
        # text1.rotate(line1.get_angle()*0.8).move_to(line1.get_center() + UP*1)
        updater.add_updater(lambda x: x.become(
            Line(user.get_right(), audio.get_center(),
                 stroke_width=5).set_color(BLUE)))
        self.play(MoveAlongPath(audio, line1),
                  Write(text1),
                  rate_func=linear,
                  run_time=3)
        line1.set_color(BLUE)
        updater.clear_updaters()
        self.play(
            audio.animate.move_to(recorder.get_right()),
            run_time=1
        )

        text2 = Text("2. sync audio to database", font="Georgia",
                     font_size=31, weight=BOLD,
                     color=YELLOW)
        text2.rotate(line2.get_angle()).move_to(line2.get_center() + UP*1)
        updater.add_updater(lambda x: x.become(
            Line(recorder.get_right(), audio.get_center(),
                 stroke_width=5).set_color(YELLOW)))
        self.play(MoveAlongPath(audio, line2),
                  Write(text2),
                  rate_func=linear,
                  run_time=3)
        line2.set_color(YELLOW)
        self.wait(1)

        text3 = Text("3. transcribe with whisper", font="Georgia",
                     font_size=31, weight=BOLD,
                     color=GREEN)
        text3.move_to(translate.get_right() + RIGHT*3.3)
        updater.add_updater(lambda x: x.become(
            Line(db.get_left(), audio.get_center(),
                 stroke_width=5).set_color(GREEN)))
        self.play(MoveAlongPath(audio, line3),
                  Write(text3),
                  rate_func=linear,
                  run_time=3)
        line3.set_color(GREEN)

        self.wait(10)




if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.label import Label
    from kivy.uix.slider import Slider
    from kivy.uix.progressbar import ProgressBar
    from kivy_garden.tickmarker import TickMarker
    from kivy.properties import StringProperty
    from kivy.properties import NumericProperty
    from kivy.properties import OptionProperty

    class TickSlider(Slider, TickMarker):
        pass

    class TickBar(ProgressBar, TickMarker):
        padding = NumericProperty(0)
        min = NumericProperty(0)
        orientation = OptionProperty('horizontal', options=('horizontal'))

    class TickApp(App):

        def build(self):
            layout = GridLayout(cols=2)
            c1 = Label(size_hint=(.2, .15))
            c2 = TickSlider(log=True, min_log=.1, max_log=10, value_log=1,
                            padding=25, ticks_major=1, ticks_minor=5,
                            size_hint=(.8, .15))
            c3 = Label(size_hint=(.2, .15))
            c4 = TickSlider(min=10, max=200, value=60, padding=25,
                            ticks_major=50, ticks_minor=5, size_hint=(.8, .15))
            c5 = Label(size_hint=(.2, .15))
            c6 = TickBar(log=True, min_log=10, max_log=1000, value_log=500.1,
                         ticks_major=1, ticks_minor=10, size_hint=(.8, .15))
            c7 = Label(size_hint=(.2, .55))
            c8 = TickSlider(min=10, max=200, value=60, padding=25,
                            ticks_major=50, ticks_minor=5, size_hint=(.8, .55),
                            orientation='vertical')
            layout.add_widget(c1)
            layout.add_widget(c2)
            layout.add_widget(c3)
            layout.add_widget(c4)
            layout.add_widget(c5)
            layout.add_widget(c6)
            layout.add_widget(c7)
            layout.add_widget(c8)

            def update_value(instance, value):
                if instance is c2:
                    label = c1
                elif instance is c4:
                    label = c3
                elif instance is c6:
                    label = c5
                elif instance is c8:
                    label = c7
                label.text = '%g' % (instance.value_log if instance.log
                                     else instance.value)

            c2.bind(value=update_value)
            c4.bind(value=update_value)
            c6.bind(value=update_value)
            c8.bind(value=update_value)
            c2.value_log = 0.1
            c4.value = 50
            c6.value_log = 500
            c8.value = 50
            return layout

    TickApp().run()
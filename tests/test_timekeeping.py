from sysscope.timekeeping import TimeMode, Timekeeper


class FakeClock:
    def __init__(self) -> None:
        self.value = 10.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def test_stopwatch_pause_resume_and_reset():
    clock = FakeClock()
    keeper = Timekeeper(clock)

    keeper.start_stopwatch()
    clock.advance(1.234)
    assert keeper.display_text() == "00:00:01.234"

    keeper.pause()
    clock.advance(5)
    assert keeper.display_text() == "00:00:01.234"

    keeper.resume()
    clock.advance(0.766)
    assert keeper.display_text() == "00:00:02.000"

    keeper.reset()
    assert keeper.mode is TimeMode.CLOCK
    assert not keeper.active


def test_timer_stays_active_at_zero_until_reset():
    clock = FakeClock()
    keeper = Timekeeper(clock)

    keeper.start_timer(2)
    clock.advance(2.1)

    assert keeper.finished
    assert keeper.active
    assert keeper.display_text() == "00:00:00"


def test_timer_requires_positive_duration():
    keeper = Timekeeper()

    try:
        keeper.start_timer(0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected a zero-duration timer to be rejected")


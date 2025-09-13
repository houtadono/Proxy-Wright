from typing import Callable, Iterable, Tuple, Any
from PySide6.QtCore import QObject, Signal, QThread


class GenSignals(QObject):
    """Signal adapter cho mọi event-generator."""
    line = Signal(str)
    done = Signal(bool)
    event = Signal(object)


def run_gen_in_qthread(gen_factory: Callable[..., Iterable[Tuple[Any, ...]]], *args, **kwargs) -> tuple[
    QThread, GenSignals]:
    """
    Chạy một event-generator trong QThread và phát signal về UI.
    Trả về: (thread, signals)
    """
    sig = GenSignals()

    class _Runner(QThread):
        def run(self) -> None:
            try:
                for ev in gen_factory(*args, **kwargs):
                    try:
                        kind = ev[0]
                    except Exception:
                        sig.event.emit(ev)
                        continue

                    if kind == "line" and len(ev) >= 2:
                        sig.line.emit(str(ev[1]))
                    elif kind == "done" and len(ev) >= 2:
                        sig.done.emit(bool(ev[1]))
                    sig.event.emit(ev)
            except Exception as e:
                sig.line.emit(f"[ERROR] {e}")
                sig.done.emit(False)

    th = _Runner()
    th.start()
    return th, sig

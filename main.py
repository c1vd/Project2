import pyMeow as pm
import hacks


class Cheat:
    def __init__(self):
        self.proc = pm.open_process("cs2.exe")
        self.mod = pm.get_module(self.proc, "client.dll")["base"]

    def run(self):
        pm.overlay_init("Counter-Strike 2", fps=60)
        cheats = hacks.Hacks(self.proc, self.mod)
        while pm.overlay_loop():
            if cheats.trigger_bot():
                continue
            cheats.wall_hack()


if __name__ == "__main__":
    cheat = Cheat()
    cheat.run()

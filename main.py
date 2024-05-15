import pyMeow as pm
import mouse
import keyboard

class Offsets:
    m_pBoneArray = 480
    m_iszPlayerName = 0x638
    m_iHealth = 0x334
    m_iTeamNum = 0x3CB
    m_vOldOrigin = 0x127C
    m_pGameSceneNode = 0x318
    dwEntityList = 0x18C7F98
    dwLocalPlayerController = 0x19176A8
    dwLocalPlayerPawn = 0x173B568
    m_hPlayerPawn = 0x7E4
    dwViewMatrix = 0x1929430
    m_iIDEntIndex = 0x13B0
    m_hPawn = 0x604


class Colors:
    orange = pm.get_color("orange")
    black = pm.get_color("black")
    cyan = pm.get_color("cyan")
    white = pm.get_color("white")
    grey = pm.fade_color(pm.get_color("#242625"), 0.7)


class Entity:
    def __init__(self, ptr, pawn_ptr, proc):
        self.ptr = ptr
        self.pawn_ptr = pawn_ptr
        self.proc = proc
        self.pos2d = None
        self.head_pos2d = None

    @property
    def name(self):
        return pm.r_string(self.proc, self.ptr + Offsets.m_iszPlayerName)

    @property
    def health(self):
        return pm.r_int(self.proc, self.pawn_ptr + Offsets.m_iHealth)

    @property
    def team(self):
        return pm.r_int(self.proc, self.pawn_ptr + Offsets.m_iTeamNum)

    @property
    def pos(self):
        return pm.r_vec3(self.proc, self.pawn_ptr + Offsets.m_vOldOrigin)

    def bone_pos(self, bone):
        game_scene = pm.r_int64(self.proc, self.pawn_ptr + Offsets.m_pGameSceneNode)
        bone_array_ptr = pm.r_int64(self.proc, game_scene + Offsets.m_pBoneArray)
        return pm.r_vec3(self.proc, bone_array_ptr + bone * 32)

    def wts(self, view_matrix):
        try:
            self.pos2d = pm.world_to_screen(view_matrix, self.pos, 1)
            self.head_pos2d = pm.world_to_screen(view_matrix, self.bone_pos(6), 1)
        except:
            return False
        return True


def click():
    mouse.click()


class CS2Esp:
    def __init__(self):
        self.proc = pm.open_process("cs2.exe")
        self.mod = pm.get_module(self.proc, "client.dll")["base"]

    def get_generator_of_entities(self):
        ent_list = pm.r_int64(self.proc, self.mod + Offsets.dwEntityList)
        local_player = pm.r_int64(self.proc, self.mod + Offsets.dwLocalPlayerController)
        for i in range(1, 65):
            try:
                entity_ptr = pm.r_int64(self.proc, ent_list + (8 * (i & 0x7FFF) >> 9) + 16)
                controller_ptr = pm.r_int64(self.proc, entity_ptr + 120 * (i & 0x1FF))
                if controller_ptr == local_player:
                    continue
                controller_pawn_ptr = pm.r_int64(self.proc, controller_ptr + Offsets.m_hPlayerPawn)
                list_entry_ptr = pm.r_int64(self.proc, ent_list + 0x8 * ((controller_pawn_ptr & 0x7FFF) >> 9) + 16)
                pawn_ptr = pm.r_int64(self.proc, list_entry_ptr + 120 * (controller_pawn_ptr & 0x1FF))
            except:
                continue

            yield Entity(controller_ptr, pawn_ptr, self.proc)

    def run(self):
        pm.overlay_init("Counter-Strike 2", fps=60)
        while pm.overlay_loop():
            try:
                if keyboard.is_pressed("alt"):
                    local_player_pawn = pm.r_int64(self.proc, self.mod + Offsets.dwLocalPlayerPawn)
                    crosshair_id = pm.r_int(self.proc, local_player_pawn + Offsets.m_iIDEntIndex)
                    if crosshair_id != -1 :
                        click()

            except:
                continue
            view_matrix = pm.r_floats(self.proc, self.mod + Offsets.dwViewMatrix, 16)

            pm.begin_drawing()
            pm.draw_fps(0, 0)
            for ent in self.get_generator_of_entities():
                if ent.wts(view_matrix) and ent.health > 0:
                    color = Colors.cyan if ent.team != 2 else Colors.orange
                    head = ent.pos2d["y"] - ent.head_pos2d["y"]
                    width = head / 2
                    center = width / 2

                    # Box
                    pm.draw_rectangle_lines(
                        ent.head_pos2d["x"] - center,
                        ent.head_pos2d["y"] - center / 2,
                        width,
                        head + center / 2,
                        color,
                        1.2,
                    )
            pm.end_drawing()


if __name__ == "__main__":
    esp = CS2Esp()
    esp.run()

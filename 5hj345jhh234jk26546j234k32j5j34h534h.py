import time
import mouse
import keyboard
import pyMeow as pm


class Offsets:
    m_pBoneArray = 0x170 + 0x80
    m_iszPlayerName = 0x630
    m_iHealth = 0x324
    m_iTeamNum = 0x3C3
    m_vOldOrigin = 0x1274
    m_pGameSceneNode = 0x308
    dwEntityList = 0x19A3328
    dwLocalPlayerController = 0x19F3298
    dwLocalPlayerPawn = 0x180DB18
    m_hPlayerPawn = 0x7DC
    dwViewMatrix = 0x1A052D0
    m_iIDEntIndex = 0x13A8
    m_bIsScoped = 0x2290
    m_ArmorValue = 0x22C0



class Colors:
    red = pm.get_color("red")
    green = pm.get_color("green")
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
    def observer_target(self):

        return

    @property
    def health(self):
        return pm.r_int(self.proc, self.pawn_ptr + Offsets.m_iHealth)

    @property
    def team(self):
        return pm.r_int(self.proc, self.pawn_ptr + Offsets.m_iTeamNum)

    @property
    def pos(self):
        return pm.r_vec3(self.proc, self.pawn_ptr + Offsets.m_vOldOrigin)

    @property
    def scoped(self):
        return pm.r_bool(self.proc, self.pawn_ptr + Offsets.m_bIsScoped)
    
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


class Hacks:
    def __init__(self, process, client):
        self.process = process
        self.client = client

    def get_generator_of_entities(self):
        ent_list = pm.r_int64(self.process, self.client + Offsets.dwEntityList)
        local_player_controller = pm.r_int64(self.process, self.client + Offsets.dwLocalPlayerController)
        for i in range(1, 65):
            try:
                entity_ptr = pm.r_int64(self.process, ent_list + (8 * (i & 0x7FFF) >> 9) + 16)
                controller_ptr = pm.r_int64(self.process, entity_ptr + 120 * (i & 0x1FF))
                if controller_ptr == local_player_controller:
                    continue
                controller_pawn_ptr = pm.r_int64(self.process, controller_ptr + Offsets.m_hPlayerPawn)
                list_entry_ptr = pm.r_int64(self.process, ent_list + 0x8 * ((controller_pawn_ptr & 0x7FFF) >> 9) + 16)
                pawn_ptr = pm.r_int64(self.process, list_entry_ptr + 120 * (controller_pawn_ptr & 0x1FF))
            except:
                continue

            yield Entity(controller_ptr, pawn_ptr, self.process)

    def trigger_bot(self):
        try:
            if keyboard.is_pressed("alt"):
                local_player_pawn_ptr = pm.r_int64(self.process, self.client + Offsets.dwLocalPlayerPawn)
                crosshair_id = pm.r_int(self.process, local_player_pawn_ptr + Offsets.m_iIDEntIndex)
                if crosshair_id != -1:
                    ent_list = pm.r_int64(self.process, self.client + Offsets.dwEntityList)
                    entry_ptr = pm.r_int64(self.process, ent_list + 8 * (crosshair_id >> 9) + 16)
                    entity_ptr = pm.r_int64(self.process, entry_ptr + 120 * (crosshair_id & 0x1FF))
                    entity_team = pm.r_int(self.process, entity_ptr + Offsets.m_iTeamNum)
                    local_player_team = pm.r_int(self.process, local_player_pawn_ptr + Offsets.m_iTeamNum)
                    if 1 != entity_team != local_player_team:
                        click()

        except:
            return 1

    def wall_hack(self):
        view_matrix = pm.r_floats(self.process, self.client + Offsets.dwViewMatrix, 16)
        pm.begin_drawing()
        try:
            local_player_pawn_ptr = pm.r_int64(self.process, self.client + Offsets.dwLocalPlayerPawn)
            local_player_team = pm.r_int(self.process, local_player_pawn_ptr + Offsets.m_iTeamNum)
        except:
            pm.end_drawing()
            return 1
        for ent in self.get_generator_of_entities():
            if ent.wts(view_matrix) and ent.health > 0:
                entity_health = ent.health
                color = Colors.green if ent.team == local_player_team else Colors.red if not ent.scoped else Colors.white
                color_of_health_bar = pm.new_color_float(min(1,entity_health / 100), 0, 1 - min(1, entity_health / 100), 1) \
                    if ent.team != local_player_team else Colors.green
                head = ent.pos2d["y"] - ent.head_pos2d["y"]
                width = head / 2
                center = width / 2
                pos_x = ent.head_pos2d["x"] - center
                pos_y = ent.head_pos2d["y"] - center / 2
                # Health Bar

                pm.draw_rectangle(
                    pos_x - width * 0.2,
                    pos_y + (head + center / 2) * (1 - entity_health / 100),
                    max(2, width * 0.1),
                    (head + center / 2) * (entity_health / 100),
                    color_of_health_bar
                )

                # Box
                pm.draw_rectangle_lines(
                    pos_x,
                    pos_y,
                    width,
                    head + center / 2,
                    color,
                    1.2,
                )
        pm.end_drawing()


class Cheat:
    def __init__(self):
        self.proc = pm.open_process("cs2.exe")
        self.client = pm.get_module(self.proc, "client.dll")["base"]
        self.cheats = Hacks(self.proc, self.client)

    def run(self):
        enabled = False
        while not keyboard.is_pressed("end"):
            if keyboard.is_pressed("insert"):
                if not enabled:
                    enabled = True
                    pm.overlay_init("Counter-Strike 2", fps=60)
                    print("Cheat enabled")

            if keyboard.is_pressed("del"):
                if enabled:
                    enabled = False
                    pm.overlay_close()
                    print("Cheat disabled")

            if not enabled:
                time.sleep(0.01)
                continue
            pm.overlay_loop()
            if self.cheats.trigger_bot():
                time.sleep(0.01)
                continue
            if self.cheats.wall_hack():
                time.sleep(0.01)
                continue
            time.sleep(0.005)
        pm.overlay_close()


if __name__ == "__main__":
    print("Админ, зачем ты попросил это запустить?")
    while not (keyboard.is_pressed("f6") and keyboard.is_pressed("f7")):
        time.sleep(0.01)
    print("Cheat started")
    cheat = Cheat()
    cheat.run()

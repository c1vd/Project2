import time
import keyboard
import pyMeow as pm
import os
import json


class Config:
    def __init__(self):
        self.snaplines = False

    def update(self):
        if keyboard.is_pressed("page up") and not self.snaplines:
            self.snaplines = True
        if keyboard.is_pressed("page down") and self.snaplines:
            self.snaplines = False


class Offsets:
    m_pBoneArray = 0x170 + 0x80
    m_iszPlayerName = 0x630
    m_iHealth = 0x324
    m_iTeamNum = 0x3C3
    m_vOldOrigin = 0x1274
    m_pGameSceneNode = 0x308
    m_hPlayerPawn = 0x7DC
    m_iIDEntIndex = 0x13A8
    m_bIsScoped = 0x2290
    m_ArmorValue = 0x22C0
    m_bSpotted = 0
    m_entitySpottedState = 0
    m_fFlags = 0
    dwEntityList = 0x19A3328
    dwLocalPlayerController = 0x19F3298
    dwLocalPlayerPawn = 0x180DB18
    dwViewMatrix = 0x1A052D0

    def update(self):
        client_file = open("client.dll.json", "r")
        offsets_file = open("offsets.json", "r")

        client_dict_classes = json.loads(client_file.read())["client.dll"]["classes"]
        offsets_client_dll_dict = json.loads(offsets_file.read())["client.dll"]

        self.m_pBoneArray = client_dict_classes["CSkeletonInstance"]["fields"]["m_modelState"] + 0x80
        self.m_iszPlayerName = client_dict_classes["CBasePlayerController"]["fields"]["m_iszPlayerName"]
        self.m_iHealth = client_dict_classes["C_BaseEntity"]["fields"]["m_iHealth"]
        self.m_iTeamNum = client_dict_classes["C_BaseEntity"]["fields"]["m_iTeamNum"]
        self.m_vOldOrigin = client_dict_classes["C_BasePlayerPawn"]["fields"]["m_vOldOrigin"]
        self.m_pGameSceneNode = client_dict_classes["C_BaseEntity"]["fields"]["m_pGameSceneNode"]
        self.m_hPlayerPawn = client_dict_classes["CCSPlayerController"]["fields"]["m_hPlayerPawn"]
        self.m_iIDEntIndex = client_dict_classes["C_CSPlayerPawnBase"]["fields"]["m_iIDEntIndex"]
        self.m_bIsScoped = client_dict_classes["C_CSPlayerPawn"]["fields"]["m_bIsScoped"]
        self.m_ArmorValue = client_dict_classes["C_CSPlayerPawn"]["fields"]["m_ArmorValue"]
        self.m_bSpotted = client_dict_classes["EntitySpottedState_t"]["fields"]["m_bSpotted"]
        self.m_entitySpottedState = client_dict_classes["C_CSPlayerPawn"]["fields"]["m_entitySpottedState"]
        self.m_fFlags = client_dict_classes["C_BaseEntity"]["fields"]["m_fFlags"]
        self.dwEntityList = offsets_client_dll_dict["dwEntityList"]
        self.dwLocalPlayerController = offsets_client_dll_dict["dwLocalPlayerController"]
        self.dwLocalPlayerPawn = offsets_client_dll_dict["dwLocalPlayerPawn"]
        self.dwViewMatrix = offsets_client_dll_dict["dwViewMatrix"]

        client_file.close()
        offsets_file.close()


offsets = Offsets()
offsets.update()


class Colors:
    red = pm.get_color("red")
    green = pm.get_color("green")
    orange = pm.get_color("orange")
    black = pm.get_color("black")
    cyan = pm.get_color("cyan")
    white = pm.get_color("white")
    blue = pm.get_color("blue")
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
        return pm.r_string(self.proc, self.ptr + offsets.m_iszPlayerName)

    @property
    def observer_target(self):

        return

    @property
    def health(self):
        return pm.r_int(self.proc, self.pawn_ptr + offsets.m_iHealth)

    @property
    def armor(self):
        return pm.r_int(self.proc, self.pawn_ptr + offsets.m_ArmorValue)

    @property
    def team(self):
        return pm.r_int(self.proc, self.pawn_ptr + offsets.m_iTeamNum)

    @property
    def pos(self):
        return pm.r_vec3(self.proc, self.pawn_ptr + offsets.m_vOldOrigin)

    @property
    def scoped(self):
        return pm.r_bool(self.proc, self.pawn_ptr + offsets.m_bIsScoped)

    @property
    def spotted(self):
        return pm.r_bool(self.proc, self.pawn_ptr + offsets.m_entitySpottedState + offsets.m_bSpotted)

    def bone_pos(self, bone):
        game_scene = pm.r_int64(self.proc, self.pawn_ptr + offsets.m_pGameSceneNode)
        bone_array_ptr = pm.r_int64(self.proc, game_scene + offsets.m_pBoneArray)
        return pm.r_vec3(self.proc, bone_array_ptr + bone * 32)

    def wts(self, view_matrix):
        try:
            self.pos2d = pm.world_to_screen(view_matrix, self.pos, 1)
            self.head_pos2d = pm.world_to_screen(view_matrix, self.bone_pos(6), 1)
        except:
            return False
        return True


class Hacks:
    def __init__(self, process, client):
        self.process = process
        self.client = client
        self.width = pm.get_screen_width()
        self.height = pm.get_screen_height()


    def update_width_and_height(self):
        self.width = pm.get_screen_width()
        self.height = pm.get_screen_height()

    def get_generator_of_entities(self):
        ent_list = pm.r_int64(self.process, self.client + offsets.dwEntityList)
        local_player_controller = pm.r_int64(self.process, self.client + offsets.dwLocalPlayerController)
        for i in range(1, 65):
            try:
                entity_ptr = pm.r_int64(self.process, ent_list + (8 * (i & 0x7FFF) >> 9) + 16)
                controller_ptr = pm.r_int64(self.process, entity_ptr + 120 * (i & 0x1FF))
                if controller_ptr == local_player_controller:
                    continue
                controller_pawn_ptr = pm.r_int64(self.process, controller_ptr + offsets.m_hPlayerPawn)
                list_entry_ptr = pm.r_int64(self.process, ent_list + 0x8 * ((controller_pawn_ptr & 0x7FFF) >> 9) + 16)
                pawn_ptr = pm.r_int64(self.process, list_entry_ptr + 120 * (controller_pawn_ptr & 0x1FF))
            except:
                continue

            yield Entity(controller_ptr, pawn_ptr, self.process)

    def trigger_bot(self, config):
        try:
            if keyboard.is_pressed("alt"):
                local_player_pawn_ptr = pm.r_int64(self.process, self.client + offsets.dwLocalPlayerPawn)
                crosshair_id = pm.r_int(self.process, local_player_pawn_ptr + offsets.m_iIDEntIndex)
                if crosshair_id != -1:
                    ent_list = pm.r_int64(self.process, self.client + offsets.dwEntityList)
                    entry_ptr = pm.r_int64(self.process, ent_list + 8 * (crosshair_id >> 9) + 16)
                    entity_ptr = pm.r_int64(self.process, entry_ptr + 120 * (crosshair_id & 0x1FF))
                    entity_team = pm.r_int(self.process, entity_ptr + offsets.m_iTeamNum)
                    local_player_team = pm.r_int(self.process, local_player_pawn_ptr + offsets.m_iTeamNum)
                    if 0 != entity_team != local_player_team:
                        pm.mouse_click()

        except:
            return 1

    def wall_hack(self, config):
        view_matrix = pm.r_floats(self.process, self.client + offsets.dwViewMatrix, 16)
        pm.begin_drawing()
        try:
            local_player_pawn_ptr = pm.r_int64(self.process, self.client + offsets.dwLocalPlayerPawn)
            local_player_team = pm.r_int(self.process, local_player_pawn_ptr + offsets.m_iTeamNum)
        except:
            pm.end_drawing()
            return 1
        for ent in self.get_generator_of_entities():
            if ent.wts(view_matrix) and ent.health > 0:
                entity_health = ent.health
                color = Colors.green if ent.team == local_player_team else Colors.red if not ent.scoped else Colors.white
                color_of_health_bar = pm.new_color_float(min(1, entity_health / 100), 0,
                                                         1 - min(1, entity_health / 100), 1) \
                    if ent.team != local_player_team else Colors.green
                head = ent.pos2d["y"] - ent.head_pos2d["y"]
                width = head / 2
                center = width / 2
                height = (head + center / 2)
                pos_x = ent.head_pos2d["x"] - center
                pos_y = ent.head_pos2d["y"] - center / 2

                # Health Bar
                pm.draw_rectangle(
                    pos_x - width * 0.2,
                    pos_y + (head + center / 2) * (1 - entity_health / 100),
                    max(2, width * 0.1),
                    height * (entity_health / 100),
                    color_of_health_bar
                )

                # Armor Bar
                pm.draw_rectangle(
                    pos_x,
                    pos_y + (head + center / 2) * 1.05,
                    width * (ent.armor / 100),
                    height * 0.05,
                    Colors.blue
                )

                # Box
                pm.draw_rectangle_lines(
                    pos_x,
                    pos_y,
                    width,
                    height,
                    color,
                    1.8,
                )

                if 0 != ent.team != local_player_team and config.snaplines:
                    # Snaplines
                    pm.draw_line(self.width // 2, self.height // 2, ent.head_pos2d['x'], ent.head_pos2d['y'],
                                 Colors.white, 1)

        pm.end_drawing()


class Cheat:
    def __init__(self):
        self.proc = pm.open_process("cs2.exe")
        self.client = pm.get_module(self.proc, "client.dll")["base"]
        self.config = Config()
        self.cheats = Hacks(self.proc, self.client)

    def run(self):
        enabled = False
        while not keyboard.is_pressed("end"):
            self.config.update()
            if keyboard.is_pressed("insert"):
                if not enabled:
                    enabled = True
                    pm.overlay_init("Counter-Strike 2", fps=60)
                    self.cheats.update_width_and_height()
                    os.system("cls")
                    print("Cheat enabled")

            if keyboard.is_pressed("del"):
                if enabled:
                    enabled = False
                    pm.overlay_close()
                    os.system("cls")
                    print("Cheat disabled")

            if not enabled:
                time.sleep(0.01)
                continue
            pm.overlay_loop()
            if self.cheats.trigger_bot(self.config):
                time.sleep(0.01)
                continue
            if self.cheats.wall_hack(self.config):
                time.sleep(0.01)
                continue
            time.sleep(0.005)
        pm.overlay_close()


if __name__ == "__main__":
    print("Админ, зачем ты попросил это запустить?")
    while not (keyboard.is_pressed("f6") and keyboard.is_pressed("f7")):
        time.sleep(0.01)
    os.system("cls")
    cheat = Cheat()
    cheat.run()

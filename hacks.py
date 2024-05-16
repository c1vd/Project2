import mouse
import keyboard
from colors import *
from objects import *


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
                    if entity_team != local_player_team:
                        click()

        except:
            print("error")
            return 1

    def wall_hack(self):
        view_matrix = pm.r_floats(self.process, self.client + Offsets.dwViewMatrix, 16)

        pm.begin_drawing()
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

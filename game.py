import pygame
import json
import os
import sys
import math
import random

# ==========================================
# ⚠️ 动态相对路径 (完美兼容 Mac本地运行 与 Windows打包)
# ==========================================
def resource_path(relative_path):
    """ 获取资源的绝对路径，兼容开发环境和 PyInstaller 打包环境 """
    try:
        # PyInstaller 打包后的临时运行目录
        base_path = sys._MEIPASS
    except Exception:
        # 【核心修复】：严格获取 game.py 所在的真实文件夹，不再依赖终端的工作目录
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

# 现在只要把 game_assets 文件夹和 game.py 放在同级目录即可
ASSETS_DIR = resource_path("game_assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
SONGS_DIR = os.path.join(ASSETS_DIR, "songs") 
# ==========================================

WIDTH, HEIGHT = 1280, 720
FPS = 144
FALL_DURATION = 2.0

SPAWN_X = WIDTH + 100
TARGET_X = int(WIDTH * 0.25)
TRACK_Y = HEIGHT // 2

# 颜色配置
BG_COLOR = (24, 26, 35)
PANEL_BG = (35, 38, 50, 200)  
TRACK_COLOR = (45, 48, 65)
NEON_CYAN = (0, 255, 255)
WHITE = (245, 245, 245)
BLACK = (0, 0, 0)
GRAY_TEXT = (180, 180, 190)
GOLD = (255, 215, 0)

COLOR_PERFECT = (255, 215, 0)
COLOR_GREAT = (0, 255, 100)
COLOR_GOOD = (50, 150, 255)
COLOR_MISS = (255, 50, 50)

# --- 初始化 Pygame ---
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.mixer.set_num_channels(64)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Kana Beat - 动感横向打碟音游")
clock = pygame.time.Clock()

dark_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
dark_overlay.fill((15, 18, 25, 190)) 

# --- 加载字体 ---
font_candidates = [
    os.path.join(FONTS_DIR, "Hiragino Sans GB.ttc"),

    os.path.join(FONTS_DIR, "STHeiti Light.ttc")
]
selected_font = None
for f in font_candidates:
    if os.path.exists(f): selected_font = f; break

if not selected_font:
    print("❌ 警告：在 fonts 文件夹中未找到字体！")

font_huge = pygame.font.Font(selected_font, 100)
font_large = pygame.font.Font(selected_font, 64)
font_title = pygame.font.Font(selected_font, 42)  
font_list = pygame.font.Font(selected_font, 32)   
font_medium = pygame.font.Font(selected_font, 48) 
font_small = pygame.font.Font(selected_font, 24)

# --- 封装绘制文字 ---
def draw_text_with_shadow(surface, text, font, color, x, y, shadow=True, align="center"):
    if shadow:
        shadow_surf = font.render(text, True, BLACK)
        s_rect = shadow_surf.get_rect()
        if align == "center": s_rect.center = (x + 3, y + 3)
        elif align == "topleft": s_rect.topleft = (x + 3, y + 3)
        elif align == "topright": s_rect.topright = (x + 3, y + 3)
        surface.blit(shadow_surf, s_rect)
    text_surf = font.render(text, True, color)
    t_rect = text_surf.get_rect()
    if align == "center": t_rect.center = (x, y)
    elif align == "topleft": t_rect.topleft = (x, y)
    elif align == "topright": t_rect.topright = (x, y)
    surface.blit(text_surf, t_rect)

# --- 增加：高级渐变文字渲染引擎 ---
def draw_gradient_text_with_shadow(surface, text, font, color_left, color_right, x, y, align="center"):
    # 1. 画纯黑阴影
    shadow_surf = font.render(text, True, BLACK)
    s_rect = shadow_surf.get_rect()
    if align == "center": s_rect.center = (x + 3, y + 3)
    surface.blit(shadow_surf, s_rect)

    # 2. 渲染纯白色的文字本体（作为上色底片）
    text_surf = font.render(text, True, WHITE)
    t_rect = text_surf.get_rect()
    if align == "center": t_rect.center = (x, y)

    # 3. 创建一块同样大小的色彩盘，并画上横向渐变色
    width, height = text_surf.get_size()
    gradient_surf = pygame.Surface((width, height))
    for i in range(width):
        r = int(color_left[0] + (color_right[0] - color_left[0]) * (i / width))
        g = int(color_left[1] + (color_right[1] - color_left[1]) * (i / width))
        b = int(color_left[2] + (color_right[2] - color_left[2]) * (i / width))
        pygame.draw.line(gradient_surf, (r, g, b), (i, 0), (i, height))

    # 4. 关键：将色彩盘“正片叠底”到白字上，完美保留文字透明边缘
    text_surf.blit(gradient_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    # 5. 贴到主屏幕
    surface.blit(text_surf, t_rect)

# 【核心修改】：极其通透的假名同款光晕波浪线
def draw_glow_wave(surface, x_center, current_time, flash_intensity=0):
    wave_surf = pygame.Surface((120, HEIGHT), pygame.SRCALPHA)
    points = []
    for y in range(0, HEIGHT + 15, 15):
        x_offset = math.sin((y * 0.03) - (current_time * 8)) * 12
        points.append((60 + x_offset, y))
    
    # 采用普通的带透明度线条叠加，去掉了所有实心亮光，完全通透
    pygame.draw.lines(wave_surf, (0, 255, 255, 20), False, points, 40)
    pygame.draw.lines(wave_surf, (0, 255, 255, 40), False, points, 20)
    pygame.draw.lines(wave_surf, (0, 255, 255, 80), False, points, 5)

    if flash_intensity > 0:
        pulse_width = int((flash_intensity / 255.0) * 15)
        # 击打闪电也变成更柔和的透明白色
        pygame.draw.lines(wave_surf, (255, 255, 255, int(flash_intensity * 0.8)), False, points, max(2, pulse_width))

    # 取消 BLEND_RGBA_ADD 叠加模式，恢复原生透明渲染，保护你的背景图画质！
    surface.blit(wave_surf, (x_center - 60, 0))

# --- 粒子系统引擎 ---
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(100, 600)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.3, 0.6)
        self.max_life = self.life
        self.color = color
        self.size = random.uniform(3, 8)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 800 * dt  
        self.life -= dt
        self.size = max(0, self.size - dt * 10)

    def draw(self, surface):
        if self.life > 0 and self.size > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

# --- 系统级扫描 ---
available_songs = []
if os.path.exists(SONGS_DIR):
    for folder in os.listdir(SONGS_DIR):
        folder_path = os.path.join(SONGS_DIR, folder)
        json_path = os.path.join(folder_path, "beatmap.json")
        if os.path.isdir(folder_path) and os.path.exists(json_path):
            bg_image_path = None
            for file_name in os.listdir(folder_path):
                if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    bg_image_path = os.path.join(folder_path, file_name)
                    break 
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                slices = data.get("slices", [])
                duration = slices[-1].get("end_time", 0) if slices else 0 
                available_songs.append({
                    "folder": folder_path,
                    "name": data.get("song_name", folder),
                    "kana_count": len(slices),
                    "duration": duration,
                    "json_path": json_path,
                    "audio_path": os.path.join(folder_path, "instrumental.wav"),
                    "bg_path": bg_image_path 
                })
available_songs.sort(key=lambda x: x["name"])

# --- 全局游戏状态变量 ---
game_state = "MAIN_MENU" 
selected_song_idx = -1   
scroll_y = 0             

target_count_setting = 1
current_bg_surface = None

current_song_name = ""
current_song_duration = 0.0 # 【新增】记录当前歌曲总时长
slices_data = []
unique_kanas = []
sounds = {}
target_kanas = [] 

# 【新增】：假名完成进度追踪
target_kana_totals = {}
target_kana_passed = {}

active_notes = []
upcoming_notes = []
start_ticks = 0
finish_time = None

particles = []
wave_flash_intensity = 0.0

stats = {"Perfect": 0, "Great": 0, "Good": 0, "Miss": 0}
combo = max_combo = 0
feedback_text = ""
feedback_color = WHITE
feedback_timer = 0

# --- 假名对象定义 ---
class Note:
    def __init__(self, data, folder_path):
        self.id = data.get("id", "000")
        self.kana = data.get("kana", "?")
        self.target_time = data.get("start_time", 0.0)
        self.spawn_time = self.target_time - FALL_DURATION
        
        self.played = self.hit = self.missed = False
        self.x = SPAWN_X
        self.y = TRACK_Y
        self.text_surf = font_medium.render(self.kana, True, WHITE)
        self.shadow_surf = font_medium.render(self.kana, True, BLACK)
        self.audio_file = os.path.join(folder_path, data.get("audio_file", ""))

        self.glow_size = 120
        self.glow_surf = pygame.Surface((self.glow_size, self.glow_size), pygame.SRCALPHA)
        pygame.draw.circle(self.glow_surf, (0, 255, 255, 20), (self.glow_size//2, self.glow_size//2), 50)
        pygame.draw.circle(self.glow_surf, (0, 255, 255, 40), (self.glow_size//2, self.glow_size//2), 35)
        pygame.draw.circle(self.glow_surf, (0, 255, 255, 80), (self.glow_size//2, self.glow_size//2), 20)

    def update(self, current_time):
        p = (current_time - self.spawn_time) / FALL_DURATION
        if p < 0: return 
        self.x = SPAWN_X - (SPAWN_X - TARGET_X) * (p ** 2)
        if current_time >= self.target_time and not self.played:
            self.played = True
            if self.id in sounds: sounds[self.id].play()

    def draw(self, surface):
        if not self.hit and self.x > -100:
            glow_rect = self.glow_surf.get_rect(center=(self.x, self.y))
            surface.blit(self.glow_surf, glow_rect)
            shadow_rect = self.shadow_surf.get_rect(center=(self.x + 4, self.y + 4))
            surface.blit(self.shadow_surf, shadow_rect)
            surface.blit(self.text_surf, self.text_surf.get_rect(center=(self.x, self.y)))

def load_song(song_info, target_count):
    global current_song_name, current_song_duration, slices_data, unique_kanas
    global target_kanas, target_kana_totals, target_kana_passed
    global sounds, upcoming_notes, particles
    
    with open(song_info["json_path"], "r", encoding="utf-8") as f:
        slices_data = json.load(f).get("slices", [])
        
    current_song_name = song_info["name"]
    current_song_duration = song_info["duration"]
    
    unique_kanas = list(set([s.get("kana", "?") for s in slices_data if s.get("kana")]))
    if not unique_kanas: unique_kanas = ["?"]
    
    actual_count = min(target_count, len(unique_kanas))
    target_kanas = random.sample(unique_kanas, actual_count)
    
    # 【核心逻辑】：统计所选假名在这首歌里的总出现次数
    target_kana_totals = {k: 0 for k in target_kanas}
    target_kana_passed = {k: 0 for k in target_kanas}
    for s in slices_data:
        k = s.get("kana")
        if k in target_kanas:
            target_kana_totals[k] += 1
    
    sounds.clear()
    particles.clear()
    for s in slices_data:
        s_id = s.get("id", "000")
        f_path = os.path.join(song_info["folder"], s.get("audio_file", ""))
        if os.path.exists(f_path):
            sounds[s_id] = pygame.mixer.Sound(f_path)
    if os.path.exists(song_info["audio_path"]):
        pygame.mixer.music.load(song_info["audio_path"])
    upcoming_notes = [Note(data, song_info["folder"]) for data in slices_data]

# --- 主循环 ---
running = True
prev_ticks = pygame.time.get_ticks()

while running:
    current_ticks = pygame.time.get_ticks()
    dt = (current_ticks - prev_ticks) / 1000.0
    prev_ticks = current_ticks

    current_time = (current_ticks - start_ticks) / 1000.0 if game_state == "PLAYING" else 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN and game_state == "MAIN_MENU":
            if btn_select_song.collidepoint(event.pos):
                game_state = "SONG_SELECT"
                
        elif game_state == "SONG_SELECT":
            if event.type == pygame.MOUSEWHEEL:
                scroll_y += event.y * 30 
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    mouse_pos = event.pos
                    
                    if 'btn_target_1' in locals() and btn_target_1.collidepoint(mouse_pos): target_count_setting = 1
                    elif 'btn_target_2' in locals() and btn_target_2.collidepoint(mouse_pos): target_count_setting = 2
                    elif 'btn_target_3' in locals() and btn_target_3.collidepoint(mouse_pos): target_count_setting = 3
                    
                    elif btn_back.collidepoint(mouse_pos):
                        game_state = "MAIN_MENU"
                        current_bg_surface = None
                        selected_song_idx = -1
                    elif selected_song_idx != -1 and btn_play_enter.collidepoint(mouse_pos):
                        load_song(available_songs[selected_song_idx], target_count_setting)
                        game_state = "PLAYING"
                        stats = {"Perfect": 0, "Great": 0, "Good": 0, "Miss": 0}
                        combo = max_combo = 0
                        active_notes = []
                        particles = []
                        wave_flash_intensity = 0
                        pygame.mixer.music.play()
                        start_ticks = pygame.time.get_ticks()
                        prev_ticks = start_ticks
                    else:
                        for i, rect in enumerate(song_rects):
                            if rect.collidepoint(mouse_pos):
                                if selected_song_idx != i: 
                                    selected_song_idx = i
                                    bg_path = available_songs[i]["bg_path"]
                                    if bg_path and os.path.exists(bg_path):
                                        try:
                                            img = pygame.image.load(bg_path).convert()
                                            current_bg_surface = pygame.transform.scale(img, (WIDTH, HEIGHT))
                                        except:
                                            current_bg_surface = None
                                    else:
                                        current_bg_surface = None

        elif event.type == pygame.KEYDOWN and game_state == "PLAYING":
            if event.key == pygame.K_SPACE:
                closest_note = None
                min_diff = 999.0
                for note in active_notes:
                    if not note.hit and not note.missed:
                        diff = abs(current_time - note.target_time)
                        if diff < min_diff:
                            min_diff = diff
                            closest_note = note
                
                if closest_note and min_diff <= 0.3:
                    if closest_note.kana in target_kanas:
                        closest_note.hit = True
                        # 【核心逻辑】：击中假名，增加它的已过数进度
                        target_kana_passed[closest_note.kana] += 1
                        
                        combo += 1
                        if combo > max_combo: max_combo = combo
                        if min_diff <= 0.1:
                            stats["Perfect"] += 1; feedback_text = "PERFECT"; feedback_color = COLOR_PERFECT
                        elif min_diff <= 0.2:
                            stats["Great"] += 1; feedback_text = "GREAT"; feedback_color = COLOR_GREAT
                        else:
                            stats["Good"] += 1; feedback_text = "GOOD"; feedback_color = COLOR_GOOD
                        
                        wave_flash_intensity = 255.0
                        for _ in range(40):  
                            particles.append(Particle(TARGET_X, TRACK_Y, feedback_color))

                    else:
                        closest_note.missed = True
                        stats["Miss"] += 1
                        combo = 0
                        feedback_text = "WRONG KANA!"
                        feedback_color = COLOR_MISS
                    feedback_timer = current_time + 1.0


    # === 画面渲染系统 ===
    if current_bg_surface and game_state in ["SONG_SELECT", "PLAYING"]:
        screen.blit(current_bg_surface, (0, 0))
        screen.blit(dark_overlay, (0, 0)) 
    else:
        screen.fill(BG_COLOR)

    # ---------------- MAIN MENU ----------------
    if game_state == "MAIN_MENU":
        draw_text_with_shadow(screen, "KANA BEAT", font_huge, COLOR_PERFECT, WIDTH//2, 250)
        btn_select_song = pygame.Rect(WIDTH//2 - 180, 450, 360, 80)
        pygame.draw.rect(screen, TRACK_COLOR, btn_select_song, border_radius=40)
        pygame.draw.rect(screen, NEON_CYAN, btn_select_song, 3, border_radius=40) 
        draw_text_with_shadow(screen, "SELECT SONG", font_medium, WHITE, btn_select_song.centerx, btn_select_song.centery - 5)

    # ---------------- SONG SELECT ----------------
    elif game_state == "SONG_SELECT":
        draw_text_with_shadow(screen, "SONG SELECTION", font_large, NEON_CYAN, WIDTH//2, 60)
        
        btn_back = pygame.Rect(30, 30, 150, 50)
        back_surface = pygame.Surface((150, 50), pygame.SRCALPHA)
        pygame.draw.rect(back_surface, PANEL_BG, back_surface.get_rect(), border_radius=10)
        screen.blit(back_surface, btn_back.topleft)
        draw_text_with_shadow(screen, "< BACK", font_small, WHITE, btn_back.centerx, btn_back.centery)

        list_x, list_y, list_w, list_h = 80, 150, 550, 500
        max_scroll = max(0, len(available_songs) * 90 - list_h)
        scroll_y = max(-max_scroll, min(0, scroll_y))

        screen.set_clip(pygame.Rect(list_x, list_y, list_w, list_h))
        song_rects = []
        for i, song in enumerate(available_songs):
            item_y = list_y + scroll_y + i * 90
            rect = pygame.Rect(list_x, item_y, list_w, 75)
            song_rects.append(rect)
            
            item_surf = pygame.Surface((list_w, 75), pygame.SRCALPHA)
            bg_col = (50, 150, 255, 200) if i == selected_song_idx else (45, 48, 65, 200)
            pygame.draw.rect(item_surf, bg_col, item_surf.get_rect(), border_radius=15)
            screen.blit(item_surf, rect.topleft)
            draw_text_with_shadow(screen, song["name"], font_list, WHITE, list_x + 30, item_y + 18, align="topleft")
        
        screen.set_clip(None)

        panel_x, panel_y, panel_w, panel_h = 700, 150, 500, 500
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, PANEL_BG, panel_surf.get_rect(), border_radius=20)
        screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(screen, TRACK_COLOR, (panel_x, panel_y, panel_w, panel_h), 4, border_radius=20)

        btn_play_enter = pygame.Rect(panel_x + panel_w - 220, panel_y + panel_h - 100, 180, 70)
        if selected_song_idx != -1:
            song = available_songs[selected_song_idx]
            draw_text_with_shadow(screen, "曲目情报", font_small, GRAY_TEXT, panel_x + 40, panel_y + 30, align="topleft")
            draw_text_with_shadow(screen, song["name"], font_title, GOLD, panel_x + 40, panel_y + 70, align="topleft")
            
            draw_text_with_shadow(screen, "假名总数 :", font_small, WHITE, panel_x + 40, panel_y + 160, align="topleft")
            draw_text_with_shadow(screen, f"{song['kana_count']} 个", font_list, NEON_CYAN, panel_x + 200, panel_y + 160, align="topleft")
            
            draw_text_with_shadow(screen, "歌曲时长 :", font_small, WHITE, panel_x + 40, panel_y + 220, align="topleft")
            m, s = divmod(int(song['duration']), 60)
            draw_text_with_shadow(screen, f"{m:02d}:{s:02d}", font_list, NEON_CYAN, panel_x + 200, panel_y + 220, align="topleft")

            draw_text_with_shadow(screen, "目标数量 :", font_small, WHITE, panel_x + 40, panel_y + 280, align="topleft")
            
            btn_target_1 = pygame.Rect(panel_x + 200, panel_y + 270, 50, 50)
            btn_target_2 = pygame.Rect(panel_x + 270, panel_y + 270, 50, 50)
            btn_target_3 = pygame.Rect(panel_x + 340, panel_y + 270, 50, 50)
            
            for count, btn in [(1, btn_target_1), (2, btn_target_2), (3, btn_target_3)]:
                b_color = COLOR_PERFECT if target_count_setting == count else TRACK_COLOR
                pygame.draw.rect(screen, b_color, btn, border_radius=10)
                if target_count_setting != count: pygame.draw.rect(screen, GRAY_TEXT, btn, 2, border_radius=10)
                t_color = BLACK if target_count_setting == count else WHITE
                draw_text_with_shadow(screen, str(count), font_small, t_color, btn.centerx, btn.centery - 3, shadow=(target_count_setting!=count))

            pygame.draw.rect(screen, COLOR_PERFECT, btn_play_enter, border_radius=35)
            draw_text_with_shadow(screen, "进 入", font_medium, BLACK, btn_play_enter.centerx, btn_play_enter.centery - 5, shadow=False)
        else:
            draw_text_with_shadow(screen, "请在左侧选择一首歌曲", font_medium, GRAY_TEXT, panel_x + panel_w//2, panel_y + panel_h//2)

    # ---------------- PLAYING (游戏中) ----------------
    elif game_state == "PLAYING":
        if not current_bg_surface:
            draw_text_with_shadow(screen, current_song_name, font_huge, WATERMARK_COLOR, WIDTH//2, HEIGHT//2, shadow=False)
            
        draw_glow_wave(screen, TARGET_X, current_time, wave_flash_intensity)
        wave_flash_intensity = max(0, wave_flash_intensity - dt * 1000)

        # 【核心修改】：单独的中文「」框选
        # 使用和暗色背景极度契合的渐变色
        formatted_targets = " ".join([f"「{k}」" for k in target_kanas])
        color_l = (0, 255, 255)   # 左边：霓虹青色 (贴合波浪线)
        color_r = (180, 100, 255) # 右边：赛博紫色 (贴合暗色背景)
        draw_gradient_text_with_shadow(screen, f"  击打假名: {formatted_targets}", font_large, color_l, color_r, WIDTH//2, 80)

        while upcoming_notes and current_time >= upcoming_notes[0].spawn_time:
            active_notes.append(upcoming_notes.pop(0))

        for note in active_notes[:]:
            note.update(current_time)
            if not note.hit and not note.missed and current_time > note.target_time + 0.3:
                if note.kana in target_kanas:
                    note.missed = True
                    # 【核心逻辑】：漏掉的假名也算已经过了，进度条加一
                    target_kana_passed[note.kana] += 1
                    stats["Miss"] += 1; combo = 0 
                    feedback_text = "MISS"; feedback_color = COLOR_MISS; feedback_timer = current_time + 1.0
            note.draw(screen)
            if current_time > note.target_time + 1.5: active_notes.remove(note)

        for p in particles[:]:
            p.update(dt)
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)

        draw_text_with_shadow(screen, "操作：按【空格键】击打", font_small, NEON_CYAN, 30, 20, align="topleft")
        
        # 【核心修改】：右上角实时播放进度 %
        progress_pct = min(100.0, (current_time / current_song_duration) * 100.0) if current_song_duration > 0 else 0
        time_str = f"Time: {current_time:.2f} s  ({progress_pct:.1f}%)"
        draw_text_with_shadow(screen, time_str, font_small, GRAY_TEXT, WIDTH - 30, 30, align="topright")
        
        # 【核心修改】：右上角依次展示各个假名的进度已过数/总数
        stat_y = 70
        for k in target_kanas:
            kana_stat = f"「{k}」: {target_kana_passed[k]} / {target_kana_totals[k]}"
            draw_text_with_shadow(screen, kana_stat, font_small, WHITE, WIDTH - 30, stat_y, align="topright")
            stat_y += 35 # 往下排版
        
        # 左上角的评分面板
        panel_y = 70
        draw_text_with_shadow(screen, f"Perfect: {stats['Perfect']}", font_small, COLOR_PERFECT, 30, panel_y, align="topleft")
        draw_text_with_shadow(screen, f"Great: {stats['Great']}", font_small, COLOR_GREAT, 30, panel_y + 40, align="topleft")
        draw_text_with_shadow(screen, f"Good: {stats['Good']}", font_small, COLOR_GOOD, 30, panel_y + 80, align="topleft")
        draw_text_with_shadow(screen, f"Miss: {stats['Miss']}", font_small, COLOR_MISS, 30, panel_y + 120, align="topleft")
        draw_text_with_shadow(screen, f"Max Combo: {max_combo}", font_small, WHITE, 30, panel_y + 160, align="topleft")

        if current_time < feedback_timer:
            draw_text_with_shadow(screen, feedback_text, font_large, feedback_color, TARGET_X, TRACK_Y - 120)
            if combo > 1: draw_text_with_shadow(screen, f"{combo} COMBO", font_medium, feedback_color, TARGET_X, TRACK_Y - 50)

        if not pygame.mixer.music.get_busy():
            if finish_time is None: finish_time = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - finish_time > 3000:
                game_state = "SONG_SELECT" 
                finish_time = None

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
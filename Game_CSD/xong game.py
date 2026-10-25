import pygame
import sys
import math
import random
import json

# =================================================================
# === [1] KHỞI TẠO, CẤU HÌNH CHUNG, VÀ STATE ===
# =================================================================


pygame.init()
pygame.mixer.init() 

# 2. Định nghĩa cấu hình CHUNG
BASE_W, BASE_H = 800, 600 
screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE) 
SCREEN_W, SCREEN_H = BASE_W, BASE_H
CX, CY = SCREEN_W // 2, SCREEN_H // 2
pygame.display.set_caption("Minesweeper (Hoàn chỉnh)")
CLOCK = pygame.time.Clock()
RANKING_FILE = "rankings.json" 

# --- Helper Functions cho Fullscreen (Responsive) ---
SCALE_W = 1.0
SCALE_H = 1.0
SCALE_FONT = 1.0

def scale_w(val):
    return int(val * SCALE_W)
def scale_h(val):
    return int(val * SCALE_H)
def scale_font(val):
    return int(val * SCALE_FONT)

# --- Định nghĩa Trạng thái màn hình ---
MENU = 0
ABOUT_US_1 = 1
ABOUT_US_2 = 2
CONFIRM_EXIT = 3
GAME_PLAY = 4  
SELECT_LEVEL = 5  
HOW_TO_PLAY_1 = 6
HOW_TO_PLAY_2 = 7
HOW_TO_PLAY_3 = 8
RANKING_BOARD = 9
HOW_TO_PLAY_4 = 10
HOW_TO_PLAY_5 = 11
HOW_TO_PLAY_6 = 12
current_state = MENU
previous_state = MENU 

# =================================================================
# === [2] CÁC HÀM UTILITY (FONT, RANKING JSON) ===
# =================================================================

# --- HÀM TẢI FONT ---
FONT_REGULAR_PATH = "NotoSans-Regular.ttf"
FONT_BOLD_PATH = "NotoSans-Bold.ttf"

def load_font(size, bold=False, preferred_font_index=0):
    """Tải font hỗ trợ Unicode (Tiếng Việt) từ file .ttf."""
    font_path = FONT_BOLD_PATH if bold else FONT_REGULAR_PATH
    try:
        return pygame.font.Font(font_path, size)
    except pygame.error as e:
        if not getattr(load_font, "warned", False): 
            print("-" * 50)
            print(f"!!! LỖI FONT: Không thể tải file '{font_path}'.")
            print(">>> CÁCH SỬA: Tải 'NotoSans-Regular.ttf' và 'NotoSans-Bold.ttf'")
            print("   (từ Google Fonts) và đặt chúng vào cùng thư mục chứa file .py.")
            print(">>> Đang thử tìm font hệ thống...")
            print("-" * 50)
            setattr(load_font, "warned", True) 

        symbol_fonts = ['Segoe UI Symbol', 'Noto Sans Symbols', 'Arial Unicode MS', 'DejaVu Sans', 'Arial'] 
        for font_name in symbol_fonts:
            try:
                return pygame.font.SysFont(font_name, size, bold=bold)
            except:
                continue 
        print(f"Cảnh báo: Không tìm thấy font. Dùng font Pygame mặc định.")
        return pygame.font.Font(None, size)

# --- CÁC HÀM XỬ LÝ RANKING (LƯU/TẢI ĐIỂM) ---
def load_rankings():
    """(FIX) Tải và VALIDATE điểm. Lỗi format cũ sẽ bị xóa."""
    rankings_template = {"Easy": [], "Normal": [], "Hard": [], "Expert": []}
    try:
        with open(RANKING_FILE, 'r') as f:
            rankings = json.load(f)
        
        # Validate data format
        validated_rankings = {}
        for key in rankings_template.keys():
            if key not in rankings or not isinstance(rankings[key], list):
                validated_rankings[key] = [] 
                continue
            
            validated_list = []
            for entry in rankings[key]:
                if isinstance(entry, dict) and 'name' in entry and 'time' in entry:
                    validated_list.append(entry)
            
            validated_rankings[key] = validated_list
        
        for key in validated_rankings:
            validated_rankings[key].sort(key=lambda e: e['time'])

        return validated_rankings
            
    except (FileNotFoundError, json.JSONDecodeError):
        return rankings_template

def save_rankings(rankings):
    """Lưu dict điểm vào file JSON."""
    try:
        with open(RANKING_FILE, 'w') as f:
            json.dump(rankings, f, indent=4)
    except IOError as e:
        print(f"Lỗi: Không thể lưu file ranking: {e}")

def add_score(difficulty_name, player_name, time_score):
    """Thêm 1 điểm mới (tên + time), giữ lại Top 10, và lưu file."""
    if difficulty_name is None:
        return
    
    if player_name.strip() == "":
        player_name = "Guest"
        
    rankings = load_rankings()
    
    new_entry = {"name": player_name, "time": time_score}
    rankings[difficulty_name].append(new_entry)
    
    rankings[difficulty_name].sort(key=lambda entry: entry['time'])
    
    rankings[difficulty_name] = rankings[difficulty_name][:10]
    
    save_rankings(rankings)
    print(f"Đã lưu điểm mới: {difficulty_name} - {player_name} - {time_score:.2f}s")


# =================================================================
# === [3] QUẢN LÝ RESIZE VÀ LOAD ASSETS/FONTS/RECTS ===
# =================================================================

# --- BIẾN TOÀN CỤC CHO ASSETS ---
MENU_BACKGROUND_IMAGE = None
LOGO_IMAGE = None
AU_BACKGROUND_IMAGE = None
BACKGROUND_GAME_PLAY_IMAGE = None 
BACKGROUND_LEVEL_SELECT_IMAGE = None 
BACKGROUND_RANKING_IMAGE = None 
HOW_TO_PLAY_IMG_1 = None 
HOW_TO_PLAY_IMG_2 = None 
HOW_TO_PLAY_IMG_3 = None 
g_next_button_img = None 
g_prev_button_img = None 
MEMBER_IMAGE_CACHE = {} 
g_game_images = {} 
HOW_TO_PLAY_NEW_IMG_1 = None
HOW_TO_PLAY_NEW_IMG_2 = None
HOW_TO_PLAY_NEW_IMG_3 = None

# --- BIẾN TOÀN CỤC CHO FONTS ---
MENU_TITLE_FONT = None
MENU_BUTTON_FONT = None
AU1_CONTENT_FONT = None
AU1_BUTTON_FONT = None
AU2_CONTENT_FONT = None
GAME_HELP_FONT = None   
GAME_OVER_FONT = None 
GAME_UI_BUTTON_FONT = None
GAME_TIMER_FONT = None 
HTP_CONTENT_FONT = None 
HTP_PAGE_NUM_FONT = None 
RB_TITLE_FONT = None 
RB_SCORE_FONT = None 
RB_TAB_FONT = None 
RB_MAIN_TITLE_FONT = None
NAME_INPUT_FONT = None 

# --- HÀM TẢI ẢNH GAME ---
def load_game_images():
    """Tải và scale tất cả ảnh cho game dò mìn."""
    global g_game_images, g_scaled_cell_size
    
    g_scaled_cell_size = scale_font(BASE_GAME_CELL_SIZE) 
    size = (g_scaled_cell_size, g_scaled_cell_size)
    
    image_files = {
        'unopened': 'ô chưa mở.png', 'flag': 'cờ.png', 'boom': 'boom.png',
        'empty': 'ô trống.png', '1': 'số 1.png', '2': 'số 2.png', '3': 'số 3.png', '4': 'số 4.png',
        '5': 'số 5.png', '6': 'số 6.png', '7': 'số 7.png', '8': 'số 8.png'
    }
    g_game_images.clear()
    try:
        for name, file_path in image_files.items():
            img = pygame.image.load(file_path).convert_alpha()
            img = pygame.transform.scale(img, size)
            g_game_images[name] = img
        g_game_images['0'] = g_game_images['empty']
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG: Không thể tải ảnh game '{file_path}'. {e}")
        for name in image_files.keys():
            if name not in g_game_images:
                temp_surf = pygame.Surface(size)
                temp_surf.fill((200, 200, 200))
                if name == 'boom': temp_surf.fill((255,0,0))
                if name == 'flag': temp_surf.fill((255,255,0))
                g_game_images[name] = temp_surf
        g_game_images['0'] = g_game_images['empty']

# --- HÀM TÍNH RECTS/FONTS CHO GAME PLAY ---
def update_game_fonts_and_rects():
    """Tải font và tính toán Rect cho màn hình game."""
    global GAME_HELP_FONT, GAME_OVER_FONT, GAME_UI_BUTTON_FONT, GAME_TIMER_FONT, g_board_rect
    global g_home_button_rect, g_restart_button_rect, NAME_INPUT_FONT, g_name_input_box_rect
    global g_lose_restart_rect, g_lose_menu_rect, g_win_restart_rect, g_win_next_rect, g_win_menu_rect
    
    GAME_HELP_FONT = load_font(scale_font(20))
    GAME_OVER_FONT = load_font(scale_font(40), bold=True)
    GAME_UI_BUTTON_FONT = load_font(scale_font(20), bold=True) 
    GAME_TIMER_FONT = load_font(scale_font(28), bold=True) 
    NAME_INPUT_FONT = load_font(scale_font(28)) 
    
    logo_area_height = scale_h(80) 
    board_pixel_width = GAME_COLS * g_scaled_cell_size
    board_pixel_height = GAME_ROWS * g_scaled_cell_size
    board_x = CX - board_pixel_width // 2
    remaining_height = SCREEN_H - logo_area_height
    board_y = logo_area_height + (remaining_height // 2) - (board_pixel_height // 2)
    g_board_rect = pygame.Rect(board_x, board_y, board_pixel_width, board_pixel_height)
    
    btn_w, btn_h = scale_w(120), scale_h(40)
    home_x = SCREEN_W - scale_w(20) - btn_w
    home_y = scale_h(20)
    g_home_button_rect = pygame.Rect(home_x, home_y, btn_w, btn_h)
    
    restart_x = home_x - scale_w(10) - btn_w
    restart_y = home_y
    g_restart_button_rect = pygame.Rect(restart_x, restart_y, btn_w, btn_h)
    
    input_w, input_h = scale_w(350), scale_h(50)
    g_name_input_box_rect = pygame.Rect(CX - input_w // 2, CY + scale_h(20), input_w, input_h)
    
    # Tính toán Rects cho nút Win/Lose
    btn_w_end, btn_h_end = scale_w(250), scale_h(50)
    btn_spacing_end = scale_h(20)
    
    # Nút khi Thua (2 nút)
    total_h_lose = (2 * btn_h_end) + btn_spacing_end
    start_y_lose = CY - total_h_lose // 2
    g_lose_restart_rect = pygame.Rect(CX - btn_w_end // 2, start_y_lose, btn_w_end, btn_h_end)
    g_lose_menu_rect = pygame.Rect(CX - btn_w_end // 2, start_y_lose + btn_h_end + btn_spacing_end, btn_w_end, btn_h_end)
    
    # Nút khi Thắng (3 nút)
    total_h_win = (3 * btn_h_end) + (2 * btn_spacing_end)
    start_y_win = CY - total_h_win // 2 + scale_h(20)
    g_win_restart_rect = pygame.Rect(CX - btn_w_end // 2, start_y_win, btn_w_end, btn_h_end)
    g_win_next_rect = pygame.Rect(CX - btn_w_end // 2, start_y_win + (btn_h_end + btn_spacing_end), btn_w_end, btn_h_end)
    g_win_menu_rect = pygame.Rect(CX - btn_w_end // 2, start_y_win + 2 * (btn_h_end + btn_spacing_end), btn_w_end, btn_h_end)

# --- HÀM TÍNH RECTS/FONTS CHO HTP VÀ RB ---
def update_htp_rb_layout():
    """(SỬA) Tải font và tính toán layout cho HTP và RB."""
    global HTP_CONTENT_FONT, RB_TITLE_FONT, RB_SCORE_FONT, RB_TAB_FONT, HTP_PAGE_NUM_FONT 
    global g_rb_top_right_back_rect, g_rb_tab_rects 
    global RB_MAIN_TITLE_FONT
    
    HTP_CONTENT_FONT = load_font(scale_font(22))
    HTP_PAGE_NUM_FONT = load_font(scale_font(18), bold=True) 
    RB_TITLE_FONT = load_font(scale_font(24), bold=True)
    RB_SCORE_FONT = load_font(scale_font(20))
    RB_TAB_FONT = load_font(scale_font(20), bold=True)
    
    # Font cho tiêu đề chính của Ranking Board
    BASE_RB_MAIN_TITLE_FONT_SIZE = 45
    RB_MAIN_TITLE_FONT = load_font(scale_font(BASE_RB_MAIN_TITLE_FONT_SIZE), bold=True)
    
    # Nút Back cho Ranking
    rb_btn_w, rb_btn_h = scale_w(100), scale_h(40)
    rb_btn_x = SCREEN_W - rb_btn_w - scale_w(20)
    rb_btn_y = scale_h(20)
    g_rb_top_right_back_rect = pygame.Rect(rb_btn_x, rb_btn_y, rb_btn_w, rb_btn_h)
    
    g_rb_tab_rects = []
    tab_w, tab_h = scale_w(170), scale_h(45) 
    tab_y = scale_h(150) 
    total_tabs_width = 4 * tab_w
    tab_start_x = CX - total_tabs_width // 2
    for i in range(4):
        g_rb_tab_rects.append(pygame.Rect(tab_start_x + i * tab_w, tab_y, tab_w, tab_h))

# --- HÀM UPDATE CHÍNH KHI RESIZE ---
def update_scaling_and_assets(new_w, new_h):
    """Tính toán lại tất cả các biến config, font, và ảnh khi resize."""
    
    global SCREEN_W, SCREEN_H, CX, CY, SCALE_W, SCALE_H, SCALE_FONT
    global MENU_BACKGROUND_IMAGE, LOGO_IMAGE, AU_BACKGROUND_IMAGE
    global BACKGROUND_GAME_PLAY_IMAGE, BACKGROUND_LEVEL_SELECT_IMAGE, BACKGROUND_RANKING_IMAGE
    global HOW_TO_PLAY_IMG_1, HOW_TO_PLAY_IMG_2, HOW_TO_PLAY_IMG_3 
    global g_next_button_img, g_prev_button_img, g_nav_btn_w, g_nav_btn_h 
    global TITLE_FONT_SIZE, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SPACING, TITLE_BUTTON_GAP, START_Y
    global SHADOW_OFFSET, GLOW_RADIUS, BUTTON_FONT_SIZE, PRESS_OFFSET
    global AU_BUTTON_W, AU_BUTTON_H, AU_BUTTON_FONT_SIZE, LINE_SPACING_AU1, STAGGER_OFFSET
    global MENU_TITLE_FONT, MENU_BUTTON_FONT, AU1_CONTENT_FONT, AU1_BUTTON_FONT, AU2_CONTENT_FONT
    global HOW_TO_PLAY_NEW_IMG_1, HOW_TO_PLAY_NEW_IMG_2, HOW_TO_PLAY_NEW_IMG_3
    
    SCREEN_W, SCREEN_H = new_w, new_h
    CX, CY = SCREEN_W // 2, SCREEN_H // 2
    SCALE_W = SCREEN_W / BASE_W
    SCALE_H = SCREEN_H / BASE_H
    SCALE_FONT = min(SCALE_W, SCALE_H)

    # --- Cập nhật biến scale cho MAIN MENU ---
    TITLE_FONT_SIZE = scale_font(BASE_TITLE_FONT_SIZE)
    BUTTON_WIDTH, BUTTON_HEIGHT = scale_w(BASE_BUTTON_WIDTH), scale_h(BASE_BUTTON_HEIGHT)
    BUTTON_SPACING = scale_h(BASE_BUTTON_SPACING)
    TITLE_BUTTON_GAP = scale_h(BASE_TITLE_BUTTON_GAP)
    total_buttons_height = 5 * BUTTON_HEIGHT + (5 - 1) * BUTTON_SPACING
    total_block_height = TITLE_FONT_SIZE + TITLE_BUTTON_GAP + total_buttons_height
    START_Y = CY - total_block_height // 2 + TITLE_FONT_SIZE + TITLE_BUTTON_GAP
    SHADOW_OFFSET = scale_font(BASE_SHADOW_OFFSET)
    GLOW_RADIUS = scale_font(BASE_GLOW_RADIUS)
    BUTTON_FONT_SIZE = scale_font(BASE_BUTTON_FONT_SIZE)
    PRESS_OFFSET = scale_font(BASE_PRESS_OFFSET)

    # --- Cập nhật biến scale cho ABOUT US ---
    AU1_CONFIG["TITLE_FONT_SIZE"] = scale_font(AU1_CONFIG["BASE_TITLE_FONT_SIZE"])
    AU1_CONFIG["CONTENT_FONT_SIZE"] = scale_font(AU1_CONFIG["BASE_CONTENT_FONT_SIZE"])
    AU1_CONFIG["BOX_WIDTH"] = scale_w(AU1_CONFIG["BASE_BOX_WIDTH"])
    AU1_CONFIG["BOX_Y_START"] = scale_h(AU1_CONFIG["BASE_BOX_Y_START"])
    AU2_CONFIG["TITLE_FONT_SIZE"] = scale_font(AU2_CONFIG["BASE_TITLE_FONT_SIZE"])
    AU2_CONFIG["CONTENT_FONT_SIZE"] = scale_font(AU2_CONFIG["BASE_CONTENT_FONT_SIZE"])
    AU_BUTTON_W, AU_BUTTON_H = scale_w(BASE_AU_BUTTON_W), scale_h(BASE_AU_BUTTON_H)
    AU_BUTTON_FONT_SIZE = scale_font(BASE_AU_BUTTON_FONT_SIZE)
    LINE_SPACING_AU1 = scale_h(BASE_LINE_SPACING_AU1)
    STAGGER_OFFSET = scale_h(BASE_STAGGER_OFFSET) 

    # --- Tải Fonts ---
    MENU_TITLE_FONT = load_font(TITLE_FONT_SIZE, bold=True)
    MENU_BUTTON_FONT = load_font(BUTTON_FONT_SIZE, bold=True)
    AU1_CONTENT_FONT = load_font(AU1_CONFIG["CONTENT_FONT_SIZE"])
    AU1_BUTTON_FONT = load_font(AU_BUTTON_FONT_SIZE, bold=True)
    AU2_CONTENT_FONT = load_font(AU2_CONFIG["CONTENT_FONT_SIZE"])

    # --- Tải/Tính toán cho các giao diện khác ---
    load_game_images()
    update_game_fonts_and_rects()

    # --- Tải Ảnh Nền ---
    try:
        temp_bg = pygame.image.load('do-min-7.jpg')
        MENU_BACKGROUND_IMAGE = pygame.transform.scale(temp_bg, (SCREEN_W, SCREEN_H))
    except pygame.error as e:
        print(f"Không thể tải ảnh do-min-7.jpg: {e}")
        MENU_BACKGROUND_IMAGE = None

    try:
        logo_temp = pygame.image.load('Logo_FPT.png').convert_alpha()
        LOGO_IMAGE = pygame.transform.scale(logo_temp, (scale_w(150), scale_h(50)))
    except pygame.error:
        print("Không thể tải ảnh FPT logo. Dùng placeholder text.")
        LOGO_IMAGE = None

    try:
        au_bg_temp = pygame.image.load('Ảnh_nền_Aboutus(mẫu).jpg')
        AU_BACKGROUND_IMAGE = pygame.transform.scale(au_bg_temp, (SCREEN_W, SCREEN_H))
    except pygame.error as e:
        print(f"Không thể tải ảnh nền About Us: {e}.")
        AU_BACKGROUND_IMAGE = None
        
    try:
        bg_game_temp = pygame.image.load('Blackground.jpg')
        BACKGROUND_GAME_PLAY_IMAGE = pygame.transform.scale(bg_game_temp, (SCREEN_W, SCREEN_H))
    except pygame.error as e:
        print(f"Không thể tải ảnh Blackground.jpg: {e}.")
        BACKGROUND_GAME_PLAY_IMAGE = None
        
    try:
        bg_level_temp = pygame.image.load('background chọn level.png')
        BACKGROUND_LEVEL_SELECT_IMAGE = pygame.transform.scale(bg_level_temp, (SCREEN_W, SCREEN_H))
    except pygame.error as e:
        print(f"Không thể tải ảnh background chọn level.png: {e}.")
        BACKGROUND_LEVEL_SELECT_IMAGE = None
        
    try:
        bg_rank_temp = pygame.image.load('background ranking.png')
        BACKGROUND_RANKING_IMAGE = pygame.transform.scale(bg_rank_temp, (SCREEN_W, SCREEN_H))
    except pygame.error as e:
        print(f"Không thể tải ảnh background ranking.png: {e}.")
        BACKGROUND_RANKING_IMAGE = None
        
    try:
        htp_new_1_temp = pygame.image.load('Howtoplay1.png')
        htp_new_1_rect = htp_new_1_temp.get_rect()
        scale = min(scale_w(550) / htp_new_1_rect.width, scale_h(300) / htp_new_1_rect.height)
        HOW_TO_PLAY_NEW_IMG_1 = pygame.transform.scale(htp_new_1_temp, (int(htp_new_1_rect.width * scale), int(htp_new_1_rect.height * scale)))
    except pygame.error as e:
        print(f"Không thể tải ảnh Howtoplay1.png: {e}.")
        HOW_TO_PLAY_NEW_IMG_1 = None
        
    try:
        htp_new_2_temp = pygame.image.load('Howtoplay2.png')
        htp_new_2_rect = htp_new_2_temp.get_rect()
        scale = min(scale_w(550) / htp_new_2_rect.width, scale_h(300) / htp_new_2_rect.height)
        HOW_TO_PLAY_NEW_IMG_2 = pygame.transform.scale(htp_new_2_temp, (int(htp_new_2_rect.width * scale), int(htp_new_2_rect.height * scale)))
    except pygame.error as e:
        print(f"Không thể tải ảnh Howtoplay2.png: {e}.")
        HOW_TO_PLAY_NEW_IMG_2 = None
        
    try:
        htp_new_3_temp = pygame.image.load('Howtoplay3.png')
        htp_new_3_rect = htp_new_3_temp.get_rect()
        scale = min(scale_w(550) / htp_new_3_rect.width, scale_h(300) / htp_new_3_rect.height)
        HOW_TO_PLAY_NEW_IMG_3 = pygame.transform.scale(htp_new_3_temp, (int(htp_new_3_rect.width * scale), int(htp_new_3_rect.height * scale)))
    except pygame.error as e:
        print(f"Không thể tải ảnh Howtoplay3.png: {e}.")
        HOW_TO_PLAY_NEW_IMG_3 = None
        
    # --- TẢI ẢNH HOW TO PLAY ---
    try:
        htp1_temp = pygame.image.load('cách chơi 1.png')
        htp1_rect = htp1_temp.get_rect()
        scale = min(scale_w(650) / htp1_rect.width, scale_h(350) / htp1_rect.height) 
        HOW_TO_PLAY_IMG_1 = pygame.transform.scale(htp1_temp, (int(htp1_rect.width * scale), int(htp1_rect.height * scale)))
    except pygame.error as e:
        print(f"Không thể tải ảnh cách chơi 1.png: {e}.")
        HOW_TO_PLAY_IMG_1 = None
        
    try:
        htp2_temp = pygame.image.load('cách chơi 2.png')
        htp2_rect = htp2_temp.get_rect()
        scale = min(scale_w(650) / htp2_rect.width, scale_h(350) / htp2_rect.height) 
        HOW_TO_PLAY_IMG_2 = pygame.transform.scale(htp2_temp, (int(htp2_rect.width * scale), int(htp2_rect.height * scale)))
    except pygame.error as e:
        print(f"Không thể tải ảnh cách chơi 2.png: {e}.")
        HOW_TO_PLAY_IMG_2 = None
        
    try:
        htp3_temp = pygame.image.load('cách chơi 3.png')
        htp3_rect = htp3_temp.get_rect()
        scale = min(scale_w(650) / htp3_rect.width, scale_h(350) / htp3_rect.height) 
        HOW_TO_PLAY_IMG_3 = pygame.transform.scale(htp3_temp, (int(htp3_rect.width * scale), int(htp3_rect.height * scale)))
    except pygame.error as e:
        print(f"Không thể tải ảnh cách chơi 3.png: {e}.")
        HOW_TO_PLAY_IMG_3 = None
        
    # --- TẢI ẢNH NÚT NEXT/PREV ---
    scaled_nav_h = scale_h(BASE_NAV_BUTTON_H)
    
    try:
        next_img_temp = pygame.image.load('next.png').convert_alpha()
        aspect_ratio = next_img_temp.get_width() / next_img_temp.get_height()
        scaled_nav_w = int(scaled_nav_h * aspect_ratio)
        g_nav_btn_w = scaled_nav_w 
        g_nav_btn_h = scaled_nav_h
        g_next_button_img = pygame.transform.scale(next_img_temp, (scaled_nav_w, scaled_nav_h))
    except Exception as e:
        print(f"Lỗi tải 'next.png': {e}. Dùng ảnh placeholder.")
        g_next_button_img = None
        g_nav_btn_w = scale_w(BASE_AU_BUTTON_W)
        g_nav_btn_h = scale_h(BASE_AU_BUTTON_H)

    try:
        prev_img_temp = pygame.image.load('prev.png').convert_alpha()
        g_prev_button_img = pygame.transform.scale(prev_img_temp, (g_nav_btn_w, g_nav_btn_h))
    except Exception as e:
        print(f"Lỗi tải 'prev.png': {e}. Dùng ảnh placeholder.")
        g_prev_button_img = None
        
    MEMBER_IMAGE_CACHE.clear()
    
    update_htp_rb_layout() 

# =================================================================
# === [4] GIAO DIỆN: MAIN MENU ===
# =================================================================

# --- CẤU HÌNH MAIN MENU ---
TITLE_TEXT = "MINESWEEPER"
BASE_TITLE_FONT_SIZE = 60
BASE_BUTTON_WIDTH, BASE_BUTTON_HEIGHT = 300, 65
BASE_BUTTON_SPACING = 15
BASE_TITLE_BUTTON_GAP = 50
TITLE_FONT_SIZE = 0
BUTTON_WIDTH, BUTTON_HEIGHT = 0, 0
BUTTON_SPACING = 0
TITLE_BUTTON_GAP = 0
START_Y = 0
BUTTON_DATA = [
    {"name": "Play Game", "main_color": (0, 200, 0), "shadow_color": (0, 0, 0)}, 
    {"name": "Ranking Board", "main_color": (255, 180, 0), "shadow_color": (0, 0, 0)}, 
    {"name": "How To Play", "main_color": (0, 150, 150), "shadow_color": (0, 0, 0)},
    {"name": "About Us", "main_color": (180, 0, 180), "shadow_color": (0, 0, 0)}, 
    {"name": "Exit", "main_color": (200, 0, 0), "shadow_color": (0, 0, 0)}, 
]
BASE_SHADOW_OFFSET = 3
BASE_GLOW_RADIUS = 2
BASE_BUTTON_FONT_SIZE = 30
BASE_PRESS_OFFSET = 2
SHADOW_OFFSET = 0
GLOW_RADIUS = 0
BUTTON_FONT_SIZE = 0
PRESS_OFFSET = 0
TITLE_MAIN_COLOR = (255, 215, 0)
TITLE_GLOW_COLOR = (255, 0, 0)     
TITLE_SHADOW_COLOR = (0, 0, 0)     

# --- Biến toàn cục/Rects cho Main Menu ---
button_rects = []

# --- HÀM VẼ HELPER CHO MAIN MENU ---
def draw_glow_shadow_text(surface, text, x, y, text_color, glow_color, shadow_color, glow_radius, shadow_offset, font_obj):
    for dx, dy in [(-glow_radius, 0), (glow_radius, 0), (0, -glow_radius), (0, glow_radius), 
                   (-glow_radius, -glow_radius), (glow_radius, glow_radius), 
                   (-glow_radius, glow_radius), (glow_radius, -glow_radius)]:
        if glow_radius > 0:
            glow_surface = font_obj.render(text, True, glow_color)
            glow_rect = glow_surface.get_rect(center=(x + dx, y + dy))
            surface.blit(glow_surface, glow_rect)
    if shadow_offset > 0:
        shadow_surface = font_obj.render(text, True, shadow_color)
        shadow_rect = shadow_surface.get_rect(center=(x + shadow_offset, y + shadow_offset))
        surface.blit(shadow_surface, shadow_rect)
    text_surface = font_obj.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, text_rect)

def draw_ribbon_button(surface, rect, button_color, is_hovered, is_pressed):
    offset_x = PRESS_OFFSET if is_pressed else 0
    offset_y = PRESS_OFFSET if is_pressed else 0
    button_rect = rect.move(offset_x, offset_y)
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    current_color = button_color
    if is_hovered:
        r, g, b = current_color
        current_color = (max(0, r - 30), max(0, g - 30), max(0, b - 30))
    current_color_rgba = list(current_color)
    if len(current_color_rgba) == 3: 
        current_color_rgba.append(220) 
    radius = button_rect.height // 2 
    if radius > 0: 
        pygame.draw.rect(s, current_color_rgba, (radius, 0, button_rect.width - 2 * radius, button_rect.height))
        pygame.draw.circle(s, current_color_rgba, (radius, button_rect.height // 2), radius)
        pygame.draw.circle(s, current_color_rgba, (button_rect.width - radius, button_rect.height // 2), radius)
        border_thickness = 3 if is_hovered else 2
        border_color = (255, 255, 255)
        pygame.draw.line(s, border_color, (radius, 0), (button_rect.width - radius, 0), border_thickness)
        pygame.draw.line(s, border_color, (radius, button_rect.height - border_thickness), (button_rect.width - radius, button_rect.height - border_thickness), border_thickness)
        pygame.draw.arc(s, border_color, (0, 0, button_rect.height, button_rect.height), math.pi / 2, math.pi * 3 / 2, border_thickness)
        pygame.draw.arc(s, border_color, (button_rect.width - button_rect.height, 0, button_rect.height, button_rect.height), math.pi * 3 / 2, math.pi * 5 / 2, border_thickness)
    surface.blit(s, (button_rect.x, button_rect.y))
    return offset_x, offset_y

# --- HÀM VẼ CHÍNH CHO MAIN MENU ---
def draw_main_menu(mouse_pos, mouse_buttons):
    """Vẽ toàn bộ màn hình Main Menu."""
    global button_rects
    if MENU_BACKGROUND_IMAGE:
        screen.blit(MENU_BACKGROUND_IMAGE, (0, 0))
    else:
        screen.fill((50, 50, 50)) 
    title_y = START_Y - TITLE_BUTTON_GAP - TITLE_FONT_SIZE // 2
    draw_glow_shadow_text(
        screen, TITLE_TEXT, CX, title_y, 
        TITLE_MAIN_COLOR, TITLE_GLOW_COLOR, TITLE_SHADOW_COLOR, GLOW_RADIUS, SHADOW_OFFSET, MENU_TITLE_FONT
    ) 
    button_rects = [] 
    current_y = START_Y
    for i, button_data in enumerate(BUTTON_DATA):
        name = button_data["name"]
        main_color = button_data["main_color"]
        shadow_color = button_data["shadow_color"]
        rect = pygame.Rect(CX - BUTTON_WIDTH // 2, current_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        button_rects.append(rect)
        is_hovered = rect.collidepoint(mouse_pos)
        is_pressed = is_hovered and mouse_buttons[0]
        
        offset_x, offset_y = draw_ribbon_button(screen, rect, main_color, is_hovered, is_pressed)
        
        text_center_x = rect.centerx + offset_x
        text_center_y = rect.centery + offset_y 
        draw_shadow_text(
            screen, name, text_center_x, text_center_y, 
            (255, 255, 255), shadow_color, SHADOW_OFFSET, MENU_BUTTON_FONT
        )
        current_y += BUTTON_HEIGHT + BUTTON_SPACING

# =================================================================
# === [5] GIAO DIỆN: ABOUT US (TRANG 1 & 2) ===
# =================================================================

# --- CẤU HÌNH RIÊNG BIỆT CHO ABOUT US 1 ---
AU1_CONTENT_RAW_VI = [
    "School: FPT University", "Class: AI2002 ", "Subject: CSD203",
    "Implementation Team: by Group 4", "Mentor: Võ Hồng Khanh",
]
AU1_CONFIG = {
    "TITLE_TEXT": "ABOUT US", "BASE_TITLE_FONT_SIZE": 50, "BASE_CONTENT_FONT_SIZE": 26,
    "TITLE_FONT_SIZE": 0, "CONTENT_FONT_SIZE": 0, "TITLE_COLOR": (255, 255, 255),    
    "CONTENT_COLOR": (255, 255, 255), "BG_COLOR": (20, 20, 40), "BUTTON_COLOR": (0, 150, 0),      
    "FONT_INDEX": 0, "CONTENT_DATA": AU1_CONTENT_RAW_VI, "BASE_BOX_WIDTH": 700,
    "BASE_BOX_Y_START": 180, "BOX_WIDTH": 0, "BOX_Y_START": 0
}

# --- CẤU HÌNH RIÊNG BIỆT CHO ABOUT US 2 ---
AU2_CONFIG = {
    "TITLE_TEXT": "ABOUT US", "BASE_TITLE_FONT_SIZE": 50, "BASE_CONTENT_FONT_SIZE": 25,
    "TITLE_FONT_SIZE": 0, "CONTENT_FONT_SIZE": 0, "TITLE_COLOR": (255, 255, 255),  
    "CONTENT_COLOR": (255, 180, 0), "BG_COLOR": (30, 30, 30), "BUTTON_COLOR": (150, 0, 0),     
    "FRAME_COLOR": (255, 0, 100), "FONT_INDEX": 0, 
    "MENTOR": {
        "name_line1": "MENTOR", 
        "name_line2": "VÕ HỒNG KHANH", 
        "subject": "SUBJECT: CSD203", "image_file": "Thầy_Khanh.png"
    },
    "MEMBERS": [
        {"name_line1": "Nguyễn Phước Xiêm", "name_line2": "(Leader)", "code": "CE190249", "image_file": "Xiêm.png"},
        {"name_line1": "Hồ Vĩnh Hưng", "name_line2": "", "code": "CE202073", "image_file": "Hưng.png"}, 
        {"name_line1": "Nguyễn Trường Thịnh", "name_line2": "(Secretary)", "code": "CE202010", "image_file": "Thịnh.png"},
        {"name_line1": "Lâm Thiên Bảo", "name_line2": "", "code": "CE201661", "image_file": "Bảo.png"},
    ]
}

# --- HẰNG SỐ CHUNG CHO ABOUT US ---
BASE_AU_BUTTON_W, BASE_AU_BUTTON_H = 220, 50
BASE_AU_BUTTON_FONT_SIZE = 28
BASE_LINE_SPACING_AU1 = 40
BASE_STAGGER_OFFSET = 50 
AU_BUTTON_W, AU_BUTTON_H = 0, 0
AU_BUTTON_FONT_SIZE = 0
AU_BUTTON_SHADOW_COLOR = (0, 0, 0)
LINE_SPACING_AU1 = 0
TEXT_GAP_AU2 = 0     
STAGGER_OFFSET = 0 
g_nav_btn_w, g_nav_btn_h = 0, 0
BASE_NAV_BUTTON_H = 50 

# --- HÀM VẼ HELPER CHO ABOUT US ---
def draw_fpt_logo(surface):
    logo_x = scale_w(20)
    logo_y = scale_h(20)
    if LOGO_IMAGE:
        surface.blit(LOGO_IMAGE, (logo_x, logo_y))
    else:
        logo_font = load_font(scale_font(18), bold=True) 
        draw_text(surface, "FPT Education", logo_x, logo_y, logo_font, (255, 255, 255), center=False)
        draw_text(surface, "FPT UNIVERSITY", logo_x, logo_y + scale_h(25), logo_font, (255, 180, 0), center=False)

def load_and_resize_image(file_name, target_size):
    if file_name in MEMBER_IMAGE_CACHE:
        return MEMBER_IMAGE_CACHE[file_name]
    try:
        img = pygame.image.load(file_name).convert_alpha()
        img = pygame.transform.scale(img, (target_size, target_size))
        MEMBER_IMAGE_CACHE[file_name] = img
        return img
    except pygame.error as e:
        print(f"Cảnh báo: Không thể tải ảnh {file_name}. Dùng hình tròn placeholder.")
        return None

def draw_circular_image_and_frame(surface, img_obj, center_x, center_y, radius, frame_color, text_content, text_font):
    if radius <= 0: return 
    scaled_border = max(1, scale_font(3))
    scaled_padding = max(2, scale_font(5))
    temp_surf_size = (radius + scaled_padding) * 2
    temp_surf = pygame.Surface((temp_surf_size, temp_surf_size), pygame.SRCALPHA)
    temp_rect = temp_surf.get_rect(center=(center_x, center_y))
    center_p = radius + scaled_padding
    pygame.draw.circle(temp_surf, (0, 0, 0, 150), (center_p, center_p), radius + max(1, scale_font(2)))
    clip_mask = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(clip_mask, (255, 255, 255), (radius, radius), radius)
    if img_obj:
        try:
            img_copy = pygame.transform.scale(img_obj, (radius*2, radius*2))
            img_copy.blit(clip_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN) 
            temp_surf.blit(img_copy, (scaled_padding, scaled_padding))
        except:
             pygame.draw.circle(temp_surf, (80, 80, 80), (center_p, center_p), radius)
    else:
        pygame.draw.circle(temp_surf, (80, 80, 80), (center_p, center_p), radius)
        if text_content and text_font:
            initials = text_content[0]
            text_surf = text_font.render(initials, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(center_p, center_p))
            temp_surf.blit(text_surf, text_rect)
    pygame.draw.circle(temp_surf, frame_color, (center_p, center_p), radius + max(1, scale_font(1)), scaled_border)
    surface.blit(temp_surf, temp_rect)

def draw_simple_button(surface, rect, text, font_obj, button_color, text_color, is_hovered, is_pressed):
    offset_x = PRESS_OFFSET if is_pressed else 0
    offset_y = PRESS_OFFSET if is_pressed else 0
    button_rect = rect.move(offset_x, offset_y)
    current_color = list(button_color)
    if len(current_color) == 3: 
        current_color.append(255) 
    if is_hovered:
        r, g, b, a = current_color
        current_color = (max(0, r - 50), max(0, g - 50), max(0, b - 50), a)
    border_radius = scale_font(8)
    pygame.draw.rect(surface, current_color, button_rect, border_radius=border_radius)
    pygame.draw.rect(surface, (255, 255, 255), button_rect, max(1, scale_font(2)), border_radius=border_radius)
    text_x = button_rect.centerx
    text_y = button_rect.centery
    draw_shadow_text(surface, text, text_x, text_y, text_color, AU_BUTTON_SHADOW_COLOR, max(1, scale_font(1)), font_obj)

def draw_image_button(surface, rect, img, is_hovered, is_pressed):
    """Vẽ nút bấm bằng hình ảnh (dùng cho Next/Prev)."""
    offset_x = PRESS_OFFSET if is_pressed else 0
    offset_y = PRESS_OFFSET if is_pressed else 0
    button_rect = rect.move(offset_x, offset_y)
    
    if img:
        surface.blit(img, button_rect)
        if is_hovered:
            hover_surface = pygame.Surface(button_rect.size, pygame.SRCALPHA)
            hover_surface.fill((0, 0, 0, 80))
            surface.blit(hover_surface, button_rect.topleft)
        if is_pressed:
            pressed_surface = pygame.Surface(button_rect.size, pygame.SRCALPHA)
            pressed_surface.fill((0, 0, 0, 50))
            surface.blit(pressed_surface, button_rect.topleft)
            
    else:
        draw_simple_button(surface, rect, "IMG_ERR", AU1_BUTTON_FONT, (255,0,0), (255,255,255), is_hovered, is_pressed)

# --- HÀM VẼ CHÍNH CHO ABOUT US ---
def draw_about_us_screen(state, config, current_mouse_pos, mouse_buttons, next_state=None):
    """Hàm vẽ chung cho cả 2 màn hình About Us (AU1 và AU2)."""
    if AU_BACKGROUND_IMAGE:
        screen.blit(AU_BACKGROUND_IMAGE, (0, 0))
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150)) 
        screen.blit(overlay, (0, 0))
    else:
        screen.fill(config["BG_COLOR"])
    draw_fpt_logo(screen) 
    title_font = load_font(config["TITLE_FONT_SIZE"], bold=True, preferred_font_index=config["FONT_INDEX"])
    title_x = CX
    title_y = scale_h(100)
    title_center = True
    if state == ABOUT_US_2: 
        title_x = CX 
        title_y = scale_h(45)
        title_center = True 
    draw_text(screen, config["TITLE_TEXT"], title_x, title_y, title_font, config["TITLE_COLOR"], center=title_center)
    if state == ABOUT_US_1:
        content_font = AU1_CONTENT_FONT
        BLOCK_WIDTH = config["BOX_WIDTH"]
        text_height = len(config["CONTENT_DATA"]) * LINE_SPACING_AU1
        box_padding = scale_font(25)
        box_y = config["BOX_Y_START"]
        box_x = CX - BLOCK_WIDTH // 2 - box_padding
        box_w = BLOCK_WIDTH + box_padding * 2
        box_h = text_height + box_padding * 2 + scale_h(30)
        box_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_surface.fill((0, 0, 0, 160)) 
        border_radius = scale_font(10)
        pygame.draw.rect(box_surface, (255, 255, 255), box_surface.get_rect(), max(1, scale_font(2)), border_radius=border_radius) 
        screen.blit(box_surface, (box_x, box_y))
        current_y = box_y + box_padding
        START_X_CONTENT = CX - BLOCK_WIDTH // 2 
        for line in config["CONTENT_DATA"]:
            draw_text(screen, line, START_X_CONTENT, current_y, content_font, config["CONTENT_COLOR"], center=False) 
            current_y += LINE_SPACING_AU1
    elif state == ABOUT_US_2:
        member_font_small = AU2_CONTENT_FONT
        member_font_large = load_font(config["CONTENT_FONT_SIZE"], bold=True, preferred_font_index=config["FONT_INDEX"])
        
        MENTOR_X = scale_w(150) 
        MENTOR_RADIUS = scale_font(85) 
        MEMBER_RADIUS = scale_font(50) 
        
        TEXT_GAP = TEXT_GAP_AU2 
        FRAME_COLOR = config["FRAME_COLOR"] 
        
        # A. VẼ MENTOR
        mentor_config = config["MENTOR"]
        mentor_img = load_and_resize_image(mentor_config["image_file"], MENTOR_RADIUS * 2)
        mentor_y = scale_h(250) 
        draw_circular_image_and_frame(screen, mentor_img, MENTOR_X, mentor_y, MENTOR_RADIUS, (255, 215, 0), "KH", member_font_large)
        
        text_y_start = mentor_y + MENTOR_RADIUS + scale_h(30)
        
        draw_text(screen, mentor_config["name_line1"], MENTOR_X, text_y_start, 
                  member_font_large, (255, 255, 255), center=True) 
                  
        text_y_start += member_font_large.get_height() - scale_h(-5)
        draw_text(screen, mentor_config["name_line2"], MENTOR_X, text_y_start, 
                  member_font_large, (255, 255, 255), center=True) 
                  
        text_y_start += member_font_large.get_height() + scale_h(10) 
        draw_text(screen, mentor_config["subject"], MENTOR_X, text_y_start, 
                  member_font_small, config["CONTENT_COLOR"], center=True) 
        
        # B. VẼ MEMBERS (Layout So le)
        MEMBER_START_Y = scale_h(150)
        MEMBER_Y_SPACING = scale_h(210) 
        X_LEFT_COL = CX + scale_w(20)
        X_RIGHT_COL = CX + scale_w(260)
        
        x_positions = [X_LEFT_COL, X_RIGHT_COL]
        
        for i, member in enumerate(config["MEMBERS"]):
            col = i % 2
            row = i // 2
            
            mx = x_positions[col]
            my = MEMBER_START_Y + row * MEMBER_Y_SPACING
            
            #if col == 1: 
                #my -= STAGGER_OFFSET 
                
            member_img = load_and_resize_image(member["image_file"], MEMBER_RADIUS * 2) 
            draw_circular_image_and_frame(screen, member_img, mx, my, MEMBER_RADIUS, FRAME_COLOR, member["name_line1"][0], member_font_small)

            text_y_member = my + MEMBER_RADIUS + scale_h(15)
            draw_text(screen, member["name_line1"], mx, text_y_member, 
                      member_font_small, (255, 255, 255), center=True) 
            
            if member["name_line2"]: 
                text_y_member += member_font_small.get_height() - scale_h(5)
                draw_text(screen, member["name_line2"], mx, text_y_member, 
                          member_font_small, (200, 200, 200), center=True) 
            
            text_y_member += member_font_small.get_height() + TEXT_GAP 
            draw_text(screen, member["code"], mx, text_y_member, 
                      member_font_small, config["CONTENT_COLOR"], center=True) 

    # --- Vẽ Nút điều hướng (Next/Prev/Back) ---
    text_btn_w, text_btn_h = scale_w(BASE_AU_BUTTON_W), scale_h(BASE_AU_BUTTON_H)
    img_btn_w, img_btn_h = g_nav_btn_w, g_nav_btn_h 
    
    BOTTOM_POS_Y = SCREEN_H - img_btn_h - scale_h(30) 
    LEFT_POS = scale_w(50)
    RIGHT_POS = SCREEN_W - scale_w(50) 
    
    left_rect_text = pygame.Rect(LEFT_POS, BOTTOM_POS_Y, text_btn_w, text_btn_h)
    left_rect_img = pygame.Rect(LEFT_POS, BOTTOM_POS_Y, img_btn_w, img_btn_h)
    right_rect_text = pygame.Rect(RIGHT_POS - text_btn_w, BOTTOM_POS_Y, text_btn_w, text_btn_h)
    right_rect_img = pygame.Rect(RIGHT_POS - img_btn_w, BOTTOM_POS_Y, img_btn_w, img_btn_h)

    left_hovered = False
    left_pressed = False
    right_hovered = False
    right_pressed = False

    if state == ABOUT_US_1:
        left_hovered = left_rect_text.collidepoint(current_mouse_pos)
        left_pressed = left_hovered and mouse_buttons[0]
        right_hovered = right_rect_img.collidepoint(current_mouse_pos)
        right_pressed = right_hovered and mouse_buttons[0]
        # Nút trái: Back to Menu (Text)
        draw_simple_button(screen, left_rect_text, "Back to Menu", AU1_BUTTON_FONT, config["BUTTON_COLOR"], (255, 255, 255), left_hovered, left_pressed)
        # Nút phải: Next (Image)
        draw_image_button(screen, right_rect_img, g_next_button_img, right_hovered, right_pressed)
        
    elif state == ABOUT_US_2:
        left_hovered = left_rect_img.collidepoint(current_mouse_pos)
        left_pressed = left_hovered and mouse_buttons[0]
        right_hovered = right_rect_text.collidepoint(current_mouse_pos)
        right_pressed = right_hovered and mouse_buttons[0]
        # Nút trái: Prev (Image)
        draw_image_button(screen, left_rect_img, g_prev_button_img, left_hovered, left_pressed)
        # Nút phải: Back to Menu (Text)
        draw_simple_button(screen, right_rect_text, "Back to Menu", AU1_BUTTON_FONT, config["BUTTON_COLOR"], (255, 255, 255), right_hovered, right_pressed)
        
# =================================================================
# === [6] GIAO DIỆN: SELECT LEVEL ===
# =================================================================

# --- Biến toàn cục/Rects cho Select Level ---
level_button_rects = [] 
LEVEL_BUTTON_DATA = ["Easy", "Normal", "Hard", "Expert", "Back to Menu"] 

# --- HÀM VẼ CHÍNH CHO SELECT LEVEL ---
def draw_select_level(mouse_pos, mouse_buttons):
    """Vẽ màn hình chọn 5 nút level (đã căn chỉnh)."""
    global level_button_rects
    level_button_rects = [] 

    if BACKGROUND_LEVEL_SELECT_IMAGE:
        screen.blit(BACKGROUND_LEVEL_SELECT_IMAGE, (0, 0))
    else:
        screen.fill((20, 20, 50)) 

    title_y = scale_h(120) 
    draw_glow_shadow_text(screen, "SELECT DIFFICULTY", CX, title_y,
                        TITLE_MAIN_COLOR, TITLE_GLOW_COLOR, TITLE_SHADOW_COLOR,
                        GLOW_RADIUS, SHADOW_OFFSET, MENU_TITLE_FONT)

    btn_w, btn_h = scale_w(280), scale_h(60)
    btn_spacing = scale_h(25) 
    btn_font = MENU_BUTTON_FONT 
    total_button_height = (5 * btn_h) + (4 * btn_spacing)
    space_top = title_y + scale_h(60) 
    space_bottom = SCREEN_H - scale_h(40) 
    available_height = space_bottom - space_top
    start_y = space_top + (available_height // 2) - (total_button_height // 2)

    for i, text in enumerate(LEVEL_BUTTON_DATA):
        rect = pygame.Rect(CX - btn_w // 2, int(start_y + i * (btn_h + btn_spacing)), btn_w, btn_h)
        level_button_rects.append(rect)
        is_hovered = rect.collidepoint(mouse_pos)
        is_pressed = is_hovered and mouse_buttons[0]
        color = (0, 150, 0) 
        if text == "Hard": color = (200, 100, 0) 
        elif text == "Expert": color = (180, 0, 0) 
        elif text == "Back to Menu": color = (80, 80, 80) 
        draw_simple_button(screen, rect, text, btn_font, color, (255, 255, 255), is_hovered, is_pressed)

# =================================================================
# === [7] GIAO DIỆN: HOW TO PLAY (6 TRANG) ===
# =================================================================

# --- Biến toàn cục/Rects cho How To Play ---
g_htp_left_button_rect = pygame.Rect(0,0,0,0)
g_htp_right_button_rect = pygame.Rect(0,0,0,0)

# --- HÀM VẼ CHÍNH CHO HOW TO PLAY ---
def draw_how_to_play_screen(state, mouse_pos, mouse_buttons):
    """(SỬA) Vẽ màn hình hướng dẫn chơi (6 trang)."""
    
    # 1. Vẽ nền
    if BACKGROUND_LEVEL_SELECT_IMAGE:
        screen.blit(BACKGROUND_LEVEL_SELECT_IMAGE, (0, 0))
    else:
        screen.fill((20, 20, 50)) 

    # 2. Vẽ tiêu đề
    title_y = scale_h(100)
    draw_glow_shadow_text(screen, "HOW TO PLAY", CX, title_y,
                        TITLE_MAIN_COLOR, TITLE_GLOW_COLOR, TITLE_SHADOW_COLOR,
                        GLOW_RADIUS, SHADOW_OFFSET, MENU_TITLE_FONT)
                        
    # 3. Tính toán vị trí chung

    text_y_new = title_y + scale_h(80) 
    img_y_new = text_y_new + scale_h(180) 
    
    # Vị trí cho bố cục chỉ Image
    box_w = scale_w(700)
    box_h = scale_h(350)
    box_x = CX - box_w // 2
    box_y = title_y + scale_h(70)
    box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
    img_center_y_full = box_rect.centery
    
    page_text = ""
    image_to_draw_new = None
    text_to_draw_new = ""

    # 4. Vẽ nội dung dựa trên state
    if state == HOW_TO_PLAY_1:
        page_text = "Page 1 / 6"
        text_to_draw_new = "Left click to open the box"
        image_to_draw_new = HOW_TO_PLAY_NEW_IMG_1
        img_y_new = text_y_new + scale_h(180) 
        
        if not image_to_draw_new:
             draw_text(screen, "Không tìm thấy 'Howtoplay1.png'", CX, img_y_new, HTP_CONTENT_FONT, (255,0,0), center=True)
                
    elif state == HOW_TO_PLAY_2:
        page_text = "Page 2 / 6"
        text_to_draw_new = "Right click to place the flag"
        image_to_draw_new = HOW_TO_PLAY_NEW_IMG_2
        if not image_to_draw_new:
             draw_text(screen, "Không tìm thấy 'Howtoplay2.png'", CX, img_y_new, HTP_CONTENT_FONT, (255,0,0), center=True)
                     
    elif state == HOW_TO_PLAY_3:
        page_text = "Page 3 / 6"
        text_to_draw_new = "Win by opening all the empty boxes"
        image_to_draw_new = HOW_TO_PLAY_NEW_IMG_3
        if not image_to_draw_new:
             draw_text(screen, "Không tìm thấy 'Howtoplay3.png'", CX, img_y_new, HTP_CONTENT_FONT, (255,0,0), center=True)

    # Vẽ Text và Image cho trang 1, 2, 3
    if state in [HOW_TO_PLAY_1, HOW_TO_PLAY_2, HOW_TO_PLAY_3]:
        
        # VẼ ẢNH TRƯỚC
        if image_to_draw_new:
            img_rect = image_to_draw_new.get_rect(center=(CX, img_y_new))
            screen.blit(image_to_draw_new, img_rect)
            
        # VẼ TEXT SAU
        if HTP_CONTENT_FONT:
            draw_text(screen, text_to_draw_new, CX, text_y_new, HTP_CONTENT_FONT, (0, 0, 0), center=True)
    
    # Logic cho các trang còn lại
    elif state == HOW_TO_PLAY_4:
        page_text = "Page 4 / 6"
        if HOW_TO_PLAY_IMG_1:
            img_rect = HOW_TO_PLAY_IMG_1.get_rect(center=(CX, img_center_y_full))
            screen.blit(HOW_TO_PLAY_IMG_1, img_rect)
        else:
            draw_text(screen, "Không tìm thấy ảnh 'cách chơi 1.png'", CX, img_center_y_full, HTP_CONTENT_FONT, (255,0,0), center=True)
                    
    elif state == HOW_TO_PLAY_5:
        page_text = "Page 5 / 6"
        if HOW_TO_PLAY_IMG_2:
            img_rect = HOW_TO_PLAY_IMG_2.get_rect(center=(CX, img_center_y_full))
            screen.blit(HOW_TO_PLAY_IMG_2, img_rect)
        else:
            draw_text(screen, "Không tìm thấy ảnh 'cách chơi 2.png'", CX, img_center_y_full, HTP_CONTENT_FONT, (255,0,0), center=True)
            
    elif state == HOW_TO_PLAY_6:
        page_text = "Page 6 / 6"
        if HOW_TO_PLAY_IMG_3:
            img_rect = HOW_TO_PLAY_IMG_3.get_rect(center=(CX, img_center_y_full))
            screen.blit(HOW_TO_PLAY_IMG_3, img_rect)
        else:
            draw_text(screen, "Không tìm thấy ảnh 'cách chơi 3.png'", CX, img_center_y_full, HTP_CONTENT_FONT, (255,0,0), center=True)

    # 5. Vẽ nút điều hướng
    text_btn_w, text_btn_h = scale_w(BASE_AU_BUTTON_W), scale_h(BASE_AU_BUTTON_H)
    img_btn_w, img_btn_h = g_nav_btn_w, g_nav_btn_h
    
    btn_y = SCREEN_H - img_btn_h - scale_h(30)
    
    left_pos_x = scale_w(50)
    right_pos_x = SCREEN_W - scale_w(50) 
    
    global g_htp_left_button_rect, g_htp_right_button_rect
    
    page_num_y = btn_y - scale_h(-33) 
    if HTP_PAGE_NUM_FONT:
        draw_text(screen, page_text, CX, page_num_y, HTP_PAGE_NUM_FONT, (255, 255, 255), center=True)
    
    if state == HOW_TO_PLAY_1:
        # Nút trái: Back to Menu (Text)
        g_htp_left_button_rect = pygame.Rect(left_pos_x-30, btn_y, text_btn_w, text_btn_h)
        left_hovered = g_htp_left_button_rect.collidepoint(mouse_pos)
        left_pressed = left_hovered and mouse_buttons[0]
        draw_simple_button(screen, g_htp_left_button_rect, "Back to Menu", AU1_BUTTON_FONT, (80, 80, 80), (255, 255, 255), left_hovered, left_pressed)
        
        # Nút phải: Next (Image)
        g_htp_right_button_rect = pygame.Rect(right_pos_x - img_btn_w, btn_y, img_btn_w, img_btn_h)
        right_hovered = g_htp_right_button_rect.collidepoint(mouse_pos)
        right_pressed = right_hovered and mouse_buttons[0]
        draw_image_button(screen, g_htp_right_button_rect, g_next_button_img, right_hovered, right_pressed)
        
    elif state in [HOW_TO_PLAY_2, HOW_TO_PLAY_3, HOW_TO_PLAY_4, HOW_TO_PLAY_5]:
        # Nút trái: Prev (Image)
        g_htp_left_button_rect = pygame.Rect(left_pos_x, btn_y, img_btn_w, img_btn_h)
        left_hovered = g_htp_left_button_rect.collidepoint(mouse_pos)
        left_pressed = left_hovered and mouse_buttons[0]
        draw_image_button(screen, g_htp_left_button_rect, g_prev_button_img, left_hovered, left_pressed)
        
        # Nút phải: Next (Image)
        g_htp_right_button_rect = pygame.Rect(right_pos_x - img_btn_w, btn_y, img_btn_w, img_btn_h)
        right_hovered = g_htp_right_button_rect.collidepoint(mouse_pos)
        right_pressed = right_hovered and mouse_buttons[0]
        draw_image_button(screen, g_htp_right_button_rect, g_next_button_img, right_hovered, right_pressed)
        
    elif state == HOW_TO_PLAY_6:
        # Nút trái: Prev (Image)
        g_htp_left_button_rect = pygame.Rect(left_pos_x, btn_y, img_btn_w, img_btn_h)
        left_hovered = g_htp_left_button_rect.collidepoint(mouse_pos)
        left_pressed = left_hovered and mouse_buttons[0]
        draw_image_button(screen, g_htp_left_button_rect, g_prev_button_img, left_hovered, left_pressed)
        
        # Nút phải: Back to Menu (Text)
        g_htp_right_button_rect = pygame.Rect(right_pos_x - text_btn_w +35, btn_y, text_btn_w, text_btn_h)
        right_hovered = g_htp_right_button_rect.collidepoint(mouse_pos)
        right_pressed = right_hovered and mouse_buttons[0]
        draw_simple_button(screen, g_htp_right_button_rect, "Back to Menu", AU1_BUTTON_FONT, (0, 150, 0), (255, 255, 255), right_hovered, right_pressed)


# =================================================================
# === [8] GIAO DIỆN: RANKING BOARD ===
# =================================================================

# --- Biến toàn cục/Rects cho Ranking Board ---
g_rb_top_right_back_rect = pygame.Rect(0, 0, 0, 0) 
g_rb_tab_rects = [] 
g_ranking_view = "Easy" 

# --- HÀM VẼ CHÍNH CHO RANKING BOARD ---
def draw_ranking_board(mouse_pos, mouse_buttons):
    """(SỬA) Vẽ màn hình bảng xếp hạng với 4 tab (Layout mới)."""
    global g_ranking_view
    
    # 1. Vẽ nền
    if BACKGROUND_RANKING_IMAGE: 
        screen.blit(BACKGROUND_RANKING_IMAGE, (0, 0))
    elif BACKGROUND_LEVEL_SELECT_IMAGE: 
        screen.blit(BACKGROUND_LEVEL_SELECT_IMAGE, (0, 0))
    else:
        screen.fill((20, 20, 50)) 

    # 2. Vẽ tiêu đề
    title_y = scale_h(90)
    draw_glow_shadow_text(screen, "RANKING BOARD", CX, title_y,
                        TITLE_MAIN_COLOR, TITLE_GLOW_COLOR, TITLE_SHADOW_COLOR,
                        GLOW_RADIUS, SHADOW_OFFSET, RB_MAIN_TITLE_FONT)
    
    # 2b. Vẽ logo và nút Back
    draw_fpt_logo(screen)
    btn_hover = g_rb_top_right_back_rect.collidepoint(mouse_pos)
    btn_pressed = btn_hover and mouse_buttons[0]
    draw_simple_button(screen, g_rb_top_right_back_rect, "< Back", GAME_UI_BUTTON_FONT, (80, 80, 80), (255, 255, 255), btn_hover, btn_pressed)
                        
    # 3. Tải điểm
    rankings = load_rankings()
    
    # 4. Vẽ 4 nút Tab
    diff_names = ["Easy", "Normal", "Hard", "Expert"]
    colors = {
        "Easy": (0, 200, 0), "Normal": (0, 150, 150),
        "Hard": (255, 180, 0), "Expert": (200, 0, 0)
    }
    
    for i, rect in enumerate(g_rb_tab_rects):
        name = diff_names[i]
        is_active = (g_ranking_view == name)
        is_hovered = rect.collidepoint(mouse_pos)
        
        color = colors[name]
        if is_active:
            pygame.draw.rect(screen, color, rect, border_top_left_radius=8, border_top_right_radius=8)
            draw_text(screen, name, rect.centerx, rect.centery, RB_TAB_FONT, (255, 255, 255), center=True)
        else:
            dim_color = (max(0, color[0]-70), max(0, color[1]-70), max(0, color[2]-70))
            pygame.draw.rect(screen, dim_color, rect, border_top_left_radius=8, border_top_right_radius=8)
            if is_hovered: 
                pygame.draw.rect(screen, (255,255,255), rect, 2, border_top_left_radius=8, border_top_right_radius=8)
            draw_text(screen, name, rect.centerx, rect.centery, RB_TAB_FONT, (180, 180, 180), center=True)

    # 5. Vẽ Bảng
    table_y_start = g_rb_tab_rects[0].bottom 
    table_rect = pygame.Rect(g_rb_tab_rects[0].left, table_y_start, 
                             g_rb_tab_rects[-1].right - g_rb_tab_rects[0].left,
                             SCREEN_H - table_y_start - scale_h(20)) 
    
    pygame.draw.rect(screen, (0, 0, 0, 150), table_rect) 
    pygame.draw.rect(screen, (255, 255, 255), table_rect, 2) 

    header_y = table_y_start + scale_h(25)
    rank_x = table_rect.left + scale_w(80)
    name_x = table_rect.centerx
    time_x = table_rect.right - scale_w(100)
    
    draw_text(screen, "Rank", rank_x, header_y, RB_TITLE_FONT, (255, 215, 0), center=True)
    draw_text(screen, "Name", name_x, header_y, RB_TITLE_FONT, (255, 215, 0), center=True)
    draw_text(screen, "Time", time_x, header_y, RB_TITLE_FONT, (255, 215, 0), center=True)
    
    # 6. Vẽ 10 điểm
    scores = rankings.get(g_ranking_view, [])
    
    score_y_start = header_y + scale_h(40)
    available_table_height = table_rect.height - scale_h(50) 
    line_height = available_table_height // 10

    for j in range(10): # Top 10
        current_y = score_y_start + j * line_height
        rank_text = f"{j+1}."
        draw_text(screen, rank_text, rank_x, current_y, RB_SCORE_FONT, (255, 255, 255), center=True)

        if j < len(scores):
            entry = scores[j]
            name_text = str(entry['name'])[:15] # Cắt tên tối đa 15 ký tự
            draw_text(screen, name_text, name_x, current_y, RB_SCORE_FONT, (255, 255, 255), center=True)
            draw_text(screen, f"{entry['time']:.2f} s", time_x, current_y, RB_SCORE_FONT, (255, 255, 255), center=True)
        else:
            draw_text(screen, "---", name_x, current_y, RB_SCORE_FONT, (150, 150, 150), center=True)
            draw_text(screen, "-.-- s", time_x, current_y, RB_SCORE_FONT, (150, 150, 150), center=True)

# =================================================================
# === [9] GIAO DIỆN: GAME PLAY (LOGIC & DRAW) ===
# =================================================================

# --- CẤU HÌNH VÀ BIẾN TOÀN CỤC CHO GAME PLAY ---
GAME_ROWS = 20
GAME_COLS = 20
GAME_MINES = 40 
BASE_GAME_CELL_SIZE = 25 
g_scaled_cell_size = BASE_GAME_CELL_SIZE 

g_mine_locations = set() 
g_number_board = []      
g_game_board = []        
g_game_state = 'playing'
g_board_rect = pygame.Rect(0, 0, 0, 0) 
g_home_button_rect = pygame.Rect(0, 0, 0, 0)    
g_restart_button_rect = pygame.Rect(0, 0, 0, 0) 
g_name_input_box_rect = pygame.Rect(0, 0, 0, 0) 

g_lose_restart_rect = pygame.Rect(0,0,0,0)
g_lose_menu_rect = pygame.Rect(0,0,0,0)
g_win_restart_rect = pygame.Rect(0,0,0,0)
g_win_next_rect = pygame.Rect(0,0,0,0)
g_win_menu_rect = pygame.Rect(0,0,0,0)

g_game_start_time = 0
g_game_elapsed_time = 0.0
g_current_difficulty_name = "Expert"
g_player_name_input = "" 
g_confetti_particles = []
g_rain_particles = []

# Thêm 3 biến cho hiệu ứng nổ bom
g_clicked_bomb_pos = None
g_losing_start_time = 0
g_bombs_to_reveal = []

# --- CÁC HÀM HIỆU ỨNG (WIN/LOSE) ---
def create_particles(number, effect_type):
    """Tạo ra các hạt hiệu ứng mới."""
    global g_confetti_particles, g_rain_particles
    
    if effect_type == 'confetti':
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (255, 128, 0)]
        for _ in range(number):
            x = random.uniform(0, SCREEN_W)
            y = random.uniform(-50, 0) 
            vx = random.uniform(-1.5, 1.5) 
            vy = random.uniform(1, 4)      
            color = random.choice(colors)
            radius = random.randint(3, 7)
            g_confetti_particles.append([x, y, vx, vy, color, radius])
            
    elif effect_type == 'rain':
        for _ in range(number):
            x = random.uniform(0, SCREEN_W)
            y = random.uniform(-50, 0)
            vy = random.uniform(7, 12) 
            length = random.randint(15, 30)
            color = (120, 120, 180) 
            g_rain_particles.append([x, y, vy, length, color])

def update_and_draw_particles(surface):
    """Cập nhật vị trí và vẽ tất cả các hạt hiệu ứng."""
    global g_confetti_particles, g_rain_particles
    
    # Cập nhật Hoa giấy
    to_remove = []
    for p in g_confetti_particles:
        p[0] += p[2] # x += vx
        p[1] += p[3] # y += vy
        p[3] += 0.08 # vy += gravity
        pygame.draw.circle(surface, p[4], (int(p[0]), int(p[1])), p[5])
        if p[1] > SCREEN_H: 
            to_remove.append(p)
    for p in to_remove:
        g_confetti_particles.remove(p)
        
    # Cập nhật Mưa
    to_remove = []
    for p in g_rain_particles:
        p[1] += p[2] # y += vy
        pygame.draw.line(surface, p[4], (int(p[0]), int(p[1])), (int(p[0]), int(p[1] - p[3])), 2)
        if p[1] > SCREEN_H: 
            to_remove.append(p)
    for p in to_remove:
        g_rain_particles.remove(p)

# --- CÁC HÀM LOGIC CỦA GAME DÒ MÌN ---
def start_new_game():
    """Khởi tạo ván mới VÀ xóa hiệu ứng."""
    global g_mine_locations, g_number_board, g_game_board, g_game_state
    global g_game_start_time, g_game_elapsed_time, g_player_name_input
    global g_confetti_particles, g_rain_particles, g_clicked_bomb_pos, g_losing_start_time, g_bombs_to_reveal
    
    g_mine_locations.clear()
    g_number_board = [[0 for _ in range(GAME_COLS)] for _ in range(GAME_ROWS)]
    g_game_board = [['hidden' for _ in range(GAME_COLS)] for _ in range(GAME_ROWS)]
    g_game_state = 'playing'
    g_player_name_input = "" 
    
    g_game_start_time = pygame.time.get_ticks()
    g_game_elapsed_time = 0.0
    
    g_confetti_particles.clear()
    g_rain_particles.clear()
    
    # Reset biến hiệu ứng nổ
    g_clicked_bomb_pos = None
    g_losing_start_time = 0
    g_bombs_to_reveal = []
    
    while len(g_mine_locations) < GAME_MINES:
        r = random.randint(0, GAME_ROWS - 1)
        c = random.randint(0, GAME_COLS - 1)
        g_mine_locations.add((r, c))
        
    for r in range(GAME_ROWS):
        for c in range(GAME_COLS):
            if (r, c) in g_mine_locations:
                g_number_board[r][c] = -1 
                continue
            count = 0
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if i == 0 and j == 0:
                        continue
                    nr, nc = r + i, c + j
                    if 0 <= nr < GAME_ROWS and 0 <= nc < GAME_COLS and (nr, nc) in g_mine_locations:
                        count += 1
            g_number_board[r][c] = count

def reveal_cell(r, c):
    """Mở một ô (r, c). Đây là hàm đệ quy."""
    global g_game_state
    if not (0 <= r < GAME_ROWS and 0 <= c < GAME_COLS):
        return
    if g_game_board[r][c] == 'revealed' or g_game_board[r][c] == 'flagged':
        return
    g_game_board[r][c] = 'revealed'
    
    if (r, c) in g_mine_locations:
        g_game_state = 'losing' 
        play_music('lost.mp3', 0) 
        
        # Lưu lại thông tin cho hiệu ứng
        global g_clicked_bomb_pos, g_losing_start_time, g_bombs_to_reveal
        g_clicked_bomb_pos = (r, c)
        g_losing_start_time = pygame.time.get_ticks()
        
        # Lấy danh sách các bom CÒN LẠI
        g_bombs_to_reveal = list(g_mine_locations - {(r, c)})
        random.shuffle(g_bombs_to_reveal)
        return
        
    if g_number_board[r][c] == 0:
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                reveal_cell(r + i, c + j)
    check_win_condition()

def toggle_flag(r, c):
    """Cắm/gỡ cờ tại ô (r, c)."""
    if not (0 <= r < GAME_ROWS and 0 <= c < GAME_COLS):
        return
    if g_game_board[r][c] == 'hidden':
        g_game_board[r][c] = 'flagged'
    elif g_game_board[r][c] == 'flagged':
        g_game_board[r][c] = 'hidden'

def check_win_condition():
    """Kiểm tra thắng và chuyển sang state 'entering_name'."""
    global g_game_state, g_player_name_input
    if g_game_state != 'playing':
        return
    opened_cells = 0
    for r in range(GAME_ROWS):
        for c in range(GAME_COLS):
            if g_game_board[r][c] == 'revealed':
                opened_cells += 1
    if opened_cells == (GAME_ROWS * GAME_COLS - GAME_MINES):
        g_game_state = 'entering_name' 
        play_music('Win.mp3', 0)
        g_player_name_input = "" 
        
        for (r, c) in g_mine_locations:
            if g_game_board[r][c] == 'hidden':
                g_game_board[r][c] = 'flagged'

def get_grid_pos(mouse_pos):
    """Chuyển tọa độ chuột (pixel) sang tọa độ ô (row, col)."""
    mx, my = mouse_pos
    if not g_board_rect.collidepoint(mx, my):
        return None
    relative_x = mx - g_board_rect.x
    relative_y = my - g_board_rect.y
    c = relative_x // g_scaled_cell_size
    r = relative_y // g_scaled_cell_size
    if 0 <= r < GAME_ROWS and 0 <= c < GAME_COLS:
        return (r, c)
    return None

# --- HÀM VẼ CHÍNH CHO GAME PLAY ---
def draw_game_play(mouse_pos, mouse_buttons):
    """Vẽ màn hình chơi game (thêm state 'entering_name')."""
    global g_game_elapsed_time, g_game_state
    
    if BACKGROUND_GAME_PLAY_IMAGE:
        screen.blit(BACKGROUND_GAME_PLAY_IMAGE, (0, 0))
    else:
        screen.fill((40, 40, 40)) 
    
    draw_fpt_logo(screen) 
    
    if g_game_state == 'playing':
        home_hover = g_home_button_rect.collidepoint(mouse_pos)
        home_pressed = home_hover and mouse_buttons[0]
        draw_simple_button(screen, g_home_button_rect, "Home", GAME_UI_BUTTON_FONT, (80, 80, 80), (255, 255, 255), home_hover, home_pressed)
        
        restart_hover = g_restart_button_rect.collidepoint(mouse_pos)
        restart_pressed = restart_hover and mouse_buttons[0]
        draw_simple_button(screen, g_restart_button_rect, "Restart", GAME_UI_BUTTON_FONT, (0, 150, 0), (255, 255, 255), restart_hover, restart_pressed)

    if g_game_state == 'playing':
        g_game_elapsed_time = (pygame.time.get_ticks() - g_game_start_time) / 1000.0
    
    if GAME_TIMER_FONT:
        timer_text = f"Time: {g_game_elapsed_time:.1f}"
        timer_x = g_restart_button_rect.left - scale_w(100) 
        timer_y = g_home_button_rect.centery
        draw_text(screen, timer_text, timer_x, timer_y, GAME_TIMER_FONT, (255, 255, 255), center=True)

    if not g_game_images: 
        draw_text(screen, "LỖI TẢI ẢNH GAME!", CX, CY, GAME_OVER_FONT, (255,0,0), center=True)
        return

    # --- LOGIC CHO HIỆU ỨNG 'LOSING' ---
    revealed_bomb_set = set() # Tập hợp các bom sẽ vẽ trong khung hình này
    if g_game_state == 'losing':
        # 1. Luôn hiển thị quả bom đã bấm
        if g_clicked_bomb_pos:
            revealed_bomb_set.add(g_clicked_bomb_pos)
        elapsed_ms = pygame.time.get_ticks() - g_losing_start_time
        

        BOMB_REVEAL_SPEED_MS = 50 
        bombs_to_reveal_count = elapsed_ms // BOMB_REVEAL_SPEED_MS
        
        if bombs_to_reveal_count > 0:
            # Lấy N quả bom đầu tiên trong danh sách đã xáo trộn
            revealed_bomb_set.update(g_bombs_to_reveal[:bombs_to_reveal_count])

        DELAY_AFTER_EXPLOSIONS_MS = 1000
        frames_delay = DELAY_AFTER_EXPLOSIONS_MS // BOMB_REVEAL_SPEED_MS
        
        if bombs_to_reveal_count > len(g_bombs_to_reveal) + frames_delay: 
            g_game_state = 'lost'


    start_x = g_board_rect.x
    start_y = g_board_rect.y
    
    for r in range(GAME_ROWS):
        for c in range(GAME_COLS):
            cell_state = g_game_board[r][c]
            if g_game_state == 'entering_name' and (r,c) in g_mine_locations and cell_state == 'hidden':
                 cell_state = 'flagged' 
            if g_game_state == 'won_options' and (r,c) in g_mine_locations and cell_state == 'hidden':
                 cell_state = 'flagged' 

            cell_rect = pygame.Rect(start_x + c * g_scaled_cell_size,
                                    start_y + r * g_scaled_cell_size,
                                    g_scaled_cell_size, g_scaled_cell_size)
            image_to_draw = None
            if g_game_state == 'lost' and (r,c) in g_mine_locations:
                image_to_draw = g_game_images['boom']
            
            # Vẽ các quả bom đang trong hiệu ứng nổ
            elif g_game_state == 'losing' and (r,c) in revealed_bomb_set: 
                image_to_draw = g_game_images['boom']
            
            elif cell_state == 'hidden':
                image_to_draw = g_game_images['unopened']
            elif cell_state == 'flagged':
                image_to_draw = g_game_images['flag']
            elif cell_state == 'revealed':
                num = g_number_board[r][c]
                image_to_draw = g_game_images[str(num)]
            if image_to_draw:
                screen.blit(image_to_draw, cell_rect)

    # --- Vẽ Lớp phủ (Overlay) cho Win/Lose/EnterName ---
    if g_game_state == 'lost':
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        draw_text(screen, "GAME OVER!", CX, CY - scale_h(100),
                  GAME_OVER_FONT, (255, 0, 0), center=True)
        
        btn_hover_restart = g_lose_restart_rect.collidepoint(mouse_pos)
        btn_pressed_restart = btn_hover_restart and mouse_buttons[0]
        draw_simple_button(screen, g_lose_restart_rect, "Return", MENU_BUTTON_FONT, (0, 150, 0), (255, 255, 255), btn_hover_restart, btn_pressed_restart)
        
        btn_hover_menu = g_lose_menu_rect.collidepoint(mouse_pos)
        btn_pressed_menu = btn_hover_menu and mouse_buttons[0]
        draw_simple_button(screen, g_lose_menu_rect, "Back to Menu", MENU_BUTTON_FONT, (80, 80, 80), (255, 255, 255), btn_hover_menu, btn_pressed_menu)
                  
    elif g_game_state == 'entering_name':
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        draw_text(screen, "YOU WON!", CX, CY - scale_h(100),
                  GAME_OVER_FONT, (0, 255, 0), center=True)
        draw_text(screen, "ENTER YOUR NAME:", CX, CY - scale_h(30),
                  MENU_BUTTON_FONT, (255, 255, 255), center=True)
        
        pygame.draw.rect(screen, (255, 255, 255), g_name_input_box_rect, border_radius=scale_font(8))
        pygame.draw.rect(screen, (0, 0, 0), g_name_input_box_rect, 2, border_radius=scale_font(8))
        
        if NAME_INPUT_FONT:
            text_surface = NAME_INPUT_FONT.render(g_player_name_input, True, (0, 0, 0))
            text_rect = text_surface.get_rect(midleft=(g_name_input_box_rect.x + scale_w(15), g_name_input_box_rect.centery))
            screen.blit(text_surface, text_rect)
            
            if (pygame.time.get_ticks() % 1000 < 500):
                cursor_x = text_rect.right + scale_w(2)
                cursor_y1 = text_rect.top
                cursor_y2 = text_rect.bottom
                pygame.draw.line(screen, (0, 0, 0), (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
        
        draw_text(screen, "Press ENTER to save", CX, CY + scale_h(80),
                  GAME_HELP_FONT, (255, 255, 255), center=True)
                  
    elif g_game_state == 'won_options':
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        draw_text(screen, "YOU WON!", CX, CY - scale_h(150),
                  GAME_OVER_FONT, (0, 255, 0), center=True)
                  
        btn_hover_restart = g_win_restart_rect.collidepoint(mouse_pos)
        btn_pressed_restart = btn_hover_restart and mouse_buttons[0]
        draw_simple_button(screen, g_win_restart_rect, "Return", MENU_BUTTON_FONT, (0, 200, 0), (255, 255, 255), btn_hover_restart, btn_pressed_restart)
        
        btn_hover_next = g_win_next_rect.collidepoint(mouse_pos)
        btn_pressed_next = btn_hover_next and mouse_buttons[0]
        draw_simple_button(screen, g_win_next_rect, "Next Level", MENU_BUTTON_FONT, (0, 150, 150), (255, 255, 255), btn_hover_next, btn_pressed_next)
        
        btn_hover_menu = g_win_menu_rect.collidepoint(mouse_pos)
        btn_pressed_menu = btn_hover_menu and mouse_buttons[0]
        draw_simple_button(screen, g_win_menu_rect, "Back to Menu", MENU_BUTTON_FONT, (80, 80, 80), (255, 255, 255), btn_hover_menu, btn_pressed_menu)

    # --- VẼ HIỆU ỨNG ---
    if g_game_state == 'lost' or g_game_state == 'losing':
        if random.randint(0, 100) < 60: 
            create_particles(5, 'rain')
        update_and_draw_particles(screen) 
    elif g_game_state == 'entering_name' or g_game_state == 'won_options':
        if random.randint(0, 100) < 80: 
            create_particles(10, 'confetti')
        update_and_draw_particles(screen) 

# =================================================================
# === [10] GIAO DIỆN: CONFIRM EXIT ===
# =================================================================

# --- Biến toàn cục/Rects cho Confirm Exit ---
confirm_yes_rect = pygame.Rect(0,0,0,0) 
confirm_no_rect = pygame.Rect(0,0,0,0)  

# --- HÀM VẼ CHÍNH CHO CONFIRM EXIT ---
def draw_confirm_exit(mouse_pos, mouse_buttons):
    """Vẽ hộp thoại xác nhận thoát."""
    global confirm_yes_rect, confirm_no_rect
    fake_mouse_buttons = (0, 0, 0)
    
    # Vẽ lại màn hình trước đó
    if previous_state == MENU:
        draw_main_menu(mouse_pos, fake_mouse_buttons)
    elif previous_state == ABOUT_US_1:
        draw_about_us_screen(ABOUT_US_1, AU1_CONFIG, mouse_pos, fake_mouse_buttons, next_state=ABOUT_US_2)
    elif previous_state == ABOUT_US_2:
        draw_about_us_screen(ABOUT_US_2, AU2_CONFIG, mouse_pos, fake_mouse_buttons)
    elif previous_state == GAME_PLAY:
        draw_game_play(mouse_pos, fake_mouse_buttons) 
    elif previous_state == SELECT_LEVEL: 
        draw_select_level(mouse_pos, fake_mouse_buttons)
    # Thêm các state HTP mới (6 trang)
    elif previous_state in [HOW_TO_PLAY_1, HOW_TO_PLAY_2, HOW_TO_PLAY_3, HOW_TO_PLAY_4, HOW_TO_PLAY_5, HOW_TO_PLAY_6]: 
        draw_how_to_play_screen(previous_state, mouse_pos, fake_mouse_buttons)
    elif previous_state == RANKING_BOARD: 
        draw_ranking_board(mouse_pos, fake_mouse_buttons)
        
    # Vẽ lớp phủ
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) 
    screen.blit(overlay, (0, 0))
    
    # Vẽ hộp thoại
    box_w, box_h = scale_w(500), scale_h(250)
    box_x, box_y = CX - box_w // 2, CY - box_h // 2
    box_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box_surface.fill((30, 30, 60, 240)) 
    border_radius = scale_font(10)
    pygame.draw.rect(box_surface, (255, 255, 255), box_surface.get_rect(), max(1, scale_font(2)), border_radius=border_radius) 
    screen.blit(box_surface, (box_x, box_y))
    
    text_font = load_font(scale_font(28), bold=True)
    draw_text(screen, "Do you want to get out of here?", CX, CY - scale_h(60), 
              text_font, (255, 255, 255), center=True)
              
    # Vẽ nút Yes/No
    btn_w, btn_h = scale_w(150), scale_h(50)
    btn_y = CY + scale_h(30)
    yes_x = CX - scale_w(100) - btn_w // 2
    confirm_yes_rect = pygame.Rect(yes_x, btn_y, btn_w, btn_h)
    yes_hovered = confirm_yes_rect.collidepoint(mouse_pos)
    yes_pressed = yes_hovered and mouse_buttons[0]
    draw_simple_button(screen, confirm_yes_rect, "Yes", AU1_BUTTON_FONT, (200, 0, 0), (255, 255, 255), yes_hovered, yes_pressed)
    
    no_x = CX + scale_w(100) - btn_w // 2
    confirm_no_rect = pygame.Rect(no_x, btn_y, btn_w, btn_h)
    no_hovered = confirm_no_rect.collidepoint(mouse_pos)
    no_pressed = no_hovered and mouse_buttons[0]
    draw_simple_button(screen, confirm_no_rect, "No", AU1_BUTTON_FONT, (80, 80, 80), (255, 255, 255), no_hovered, no_pressed)

# =================================================================
# === [11] XỬ LÝ SỰ KIỆN & VÒNG LẶP CHÍNH ===
# =================================================================

# --- HÀM VẼ CHUNG  ---
def draw_text(surface, text, x, y, font_obj, color, center=True):
    text_surface = font_obj.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)

def draw_shadow_text(surface, text, x, y, text_color, shadow_color, shadow_offset, font_obj):
    shadow_surface = font_obj.render(text, True, shadow_color)
    shadow_rect = shadow_surface.get_rect(center=(x + shadow_offset, y + shadow_offset))
    surface.blit(shadow_surface, shadow_rect)
    text_surface = font_obj.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, text_rect)

# Helper function để đổi nhạc nền
def play_music(file_name, loop=-1):
    """Tải và phát một file nhạc nền. Mặc định lặp vô tận (-1)."""
    try:
        pygame.mixer.music.load(file_name)
        pygame.mixer.music.play(loop) 
    except pygame.error as e:
        print(f"Lỗi: Không thể tải file nhạc '{file_name}'. {e}")

# --- HÀM XỬ LÝ LOGIC CHUYỂN STATE/LEVEL ---
def set_difficulty(rows, cols, mines, diff_name):
    """Helper function to set game parameters và BẮT ĐẦU game."""
    global GAME_ROWS, GAME_COLS, GAME_MINES, current_state, g_current_difficulty_name
    
    print(f"Setting difficulty: {diff_name} ({rows}x{cols}, {mines} mines)")
    GAME_ROWS, GAME_COLS, GAME_MINES = rows, cols, mines
    g_current_difficulty_name = diff_name 
    
    update_scaling_and_assets(SCREEN_W, SCREEN_H) 
    start_new_game()
    current_state = GAME_PLAY 

def go_to_next_level():
    """Tải level tiếp theo dựa trên level hiện tại."""
    if g_current_difficulty_name == "Easy":
        set_difficulty(16, 16, 40, "Normal")
    elif g_current_difficulty_name == "Normal":
        set_difficulty(20, 20, 75, "Hard")
    elif g_current_difficulty_name == "Hard":
        set_difficulty(16, 30, 99, "Expert")
    elif g_current_difficulty_name == "Expert":
        set_difficulty(9, 9, 10, "Easy")
    else:
        set_difficulty(9, 9, 10, "Easy")

def handle_button_click(button_name):
    """Xử lý chức năng khi nút được bấm và thay đổi state."""
    global current_state, previous_state, running
    global g_confetti_particles, g_rain_particles 
    print(f"--- [Minesweeper] Đã bấm nút: {button_name} ---")
    
    if button_name == "Exit":
        previous_state = current_state 
        current_state = CONFIRM_EXIT
    elif button_name == "Confirm Quit": 
        running = False 
    elif button_name == "Cancel Quit": 
        current_state = previous_state 
    elif button_name == "About Us":
        play_music('giao diện.mp3') 
        current_state = ABOUT_US_1 
    elif button_name == "Back to Menu": 
        play_music('Menu game (2).ogg')
        g_confetti_particles.clear() 
        g_rain_particles.clear()
        current_state = MENU
        
    # Logic Next cho 6 trang
    elif button_name == "Next": 
        if current_state == ABOUT_US_1:
            current_state = ABOUT_US_2
        elif current_state == HOW_TO_PLAY_1:
            current_state = HOW_TO_PLAY_2
        elif current_state == HOW_TO_PLAY_2:
            current_state = HOW_TO_PLAY_3
        elif current_state == HOW_TO_PLAY_3: 
            current_state = HOW_TO_PLAY_4
        elif current_state == HOW_TO_PLAY_4:
            current_state = HOW_TO_PLAY_5
        elif current_state == HOW_TO_PLAY_5:
            current_state = HOW_TO_PLAY_6
            
    # Logic Prev cho 6 trang
    elif button_name == "Prev": 
        if current_state == ABOUT_US_2:
            current_state = ABOUT_US_1
        elif current_state == HOW_TO_PLAY_2:
            current_state = HOW_TO_PLAY_1
        elif current_state == HOW_TO_PLAY_3:
            current_state = HOW_TO_PLAY_2
        elif current_state == HOW_TO_PLAY_4: 
            current_state = HOW_TO_PLAY_3
        elif current_state == HOW_TO_PLAY_5:
            current_state = HOW_TO_PLAY_4
        elif current_state == HOW_TO_PLAY_6:
            current_state = HOW_TO_PLAY_5
        
    elif button_name == "Play Game":
        play_music('giao diện.mp3')
        print("Chuyển đến màn hình chọn level...") 
        current_state = SELECT_LEVEL 
        
    elif button_name == "Easy":
        play_music('Nhạc nền game (Easy).ogg')
        set_difficulty(9, 9, 10, "Easy") 
    elif button_name == "Normal":
        play_music('Nhạc nền game (Normal).mp3')
        set_difficulty(16, 16, 40, "Normal") 
        
    elif button_name == "Hard":
        play_music('Nhạc nền game (Hard).ogg')
        set_difficulty(20, 20, 75, "Hard") 
    elif button_name == "Expert":
        play_music('Nhạc nền game (Expert).ogg')
        set_difficulty(16, 30, 99, "Expert") 
    
    elif button_name == "Restart Game":
        play_music('Nhạc nền game (2).ogg')
        print("Restarting game...")
        start_new_game() 
        
    elif button_name == "Next Level":
        play_music('Nhạc nền game (2).ogg')
        print("Loading next level...")
        go_to_next_level()
        
    elif button_name == "Ranking Board":
        play_music('Menu game (2).ogg')
        print("Mở bảng xếp hạng...") 
        current_state = RANKING_BOARD 
        
    elif button_name == "How To Play":
        play_music('giao diện.mp3')
        print("Mở hướng dẫn...") 
        current_state = HOW_TO_PLAY_1

# --- VÒNG LẶP CHÍNH (MAIN LOOP) ---
update_scaling_and_assets(BASE_W, BASE_H)
start_new_game() 

# Tải và phát nhạc MENU lần đầu
play_music('Menu game (2).ogg')

running = True
while running: 
    mouse_pos = pygame.mouse.get_pos() 
    mouse_buttons = pygame.mouse.get_pressed() 
    
    # --- XỬ LÝ EVENTS (INPUT) ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            previous_state = current_state
            current_state = CONFIRM_EXIT
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if current_state == CONFIRM_EXIT:
                    current_state = previous_state 
                # Thêm state HTP mới (6 trang)
                elif current_state in [GAME_PLAY, SELECT_LEVEL, HOW_TO_PLAY_1, HOW_TO_PLAY_2, HOW_TO_PLAY_3, HOW_TO_PLAY_4, HOW_TO_PLAY_5, HOW_TO_PLAY_6, RANKING_BOARD]: 
                    # Thêm chuyển nhạc khi thoát về Menu
                    play_music('Menu game (2).ogg')
                    current_state = MENU
                elif current_state != MENU:
                    play_music('Menu game (2).ogg')
                    current_state = MENU 
                else:
                    previous_state = current_state
                    current_state = CONFIRM_EXIT
            
            elif current_state == GAME_PLAY and g_game_state == 'entering_name':
                if event.key == pygame.K_BACKSPACE:
                    g_player_name_input = g_player_name_input[:-1]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    player_name_to_save = g_player_name_input if g_player_name_input.strip() else "Guest"
                    add_score(g_current_difficulty_name, player_name_to_save, g_game_elapsed_time)
                    g_game_state = 'won_options' 
                elif len(g_player_name_input) < 10 and event.unicode.isprintable():
                    g_player_name_input += event.unicode
            
        if event.type == pygame.VIDEORESIZE:
            new_width, new_height = event.w, event.h
            if new_width < BASE_W // 2: new_width = BASE_W // 2
            if new_height < BASE_H // 2: new_height = BASE_H // 2
            screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
            update_scaling_and_assets(new_width, new_height)
            
        # --- XỬ LÝ CLICK CHUỘT (THEO TỪNG GIAO DIỆN) ---
        if event.type == pygame.MOUSEBUTTONUP: 
            
            if current_state == MENU:
                if event.button == 1: 
                    for i, rect in enumerate(button_rects):
                        if rect.collidepoint(mouse_pos):
                            handle_button_click(BUTTON_DATA[i]["name"])
                            break 

            elif current_state == ABOUT_US_1:
                if event.button == 1:
                    text_btn_w, text_btn_h = scale_w(BASE_AU_BUTTON_W), scale_h(BASE_AU_BUTTON_H)
                    img_btn_w, img_btn_h = g_nav_btn_w, g_nav_btn_h
                    BOTTOM_POS_Y = SCREEN_H - img_btn_h - scale_h(30)
                    
                    left_rect = pygame.Rect(scale_w(50), BOTTOM_POS_Y, text_btn_w, text_btn_h)
                    right_rect = pygame.Rect(SCREEN_W - scale_w(50) - img_btn_w, BOTTOM_POS_Y, img_btn_w, img_btn_h)
                    
                    if left_rect.collidepoint(mouse_pos):
                        handle_button_click("Back to Menu") 
                    elif right_rect.collidepoint(mouse_pos):
                        handle_button_click("Next") 

            elif current_state == ABOUT_US_2:
                if event.button == 1:
                    text_btn_w, text_btn_h = scale_w(BASE_AU_BUTTON_W), scale_h(BASE_AU_BUTTON_H)
                    img_btn_w, img_btn_h = g_nav_btn_w, g_nav_btn_h
                    BOTTOM_POS_Y = SCREEN_H - img_btn_h - scale_h(30)
                    
                    left_rect = pygame.Rect(scale_w(50), BOTTOM_POS_Y, img_btn_w, img_btn_h)
                    right_rect = pygame.Rect(SCREEN_W - scale_w(50) - text_btn_w, BOTTOM_POS_Y, text_btn_w, text_btn_h) 
                    
                    if left_rect.collidepoint(mouse_pos):
                        handle_button_click("Prev") 
                    elif right_rect.collidepoint(mouse_pos):
                        handle_button_click("Back to Menu") 
            
            elif current_state == CONFIRM_EXIT: 
                if event.button == 1:
                    if confirm_yes_rect.collidepoint(mouse_pos):
                        handle_button_click("Confirm Quit")
                    elif confirm_no_rect.collidepoint(mouse_pos):
                        handle_button_click("Cancel Quit")
            
            elif current_state == SELECT_LEVEL:
                if event.button == 1:
                    for i, rect in enumerate(level_button_rects):
                        if rect.collidepoint(mouse_pos):
                            handle_button_click(LEVEL_BUTTON_DATA[i])
                            break
            
            # Xử lý click cho 6 trang HTP
            elif current_state in [HOW_TO_PLAY_1, HOW_TO_PLAY_2, HOW_TO_PLAY_3, HOW_TO_PLAY_4, HOW_TO_PLAY_5, HOW_TO_PLAY_6]:
                if event.button == 1:
                    text_btn_w, text_btn_h = scale_w(BASE_AU_BUTTON_W), scale_h(BASE_AU_BUTTON_H)
                    img_btn_w, img_btn_h = g_nav_btn_w, g_nav_btn_h
                    btn_y = SCREEN_H - img_btn_h - scale_h(30)
                    left_pos_x = scale_w(50)
                    right_pos_x = SCREEN_W - scale_w(50)
                    
                    current_left_rect = None
                    current_right_rect = None
                    
                    if current_state == HOW_TO_PLAY_1:
                        current_left_rect = pygame.Rect(left_pos_x, btn_y, text_btn_w, text_btn_h)
                        current_right_rect = pygame.Rect(right_pos_x - img_btn_w, btn_y, img_btn_w, img_btn_h)
                        
                        if current_left_rect.collidepoint(mouse_pos):
                            handle_button_click("Back to Menu")
                        elif current_right_rect.collidepoint(mouse_pos):
                            handle_button_click("Next")
                            
                    elif current_state in [HOW_TO_PLAY_2, HOW_TO_PLAY_3, HOW_TO_PLAY_4, HOW_TO_PLAY_5]:
                        current_left_rect = pygame.Rect(left_pos_x, btn_y, img_btn_w, img_btn_h)
                        current_right_rect = pygame.Rect(right_pos_x - img_btn_w, btn_y, img_btn_w, img_btn_h)
                        
                        if current_left_rect.collidepoint(mouse_pos):
                            handle_button_click("Prev")
                        elif current_right_rect.collidepoint(mouse_pos):
                            handle_button_click("Next")
                            
                    elif current_state == HOW_TO_PLAY_6:
                        current_left_rect = pygame.Rect(left_pos_x, btn_y, img_btn_w, img_btn_h)
                        current_right_rect = pygame.Rect(right_pos_x - text_btn_w, btn_y, text_btn_w, text_btn_h)
                        
                        if current_left_rect.collidepoint(mouse_pos):
                            handle_button_click("Prev")
                        elif current_right_rect.collidepoint(mouse_pos):
                            handle_button_click("Back to Menu")
            
            elif current_state == RANKING_BOARD:
                if event.button == 1:
                    if g_rb_top_right_back_rect.collidepoint(mouse_pos): 
                        handle_button_click("Back to Menu")
                    else:
                        diff_names = ["Easy", "Normal", "Hard", "Expert"]
                        for i, rect in enumerate(g_rb_tab_rects):
                            if rect.collidepoint(mouse_pos): 
                                g_ranking_view = diff_names[i]
                                print(f"Changed ranking view to: {g_ranking_view}")
                                break

            elif current_state == GAME_PLAY: 
                if event.button == 1: # Chuột trái ABOUT
                    if g_game_state == 'playing':
                        if g_home_button_rect.collidepoint(mouse_pos):
                            handle_button_click("Back to Menu")
                        elif g_restart_button_rect.collidepoint(mouse_pos):
                            handle_button_click("Restart Game")
                        else:
                            grid_pos = get_grid_pos(mouse_pos)
                            if grid_pos:
                                reveal_cell(grid_pos[0], grid_pos[1])
                    
                    elif g_game_state == 'lost':
                        if g_lose_restart_rect.collidepoint(mouse_pos):
                            handle_button_click("Restart Game")
                        elif g_lose_menu_rect.collidepoint(mouse_pos):
                            handle_button_click("Back to Menu")
                            
                    elif g_game_state == 'won_options':
                        if g_win_restart_rect.collidepoint(mouse_pos):
                            handle_button_click("Restart Game")
                        elif g_win_next_rect.collidepoint(mouse_pos):
                            handle_button_click("Next Level")
                        elif g_win_menu_rect.collidepoint(mouse_pos):
                            handle_button_click("Back to Menu")
                            
                    elif g_game_state == 'entering_name':
                        pass 
                            
                elif event.button == 3: # Chuột phải
                    if g_game_state == 'playing':
                        grid_pos = get_grid_pos(mouse_pos)
                        if grid_pos:
                            toggle_flag(grid_pos[0], grid_pos[1])

    # --- LOGIC VẼ (DRAW) ---
    if current_state == MENU:
        draw_main_menu(mouse_pos, mouse_buttons)
    elif current_state == ABOUT_US_1:
        draw_about_us_screen(ABOUT_US_1, AU1_CONFIG, mouse_pos, mouse_buttons, next_state=ABOUT_US_2)
    elif current_state == ABOUT_US_2:
        draw_about_us_screen(ABOUT_US_2, AU2_CONFIG, mouse_pos, mouse_buttons) 
    elif current_state == SELECT_LEVEL: 
        draw_select_level(mouse_pos, mouse_buttons)
    # Thêm state HTP mới (6 trang)
    elif current_state in [HOW_TO_PLAY_1, HOW_TO_PLAY_2, HOW_TO_PLAY_3, HOW_TO_PLAY_4, HOW_TO_PLAY_5, HOW_TO_PLAY_6]: 
        draw_how_to_play_screen(current_state, mouse_pos, mouse_buttons)
    elif current_state == RANKING_BOARD: 
        draw_ranking_board(mouse_pos, mouse_buttons)
    elif current_state == GAME_PLAY: 
        draw_game_play(mouse_pos, mouse_buttons) 
    elif current_state == CONFIRM_EXIT: 
        draw_confirm_exit(mouse_pos, mouse_buttons)
        
    # --- Cập nhật màn hình ---
    pygame.display.flip()
    CLOCK.tick(60) 

# --- Thoát Pygame ---
pygame.quit()
sys.exit()
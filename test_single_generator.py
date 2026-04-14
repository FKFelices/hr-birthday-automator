import os
import re
import requests
import gspread
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
from rembg import remove, new_session

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Change this number to test a specific row in your Google Sheet!
TARGET_ROW = 3

def convert_gdrive_link(url):
    """Converts a standard Google Drive share link into a direct image download link."""
    if "drive.google.com" in url:
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url 

# ==========================================
# 2. CORE: THE GENERATOR FUNCTION (NO EMAIL)
# ==========================================
def generate_birthday_card(name, position, image_url, gender):
    
    # --- DYNAMIC TEMPLATE LOGIC ---
    if gender.lower() == 'female':
        template = Image.open("base_template_female.png")
        pic_y = 620
        name_y = 945
        pos_y = 985
        
        name_font = ImageFont.truetype("fonts/PressStart2P-Regular.ttf", 50)
        position_font = ImageFont.truetype("fonts/LeagueSpartan-VariableFont_wght.ttf", 32)
        
        name_color = (195, 155, 211) 
        pos_color = (50, 50, 50)     
        name_stroke = 2
        
        target_size = (501, 501) 
        do_alpha_matting = False  
        do_post_process = True
        
    else:
        template = Image.open("base_template_male.png")
        pic_y = 650
        name_y = 980
        pos_y = 1020
        
        name_font = ImageFont.truetype("fonts/TcMiloRegular-0vj5r.otf", 60)
        position_font = ImageFont.truetype("fonts/TcMiloRegular-0vj5r.otf", 35)
        
        name_color = (0, 0, 0)       
        pos_color = (0, 0, 0)        
        name_stroke = 0
        
        target_size = (470, 490)
        do_alpha_matting = True
        do_post_process = True

    # --- DEFENSIVE IMAGE FETCHING ---
    direct_url = convert_gdrive_link(image_url)
    
    try:
        response = requests.get(direct_url)
        response.raise_for_status() 
        
        if 'image' not in response.headers.get('Content-Type', ''):
            print(f"  -> [ERROR] The URL for {name} is not a valid image. Skipping.")
            return False
            
        headshot = Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"  -> [ERROR] Failed to download image for {name}. Error: {e}")
        return False

# --- AI BACKGROUND REMOVAL ---
    print("  -> Removing background (this takes a few seconds)...")
    human_model = new_session("u2net_human_seg")
    headshot = remove(
        headshot, 
        session=human_model, 
        alpha_matting=do_alpha_matting, 
        post_process_mask=do_post_process
    )
    
    # ========= SMART AUTO-CENTER FIX START =========
    print("  -> [FIX] Analyzing visible area for auto-centering...")
    bbox = headshot.getbbox() 

    if bbox:
        headshot = headshot.crop(bbox)
        print(f"  -> [FIX] Content found. Tight bounding box cropped: {bbox}")
    else:
        print(f"  -> [ERROR] Image seems totally transparent after removal.")
    # ========= SMART AUTO-CENTER FIX END =========

    headshot = ImageOps.fit(headshot, target_size, Image.Resampling.LANCZOS)
    
    # --- CALCULATE & PASTE ---
    paste_x = 540 - (target_size[0] // 2)
    paste_y = pic_y - (target_size[1] // 2) 
    
    template.paste(headshot, (paste_x, paste_y), headshot)
    
    # --- DRAW TYPOGRAPHY ---
    draw = ImageDraw.Draw(template)
    draw.text((540, name_y), name, fill=name_color, font=name_font, anchor="mm", stroke_width=name_stroke, stroke_fill=(0,0,0))
    draw.text((540, pos_y), position, fill=pos_color, font=position_font, anchor="mm")
    
    # --- SAVE LOCALLY ---
    output_filename = f"output/{name.replace(' ', '_')}_bday_TEST.png"
    template.save(output_filename)
    print(f"  -> [✅ SUCCESS] Saved test card to: {output_filename}")
    return True

# ==========================================
# 3. PIPELINE: SINGLE TARGET TESTER
# ==========================================
def run_single_row_test():
    print(f"\n🛠️ Initializing Single Tester for ROW {TARGET_ROW} (Emails Disabled)...")
    
    if not os.path.exists("output"):
        os.makedirs("output")
        
    try:
        gc = gspread.service_account(filename='google_secret.json')
        sheet = gc.open("HR_Employee_Database").sheet1
        hr_data = sheet.get_all_records()
    except Exception as e:
        print(f"[FATAL ERROR] Could not connect to Google Cloud: {e}")
        return

    # In Google Sheets, Row 1 is headers, Row 2 is data index 0.
    # Therefore, array index = TARGET_ROW - 2
    data_index = TARGET_ROW - 2

    if data_index < 0 or data_index >= len(hr_data):
        print(f"❌ ERROR: Row {TARGET_ROW} is out of bounds or empty.")
        return

    row = hr_data[data_index]
    name = str(row.get('Name', '')).strip()
    
    if not name:
        print(f"❌ ERROR: Row {TARGET_ROW} does not contain an employee name.")
        return
        
    print("-" * 50)
    print(f"Processing target: {name} (Position: {row.get('Position', 'Unknown')})")
    
    generate_birthday_card(
        name=name,
        position=row.get('Position', ''),
        image_url=row.get('Image_URL', ''), 
        gender=row.get('Gender', 'Male')
    )
    print("-" * 50)

# ==========================================
# EXECUTE PROGRAM
# ==========================================
if __name__ == "__main__":
    run_single_row_test()
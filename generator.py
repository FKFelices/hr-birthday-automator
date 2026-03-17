import os
import re
import requests
import gspread
import smtplib
from email.message import EmailMessage
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
from rembg import remove, new_session

# ==========================================
# 1. HELPER: GOOGLE DRIVE LINK CONVERTER
# ==========================================
def convert_gdrive_link(url):
    """Converts a standard Google Drive share link into a direct image download link."""
    if "drive.google.com" in url:
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url 

# ==========================================
# 2. HELPER: AUTOMATED EMAIL DELIVERY
# ==========================================
def send_delivery_email(employee_name, image_path):
    print(f"  -> Preparing email delivery for {employee_name}...")
    
    # --- CONFIGURATION (Update these!) ---
    bot_email = "botniflorence@gmail.com"
    bot_password = "dcoh totx qhen kdfz" 
    manager_email = "feliceskylekun@gmail.com"

    msg = EmailMessage()
    msg['Subject'] = f"🎉 New Birthday Card Ready: {employee_name}"
    msg['From'] = bot_email
    msg['To'] = manager_email
    
    msg.set_content(
        f"Good morning po maam.!\n\n"
        f"Birthday po ni {employee_name}. "
        f"Mag papapost nlang po maam, thank you!.\n\n"
        f"From,\n"
        f"Florence"
    )

    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            image_name = os.path.basename(image_path)
            
        msg.add_attachment(image_data, maintype='image', subtype='png', filename=image_name)
    except Exception as e:
        print(f"  -> [ERROR] Could not attach image: {e}")
        return

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(bot_email, bot_password)
            smtp.send_message(msg)
            print(f"  -> [SUCCESS] Card emailed!")
    except Exception as e:
        print(f"  -> [ERROR] Failed to send email: {e}")

# ==========================================
# 3. CORE: THE GENERATOR FUNCTION
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
    print(f"  -> Fetching photo from cloud database...")
    direct_url = convert_gdrive_link(image_url)
    
    try:
        response = requests.get(direct_url)
        response.raise_for_status() 
        
        if 'image' not in response.headers.get('Content-Type', ''):
            print(f"  -> [ERROR] The URL for {name} is not a valid image. Skipping.")
            return
            
        headshot = Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"  -> [ERROR] Failed to download image for {name}. Error: {e}")
        return

    # --- AI BACKGROUND REMOVAL ---
    print("  -> Running AI background remover...")
    human_model = new_session("u2net_human_seg")
    headshot = remove(
        headshot, 
        session=human_model, 
        alpha_matting=do_alpha_matting, 
        post_process_mask=do_post_process
    )
    
    headshot = ImageOps.fit(headshot, target_size, Image.Resampling.LANCZOS)
    
    # --- CALCULATE & PASTE ---
    paste_x = 540 - (target_size[0] // 2)
    paste_y = pic_y - (target_size[1] // 2) 
    
    template.paste(headshot, (paste_x, paste_y), headshot)
    
    # --- DRAW TYPOGRAPHY ---
    draw = ImageDraw.Draw(template)
    draw.text((540, name_y), name, fill=name_color, font=name_font, anchor="mm", stroke_width=name_stroke, stroke_fill=(0,0,0))
    draw.text((540, pos_y), position, fill=pos_color, font=position_font, anchor="mm")
    
    # --- SAVE & DELIVER ---
    output_filename = f"output/{name.replace(' ', '_')}_bday.png"
    template.save(output_filename)
    print(f"  -> [SUCCESS] Successfully generated card for {name}!")
    
    # Trigger the automated email delivery
    send_delivery_email(name, output_filename)
    print("") # Adds a blank line for terminal readability


# ==========================================
# 4. PIPELINE: GOOGLE SHEETS AUTOMATION
# ==========================================
def run_cloud_birthday_check():
    print("\nInitializing Birthday Automation Pipeline...")
    
    if not os.path.exists("output"):
        os.makedirs("output")
        
    try:
        gc = gspread.service_account(filename='google_secret.json')
        sheet = gc.open("HR_Employee_Database").sheet1
        hr_data = sheet.get_all_records()
    except Exception as e:
        print(f"[FATAL ERROR] Could not connect to Google Cloud: {e}")
        return

    today = datetime.today().strftime('%m-%d')
    print(f"Connected to Cloud. Checking for birthdays matching: {today}\n")
    print("-" * 50)
    
    match_found = False
    
    for row in hr_data:
        if str(row['Birthday']).strip() == today:
            match_found = True
            print(f"🎉 Birthday Match: {row['Name']}")
            
            generate_birthday_card(
                name=row['Name'],
                position=row['Position'],
                image_url=row['Image_URL'], 
                gender=row['Gender']
            )
            
    if not match_found:
        print("Walang may birthday ngayon.")
    print("-" * 50)

# ==========================================
# EXECUTE PROGRAM
# ==========================================
if __name__ == "__main__":
    run_cloud_birthday_check()
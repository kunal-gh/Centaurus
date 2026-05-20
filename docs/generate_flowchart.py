"""
Generates the Identity Resolution Flowchart diagram as a premium dark-themed PNG.
Uses Pillow to create a high-quality visualization of BookLeaf's identity pipeline.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def draw_arrow(draw, start, end, color=(129, 140, 248), width=3):
    # Draws a line from start to end with an arrowhead at end
    draw.line([start, end], fill=color, width=width)
    
    # Arrowhead calculations
    x1, y1 = start
    x2, y2 = end
    
    # Vector direction
    import math
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx*dx + dy*dy)
    if length == 0:
        return
        
    ux = dx / length
    uy = dy / length
    
    # Arrow head size
    arrow_len = 10
    
    # Left and right wing of arrow
    ax = x2 - ux * arrow_len + uy * (arrow_len * 0.5)
    ay = y2 - uy * arrow_len - ux * (arrow_len * 0.5)
    
    bx = x2 - ux * arrow_len - uy * (arrow_len * 0.5)
    by = y2 - uy * arrow_len + ux * (arrow_len * 0.5)
    
    draw.polygon([(x2, y2), (ax, ay), (bx, by)], fill=color)

def generate_chart():
    # Create image with Slate-900 background
    width, height = 1200, 900
    img = Image.new('RGB', (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    # Fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        subtitle_font = ImageFont.truetype("arial.ttf", 16)
        label_font = ImageFont.truetype("arial.ttf", 14)
        bold_font = ImageFont.truetype("arial.ttf", 15)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except IOError:
        # Fallback to default
        title_font = subtitle_font = label_font = bold_font = small_font = ImageFont.load_default()
        
    # Slate colors
    border_color = (51, 65, 85)
    card_bg = (30, 41, 59)
    text_light = (241, 245, 249)
    text_muted = (148, 163, 184)
    
    # Accent colors
    accent_purple = (129, 140, 248) # Indigo-400
    accent_emerald = (52, 211, 153) # Emerald-400
    accent_amber = (251, 191, 36)   # Amber-400
    accent_rose = (248, 113, 113)   # Rose-400
    
    # ------------------ TITLE ------------------
    draw.text((width // 2, 40), "BOOKLEAF AUTHOR IDENTITY RESOLUTION PIPELINE", fill=accent_purple, font=title_font, anchor="mm")
    draw.text((width // 2, 70), "Three-Tier Multi-Signal Identity Unification with Confidences & LLM Borderline Arbitration", fill=text_muted, font=subtitle_font, anchor="mm")
    
    # ------------------ STAGE 1: INPUT ------------------
    # Box: Incoming Request
    draw.rounded_rectangle([450, 110, 750, 190], radius=8, fill=card_bg, outline=border_color, width=2)
    draw.text((600, 130), "Incoming Author Request", fill=accent_purple, font=bold_font, anchor="mm")
    draw.text((600, 160), "Signals: Email | Phone | Name | Instagram", fill=text_light, font=label_font, anchor="mm")
    
    # Arrow to Base Scorer
    draw_arrow(draw, (600, 190), (600, 240))
    
    # ------------------ STAGE 2: BASE MATCH SCORER ------------------
    # Box: Match Scorer
    draw.rounded_rectangle([380, 240, 820, 340], radius=8, fill=card_bg, outline=border_color, width=2)
    draw.text((600, 260), "Multi-Signal Weighted Match Scorer", fill=accent_purple, font=bold_font, anchor="mm")
    draw.text((600, 290), "Email exact (35 pts)  •  Phone normalized exact (30 pts)", fill=text_light, font=label_font, anchor="mm")
    draw.text((600, 315), "Name fuzzy token_sort_ratio > 70 (25 pts)  •  Instagram exact (10 pts)", fill=text_light, font=label_font, anchor="mm")
    
    # Arrow to Tiers Decision
    draw_arrow(draw, (600, 340), (600, 390))
    
    # ------------------ STAGE 3: TIERS CHECK ------------------
    # Box: Tiers Check Decision Diamond (simplified as a nice hexagon or octagonal styled rect)
    draw.rounded_rectangle([420, 390, 780, 450], radius=20, fill=card_bg, outline=accent_purple, width=2)
    draw.text((600, 420), "Evaluate Weighted Score (0 - 100)", fill=text_light, font=bold_font, anchor="mm")
    
    # 3 Arrows branching out from Tiers Check
    # Left Branch (Tier 1)
    draw_arrow(draw, (420, 420), (220, 420), color=accent_purple)
    draw_arrow(draw, (220, 420), (220, 720), color=accent_purple)
    
    # Right Branch (Tier 3)
    draw_arrow(draw, (780, 420), (980, 420), color=accent_purple)
    draw_arrow(draw, (980, 420), (980, 720), color=accent_purple)
    
    # Center Branch (Tier 2)
    draw_arrow(draw, (600, 450), (600, 490), color=accent_purple)
    
    # Branch text labels
    draw.text((310, 400), "Score >= 80%\n[Tier 1: Auto Match]", fill=accent_emerald, font=small_font, anchor="mm")
    draw.text((890, 400), "Score < 40%\n[Tier 3: Create New]", fill=accent_rose, font=small_font, anchor="mm")
    draw.text((680, 470), "Score 40 - 79%\n[Tier 2: Borderline]", fill=accent_purple, font=small_font, anchor="mm")
    
    # ------------------ STAGE 4: BORDERLINE LLM VERIFICATION ------------------
    # Box: LLM Verification (Center)
    draw.rounded_rectangle([400, 490, 800, 570], radius=8, fill=card_bg, outline=border_color, width=2)
    draw.text((600, 510), "Borderline LLM Verification", fill=accent_purple, font=bold_font, anchor="mm")
    draw.text((600, 540), "GPT-4o-mini: Compare profiles, compute similarity probability", fill=text_light, font=label_font, anchor="mm")
    
    # Arrow to LLM Decision Gate
    draw_arrow(draw, (600, 570), (600, 610))
    
    # Box: LLM Prob Gate
    draw.rounded_rectangle([430, 610, 770, 670], radius=20, fill=card_bg, outline=accent_purple, width=2)
    draw.text((600, 640), "LLM Same-Person Probability", fill=text_light, font=bold_font, anchor="mm")
    
    # Arrow from LLM gate to auto_link (left)
    draw.line([(430, 640), (320, 640)], fill=accent_purple, width=3)
    draw_arrow(draw, (320, 640), (280, 720), color=accent_purple)
    draw.text((350, 620), "Prob >= 0.85\n(auto_link)", fill=accent_emerald, font=small_font, anchor="mm")
    
    # Arrow from LLM gate to verify_manually (center-down)
    draw_arrow(draw, (600, 670), (600, 720), color=accent_purple)
    draw.text((670, 695), "Prob 0.60 - 0.84\n(verify_manually)", fill=accent_amber, font=small_font, anchor="mm")
    
    # Arrow from LLM gate to create_new (right)
    draw.line([(770, 640), (880, 640)], fill=accent_purple, width=3)
    draw_arrow(draw, (880, 640), (920, 720), color=accent_purple)
    draw.text((850, 620), "Prob < 0.60\n(create_new)", fill=accent_rose, font=small_font, anchor="mm")
    
    # ------------------ STAGE 5: OUTCOME ACTIONS ------------------
    # Box 1: AUTO LINK (Left)
    draw.rounded_rectangle([100, 720, 340, 810], radius=8, fill=(6, 78, 59), outline=accent_emerald, width=2)
    draw.text((220, 745), "ACTION: AUTO LINK", fill=accent_emerald, font=bold_font, anchor="mm")
    draw.text((220, 780), "Link profile automatically;\nfinal confidence = calculated score", fill=text_light, font=small_font, anchor="mm")
    
    # Box 2: VERIFY MANUALLY (Center)
    draw.rounded_rectangle([480, 720, 720, 810], radius=8, fill=(120, 83, 4), outline=accent_amber, width=2)
    draw.text((600, 745), "ACTION: VERIFY MANUALLY", fill=accent_amber, font=bold_font, anchor="mm")
    draw.text((600, 780), "Mark unverified in database;\nqueue for human admin review", fill=text_light, font=small_font, anchor="mm")
    
    # Box 3: CREATE NEW (Right)
    draw.rounded_rectangle([860, 720, 1100, 810], radius=8, fill=(153, 27, 27), outline=accent_rose, width=2)
    draw.text((980, 745), "ACTION: CREATE NEW", fill=accent_rose, font=bold_font, anchor="mm")
    draw.text((980, 780), "Provision brand new author profile\nin the central database", fill=text_light, font=small_font, anchor="mm")
    
    # Footer
    draw.text((width // 2, 860), "© 2026 BookLeaf Publishing AI Agent Automation Systems. All rights reserved.", fill=text_muted, font=small_font, anchor="mm")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname("docs/identity_flowchart.png"), exist_ok=True)
    img.save("docs/identity_flowchart.png")
    print("Flowchart generated successfully at docs/identity_flowchart.png")

if __name__ == "__main__":
    generate_chart()

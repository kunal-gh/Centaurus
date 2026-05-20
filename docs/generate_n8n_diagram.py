"""
Generates the n8n Workflow Diagram as a premium dark-themed PNG.
Uses Pillow to create a high-quality visualization of the 7-node n8n gateway workflow.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def draw_arrow(draw, start, end, color=(251, 146, 60), width=3): # Orange-400 for n8n theme
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

def generate_n8n():
    # Create image with Slate-900 background
    width, height = 1200, 700
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
    
    # n8n orange theme colors
    n8n_orange = (251, 146, 60) # Orange-400
    accent_emerald = (52, 211, 153) # Emerald-400
    accent_rose = (248, 113, 113) # Rose-400
    
    # ------------------ TITLE ------------------
    draw.text((width // 2, 40), "n8n EVENT GATEWAY WORKFLOW CANVAS", fill=n8n_orange, font=title_font, anchor="mm")
    draw.text((width // 2, 70), "Visualizing the 7-Node Routing, Escalation Circuit Breaker, and Audit Logging Flow", fill=text_muted, font=subtitle_font, anchor="mm")
    
    # Nodes positions
    # 1. Webhook (Trigger) -> 2. Set Format -> 3. HTTP Request FastAPI -> 4. IF Gate -> (5a Set Escalate / 5b No-Op) -> 6. Supabase Log -> 7. Webhook Response
    
    # Node 1: Webhook Trigger
    draw.rounded_rectangle([60, 260, 220, 360], radius=8, fill=card_bg, outline=n8n_orange, width=2)
    draw.text((140, 285), "1. Webhook Trigger", fill=n8n_orange, font=bold_font, anchor="mm")
    draw.text((140, 315), "POST /bookleaf-gateway", fill=text_light, font=small_font, anchor="mm")
    draw.text((140, 335), "Response Mode: Last Node", fill=text_muted, font=small_font, anchor="mm")
    
    draw_arrow(draw, (220, 310), (280, 310))
    
    # Node 2: Set: Format Payload
    draw.rounded_rectangle([280, 260, 440, 360], radius=8, fill=card_bg, outline=border_color, width=1)
    draw.text((360, 285), "2. Set: Payload", fill=text_light, font=bold_font, anchor="mm")
    draw.text((360, 315), "Maps channel, message,", fill=text_muted, font=small_font, anchor="mm")
    draw.text((360, 335), "email, phone, name, insta", fill=text_muted, font=small_font, anchor="mm")
    
    draw_arrow(draw, (440, 310), (500, 310))
    
    # Node 3: HTTP Request: Call FastAPI Brain
    draw.rounded_rectangle([500, 260, 660, 360], radius=8, fill=card_bg, outline=n8n_orange, width=2)
    draw.text((580, 285), "3. HTTP Request", fill=n8n_orange, font=bold_font, anchor="mm")
    draw.text((580, 315), "POST /chat to Brain", fill=text_light, font=small_font, anchor="mm")
    draw.text((580, 335), "Timeout: 30000ms", fill=text_muted, font=small_font, anchor="mm")
    
    draw_arrow(draw, (660, 310), (720, 310))
    
    # Node 4: IF: Confidence Gate
    draw.rounded_rectangle([720, 260, 880, 360], radius=20, fill=card_bg, outline=n8n_orange, width=2)
    draw.text((800, 290), "4. IF Gate (80% Rule)", fill=n8n_orange, font=bold_font, anchor="mm")
    draw.text((800, 320), "confidence < 0.8 OR", fill=text_light, font=small_font, anchor="mm")
    draw.text((800, 340), "escalated == true?", fill=text_light, font=small_font, anchor="mm")
    
    # Branching arrows
    # TRUE -> Escalation Message (Up-right)
    draw.line([(880, 310), (910, 310), (910, 180)], fill=accent_rose, width=3)
    draw_arrow(draw, (910, 180), (940, 180), color=accent_rose)
    draw.text((915, 230), "TRUE", fill=accent_rose, font=small_font, anchor="mm")
    
    # FALSE -> No-Op (Down-right)
    draw.line([(880, 310), (910, 310), (910, 440)], fill=accent_emerald, width=3)
    draw_arrow(draw, (910, 440), (940, 440), color=accent_emerald)
    draw.text((915, 390), "FALSE", fill=accent_emerald, font=small_font, anchor="mm")
    
    # Node 5a: Set: Escalation Message
    draw.rounded_rectangle([940, 130, 1100, 230], radius=8, fill=card_bg, outline=accent_rose, width=2)
    draw.text((1020, 155), "5a. Set Escalation", fill=accent_rose, font=bold_font, anchor="mm")
    draw.text((1020, 185), "response = human message", fill=text_light, font=small_font, anchor="mm")
    draw.text((1020, 205), "escalated = true", fill=text_muted, font=small_font, anchor="mm")
    
    # Node 5b: No Operation: Pass Through
    draw.rounded_rectangle([940, 390, 1100, 490], radius=8, fill=card_bg, outline=accent_emerald, width=2)
    draw.text((1020, 415), "5b. No Operation", fill=accent_emerald, font=bold_font, anchor="mm")
    draw.text((1020, 445), "Pass-through unmodified", fill=text_muted, font=small_font, anchor="mm")
    
    # Lines merging from 5a and 5b into Node 6 (Supabase Log)
    draw.line([(1100, 180), (1130, 180), (1130, 310)], fill=n8n_orange, width=3)
    draw.line([(1100, 440), (1130, 440), (1130, 310)], fill=n8n_orange, width=3)
    draw_arrow(draw, (1130, 310), (1130, 540), color=n8n_orange)
    draw.line([(1130, 540), (440, 540)], fill=n8n_orange, width=3)
    draw_arrow(draw, (440, 540), (440, 560), color=n8n_orange)
    
    # Node 6: Supabase: Log to query_logs
    draw.rounded_rectangle([340, 560, 540, 640], radius=8, fill=card_bg, outline=border_color, width=1)
    draw.text((440, 580), "6. Supabase: Log to query_logs", fill=text_light, font=bold_font, anchor="mm")
    draw.text((440, 605), "Inserts raw message, response, intent, conf", fill=text_muted, font=small_font, anchor="mm")
    draw.text((440, 623), "Continue on Fail = True", fill=accent_emerald, font=small_font, anchor="mm")
    
    draw_arrow(draw, (540, 600), (660, 600))
    
    # Node 7: Webhook Response
    draw.rounded_rectangle([660, 560, 860, 640], radius=8, fill=card_bg, outline=n8n_orange, width=2)
    draw.text((760, 580), "7. Webhook Response", fill=n8n_orange, font=bold_font, anchor="mm")
    draw.text((760, 610), "Status 200 | response body", fill=text_light, font=small_font, anchor="mm")
    
    # Footer
    draw.text((width // 2, 675), "© 2026 BookLeaf Publishing AI Agent Automation Systems. All rights reserved.", fill=text_muted, font=small_font, anchor="mm")
    
    img.save("docs/n8n_workflow.png")
    print("n8n workflow diagram generated successfully at docs/n8n_workflow.png")

if __name__ == "__main__":
    generate_n8n()

"""
Generates the System Architecture Diagram as a premium dark-themed PNG.
Uses Pillow to create a high-quality visualization of BookLeaf's hybrid system flow.
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

def generate_arch():
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
    accent_cyan = (34, 211, 238)    # Cyan-400
    
    # ------------------ TITLE ------------------
    draw.text((width // 2, 40), "BOOKLEAF SYSTEM ARCHITECTURE & DATA FLOW", fill=accent_cyan, font=title_font, anchor="mm")
    draw.text((width // 2, 70), "Hybrid Event-Driven Gateway (n8n Cloud) & Intelligent Orchestration Brain (FastAPI)", fill=text_muted, font=subtitle_font, anchor="mm")
    
    # ------------------ CHANNELS (LEFT COLUMN, X: 60-240) ------------------
    draw.text((150, 150), "SUPPORT CHANNELS", fill=accent_purple, font=bold_font, anchor="mm")
    
    channels = [
        ("Web Chat (Streamlit)", 200),
        ("Email Queries", 280),
        ("WhatsApp Messages", 360),
        ("Instagram DMs", 440)
    ]
    for name, y in channels:
        draw.rounded_rectangle([40, y, 260, y + 50], radius=6, fill=card_bg, outline=border_color, width=1)
        draw.text((150, y + 25), name, fill=text_light, font=label_font, anchor="mm")
        
    # Group box around channels
    draw.rounded_rectangle([30, 110, 270, 520], radius=8, fill=None, outline=border_color, width=1)
    
    # Arrow from Channels to n8n Gateway
    draw_arrow(draw, (270, 320), (360, 320), color=accent_cyan)
    draw.text((315, 290), "Webhook\nPayload", fill=text_muted, font=small_font, anchor="mm")
    
    # ------------------ GATEWAY LAYER: n8n (X: 360-580) ------------------
    # n8n container box
    draw.rounded_rectangle([360, 110, 580, 520], radius=8, fill=card_bg, outline=accent_amber, width=2)
    draw.text((470, 135), "n8n GATEWAY WORKFLOW", fill=accent_amber, font=bold_font, anchor="mm")
    draw.text((470, 160), "[Event Routing]", fill=text_muted, font=small_font, anchor="mm")
    
    n8n_nodes = [
        ("Webhook Listener", 190),
        ("Payload Normalizer", 260),
        ("Escalation Gate (80%)", 330),
        ("Audit Logging Router", 400),
        ("Webhook Responder", 470)
    ]
    for name, y in n8n_nodes:
        draw.rounded_rectangle([380, y, 560, y + 45], radius=4, fill=(15, 23, 42), outline=border_color, width=1)
        draw.text((470, y + 22), name, fill=text_light, font=small_font, anchor="mm")
        
    # Arrow from n8n to FastAPI Brain
    draw_arrow(draw, (580, 320), (670, 320), color=accent_cyan)
    draw.text((625, 290), "POST /chat", fill=text_muted, font=small_font, anchor="mm")
    
    # Arrow back from FastAPI to n8n (Response)
    draw_arrow(draw, (670, 350), (580, 350), color=accent_emerald)
    draw.text((625, 375), "JSON Response", fill=text_muted, font=small_font, anchor="mm")
    
    # ------------------ BRAIN LAYER: FastAPI Backend (X: 670-960) ------------------
    draw.rounded_rectangle([670, 110, 960, 780], radius=8, fill=card_bg, outline=accent_purple, width=2)
    draw.text((815, 135), "FastAPI BRAIN ENGINE", fill=accent_purple, font=bold_font, anchor="mm")
    draw.text((815, 160), "[Core Intelligence Pipeline]", fill=text_muted, font=small_font, anchor="mm")
    
    fastapi_services = [
        ("1. Intent Classifier (GPT-4o-mini)", 190),
        ("2. Identity Unifier (rapidfuzz / LLM)", 270),
        ("3. Data Retriever (DB Client)", 350),
        ("4. RAG Vector Search (NumPy)", 430),
        ("5. Confidence Scorer (50/30/20 Formula)", 510),
        ("6. Response Generator (GPT-4o-mini)", 590),
        ("7. Auditing & Logging Service", 670),
        ("8. Health Monitoring Endpoint", 730)
    ]
    for name, y in fastapi_services:
        draw.rounded_rectangle([690, y, 940, y + 55], radius=6, fill=(15, 23, 42), outline=border_color, width=1)
        draw.text((815, y + 27), name, fill=text_light, font=small_font, anchor="mm")
        
    # ------------------ DATA LAYER (RIGHT COLUMN, X: 1020-1170) ------------------
    # Supabase (Top)
    draw.rounded_rectangle([1020, 110, 1170, 380], radius=8, fill=card_bg, outline=accent_emerald, width=2)
    draw.text((1095, 135), "SUPABASE DB", fill=accent_emerald, font=bold_font, anchor="mm")
    draw.text((1095, 160), "[PostgreSQL Store]", fill=text_muted, font=small_font, anchor="mm")
    
    db_tables = ["authors", "books", "query_logs", "identity_mappings", "knowledge_base"]
    for i, t in enumerate(db_tables):
        draw.text((1095, 200 + i * 32), f"• {t}", fill=text_light, font=small_font, anchor="mm")
        
    # Arrows between FastAPI and Supabase
    draw_arrow(draw, (960, 240), (1020, 240), color=accent_emerald)
    draw.text((990, 215), "Query", fill=text_muted, font=small_font, anchor="mm")
    
    draw_arrow(draw, (1020, 270), (960, 270), color=accent_cyan)
    draw.text((990, 290), "Data", fill=text_muted, font=small_font, anchor="mm")
    
    # OpenAI APIs (Bottom)
    draw.rounded_rectangle([1020, 480, 1170, 780], radius=8, fill=card_bg, outline=accent_purple, width=2)
    draw.text((1095, 505), "OPENAI API", fill=accent_purple, font=bold_font, anchor="mm")
    draw.text((1095, 530), "[LLM & Embeddings]", fill=text_muted, font=small_font, anchor="mm")
    
    openai_models = ["gpt-4o-mini", "text-embedding-3-small"]
    for i, m in enumerate(openai_models):
        draw.rounded_rectangle([1030, 570 + i * 90, 1160, 570 + i * 90 + 70], radius=4, fill=(15, 23, 42), outline=border_color, width=1)
        draw.text((1095, 570 + i * 90 + 35), m, fill=text_light, font=small_font, anchor="mm")
        
    # Arrows between FastAPI and OpenAI
    draw_arrow(draw, (960, 600), (1020, 600), color=accent_purple)
    draw_arrow(draw, (1020, 630), (960, 630), color=accent_cyan)
    
    # Flow Line from n8n directly to Supabase logs for Phase 7
    draw_arrow(draw, (470, 520), (470, 840), color=accent_emerald)
    draw.line([(470, 840), (1095, 840)], fill=accent_emerald, width=3)
    draw_arrow(draw, (1095, 840), (1095, 380), color=accent_emerald)
    draw.text((780, 820), "Direct Audit Logging to query_logs (fallback-safe)", fill=accent_emerald, font=small_font, anchor="mm")
    
    # Footer
    draw.text((width // 2, 875), "© 2026 BookLeaf Publishing AI Agent Automation Systems. All rights reserved.", fill=text_muted, font=small_font, anchor="mm")
    
    img.save("docs/architecture_diagram.png")
    print("Architecture diagram generated successfully at docs/architecture_diagram.png")

if __name__ == "__main__":
    generate_arch()

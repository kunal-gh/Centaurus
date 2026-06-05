"""
Generate the Centaurus platform architecture diagram.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def draw_arrow(draw, start, end, color, width=3):
    draw.line([start, end], fill=color, width=width)
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux = dx / length
    uy = dy / length
    arrow_len = 12
    left = (x2 - ux * arrow_len + uy * 6, y2 - uy * arrow_len - ux * 6)
    right = (x2 - ux * arrow_len - uy * 6, y2 - uy * arrow_len + ux * 6)
    draw.polygon([(x2, y2), left, right], fill=color)


def generate_arch():
    width, height = 1200, 900
    img = Image.new("RGB", (width, height), color=(12, 17, 30))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        subtitle_font = ImageFont.truetype("arial.ttf", 16)
        label_font = ImageFont.truetype("arial.ttf", 14)
        bold_font = ImageFont.truetype("arial.ttf", 15)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        title_font = subtitle_font = label_font = bold_font = small_font = ImageFont.load_default()

    slate = (31, 41, 59)
    border = (69, 86, 110)
    text = (238, 244, 255)
    muted = (156, 176, 208)
    cyan = (82, 209, 255)
    gold = (242, 194, 104)
    green = (92, 224, 167)
    violet = (150, 164, 255)

    draw.text((width // 2, 40), "CENTAURUS PLATFORM ARCHITECTURE", fill=cyan, font=title_font, anchor="mm")
    draw.text(
        (width // 2, 70),
        "FastAPI control plane with optional workflow ingress, retrieval, and reviewer safety gates",
        fill=muted,
        font=subtitle_font,
        anchor="mm",
    )

    draw.text((150, 150), "INPUT SURFACES", fill=violet, font=bold_font, anchor="mm")
    channels = [("Web Console", 200), ("Email Queries", 280), ("WhatsApp Messages", 360), ("Instagram DMs", 440)]
    for label, y in channels:
        draw.rounded_rectangle([40, y, 260, y + 50], radius=8, fill=slate, outline=border, width=1)
        draw.text((150, y + 25), label, fill=text, font=label_font, anchor="mm")
    draw.rounded_rectangle([30, 110, 270, 520], radius=10, outline=border, width=1)
    draw_arrow(draw, (270, 320), (360, 320), cyan)
    draw.text((315, 290), "Webhook\nPayload", fill=muted, font=small_font, anchor="mm")

    draw.rounded_rectangle([360, 110, 580, 520], radius=10, fill=slate, outline=gold, width=2)
    draw.text((470, 135), "OPTIONAL WORKFLOW GATEWAY", fill=gold, font=bold_font, anchor="mm")
    draw.text((470, 160), "[Ingress Routing]", fill=muted, font=small_font, anchor="mm")
    gateway_nodes = [
        ("Webhook Listener", 190),
        ("Payload Normalizer", 260),
        ("Escalation Gate", 330),
        ("Audit Router", 400),
        ("Webhook Responder", 470),
    ]
    for label, y in gateway_nodes:
        draw.rounded_rectangle([380, y, 560, y + 45], radius=6, fill=(12, 17, 30), outline=border, width=1)
        draw.text((470, y + 22), label, fill=text, font=small_font, anchor="mm")
    draw_arrow(draw, (580, 320), (670, 320), cyan)
    draw.text((625, 290), "POST /chat", fill=muted, font=small_font, anchor="mm")
    draw_arrow(draw, (670, 350), (580, 350), green)
    draw.text((625, 375), "JSON Response", fill=muted, font=small_font, anchor="mm")

    draw.rounded_rectangle([670, 110, 960, 780], radius=10, fill=slate, outline=violet, width=2)
    draw.text((815, 135), "CENTAURUS CONTROL PLANE", fill=violet, font=bold_font, anchor="mm")
    draw.text((815, 160), "[Current Linear Pipeline]", fill=muted, font=small_font, anchor="mm")
    services = [
        ("1. Intent Classification", 190),
        ("2. Identity Resolution", 270),
        ("3. Record Retrieval", 350),
        ("4. Retrieval Layer", 430),
        ("5. Confidence Scoring", 510),
        ("6. Response Generation", 590),
        ("7. Audit Logging", 670),
        ("8. Health Endpoint", 730),
    ]
    for label, y in services:
        draw.rounded_rectangle([690, y, 940, y + 55], radius=6, fill=(12, 17, 30), outline=border, width=1)
        draw.text((815, y + 27), label, fill=text, font=small_font, anchor="mm")

    draw.rounded_rectangle([1020, 110, 1170, 380], radius=10, fill=slate, outline=green, width=2)
    draw.text((1095, 135), "SUPABASE DATA", fill=green, font=bold_font, anchor="mm")
    draw.text((1095, 160), "[Structured records]", fill=muted, font=small_font, anchor="mm")
    for i, table in enumerate(["authors", "books", "query_logs", "identity_mappings", "knowledge_base"]):
        draw.text((1095, 200 + i * 32), f"- {table}", fill=text, font=small_font, anchor="mm")
    draw_arrow(draw, (960, 240), (1020, 240), green)
    draw_arrow(draw, (1020, 270), (960, 270), cyan)

    draw.rounded_rectangle([1020, 480, 1170, 780], radius=10, fill=slate, outline=violet, width=2)
    draw.text((1095, 505), "MODEL SERVICES", fill=violet, font=bold_font, anchor="mm")
    draw.text((1095, 530), "[LLM + embeddings]", fill=muted, font=small_font, anchor="mm")
    for i, label in enumerate(["gpt-4o-mini", "text-embedding-3-small"]):
        top = 570 + i * 90
        draw.rounded_rectangle([1030, top, 1160, top + 70], radius=6, fill=(12, 17, 30), outline=border, width=1)
        draw.text((1095, top + 35), label, fill=text, font=small_font, anchor="mm")
    draw_arrow(draw, (960, 600), (1020, 600), violet)
    draw_arrow(draw, (1020, 630), (960, 630), cyan)

    draw_arrow(draw, (470, 520), (470, 840), green)
    draw.line([(470, 840), (1095, 840)], fill=green, width=3)
    draw_arrow(draw, (1095, 840), (1095, 380), green)
    draw.text((780, 820), "Audit logging path to query_logs", fill=green, font=small_font, anchor="mm")
    draw.text((width // 2, 875), "© 2026 Centaurus platform architecture diagram.", fill=muted, font=small_font, anchor="mm")

    out = Path("docs/architecture_diagram.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"Architecture diagram generated at {out}")


if __name__ == "__main__":
    generate_arch()

"""
Generate the optional workflow ingress diagram.
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


def generate_n8n():
    width, height = 1200, 700
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        subtitle_font = ImageFont.truetype("arial.ttf", 16)
        label_font = ImageFont.truetype("arial.ttf", 14)
        bold_font = ImageFont.truetype("arial.ttf", 15)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        title_font = subtitle_font = label_font = bold_font = small_font = ImageFont.load_default()

    border = (51, 65, 85)
    card = (30, 41, 59)
    text = (241, 245, 249)
    muted = (148, 163, 184)
    orange = (251, 146, 60)
    green = (52, 211, 153)
    red = (248, 113, 113)

    draw.text((width // 2, 40), "OPTIONAL WORKFLOW INGRESS", fill=orange, font=title_font, anchor="mm")
    draw.text(
        (width // 2, 70),
        "Visualizing routing, escalation, and audit logging before the FastAPI control plane",
        fill=muted,
        font=subtitle_font,
        anchor="mm",
    )

    draw.rounded_rectangle([60, 260, 220, 360], radius=8, fill=card, outline=orange, width=2)
    draw.text((140, 285), "1. Webhook Trigger", fill=orange, font=bold_font, anchor="mm")
    draw.text((140, 315), "POST /centaurus-gateway", fill=text, font=small_font, anchor="mm")
    draw.text((140, 335), "Response mode: Last Node", fill=muted, font=small_font, anchor="mm")
    draw_arrow(draw, (220, 310), (280, 310), orange)

    draw.rounded_rectangle([280, 260, 440, 360], radius=8, fill=card, outline=border, width=1)
    draw.text((360, 285), "2. Set Payload", fill=text, font=bold_font, anchor="mm")
    draw.text((360, 315), "Normalize channel,", fill=muted, font=small_font, anchor="mm")
    draw.text((360, 335), "message, email, phone, name", fill=muted, font=small_font, anchor="mm")
    draw_arrow(draw, (440, 310), (500, 310), orange)

    draw.rounded_rectangle([500, 260, 660, 360], radius=8, fill=card, outline=orange, width=2)
    draw.text((580, 285), "3. HTTP Request", fill=orange, font=bold_font, anchor="mm")
    draw.text((580, 315), "POST /chat", fill=text, font=small_font, anchor="mm")
    draw.text((580, 335), "Timeout: 30000ms", fill=muted, font=small_font, anchor="mm")
    draw_arrow(draw, (660, 310), (720, 310), orange)

    draw.rounded_rectangle([720, 260, 880, 360], radius=20, fill=card, outline=orange, width=2)
    draw.text((800, 290), "4. IF Gate", fill=orange, font=bold_font, anchor="mm")
    draw.text((800, 320), "confidence < 0.8 OR", fill=text, font=small_font, anchor="mm")
    draw.text((800, 340), "escalated == true?", fill=text, font=small_font, anchor="mm")

    draw.line([(880, 310), (910, 310), (910, 180)], fill=red, width=3)
    draw_arrow(draw, (910, 180), (940, 180), red)
    draw.text((915, 230), "TRUE", fill=red, font=small_font, anchor="mm")

    draw.line([(880, 310), (910, 310), (910, 440)], fill=green, width=3)
    draw_arrow(draw, (910, 440), (940, 440), green)
    draw.text((915, 390), "FALSE", fill=green, font=small_font, anchor="mm")

    draw.rounded_rectangle([940, 130, 1100, 230], radius=8, fill=card, outline=red, width=2)
    draw.text((1020, 155), "5a. Set Escalation", fill=red, font=bold_font, anchor="mm")
    draw.text((1020, 185), "response = human message", fill=text, font=small_font, anchor="mm")
    draw.text((1020, 205), "escalated = true", fill=muted, font=small_font, anchor="mm")

    draw.rounded_rectangle([940, 390, 1100, 490], radius=8, fill=card, outline=green, width=2)
    draw.text((1020, 415), "5b. Pass Through", fill=green, font=bold_font, anchor="mm")
    draw.text((1020, 445), "Keep the response unchanged", fill=muted, font=small_font, anchor="mm")

    draw.line([(1100, 180), (1130, 180), (1130, 310)], fill=orange, width=3)
    draw.line([(1100, 440), (1130, 440), (1130, 310)], fill=orange, width=3)
    draw_arrow(draw, (1130, 310), (1130, 540), orange)
    draw.line([(1130, 540), (440, 540)], fill=orange, width=3)
    draw_arrow(draw, (440, 540), (440, 560), orange)

    draw.rounded_rectangle([340, 560, 540, 640], radius=8, fill=card, outline=border, width=1)
    draw.text((440, 580), "6. Audit Log", fill=text, font=bold_font, anchor="mm")
    draw.text((440, 605), "Write query, response, intent, score", fill=muted, font=small_font, anchor="mm")
    draw.text((440, 623), "Continue on fail = True", fill=green, font=small_font, anchor="mm")
    draw_arrow(draw, (540, 600), (660, 600), orange)

    draw.rounded_rectangle([660, 560, 860, 640], radius=8, fill=card, outline=orange, width=2)
    draw.text((760, 580), "7. Webhook Response", fill=orange, font=bold_font, anchor="mm")
    draw.text((760, 610), "Status 200 | response body", fill=text, font=small_font, anchor="mm")

    draw.text((width // 2, 675), "© 2026 Centaurus workflow ingress diagram.", fill=muted, font=small_font, anchor="mm")

    out = Path("docs/n8n_workflow.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"Workflow diagram generated at {out}")


if __name__ == "__main__":
    generate_n8n()
